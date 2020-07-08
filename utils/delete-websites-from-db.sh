#!/bin/bash

temp_file=urls-timed-out.txt

# 1. Extract all URLs with timeouts from the logs and save to temporary file
grep -r -oP 'evaluating .*: Timeout  -' ../../extensions-logs/ | perl -n -e'/evaluating (.+):/ && print "$1\n"' > $temp_file

# 2. Copy file to db server
scp $temp_file extscandb:/home/myusername/

# !!! Execute the rest on the DB server - 3. For each line (= url), delete the URL from the DB
while IFS= read -r line
do
 	echo "$line"
	#sudo -u postgres -H -- psql -d scanresults -c "DELETE FROM website WHERE url='$line'"
done < "$temp_file"

