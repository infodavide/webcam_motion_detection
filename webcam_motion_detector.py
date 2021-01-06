# -*- coding: utf-*-
# Webcam Motion Detector
import atexit
import cv2
import datetime
import logging
import numpy as np
import os
import signal
import sys
import threading
import time
import traceback

from abc import ABC, abstractmethod
from builtins import int
from datetime import datetime
from typing import List
from webcam_driver import WebcamDriver
from webcam_motion_config import Periods, WebcamMotionConfig
from extension import Extension
from id_network_utils import find_ip_v4, is_reachable, scan_network

CAPTURE_DELAY: float = 0.2
CAPTURE_CONTOUR: int = 25000
MAX_IMAGES: int = 10
ACTIVATED_SPACE: str = 'activated: '
SUSPENDED_SPACE: str = 'suspended: '


class ImageItem(object):
    def __init__(self, basename: str, data: bytes):
        """
        Initialize the image object passed to the extensions.
        :param basename: the image name with time of capture
        :param data: the binary data
        """
        self.basename = basename
        self.data = data

    """ Returns the string representation of the view """

    def __str__(self) -> str:
        """
        Return the textual view, the image name with time of capture.
        :return: the text
        """
        return str(self.basename)


class ImageListener(ABC):
    @abstractmethod
    def on_image(self, image: bytes) -> None:
        """
        Listener interface used to receive image from detector mechanism.
        """
        pass


ListOfImageListeners = List[ImageListener]
ListOfExtensions = List[Extension]


