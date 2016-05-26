#!/usr/bin/env bash
sudo apt-get install haproxy -y
touch /home/ubuntu/haproxy.cfg
cat << EOF > /home/ubuntu/haproxy.cfg
listen l1 0.0.0.0:80
mode tcp
clitimeout 180000
srvtimeout 180000
contimeout 4000
server wp1 wp:80

global
daemon
maxconn 256
EOF
chmod 0666 /home/ubuntu/haproxy.cfg
touch /home/ubuntu/run_haproxy.sh
cat << EOF > /home/ubuntu/run_haproxy.sh       
#!/bin/bash
until sudo haproxy -f /home/ubuntu/haproxy.cfg
do
echo "Re-Try in 3 seconds"
sleep 3
done
EOF
chmod +x /home/ubuntu/run_haproxy.sh
/home/ubuntu/run_haproxy.sh > /dev/null 2>&1 &
