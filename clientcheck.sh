#!/bin/bash

PATH="/bin:/usr/bin:/sbin:/usr/sbin"
cd ~/code
client=`cat CLIENT`
pgrep -f kinectclient

if [ $? -ne 0 ]; then
    echo "restart"
    cd ~/code/kinect_new
    python kinectclient.py -b $client  &
fi
