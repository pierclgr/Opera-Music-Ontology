#!/bin/bash

# Unzip file and store in folder data/
unzip -qq -j ../data/soilc.zip -d ../data/

# Change fiels encoding to UTF-8
FROM_ENCODING="LATIN1"
TO_ENCODING="UTF-8"
CONVERT="iconv  -f   $FROM_ENCODING  -t   $TO_ENCODING" 
for  file  in  ../data/*.csv; do
     $CONVERT   "$file"   -o  "${file%.csv}.utf8"
done

rm ../data/*.csv

for FILENAME in ../data/*.utf8; do
    mv $FILENAME ${FILENAME%.utf8}.csv;
done 

exit 0
