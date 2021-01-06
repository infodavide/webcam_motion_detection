# -*- coding: utf-*-
# Webcam Motion Detector Configuration
import json
import os
import pathlib
import tempfile
import threading

from id_classes_utils import import_files_of_dir, subclasses_of, DictOfTypes
from id_utils import del_none, is_json

from builtins import list
from datetime import datetime, time
from extension import Extension, ExtensionConfig
from id_setting import Setting, Settings
from typing import cast, List, Dict

TIME_FORMAT: str = '%H:%M'


class DetectionZone(object):
    def __init__(self):
        """
        Initialize an empty zone.
        """
        self.x1: int = -1
        self.y1: int = -1
        self.x2: int = -1
        self.y2: int = -1

    def clone(self):
        r: DetectionZone = DetectionZone()
        r.x1 = self.x1
        r.y1 = self.y1
        r.x2 = self.x2
        r.y2 = self.y2
        return r

    def parse(self, value: any) -> None:
        """
        Parse the list object describing coordinates x1, y1, x2, y2 or a JSON array like: [ -1, -1, -1, -1 ].
        :param value: the list object or the JSON representation
        :return:
        """
        obj = None
        if isinstance(value, list):
            obj = value
        elif isinstance(value, str):
            obj = is_json(value)
        if not isinstance(obj, list):
            raise ValueError('Invalid JSON for detection zone: ' + value)
        data: list = cast(list, obj)
        self.x1 = data[0]
        self.y1 = data[1]
        self.x2 = data[2]
        self.y2 = data[3]

    def to_json_object(self) -> list:
        """
        Return the list object used to get the JSON view.
        :return: the list object
        """
        result: list = list()
        result.append(self.x1)
        result.append(self.y1)
        result.append(self.x2)
        result.append(self.y2)
        return result

    def to_json(self) -> str:
        """
        Return the JSON view.
        :return: the JSON data
        """
        return json.dumps(self.to_json_object())

    def __str__(self) -> str:
        """
        Return the textual view.
        :return: the text
        """
        return self.to_json()


class Period:
    def __init__(self, day: int, start: datetime.time, end: datetime.time):
        self._day: int = day
        self._start: datetime.time = start
        self._end: datetime.time = end

    def clone(self):
        return Period(self._day, self._start, self._end)

    def get_day(self) -> int:
        return self._day

    def get_start(self) -> datetime.time:
        return self._start

    def get_end(self) -> datetime.time:
        return self._start

    def set_day(self, day: int):
        if day < 0 or day > 6:
            raise ValueError('Invalid value: ' + str(day))
        self._day = day

    def set_start(self, start: datetime.time):
        if self._end and self._end < start:
            raise ValueError('Invalid value: ' + str(start))
        self._start = start

    def set_end(self, end: datetime.time):
        if self._start and self._start > end:
            raise ValueError('Invalid value: ' + str(end))
        self._end = end

    def to_json_object(self) -> list:
        """
        Return the list object used to get the JSON view.
        :return: the list object
        """
        result: list = list()
        result.append(self._day)
        result.append(self._start.strftime(TIME_FORMAT))
        result.append(self._end.strftime(TIME_FORMAT))
        return result

    def to_json(self) -> str:
        """
        Return the JSON view.
        :return: the JSON data
        """
        return json.dumps(self.to_json_object())

    def __str__(self) -> str:
        """
        Return the textual view.
        :return: the text
        """
        return self.to_json()


Periods = List[Period]


