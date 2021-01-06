# Python program to implement
# Webcam Driver for unit tests

import cv2
import logging
import numpy as np
import os
import threading

from webcam_driver import WebcamDriver
from webcam_motion_config import WebcamMotionConfig
from webcam_motion_detector import ImageListener


class WebcamMockDriver(WebcamDriver):
    def __init__(self, parent_logger: logging.Logger, config: WebcamMotionConfig, listener: ImageListener, path: str):
        """
        Set the logger and configuration.
        :param parent_logger: the logger
        :param config: the configuration
        :param listener: the listener
        :param path: the path of the images
        """
        super().__init__(parent_logger, config)
        self.__device_address: str = config.get_video_device_address()
        self.__listener: ImageListener = listener
        self.__frame: np.ndarray = np.ndarray()
        self.__path: str = path
        self.__state: int = 0
        # noinspection PyTypeChecker
        self.__task: threading.Timer = None
        self.__toggle()

    def read(self) -> (bool, np.ndarray):
        """
        Read a frame as numpy.ndarray.
        :return: the frame as numpy.ndarray.
        """
        if self.__frame is None:
            return False, None
        return True, self.__frame

    def __toggle(self) -> None:
        """
        Change the current image according to the internal state.
        :return:
        """
        if self.__state <= 0 or self.__state > 1:
            self.__state = 1
        else:
            self.__state = 2
        path = self.__path + str(self.__state) + '.jpeg'
        if os.path.exists(path):
            self.__class__.logger.info('Loading image from: ' + path)
            self.__frame = cv2.imread(path)
        else:
            self.__class__.logger.warning('Cannot load the image, file not found: ' + path)
        self.__listener.on_image(self.__frame.tobytes())

    def set(self, frame: np.ndarray) -> None:
        """
        Set the frame as numpy.ndarray.
        :param frame: the frame as numpy.ndarray
        :return:
        """
        self.__frame = frame

    def __del__(self) -> None:
        """
        Stop the timer on destruction.
        :return:
        """
        self.stop()

    def __run(self):
        """
        Start the timer to simulate video.
        :return:
        """
        self.__toggle()
        self.__task: threading.Timer = threading.Timer(2, self.__toggle)
        self.__task.start()

    def start(self):
        """
        Start the timer to simulate video.
        :return:
        """
        self.__run()

    def stop(self):
        """
        Stop the timer used to simulate video.
        :return:
        """
        if self.__task is not None:
            self.__task.cancel()
            self.__task = None