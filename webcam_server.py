#!/usr/bin/python
# -*- coding: utf-*-
# Webcam HTTP server for administration

import atexit
import datetime
import io
import json
import logging
import multiprocessing
import os
import pathlib
import shutil
import signal
import statistics
import sys
import threading
import time
import traceback
from logging.handlers import RotatingFileHandler
from typing import cast

import flask
import flask_cors
import humanize
import psutil
import requests
from expiringdict import ExpiringDict
from flask_accept import accept

from drivers.webcam_mock_driver import WebcamMockDriver
from id_classes_utils import subclasses_of
from id_network_utils import find_local_mac_address, find_ip_v4, find_netmask, find_gateway, is_dhcp_enabled, find_wifi_ssid
from id_utils import is_json
from id_webapp_auth import decode_auth_token, encode_auth_token
from webcam_driver import WebcamDriver
from webcam_motion_config import WebcamMotionConfig, Settings, GRAPHICAL_KEY, TEST_KEY, PASSWORD_KEY, TEMP_DIR_KEY, VIDEO_DEVICE_ADDR_KEY, LOG_LEVEL_KEY
from webcam_motion_detector import ImageListener, WebcamMotionDetector


class ConcreteImageListener(ImageListener):
    def __init__(self):
        """
        Initialize the image listener used by the web interface.
        """
        super().__init__()
        self.__lock = threading.RLock()
        self._image: bytes = b''

    def on_image(self, image: bytes) -> None:
        """
        Store internally the image read by the video driver.
        :param image: the image read by the video driver.
        :return:
        """
        with self.__lock:
            self._image = image

    def get_image(self) -> bytes:
        """
        Return the last image read by the video driver.
        :return:
        """
        with self.__lock:
            return self._image


VERSION: str = '1.0'
APPLICATION_JSON: str = 'application/json'
SENDING_MSG: str = 'Sending: '
NOT_A_JSON_REQUEST: str = 'Request was not JSON'
CHARSET: str = 'utf-8'
BOUNDARY: str = 'bdy' + str(time.time())
SECRET_KEY: str = os.urandom(24).decode(errors="ignore")
# noinspection PyTypeChecker
authentications_cache: ExpiringDict = None
# noinspection PyTypeChecker
config: WebcamMotionConfig = None
# noinspection PyTypeChecker
logger: logging.Logger = None
# noinspection PyTypeChecker
root_path: str = None
# noinspection PyTypeChecker
motion_detector: WebcamMotionDetector = None
image_listener: ConcreteImageListener = ConcreteImageListener()
no_image_available: bytes = b''
webapp_stopped = True


def create_rotating_log(path: str) -> logging.Logger:
    """
    Create the logger with file rotation.
    :param path: the path of the main log file
    :return: the logger
    """
    global config
    result: logging.Logger = logging.getLogger("Webcam HTTP server")
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
    console_handler.setLevel(config.get_log_level())
    console_handler.setFormatter(formatter)
    result.addHandler(console_handler)
    file_handler: logging.Handler = RotatingFileHandler(path, maxBytes=1024 * 1024 * 5, backupCount=5)
    # noinspection PyUnresolvedReferences
    file_handler.setLevel(config.get_log_level())
    file_handler.setFormatter(formatter)
    result.addHandler(file_handler)
    # noinspection PyUnresolvedReferences
    result.setLevel(config.get_log_level())
    return result


def shutdown():
    """
    Clean shutdown of the detector and HTTP server.
    :return:
    """
    global logger, config
    if globals().get('motion_detector'):
        logger.info('Stopping motion detector...')
        try:
            globals().get('motion_detector').stop()
        except Exception as ex:
            print('Error when shutting down the motion detector: %s' % ex, file=sys.stderr)
    if globals().get('webapp') and not webapp_stopped:
        logger.info('Stopping webapp...')
        try:
            requests.post('http://localhost:' + str(config.get_http_port()) + '/rest/app/shutdown')
        except Exception as ex:
            print('Error when shutting down the application: %s' % ex, file=sys.stderr)


CONFIG_PATH = str(pathlib.Path(__file__).parent) + os.sep + 'webcam_motion_detection.json'


