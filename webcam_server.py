# Python program to implement
# Webcam HTTP server for administration

import atexit
import configparser
import cv2
import datetime
import flask
import humanize
import logging
import multiprocessing
import os
import pathlib
import psutil
import signal
import shutil
import sys
import time

from logging.handlers import RotatingFileHandler
from webcam_motion_detector import WebcamMotionDetector


class ObjectView(object):
    def __init__(self, d):
        self.__dict__ = d

    """ Returns the string representation of the view """

    def __str__(self):
        return str(self.__dict__)


config = None
logger = None
root_path = None
motion_detector = None


def create_rotating_log(path):
    global config
    result = logging.getLogger("Webcam HTTP server")
    result.setLevel(logging.INFO)
    path_obj = pathlib.Path(path)
    if not os.path.exists(path_obj.parent.absolute()):
        os.makedirs(path_obj.parent.absolute())
    if not os.path.exists(path):
        path_obj.touch()
    # noinspection Spellchecker
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    result.addHandler(console_handler)
    file_handler = RotatingFileHandler(path, maxBytes=1024 * 1024 * 5, backupCount=5)
    # noinspection PyUnresolvedReferences
    file_handler.setLevel(config.LOG_LEVEL)
    file_handler.setFormatter(formatter)
    result.addHandler(file_handler)
    # noinspection PyUnresolvedReferences
    result.setLevel(config.LOG_LEVEL)
    return result


def configure():
    global config, logger, root_path, motion_detector
    config_parser = configparser.ConfigParser()
    config_parser.optionxform = str
    config_parser.read(str(pathlib.Path(__file__).parent) + os.sep + 'webcam_motion_detection.conf')
    config = ObjectView(dict(config_parser['Main']))
    # noinspection PyUnresolvedReferences
    log_file_path = config.TMP_DIR + os.sep + 'webcam_motion_detection.log'
    root_path = str(pathlib.Path(__file__).parent) + os.sep + 'webapp'
    logger = create_rotating_log(log_file_path)
    logger.info('Configuring...')
    atexit.register(shutdown)
    signal.signal(signal.SIGINT, shutdown)
    motion_detector = WebcamMotionDetector(logger, config)


def shutdown():
    global web_server
    web_server.terminate()
    web_server.join()


def get_video():
    global motion_detector
    while True:
        # noinspection PyUnresolvedReferences
        frame = motion_detector.get_frame()
        if frame is None:
            continue
        (flag, encodedImage) = cv2.imencode(".jpg", frame)
        if not flag:
            continue
        yield b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n'


configure()
# noinspection PyUnresolvedReferences
logger.info('Starting web server')
webapp = flask.Flask(__name__, static_url_path=root_path)


@webapp.route('/css/<path:path>', methods=['GET'])
def send_css(path):
    global logger
    # noinspection PyUnresolvedReferences
    logger.debug('Sending: ' + str(root_path) + os.sep + 'static' + os.sep + 'css' + os.sep + path)
    return flask.send_from_directory(str(root_path) + os.sep + 'css', path)


@webapp.route('/images/<path:path>', methods=['GET'])
def send_images(path):
    global logger
    # noinspection PyUnresolvedReferences
    logger.debug('Sending: ' + str(root_path) + os.sep + 'static' + os.sep + 'images' + os.sep + path)
    return flask.send_from_directory(str(root_path) + os.sep + 'images', path)


@webapp.route('/js/<path:path>', methods=['GET'])
def send_js(path):
    global logger
    # noinspection PyUnresolvedReferences
    logger.debug('Sending: ' + str(root_path) + os.sep + 'static' + os.sep + 'js' + os.sep + path)
    return flask.send_from_directory(str(root_path) + os.sep + 'js', path)


@webapp.route('/', methods=['GET'])
def send_home():
    global logger
    # noinspection PyUnresolvedReferences
    logger.debug('Sending: ' + str(root_path) + os.sep + 'static' + os.sep + 'index.html')
    return flask.send_file(str(root_path) + os.sep + 'index.html')


@webapp.route('/rest/app/health', methods=["GET"])
def rest_app_health():
    result = dict()
    disks = []
    storage_status = 0
    for partition in psutil.disk_partitions():
        disk_total, disk_used, disk_free = shutil.disk_usage(partition.mountpoint)
        # noinspection PyUnresolvedReferences
        logger.debug(partition.mountpoint + ':\n\ttotal: ' + str(disk_total) + ', used: ' + str(disk_used))
        disk_status = round(disk_used * 100 / disk_total, 2)
        if storage_status == 0 or storage_status > disk_status:
            storage_status = disk_status
        disk_total = humanize.naturalsize(disk_total)
        disk_used = humanize.naturalsize(disk_used)
        disk_free = humanize.naturalsize(disk_free)
        disk = {'name': partition.device + ' (' + partition.mountpoint + ')', 'status': disk_status,
                'usable': disk_free, 'total': disk_total, 'used': disk_used}
        disks.append(disk)
    result['storage'] = {'status': storage_status, 'disks': disks}
    memory = psutil.virtual_memory()
    # noinspection PyUnresolvedReferences
    logger.debug('memory:\n\ttotal: ' + str(memory.total) + ', used: ' + str(memory.used))
    memory_status = round(memory.used * 100 / memory.total, 2)
    memory_total = humanize.naturalsize(memory.total)
    memory_free = humanize.naturalsize(memory.available)
    memory_used = humanize.naturalsize(memory.used)
    swap_memory = psutil.swap_memory()
    swap_memory_total = humanize.naturalsize(swap_memory.total)
    swap_memory_used = humanize.naturalsize(swap_memory.used)
    result['memory'] = {
        'sys': {'status': memory_status, 'free': memory_free, 'total': memory_total, 'used': memory_used},
        'swap': {'total': swap_memory_total, 'used': swap_memory_used}}
    cpu_temperature = 0
    try:
        cpu_temperature = psutil.sensors_temperatures().get('coretemp')[0].current
    except Exception as e:
        # noinspection PyUnresolvedReferences
        logger.warn('Cannot stop service: %s' % e, file=sys.stderr)
    uptime = humanize.naturaldelta(datetime.timedelta(seconds=round(time.time() - psutil.boot_time(), 0)))
    result['sys'] = {'processors': multiprocessing.cpu_count(), 'cpuLoad': os.getloadavg(), 'uptime': uptime,
                     'cpuTemperature': cpu_temperature}
    if storage_status > 90 or cpu_temperature > 90 or memory_status > 90:
        result['health'] = -1
    else:
        result['health'] = 0
    return flask.jsonify(result)


@webapp.route("/video")
def video():
    return flask.Response(get_video(), mimetype="multipart/x-mixed-replace; boundary=frame")


# noinspection PyUnresolvedReferences
webapp_args = {'host': '0.0.0.0', 'port': int(config.HTTP_PORT)}
web_server = multiprocessing.Process(target=webapp.run, kwargs=webapp_args)
web_server.start()
# noinspection PyUnresolvedReferences
logger.info('Listening on port: ' + config.HTTP_PORT)
sys.exit(0)
