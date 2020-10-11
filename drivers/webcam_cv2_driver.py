# Python program to implement
# Webcam Driver using cv2 module

import cv2
import logging
import sys

from webcam_driver import WebcamDriver
from webcam_motion_config import Times, WebcamMotionConfig


class WebcamCv2Driver(WebcamDriver):
    logger: logging.Logger = None

    def __init__(self, parent_logger: logging.Logger, config: WebcamMotionConfig):
        super().__init__(parent_logger, config)
        self.__video: cv2.VideoCapture = cv2.VideoCapture(int(config.get_video_device_address()))
        if not self.__video or not self.__video.isOpened():
            # noinspection PyUnresolvedReferences
            raise Exception('Device is not valid: ' + config.get_video_device_address())
        self.__video.setExceptionMode(enable=True)

    def __del__(self) -> None:
        try:
            if self.__video:
                # Release video device
                self.__video.release()
            # noinspection PyUnresolvedReferences
            if self._config.is_graphical():
                # Destroying all the windows
                cv2.destroyAllWindows()
        except Exception as e:
            print('Cannot stop video: %s' % e, file=sys.stderr)

    def read(self) -> (bool, object):
        return self.__video.read()