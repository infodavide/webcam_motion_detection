# Python program to implement
# Webcam HTTP server for administration

import atexit
import base64
import configparser
import datetime
import io
import json
import logging
import multiprocessing
import os
import pathlib
import shutil
import signal
import sys
import threading
import time
from logging.handlers import RotatingFileHandler

import cv2
import flask
import flask_cors
import flask_socketio
import humanize
import psutil

from webcam_motion_detector import WebcamMotionDetector, ImageListener


class ObjectView(object):
    def __init__(self, d):
        self.__dict__ = d

    """ Returns the string representation of the view """

    def __str__(self):
        return str(self.__dict__)


class ConcreteImageListener(ImageListener):

    def __init__(self):
        super().__init__()
        self.__lock = threading.RLock()
        self._image: bytes = b''

    def on_image(self, image: bytearray) -> None:
        with self.__lock:
            self._image = image

    def get_image(self) -> bytes:
        with self.__lock:
            return self._image


config: ObjectView = None
logger: logging.Logger = None
root_path: str = None
motion_detector: WebcamMotionDetector = None
image_listener: ConcreteImageListener = ConcreteImageListener()
no_image_available: bytes = b''


def create_rotating_log(path: str):
    global config
    result: logging.Logger = logging.getLogger("Webcam HTTP server")
    result.setLevel(logging.INFO)
    path_obj: pathlib.Path = pathlib.Path(path)
    if not os.path.exists(path_obj.parent.absolute()):
        os.makedirs(path_obj.parent.absolute())
    if os.path.exists(path):
        open(path, 'w').close()
    else:
        path_obj.touch()
    # noinspection Spellchecker
    formatter: logging.Formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler: logging.Handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    result.addHandler(console_handler)
    file_handler: logging.Handler = RotatingFileHandler(path, maxBytes=1024 * 1024 * 5, backupCount=5)
    # noinspection PyUnresolvedReferences
    file_handler.setLevel(config.LOG_LEVEL)
    file_handler.setFormatter(formatter)
    result.addHandler(file_handler)
    # noinspection PyUnresolvedReferences
    result.setLevel(config.LOG_LEVEL)
    return result


def configure():
    global config, image_listener, logger, root_path, motion_detector, no_image_available
    config_parser = configparser.ConfigParser()
    config_parser.optionxform = str
    config_parser.read(str(pathlib.Path(__file__).parent) + os.sep + 'webcam_motion_detection.conf')
    config = ObjectView(dict(config_parser['Main']))
    # noinspection PyUnresolvedReferences
    log_file_path: str = config.TMP_DIR + os.sep + 'webcam_motion_detection.log'
    root_path = str(pathlib.Path(__file__).parent) + os.sep + 'webapp'
    logger = create_rotating_log(log_file_path)
    logger.info('Configuring...')
    atexit.register(shutdown)
    signal.signal(signal.SIGINT, shutdown)
    try:
        motion_detector = WebcamMotionDetector(logger, config)
    except Exception as e:
        logger.error(e)
        sys.exit(1)
    is_success, image_buffer = cv2.imencode('.jpg', cv2.imread(root_path + '/images/no-image-available.jpg'))
    if is_success:
        no_image_available = image_buffer.tobytes()
    else:
        logger.error("no-image-available.jpg is missing")
        print("no-image-available.jpg is missing")
        sys.exit(1)


def get_video():
    global logger, image_listener, no_image_available
    while True:
        array: bytes = image_listener.get_image()
        if array is b'':
            array = no_image_available
        yield b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + array + b'\r\n'
        time.sleep(0.1)

        
def shutdown():
    global logger, webapp
    if globals().get('webapp'):
        func = webapp.env.get('werkzeug.server.shutdown')
        if func is None:
            logger.warning('Shutdown function not available')
        else:
            func()


