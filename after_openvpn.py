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
    savi_ips = nodes['savi_ips']
    aws_ips = nodes['aws_ips']

    for name, ip in savi_ips.items():
        savi_ips[name] = {'ip': ip, 'tun_ip': get_tun_ip(ip, 'ubuntu')}

    aws_ips['ws'] = {'ip': aws_ips['ws'], get_tun_ip(aws_ips['ws'], 'ubuntu')}

    #Write to the wordpress hosts (inventory)
    with open(wordpress_hosts, 'w') as file_desc:
        file_desc.write("[database]\n")
        file_desc.write("{} ansible_user=ubuntu \n\n".format(savi_ips['db']['ip']))
        file_desc.write("[gateway]\n")
        file_desc.write("{} ansible_user=ubuntu \n\n".format(savi_ips['gw']['ip']))
        file_desc.write("[firewall]\n")
        file_desc.write("{} ansible_user=ubuntu \n\n".format(savi_ips['firewall']['ip']))
        file_desc.write("[webserver]\n")
        file_desc.write("{} ansible_user=ubuntu\n".format(aws_ips['ws']['ip']))

    #wordpress run file    
    with open(wordpress_run, 'w') as file_desc:
        file_desc.write("#!/bin/bash\n")
        file_desc.write('ansible-playbook -i hosts --extra-vars "db_ip={};master_tun_ip={}" wordpress.yaml -f 10'.format(savi_ips['db']['ip'], savi_ips['master']['tun_ip']))
    os.chmod(wordpress_run, 0774)


if __name__ == "__main__":
    create_worpress_run_file()