class ActivationPeriods(Periods):
    def __init__(self):
        """
        Initialize the object to always activate the detection.
        """
        self.append(list())
        self.append(list())
        self.append(list())
        self.append(list())
        self.append(list())
        self.append(list())
        self.append(list())

    def clone(self):
        r: ActivationPeriods = ActivationPeriods()
        for day in range(len(self) - 1):
            periods: Periods = self[day]
            for period in periods:
                r[day].append(period.clone())
        return r

    def add(self, day: int, start: datetime.time, end: datetime.time) -> None:
        """
        Add the time interval associated to the given day of week
        :param day: the day of week
        :param start: the start time
        :param end: the end time
        :return:
        """
        if day > 6 or day < 0:
            raise ValueError('Invalid value for day: ' + repr(day))
        periods: Periods = self[day]
        for period in periods:
            if period.get_start() <= start <= period.get_end():
                if end < period.get_end():
                    return
                period.set_end(end)
                return
            if period.get_start() <= end <= period.get_end():
                if start > period.get_start():
                    return
                period.set_start(start)
                return
        periods.append(Period(day, start, end))

    def get(self, day: int) -> Periods:
        """
        Return the time interval associated to the given day of week
        :param day: the day of week
        :return: the time interval
        """
        return self[day % 7]

    def __delitem__(self, day: int) -> None:
        """
        Delete the data associated to a day
        :param day:
        :return:
        """
        self[day] = Periods()

    def is_in(self, value: datetime) -> bool:
        periods: Periods = self[value.weekday()]
        for period in periods:
            if period.get_start() <= value.time() <= period.get_end():
                return True
        return False

    def parse(self, value: any) -> None:
        """
        Parse the list object describing the time interval per day of week or a JSON array like: [ [ "08:30", "23:00" ], [ "08:30", "23:00" ], etc.
        :param value: the list object or the JSON representation
        :return:
        """
        obj = None
        if isinstance(value, list):
            obj = value
        elif isinstance(value, str):
            obj = is_json(value)
        if not isinstance(obj, list):
            raise ValueError('Invalid JSON for activation zones: ' + value)
        data: list = cast(list, obj)
        for item in data:
            if not item:
                raise ValueError('Invalid string value for activation periods (missing day): ' + repr(item))
            if not len(item) == 3:
                raise ValueError(
                    'Invalid string value for activation periods (wrong number of times): ' + repr(item))
            self.add(item[0], datetime.strptime(item[1], TIME_FORMAT).time(),
                       datetime.strptime(item[2], TIME_FORMAT).time())

    def to_json_object(self) -> list:
        """
        Return the list object used to get the JSON view.
        :return: the list object
        """
        result: list = list()
        for day in [0, 1, 2, 3, 4, 5, 6]:
            periods: Periods = cast(Periods, self.get(day))
            items: list = list()
            for period in periods:
                items.append(period.to_json_object())
            result.append(items)
        return result

    def to_json(self) -> str:
        """
        Return the JSON view.
        :return: the JSON data
        """
        return json.dumps(self.to_json_object())

    def __str__(self) -> str:
        """
        Return the textual view.
        :return: the text
        """
        return self.to_json()


ListOfStrings = List[str]
DictOfStrings = Dict[str, str]


class MacAddresses(DictOfStrings):
    @staticmethod
    def _validate(key: str) -> None:
        """
        Validate the given MAC address.
        :param key:  the MAC address
        :return:
        :raise ValueError: MAC address is invalid
        """
        if not key or len(key) == 0:
            raise ValueError('Invalid string value for MAC address: ' + key)
        parts = key.split(':')
        if not len(parts) == 6:
            raise ValueError('Invalid string value for MAC address: ' + key)

    def clone(self):
        r: MacAddresses = MacAddresses()
        for k in sorted(self.keys()):
            r[k] = self[k]
        return r

    def setdefault(self, key, value=None):
        """
        Override the method
        :param key: the key
        :param value:  the value
        :return:
        """
        if key not in self:
            MacAddresses._validate(key)
            self[key] = value
        return self[key]

    def __setitem__(self, key: str, value: str) -> None:
        """
        Override the method
        :param key: the key
        :param value:  the value
        :return:
        """
        MacAddresses._validate(key)
        super().__setitem__(key, value)

    def parse(self, value: any) -> None:
        """
        Parse the dict object or JSON representation like: { "40:40:A7:92:F5:00": "My device 1", "40:40:A7:92:F5:01": "My device 2", etc.
        :param value: the dict object or JSON
        :return:
        """
        obj = None
        if isinstance(value, Dict):
            obj = value
        elif isinstance(value, str):
            obj = is_json(value)
        if not isinstance(obj, Dict):
            raise ValueError('Invalid JSON for MAC addresses: ' + value)
        data: dict = cast(dict, obj)
        self.clear()
        for address, comment in data.items():
            self[address] = comment

    def to_json_object(self) -> dict:
        """
        Return the dict object used to get the JSON view.
        :return: the dict object
        """
        result: dict = dict()
        # noinspection PyTypeChecker
        for k in sorted(self.keys()):
            result[k] = self[k]
        return result

    def to_json(self) -> str:
        """
        Return the JSON view.
        :return: the JSON data
        """
        return json.dumps(self.to_json_object())

    def __str__(self) -> str:
        """
        Return the textual view.
        :return: the text
        """
        return self.to_json()


