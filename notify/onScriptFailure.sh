#!/bin/bash
# ./onScriptFailure [mail] "error message"

logFile="`dirname $0`/log.log"

# if the log file doens't exist, or is empty -> print something to it
if [ ! -s "$logFile" ] ; then
    echo "Empty log" > "$logFile"
fi

rm "$logFile"
