#!/bin/bash

PATH="/bin:/usr/bin:/sbin:/usr/sbin"

pgrep -f kinectuploader

if [ $? -ne 0 ]; then
  echo "start uploader"
  cd ~/code/kinect_new
  python kinectuploader.py WICU-room5 1 &
fi
