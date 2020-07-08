#!/bin/bash

# Find urls that timed out in logfiles
# Timeouts look like this:

# Find all log files
find ../../extensions-logs/ -name "scan-*-extscan*.log"  | sort 

# Show last n lines of a single file
tail ../../extensions-logs/extscan01/scan-1580944321-extscan01.log -n 200

