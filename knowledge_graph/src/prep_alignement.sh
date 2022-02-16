#!/bin/bash

# Change fiels encoding to UTF-8
FROM_ENCODING="LATIN1"
TO_ENCODING="UTF-8"
CONVERT="iconv  -f   $FROM_ENCODING  -t   $TO_ENCODING" 
for  file  in  alignment/*.txt; do
     $CONVERT   "$file"   -o  "${file%.txt}.utf8"
done

for FILENAME in alignment/*.utf8; do
    mv $FILENAME ${FILENAME%.utf8}.txt;
done 

exit 0
