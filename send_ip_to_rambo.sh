#!/bin/bash

PATH="/bin:/usr/bin:/sbin:/usr/sbin"

cd ~/code

new_ip=`ifconfig wlan0 | grep "inet addr" | cut -d ":" -f 2 | cut -d " " -f 1`
HOSTNAME=`hostname`

if [ -f "$HOSTNAME" ]
then
  old_ip=`cat "$HOSTNAME"`
else
  old_ip=""
fi

if [ "$new_ip" != "$old_ip" ]
then
  echo "$new_ip" > "$HOSTNAME"
  rsync -va "$HOSTNAME" zad@rambo.isi.jhu.edu:~/clients
  #scp "$HOSTNAME" zad@rambo.isi.jhu.edu:~/clients
fi

