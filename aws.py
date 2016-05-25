"""
https://github.com/boto/boto3#quick-start

Security credentials:
http://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html

Documentation
https://boto3.readthedocs.org/en/latest/
http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.run_instances

Gotcha's:
Make sure the security group allows SSH connectivity 
"""

import boto3
import pdb
import os
from keys import sync_aws_key 
from vino.utils import SleepFSM
import paramiko
from socket import error as socket_error
from utils import create_and_raise
import sys


def get_server_ips(aws_client, instance_ids, username="ubuntu"):
    """
    blocking method that waits until all server are ready and 
    are SSHable 
    """
    sleep = SleepFSM()
    sleep.init(max_tries=7)
    
    server_ips = []

    running = aws_client.list_running_servers(instance_ids)
    while len(running) != len(instance_ids):
        running = aws_client.list_running_servers(instance_ids)
        sleep()
       
    sshClient = paramiko.SSHClient()
    sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    while len(running):
        #Need nested for loop since AWS's response is
        #nested
        group = running.pop()["Instances"]
        while len(group):
            node = group.pop()
            while True:
                try:
                    print "Trying ssh {}@{}".format(username, node['PublicDnsName'])
                    sshClient.connect(node['PublicDnsName'], username=username)
                    server_ips.append(node['PublicDnsName'])
                    break
                except socket_error:
                    print "SSH failed...."
                sleep()
    return server_ips

#Image id's for same image vary by location
#Ubuntu 14.04
ubuntu = {
    'us-east-1':'ami-fce3c696', #N. Virginia
    'us-west-1':'ami-06116566', #N. California
    'us-west-2':'ami-9abea4fb', #Oregon
}


