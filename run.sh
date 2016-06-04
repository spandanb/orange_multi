#!/bin/bash

#ssh-keygen -f file.rsa -t rsa -N ''

echo "Sourcing environment vars ..."
echo "$ source secret_envvarsh.sh\n"
source secret_envvarsh.sh

echo "Cleaning up ..."
echo "$ python parser.py --clean-up\n"
python parser.py --clean-up
sleep 5

echo "Booting topology ..."
echo "$ python parser.py --template-file topology_wordpress.yaml\n"
python parser.py -f topology_wordpress.yaml
sleep 5

echo "Preparing to run ansible"
echo "$ python create_interm_files.py\n"
python create_interm_files.py
sleep 5

echo "Configuring master"
echo "cd master && ./run.sh\n"
cd master
./run.sh

sleep 120

echo "Configuring nodes"
echo "cd ../wordpress && ./configure_wordpress.sh\n"
cd ../wordpress
./configure_wordpress.sh


