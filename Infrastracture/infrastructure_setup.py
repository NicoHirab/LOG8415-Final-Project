from infrastructure_utils import *

STANDALONE_DB_PORT = 3306
SSH_PORT = 22
FLASK_PORT = 5000
DB_MANAGER_PORT=1186
DB_NODE_PORT = 2202

private_ip_addresses = {
    "host_manager":"10.0.1.4",
    "data_nodes":["10.0.1.5","10.0.1.6","10.0.1.7"],
    "proxy":"10.0.1.8",
    "gatekeeper":"10.0.1.9",
    "standalone":"10.0.1.10"
}


def create_gatekeeper_instance(vpc_id: str, subnet_id: str, key_name: str):
    sq_gatekeeper = create_security_group(vpc_id, "sg_gatekeeper", "Security group for the gatekeeper")
    
    set_security_group_policy(sq_gatekeeper, 
        [{"IpProtocol": "tcp", "FromPort":FLASK_PORT,"ToPort":FLASK_PORT, "IpRanges": [{'CidrIp': '0.0.0.0/0'}]},
        {"IpProtocol": "tcp", "FromPort":SSH_PORT,"ToPort":SSH_PORT, "IpRanges": [{'CidrIp': '0.0.0.0/0'}]}],
    )
    gatekeeper_instance = launch_ec2(
        1,"t2.micro", key_name, subnet_id, sq_gatekeeper["GroupId"])[0]

    return gatekeeper_instance


def create_proxy_instance(vpc_id: str, subnet_id: str, key_name: str,gate_keeper_ip:str):
    sq_proxy = create_security_group(vpc_id, "sg_proxy", "Security group for the proxy")
    
    set_security_group_policy(sq_proxy, 
        [{"IpProtocol": "tcp", "FromPort":FLASK_PORT,"ToPort":FLASK_PORT, "IpRanges": [{'CidrIp': gate_keeper_ip + '/32'}]},
        {"IpProtocol": "tcp", "FromPort":SSH_PORT,"ToPort":SSH_PORT, "IpRanges": [{'CidrIp': '0.0.0.0/0'}]}],
    )

    standalone_mysql_instance = launch_ec2(
        1,"t2.micro", key_name, subnet_id, sq_proxy["GroupId"],private_ip_address=private_ip_addresses["proxy"])[0]

    return standalone_mysql_instance

def create_standalone_infra(vpc_id: str, subnet_id: str, key_name: str, user_data: str):

    sg_standalone_mysql = create_security_group(vpc_id, "sg_standalone_mysql", "Security group for Standalone Infrastructure")
    
    set_security_group_policy(sg_standalone_mysql, 
        [{"IpProtocol": "tcp", "FromPort":STANDALONE_DB_PORT,"ToPort":STANDALONE_DB_PORT, "IpRanges": [{'CidrIp': '0.0.0.0/0'}]},
        {"IpProtocol": "tcp", "FromPort":SSH_PORT,"ToPort":SSH_PORT, "IpRanges": [{'CidrIp': '0.0.0.0/0'}]}],
    )
    standalone_mysql_instance = launch_ec2(
        1,"t2.micro", key_name, subnet_id, sg_standalone_mysql["GroupId"], user_data)[0]

    return standalone_mysql_instance

def create_cluster_manager_instance(vpc_id: str, subnet_id: str,subnet_cidr:str , key_name: str,  proxy_ip:str,user_data:str=None):

    # Create cluster manager
    sg_cluster_manager_mysql = create_security_group(vpc_id, "sg_cluster_mysql", "Security group for Cluster Infrastructure")
    
    set_security_group_policy(sg_cluster_manager_mysql, 
        [{"IpProtocol": "tcp", "FromPort":STANDALONE_DB_PORT,"ToPort":STANDALONE_DB_PORT, "IpRanges": [{'CidrIp': proxy_ip + '/32'}]},
        {"IpProtocol": "tcp", "FromPort":DB_MANAGER_PORT,"ToPort":DB_MANAGER_PORT, "IpRanges": [{'CidrIp':subnet_cidr}]},
        {"IpProtocol": "tcp", "FromPort":SSH_PORT,"ToPort":SSH_PORT, "IpRanges": [{'CidrIp': '0.0.0.0/0'}]}],
        
    )
    cluster_manager_instance = launch_ec2(
        1,"t2.micro", key_name, subnet_id, sg_cluster_manager_mysql["GroupId"],user_data,private_ip_address=private_ip_addresses["host_manager"])[0]

    return cluster_manager_instance

def create_cluster_data_instance(vpc_id: str, subnet_id: str,subnet_cidr:str,key_name: str,  proxy_ip:str, user_data:str=None,number_instances:int=3):

    sg_data_nodes_mysql = create_security_group(vpc_id, "sg_data_nodes_mysql", "Security group for Cluster data nodes Infrastructure")
    
    set_security_group_policy(sg_data_nodes_mysql, 
        [{"IpProtocol": "tcp", "FromPort":STANDALONE_DB_PORT,"ToPort":STANDALONE_DB_PORT, "IpRanges": [{'CidrIp': proxy_ip + '/32'}]},
        {"IpProtocol": "tcp", "FromPort":SSH_PORT,"ToPort":SSH_PORT, "IpRanges": [{'CidrIp': '0.0.0.0/0'}]},
        {"IpProtocol": "tcp", "FromPort":DB_NODE_PORT,"ToPort":DB_NODE_PORT, "IpRanges": [{'CidrIp': subnet_cidr}]}
        ],
        
    )

    for private_ip_address in private_ip_addresses["data_nodes"]:
        cluster_data_node_instances = launch_ec2(
                1,"t2.micro", key_name, subnet_id, sg_data_nodes_mysql["GroupId"],user_data,private_ip_address=private_ip_address,)[0]

    return cluster_data_node_instances



def setup_infrastructure():
    key_name = "LOG8415_Final_Project"

    vpc_id = retrieve_default_vpc()['VpcId']

    subnets = retrieve_subnets(vpc_id)
    subnet_id = subnets[0]['SubnetId']
    create_key_pairs(key_name)

    gatekeeper = create_gatekeeper_instance(vpc_id,subnet_id,key_name)

    proxy = create_proxy_instance(vpc_id,subnet_id,key_name,gatekeeper.private_ip_address)



    with open(os.path.join(sys.path[0], '../Setup_Scripts/manager_node_mysql_setup.sh'), 'r') as f:
            manager_node_setup = f.read() 

    cluster_manager = create_cluster_manager_instance(vpc_id,subnet_id,subnets[0]['CidrBlock'],key_name,proxy.private_ip_address,manager_node_setup)

    with open(os.path.join(sys.path[0], '../Setup_Scripts/data_node_mysql_setup.sh'), 'r') as f:
            data_node_setup = f.read() 

    cluster_data_node_instances = create_cluster_data_instance(vpc_id,subnet_id,subnets[0]['CidrBlock'],key_name,proxy.private_ip_address,data_node_setup)

    with open(os.path.join(sys.path[0], '../Setup_Scripts/standalone_mysql_setup.sh'), 'r') as f:
            standalone_MYSQL_data = f.read() 

    create_standalone_infra(vpc_id,subnet_id,key_name,standalone_MYSQL_data)




if __name__ == '__main__':
    setup_infrastructure()