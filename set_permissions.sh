#!/bin/bash
chmod u+rwX,g+rwX,o-w /opt/webcam_motion_detection
chmod u+x,g+x,o-wx /opt/webcam_motion_detection/*.sh
chown -R wmd.wmd /opt/webcam_motion_detection