class WebcamMotionDetector(object):
    logger: logging.Logger = None

    def __init__(self, parent_logger: logging.Logger, config: WebcamMotionConfig, driver: WebcamDriver):
        """
        Initialize the detection mechanism.
        :param parent_logger: the main logger
        :param config: the configuration object
        :param driver: the video driver object
        """
        self.__active = False
        if not WebcamMotionDetector.logger:
            WebcamMotionDetector.logger = logging.getLogger(self.__class__.__name__)
            for handler in parent_logger.handlers:
                WebcamMotionDetector.logger.addHandler(handler)
            WebcamMotionDetector.logger.setLevel(parent_logger.level)
        WebcamMotionDetector.logger.info('Initializing ' + self.__class__.__name__ + '...')
        # Listeners
        self.__listeners: ListOfImageListeners = list()
        # Extensions
        self.__extensions: ListOfExtensions = list()
        # Last detection
        # noinspection PyTypeChecker
        self.__last_detection_time: datetime = None
        # Video capture and JPEG image
        self.__image_event: threading.Event = threading.Event()
        self.__images: list = list()
        # Status flags
        self.__activated: bool = False
        self.__suspended: bool = True
        self.moving: bool = False
        # Locks
        self.__start_capture_lock: threading.Lock = threading.Lock()
        self.__start_lock: threading.Lock = threading.Lock()
        self.__stop_lock: threading.Lock = threading.Lock()
        # Tasks
        # noinspection PyTypeChecker
        self.__check_activated_task: threading.Timer = None
        # noinspection PyTypeChecker
        self.__check_suspended_task: threading.Timer = None
        # noinspection PyTypeChecker
        self.__capture_task: threading.Timer = None
        # Network scan results
        # noinspection PyTypeChecker
        self.__scan_results: list = None
        atexit.register(self.__del__)
        signal.signal(signal.SIGINT, self.__del__)
        WebcamMotionDetector.logger.info('Configuring motion detector...')
        self.__config: WebcamMotionConfig = config
        # noinspection PyUnresolvedReferences
        self.__log_file_path: str = self.__config.get_temp_dir() + os.sep + 'webcam_motion_detection.log'
        # noinspection PyUnresolvedReferences
        self.__driver: WebcamDriver = driver
        WebcamMotionDetector.logger.info('Motion detector configured')

    def __del__(self) -> None:
        """
        Stop the task on destruction.
        :return:
        """
        self.stop(True)

    def __process(self, images, message=None) -> None:
        """
        Forward the images and messages to the extensions on detection.
        :param images: the list of images
        :param message: the message
        :return:
        """
        if not self.__extensions or len(self.__extensions) == 0:
            return
        WebcamMotionDetector.logger.info('Dispatching to notifier')
        for extension in self.__extensions:
            if extension.get_config().is_enabled():
                extension.process(images, message)

    def __check_activated(self) -> None:
        """
        Check activation according to interval of times and current time and then start or stop the capture according to the result.
        :return:
        """
        WebcamMotionDetector.logger.debug('Checking if activated according to time settings...')
        d = datetime.now()
        r: bool = self.__config.get_activation_periods().is_in(d)
        if self.__activated != r:
            WebcamMotionDetector.logger.info(ACTIVATED_SPACE + str(r) + ', ' + SUSPENDED_SPACE + str(self.__suspended))
            self.__activated = r
            WebcamMotionDetector.logger.debug(ACTIVATED_SPACE + str(self.__activated) + ', ' + SUSPENDED_SPACE + str(self.__suspended))
            if self.__activated and not self.__suspended:
                self.__start_capture_task()
        self.__check_activated_task = threading.Timer(60, self.__check_activated)
        self.__check_activated_task.start()
        WebcamMotionDetector.logger.debug('Check activated scheduled...' + repr(self.__check_activated_task))

    def __check_suspended(self) -> None:
        """
        Check suspension according to presence of devices on the network and then start or stop the capture according to the result.
        :return:
        """
        WebcamMotionDetector.logger.debug('Checking if suspended by detection of a secure device on the network...')
        ip_v4: str = find_ip_v4()
        r: bool = False
        # noinspection PyUnresolvedReferences
        self.__scan_results = scan_network(ip_v4)
        # noinspection PyUnresolvedReferences
        if self.__config.get_mac_addresses() and len(self.__config.get_mac_addresses()) > 0:
            # noinspection PyUnresolvedReferences
            r = is_reachable(ip_v4, self.__config.get_mac_addresses(), self.__scan_results)
        if self.__suspended != r:
            WebcamMotionDetector.logger.info(ACTIVATED_SPACE + str(self.__activated) + ', suspended: ' + str(r))
            self.__suspended = r
            WebcamMotionDetector.logger.debug(ACTIVATED_SPACE + str(self.__activated) + ', suspended: ' + str(self.__suspended))
            if not self.__suspended and self.__activated:
                self.__start_capture_task()
        self.__check_suspended_task = threading.Timer(120, self.__check_suspended)
        self.__check_suspended_task.start()
        WebcamMotionDetector.logger.debug('Check suspended scheduled...' + repr(self.__check_suspended_task))

    def add_listener(self, listener: ImageListener) -> None:
        """
        Add an image listener to get all the frames read by the video driver.
        :param listener:  the listener
        :return:
        """
        if listener not in self.__listeners:
            self.__listeners.append(listener)

    def remove_listener(self, listener: ImageListener) -> None:
        """
        Remove the image listener to get all the frames read by the video driver.
        :param listener:  the listener
        :return:
        """
        if listener in self.__listeners:
            self.__listeners.remove(listener)

    def __capture(self) -> None:
        """
        Main capture and detection mechanism.
        :return:
        """
        WebcamMotionDetector.logger.info('Capturing...')
        # Assigning our static_back to None
        static_back = None
        # Infinite while loop to treat stack of image as video
        try:
            while self.__active and self.__activated and not self.__suspended:
                now: datetime.datetime = datetime.now()
                # Reading frame(image) from video
                ready, frame = self.__driver.read()
                if not ready:
                    continue
                # Extract the JPEG image associated to the frame
                is_success, resized_frame = cv2.imencode('.jpg', frame, params=[int(cv2.IMWRITE_JPEG_QUALITY), 90])
                resized_frame_bytes: bytes = resized_frame.tobytes()
                # Notify
                for listener in self.__listeners:
                    listener.on_image(resized_frame_bytes)
                self.__image_event.set()
                # Initializing motion = False (no motion)
                motion: bool = False
                # Converting color image to gray_scale image
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Converting gray scale image to GaussianBlur so that change can be find easily
                gray = cv2.GaussianBlur(gray, (21, 21), 0)
                # In first iteration we assign the value of static_back to our first frame
                if static_back is None:
                    static_back = gray
                    continue
                # Difference between static background and current frame(which is GaussianBlur)
                diff_frame = cv2.absdiff(static_back, gray)
                # If change in between static background and current frame is greater than 30
                # it will show white color(255)
                thresh_frame = cv2.threshold(diff_frame, 30, 255, cv2.THRESH_BINARY)[1]
                thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)
                # Finding contour of moving object
                contours, _ = cv2.findContours(thresh_frame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for contour in contours:
                    if cv2.contourArea(contour) > CAPTURE_CONTOUR:
                        motion = True
                        (x, y, w, h) = cv2.boundingRect(contour)
                        # Making green rectangle around the moving object
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                        break
                if not self.moving and motion and (self.__last_detection_time is None or (now - self.__last_detection_time).total_seconds() > 1):
                    image = ImageItem('webcam_motion_detection-' + str(now) + '.jpg', resized_frame_bytes)
                    while len(self.__images) > MAX_IMAGES:
                        self.__images.pop(0)
                    self.__images.append(image)
                    WebcamMotionDetector.logger.info('Motion detected and stored to ' + image.basename)
                    self.__last_detection_time = now
                    static_back = gray
                # noinspection PyUnresolvedReferences
                if self.__last_detection_time and (now - self.__last_detection_time).total_seconds() > int(self.__config.get_notification_delay()):
                    # Call extensions on detection
                    # noinspection PyUnresolvedReferences
                    task = threading.Timer(0, self.__process, args=[self.__images.copy(), 'Motion detected using ' + self.__config.get_video_device_name()])
                    task.start()
                    self.__images.clear()
                # noinspection PyUnresolvedReferences
                if self.__config.is_graphical():
                    cv2.imshow("Color Frame", frame)
                key = cv2.waitKey(1)
                # If q entered process will stop
                if key == ord('q'):
                    WebcamMotionDetector.logger.info('Stopping...')
                    if self.__check_activated_task:
                        self.__check_activated_task.cancel()
                    if self.__check_suspended_task:
                        self.__check_suspended_task.cancel()
                    break
                time.sleep(CAPTURE_DELAY)
        except Exception as e:
            WebcamMotionDetector.logger.error('Stopping after failure: ' + repr(e))
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback, limit=6, file=sys.stderr)
            if self.__check_activated_task:
                self.__check_activated_task.cancel()
            if self.__check_suspended_task:
                self.__check_suspended_task.cancel()
        WebcamMotionDetector.logger.info('Stopping capture...')
        self.__capture_task = None

    def __start_capture_task(self) -> None:
        """
        Start the capture thread.
        :return:
        """
        with self.__stop_lock:
            if not self.__active:
                WebcamMotionDetector.logger.info('Detector is not active, capture not started...')
                return
        with self.__start_capture_lock:
            if self.__capture_task is None:
                WebcamMotionDetector.logger.info('Starting capture...')
                self.__active = True
                self.__capture_task = threading.Timer(1, self.__capture)
                self.__capture_task.start()
                WebcamMotionDetector.logger.debug('Capture scheduled...' + repr(self.__capture_task))
            else:
                WebcamMotionDetector.logger.info('Capture already running')

    def is_running(self) -> bool:
        """
        Check if capture is running.
        :return: True if running
        """
        return self.__active

    def is_activated(self) -> bool:
        """
        Check if capture is activated.
        :return: True if activated
        """
        return self.__activated

    def is_suspended(self) -> bool:
        """
        Check if capture is suspended.
        :return: True if suspended
        """
        return self.__suspended

    def start(self) -> None:
        """
        Start the threads (activation, suspension) used to start or stop the capture.
        :return:
        """
        WebcamMotionDetector.logger.debug('Starting...')
        with self.__start_lock:
            self.__active = True
            self.__check_activated_task = threading.Timer(1, self.__check_activated)
            self.__check_activated_task.start()
            self.__check_suspended_task = threading.Timer(1, self.__check_suspended)
            self.__check_suspended_task.start()

    def stop(self, destructor: bool = False) -> None:
        """
        Stop the threads (activation, suspension and capture).
        :return:
        """
        with self.__start_lock:
            with self.__stop_lock:
                try:
                    if not destructor:
                        WebcamMotionDetector.logger.debug('Stopping...')
                except NameError:
                    pass
                self.__active = False
                try:
                    if self.__check_activated_task:
                        self.__check_activated_task.cancel()
                    self.__check_activated_task = None
                except Exception as e:
                    print('Cannot stop __check_activated_task: %s' % e, file=sys.stderr)
                try:
                    if self.__check_suspended_task:
                        self.__check_suspended_task.cancel()
                    self.__check_suspended_task = None
                except Exception as e:
                    print('Cannot stop __check_suspended_task: %s' % e, file=sys.stderr)
                try:
                    if self.__capture_task:
                        self.__capture_task.cancel()
                    self.__capture_task = None
                except Exception as e:
                    print('Cannot stop __capture_task: %s' % e, file=sys.stderr)

    def restart(self):
        """
        Stop and start the threads.
        :return:
        """
        self.stop()
        time.sleep(1)
        self.start()

    def get_image_event(self) -> threading.Event:
        """
        Return the lock on image.
        :return:
        """
        return self.__image_event

    def get_scan_results(self):
        """
        Return and share the results of the network scan used by the suspension thread.
        :return:
        """
        return self.__scan_results
