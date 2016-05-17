#!/bin/bash

#Sets up vino wordpress, across SAVI and AWS

source confidential/envvars.sh

python vino_wordpress.py

sleep 30

cd openvpn 
./openvpn_run.sh

sleep 30
cd ../wordpress
./wordpress_run.sh