VIDEO_DEVICE_NAME_KEY: str = 'video_device'
VIDEO_DEVICE_ADDR_KEY: str = 'video_device_address'
NOTIFICATION_DELAY_KEY: str = 'notification_delay'
GRAPHICAL_KEY: str = 'window_enabled'
TEMP_DIR_KEY: str = 'temp_dir'
HTTP_PORT_KEY: str = 'http_port'
USER_KEY: str = 'user'
USER_DISPLAY_NAME_KEY: str = 'user_display_name'
EMAIL_KEY: str = 'email'
PASSWORD_KEY: str = 'password'
LOG_LEVEL_KEY: str = 'log_level'
TEST_KEY: str = 'test_enabled'
DEFAULT_USER: str = 'admin'
DEFAULT_PASSWORD: str = 'secret'
DEFAULT_NOTIFICATION_DELAY: int = 5
DEFAULT_LOG_LEVEL: str = 'INFO'
DEFAULT_VIDEO_DEVICE_NAME: str = 'Camera 1'
DEFAULT_VIDEO_DEVICE_ADDRESS: str = '0'
DEFAULT_HTTP_PORT: int = 8080
DEFAULT_TEMP_DIR: str = tempfile.gettempdir() + os.sep + 'Webcam_motion_detection'
ListOfExtensionConfigs = List[ExtensionConfig]


