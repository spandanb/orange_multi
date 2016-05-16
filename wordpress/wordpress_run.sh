#!/bin/bash
ansible-playbook -i hosts --extra-vars "db_ip=10.8.0.6" wordpress.yaml