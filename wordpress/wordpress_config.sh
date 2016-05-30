#!/bin/bash
ansible-playbook -i hosts --extra-vars "master_ip=142.150.208.237 webserver_ip=54.84.183.176" wordpress2.yaml
