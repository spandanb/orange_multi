#!/usr/bin/env bash
touch /home/ubuntu/snort.conf
cat << EOF > /home/ubuntu/snort.conf
drop tcp any any -> any any (flags:S; msg:"Possible TCP DoS, reject"; flow:stateless; detection_filter:track by_src, count 10, seconds 2; sid:5000000;)
reject tcp any any -> any 80 (content:"page_id=2"; nocase; msg:"accessed forbidden pages!!"; sid:5000001;)
reject tcp any any -> any 80 (content:"inject"; nocase; msg:"accessed forbidden pages!!"; sid:5000002;)
EOF
touch /home/ubuntu/run_snort.sh
mkdir /home/ubuntu/log
cat << EOF > /home/ubuntu/run_snort.sh
#!/bin/bash
until sudo snort -D -Q --daq afpacket -i p2:p3 -c /home/ubuntu/snort.conf -l /home/ubuntu/log
do
echo "Re-Try in 5 seconds"
sleep 5
done
EOF
chmod +x /home/ubuntu/run_snort.sh
/home/ubuntu/run_snort.sh > /dev/null 2>&1 &
