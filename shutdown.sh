#!/bin/bash
SCRIPT=`realpath $0`
SCRIPT_DIR=`dirname $SCRIPT`

if [[ -e "$SCRIPT_DIR/webcam_motion_detection.json" ]]
then
	port=`cat $SCRIPT_DIR/webcam_motion_detection.json|grep http_port|cut -d: -f2|cut -d, -f1|xargs`
else
	port='8080'
fi

echo "Shutting down webcam motion detection using port: $port"

curl -s -X POST http://127.0.0.1:$port/rest/app/shutdown >/dev/null

if [[ $? -eq 7 ]]
then
	echo "Application webcam motion detection is not available on port: $port"
fi