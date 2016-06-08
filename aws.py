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

    def create_server(self, image, flavor, keyname='', user_data='', secgroups=["default"]):
        """
        Creates a server 
        """
        vpc_id = self.get_vpc_id()
        resp = self.ec2_client.describe_subnets(Filters=[{'Name':'vpc-id', 'Values':[vpc_id]}])
        subnet_id = resp['Subnets'][0]['SubnetId']

        secgroup_ids = [self.get_secgroup(name, get_id=True) for name in secgroups]
            
        net_ifaces=[{'SubnetId': subnet_id, 'DeviceIndex':0, 'AssociatePublicIpAddress':True, 'Groups':secgroup_ids}]

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
    
    def delete_servers(self, server_ids):
        """
        Deletes the servers referenced by
        server_ids
        """
        self.ec2_client.terminate_instances(InstanceIds=server_ids)


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

    def _rule_matches(self, rule, candidate):
        """
        Check if given rule matches candidate (rule).
        """
        if rule['from'] != candidate['FromPort']:
            return False
        if rule['to'] != candidate['ToPort']:
            return False
        if rule['protocol'] != candidate['IpProtocol']:
            return False
        if sorted([{'CidrIp': rng} for rng in rule['allowed']]) != sorted(candidate['IpRanges']):
            return False
        return True

    def _all_rules_match(self, rules, existing):
        """
        Check if all `rules` is a subset of`existing`.
        Arguments:- 
            rules:- list of new security rules
            existing:- list of exsiting security rules
        """
        for rule in rules:
            for candidate in existing:
                if self._rule_matches(rule, candidate):
                    break
            else:
               #For loop continued w/o break => mismatch
               return False
        return True

                    
    def create_secgroup(self, group_name, rules, description=" "):
        """
        Creates a secgroup and returns its id.
        If a secgroup with the same name exists (group names are unique
        in a VPC), checks whether the rules match. If they don't match
        raises an exception. 

        Rules should be the following format:
        rules = {'ingress': [
                              {'protocol': 'tcp', 'from': 22, 'to':22, 'allowed': ['0.0.0.0/0']  }
                            ], 
                 'egress': []
                 }
        """

        #secgroup names are unique per VPC
        resp = self.ec2_client.describe_security_groups(Filters=[{'Name':'group-name', 'Values': [group_name]}])
        
        if len(resp['SecurityGroups']) > 0:
            #Check if the rules matches
            secgroup = resp['SecurityGroups'][0]

            #Compare ingress and egress rules
            match = self._all_rules_match(rules["ingress"], secgroup["IpPermissions"]) and \
                        self._all_rules_match(rules["egress"], secgroup["IpPermissionsEgress"])
            if match:
                return secgroup['GroupId']
            else:
                create_and_raise("SecurityRuleMismatchException", 
                                 "Security group with name {} exists with different rules".format(group_name))


        else: 
            #create the Secgroup
            vpc_id = self.get_vpc_id()
            resp = self.ec2_client.create_security_group(GroupName=group_name, 
                                                         Description=description,
                                                         VpcId=vpc_id)
            secgroup_id = resp['GroupId']

            #Add the ingress rules
            rules_list = []
            for rule in rules["ingress"]:
                to_add = {"IpProtocol" : rule["protocol"], 
                          "FromPort"   : rule["from"], 
                          "ToPort"     : rule["to"], 
                          "IpRanges"   : [{"CidrIp": rng} for rng in rule["allowed"]]}
                rules_list.append(to_add)

            if rules_list:
                self.ec2_client.authorize_security_group_ingress(GroupId=secgroup_id, IpPermissions=rules_list)
    
            #Add the egress rules
            rules_list = []
            for rule in rules["egress"]:
                to_add = {"IpProtocol" : rule["protocol"], 
                          "FromPort"   : rule["from"], 
                          "ToPort"     : rule["to"], 
                          "IpRanges"   : [{"CidrIp": rng} for rng in rule["allowed"]]}
                rules_list.append(to_add)

            if rules_list:
                #self.ec2_client.authorize_security_group_egress(GroupId=secgroup_id, IpPermissions=rules_list)
                #NOTE: This maybe a boto bug since the docs show the param name is 'IpPermissions', not 'ipPermissions'
                self.ec2_client.authorize_security_group_egress(GroupId=secgroup_id, ipPermissions=rules_list)


    def get_secgroup(self, group_name, get_id=False):
        """
        Returns secgroup object with matching name. 
        If does not exist, returns None

        Arguments:-
            group_name: name of group to fetch
            get_id: if True only return id, else return the whole group obj
        """

        resp = self.ec2_client.describe_security_groups(Filters=[{'Name':'group-name', 'Values': [group_name]}])
        
        if len(resp['SecurityGroups']) > 0: 
            if get_id:
                return resp['SecurityGroups'][0]['GroupId'] 
            else:
                return resp['SecurityGroups'][0]
        else:
            return None

    def delete_secgroup(self, secgroup_id):
        """
        Removes the specified secgroup
        """
        self.ec2_client.delete_security_group(GroupId=secgroup_id)
        
    def get_server_ips(self, instance_ids, username="ubuntu"):
        """
        blocking method that waits until all server are ready and 
        are SSHable 
        """
        sleep = SleepFSM()
        sleep.init(max_tries=7)
        
        server_ips = []
    
        running = self.list_running_servers(instance_ids)
        while len(running) != len(instance_ids):
            running = self.list_running_servers(instance_ids)
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
                        print "Trying ssh {}@{}".format(username, node['PublicIpAddress']) #PublicDnsName
                        sshClient.connect(node['PublicIpAddress'], username=username)
                        server_ips.append(node['PublicIpAddress'])
                        break
                    except socket_error:
                        print "SSH failed...."
                    sleep()
        return server_ips

if __name__ == "__main__":
    DEFAULT_KEYNAME="spandan_key"

    aws = AwsClient()
    #region is set through env var, but explicitly set it again
    region = 'us-east-1'
    aws.set_region(region)
    
    #List the servers
    #print "Listing servers...."
    #print aws.list_servers()

    #First, let's handle the keys
    #sync_aws_key(DEFAULT_KEYNAME, aws)
    #aws.delete_all()

    #aws.delete_secgroup(secgroup_id)
    print aws.get_secgroup("wordpress-vino")

    #First check if secgroup exists
    #If not check and add it 
    #Then boot servers
    
    #instance_ids = aws.create_server("ami-df24d9b2", "t2.micro", keyname=DEFAULT_KEYNAME)
    #print "getting server IPs..."
    #print aws.get_server_ips(instance_ids)

    #print aws.list_security_groups()
