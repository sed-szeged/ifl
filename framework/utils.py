from glob import glob
from os.path import join as j, isdir
from os import remove
from shutil import copy, rmtree


def cp(source_dir, pattern, dst):
    for file in glob(j(source_dir, pattern)):
        copy(file, dst)


def rm(directory, pattern):
    for file in glob(j(directory, pattern)):
        if isdir(file):
            rmtree(file)
        else:
            remove(file)
