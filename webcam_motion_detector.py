# Python program to implement 
# Webcam Motion Detector
import atexit
import cv2
import datetime
import logging
import nmap
import os
import signal
import subprocess
import smtplib
import sys
import threading
import time
import traceback
import zipstream

from builtins import int
from abc import ABC, abstractmethod
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Constants
TIME_FORMAT: str = '%H:%M'
CAPTURE_DELAY: float = 0.2
CAPTURE_CONTOUR: int = 25000
MAX_IMAGES: int = 10


def find_ip_v4():
    address: str = subprocess.check_output(['hostname', '--all-ip-addresses']).decode()
    if address and not address.startswith('127.'):
        return address
    return '127.0.0.1'


class ObjectView(object):
    def __init__(self, d):
        self.__dict__ = d

    """ Returns the string representation of the view """
    def __str__(self):
        return str(self.__dict__)


class ImageItem(object):
    def __init__(self, basename, data):
        self.basename = basename
        self.data = data

    """ Returns the string representation of the view """
    def __str__(self):
        return str(self.basename)


class ImageListener(ABC):

    @abstractmethod
    def on_image(self, image: bytearray) -> None:
        """
        Receive image from WebcamMotionDetector.
        """
        pass


class WebcamMotionDetector(object):

    def __init__(self, logger: logging.Logger, configuration: ObjectView, listener: ImageListener):
        # Last detection
        self.__last_detection: datetime = None
        # Video capture and JPEG image
        self.__image_bytes: bytes = b''
        self.__image_event: threading.Event = threading.Event()
        self.__images: list = list()
        # Listener
        self.__listener: ImageListener = listener
        # Status flags
        self.activated: bool = False
        self.suspended: bool = True
        # Tasks
        self.__check_activated_task: threading.Timer = None
        self.__check_suspended_task: threading.Timer = None
        self.__capture_task: threading.Timer = None
        self.logger: logging.Logger = logger
        atexit.register(self.__del__)
        signal.signal(signal.SIGINT, self.__del__)
        self.logger.info('Configuring motion detector...')
        self.__config: ObjectView = configuration
        # noinspection PyUnresolvedReferences
        self.__log_file_path: str = self.__config.TMP_DIR + os.sep + 'webcam_motion_detection.log'
        # Time ranges for activation
        self.__times_on: dict = dict()
        self.__times_on[1] = []
        self.__times_on[2] = []
        self.__times_on[3] = []
        self.__times_on[4] = []
        self.__times_on[5] = []
        self.__times_on[6] = []
        self.__times_on[7] = []
        # noinspection PyUnresolvedReferences
        if self.__config.ACTIVATION_TIMES and len(self.__config.ACTIVATION_TIMES) > 0:
            # noinspection PyUnresolvedReferences
            for value in self.__config.ACTIVATION_TIMES.split(','):
                fields = value.split('|')
                self.__times_on[int(fields[0])].append([datetime.strptime(fields[1], TIME_FORMAT).time(),
                                                        datetime.strptime(fields[2], TIME_FORMAT).time()])
        # noinspection PyUnresolvedReferences
        self.__video: cv2.VideoCapture = cv2.VideoCapture(int(self.__config.VIDEO_DEVICE))
        if not self.__video or not self.__video.isOpened():
            # noinspection PyUnresolvedReferences
            raise Exception('Device is not valid: ' + self.__config.VIDEO_DEVICE)
        self.__video.setExceptionMode(enable=True)
        self.logger.info('Motion detector configured')
        self.__check_activated()
        self.__check_suspended()

    def __del__(self):
        print('Destroying motion detector...')
        try:
            if self.__check_activated_task:
                self.__check_activated_task.cancel()
        except Exception as e:
            print('Cannot stop __check_activated_task: %s' % e, file=sys.stderr)
        try:
            if self.__check_suspended_task:
                self.__check_suspended_task.cancel()
        except Exception as e:
            print('Cannot stop __check_suspended_task: %s' % e, file=sys.stderr)
        try:
            if self.__capture_task:
                self.__capture_task.cancel()
        except Exception as e:
            print('Cannot stop __capture_task: %s' % e, file=sys.stderr)
        try:
            if self.__video:
                # Release video device
                self.__video.release()
            # noinspection PyUnresolvedReferences
            if self.__config.GRAPHICAL:
                # Destroying all the windows
                cv2.destroyAllWindows()
        except Exception as e:
            print('Cannot stop video: %s' % e, file=sys.stderr)

    def __notify(self, images, message=None) -> None:
        # noinspection PyUnresolvedReferences
        if not self.__config.SMTP_SERVER or not self.__config.SMTP_PORT:
            self.logger.warning('SMTP_SERVER or SMTP_PORT not specified in configuration, skipping email notification')
            return
        # noinspection PyUnresolvedReferences
        if not self.__config.SMTP_FROM or not self.__config.SMTP_TO:
            self.logger.warning('No email address specified, skipping email notification')
            return
        parts = []
        for image in images:
            part: MIMEApplication = MIMEApplication(
                image.data,
                Name=image.basename
            )
            part['Content-Disposition'] = 'attachment; filename="%s"' % image.basename
            parts.append(part)
        if len(parts) == 0:
            return
        # noinspection PyUnresolvedReferences
        self.logger.info('Sending email to ' + self.__config.SMTP_TO)
        # noinspection PyTypeChecker
        server: smtplib.SMTP = None
        try:
            # noinspection PyUnresolvedReferences
            server = smtplib.SMTP(self.__config.SMTP_SERVER, self.__config.SMTP_PORT)
            msg: MIMEMultipart = MIMEMultipart()
            # noinspection PyUnresolvedReferences
            msg['From'] = self.__config.SMTP_FROM
            # noinspection PyUnresolvedReferences
            msg['To'] = self.__config.SMTP_TO
            if message is None:
                mt = MIMEText(os.path.splitext(os.path.basename(__file__))[0] + ' completed', 'plain')
                mt['Subject'] = os.path.splitext(os.path.basename(__file__))[0] + ' completed'
            else:
                self.logger.debug(message)
                mt = MIMEText(os.path.splitext(os.path.basename(__file__))[0] + ' completed with error(s): ' + message + ', check logs', 'plain')
                mt['Subject'] = os.path.splitext(os.path.basename(__file__))[0] + ' completed with error(s)'
            msg['Subject'] = mt['Subject']
            # noinspection PyUnresolvedReferences
            mt['From'] = self.__config.SMTP_FROM
            # noinspection PyUnresolvedReferences
            mt['To'] = self.__config.SMTP_TO
            msg.attach(mt)
            if self.__log_file_path is not None:
                basename: str = os.path.basename(self.__log_file_path + '.zip')
                zipfile = zipstream.ZipFile()
                zipfile.write(self.__log_file_path, os.path.basename(self.__log_file_path))
                part = None
                for data in zipfile:
                    part = MIMEApplication(
                        data,
                        Name=basename
                    )
                part['Content-Disposition'] = 'attachment; filename="%s"' % basename
                msg.attach(part)
            for part in parts:
                msg.attach(part)
            # noinspection PyUnresolvedReferences
            if not self.__config.TEST:
                # noinspection PyUnresolvedReferences
                server.sendmail(msg['From'], self.__config.SMTP_TO, msg.as_string())
            else:
                self.logger.warning('Not sending (see configuration and TEST property')
        finally:
            if server:
                server.close()

    def __check_activated(self) -> None:
        self.logger.debug('Checking if activated according to time settings...')
        r: bool = False
        d = datetime.now()
        ranges = self.__times_on[d.weekday()]
        if len(ranges) > 0:
            t = d.time()
            for rng in ranges:
                if rng[0] <= t <= rng[1]:
                    r = True
                    break
        if self.activated != r:
            self.logger.info('activated: ' + str(r) + ', suspended: ' + str(self.suspended))
            self.activated = r
            self.logger.debug('activated: ' + str(self.activated) + ', suspended: ' + str(self.suspended))
            if self.activated and not self.suspended:
                self.start()
        self.__check_activated_task = threading.Timer(60, self.__check_activated)
        self.__check_activated_task.start()
        self.logger.debug('Check activated scheduled...' + repr(self.__check_activated_task))

    def __check_suspended(self) -> None:
        self.logger.debug('Checking if suspended by detection of a secure device on the network...')
        r: bool = False
        # noinspection PyUnresolvedReferences
        if self.__config.TEST:
            self.logger.warning('Suspended forced to false (see configuration and TEST property')
        # noinspection PyUnresolvedReferences
        elif self.__config.MAC_ADDRESSES and len(self.__config.MAC_ADDRESSES) > 0:
            ip_v4 = find_ip_v4()
            nm: nmap.PortScanner = nmap.PortScanner()
            nm.scan(hosts=ip_v4.rsplit('.', 1)[0] + '.0/24', arguments='-sPn', sudo=True)
            hosts: list = nm.all_hosts()
            # noinspection PyUnresolvedReferences
            mac_addresses = self.__config.MAC_ADDRESSES.split(',')
            for host in hosts:
                data = nm[host]
                if data:
                    addresses = data['addresses']
                    if addresses and 'mac' in addresses and addresses['mac'] in mac_addresses:
                        r = True
                        break
        if self.suspended != r:
            self.logger.info('activated: ' + str(self.activated) + ', suspended: ' + str(r))
            self.suspended = r
            self.logger.debug('activated: ' + str(self.activated) + ', suspended: ' + str(self.suspended))
            if not self.suspended and self.activated:
                self.start()
        self.__check_suspended_task = threading.Timer(60, self.__check_suspended)
        self.__check_suspended_task.start()
        self.logger.debug('Check suspended scheduled...' + repr(self.__check_suspended_task))

    def __capture(self) -> None:
        self.logger.info('Starting capture...')
        # Assigning our static_back to None
        static_back = None
        # Infinite while loop to treat stack of image as video
        try:
            while self.activated and not self.suspended:
                now: datetime.datetime = datetime.now()
                # Reading frame(image) from video
                check, frame = self.__video.read()
                # Reset the JPEG image associated to the previous frame
                is_success, image = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
                self.__listener.on_image(bytearray(image))
                self.__image_event.set()
                # Initializing motion = 0(no motion)
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
                # If change in between static background and current frame is greater than 30 it will show white color(255)
                thresh_frame = cv2.threshold(diff_frame, 30, 255, cv2.THRESH_BINARY)[1]
                thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)
                # Finding contour of moving object
                contours, _ = cv2.findContours(thresh_frame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for contour in contours:
                    if cv2.contourArea(contour) > CAPTURE_CONTOUR:
                        motion = True
                        (x, y, w, h) = cv2.boundingRect(contour)
                        # making green rectangle around the moving object
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                        break
                if motion and (self.__last_detection is None or (now - self.__last_detection).total_seconds() > 1):
                    image = ImageItem('webcam_motion_detection-' + str(now) + '.jpg', self.__image_bytes)
                    while len(self.__images) > MAX_IMAGES:
                        self.__images.pop(0)
                    self.__images.append(image)
                    self.logger.info('Motion detected and stored to ' + image.basename)
                    self.__last_detection = now
                    static_back = gray
                # noinspection PyUnresolvedReferences
                if self.__last_detection and (now - self.__last_detection).total_seconds() > int(self.__config.NOTIFICATION_DELAY):
                    # noinspection PyUnresolvedReferences
                    task = threading.Timer(0, self.__notify, args=[self.__images.copy(), 'Motion detected using ' + self.__config.VIDEO_DEVICE_NAME])
                    self.__images.clear()
                    task.start()
                # noinspection PyUnresolvedReferences
                if self.__config.GRAPHICAL:
                    cv2.imshow("Color Frame", frame)
                key = cv2.waitKey(1)
                # if q entered process will stop
                if key == ord('q'):
                    self.logger.info('Stopping...')
                    if self.__check_activated_task:
                        self.__check_activated_task.cancel()
                    if self.__check_suspended_task:
                        self.__check_suspended_task.cancel()
                    break
                time.sleep(CAPTURE_DELAY)
        except Exception as e:
            self.logger.error('Stopping after failure: ' + repr(e))
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback, limit=6, file=sys.stderr)
            if self.__check_activated_task:
                self.__check_activated_task.cancel()
            if self.__check_suspended_task:
                self.__check_suspended_task.cancel()
        self.logger.info('Stopping capture...')
        self.__capture_task = None

    def start(self) -> None:
        self.logger.info('Start triggered')
        if self.__capture_task is None:
            self.__capture_task = threading.Timer(1, self.__capture)
            self.__capture_task.start()
            self.logger.debug('Capture scheduled...' + repr(self.__capture_task))
        else:
            self.logger.info('Capture already running...')

    def get_image_event(self) -> threading.Event:
        return self.__image_event
