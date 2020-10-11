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
        self._type: str = extension_class_name
        self._settings: Settings = Settings()
        self._settings[ENABLED_KEY]: Setting = Setting(False)
        self._settings[TRIGGERING_INTERVAL_KEY]: Setting = Setting[int](None)

    def get_extension_class_name(self) -> str:
        return self._type

    def is_enabled(self) -> bool:
        return self._settings[ENABLED_KEY].get_value()

    def set_enabled(self, value: bool) -> None:
        self._settings[ENABLED_KEY].set_value(value)

    def get(self, value: str):
        return self._settings[value]

    def get_triggering_interval(self) -> int:
        return self._settings[TRIGGERING_INTERVAL_KEY].get_value()

    def set_triggering_interval(self, value: int) -> None:
        self._settings[TRIGGERING_INTERVAL_KEY].set_value(value)

    def parse(self, value: any) -> None:
        self._settings.parse(value)

    def to_json_object(self) -> dict:
        return self._settings.to_json_object()

    def to_json(self) -> str:
        return json.dumps(self.to_json_object())

    def __str__(self) -> str:
        return self.to_json()


SERVER_KEY: str = 'server'
PORT_KEY: str = 'port'
USER_KEY: str = 'user'
PASSWORD_KEY: str = 'password'


class NetExtensionConfig(ExtensionConfig):
    def __init__(self, extension_class_name: str):
        super().__init__(extension_class_name)
        self._settings[SERVER_KEY]: Setting = Setting[str](None)
        self._settings[PORT_KEY]: Setting = Setting[int](None)
        self._settings[USER_KEY]: Setting = Setting[str](None)
        self._settings[PASSWORD_KEY]: Setting = Setting[str](None)

    def get_server(self) -> str:
        return self._settings[SERVER_KEY].get_value()

    def set_server(self, value: str) -> None:
        self._settings[SERVER_KEY].set_value(value)

    def get_port(self) -> int:
        return self._settings[PORT_KEY].get_value()

    def set_port(self, value: int) -> None:
        self._settings[PORT_KEY].set_value(value)

    def get_user(self) -> str:
        return self._settings[USER_KEY].get_value()

    def set_user(self, value: str) -> None:
        self._settings[USER_KEY].set_value(value)

    def get_password(self) -> str:
        return self._settings[PASSWORD_KEY].get_value()

    def set_password(self, value: str) -> None:
        self._settings[PASSWORD_KEY].set_value(value)


class Extension(object):
    """ Each subclass of Extension have to define a class method called 'new_config_instance' returning an """
    """ instance of a ExtensionConfig, NetExtensionConfig or oen of a subclass of ExtensionConfig according """
    """ to the extension. """
    logger: logging.Logger = None

    def __init__(self, config: ExtensionConfig):
        self._config: ExtensionConfig = config
        self._last_processing_time: int = -1
        self._process_lock: threading.Lock = threading.Lock()

    def initialize(self, parent_logger: logging.Logger):
        if not self.__class__.logger:
            self.__class__.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
            for handler in parent_logger.handlers:
                self.__class__.logger.addHandler(handler)
            self.__class__.logger.setLevel(parent_logger.level)
        self.__class__.logger.info('Initializing ' + self.__class__.__name__ + '...')

    def _get_logger(self) -> logging.Logger:
        return self.__class__.logger

    def get_config(self) -> ExtensionConfig:
        return self._config

    def get_last_processing_time(self) -> int:
        return self._last_processing_time

    def process(self, images: list, message=None) -> bool:
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
        Add images and optional message to pending elements to process
        """
        pass

    @abstractmethod
    def _process(self, images: list, message=None) -> bool:
        """
        Process images and optional message
        """
        pass
