from utils import read_yaml, overlay_ip
import os

def create_hosts_files():
    wordpress_hosts = "wordpress/hosts"
    wordpress_run   = "wordpress/configure_wordpress.sh"
    master_hosts    = "master/hosts"
    master_run      = "master/run.sh"
    nodes_file      = "nodes.yaml"

    print "Creating host files..."

    nodes = read_yaml(filepath=nodes_file)

    master_ip    = next((node['ip'] for node in nodes if node['role'] == 'master'), None)
    webserver_ip = next((node['ip'] for node in nodes if node['role'] == 'webserver'), None)
    gateway_ip = next((node['ip'] for node in nodes if node['role'] == 'gateway'), None)

    #master hosts file
    with open(master_hosts, 'w') as fileptr:
        fileptr.write("[master]\n")
        fileptr.write("{} ansible_user=ubuntu \n\n".format(master_ip))

    #master run file
    with open(master_run , 'w') as fileptr:
        fileptr.write("#!/bin/bash\n")
        fileptr.write(
            'ansible-playbook -i hosts --extra-vars "master_ip={}" master.yaml\n'
            .format(master_ip))
    os.chmod(master_run, 0774)

    #wordpress hosts file
    with open(wordpress_hosts, 'w') as fileptr:
        for role in ["gateway", "firewall", "webserver"]:
            fileptr.write("[{}]\n".format(role))
            matches = filter(lambda node: node["role"] == role, nodes)

            for node in matches:
                fileptr.write("{} ansible_user=ubuntu \n\n".format(node['ip']))

    #wordpress run file
    with open(wordpress_run, 'w') as fileptr:
        fileptr.write("#!/bin/bash\n")
        fileptr.write(
            'ansible-playbook -i hosts --extra-vars "webserver_ip={} gateway_ip={}" wordpress.yaml\n'
            .format(overlay_ip(webserver_ip), overlay_ip(gateway_ip)))
    os.chmod(wordpress_run, 0774)


if __name__ == "__main__":
    create_hosts_files()