configure()
# noinspection PyUnresolvedReferences
logger.info('Starting web server')
webapp = flask.Flask(__name__, static_url_path=root_path)
webapp.config['SECRET_KEY'] = 'th!s_!s_s3cr3t'
websocket = flask_socketio.SocketIO(webapp, cors_allowed_origins="*", ping_timeout=120, path='/websocket',
                                    async_mode='gevent', logger=False)


@webapp.route('/css/<path:path>', methods=['GET'])
def send_css(path):
    global logger, root_path
    # noinspection PyUnresolvedReferences
    logger.debug('Sending: ' + str(root_path) + os.sep + 'static' + os.sep + 'css' + os.sep + path)
    return flask.send_from_directory(str(root_path) + os.sep + 'css', path)


@webapp.route('/images/<path:path>', methods=['GET'])
def send_images(path):
    global logger, root_path
    # noinspection PyUnresolvedReferences
    logger.debug('Sending: ' + str(root_path) + os.sep + 'static' + os.sep + 'images' + os.sep + path)
    return flask.send_from_directory(str(root_path) + os.sep + 'images', path)


@webapp.route('/js/<path:path>', methods=['GET'])
def send_js(path):
    global logger, root_path
    # noinspection PyUnresolvedReferences
    logger.debug('Sending: ' + str(root_path) + os.sep + 'static' + os.sep + 'js' + os.sep + path)
    return flask.send_from_directory(str(root_path) + os.sep + 'js', path)


@webapp.route('/', methods=['GET'])
def send_home():
    global logger, root_path
    # noinspection PyUnresolvedReferences
    logger.debug('Sending: ' + str(root_path) + os.sep + 'static' + os.sep + 'index.html')
    return flask.send_file(str(root_path) + os.sep + 'index.html')


@webapp.route('/rest/app/health', methods=["GET"])
def rest_app_health():
    global logger
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
        logger.warning('Cannot stop service: %s' % e, file=sys.stderr)
    uptime = humanize.naturaldelta(datetime.timedelta(seconds=round(time.time() - psutil.boot_time(), 0)))
    result['sys'] = {'processors': multiprocessing.cpu_count(), 'cpuLoad': os.getloadavg(), 'uptime': uptime,
                     'cpuTemperature': cpu_temperature}
    if storage_status > 90 or cpu_temperature > 90 or memory_status > 90:
        result['health'] = -1
    else:
        result['health'] = 0
    return flask.jsonify(result)


@flask_cors.cross_origin
@websocket.on_error_default  # handles all namespaces without an explicit error handler
def default_error_handler(e):
    global logger
    logger.error('Websocket error: ' + e)
    pass


@flask_cors.cross_origin
@websocket.on('connect')
def handle_connect():
    global logger
    logger.info('Websocket connected')
    flask_socketio.emit('message', 'You are welcome.')


@flask_cors.cross_origin
@websocket.on('subscribe')
def handle_subscribe(topic):
    global logger, motion_detector
    logger.info('Websocket subscribing to topic: ' + topic)
    flask_socketio.join_room(topic)
    flask_socketio.emit('message', 'You subscribed to ' + topic)


@websocket.on('unsubscribe')
def handle_unsubscribe(topic):
    global logger, motion_detector
    logger.info('Websocket unsubscribing to topic: ' + topic)
    flask_socketio.leave_room(topic)
    flask_socketio.emit('message', 'You unsubscribed from ' + topic)


@flask_cors.cross_origin
@websocket.on('disconnect')
def handle_disconnect():
    global logger
    logger.info('Websocket disconnected')


@webapp.route("/video", methods=['GET'])
def send_video():
    global logger, motion_detector
    # noinspection PyUnresolvedReferences
    logger.debug('Streaming video...')
    motion_detector.add_listener(image_listener)
    return flask.Response(get_video(), mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == '__main__':
    # noinspection PyUnresolvedReferences
    logger.info('Starting on port: ' + config.HTTP_PORT)
    # Cross Origin Resource Sharing
    flask_cors.CORS(webapp)
    # noinspection PyUnresolvedReferences
    websocket.run(webapp, host='0.0.0.0', port=int(config.HTTP_PORT), debug=False)
    print('Stopping')
