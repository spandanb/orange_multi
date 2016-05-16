#!/bin/bash

#NOTE: Port 3306 should be open on 

ansible-playbook -i hosts --extra-vars "db_ip=ec2-54-208-117-50.compute-1.amazonaws.com" wordpress.yaml  -vv