def configure():
    """
    Configure the application by creating the logger, the authentication cache, the video driver, the detector, reading the default image, registering the signal hooks.
    :return:
    """
    global CONFIG_PATH, authentications_cache, config, image_listener, logger, root_path, motion_detector, no_image_available
    config = WebcamMotionConfig()
    config.read(CONFIG_PATH)
    # noinspection PyUnresolvedReferences
    log_file_path: str = config.get_temp_dir() + os.sep + 'webcam_motion_detection.log'
    root_path = str(pathlib.Path(__file__).parent) + os.sep + 'webapp'
    logger = create_rotating_log(log_file_path)
    logger.info('Configuring...')
    atexit.register(shutdown)
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    authentications_cache = ExpiringDict(max_len=20, max_age_seconds=3600)
    no_image_available_path: str = root_path + '/images/no-image-available.jpg'
    if os.path.exists(no_image_available_path):
        logger.info('Loading image from: ' + no_image_available_path)
        with open(no_image_available_path, 'rb') as image_file:
            no_image_available = image_file.read()
        image_listener.on_image(no_image_available)
    else:
        logger.error("no-image-available.jpg is missing")
        print("no-image-available.jpg is missing")
        sys.exit(1)
    # noinspection PyTypeChecker
    driver: WebcamDriver = None
    if config.is_test():
        print('Using test driver: ' + WebcamMockDriver.__name__)
        driver = WebcamMockDriver(logger, config, image_listener, str(pathlib.Path(__file__).parent) + os.sep + 'drivers' + os.sep + 'cattura')
    else:
        for subclass in subclasses_of(WebcamDriver):
            if 'Mock' in subclass.__name__:
                continue
            print('Using driver: ' + subclass.__name__)
            driver = subclass(logger, config)
            break
    try:
        motion_detector = WebcamMotionDetector(logger, config, driver)
    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback, limit=6, file=sys.stderr)
        logger.error(ex)
        sys.exit(1)


def get_video():
    """
    Return the video stream (using yield).
    :return:
    """
    global logger, image_listener, no_image_available, motion_detector
    while motion_detector.is_running():
        array: bytes = image_listener.get_image()
        if array is None or len(array) == 0:
            array = no_image_available
        yield b'--' + BOUNDARY.encode() + b'\r\n' + b'Content-Type: image/jpeg\r\n\r\n' + array + b'\r\n'
        time.sleep(0.1)


def get_frame() -> bytes:
    """
    Return the last frame read by the video driver, as JPEG.
    :return: the binary data of the JPEG image
    """
    global logger, image_listener, no_image_available, motion_detector
    array: bytes = image_listener.get_image()
    i = 0
    while motion_detector.is_running() and (array is None or len(array) == 0) and i < 5:
        i += 1
        time.sleep(0.2)
        array: bytes = image_listener.get_image()
    if array is None or len(array) == 0:
        logger.warning('Frame is not available')
        array = no_image_available
    return array


def assert_authenticated(request: flask.Request) -> str:
    """
    Check authentication.
    :param request: the request containing the 'Authorization' header
    :return: the name of the user or None
    """
    global logger, authentications_cache, SECRET_KEY
    token: str = request.headers.get('Authorization')
    if token is None:
        token = request.cookies.get('token')
        if token is not None:
            token = token.replace('%20', ' ')
    if token is None:
        logger.debug('Header "Authorization" was not found in request')
        # noinspection PyTypeChecker
        return None
    logger.debug('Authentication token: ' + token)
    # noinspection PyTypeChecker
    username: str = None
    try:
        username = decode_auth_token(SECRET_KEY, token)
    except ValueError as ve:
        logger.warning('Authentication failed: ' + str(ve))
    if username is None or len(username) == 0 or username not in authentications_cache:
        logger.debug('Authentication token is not valid')
        # noinspection PyTypeChecker
        return None
    logger.debug('Authentication user: ' + username)
    return username


configure()
motion_detector.start()
# noinspection PyUnresolvedReferences
logger.info('Starting web server')
webapp = flask.Flask(__name__, static_url_path=root_path)
webapp.config['SECRET_KEY'] = 'th!s_!s_s3cr3t'


@webapp.after_request
def set_response_headers(response: flask.Response):
    """
    Set the cache headers according to the resource.
    :param response: the response object
    :return:
    """
    path: str = flask.request.path
    if path.endswith('/video') or path.endswith('/frame') or ('/rest/' in path) or ('text/html' in response.content_type.lower()):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    else:
        response.headers['Cache-Control'] = 'private, max-age=31536000'
    response.headers['Server'] = 'Webcam server'
    return response


