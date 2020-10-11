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
VERSION: str = '1.0'


class DetectionZone(object):
    def __init__(self):
        self.x1: int = -1
        self.y1: int = -1
        self.x2: int = -1
        self.y2: int = -1

    def parse(self, value: any) -> None:
        # Expecting something like: [ -1, -1, -1, -1 ]
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
        result: list = list()
        result.append(self.x1)
        result.append(self.y1)
        result.append(self.x2)
        result.append(self.y2)
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_json_object())

    def __str__(self) -> str:
        return self.to_json()


Times = List[datetime.time]
Periods = List[Times]


class ActivationPeriods(Periods):
    def __init__(self):
        self.append((time(0, 0), time(23, 59)))
        self.append((time(0, 0), time(23, 59)))
        self.append((time(0, 0), time(23, 59)))
        self.append((time(0, 0), time(23, 59)))
        self.append((time(0, 0), time(23, 59)))
        self.append((time(0, 0), time(23, 59)))
        self.append((time(0, 0), time(23, 59)))

    def put(self, day: int, start: datetime.time, end: datetime.time) -> None:
        self[day] = [start, end]

    def get(self, day: int) -> Times:
        return self[day % 7]

    def __delitem__(self, day: int) -> None:
        self[day] = []

    def parse(self, value: any) -> None:
        # Expecting something like: [ [ "08:30", "23:00" ], [ "08:30", "23:00" ], etc.
        obj = None
        if isinstance(value, list):
            obj = value
        elif isinstance(value, str):
            obj = is_json(value)
        if not isinstance(obj, list):
            raise ValueError('Invalid JSON for activation zones: ' + value)
        data: list = cast(list, obj)
        for day in [0, 1, 2, 3, 4, 5, 6]:
            parts = data[day]
            if not parts:
                raise ValueError('Invalid string value for activation periods (missing day): ' + str(day))
            if not len(parts) == 2:
                raise ValueError(
                    'Invalid string value for activation periods (wrong number of times): ' + repr(parts))
            self.put(day, datetime.strptime(parts[0], TIME_FORMAT).time(),
                       datetime.strptime(parts[1], TIME_FORMAT).time())

    def to_json_object(self) -> list:
        result: list = list()
        for day in [0, 1, 2, 3, 4, 5, 6]:
            times: Times = cast(Times, self.get(day))
            item: list = list()
            if len(times) != 2:
                result.append(item)
                continue
            item.append(times[0].strftime(TIME_FORMAT))
            item.append(times[1].strftime(TIME_FORMAT))
            result.append(item)
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_json_object())

    def __str__(self) -> str:
        return self.to_json()


ListOfStrings = List[str]
DictOfStrings = Dict[str, str]


