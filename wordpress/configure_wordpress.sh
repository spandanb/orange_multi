#!/bin/bash
ansible-playbook -i hosts --extra-vars "webserver_ip=54.165.80.166" wordpress3.yaml
