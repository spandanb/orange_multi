
"""
Parses topology and instantiates nodes.
"""

from clients import get_aws_client, get_savi_client
from aws import AwsClient, get_server_ips, ubuntu
import sys, os, pdb, argparse
import base64
import cPickle as pickle
import pprint, json
from keys import sync_savi_key, sync_aws_key
from utils import read_yaml, write_yaml, create_and_raise

##############################################
################    CONSTS    ################
##############################################
NODESFILE="./nodes.yaml"


def resolve_special(form):
    """
    There are some special functions that can 
    be used in template files. An example is
    "aws::get_image_id(`image_name`)".
    These need to be identified and resolved.
    These forms can't be arbitrarily nested
    """
    form_arr = form.split("::")
    if len(form_arr) == 1: return form_arr[0]

    namespace, method = form_arr
    method, args = method.split("(") #split on left-paren
    args = args.replace(")", "") #remove right paren
    args = args.split(",")

    if namespace == "aws":
        if method == "get_image_id":
            return ubuntu[os.environ["AWS_DEFAULT_REGION"]]
        else:
            print "Method {} not found".format(method)
    else:
        print "Namespace {} not found".format(namespace)
   


def parse_node(resc):
    """
    Parse a node object.
    There are a few special cases to handle
    If optional fields are not specified, then behaviod is undef

    Currently only handles virtual-machines
    """
    #TODO: Error checking; 

    node = {}
    #required fields
    node["image"]  = resolve_special(resc["image"])
    node["flavor"] = resc["flavor"]
    node["name"]   = resc["name"]
    node["type"]   = resc["type"]

    #Optional Fields
    node["secgroups"] = resc.get("security-groups", [])
    node["key_name"]  = resc.get("key_name")
    node["region"]    = resc.get("region", "CORE")
    node["role"]      = resc.get("role") #TODO: should be a list
    
    if resc.get("provider", "savi") == "savi":
        node["provider"]  = "savi" 
        node["tenant"]    = resc["tenant"]
        node["floating_ip"] = resc.get("assign_floating_ip", False)
    else:
        node["provider"] = resc.get("provider")
        if node["provider"] != "aws":
            create_and_raise("InvalidProviderException", "Provider must be 'savi' or 'aws'") 

    #TODO: check whether need to base64 encode, AWS docs say so, but works w/o
    node["user_data"] = resc.get("user_data")

    return node

def parse_template(template):
    """
    Reads topology file and creates required topology
    """
    topology = read_yaml(filepath=template)

    #Parse the nodes
    nodes = [parse_node(resc) for resc in topology["Nodes"]]
    return nodes

def instantiate_nodes(nodes):
    """
    Instantiate the nodes
    """
    aws =  get_aws_client()
    savi = get_savi_client()  
    
    savi_key_synced = False
    aws_key_synced = False

    #Instantiation Loop
    for node in nodes:
        if node["provider"] == "savi":
            if not savi_key_synced:
                sync_savi_key(node["key_name"], savi)
                savi_key_synced = True
            
            print "Booting {} in SAVI".format(node["name"])
            node["id"] = savi.create_server(node['name'], node['image'], node['flavor'], secgroups=node["secgroups"], key_name=node["key_name"])

        else: #aws
            if not aws_key_synced:
                sync_aws_key(node["key_name"], aws)
                aws_key_synced = True

            print "Booting {} in AWS".format(node["name"])
            node["id"] = aws.create_server(node["image"], node["flavor"], keyname=node["key_name"], user_data=node["user_data"])[0]

    #Waiting-until-built loop
    for node in nodes:
        if node["provider"] == "savi":
            node_ip = savi.wait_until_sshable(node["id"])
            #The property 'ip' has value of floating-ip if defined, else ip
            if node["floating_ip"]:
                print "Requesting floating IP for {}".format(node["id"]) 
                node["ip"] = savi.assign_floating_ip(node["id"])
                node["int_ip"] = node_ip
            else:
                node["ip"] = node_ip
        else: #aws
            node["ip"] = get_server_ips(aws, [node["id"]])[0]

    #Print some info 
    for node in nodes:
        print "{}({}) is available at {}".format(node["name"], node["id"], node["ip"])

    return nodes

def write_results(nodes):
    """
    Writes the results to file
    """
    write_yaml(nodes, filepath=NODESFILE) 
            
def cleanup():
    """
    Reads last created topology and deletes it
    """
    aws =  get_aws_client()
    savi = get_savi_client()  
   
    print "Deleting on AWS..."
    aws.delete_all()

    nodes = read_yaml(filepath=NODESFILE)
    print "Deleting on SAVI..."
    for node in nodes:
        if node["provider"] == "savi":
            print "Deleting {} ({})".format(node["name"], node["id"])
            try:
                savi.delete_servers(server_id=node["id"])
            except ValueError as err:
                print "Warning: nodes file ({}) is out of sync".format(NODESFILE)
    
    #Nuke the file
    with open(NODESFILE, 'w') as fileptr:
        fileptr.write('')

def parse_args():
    """
    Parse arguments and call yaml parser
    """
    parser = argparse.ArgumentParser(description='Vino command line interface')
    
    parser.add_argument('-f', '--template-file', nargs=1, help="specify the template to use")
    parser.add_argument('-c', '--clean-up', action="store_true", help="Deletes any provisioned topologies")
    
    args = parser.parse_args()

    if args.clean_up:  
        cleanup()
    elif args.template_file:
        template = args.template_file[0]
        nodes = parse_template(template)
        nodes = instantiate_nodes(nodes)
        write_results(nodes)
    else:
        parser.print_help()
        create_and_raise("TemplateNotSpecifiedException", "Please specify a template file")
        
if __name__ == "__main__":
    #TODO: creating new secgroup
    parse_args()
