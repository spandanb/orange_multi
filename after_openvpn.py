import cPickle as pickle 
from remote import get_tun_ip 
import os

def create_worpress_run_file(nodes_pickle_file='./nodes.p',
                wordpress_hosts='./wordpress/hosts', 
                wordpress_run='./wordpress/wordpress_run.sh'):
    """
    Creates the wordpress_run.sh and hosts file
    """
    with open(nodes_pickle_file, 'rb') as file_desc:
        nodes = pickle.load(file_desc)

    #These are the openvpn files
    savi_ip = nodes['savi_ip']
    aws_ip = nodes['aws_ip']
    savi_vpn_ip = get_tun_ip(savi_ip, 'ubuntu')
    aws_vpn_ip = get_tun_ip(aws_ip, 'ubuntu') #Unused

    #Write to the wordpress hosts (inventory)
    with open(wordpress_hosts, 'w') as file_desc:
        file_desc.write("[database]\n")
        file_desc.write("{} ansible_user=ubuntu \n\n".format(savi_ip))
        file_desc.write("[webserver]\n")
        file_desc.write("{} ansible_user=ubuntu\n".format(aws_ip))

    #wordpress run file    
    with open(wordpress_run, 'w') as file_desc:
        file_desc.write("#!/bin/bash\n")
        file_desc.write('ansible-playbook -i hosts --extra-vars "db_ip={}" wordpress.yaml'.format(savi_vpn_ip))
    os.chmod(wordpress_run, 0774)


if __name__ == "__main__":
    create_worpress_run_file()





