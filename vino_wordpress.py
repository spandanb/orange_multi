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

def node_name(ntype, prefix="span-vino-"):
    """
    Return node_name, i.e. cat prefix + `n(ode)type`  
    ntype = [db | ws | gw | master | firewall ]
    """
    return prefix + ntype

def nodes_to_files(aws_ips, savi_ips, 
                    nodes_file='./nodes', 
                    nodes_pickle_file='./nodes.p',
                    openvpn_hosts='./openvpn/hosts', 
                    openvpn_run='./openvpn/openvpn_run.sh',
                    ):

    """
    Creates the various inventory and run.sh files
    """

    aws_ip = aws_ips["ws"]

    #Write to the nodes file 
    with open(nodes_file, 'w') as file_desc:
        for name, ip in aws_ips.items():
            file_desc.write("{}:{}\n".format(name, ip))
        
        for name, ip in savi_ips.items():
            file_desc.write("{}:{}\n".format(name, ip))

    with open(nodes_pickle_file, 'wb') as file_desc:
        pickle.dump({"savi_ips": savi_ips, "aws_ips": aws_ips}, file_desc)

    #Write to the openvpn hosts (inventory)
    with open(openvpn_hosts, 'w') as file_desc:
        file_desc.write("[server]\n")
        file_desc.write("{} ansible_user=ubuntu \n\n".format(aws_ip))

        file_desc.write("[client1]\n")
        file_desc.write("{} ansible_user=ubuntu \n".format(savi_ips["master"]))
        file_desc.write("[client2]\n")
        file_desc.write("{} ansible_user=ubuntu \n".format(savi_ips["db"]))
        file_desc.write("[client3]\n")
        file_desc.write("{} ansible_user=ubuntu \n".format(savi_ips["gw"]))
        file_desc.write("[client4]\n")
        file_desc.write("{} ansible_user=ubuntu \n".format(savi_ips["firewall"]))
        
    #openvpn run file    
    with open(openvpn_run, 'w') as file_desc:
        file_desc.write("#!/bin/bash\n")
        file_desc.write('ansible-playbook -i hosts --extra-vars "server_ip={}" openvpn.yaml -f 10'.format(aws_ip))
    os.chmod(openvpn_run, 0777)

def cleanup():
    """
    Delete any old AWS or SAVI servers
    """
    server_manager = ServerManager(os.environ["OS_USERNAME"],
                                   os.environ["OS_PASSWORD"],
                                   os.environ["OS_REGION_NAME"],
                                   os.environ["OS_TENANT_NAME"])
    #Delete any existing SAVI servers
    server_manager.delete_servers(name=node_name("master"))
    server_manager.delete_servers(name=node_name("gw"))
    server_manager.delete_servers(name=node_name("db"))
    server_manager.delete_servers(name=node_name("firewall"))
    
    aws = AwsClient()
    aws.set_region('us-east-1')

    #delete all existing nodes
    aws.delete_all()

    return server_manager, aws


def vino_wordpress():
    """
    Boots all the components for the Vino wordpress example
    """
    #Constants; move to a config file 
    SAVI_KEY_NAME="span_key"
    AWS_KEY_NAME="spandan_key"

    server_manager, aws = cleanup()

    #Sync the key
    sync_savi_key(SAVI_KEY_NAME, server_manager) 
    server_ids = {}
    server_ips = {}

    ######################   SAVI #######################
    #creates master node on SAVI
    print "Booting {} on SAVI...".format(node_name("master"))
    server_ids["master"] = (server_manager.create_server(node_name("master"), "master-sdi.0.7", "m1.small", 
                    key_name=SAVI_KEY_NAME, secgroups=["default", "spandantb"]))

    #creates gw node on SAVI
    print "Booting {} on SAVI...".format(node_name("gw"))
    server_ids["gw"] = (server_manager.create_server(node_name("gw"), "Ubuntu64-3-OVS", "m1.small", 
                    key_name=SAVI_KEY_NAME, secgroups=["default", "spandantb"]))

    #creates firewall node on SAVI
    print "Booting {} on SAVI...".format(node_name("firewall"))
    server_ids["firewall"] = (server_manager.create_server(node_name("firewall"), "snort-image.2", "m1.small", 
                    key_name=SAVI_KEY_NAME, secgroups=["default", "spandantb"]))
    
    #creates db node on SAVI
    print "Booting {} on SAVI...".format(node_name("db"))
    server_ids["db"] = (server_manager.create_server(node_name("db"), "Ubuntu64-mysql-OVS", "m1.small", 
                    key_name=SAVI_KEY_NAME, secgroups=["default", "spandantb"]))

    ######################   AWS #######################
    sync_aws_key("spandan_key", aws)
    print "Booting {} on AWS...".format(node_name("ws"))
    aws_ids = aws.create_server(ubuntu['us-east-1'], "t2.micro", keyname=AWS_KEY_NAME)

    #Get IP addr     
    server_ips["master"] = server_manager.wait_until_sshable(server_ids["master"])
    server_ips["gw"] = server_manager.wait_until_sshable(server_ids["gw"])
    server_ips["firewall"] = server_manager.wait_until_sshable(server_ids["firewall"])
    server_ips["db"] = server_manager.wait_until_sshable(server_ids["db"])
    
    #list of ips
    aws_ips = {"ws": get_server_ips(aws, aws_ids)[0]}
    #server_ips["ws"] = aws_ips[0]

    #Write the node addresses to file
    nodes_to_files(aws_ips, server_ips)

if __name__ == "__main__":
    vino_wordpress()
    #cleanup()
