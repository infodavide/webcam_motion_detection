#!/bin/bash
SCRIPT=`realpath $0`
SCRIPT_DIR=`dirname $SCRIPT`

if [[ -e "$SCRIPT_DIR/webcam_motion_detection.json" ]]
then
	port=`cat $SCRIPT_DIR/webcam_motion_detection.json|grep http_port|cut -d: -f2|cut -d, -f1|xargs`
else
	port='8080'
fi

curl -s -X GET http://127.0.0.1:$port/rest/app/health >/dev/null

if [[ $? -eq 7 ]]
then
	echo "Starting application webcam motion detection on port: $port"

	cd $SCRIPT_DIR
	python3 $SCRIPT_DIR/webcam_server.py
else
	echo "Application webcam motion detection is already started on port: $port"
fi