# -*- coding: utf-*-
# Webcam Driver definition
import logging
import numpy as np
from abc import abstractmethod

from webcam_motion_config import WebcamMotionConfig


class WebcamDriver(object):
    logger: logging.Logger = None

    def __init__(self, parent_logger: logging.Logger, config: WebcamMotionConfig):
        """
        Set the logger and configuration.
        :param parent_logger: the logger
        :param config: the configuration
        """
        if not self.__class__.logger:
            self.__class__.logger = logging.getLogger(self.__class__.__name__)
            for handler in parent_logger.handlers:
                self.__class__.logger.addHandler(handler)
            self.__class__.logger.setLevel(parent_logger.level)
        self.__class__.logger.info('Initializing ' + self.__class__.__name__ + '...')
        self._config: WebcamMotionConfig = config

    @abstractmethod
    def read(self) -> (bool, np.ndarray):
        """
        Read a frame as numpy.ndarray.
        :return: the frame as numpy.ndarray.
        """
        pass
