# Python program to implement
# Webcam Driver for unit tests

import logging
import os
import threading

from webcam_driver import WebcamDriver
from webcam_motion_config import WebcamMotionConfig
from webcam_motion_detector import ImageListener


class WebcamMockDriver(WebcamDriver):

    def __init__(self, parent_logger: logging.Logger, config: WebcamMotionConfig, listener: ImageListener, path: str):
        super().__init__(parent_logger, config)
        self.__device_address: str = config.get_video_device_address()
        self.__listener: ImageListener = listener
        self.__frame: bytes = b''
        self.__path: str = path
        self.__state: int = 0
        # noinspection PyTypeChecker
        self.__task: threading.Timer = None
        self.__toggle()

    def read(self) -> (bool, object):
        if self.__frame is None:
            return False, None
        return True, self.__frame

    def __toggle(self) -> None:
        if self.__state <= 0 or self.__state > 1:
            self.__state = 1
        else:
            self.__state = 2
        path = self.__path + str(self.__state) + '.jpeg'
        if os.path.exists(path):
            self.__class__.logger.info('Loading image from: ' + path)
            with open(path, 'rb') as image_file:
                self.__frame = image_file.read()
        else:
            self.__class__.logger.warning('Cannot load the image, file not found: ' + path)
        self.__listener.on_image(self.__frame)

    def set(self, frame) -> None:
        self.__frame = frame

    def __del__(self) -> None:
        self.stop()

    def __run(self):
        self.__toggle()
        self.__task: threading.Timer = threading.Timer(2, self.__toggle)
        self.__task.start()

    def start(self):
        self.__run()

    def stop(self):
        if self.__task is not None:
            self.__task.cancel()
            self.__task = None