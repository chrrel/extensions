#!/bin/bash

# Find URLS in input files


declare -a arr=(
"aaa.com"
"bbb.pl"
"ccc.com.cn"
)

# Now loop through the array above
for url in "${arr[@]}"
do
   echo "$url"
   grep "$url" ../input_data/top-1m/* -n
done

