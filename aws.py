"""
https://github.com/boto/boto3#quick-start

Security credentials:
http://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html

Documentation
https://boto3.readthedocs.org/en/latest/
http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.run_instances
"""

import boto3
import pdb
import os
from keys import check_and_create_privkey, get_pubkey, get_pubkey_fingerprint

##S3
#s3 = boto3.resource('s3')
#for bucket in s3.buckets.all():
#        print(bucket.name)

def sync_local_key(new_keyname, aws_client):
    """
    Checks whether local RSA priv key exists and gets name
    of AWS key that corresponds to this. 
    If it does not exist locally, a new key is created. 
    If it does, but does not match with an
    AWS key, overrides AWS key info.

    Arguments:-
        new_keyname- the name to use for a new key
        aws_client- the AWS Client object
    """
    #Check if local SSH key exists; if not create it
    check_and_create_privkey()
    #get public key fingerprint
    fingerprint = get_pubkey_fingerprint()
    #find corresponding key's name    
    #NOTE: we could alternatively hardcode AWS keyname
    keyname = aws_client.get_keyname(fingerprint)
    #If no match key found on AWS, create a new key
    if not keyname:
        #delete key on AWS, with default name
        if aws_client.check_keyname(new_keyname):
            aws_client.remove_keypair(new_keyname)
        #Create new key
        aws_client.create_keypair(new_keyname, get_pubkey())
        keyname = new_keyname

    return keyname 

class AwsClient(object):
    """
    A class for a AWS Client
    """
    def __init__(self):
        self.aws_access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
        self.aws_secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]
        self.set_region(os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
        
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

    def create_server(self, image, flavor, keyname='', user_data=''):
        """
        Creates a server 
        """
        resp = self.ec2_client.run_instances(
                ImageId=image,
                InstanceType=flavor,
                MinCount=1,
                MaxCount=1,
                KeyName = keyname,
                UserData = user_data,
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


if __name__ == "__main__":
    DEFAULT_KEYNAME="spandan_key"

    #Image id's for same image vary by location
    #Ubuntu 14.04
    ubuntu = {
        'us-east-1':'ami-fce3c696', #N. Virginia
        'us-west-1':'ami-06116566', #N. California
        'us-west-2':'ami-9abea4fb', #Oregon
    }
    
    ac = AwsClient()
    #region is set through env var, but explicitly set it again
    region = 'us-east-1'
    ac.set_region(region)

    #First, let's handle the keys
    sync_local_key(DEFAULT_KEYNAME, ac)

    #Now create a server 
    ac.create_server(ubuntu[region], "t2.micro", keyname="spandan_key")

    #List the servers
    ac.list_servers()
