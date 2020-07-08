#!/bin/bash

# Find urls that timed out in logfiles
# Timeouts look like this:
# ERROR:2020-02-17 15:20:40,553:pageevaluator:Error when evaluating http://example.com: Timeout  - Calling Page.navigate timeout


grep -r -oP 'evaluating .*: Timeout  -' ../../extensions-logs/ | 
perl -n -e'/evaluating http:\/\/(.+):/ && print "1,$1\n"' > ../input_data/timed-out-urls.csv

