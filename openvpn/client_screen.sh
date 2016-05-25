#!/bin/bash

source screen_handler.sh

#Parameter
SESSION=openvpn

#create session
create_session $SESSION

sleep 5

#start openvpn client 
screen_it $SESSION openvpn "sudo openvpn client.conf"

screen_it $SESSION getip "python ip_server.py" 
