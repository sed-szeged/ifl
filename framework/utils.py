from glob import glob
from os import remove
from os.path import isdir
from os.path import join as j
from shutil import copy
from shutil import rmtree


def cp(source_dir, pattern, destination):
    """
    Copies items matching the given pattern from the source directory to the destination.

    :param source_dir: source directory
    :param pattern: glob pattern
    :param destination: destination (may be a file)
    """
    for item in glob(j(source_dir, pattern)):
        copy(item, destination)


def rm(source_dir, pattern):
    """
    Removes items matching the given pattern from the source directory.
    If the actual item is a directory then all its contents are removed recursively.

    :param source_dir: source directory
    :param pattern: glob pattern
    """
    for item in glob(j(source_dir, pattern)):
        if isdir(item):
            rmtree(item)
        else:
            remove(item)
