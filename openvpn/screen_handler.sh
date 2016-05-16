#!/bin/bash
#script that provides a programatic interface over GNU screen

create_session(){
    #create screen session
    #Arguments:
    #$1: screen session name
    screen -S $1 -d -m
}

screen_it(){
    #creates new tabs and runs command
    #Arguments:
    #$1: screen session name
    #$2: tab name 
    #$3: command to execute
    
    SESSION_NAME=$1
    TAB_NAME=$2
    CMD=$3

    screen -S $SESSION_NAME -X screen -t $TAB_NAME /bin/bash
    screen -S $SESSION_NAME -p $TAB_NAME -X stuff "$CMD$(printf \\r)"
}

send_kill(){
    #sends kill signal (Ctrl^c) to specific tab
    #Arguments:
    #$1: screen session name
    #$2: tab name or number, arg to -p
    
    screen -x $1 -p $2 -X stuff "^C"
}