@webapp.route('/css/<path:path>', methods=['GET'])
def http_get_css(path):
    """
    Return the CSS resource.
    :param path: the path of the CSS resource
    :return:
    """
    global logger, root_path
    # noinspection PyUnresolvedReferences
    logger.debug(SENDING_MSG + str(root_path) + os.sep + 'static' + os.sep + 'css' + os.sep + path)
    return flask.send_from_directory(str(root_path) + os.sep + 'css', path)


@webapp.route('/images/<path:path>', methods=['GET'])
def http_get_images(path):
    """
    Return the image resource.
    :param path: the path of the image resource
    :return:
    """
    global logger, root_path
    # noinspection PyUnresolvedReferences
    logger.debug(SENDING_MSG + str(root_path) + os.sep + 'static' + os.sep + 'images' + os.sep + path)
    return flask.send_from_directory(str(root_path) + os.sep + 'images', path)


@webapp.route('/js/<path:path>', methods=['GET'])
def http_get_js(path):
    """
    Return the javascript resource.
    :param path: the path of the javascript resource
    :return:
    """
    global logger, root_path
    # noinspection PyUnresolvedReferences
    logger.debug(SENDING_MSG + str(root_path) + os.sep + 'static' + os.sep + 'js' + os.sep + path)
    return flask.send_from_directory(str(root_path) + os.sep + 'js', path)


@webapp.route('/templates/<path:path>', methods=['GET'])
def http_get_templates(path):
    """
    Return the template resource.
    :param path: the path of the template resource
    :return:
    """
    global logger, root_path
    # noinspection PyUnresolvedReferences
    logger.debug(SENDING_MSG + str(root_path) + os.sep + 'static' + os.sep + 'templates' + os.sep + path)
    return flask.send_from_directory(str(root_path) + os.sep + 'templates', path)


@webapp.route('/', methods=['GET'])
def http_get_home():
    """
    Return the index content as HTML.
    :return: the response object
    """
    global logger, root_path
    # noinspection PyUnresolvedReferences
    logger.debug(SENDING_MSG + str(root_path) + os.sep + 'static' + os.sep + 'index.html')
    return flask.send_file(str(root_path) + os.sep + 'index.html')


@webapp.route('/rest/app/health', methods=["GET"])
def http_get_health():
    """
    Return the health information as JSON.
    :return: the response object
    """
    global logger, motion_detector
    result = dict()
    storage_status = 0
    for partition in psutil.disk_partitions():
        disk_total, disk_used, disk_free = shutil.disk_usage(partition.mountpoint)
        # noinspection PyUnresolvedReferences
        logger.debug(partition.mountpoint + ':\n\ttotal: ' + str(disk_total) + ', used: ' + str(disk_used))
        disk_status = round(disk_used * 100 / disk_total, 2)
        if storage_status == 0 or storage_status < disk_status:
            storage_status = disk_status
    memory = psutil.virtual_memory()
    # noinspection PyUnresolvedReferences
    logger.debug('memory:\n\ttotal: ' + str(memory.total) + ', used: ' + str(memory.used))
    memory_status = round(memory.used * 100 / memory.total, 2)
    cpu_temperature = 0
    try:
        cpu_temperature = psutil.sensors_temperatures().get('coretemp')[0].current
    except Exception as ex:
        # noinspection PyUnresolvedReferences
        logger.warning('Cannot stop service: %s' % ex, file=sys.stderr)
    if storage_status > 90 or cpu_temperature > 90 or memory_status > 90:
        result['health'] = -2
    elif not motion_detector.is_running():
        result['health'] = -1
    elif not motion_detector.is_activated():
        result['health'] = 1
    elif motion_detector.is_suspended():
        result['health'] = 2
    else:
        result['health'] = 0
    return flask.jsonify(result)