class MacAddresses(DictOfStrings):
    @staticmethod
    def _validate(key: str) -> None:
        if not key or len(key) == 0:
            raise ValueError('Invalid string value for MAC address: ' + key)
        parts = key.split(':')
        if not len(parts) == 6:
            raise ValueError('Invalid string value for MAC address: ' + key)

    def setdefault(self, key, value=None):
        if key not in self:
            MacAddresses._validate(key)
            self[key] = value
        return self[key]

    def __setitem__(self, key: str, value: str) -> None:
        MacAddresses._validate(key)
        super().__setitem__(key, value)

    def parse(self, value: any) -> None:
        # Expecting something like: { "40:40:A7:92:F5:00": "My device 1", "40:40:A7:92:F5:01": "My device 2", etc.
        obj = None
        if isinstance(value, Dict):
            obj = value
        elif isinstance(value, str):
            obj = is_json(value)
        if not isinstance(obj, Dict):
            raise ValueError('Invalid JSON for MAC addresses: ' + value)
        data: dict = cast(dict, obj)
        for address, comment in data.items():
            self[address] = comment

    def to_json_object(self) -> dict:
        result: dict = dict()
        # noinspection PyTypeChecker
        for address, comment in self.items():
            result[address] = comment
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_json_object())

    def __str__(self) -> str:
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
VERSION_KEY: str = 'version'
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
        self._settings[VERSION_KEY]: Setting[str] = Setting(VERSION, 4, 96, True)
        self._zone: DetectionZone = DetectionZone()
        self._activation_periods: ActivationPeriods = ActivationPeriods()
        self._mac_addresses: MacAddresses = MacAddresses()
        self._extension_configs: ListOfExtensionConfigs = list()

    def get_extension_configs(self) -> ListOfExtensionConfigs:
        return self._extension_configs

    def get_video_device_name(self) -> str:
        return self._settings[VIDEO_DEVICE_NAME_KEY].get_value()

    def get_video_device_address(self) -> str:
        return self._settings[VIDEO_DEVICE_ADDR_KEY].get_value()

    def get_notification_delay(self) -> int:
        return self._settings[NOTIFICATION_DELAY_KEY].get_value()

    def get_zone(self) -> DetectionZone:
        return self._zone

    def is_graphical(self) -> bool:
        return self._settings[GRAPHICAL_KEY].get_value()

    def get_temp_dir(self) -> str:
        return self._settings[TEMP_DIR_KEY].get_value()

    def get_activation_periods(self) -> ActivationPeriods:
        return self._activation_periods

    def get_mac_addresses(self) -> MacAddresses:
        return self._mac_addresses

    def get_http_port(self) -> int:
        return self._settings[HTTP_PORT_KEY].get_value()

    def get_user(self) -> str:
        return self._settings[USER_KEY].get_value()

    def get_user_display_name(self) -> str:
        return self._settings[USER_DISPLAY_NAME_KEY].get_value()

    def get_email(self) -> str:
        return self._settings[EMAIL_KEY].get_value()

    def get_password(self) -> str:
        return self._settings[PASSWORD_KEY].get_value()

    def get_log_level(self) -> str:
        return self._settings[LOG_LEVEL_KEY].get_value()

    def get_settings(self) -> Settings:
        return self._settings

    def is_test(self) -> bool:
        return self._settings[TEST_KEY].get_value()

    def set_video_device_name(self, value: str) -> None:
        if value is None or len(value) == 0:
            raise ValueError('Invalid video device name: ' + str(value))
        self._settings[VIDEO_DEVICE_NAME_KEY].set_value(value)

    def set_video_device_address(self, value: str) -> None:
        if value is None or len(value) == 0:
            raise ValueError('Invalid video device address: ' + str(value))
        self._settings[VIDEO_DEVICE_ADDR_KEY].set_value(value)

    def set_notification_delay(self, value: int) -> None:
        if value is None or value <= 0:
            raise ValueError('Invalid notification delay: ' + str(value))
        self._settings[NOTIFICATION_DELAY_KEY].set_value(value)

    def set_zone(self, value: DetectionZone) -> None:
        if value is None:
            raise ValueError('Invalid detection zone')
        self._zone = value

    def set_graphical(self, value: bool) -> None:
        self._settings[GRAPHICAL_KEY].set_value(value)

    def set_temp_dir(self, value: str):
        if value is None or len(value) == 0:
            raise ValueError('Invalid temporary directory: ' + str(value))
        self._settings[TEMP_DIR_KEY].set_value(value)

    def set_activation_periods(self, value: ActivationPeriods) -> None:
        if value is None:
            raise ValueError('Invalid activation periods')
        self._activation_periods = value

    def set_mac_addresses(self, value: MacAddresses) -> None:
        if value is None:
            raise ValueError('Invalid MAC addresses')
        self._mac_addresses = value

    def set_http_port(self, value: int) -> None:
        if value is None or value <= 1:
            raise ValueError('Invalid HTTP port: ' + str(value))
        self._settings[HTTP_PORT_KEY].set_value(value)

    def set_user(self, value: str) -> None:
        if value is None or len(value) == 0:
            raise ValueError('Invalid administrator username: ' + str(value))
        self._settings[USER_KEY].set_value(value)

    def set_user_display_name(self, value: str) -> None:
        if value is None:
            raise ValueError('Administrator full name is invalid')
        self._settings[USER_DISPLAY_NAME_KEY].set_value(value)

    def set_email(self, value: str) -> None:
        if value is None:
            raise ValueError('Email is invalid')
        self._settings[EMAIL_KEY].set_value(value)

    def set_password(self, value: str) -> None:
        if value is None or len(value) == 0:
            raise ValueError('Invalid administrator password: ' + str(value))
        self._settings[PASSWORD_KEY].set_value(value)

    def set_log_level(self, value: str) -> None:
        if value is None or len(value) == 0:
            raise ValueError('Invalid logging level: ' + str(value))
        if not (value == 'INFO' or value == 'DEBUG' or value == 'WARNING' or value == 'ERROR' or value == 'CRITICAL'):
            raise ValueError('Invalid logging level: ' + value)
        self._settings[LOG_LEVEL_KEY].set_value(value)

    def set_test(self, value: bool) -> None:
        self._settings[TEST_KEY].set_value(value)

    def write(self, path: str = None) -> None:
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
        self._path = path
        available_extensions: DictOfTypes = dict()
        for subclass in subclasses_of(Extension):
            available_extensions[subclass.__name__] = subclass
        with self.__file_lock:
            with open(path, 'r') as file:
                data: dict = json.load(file)
                self._settings.parse(data)
                for k, v in data.items():
                    if k == 'zone':
                        self.get_zone().parse(v)
                    elif k == 'activation_periods':
                        self.get_activation_periods().parse(v)
                    elif k == 'mac_addresses':
                        self.get_mac_addresses().parse(v)
                    elif k == 'extensions':
                        if not isinstance(v, dict):
                            continue
                        for k2, v2 in v.items():
                            if isinstance(v2, dict):
                                cls = available_extensions[k2]
                                config: ExtensionConfig = cast(ExtensionConfig, getattr(cls, 'new_config_instance')())
                                config.parse(v2)
                                self._extension_configs.append(config)
