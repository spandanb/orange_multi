
"""
Make sure $PYTHONPATH includes: 1)orange, orange/vino

"""
#import imp
#ServerManager = servers.ServerManager
from vino.servers import ServerManager
#from servers import ServerManager
from docker import docker_api

import yaml
import sys
import os
import base64

import aws

import pprint
import json

from utils import read_yaml

def printobj(obj):
    pprint.pprint(obj)
    #print json.dumps(obj, sort_keys=True, indent=4)


def main():
    """
    Reads topology file and creates required topology
    """
    topology = read_yaml(template_file='./topology2.yaml')
    server_manager = ServerManager(os.environ["OS_USERNAME"],
                                   os.environ["OS_PASSWORD"],
                                   os.environ["OS_REGION_NAME"],
                                   os.environ["OS_TENANT_NAME"])

    for resc in topology["Resources"]:
        if resc['type'] == 'virtual-machine':

            #required fields
            image = resc["image"]
            flavor = resc["flavor"]
            name = resc["name"]

            #Optional fields
            secgroups = resc.get("secgroups", [])
            key_name = resc.get("key_name")
            if "user_data" in resc:
                #must be base64 encoded
                user_data = base64.standard_b64encode(resc.get("user_data"))
            else:
                user_data = None

            provider = resc.get("provider", "savi")

            if provider == "savi":
                print "Booting VM {} on SAVI".format(name)
                #reqired now, but will be changed later
                region = resc["region"]
                tenant = resc["tenant"]
                print server_manager.create_server(name, image, flavor, region_name=region,
                    key_name=key_name, secgroups=secgroups, user_data=user_data)

            elif provider == "aws":
                print "Booting VM {} on AWS".format(name)
                aws.create_server(image, flavor, key_name=key_name, user_data=user_data)

        elif resc['type'] == 'container':
            provider = resc.get("provider", "savi")
            if provider == "native":
                image = resc['image']
                name = resc['name']
                print "Booting Container {} locally".format(name)
                docker_api.run_container(name=name, image=image)


        #printobj(resc)

def static_boot():
    """
    Boots a topology based on a static config
    """
    server_manager = ServerManager(os.environ["OS_USERNAME"],
                                   os.environ["OS_PASSWORD"],
                                   os.environ["OS_REGION_NAME"],
                                   os.environ["OS_TENANT_NAME"])

    #creates a savi node
    server_manager.create_server("span-vm-1", "Ubuntu1404-64", "m1.medium", 
                    key_name="key_spandan", secgroups=["default"])


    #create a aws node

if __name__ == "__main__":
    #main()
    static_boot()
