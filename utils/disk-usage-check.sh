#!/bin/sh

####
# Check how much disk space is free
# If more than 65% is full ping healthechk
# If more than 80% is full terminate running screen sessions

df -H | grep -vE '^Filesystem|tmpfs|cdrom' | awk '{ print $5 " " $1 }' | while read -r output;
do
  usep=$(echo "$output" | awk '{ print $1}' | cut -d'%' -f1  )
  partition=$(echo "$output" | awk '{ print $2 }' )
  if [ "$usep" -gt 65 ]; then
  	echo "####################"
	date
    message="Running out of space \"$partition ($usep%)\" on $(hostname) as on $(date)"
    echo "$message"
    curl --silent --retry 3 --data "$message" https://hc-ping.com/ca17924f-f470-431c-b57e-36cae497f879/fail
    # Send another one without the fail message to enable the sending of mails again, sleep to avoid rate limiting
    sleep 1.5
    curl --silent --retry 3 --data "$message" https://hc-ping.com/ca17924f-f470-431c-b57e-36cae497f879
    sleep 5
  fi
  if [ "$usep" -gt 80 ]; then
  	message="Terminate running screen sessions on $(hostname) at $(date)"
    echo "$message"
    screen -X quit
    curl --silent --retry 3 --data "$message" https://hc-ping.com/ca17924f-f470-431c-b57e-36cae497f879/fail
    # Send another one without the fail message to enable the sending of mails again, sleep to avoid rate limiting
    sleep 1.5
    curl --silent --retry 3 --data "$message" https://hc-ping.com/ca17924f-f470-431c-b57e-36cae497f879
  fi
done

