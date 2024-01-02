# Importing necessary functions from infrastructure_utils module
from Infrastracture.infrastructure_utils import *

# Define constant values for various ports
STANDALONE_DB_PORT = 3306
SSH_PORT = 22
FLASK_PORT = 5001
DB_MANAGER_PORT = 1186
DB_NODE_PORT = 2202

# Define private IP addresses for different components in the infrastructure
private_ip_addresses = {
    "host_manager": "10.0.1.4",
    "data_nodes": ["10.0.1.5", "10.0.1.6", "10.0.1.7"],
    "proxy": "10.0.1.8",
    "gatekeeper": "10.0.1.9",
    "standalone": "10.0.1.10"
}

def create_gatekeeper_instance(vpc_id: str, subnet_id: str, key_name: str, user_data: str):
    """
    Creates an EC2 instance for the gatekeeper and returns the instance object.

    Parameters:
    - vpc_id (str): ID of the Virtual Private Cloud (VPC).
    - subnet_id (str): ID of the subnet.
    - key_name (str): Name of the key pair.
    - user_data (str): User data script for instance initialization.

    Returns:
    - EC2Instance: The created EC2 instance object.
    """
    # Create security group for gatekeeper
    sq_gatekeeper = create_security_group(vpc_id, "sg_gatekeeper", "Security group for the gatekeeper")
    
    # Set security group policies for gatekeeper
    set_security_group_policy(sq_gatekeeper, 
        [{"IpProtocol": "tcp", "FromPort": FLASK_PORT, "ToPort": FLASK_PORT, "IpRanges": [{'CidrIp': '0.0.0.0/0'}]},
        {"IpProtocol": "tcp", "FromPort": SSH_PORT, "ToPort": SSH_PORT, "IpRanges": [{'CidrIp': '0.0.0.0/0'}]}],
    )
    
    # Launch EC2 instance for gatekeeper
    gatekeeper_instance = launch_ec2(
        1, "t2.micro", key_name, subnet_id, sq_gatekeeper["GroupId"], user_data)[0]

    return gatekeeper_instance


def create_proxy_instance(vpc_id: str, subnet_id: str, key_name: str, gate_keeper_ip: str, user_data: str):
    """
    Creates an EC2 instance for the proxy and returns the instance object.

    Parameters:
    - vpc_id (str): ID of the Virtual Private Cloud (VPC).
    - subnet_id (str): ID of the subnet.
    - key_name (str): Name of the key pair.
    - gate_keeper_ip (str): IP address of the gatekeeper for security group policy.
    - user_data (str): User data script for instance initialization.

    Returns:
    - EC2Instance: The created EC2 instance object.
    """
    # Create security group for proxy
    sq_proxy = create_security_group(vpc_id, "sg_proxy", "Security group for the proxy")
    
    # Set security group policies for proxy
    set_security_group_policy(sq_proxy, 
        [{"IpProtocol": "tcp", "FromPort": FLASK_PORT, "ToPort": FLASK_PORT, "IpRanges": [{'CidrIp': gate_keeper_ip + '/32'}]},
        {"IpProtocol": "tcp", "FromPort": SSH_PORT, "ToPort": SSH_PORT, "IpRanges": [{'CidrIp': '0.0.0.0/0'}]}],
    )

    # Launch EC2 instance for proxy
    standalone_mysql_instance = launch_ec2(
        1, "t2.micro", key_name, subnet_id, sq_proxy["GroupId"], user_data, private_ip_address=private_ip_addresses["proxy"])[0]

    return standalone_mysql_instance

def create_standalone_infra(vpc_id: str, subnet_id: str, key_name: str, user_data: str):
    """
    Creates an EC2 instance for standalone infrastructure and returns the instance object.

    Parameters:
    - vpc_id (str): ID of the Virtual Private Cloud (VPC).
    - subnet_id (str): ID of the subnet.
    - key_name (str): Name of the key pair.
    - user_data (str): User data script for instance initialization.

    Returns:
    - EC2Instance: The created EC2 instance object.
    """
    # Create security group for standalone infrastructure
    sg_standalone_mysql = create_security_group(vpc_id, "sg_standalone_mysql", "Security group for Standalone Infrastructure")
    
    # Set security group policies for standalone infrastructure
    set_security_group_policy(sg_standalone_mysql, 
        [{"IpProtocol": "tcp", "FromPort": STANDALONE_DB_PORT, "ToPort": STANDALONE_DB_PORT, "IpRanges": [{'CidrIp': '0.0.0.0/0'}]},
        {"IpProtocol": "tcp", "FromPort": SSH_PORT, "ToPort": SSH_PORT, "IpRanges": [{'CidrIp': '0.0.0.0/0'}]}],
    )
    
    # Launch EC2 instance for standalone infrastructure
    standalone_mysql_instance = launch_ec2(
        1, "t2.micro", key_name, subnet_id, sg_standalone_mysql["GroupId"], user_data)[0]

    return standalone_mysql_instance

# Similar docstrings can be added for other functions

