from oauth2client.client import GoogleCredentials
from googleapiclient import discovery
import pdb, os
from utils import keys 
from utils.utils import SleepFSM, create_and_raise
import random
import paramiko
from socket import error as socket_error

#Prereq: 1) gcloud init
#enable compute api through console

#See https://cloud.google.com/compute/docs/tutorials/python-guide

#See: https://github.com/apache/libcloud/blob/trunk/libcloud/compute/drivers/gce.py#L631
#for how libcloud is handling ops like add key

class GceClient(object):
    
    def __init__(self, region=None, zone=None, project=None):
        self.credentials = GoogleCredentials.get_application_default()
        self.compute = discovery.build('compute', 'v1', credentials=self.credentials)
        
        if region:  self.set_region(region)
        if zone:    self.set_zone(zone)
        if project: self.set_project(project)

    def set_region(self, region):
        self.region=region

    def set_zone(self, zone):
        self.zone = zone

    def set_project(self, project):
        self.project = project

    def get_zones(self):
        """
        Returns all the zones in this project
        """
        return gce.compute.zones().list(project=self.project).execute()
        
    def list_servers(self):
        """
        Returns all the servers for the given project and zone
        """
        resp = self.compute.instances().list(project=self.project, zone=self.zone).execute()       
        if 'items' not in resp: 
            resp['items'] = []
        return resp

    def get_image(self, imgproj='ubuntu-os-cloud', family='ubuntu-1404-lts'):
        """
        Get image based on image project and family 
        """
        #See the following for image project and family 
        #https://cloud.google.com/compute/docs/images#os-compute-support
        image_response = self.compute.images().getFromFamily(
            project=imgproj, family=family).execute()
        return image_response

    def get_flavor(self): 
        #See https://cloud.google.com/compute/docs/machine-types
        return "n1-standard-1"

    def create_server(self, name, image, flavor, startup_script_path='./startup-script.sh'):
        """
        Arguments:- 
            name: name of instance
            image: image_response object as returned from `get_image` method
            flavor: 
        """
        source_disk_image = image['selfLink']
    
        # Configure the machine
        machine_type = "zones/{}/machineTypes/{}".format(zone, flavor)
        startup_script = open(
            os.path.join(
                os.path.dirname(__file__), startup_script_path), 'r').read()
    
        config = {
            'name': name,
            'machineType': machine_type,
    
            # Specify the boot disk and the image to use as a source.
            'disks': [
                {
                    'boot': True,
                    'autoDelete': True,
                    'initializeParams': {
                        'sourceImage': source_disk_image,
                    }
                }
            ],
    
            # Specify a network interface with NAT to access the public
            # internet.
            'networkInterfaces': [{
                'network': 'global/networks/default',
                'accessConfigs': [
                    {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
                ]
            }],
    
            # Metadata is readable from the instance and allows you to
            # pass configuration from deployment scripts to instances.
            'metadata': {
                'items': [{
                    # Startup script is automatically executed by the
                    # instance upon startup.
                    'key': 'startup-script',
                    'value': startup_script
                }]
            }
        }
    
        return self.compute.instances().insert(
            project=self.project,
            zone=self.zone,
            body=config).execute() 


    def get_server_ip(self, operation=None, name=None, username="ubuntu"):
        """
        Arguments:-
            operation: name of operation
            name: name of instance
        """
        
        sleep = SleepFSM()
        sleep.init(max_tries=7)
        
        #op done loop
        while True:
            result = self.compute.zoneOperations().get(
                project=self.project,
                zone=self.zone,
                operation=operation).execute()
            if result['status'] != 'PENDING':
                break
            print "Op Pending; sleeping ..."
            sleep()

        server = self.compute.instances()\
                     .get(zone=self.zone, project=self.project, instance=name).execute()
        server_ip = server['networkInterfaces'][0]['accessConfigs'][0]['natIP']
        
        #server is ping-able loop
        sshClient = paramiko.SSHClient()
        sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sleep.init(max_tries=7) #re-initialize sleep FSM
        while True:
            try:
                print "Trying ssh {}@{}".format(username, server_ip) 
                sshClient.connect(server_ip, username=username)
                break
            except socket_error:
                print "SSH failed; sleeping ..."
            sleep()

        return server_ip

    def delete_instance(self, name):
        "Delete instance by name"
        return self.compute.instances().delete(
                project=self.project,
                zone=self.zone,
                instance=name).execute()

    def delete_all(self):
        """
        Delete all instances
        """
        servers = self.list_servers()['items']
        for server in servers:
            print "deleting {}".format(server['name'])
            self.delete_instance(server['name']) 

    def _get_project(self):
        """
        Returns data about the project, including commonInstanceMetadata
        """
        resp = self.compute.projects().get(project=self.project).execute()
        return resp

    def get_keys(self):
        """
        Return list of key data objects from project commonInstanceMetadata
        """
        metadata = self._get_project()['commonInstanceMetadata']
        if 'items' not in metadata:
            keys = []
        else:
            #metadata['items'] is [{'key': ..., 'value': ...}]
            keys = [item['value'] for item in metadata['items'] if item['key'] == 'sshKeys']
        return keys

    def add_key(self, pubkey):
        """
        add pubkey to remote server
        """
        fingerprint = self._get_project()['commonInstanceMetadata']['fingerprint']
        metadata = [{'key':'sshKeys', 'value': pubkey}]
        body = {'fingerprint': fingerprint, 'items': metadata}
        resp = self.compute.projects()\
                .setCommonInstanceMetadata(project=self.project, body=body).execute()
        return resp

    def sync_gce_key(self):
        """
        synchronizes local key with GCE server.
        """
        #Check if local SSH key exists; if not create it
        keys.check_and_create_privkey()

        #check if the local key matches any remote key
        pubkey = keys.get_pubkey()
        for key in self.get_keys():
            if key == pubkey: 
                break
        else:
            #add key
            self.add_key(pubkey)

    
if  __name__ == "__main__":
    project ='project2-1345' 
    region='us-central1'
    zone='us-central1-a'
    
    gce = GceClient(project=project, region=region, zone=zone)
    
    #sync local key with remote; key pairs apply at project level
    #gce.sync_gce_key()

    print gce.list_servers()
    
    gce.delete_all()

    #Boot a VM
#    ubuntu = gce.get_image()
#    std_flavor = gce.get_flavor()
#    server_name = "span-server-{}".format(random.randint(0, 100000))
#    print "Booting {}".format(server_name)
#    resp = gce.create_server(server_name, ubuntu, std_flavor)
#    gce.get_server_ip(operation=resp['name'], name=server_name)

