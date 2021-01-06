# Python program to implement
# Webcam Driver using cv2 module

import cv2
import datetime
import logging
import numpy as np
import sys

from webcam_driver import WebcamDriver
from webcam_motion_config import WebcamMotionConfig


class WebcamCv2Driver(WebcamDriver):
    logger: logging.Logger = None

    def __init__(self, parent_logger: logging.Logger, config: WebcamMotionConfig):
        """
        Initialize and set the logger and configuration.
        :param parent_logger: the logger
        :param config: the configuration
        """
        super().__init__(parent_logger, config)
        self.__video: cv2.VideoCapture = None
        self._last_open_time: datetime.datetime = None

    def __open(self):
        """
        Open the device
        """
        now: datetime.datetime = datetime.datetime.now()
        if self._last_open_time is None or (now - self._last_open_time).total_seconds() > 30:
            self._last_open_time = now
            self.__video = cv2.VideoCapture(int(self._config.get_video_device_address()))
            if not self.__video or not self.__video.isOpened():
                self.logger.warning('Device is not valid or not activated: ' + self._config.get_video_device_address())
                return
        self.__video.setExceptionMode(enable=True)

    def __del__(self) -> None:
        """
        Close the device and windows if graphical flag is True
        """
        self._last_error_time = None
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

    def read(self) -> (bool, np.ndarray):
        """
        Read a frame as numpy.ndarray.
        :return: the frame as numpy.ndarray.
        """
        if not self.__video or not self.__video.isOpened():
            self.__open()
            if not self.__video or not self.__video.isOpened():
                return False, None
        return self.__video.read()