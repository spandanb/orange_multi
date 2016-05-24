#!/bin/bash

#Sets up vino wordpress, across SAVI and AWS

source secret_envvars.sh

echo "Running OpenVPN"
cd openvpn 
./openvpn_run.sh

sleep 30

echo "Running afterOpenVPN"
cd ..
python after_openvpn.py

sleep 30

echo "Running WordPress config"
cd wordpress
./wordpress_run.sh

