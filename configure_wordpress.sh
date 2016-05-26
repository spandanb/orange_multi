#!/bin/bash

#Sets up vino wordpress, across SAVI and AWS

source secret_envvars.sh

python vino_wordpress.py -c
sleep 10

python vino_wordpress2.py -a span_key -s spandan_key
sleep 10

#echo "Running OpenVPN"
#cd openvpn 
#./openvpn_run.sh
#
#sleep 15
#
#echo "Running afterOpenVPN"
#cd ..
#python after_openvpn.py
#
#sleep 15

echo "Running WordPress config"
cd wordpress
./wordpress_run.sh

