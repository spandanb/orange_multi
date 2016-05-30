from vino.servers import ServerManager
from docker import docker_api
from aws import ubuntu, AwsClient, get_server_ips
import pdb
from keys import sync_savi_key, sync_aws_key
import keys
import yaml
import sys
import os
import base64
import cPickle as pickle
import argparse

import aws

import pprint
import json

def node_name(ntype):
    """
    Return node_name, i.e. prefix + `n(ode)type`  
    ntype = [db | ws | gw | master | firewall ]
    """  
    prefix = os.environ["OS_USERNAME"] + "-vino-"  
    return prefix + ntype

def node_to_files(savi_ips,
                             nodes_human_file='./nodes',
                             wordpress_hosts='./wordpress/hosts', 
                             wordpress_run='./wordpress/run.sh'):
    """
    """

    #Write to the human-readable nodes file 
    with open(nodes_human_file, 'w') as file_desc:
        for name, ip in savi_ips.items():
            file_desc.write("{} : {}\n".format(name, ip))

    #Write to the wordpress hosts (inventory)
    with open(wordpress_hosts, 'w') as file_desc:
        file_desc.write("[master]\n")
        file_desc.write("{} ansible_user=ubuntu \n\n".format(savi_ips['master']))
        file_desc.write("[gateway]\n")
        file_desc.write("{} ansible_user=ubuntu \n\n".format(savi_ips['gw']))
        file_desc.write("[firewall]\n")
        file_desc.write("{} ansible_user=ubuntu \n\n".format(savi_ips['fw']))
        file_desc.write("[webserver]\n")
        file_desc.write("{} ansible_user=ubuntu\n".format(savi_ips['ws']))

    #wordpress run file    
    with open(wordpress_run, 'w') as file_desc:
        file_desc.write("#!/bin/bash\n")
        file_desc.write(
            'ansible-playbook -i hosts --extra-vars "master_ip={} webserver_ip={}" wordpress2.yaml\n'
            .format(savi_ips['master'], savi_ips['ws']))
    os.chmod(wordpress_run, 0774)


def get_clients():
    """
    Returns clients for AWS and SAVI
    """
    server_manager = ServerManager(os.environ["OS_USERNAME"],
                                   os.environ["OS_PASSWORD"],
                                   os.environ["OS_REGION_NAME"],
                                   os.environ["OS_TENANT_NAME"])
    aws = AwsClient()
    aws.set_region(os.environ['AWS_DEFAULT_REGION'])
    return server_manager, aws

def cleanup():
    """
    Delete any old AWS or SAVI servers
    """
    print "Cleaning up..."
    server_manager, aws = get_clients()

    #Delete any existing SAVI servers
    server_manager.delete_servers(name=node_name("master"))
    server_manager.delete_servers(name=node_name("gateway"))
    server_manager.delete_servers(name=node_name("webserver"))
    server_manager.delete_servers(name=node_name("firewall"))
    
    #delete all existing nodes
    aws.delete_all()


def vino_wordpress(savi_keyname="", aws_keyname=""):
    """
    Boots all the components for the Vino wordpress example
    """
    #Constants; move to a config file 
    SAVI_KEY_NAME=savi_keyname
    AWS_KEY_NAME=aws_keyname

    SAVI_KEY_NAME="span_key"
    AWS_KEY_NAME="spandan_key"

    server_manager, aws = get_clients()

    #Sync the key
    sync_savi_key(SAVI_KEY_NAME, server_manager) 
    server_ids = {}
    server_ips = {}

    ######################   SAVI #######################
    #creates master node on SAVI
    print "Booting {} on SAVI...".format(node_name("master"))
    server_ids["master"] = (server_manager.create_server(node_name("master"), "master-sdi.0.7", "m1.small", 
                    key_name=SAVI_KEY_NAME, secgroups=["default", "spandantb"]))

    #creates firewall node on SAVI
    print "Booting {} on SAVI...".format(node_name("firewall"))
    server_ids["fw"] = (server_manager.create_server(node_name("firewall"), "snort-image.2", "m1.small", 
                    key_name=SAVI_KEY_NAME, secgroups=["default", "spandantb"]))

    #creates gw node on AWS
    print "Booting {} on AWS...".format(node_name("gatway"))
    server_ids['gw'] = aws.create_server(ubuntu['us-east-1'], "t2.micro", keyname=AWS_KEY_NAME)

    #creates ws node on WS
    print "Booting {} on AWS...".format(node_name("webserver"))
    server_ids['ws'] = aws.create_server(ubuntu['us-east-1'], "t2.micro", keyname=AWS_KEY_NAME)

    server_manager.wait_until_sshable(server_ids["master"])
    server_manager.wait_until_sshable(server_ids["fw"])
    server_ips["master"] = server_manager.assign_floating_ip(server_ids["master"])
    server_ips["fw"] = server_manager.assign_floating_ip(server_ids["fw"])
    #TODO: setup wordpress secgroup
    server_ips["gw"], server_ips["ws"] = get_server_ips(aws, server_ids['gw'] + server_ids['ws']) 

    node_to_files(server_ips)

def main():
    "parse args and call vino_wordpress"
    parser = argparse.ArgumentParser(description='Vino command line interface')
    
    parser.add_argument('-a', '--aws-keyname', nargs=1, help="specify the AWS keyname")
    parser.add_argument('-s', '--savi-keyname', nargs=1, help="specify the SAVI keyname")
    parser.add_argument('-f', '--template-file', nargs=1, help="specify the template to use")
    parser.add_argument('-c', '--clean-up', action="store_true", help="Deletes any provisioned VMs")
    
    args = parser.parse_args()
    if args.clean_up:
        cleanup()
        return

    if not args.savi_keyname:
        print "Please Specify a valid SAVI keyname"
        parser.print_help()
        sys.exit(1)
    
    if not args.aws_keyname:
        print "Please Specify a valid AWS keyname"
        parser.print_help()
        sys.exit(1)
    
    vino_wordpress(aws_keyname=args.aws_keyname[0], savi_keyname=args.savi_keyname[0])

if __name__ == "__main__":
    #main()
    cleanup()
    vino_wordpress()
#    node_to_files({
#        'master': '10.12.1.23',
#        'ws': '10.12.1.37',
#        'fw': '10.12.1.42',
#        'gw': '10.12.1.41'})

