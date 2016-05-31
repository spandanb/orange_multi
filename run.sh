#!/bin/bash

echo "Cleaning up"
python parser.py -c
sleep 5

echo "Booting topology"
python parser.py -f topology_wordpress.yaml
sleep 5

echo "Preparing to run ansible"
python create_interm_files.py
sleep 5

cd master
./run.sh

cd ../wordpress
./configure_wordpress.sh


