import paramiko

def benchmark(hostname:str,private_key_path:str,benchmark_script_path:str,results_path:str):
    try:
        with paramiko.SSHClient() as client:

            client.set_missing_host_key_policy(paramiko.AutoAddPolicy)

            print("Connecting to standalone DB on:",hostname)

            client.connect(hostname=hostname,port=22, username='ubuntu', key_filename=private_key_path)

            with open(benchmark_script_path, 'r') as f:
                standalone_script = f.read()
            print("Executing benchmarking script for standalone DB")
            _, stdout, stderr = client.exec_command(command=standalone_script, get_pty=True)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                print("done\n")
            else:
                print(stderr.read())
                print(stdout.read().decode())
                raise Exception(f"Error while executing benchmarking on the standalone DB")
            with client.open_sftp() as sftp:
                # Download the remote file
                sftp.get("results.txt", results_path)

            print(f"File downloaded successfully from results.txt to results/standalone_benchmark.txt")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    benchmark("34.238.253.180","LOG8415_Final_Project.pem","/Setup_Scripts/benchmark_standalone.sh","Benchmark/results")