@webapp.route('/rest/app/status', methods=["GET"])
def http_get_status():
    """
    Return the health information as JSON.
    :return: the response object
    """
    global logger, motion_detector
    accept_lang: str = flask.request.headers.get('Accept-Language')
    if accept_lang is not None:
        try:
            accept_lang = accept_lang.split(',')[0].replace('-','_')
            logger.debug('Using language: ' + accept_lang)
            humanize.i18n.activate(accept_lang)
        except Exception as e:
            logger.debug('No translation for language: ' + accept_lang + ' (' + str(e) + ')')
    result = dict()
    result['version'] = VERSION
    if not motion_detector.is_running():
        result['status'] = 'running'
    if not motion_detector.is_activated():
        result['status'] = 'activated'
    if motion_detector.is_suspended():
        result['status'] = 'suspended'
    result['storage'] = []
    for partition in psutil.disk_partitions():
        disk_total, disk_used, disk_free = shutil.disk_usage(partition.mountpoint)
        # noinspection PyUnresolvedReferences
        logger.debug(partition.mountpoint + ':\n\ttotal: ' + str(disk_total) + ', used: ' + str(disk_used))
        disk = {'name': partition.device + ' (' + partition.mountpoint + ')', 'total': disk_total, 'used': disk_used}
        result['storage'].append(disk)
    memory = psutil.virtual_memory()
    # noinspection PyUnresolvedReferences
    logger.debug('memory:\n\ttotal: ' + str(memory.total) + ', used: ' + str(memory.used))
    swap_memory = psutil.swap_memory()
    result['memory'] = {
        'sys': {'total': memory.total, 'used': memory.used},
        'swap': {'total': swap_memory.total, 'used': swap_memory.used}}
    cpu_temperature = 0
    try:
        cpu_temperature = psutil.sensors_temperatures().get('coretemp')[0].current
    except Exception as ex:
        # noinspection PyUnresolvedReferences
        logger.warning('Cannot stop service: %s' % ex, file=sys.stderr)
    uptime = humanize.naturaldelta(datetime.timedelta(seconds=round(time.time() - psutil.boot_time(), 0)))
    ipv4 = find_ip_v4()
    result['sys'] = {'processors': multiprocessing.cpu_count(), 'cpuLoad': statistics.median(os.getloadavg()),
                     'uptime': uptime,
                     'cpuTemperature': cpu_temperature,
                     'macAddress': find_local_mac_address(ipv4),
                     'ipv4Address': ipv4,
                     'netmask' : find_netmask(ipv4),
                     'gateway' : find_gateway(),
                     'dhcp': is_dhcp_enabled(ipv4),
                     'ssid': find_wifi_ssid()}
    return flask.jsonify(result)


@webapp.route("/frame", methods=['GET'])
def http_get_frame():
    """
    Return the last frame read by the video driver as JPEG image.
    :return: the response object
    """
    global logger, motion_detector, no_image_available
    username: str = assert_authenticated(flask.request)
    # noinspection PyUnresolvedReferences
    logger.debug('Getting last frame...')
    if username is None:
        return flask.send_file(io.BytesIO(no_image_available), mimetype='image/jpeg', as_attachment=False,
                               attachment_filename='frame.jpg')
    motion_detector.add_listener(image_listener)
    return flask.send_file(io.BytesIO(get_frame()), mimetype='image/jpeg', as_attachment=False,
                           attachment_filename='frame.jpg')


@webapp.route("/video", methods=['GET'])
def http_get_video():
    """
    Return the video stream read by the video driver.
    :return: the response object
    """
    global logger, motion_detector
    username: str = assert_authenticated(flask.request)
    if username is None:
        return flask.send_file(io.BytesIO(no_image_available), mimetype='image/jpeg', as_attachment=False,
                               attachment_filename='frame.jpg')
    # noinspection PyUnresolvedReferences
    logger.debug('Streaming video...')
    motion_detector.add_listener(image_listener)
    return flask.Response(get_video(), mimetype='multipart/x-mixed-replace; boundary=' + BOUNDARY)


