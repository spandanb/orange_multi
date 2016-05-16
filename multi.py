
"""
Make sure $PYTHONPATH includes: 1)orange, orange/vino

"""
from vino.servers import ServerManager
from docker import docker_api
from aws import ubuntu, AwsClient, get_server_ips
import pdb
from keys import sync_savi_key, sync_aws_key
import yaml
import sys
import os
import base64
import cPickle as pickle

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

def nodes_to_files(aws_ip='', savi_ip='', 
                    nodes_file='./nodes', 
                    nodes_pickle_file='./nodes.p',
                    openvpn_hosts='./openvpn/hosts', 
                    openvpn_run='./openvpn/openvpn_run.sh',
                    ):

    """
    Creates the various inventory and run.sh files
    """
    #Write to the nodes file 
    with open(nodes_file, 'w') as file_desc:
        file_desc.write("{}\n".format(aws_ip))
        file_desc.write("{}\n".format(savi_ip))

    with open(nodes_pickle_file, 'wb') as file_desc:
        pickle.dump({'aws_ip': aws_ip, 'savi_ip': savi_ip}, file_desc)

    #Write to the openvpn hosts (inventory)
    with open(openvpn_hosts, 'w') as file_desc:
        file_desc.write("[server]\n")
        file_desc.write("{} ansible_user=ubuntu \n\n".format(aws_ip))
        file_desc.write("[client]\n")
        file_desc.write("{} ansible_user=ubuntu\n".format(savi_ip))
        
    #openvpn run file    
    with open(openvpn_run, 'w') as file_desc:
        file_desc.write("#!/bin/bash\n")
        file_desc.write('ansible-playbook -i hosts --extra-vars "server_ip={}" openvpn.yaml'.format(aws_ip))
    os.chmod(openvpn_run, 0777)



def static_boot():
    """
    Boots a topology based on a static config
    """
    server_manager = ServerManager(os.environ["OS_USERNAME"],
                                   os.environ["OS_PASSWORD"],
                                   os.environ["OS_REGION_NAME"],
                                   os.environ["OS_TENANT_NAME"])

    sync_savi_key("span_key", server_manager) 
    savi_node_name = "span-vm-1"

    server_manager.delete_servers(name=savi_node_name)
    #creates a savi node
    print "Booting VM on SAVI..."
    server_id = server_manager.create_server(savi_node_name, "Ubuntu1404-64", "m1.large", 
                    key_name="span_key", secgroups=["default", "spandantb"])

    #create a aws node
    aws = AwsClient()
    aws.set_region('us-east-1')
    #delete all existing nodes
    aws.delete_all()
    sync_aws_key("spandan_key", aws)
    print "Booting VM on AWS..."
    aws_ids = aws.create_server(ubuntu['us-east-1'], "t2.micro", keyname="spandan_key")

    #IP addr     
    savi_ip = server_manager.wait_until_sshable(server_id)
    print "SAVI node is available at {}".format(savi_ip)
    
    #list of ips
    aws_ips = get_server_ips(aws, aws_ids)
    print "AWS node is available at {}".format(aws_ips[0])

    #Write the node addresses to file
    nodes_to_files(aws_ip=aws_ips[0], savi_ip=savi_ip)
    
def clean_up():
    server_manager = ServerManager(os.environ["OS_USERNAME"],
                                   os.environ["OS_PASSWORD"],
                                   os.environ["OS_REGION_NAME"],
                                   os.environ["OS_TENANT_NAME"])

    savi_node_name = "span-vm-1"

    server_manager.delete_servers(name=savi_node_name)

    aws = AwsClient()
    aws.set_region('us-east-1')
    #delete all existing nodes
    aws.delete_all()


if __name__ == "__main__":
    #main()
    #static_boot()
    clean_up()
