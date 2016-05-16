#!/bin/bash

##Install openvpn
sudo -s
wget -O - https://swupdate.openvpn.net/repos/repo-public.gpg|apt-key add -
echo "deb http://swupdate.openvpn.net/apt trusty main" | tee -a /etc/apt/sources.list.d/swupdate.openvpn.net.list
apt-get update
apt-get install openvpn -y
exit

##Install easy-rsa
git clone https://github.com/OpenVPN/easy-rsa.git
cd easy-rsa
git checkout release/2.x
cd easy-rsa/2.0

