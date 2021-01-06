# -*- coding: utf-*-
# Extension definition
import json
import logging
import threading
import time

from abc import abstractmethod
from id_setting import Setting, Settings

ENABLED_KEY: str = 'enabled'
TRIGGERING_INTERVAL_KEY: str = 'triggering_interval'


class ExtensionConfig(object):
    def __init__(self, extension_class_name: str):
        """
        Set the class name of the associated extension.
        :param extension_class_name: the class name
        """
        self._type: str = extension_class_name
        self._settings: Settings = Settings()
        self._settings[ENABLED_KEY]: Setting = Setting(False)
        self._settings[TRIGGERING_INTERVAL_KEY]: Setting = Setting[int](-1)

    def get_extension_class_name(self) -> str:
        """
        Return the class name of the associated extension.
        :return: the class name
        """
        return self._type

    def get_settings(self) -> Settings:
        return self._settings

    def is_enabled(self) -> bool:
        """
        Return True if associated extension is enabled.
        :return: True if associated extension is enabled
        """
        return self._settings[ENABLED_KEY].get_value()

    def set_enabled(self, value: bool) -> None:
        """
        Set True to enable the associated extension.
        :param value: the flag
        :return:
        """
        self._settings[ENABLED_KEY].set_value(value)

    def get(self, value: str):
        """
        Get the value of the setting associated to the given key.
        :param value: the key of the setting
        :return: the value of the setting
        """
        return self._settings[value]

    def get_triggering_interval(self) -> int:
        """
        Get the interval in seconds used to trigger the extension.
        :return: the interval in seconds
        """
        return self._settings[TRIGGERING_INTERVAL_KEY].get_value()

    def set_triggering_interval(self, value: int) -> None:
        """
        Set the interval in seconds used to trigger the extension.
        :param value: the interval in seconds
        :return:
        """
        self._settings[TRIGGERING_INTERVAL_KEY].set_value(value)

    def parse(self, value: any) -> None:
        """
        Parse the JSON or object.
        :param value: the JSON or object
        :return:
        """
        self._settings.parse(value)

    def to_json_object(self) -> dict:
        """
        Return the dict object used to get the JSON view.
        :return: the dict object
        """
        return self._settings.to_json_object()

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


SERVER_KEY: str = 'server'
PORT_KEY: str = 'port'
USER_KEY: str = 'user'
PASSWORD_KEY: str = 'password'


class NetExtensionConfig(ExtensionConfig):
    def __init__(self, extension_class_name: str):
        """
        Set the class name of the associated extension.
        :param extension_class_name: the class name
        """
        super().__init__(extension_class_name)
        self._settings[SERVER_KEY]: Setting = Setting[str]('')
        self._settings[PORT_KEY]: Setting = Setting[int](-1)
        self._settings[USER_KEY]: Setting = Setting[str]('')
        self._settings[PASSWORD_KEY]: Setting = Setting[str]('')

    def get_server(self) -> str:
        """
        Return the IP or host name of the server.
        :return: the IP or host name of the server
        """
        return self._settings[SERVER_KEY].get_value()

    def set_server(self, value: str) -> None:
        """
        Set the IP or host name of the server.
        :param value: the IP or host name of the server
        :return:
        """
        self._settings[SERVER_KEY].set_value(value)

    def get_port(self) -> int:
        """
        Return the TCP port of the server.
        :return: the TCP port of the server
        """
        return self._settings[PORT_KEY].get_value()

    def set_port(self, value: int) -> None:
        """
        Set the TCP port of the server.
        :param value: the TCP port of the server
        :return:
        """
        self._settings[PORT_KEY].set_value(value)

    def get_user(self) -> str:
        """
        Return the user name used for authentication on the server.
        :return: the user name
        """
        return self._settings[USER_KEY].get_value()

    def set_user(self, value: str) -> None:
        """
        Set the user name used for authentication on the server.
        :param value: the user name
        :return:
        """
        self._settings[USER_KEY].set_value(value)

    def get_password(self) -> str:
        """
        Return the password used for authentication on the server.
        :return: the password
        """
        return self._settings[PASSWORD_KEY].get_value()

    def set_password(self, value: str) -> None:
        """
        Set the password used for authentication on the server.
        :param value: the password
        :return:
        """
        self._settings[PASSWORD_KEY].set_value(value)


class Extension(object):
    """ Each subclass of Extension have to define a class method called 'new_config_instance' returning an """
    """ instance of a ExtensionConfig, NetExtensionConfig or oen of a subclass of ExtensionConfig according """
    """ to the extension. """
    logger: logging.Logger = None

    def __init__(self, config: ExtensionConfig):
        """
        Set the configuration of the extension.
        :param config: the configuration
        """
        self._config: ExtensionConfig = config
        self._last_processing_time: int = -1
        self._process_lock: threading.Lock = threading.Lock()

    def initialize(self, parent_logger: logging.Logger) -> None:
        """
        Set the logger.
        :param parent_logger: the logger
        :return:
        """
        if not self.__class__.logger:
            self.__class__.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
            for handler in parent_logger.handlers:
                self.__class__.logger.addHandler(handler)
            self.__class__.logger.setLevel(parent_logger.level)
        self.__class__.logger.info('Initializing ' + self.__class__.__name__ + '...')

    def _get_logger(self) -> logging.Logger:
        """
        Return the logger.
        :return: the logger
        """
        return self.__class__.logger

    def get_config(self) -> ExtensionConfig:
        """
        Return the configuration of the extension
        :return: the configuration
        """
        return self._config

    def get_last_processing_time(self) -> int:
        """
        Return the timestamp of the last processing.
        :return: the timestamp
        """
        return self._last_processing_time

    def process(self, images: list, message=None) -> bool:
        """
        Process the images using an optional message according to the triggering interval and implementation of the sublass.
        :param images: the images read by the webcam driver
        :param message: the optional message
        :return: True if really processed or False if processing was not triggered
        """
        with self._process_lock:
            # noinspection PyTypeChecker
            now: int = int(time.time())

            if self._last_processing_time <= 0 or self._config.get_triggering_interval() <= 0 or (
                    self._last_processing_time + self._config.get_triggering_interval()) < now:
                self._last_processing_time = now
                self._get_logger().debug('Processing')
                return self._process(images, message)
            else:
                self._get_logger().debug('Processing skipped, triggering interval not reached')
                self._add_pending(images, message)
        return False

    @abstractmethod
    def _add_pending(self, images: list, message=None) -> None:
        """
        Abstract addition of images and optional message to pending elements to process
        :param images: the images to add for a later processing
        :param message: the message to add for a later processing
        """
        pass

    @abstractmethod
    def _process(self, images: list, message=None) -> bool:
        """
        Abstract processing of images and optional message.
        :param images: the images to process
        :param message: the message to process
        """
        pass
