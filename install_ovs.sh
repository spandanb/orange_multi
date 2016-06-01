#!/bin/bash

#https://github.com/openvswitch/ovs/blob/master/INSTALL.md

sudo apt-get update

wget http://openvswitch.org/releases/openvswitch-2.3.3.tar.gz
tar -zxf openvswitch-2.3.3.tar.gz 
cd openvswitch-2.3.3

sudo apt-get install gcc -y
sudo apt-get install libssl-dev -y
sudo apt-get install build-essential fakeroot -y

sudo apt-get install python-pip -y
sudo pip install six

sudo apt-get install debhelper autoconf automake -y
sudo apt-get install graphviz python-all python-qt4 python-twisted-conch libtool -y

#This performs a relatively fast build but skips unit tests
DEB_BUILD_OPTIONS='parallel=8 nocheck' fakeroot debian/rules binary

cd ..
sudo dpkg -i openvswitch-datapath-dkms_2.3.3-1_all.deb openvswitch-switch_2.3.3-1_amd64.deb openvswitch-common_2.3.3-1_amd64.deb

sudo reboot
