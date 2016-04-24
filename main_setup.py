"""
Make sure $PYTHONPATH includes: 1)orange, orange/vino
"""
from vino.servers import ServerManager
from ansible_wrapper.ansible_wrapper import Runner
from utils import read_yaml
import pdb
import os

def setup_substrate():
    """
    Sets up the substrate
    """
    #Constants
    SUBSTRATE_SPEC = './substrate.yaml'
    IMAGE="TBonTB_C4"

    template = read_yaml(template_file=SUBSTRATE_SPEC)
    server_manager = ServerManager(os.environ["OS_USERNAME"],
                                   os.environ["OS_PASSWORD"],
                                   os.environ["OS_REGION_NAME"],
                                   os.environ["OS_TENANT_NAME"])

    #First boot the controller
    contr_flavor = template['Cloud'].get('controller_flavor', 'm1.medium')
    contr_id = server_manager.create_server('span-contr-1', IMAGE, contr_flavor,
        key_name='key_spandan', secgroups=['default','spandantb'])

    #Next boot the agents
    agent_flavor = template['Cloud'].get('agent_flavor', 'm1.medium')
    agent_count = template['Cloud'].get('agent_count', 1)
    agent_ids = []
    for i in range(agent_count):
        agent_ids.append(server_manager.create_server('span-agent-1', IMAGE, agent_flavor,
            key_name='key_spandan', secgroups=['default','spandantb']))

    contr_ip = server_manager.wait_until_sshable(contr_id)
    agent_ips = [server_manager.wait_until_sshable(agent_id) for agent_id in agent_ids ]

    return {'contr_ip':contr_ip, 'agents_ips':agent_ip}

def setup_nodes(ip_addrs):
    #Setup TB on TB node
    runner = Runner(
        hosts={'controller': [ip_addrs['contr_ip']], 'agents':ip_addrs['agents_ips']},
        playbook='../full_node/TBonTB_C4.yml', #path to playbook
        private_key_file='~/.ssh/id_rsa',
        run_data={'user_id':''}, #what is this for?
        become_pass='ubuntu',
        verbosity=1
    )
    stats = runner.run()

    #Setup docker
    runner = Runner(
        hosts={'controller': [ip_addrs['contr_ip']], 'agents':ip_addrs['agents_ips']},
        playbook='../docker/ansible/docker_setup.yaml',
        private_key_file='~/.ssh/id_rsa',
        run_data={'user_id':''},
        become_pass='ubuntu',
        verbosity=1
    )
    stats = runner.run()


if __name__ == "__main__":
    #First boot the VMs
    ip_addrs = setup_substrate()

    #Next run ansible playbook to configure SAVI Openstack
    setup_nodes(ip_addrs)
