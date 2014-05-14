#!/bin/bash

PATH="/bin:/usr/bin:/sbin:/usr/sbin"
cd ~/code
client=`cat "CLIENT"`
pgrep -f kinectuploader

if [ $? -ne 0 ]; then
  echo "start uploader"
  cd ~/code/kinect_new
  python kinectuploader.py $client &
fi