class AwsClient(object):
    """
    A class for a AWS Client
    """
    def __init__(self, aws_access_key_id="", aws_secret_access_key="", region=""):
        self.aws_access_key_id     = aws_access_key_id or os.environ["AWS_ACCESS_KEY_ID"]
        self.aws_secret_access_key = aws_secret_access_key or os.environ["AWS_SECRET_ACCESS_KEY"]
        self.set_region(region or os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
        
        self.ec2_client = self._get_client('ec2')

    def _get_client(self, service):
        """
        Gets a client for the given service
        Arguments:-
            service:- name of service, eg. 'ec2', 's3'
        """
        #Check if the environment vars are set
        #See http://boto3.readthedocs.org/en/latest/guide/configuration.html
        #for setting credential vars
        #See http://russell.ballestrini.net/setting-region-programmatically-in-boto3/
        #for setting region
        
        return boto3.client(service, 
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region
        )

    def set_region(self, region):
        """
        Sets the default region
        """
        self.aws_region = region 

    def check_keyname(self, keyname):
        """
        Checks whether keyname exists
        """
        resp = self.ec2_client.describe_key_pairs()
        return next((True for keypair in resp["KeyPairs"] 
                    if keypair["KeyName"] == keyname), False)

    def check_keyfingerprint(self, keyname, fingerprint):
        """
        Checks whether fingerprint matches local key.
        """
        resp = self.ec2_client.describe_key_pairs()
        return next((True for keypair in resp["KeyPairs"] 
                    if keypair["KeyName"] == keyname and keypair["KeyFingerprint"] == fingerprint), False)

    def create_keypair(self, keyname, pubkey):
        """
        create a keypair with the given name
        """
        self.ec2_client.import_key_pair(
            KeyName = keyname,
            PublicKeyMaterial = pubkey
        )

    def get_keyname(self, fingerprint):
        """
        Get keyname with matching fingerprint or None
        """
        resp = self.ec2_client.describe_key_pairs()
        return next((keypair["KeyName"] for keypair in resp["KeyPairs"] 
                    if keypair["KeyFingerprint"] == fingerprint), None)

    def remove_keypair(self, keyname):
        """
        Deletes a keypair
        """
        self.ec2_client.delete_key_pair(KeyName=keyname)

    def list_images(self):
        """
        Returns a list of images. 
        Very slow operation (~15s) since AWS has 50K > images
        """
        resp = self.ec2_client.describe_images()
        return resp 

    def list_security_groups(self):
        resp = self.ec2_client.describe_security_groups()
        return resp['SecurityGroups']

    def create_server(self, image, flavor, keyname='', user_data=''):
        """
        Creates a server 
        """
        vpc_id = self.get_vpc_id()
        resp = self.ec2_client.describe_subnets(Filters=[{'Name':'vpc-id', 'Values':[vpc_id]}])
        subnet_id = resp['Subnets'][0]['SubnetId']
        secgroup_id = self.get_secgroup_id()
        net_ifaces=[{'SubnetId': subnet_id, 'DeviceIndex':0, 'AssociatePublicIpAddress':True, 'Groups':[secgroup_id]}]
        
        resp = self.ec2_client.run_instances(
                ImageId=image,
                InstanceType=flavor,
                MinCount=1,
                MaxCount=1,
                KeyName = keyname,
                UserData = user_data,
                NetworkInterfaces=net_ifaces,
                )

        return [instance["InstanceId"] for instance in resp["Instances"]]

    def list_servers(self):
        resp = self.ec2_client.describe_instances()
        return resp['Reservations'] 
#        ec2 = boto3.resource('ec2')
#        instances = [inst for inst in ec2.instances.iterator()]
#    
#        instances = ec2.instances.filter(
#            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
#    
#        instances = ec2.instances.all()
#        for instance in instances:
#            print(instance.id, instance.instance_type)

    def list_running_servers(self, instance_ids=[]):
        """
        Returns instances matching instance_ids, where
        the status is 'running'
        """
        if instance_ids:
            resp = self.ec2_client.describe_instances(
                InstanceIds=instance_ids, 
                Filters=[
                    {
                        'Name': 'instance-state-name',
                        'Values': ['running'],
                    }
                ]
            )
        else:
            resp = self.ec2_client.describe_instances(
                Filters=[
                    {
                        'Name': 'instance-state-name',
                        'Values': ['running'],
                    }
                ]
            )
        return resp['Reservations']

    def delete_all(self):
        """
        Delete all servers in running or pending state
        """
        servers = self.list_servers() 
        server_ids = [ instance['InstanceId'] for group in servers
                            for instance in group["Instances"] 
                                if instance['State']['Name'] == 'pending' 
                                    or instance['State']['Name'] == 'running'
                                ]
        print "Deleting {}".format(server_ids)
        if server_ids:
            self.ec2_client.terminate_instances(InstanceIds=server_ids)

    def get_vpc_id(self):
        """
        Returns VpcId of first VPC, if none
        exist, creates one.
        """
        resp = self.ec2_client.describe_vpcs() 
        if not resp['Vpcs']:
            #create a VPC
            resp = self.ec2_client.create_vpc(CidrBlock='10.0.0.0/28')
            return resp['Vpc']['VpcId']
        else:
            return resp['Vpcs'][0]['VpcId']

    def get_secgroup_id(self):
        """
        Returns wordpress secgroup Id, 
        If does not exist; creates wordpress secgroup and adds rules
        and returns id
        """
        group_name = 'wordpress'
        #check if group exists
        resp = self.ec2_client.describe_security_groups(Filters=[{'Name':'group-name', 'Values': [group_name]}])
        
        if len(resp['SecurityGroups']) > 0: 
            secgroup_id = resp['SecurityGroups'][0]['GroupId'] 
        else:
            #create the Secgroup
            vpc_id = self.get_vpc_id()
            resp = self.ec2_client.create_security_group(GroupName=group_name, 
                                                         Description='wordpress sec group', 
                                                         VpcId=vpc_id)
    
            #Add the rules
            secgroup_id = resp['GroupId']
            self.ec2_client.authorize_security_group_ingress(
                        GroupId=group_id, 
                        IpPermissions=[
                            {'IpProtocol':'icmp', 'FromPort':-1, 'ToPort':-1, 'IpRanges':[{'CidrIp':'0.0.0.0/0'}] },
                            {'IpProtocol':'tcp', 'FromPort':22, 'ToPort':22, 'IpRanges':[{'CidrIp':'0.0.0.0/0'}] },
                            {'IpProtocol':'udp', 'FromPort':1194, 'ToPort':1194, 'IpRanges':[{'CidrIp':'0.0.0.0/0'}] }
                        ])
        return secgroup_id

    def delete_secgroup(self, secgroup_id):
        """
        Removes the specified secgroup
        """
        self.ec2_client.delete_security_group(GroupId=secgroup_id)
        

if __name__ == "__main__":
    DEFAULT_KEYNAME="spandan_key"

    ac = AwsClient()
    #region is set through env var, but explicitly set it again
    region = 'us-east-1'
    ac.set_region(region)
    
    #List the servers
    #print "Listing servers...."
    #print ac.list_servers()

    #First, let's handle the keys
    sync_aws_key(DEFAULT_KEYNAME, ac, clobber=True)
    #ac.delete_all()

    print ac.get_secgroup_id()
    #ac.delete_secgroup()
    
    #Now create a server 
    instance_ids = ac.create_server(ubuntu[region], "t2.micro", keyname=DEFAULT_KEYNAME)
    print "getting server IPs..."
    print get_server_ips(ac, instance_ids)

    
    #ac.list_security_groups()
