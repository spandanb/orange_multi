#!/bin/bash

#Install docker engine
sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
echo "deb https://apt.dockerproject.org/repo ubuntu-trusty main" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt-get update
sudo apt-get install linux-image-extra-$(uname -r) docker-engine -y
sudo service docker start
sudo usermod -a -G docker ubuntu

#Only on SAVI machines
sudo umount /tmp

#Install compose
curl -o docker-compose -L https://github.com/docker/compose/releases/download/1.7.1/docker-compose-`uname -s`-`uname -m`
chmod +x docker-compose
sudo mv docker-compose /usr/local/bin/


