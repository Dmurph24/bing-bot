#!/bin/bash
# ./onScriptComplete [mail]

logFile="`dirname $0`/log.log"

# do nothing if there is no log file
if [ ! -s "$logFile" ] ; then
    if [ -f "$logFile" ] ; then
        rm "$logFile"
    fi

   #exit 0
fi

echo "Script Complete!"

rm "$logFile"

