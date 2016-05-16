#!/bin/bash

ansible-playbook -i hosts --extra-vars "server_ip=ec2-54-208-117-50.compute-1.amazonaws.com" openvpn.yaml
