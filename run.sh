#!/bin/bash

echo "Sourcing environment vars ..."
echo -e "$ source secret_envvars.sh\n"
source secret_envvars.sh

echo "Cleaning up ..."
echo -e "$ python parser.py --clean-up\n"
python parser.py --clean-up
sleep 5

echo "Booting topology ..."
echo -e "$ python parser.py --template-file topology_wordpress.yaml\n"
python parser.py -f topology_wordpress.yaml
sleep 5

echo "Preparing to run ansible"
echo -e "$ python create_interm_files.py\n"
python create_interm_files.py
sleep 5

echo "Configuring master"
echo -e "cd master && ./run.sh\n"
cd master
./run.sh

echo "waiting to deploy wordpress...."
sleep 60

echo "Configuring nodes"
echo -e "cd ../wordpress && ./configure_wordpress.sh\n"
cd ../wordpress
./configure_wordpress.sh


