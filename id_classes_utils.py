# -*- coding: utf-*-
# utilities for classes
import importlib
import os
import sys

from typing import Dict, Set

DictOfTypes = Dict[str, type]
SetOfTypes = Set[type]


def subclasses_of(cls) -> SetOfTypes:
    """
    Return the subclasses of the given class.
    :param cls: the base class
    :return: the subclasses
    """
    return set(cls.__subclasses__()).union([s for c in cls.__subclasses__() for s in subclasses_of(c)])


def import_files_of_dir(path: str) -> None:
    """
    Import .py files of the given directory.
    :param path: the directory
    :return:
    """
    __globals = globals()
    sys.path.append(path)
    for file in os.listdir(path):
        if file.startswith('_') or not file.lower().endswith('.py'):
            continue
        mod_name = file[:-3]   # strip .py at the end
        if mod_name not in __globals:
            print('Importing: ' + mod_name)
            __globals[mod_name] = importlib.import_module(mod_name)
            __import__(mod_name)