def create_cluster_manager_instance(vpc_id: str, subnet_id: str, subnet_cidr: str, key_name: str, proxy_ip: str, user_data: str = None):
    """
    Creates an EC2 instance for the cluster manager and returns the instance object.

    Parameters:
    - vpc_id (str): ID of the Virtual Private Cloud (VPC).
    - subnet_id (str): ID of the subnet.
    - subnet_cidr (str): CIDR block for subnet.
    - key_name (str): Name of the key pair.
    - proxy_ip (str): IP address of the proxy for security group policy.
    - user_data (str): User data script for instance initialization.

    Returns:
    - EC2Instance: The created EC2 instance object.
    """
    # Create cluster manager
    sg_cluster_manager_mysql = create_security_group(vpc_id, "sg_cluster_mysql", "Security group for Cluster Infrastructure")
    
    # Set security group policies for cluster manager
    set_security_group_policy(sg_cluster_manager_mysql, 
        [{"IpProtocol": "tcp", "FromPort": STANDALONE_DB_PORT, "ToPort": STANDALONE_DB_PORT, "IpRanges": [{'CidrIp': proxy_ip + '/32'}]},
        {"IpProtocol": "tcp", "FromPort": DB_MANAGER_PORT, "ToPort": DB_MANAGER_PORT, "IpRanges": [{'CidrIp': subnet_cidr}]},
        {"IpProtocol": "tcp", "FromPort": SSH_PORT, "ToPort": SSH_PORT, "IpRanges": [{'CidrIp': '0.0.0.0/0'}]}],
    )
    
    # Launch EC2 instance for cluster manager
    cluster_manager_instance = launch_ec2(
        1, "t2.micro", key_name, subnet_id, sg_cluster_manager_mysql["GroupId"], user_data, private_ip_address=private_ip_addresses["host_manager"])[0]

    return cluster_manager_instance

def create_cluster_data_instance(vpc_id: str, subnet_id: str, subnet_cidr: str, key_name: str, proxy_ip: str, user_data: str = None, number_instances: int = 3):
    """
    Creates multiple EC2 instances for cluster data nodes and returns the instance objects.

    Parameters:
    - vpc_id (str): ID of the Virtual Private Cloud (VPC).
    - subnet_id (str): ID of the subnet.
    - subnet_cidr (str): CIDR block for subnet.
    - key_name (str): Name of the key pair.
    - proxy_ip (str): IP address of the proxy for security group policy.
    - user_data (str): User data script for instance initialization.
    - number_instances (int): Number of instances to create.

    Returns:
    - list: List of created EC2 instance objects.
    """
    # Create security group for cluster data nodes
    sg_data_nodes_mysql = create_security_group(vpc_id, "sg_data_nodes_mysql", "Security group for Cluster data nodes Infrastructure")
    
    # Set security group policies for cluster data nodes
    set_security_group_policy(sg_data_nodes_mysql, 
        [{"IpProtocol": "tcp", "FromPort": STANDALONE_DB_PORT, "ToPort": STANDALONE_DB_PORT, "IpRanges": [{'CidrIp': proxy_ip + '/32'}]},
        {"IpProtocol": "tcp", "FromPort": SSH_PORT, "ToPort": SSH_PORT, "IpRanges": [{'CidrIp': '0.0.0.0/0'}]},
        {"IpProtocol": "tcp", "FromPort": DB_NODE_PORT, "ToPort": DB_NODE_PORT, "IpRanges": [{'CidrIp': subnet_cidr}]}
        ],
    )

    # Launch multiple EC2 instances for cluster data nodes
    cluster_data_node_instances = []
    for private_ip_address in private_ip_addresses["data_nodes"]:
        instances = launch_ec2(
                1, "t2.micro", key_name, subnet_id, sg_data_nodes_mysql["GroupId"], user_data, private_ip_address=private_ip_address)[0]
        cluster_data_node_instances.append(instances)

    return cluster_data_node_instances

def setup_infrastructure():
    """
    Sets up the entire infrastructure by creating EC2 instances for gatekeeper, proxy, cluster manager, 
    cluster data nodes, and standalone infrastructure.

    Returns:
    - tuple: Tuple containing instances for the cluster manager and standalone infrastructure.
    """
    key_name = "LOG8415_Final_Project"

    vpc_id = retrieve_default_vpc()['VpcId']

    subnets = retrieve_subnets(vpc_id)
    subnet_id = subnets[0]['SubnetId']
    create_key_pairs(key_name)

    with open(os.path.join(sys.path[0], 'Setup_Scripts/gatekeeper_setup.sh'), 'r') as f:
            gatekeeper_setup = f.read() 
    gatekeeper = create_gatekeeper_instance(vpc_id,subnet_id,key_name,gatekeeper_setup)

    with open(os.path.join(sys.path[0], 'Setup_Scripts/proxy_setup.sh'), 'r') as f:
            proxy_setup = f.read() 
    proxy = create_proxy_instance(vpc_id,subnet_id,key_name,gatekeeper.private_ip_address,proxy_setup)

    with open(os.path.join(sys.path[0], 'Setup_Scripts/manager_node_mysql_setup.sh'), 'r') as f:
            manager_node_setup = f.read() 

    cluster_manager = create_cluster_manager_instance(vpc_id,subnet_id,subnets[0]['CidrBlock'],key_name,proxy.private_ip_address,manager_node_setup)

    with open(os.path.join(sys.path[0], 'Setup_Scripts/data_node_mysql_setup.sh'), 'r') as f:
            data_node_setup = f.read() 

    cluster_data_node_instances = create_cluster_data_instance(vpc_id,subnet_id,subnets[0]['CidrBlock'],key_name,proxy.private_ip_address,data_node_setup)

    with open(os.path.join(sys.path[0], 'Setup_Scripts/standalone_mysql_setup.sh'), 'r') as f:
            standalone_MYSQL_data = f.read() 

    standalone = create_standalone_infra(vpc_id,subnet_id,key_name,standalone_MYSQL_data)

    return cluster_manager, standalone

# Entry point of the script
if __name__ == '__main__':
    cluster_manager, standalone = setup_infrastructure()
    print(cluster_manager.id)
    print(standalone.id)
