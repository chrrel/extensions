#!/bin/sh

# Start the servers at the position (URL) given in the CSV file

INPUT=scanners-manual-start.csv
OLDIFS=$IFS
IFS=','
[ ! -f $INPUT ] && { echo "$INPUT file not found"; exit 99; }
while read -r servername ip starturl
do
	echo "Starting scan on ${servername} (${ip}) at url #${starturl}"
	# Use -n option to prevent reading from stdin (which would read all remaining lines)
	ssh -n "${ip}" "cd /home/myusername/extensions/scanner; screen -d -m python3 main.py ${starturl};"
	# ssh -n "${ip}" "screen -X quit"
done < $INPUT
IFS=$OLDIFS

