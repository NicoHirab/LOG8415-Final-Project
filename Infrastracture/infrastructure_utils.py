import boto3
import sys
import os
"""
description: script which creates a key pair for the ec2 instances, it also saves the key value locally as a txt file
params: key_name : str: represents the name representing the key
return_value: the key information as a dictionnary

"""
def create_key_pairs(key_name: str) -> dict:

    ec2 : boto3.client = boto3.client('ec2')
    key_pairs = ec2.describe_key_pairs()['KeyPairs']
    print(key_pairs)
    key_pair = next((key_pair for key_pair in key_pairs if key_pair["KeyName"] == key_name),None)

    if key_pair == None:
        private_key_path = key_name+".pem"
        key_pair = ec2.create_key_pair(KeyName=key_name)
        private_key_file=open(private_key_path,"w")
        private_key_file.write(key_pair['KeyMaterial'])
        private_key_file.close 
        os.chmod(private_key_path, 0o400)



def create_security_group(vpc_id : str, sc_group_name : str, sc_description : str) -> str:
    """
    description: script which creates a new security_group
    vpc_id: the id of the virtual private cloud network to associate with the security group
    return_value: security_group_id : str: a string representing the security group_id

    """
    client = boto3.client('ec2')
    existing_sg = client.describe_security_groups(
        Filters=[
            {
                'Name': 'group-name',
                'Values': [
                    sc_group_name,
                ]
            },
        ],
    )['SecurityGroups']
    if len(existing_sg) == 0:
        response = client.create_security_group(
        Description=sc_description,
        GroupName=sc_group_name,
        VpcId= vpc_id,
        )
    else:
        response = existing_sg[0]
    return response

"""
description: script setting security group ip permissions
security_group_id : str: a string representing the security group_id
return_value: security_group_id : str: a string representing the security group_id

"""
def set_security_group_policy(security_group: dict,IpPermissions:list) -> str:
    client = boto3.client('ec2')
    client.authorize_security_group_ingress(
        GroupId=security_group["GroupId"],
        IpPermissions=IpPermissions
    )
    return security_group

def retrieve_default_vpc() -> dict:
    """
    description: retrieves the default vpc
    params: None
    return_value: the vpc dict

    """

    client : boto3.client = boto3.client('ec2')

    available_vpcs = client.describe_vpcs(
         Filters=[
            {
                'Name': 'cidr',
                'Values': [
                    '10.0.0.0/16',
                ]
            },
        ],
    )['Vpcs']
    selected_vpc = ''
    if(len(available_vpcs) == 0):
        selected_vpc = client.create_vpc(CidrBlock='10.0.0.0/16')['Vpc']
    else:
        selected_vpc = available_vpcs[0]
    print(selected_vpc)

    available_igw = client.describe_internet_gateways(Filters=[
        {
            'Name': 'attachment.vpc-id',
            'Values': [
                selected_vpc['VpcId'],
            ]
        },
    ],)['InternetGateways']
    if len(available_igw) == 0:
        igw_response = client.create_internet_gateway()

        igw_id = igw_response['InternetGateway']['InternetGatewayId']

        client.attach_internet_gateway(
            InternetGatewayId=igw_id,
            VpcId=selected_vpc["VpcId"],
        )
        route_table = client.describe_route_tables(
            Filters=[
                {
                    'Name': 'vpc-id',
                    'Values':[
                        selected_vpc["VpcId"]
                    ]
                }
            ]
        )
        client.create_route(
            DestinationCidrBlock="0.0.0.0/0",
            RouteTableId=route_table['RouteTables'][0]["Associations"][0]['RouteTableId'],
            GatewayId=igw_id
        )
    return selected_vpc

def retrieve_subnets(vpc_id : str) -> list:
    """
    description: function which creates the subnets of
    client: boto3.client : the ec2 boto3 client
    vpc_id: the vpc to which will contain the subnets
    return_value: list: a list of the subnet_id which were created

    """
    client : boto3.client = boto3.client('ec2')
    availability_zones = ['us-east-1a', 'us-east-1b']
    available_subnets = client.describe_subnets()['Subnets']
    subnet_cidr_blocks = ['10.0.1.0/24', '10.0.2.0/24']
    
    subnets = []

    for i, cidr_block in enumerate(subnet_cidr_blocks):
        available_subnet = next((subnet for subnet in available_subnets if subnet["CidrBlock"] == cidr_block),None)
        if available_subnet == None:
            subnet_response = client.create_subnet(
                VpcId=vpc_id,
                CidrBlock=cidr_block,
                AvailabilityZone=availability_zones[i],
            )
        else:
            subnet_response = available_subnet
        subnets.append(subnet_response)
    return subnets

"""
description: function which creates and configure and ec2 instance
count: int: the ammoun of ec2 isntance to create
instance_type: str : the type of ec2 instance to create
key_name: str : the name of the key needed to access ec2 instance
subnet: str: the subnet to associate the ec2 instance with
security_group_id: str: the id of the security group to associate the ec2 instance with
return_value: dict: the information on the created ec2 instances

"""
def launch_ec2(count: int, instance_type: str, key_name : str, subnet: str, security_group_id: str,userData:str = "",private_ip_address=None,volume_size=16) -> dict:
    ec2 = boto3.resource('ec2')
    NetworkInterfaces=[
            {
                'DeviceIndex': 0,
                'AssociatePublicIpAddress': True,
                'Groups': [security_group_id],
                'SubnetId': subnet
            },
        ]
    if private_ip_address != None:
        NetworkInterfaces[0]['PrivateIpAddress'] = private_ip_address
    response = ec2.create_instances(
        ImageId="ami-08bf0e5db5b302e19",
        MinCount=count,
        MaxCount=count,
        InstanceType=instance_type,
        KeyName=key_name,
        BlockDeviceMappings=[
            {
                "DeviceName": "/dev/sda1",
                "Ebs" : { 
                    "VolumeSize" : volume_size
                    }
            }
        ],
        NetworkInterfaces=NetworkInterfaces,
        UserData= userData,
        )
    return response

def waitForInstance(instanceId:str):
    ec2 = boto3.resource('ec2')
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instanceId])