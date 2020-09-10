# Python program to implement 
# Webcam Motion Detector
import atexit
import cv2
import datetime
import glob
import nmap
import os
import sched
import shutil
import signal
import subprocess
import smtplib
import sys
import threading
import time
import zipfile

from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Constants
TIME_FORMAT = '%H:%M'


def find_ip_v4():
    address = subprocess.check_output(['hostname', '--all-ip-addresses']).decode()
    if address and not address.startswith('127.'):
        return address
    return '127.0.0.1'


class ObjectView(object):
    def __init__(self, d):
        self.__dict__ = d

    """ Returns the string representation of the view """

    def __str__(self):
        return str(self.__dict__)


class WebcamMotionDetector(object):
    # Last detection
    __last_detection = None
    # Video capture
    __frame = None
    # Status flags
    activated = False
    suspended = True
    # Tasks
    __check_activated_task = None
    __check_suspended_task = None
    __capture_task = None

    def __init__(self, logger, configuration):
        self.logger = logger
        atexit.register(self.__del__)
        signal.signal(signal.SIGINT, self.__del__)
        self.logger.info('Configuring motion detector...')
        self.__config = configuration
        self.__log_file_path = self.__config.TMP_DIR + os.sep + 'webcam_motion_detection.log'
        # Time ranges for activation
        self.__times_on = dict()
        self.__times_on[1] = []
        self.__times_on[2] = []
        self.__times_on[3] = []
        self.__times_on[4] = []
        self.__times_on[5] = []
        self.__times_on[6] = []
        self.__times_on[7] = []
        if self.__config.ACTIVATION_TIMES and len(self.__config.ACTIVATION_TIMES) > 0:
            for value in self.__config.ACTIVATION_TIMES.split(','):
                fields = value.split('|')
                self.__times_on[int(fields[0])].append([datetime.strptime(fields[1], TIME_FORMAT).time(),
                                                        datetime.strptime(fields[2], TIME_FORMAT).time()])
        self.__video = cv2.VideoCapture(int(self.__config.VIDEO_DEVICE))
        if not self.__video:
            raise Exception('Device is not valid: ' + self.__config.VIDEO_DEVICE)
        self.__video.setExceptionMode(enable=True)
        self.__frame_lock = threading.Lock()
        # Scheduler
        self.__scheduler = sched.scheduler(time.time, time.sleep)
        self.__check_activated()
        self.__check_suspended()

    def __del__(self):
        try:
            if self.__video:
                # Release video device
                self.__video.release()
            if self.__config.GRAPHICAL:
                # Destroying all the windows
                cv2.destroyAllWindows()
        except Exception as e:
            self.logger.error('Cannot stop service: %s' % e, file=sys.stderr)

    def __notify(self, message=None):
        if not self.__config.SMTP_SERVER or not self.__config.SMTP_PORT:
            self.logger.warn('SMTP_SERVER or SMTP_PORT not specified in configuration, skipping email notification')
            return
        if not self.__config.SMTP_FROM or not self.__config.SMTP_TO:
            self.logger.warn('No email address specified, skipping email notification')
            return
        parts = []
        for file_path in glob.glob(self.__config.TMP_DIR + os.sep + '*.jpg'):
            if file_path == self.__config.CAPTURE_FILE:
                continue
            basename: str = os.path.basename(file_path)
            with open(file_path, "rb") as file:
                part = MIMEApplication(
                    file.read(),
                    Name=basename
                )
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename
            parts.append(part)
            os.unlink(file_path)
        if len(parts) == 0:
            return
        self.logger.info('Sending email to ' + self.__config.SMTP_TO)
        # noinspection PyTypeChecker
        server: smtplib.SMTP = None
        try:
            server = smtplib.SMTP(self.__config.SMTP_SERVER, self.__config.SMTP_PORT)
            msg = MIMEMultipart()
            msg['From'] = self.__config.SMTP_FROM
            msg['To'] = self.__config.SMTP_TO
            if message is None:
                mt = MIMEText(os.path.splitext(os.path.basename(__file__))[0] + ' completed', 'plain')
                mt['Subject'] = os.path.splitext(os.path.basename(__file__))[0] + ' completed'
            else:
                self.logger.debug(message)
                mt = MIMEText(os.path.splitext(os.path.basename(__file__))[0] + ' completed with error(s): ' + message + ', check logs', 'plain')
                mt['Subject'] = os.path.splitext(os.path.basename(__file__))[0] + ' completed with error(s)'
            msg['Subject'] = mt['Subject']
            mt['From'] = self.__config.SMTP_FROM
            mt['To'] = self.__config.SMTP_TO
            msg.attach(mt)
            if self.__log_file_path is not None:
                log_zip_file_path: str = self.__log_file_path + '.zip'
                basename: str = os.path.basename(log_zip_file_path)
                with zipfile.ZipFile(log_zip_file_path, 'w') as zf:
                    zf.write(self.__log_file_path)
                with open(log_zip_file_path, "rb") as file:
                    part = MIMEApplication(
                        file.read(),
                        Name=basename
                    )
                os.unlink(log_zip_file_path)
                part['Content-Disposition'] = 'attachment; filename="%s"' % basename
                msg.attach(part)
            for part in parts:
                msg.attach(part)
            if not self.__config.TEST:
                server.sendmail(msg['From'], self.__config.SMTP_TO, msg.as_string())
            else:
                self.logger.warn('Not sending (see configuration and TEST property')
        finally:
            if server:
                server.close()

    def __check_activated(self):
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
        self.activated = r
        self.logger.debug('activated: ' + str(self.activated) + ', suspended: ' + str(self.suspended))
        if self.activated and not self.suspended:
            self.start()
        self.__check_activated_task = self.__scheduler.enter(60, 1, self.__check_activated, ())

    def __check_suspended(self):
        self.logger.debug('Checking if suspended by detection of a secure device on the network...')
        r: bool = False
        if self.__config.MAC_ADDRESSES and len(self.__config.MAC_ADDRESSES) > 0:
            ip_v4 = find_ip_v4()
            nm = nmap.PortScanner()
            nm.scan(hosts=ip_v4.rsplit('.', 1)[0] + '.0/24', arguments='-sPn', sudo=True)
            hosts = nm.all_hosts()
            mac_addresses = self.__config.MAC_ADDRESSES.split(',')
            for host in hosts:
                data = nm[host]
                if data:
                    addresses = data['addresses']
                    if addresses and 'mac' in addresses and addresses['mac'] in mac_addresses:
                        if not self.__config.TEST:
                            r = True
                        else:
                            self.logger.warn('Suspended forced to false (see configuration and TEST property')
                        break
        self.suspended = r
        self.logger.debug('activated: ' + str(self.activated) + ', suspended: ' + str(self.suspended))
        if not self.suspended and self.activated:
            self.start()
        self.__check_suspended_task = self.__scheduler.enter(60, 1, self.__check_suspended, ())

    def __capture(self):
        self.logger.info('Starting capture...')
        # Assigning our static_back to None
        static_back = None
        # Infinite while loop to treat stack of image as video
        try:
            while self.activated and not self.suspended:
                now: datetime.datetime = datetime.now()
                # Reading frame(image) from video
                with self.__frame_lock:
                    check, self.__frame = self.__video.read()
                # Initializing motion = 0(no motion)
                motion: bool = False
                # Converting color image to gray_scale image
                gray = cv2.cvtColor(self.__frame, cv2.COLOR_BGR2GRAY)
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
                    if cv2.contourArea(contour) > 25000:
                        motion = True
                        (x, y, w, h) = cv2.boundingRect(contour)
                        # making green rectangle around the moving object
                        cv2.rectangle(self.__frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                        break
                if motion and (self.__last_detection is None or (now - self.__last_detection).total_seconds() > 1):
                    filename: str = self.__config.TMP_DIR + os.sep + 'webcam_motion_detection-' + str(now) + '.jpg'
                    self.logger.info('Motion detected adn stored to ' + filename)
                    cv2.imwrite(filename, self.__frame)
                    shutil.copy(filename, self.__config.CAPTURE_FILE)
                    self.__last_detection = now
                    static_back = gray
                if self.__last_detection and (now - self.__last_detection).total_seconds() > int(self.__config.NOTIFICATION_DELAY):
                    self.__notify('Motion detected using ' + self.__config.VIDEO_DEVICE_NAME)
                if self.__config.GRAPHICAL:
                    cv2.imshow("Color Frame", self.__frame)
                key = cv2.waitKey(1)
                # if q entered process will stop
                if key == ord('q'):
                    self.logger.info('Stopping...')
                    self.__scheduler.cancel(self.__check_activated_task)
                    self.__scheduler.cancel(self.__check_suspended_task)
                    break
        except Exception as e:
            self.logger.error('Stopping after failure: ' + repr(e))
            if self.__check_activated_task:
                self.__scheduler.cancel(self.__check_activated_task)
            if self.__check_suspended_task:
                self.__scheduler.cancel(self.__check_suspended_task)
        self.logger.info('Stopping capture...')
        self.__capture_task = None

    def start(self):
        self.logger.info('Start triggered')
        if self.__capture_task is None:
            self.__capture_task = self.__scheduler.enter(0, 1, self.__capture, ())
        else:
            self.logger.info('Capture already running...')

    def get_frame(self):
        with self.__frame_lock:
            return self.__frame.copy()
