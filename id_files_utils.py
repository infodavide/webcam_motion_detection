# -*- coding: utf-*-
# utilities for files and directories
import os
import shutil
import sys


def rm_children(path) -> None:
    """
    Delete all files and directories recursively and keep the given directory.
    :param path: the root directory used for deletion
    :return:
    """
    if not os.path.isdir(path):
        return
    for entry in os.listdir(path):
        if entry == '.' or entry == '..':
            continue
        p = os.path.join(path, entry)
        try:
            if os.path.isdir(p):
                print('Deleting folder: ' + p)
                shutil.rmtree(p)
            else:
                print('Deleting file: ' + p)
                os.unlink(p)
        except IsADirectoryError:
            print('Path is a directory: ' + p)
        except FileNotFoundError:
            print('No such file or directory found: ' + p)
        except PermissionError:
            print('Permission denied on: ' + p)
        except Exception as ex:
            print('File or directory can not be removed: %s' + p % ex, file=sys.stderr)
    print('Deletion completed')
