#!/bin/bash

PATH="/bin:/usr/bin:/sbin:/usr/sbin"

pgrep -f kinectclient

if [ $? -ne 0 ]; then
    echo "restart"
    cd ~/code/kinect_new
    python kinectclient.py -b WICU-room5 1 &
fi
