#! /bin/sh

for dir in /../../extensions-logs/*; do
    ls -lcrt "$dir/"*.log | tail -n 1
done
