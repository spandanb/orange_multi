#!/bin/bash

#Sets up vino wordpress, across SAVI and AWS

source confidential/envvars.sh

echo "Creating nodes..."
python vino_wordpress.py

sleep 30

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

