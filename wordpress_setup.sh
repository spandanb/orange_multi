#!/bin/bash

#Sets up wordpress, across SAVI and AWS


source confidential/envvars.sh

python multi.py

sleep 30

cd openvpn 
./openvpn_run.sh

sleep 30

cd ..
python after_openvpn.py

sleep 30

cd wordpress
./wordpress_run.sh

#point browser to AWS host
