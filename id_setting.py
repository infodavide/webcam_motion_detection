# -*- coding: utf-*-
# Setting and data type classes
import json
from datetime import datetime
from id_utils import is_json
from enum import Enum
from typing import cast, Dict, Generic, TypeVar

T = TypeVar('T', int, float, str, datetime, bool, Enum)


class Setting(Generic[T]):
    def __init__(self, value: T, min_length: int = None, max_length: int = None, read_only: bool = False):
        self._min_length: int = min_length
        self._max_length: int = max_length
        self._value: T = value
        self._read_only: bool = read_only
        self._data_type: type = type(value)

    def parse(self, value: any) -> None:
        if value is None:
            # noinspection PyTypeChecker
            self.set_value(None)
            return
        if self._data_type == Enum and type(value) == str:
            self.set_value(T[value])
        elif self._data_type == bool:
            if type(value) == str:
                self.set_value(value.lower() == 'true' or value.lower() == 'on' or value.lower() == '1' or value.lower() == 'yes')
            elif type(value) == bool:
                self.set_value(value)
        elif self._data_type == int:
            if type(value) == str:
                self.set_value(int(value))
            elif type(value) == int:
                self.set_value(value)
        elif self._data_type == float:
            if type(value) == str:
                self.set_value(float(value))
            elif type(value) == float:
                self.set_value(value)
        elif self._data_type == datetime:
            if type(value) == str:
                self.set_value(datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f'))
            elif type(value) == datetime:
                self.set_value(value)
        else:
            self.set_value(value)

    def get_value(self) -> T:
        return self._value

    def set_value(self, value: T) -> None:
        if self._read_only:
            return
        if value is None:
            self._value = None
            return
        if self._data_type == int or self._data_type == float:
            if self._min_length is not None and value < self._min_length:
                raise ValueError(str(value) + '<' + str(self._min_length))
            if self._max_length is not None and value > self._max_length:
                raise ValueError(str(value) + '>' + str(self._max_length))
        elif self._data_type == str:
            if self._min_length is not None and len(value) < self._min_length:
                raise ValueError('length of ' + value + '<' + str(self._min_length))
            if self._max_length is not None and len(value) > self._max_length:
                raise ValueError('length of ' + value + '>' + str(self._max_length))
        elif self._data_type == datetime:
            if self._min_length is not None and datetime.timestamp(value) < self._min_length:
                raise ValueError('timestamp of ' + value + '<' + str(self._min_length))
            if self._max_length is not None and datetime.timestamp(value) > self._max_length:
                raise ValueError('timestamp of ' + value + '>' + str(self._max_length))
        self._value = value

    def get_min_length(self) -> int:
        return self._min_length

    def get_max_length(self) -> int:
        return self._max_length

    def get_read_only(self) -> bool:
        return self._read_only

    def to_json_object(self) -> dict:
        result: dict = dict()
        if self._max_length:
            result['max_length'] = self._max_length
        if self._min_length:
            result['min_length'] = self._min_length
        if self._read_only:
            result['read_only'] = self._read_only
        if self._data_type:
            result['data_type'] = self._data_type.__name__
        if self._value:
            result['value'] = self.__str__()
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_json_object())

    def __str__(self) -> str:
        if self._value is None:
            return ''
        if isinstance(self._value, bool):
            if self._value:
                return 'true'
            return 'false'
        if isinstance(self._value, int) or isinstance(self._value, float):
            return str(self._value)
        if isinstance(self._value, datetime):
            return self._value.strftime('%Y-%m-%d %H:%M:%S.%f')
        return self._value


DictOfSettings = Dict[str, Setting]


class Settings(DictOfSettings):
    def parse(self, value: any) -> None:
        # Expecting something like: { "name": "value", etc.
        obj = None
        if isinstance(value, Dict):
            obj = value
        elif isinstance(value, str):
            obj = is_json(value)
        if not isinstance(obj, Dict):
            raise ValueError('Invalid JSON for Settings: ' + value)
        data: dict = cast(dict, obj)
        for k, v in data.items():
            if k not in self:
                continue
            setting: Setting = self[k]
            if setting is None:
                raise ValueError('Invalid setting: ' + k)
            try:
                setting.parse(v)
            except ValueError as ve:
                raise ValueError('wrong setting: ' + k + ', ' + str(ve))

    def to_json_object(self) -> dict:
        result: dict = dict()
        # noinspection PyTypeChecker
        for k, s in self.items():
            setting: Setting = cast(Setting, s)
            result[k] = setting.get_value()
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_json_object())

    def __str__(self) -> str:
        return self.to_json()
