import paramiko
import os, sys

def benchmark(hostname: str, private_key_path: str, benchmark_script_path: str, results_path: str):
    try:
        # Create an SSH client instance
        with paramiko.SSHClient() as client:

            # Automatically add the server's host key (this is for testing purposes)
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy)

            # Connect to the remote server using SSH
            print("Connecting to DB on:", hostname)
            client.connect(hostname=hostname, port=22, username='ubuntu', key_filename=private_key_path)

            # Read the benchmarking script from the local file
            with open(benchmark_script_path, 'r') as f:
                standalone_script = f.read()

            # Execute the benchmarking script on the remote server
            print("Executing benchmarking script")
            _, stdout, stderr = client.exec_command(command=standalone_script, get_pty=True)
            exit_status = stdout.channel.recv_exit_status()

            # Check if the execution was successful
            if exit_status == 0:
                print("done\n")
            else:
                # Print any error messages in case of failure
                print(stdout.read().decode())
                raise Exception(f"Error while executing benchmarking on the standalone DB")

            # Use SFTP to transfer the results file from the remote server to the local machine
            with client.open_sftp() as sftp:
                # Download the remote file
                sftp.get("results.txt", results_path)

            print(f"File downloaded successfully from results.txt to {results_path}")
            client.close()

    except Exception as e:
        # Handle any exceptions that might occur during the process
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    standalone_script_path = os.path.join(sys.path[0], "../Setup_Scripts/benchmark_standalone.sh")
    cluster_script_path = os.path.join(sys.path[0], "../Setup_Scripts/benchmark_cluster.sh")
    results_path_standalone = os.path.join(sys.path[0], "results/standalone_benchmark.txt")
    results_path_cluster = os.path.join(sys.path[0], "results/cluster_benchmark.txt")
    
    #benchmark("52.207.243.188","LOG8415_Final_Project.pem",standalone_script_path,results_path)
    benchmark("44.202.83.185","LOG8415_Final_Project.pem",cluster_script_path,results_path_cluster)