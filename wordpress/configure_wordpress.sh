#!/bin/bash
ansible-playbook -i hosts --extra-vars "master_ip=142.150.208.226 webserver_ip=54.175.81.21" wordpress2.yaml
