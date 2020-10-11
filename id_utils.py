# -*- coding: utf-*-
# utilities
import json


def is_json(value: str) -> object:
    try:
        return json.loads(value)
    except ValueError:
        return None


def to_bool(value: str) -> bool:
    lc = value.lower()
    return lc == 'on' or lc == 'yes' or lc == 'true' or lc == '1'


def del_none(d: dict):
    if d is None:
        return
    for key, value in list(d.items()):
        if value is None:
            del d[key]
        elif isinstance(value, dict):
            del_none(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    del_none(item)


class ObjectView(object):
    def __init__(self, d):
        self.__dict__ = d

    """ Returns the string representation of the view """

    def __str__(self):
        return str(self.__dict__)