@webapp.route("/rest/login", methods=['POST'])
def http_post_login():
    """
    Process the authentication request describing the user name and its password (as MD5).
    :return: the response object with the authentication token in the 'X-Authorization' header or a 40X error code
    """
    global logger, authentications_cache, config, SECRET_KEY
    if not flask.request.is_json:
        return flask.make_response(NOT_A_JSON_REQUEST, 406)
    username: str = assert_authenticated(flask.request)
    if username is not None:
        resp = flask.make_response('', 200)
        resp.headers['X-Authorization'] = flask.request.headers.get('Authorization')
        return resp
    # noinspection PyUnresolvedReferences
    json_content = flask.request.data.decode(CHARSET)
    logger.debug('Login: ' + json_content)
    obj: any = is_json(json_content)
    if not isinstance(obj, dict):
        return flask.make_response('', 400)
    logger.debug('Login data is JSON formatted')
    data: dict = cast(dict, obj)
    if 'name' not in data or not config.get_user() == data['name']:
        logger.info('Wrong username')
        return flask.make_response('', 400)
    if 'password' not in data or not config.get_password() == data['password']:
        logger.info('Wrong password')
        return flask.make_response('', 400)
    username: str = data['name']
    data['email'] = config.get_email()
    data['role'] = 'ADMINISTRATOR'
    data['id'] = 1
    data['displayName'] = config.get_user_display_name()
    resp = flask.make_response(json.dumps(data), 200)
    token: str = encode_auth_token(SECRET_KEY, username)
    authentications_cache[username] = token
    resp.headers['X-Authorization'] = token
    logger.debug('Login successful: ' + username + ' (X-Authorization: ' + token + ')')
    return resp


@webapp.route("/rest/logout", methods=['POST'])
def http_post_logout():
    """
    Process the logout request.
    :return: the response object
    """
    global logger, authentications_cache, config, SECRET_KEY
    username: str = assert_authenticated(flask.request)
    if username is not None:
        logger.debug('Logout: ' + username)
        authentications_cache[username] = None
    return flask.make_response('', 200)


@webapp.route("/rest/settings", methods=['GET'])
def http_get_settings():
    """
    Return the configuration as settings in JSON format.
    :return: the response object
    """
    global logger, config
    # noinspection PyUnresolvedReferences
    logger.debug('Getting settings...')
    copy: Settings = config.get_settings().clone()
    del copy[GRAPHICAL_KEY]
    del copy[TEST_KEY]
    del copy[TEMP_DIR_KEY]
    del copy[VIDEO_DEVICE_ADDR_KEY]
    del copy[LOG_LEVEL_KEY]
    copy[PASSWORD_KEY].set_value(len(copy[PASSWORD_KEY].get_value())*'*')
    for extension_config in config.get_extension_configs():
        extension_name: str = extension_config.get_extension_class_name()
        copy[extension_name+'.enabled'] = extension_config.is_enabled()
        for k in sorted(extension_config.get_settings().keys()):
            copy[extension_name+'.'+k] = extension_config.get_settings()[k].clone()
    return flask.Response(copy.to_full_json(), mimetype=APPLICATION_JSON)


@webapp.route("/rest/settings", methods=['POST'])
@accept(APPLICATION_JSON)
def http_post_settings():
    """
    Saves the settings into the configuration object and file if authentication is valid.
    :return: the response object (40X or 200)
    """
    global logger, config, CHARSET, motion_detector
    if not flask.request.is_json:
        return flask.make_response(NOT_A_JSON_REQUEST, 406)
    username: str = assert_authenticated(flask.request)
    if username is None:
        return flask.make_response('', 403)
    # noinspection PyUnresolvedReferences
    json_content = flask.request.data.decode(CHARSET)
    logger.debug('Setting settings: ' + json_content)
    # config.get_settings().parse(json_content)
    # config.write()
    # motion_detector.restart()
    return flask.make_response('', 200)


@webapp.route("/rest/periods", methods=['GET'])
def http_get_periods():
    """
    Return the time intervals used to activate detection in JSON format.
    :return: the response object
    """
    global logger, config
    # noinspection PyUnresolvedReferences
    logger.debug('Getting periods...')
    return flask.Response(config.get_activation_periods().to_json(), mimetype=APPLICATION_JSON)


@webapp.route("/rest/periods", methods=['POST'])
@accept(APPLICATION_JSON)
def http_post_periods():
    """
    Saves the time intervals used to activate detection into the configuration object and file if authentication is valid.
    :return: the response object (40X or 200)
    """
    global logger, config, CHARSET, motion_detector
    if not flask.request.is_json:
        return flask.make_response(NOT_A_JSON_REQUEST, 406)
    username: str = assert_authenticated(flask.request)
    if username is None:
        return flask.make_response('', 403)
    # noinspection PyUnresolvedReferences
    json_content = flask.request.data.decode(CHARSET)
    logger.debug('Setting periods: ' + json_content)
    config.get_activation_periods().parse(json_content)
    config.write()
    motion_detector.restart()
    return flask.make_response('', 200)


