#!/bin/bash
ansible-playbook -i hosts --extra-vars "server_ip=ec2-54-210-196-104.compute-1.amazonaws.com" openvpn.yaml