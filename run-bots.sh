i#!/bin/bash

echo "Getting ready to run bots!"

DATE=`date +%Y-%m-%d`

HOME_PATH=InstagramBots/

MAIN=main.py

LOGS_DIR=InstagramBots/logs/

RESULT=rav_$DATE.log

#Connect to the VPN
#windscribe connect

#Run the bots
python3 $HOME_PATH$MAIN ecstaticgames &> $LOGS_DIR$RESULT2 &

