import boto3
import os, sys, time
from Infrastracture.infrastructure_setup import setup_infrastructure
from Benchmark.benchmark import benchmark

if __name__ == "__main__":
    cluster_manager, standalone = setup_infrastructure()

    client = boto3.client('ec2')
    instance_running_waiter = client.get_waiter('instance_running')
    print(f"waiting for instances: {cluster_manager.id} {standalone.id}")
    # Define the parameters for the waiter
    waiter_params = {
        'InstanceIds': [cluster_manager.id,standalone.id],
    }
    instance_running_waiter.wait(**waiter_params)

    time.sleep(180)
    
    print(f"Instances {cluster_manager.id} and {standalone.id} are running")
    print(f"Starting benchmarking for Standalone MySQL DB")
    #Run benchmarking for standalone instance
    standalone.load()
    standalone_script_path = os.path.join(sys.path[0], "Setup_Scripts/benchmark_standalone.sh")
    results_path_standalone = os.path.join(sys.path[0], "Benchmark/results/standalone_benchmark.txt")
    benchmark(standalone.public_ip_address,"LOG8415_Final_Project.pem",standalone_script_path,results_path_standalone)
    print(f"Benchmarking for Standalone MySQL DB completed")
    print(f"Starting benchmarking for MySQL Cluster DB")

    # Run benchmarking for cluster instances
    cluster_manager.load()
    cluster_script_path = os.path.join(sys.path[0], "Setup_Scripts/benchmark_cluster.sh")
    results_path_cluster = os.path.join(sys.path[0], "Benchmark/results/cluster_benchmark.txt")
    benchmark(cluster_manager.public_ip_address,"LOG8415_Final_Project.pem",cluster_script_path,results_path_cluster)
    print(f"Benchmarking for MySQL Cluster DB completed")
