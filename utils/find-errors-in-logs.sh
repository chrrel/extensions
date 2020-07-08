#!/bin/bash

# Find sites that could not be saved to the database due to a DB error

grep -r "peewee.DatabaseError: Cannot save data for website" ../../extensions-logs/ | 
perl -n -e'/for website http:\/\/(.+):/ && print "$1\n"' > ../input_data/urls-with-errors.csv
