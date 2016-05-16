#!/bin/bash

source screen_handler.sh

#Parameter
SESSION=openvpn

#create session
create_session $SESSION

#Need to sleep, else may try to create 
#tab in screen session that does not exist
sleep 5

#start openvpn server
screen_it $SESSION openvpn "sudo openvpn server.conf"