class WebcamMotionConfig(object):
    def __init__(self):
        """
        Initialize the configuration and its settings.
        """
        import_files_of_dir(str(pathlib.Path(__file__).parent) + os.sep + 'drivers')
        import_files_of_dir(str(pathlib.Path(__file__).parent) + os.sep + 'extensions')
        self.__file_lock: threading.Lock = threading.Lock()
        # noinspection PyTypeChecker
        self._path: str = None
        self._settings: Settings = Settings()
        self._settings[VIDEO_DEVICE_NAME_KEY]: Setting[str] = Setting(DEFAULT_VIDEO_DEVICE_NAME)
        self._settings[VIDEO_DEVICE_ADDR_KEY]: Setting[str] = Setting(DEFAULT_VIDEO_DEVICE_ADDRESS)
        self._settings[NOTIFICATION_DELAY_KEY]: Setting[int] = Setting(DEFAULT_NOTIFICATION_DELAY, 0, 3600)
        self._settings[GRAPHICAL_KEY]: Setting[bool] = Setting(False)
        self._settings[TEMP_DIR_KEY]: Setting[str] = Setting(DEFAULT_TEMP_DIR)
        self._settings[HTTP_PORT_KEY]: Setting[int] = Setting(DEFAULT_HTTP_PORT, 1, 65535)
        self._settings[EMAIL_KEY]: Setting[str] = Setting('', 0, 255)
        self._settings[USER_DISPLAY_NAME_KEY]: Setting[str] = Setting('', 4, 128)
        self._settings[USER_KEY]: Setting[str] = Setting(DEFAULT_USER, 4, 96, True)
        self._settings[PASSWORD_KEY]: Setting[str] = Setting(DEFAULT_PASSWORD, 4, 32)
        self._settings[LOG_LEVEL_KEY]: Setting[str] = Setting(DEFAULT_LOG_LEVEL)
        self._settings[TEST_KEY]: Setting[bool] = Setting(False)
        self._zone: DetectionZone = DetectionZone()
        self._activation_periods: ActivationPeriods = ActivationPeriods()
        self._mac_addresses: MacAddresses = MacAddresses()
        self._extension_configs: ListOfExtensionConfigs = list()

    def clone(self):
        r: WebcamMotionConfig = WebcamMotionConfig()
        r._path: str = self._path
        r._settings: Settings = self._settings.clone()
        r._settings[VIDEO_DEVICE_NAME_KEY]: Setting[str] = self._settings[VIDEO_DEVICE_NAME_KEY].clone()
        r._settings[VIDEO_DEVICE_ADDR_KEY]: Setting[str] = self._settings[VIDEO_DEVICE_ADDR_KEY].clone()
        r._settings[NOTIFICATION_DELAY_KEY]: Setting[int] = self._settings[NOTIFICATION_DELAY_KEY].clone()
        r._settings[GRAPHICAL_KEY]: Setting[bool] = self._settings[GRAPHICAL_KEY].clone()
        r._settings[TEMP_DIR_KEY]: Setting[str] = self._settings[TEMP_DIR_KEY].clone()
        r._settings[HTTP_PORT_KEY]: Setting[int] = self._settings[HTTP_PORT_KEY].clone()
        r._settings[EMAIL_KEY]: Setting[str] = self._settings[EMAIL_KEY].clone()
        r._settings[USER_DISPLAY_NAME_KEY]: Setting[str] = self._settings[USER_DISPLAY_NAME_KEY].clone()
        r._settings[USER_KEY]: Setting[str] = self._settings[USER_KEY].clone()
        r._settings[PASSWORD_KEY]: Setting[str] = self._settings[PASSWORD_KEY].clone()
        r._settings[LOG_LEVEL_KEY]: Setting[str] = self._settings[LOG_LEVEL_KEY].clone()
        r._settings[TEST_KEY]: Setting[bool] = self._settings[TEST_KEY].clone()
        r._zone: DetectionZone = self._zone.clone()
        r._activation_periods: ActivationPeriods = self._activation_periods.clone()
        r._mac_addresses: MacAddresses = self._mac_addresses.clone()
        for extension_configs in self._extension_configs:
            r._extension_configs.append(extension_configs.clone())
        return r

    def get_extension_configs(self) -> ListOfExtensionConfigs:
        """
        Return the configurations of the extensions.
        :return: the list of configurations of the extensions
        """
        return self._extension_configs

    def get_video_device_name(self) -> str:
        """
        Return the name of the video device.
        :return: the name of the video device
        """
        return self._settings[VIDEO_DEVICE_NAME_KEY].get_value()

    def get_video_device_address(self) -> str:
        """
        Return the address of the video device.
        :return: the address of the video device
        """
        return self._settings[VIDEO_DEVICE_ADDR_KEY].get_value()

    def get_notification_delay(self) -> int:
        """
        Return the delay of notification in seconds.
        :return: the delay in seconds
        """
        return self._settings[NOTIFICATION_DELAY_KEY].get_value()

    def get_zone(self) -> DetectionZone:
        """
        Return the coordinates used for detection.
        :return: the zone object
        """
        return self._zone

    def is_graphical(self) -> bool:
        """
        Return the flag used to activate a graphical window with the video.
        :return: the boolean flag
        """
        return self._settings[GRAPHICAL_KEY].get_value()

    def get_temp_dir(self) -> str:
        """
        Return the path of the temporary directory.
        :return: the path of the temporary directory
        """
        return self._settings[TEMP_DIR_KEY].get_value()

    def get_activation_periods(self) -> ActivationPeriods:
        """
        Return the intervals of time of detection.
        :return: the intervals of time
        """
        return self._activation_periods

    def get_mac_addresses(self) -> MacAddresses:
        """
        Return the MAC addresses used to suspend detection.
        :return: the object describing the MAC addresses
        """
        return self._mac_addresses

    def get_http_port(self) -> int:
        """
        Return the TCP port of the web interface
        :return: the TCP port
        """
        return self._settings[HTTP_PORT_KEY].get_value()

    def get_user(self) -> str:
        """
        Return the user name used dor authentication on the web interface.
        :return: the user name
        """
        return self._settings[USER_KEY].get_value()

    def get_user_display_name(self) -> str:
        """
        Return the user full name.
        :return: the user full name
        """
        return self._settings[USER_DISPLAY_NAME_KEY].get_value()

    def get_email(self) -> str:
        """
        Return the email address used to send notifications to.
        :return: the email address
        """
        return self._settings[EMAIL_KEY].get_value()

    def get_password(self) -> str:
        """
        Return the password (MD5) used dor authentication on the web interface.
        :return: the password as MD5
        """
        return self._settings[PASSWORD_KEY].get_value()

    def get_log_level(self) -> str:
        """
        Return the log level (debug, info, warning, error)
        :return: the log level
        """
        return self._settings[LOG_LEVEL_KEY].get_value()

    def get_settings(self) -> Settings:
        """
        Return all the settings.
        :return: the settings object
        """
        return self._settings

    def is_test(self) -> bool:
        """
        Return the flag used to activate test features.
        :return: the boolean flag
        """
        return self._settings[TEST_KEY].get_value()

    def set_video_device_name(self, value: str) -> None:
        """
        Set the name of the video device.
        :param value: the name
        :return:
        """
        if value is None or len(value) == 0:
            raise ValueError('Invalid video device name: ' + str(value))
        self._settings[VIDEO_DEVICE_NAME_KEY].set_value(value)

    def set_video_device_address(self, value: str) -> None:
        """
        Set the address of the video device.
        :param value: the hardware address
        :return:
        """
        if value is None or len(value) == 0:
            raise ValueError('Invalid video device address: ' + str(value))
        self._settings[VIDEO_DEVICE_ADDR_KEY].set_value(value)

    def set_notification_delay(self, value: int) -> None:
        """
        Set the delay of notification in seconds.
        :param value: the delay in seconds
        :return:
        """
        if value is None or value <= 0:
            raise ValueError('Invalid notification delay: ' + str(value))
        self._settings[NOTIFICATION_DELAY_KEY].set_value(value)

    def set_zone(self, value: DetectionZone) -> None:
        """
        Set the zone object.
        :param value: the zone
        :return:
        """
        if value is None:
            raise ValueError('Invalid detection zone')
        self._zone = value

    def set_graphical(self, value: bool) -> None:
        """
        Set the flag used to activate the graphical window displaying the video.
        :param value: the boolean
        :return:
        """
        self._settings[GRAPHICAL_KEY].set_value(value)

    def set_temp_dir(self, value: str):
        """
        Set the path of the temporary directory
        :param value: the path of the temporary directory
        :return:
        """
        if value is None or len(value) == 0:
            raise ValueError('Invalid temporary directory: ' + str(value))
        self._settings[TEMP_DIR_KEY].set_value(value)

    def set_activation_periods(self, value: ActivationPeriods) -> None:
        """
        Set the activation periods object.
        :param value: the periods
        :return:
        """
        if value is None:
            raise ValueError('Invalid activation periods')
        self._activation_periods = value

    def set_mac_addresses(self, value: MacAddresses) -> None:
        """
        Set object describing the MAC addresses.
        :param value: the MAC addresses
        :return:
        """
        if value is None:
            raise ValueError('Invalid MAC addresses')
        self._mac_addresses = value

    def set_http_port(self, value: int) -> None:
        """
        Set the TCP port of the web interface.
        :param value: the TCP port
        :return:
        """
        if value is None or value <= 1:
            raise ValueError('Invalid HTTP port: ' + str(value))
        self._settings[HTTP_PORT_KEY].set_value(value)

    def set_user(self, value: str) -> None:
        """
        Set the user name used dor authentication on the web interface.
        :param value: the user name
        :return;
        """
        if value is None or len(value) == 0:
            raise ValueError('Invalid administrator username: ' + str(value))
        self._settings[USER_KEY].set_value(value)

    def set_user_display_name(self, value: str) -> None:
        """
        Set the user full name.
        :param value: the user full name
        :return:
        """
        if value is None:
            raise ValueError('Administrator full name is invalid')
        self._settings[USER_DISPLAY_NAME_KEY].set_value(value)

    def set_email(self, value: str) -> None:
        """
        Set the email address used to send notifications to.
        :param value: the email address
        :return:
        """
        if value is None:
            raise ValueError('Email is invalid')
        self._settings[EMAIL_KEY].set_value(value)

    def set_password(self, value: str) -> None:
        """
        Set the password (MD5) used dor authentication on the web interface.
        :param value: the password as MD5
        :return:
        """
        if value is None or len(value) == 0:
            raise ValueError('Invalid administrator password: ' + str(value))
        self._settings[PASSWORD_KEY].set_value(value)

    def set_log_level(self, value: str) -> None:
        """
        Set the log level (debug, info, warning, error)
        :param value: the log level
        :return:
        """
        if value is None or len(value) == 0:
            raise ValueError('Invalid logging level: ' + str(value))
        if not (value == 'INFO' or value == 'DEBUG' or value == 'WARNING' or value == 'ERROR' or value == 'CRITICAL'):
            raise ValueError('Invalid logging level: ' + value)
        self._settings[LOG_LEVEL_KEY].set_value(value)

    def set_test(self, value: bool) -> None:
        """
        Set the flag used to activate the test features.
        :param value: the boolean
        :return:
        """
        self._settings[TEST_KEY].set_value(value)

    def write(self, path: str = None) -> None:
        """
        Write the configuration to the file.
        :param path: the path of the file
        :return:
        """
        data = self._settings.to_json_object()
        data['zone'] = self._zone.to_json_object()
        data['activation_periods'] = self._activation_periods.to_json_object()
        data['mac_addresses'] = self._mac_addresses.to_json_object()
        configs: dict = dict()
        for config in self._extension_configs:
            configs[config.get_extension_class_name()] = config.to_json_object()
        data['extensions'] = configs
        del_none(data)
        with self.__file_lock:
            if path:
                with open(path, 'w+') as file:
                    json.dump(data, file, indent=4, sort_keys=True)
                    file.flush()
            elif self._path:
                with open(self._path, 'w+') as file:
                    json.dump(data, file, indent=4, sort_keys=True)
                    file.flush()
            else:
                raise ValueError('Path is not set when trying to write configuration')

    def read(self, path: str) -> None:
        """
        Read the configuration from the file.
        :param path: the path of the file
        :return:
        """
        self._path = path
        available_extensions: DictOfTypes = dict()
        for subclass in subclasses_of(Extension):
            available_extensions[subclass.__name__] = subclass
        with self.__file_lock:
            with open(path, 'r') as file:
                data: dict = json.load(file)
                self._settings.parse(data)
                for k in sorted(data.keys()):
                    if k == 'zone':
                        self.get_zone().parse(data[k])
                    elif k == 'activation_periods':
                        self.get_activation_periods().parse(data[k])
                    elif k == 'mac_addresses':
                        self.get_mac_addresses().parse(data[k])
                    elif k == 'extensions':
                        if not isinstance(data[k], dict):
                            continue
                        for k2 in sorted(data[k].keys()):
                            if isinstance(data[k][k2], dict):
                                cls = available_extensions[k2]
                                config: ExtensionConfig = cast(ExtensionConfig, getattr(cls, 'new_config_instance')())
                                config.parse(data[k][k2])
                                self._extension_configs.append(config)