@webapp.route("/rest/coordinates", methods=['GET'])
def http_get_coordinates():
    """
    Return the coordinates of the detection zone in JSON format.
    :return: the response object
    """
    global logger, config
    # noinspection PyUnresolvedReferences
    logger.debug('Getting coordinates...')
    if config.get_zone():
        data: str = config.get_zone().to_json()
    else:
        data: str = '{"x1": -1, "y1": -1, "x2": -1, "y2": -1}'
    return flask.Response(data, mimetype=APPLICATION_JSON)


@webapp.route("/rest/coordinates", methods=['POST'])
@accept(APPLICATION_JSON)
def http_post_coordinates():
    """
    Saves the coordinates of the detection zone into the configuration object and file if authentication is valid.
    :return: the response object (40X or 200)
    """
    global logger, config, CHARSET, motion_detector
    if not flask.request.is_json:
        return flask.make_response(NOT_A_JSON_REQUEST, 406)
    username: str = assert_authenticated(flask.request)
    if username is None:
        return flask.make_response('', 403)
    # noinspection PyUnresolvedReferences
    json_content = flask.request.data.decode(CHARSET)
    logger.debug('Setting coordinates: ' + json_content)
    config.get_zone().parse(json_content)
    config.write()
    motion_detector.restart()
    return flask.make_response('', 200)


@webapp.route("/rest/filters", methods=['GET'])
def http_get_filters():
    """
    Return the MAC addresses in JSON format.
    :return: the response object
    """
    global logger, config, motion_detector
    # noinspection PyUnresolvedReferences
    available = flask.request.args.get('available')
    data: str = '{}'
    if available is None:
        logger.debug('Getting filters...')
        if config.get_mac_addresses():
            data = config.get_mac_addresses().to_json()
    else:
        data = json.dumps(motion_detector.get_scan_results())
    return flask.Response(data, mimetype=APPLICATION_JSON)


@webapp.route("/rest/filters", methods=['POST'])
@accept(APPLICATION_JSON)
def http_post_filters():
    """
    Saves the MAC addresses used to suspend detection into the configuration object and file if authentication is valid.
    :return: the response object (40X or 200)
    """
    global logger, config, CHARSET, motion_detector
    if not flask.request.is_json:
        return flask.make_response(NOT_A_JSON_REQUEST, 406)
    username: str = assert_authenticated(flask.request)
    if username is None:
        return flask.make_response('', 403)
    # noinspection PyUnresolvedReferences
    json_content = flask.request.data.decode(CHARSET)
    logger.debug('Setting filters: ' + json_content)
    config.get_mac_addresses().parse(json_content)
    config.write()
    motion_detector.restart()
    return flask.make_response('', 200)


@webapp.route('/rest/app/shutdown', methods=['POST'])
def http_post_shutdown():
    """
    Call the clean shutdown function (only allowed by local HTTP request)
    :return: the response (200 or 500 if not running or 405 if not posted from localhost)
    """
    if not (flask.request.remote_addr == 'localhost' or flask.request.remote_addr == '127.0.0.1'):
        return flask.make_response('', 405)
    logger.info('Requesting shutdown...')
    func = flask.request.environ.get('werkzeug.server.shutdown')
    if func is None:
        return flask.make_response('Not running with the Werkzeug Server', 500)
    func()
    return flask.make_response('Server shutting down...', 200)


if __name__ == '__main__':
    # Start of the web interface (with clean shutdown on error)
    # noinspection PyUnresolvedReferences
    logger.info('Starting on port: ' + str(config.get_http_port()))
    # Cross Origin Resource Sharing
    flask_cors.CORS(webapp)
    # noinspection PyUnresolvedReferences
    try:
        webapp_stopped = False
        webapp.run(host='0.0.0.0', port=int(config.get_http_port()), debug=False, threaded=True)
    except TypeError as e:
        print('Error: %s' % e, file=sys.stderr)
    finally:
        webapp_stopped = True
        shutdown()
    print('Application stopped')
sys.exit(0)
