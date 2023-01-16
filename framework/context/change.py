import json
import os
import re
from collections import defaultdict
from glob import glob
from typing import Generator


class ChangeMatrix(object):

    def __init__(self):
        self.versions = []
        self.code_elements = []
        self.changes = {}

    def get_changes(self, version):
        for index, value in enumerate(self.changes[version]):
            if value == "1":
                yield self.code_elements[index]

    @classmethod
    def load_from_file(cls, csv_file_path, separator=';'):
        matrix = ChangeMatrix()

        with open(csv_file_path, 'r', encoding="utf-8") as csv_file:
            i = 1

            for line in csv_file:
                parts = line.strip().split(separator)

                # header
                if i == 1:
                    matrix.code_elements = parts[1:]
                else:
                    version = parts[0]

                    matrix.versions.append(version)
                    matrix.changes[version] = parts[1:]

                i += 1

        return matrix


class JSONChangeMatrix(object):

    def __init__(self):
        self.changes = defaultdict(set)

    def get_changes(self, version: str):
        for code_element in self.changes[version]:
            yield code_element

    @classmethod
    def load_from_file(cls, json_file_path: str, program: str):
        matrix = JSONChangeMatrix()

        with open(json_file_path, 'r') as fp:
            j = json.load(fp)

            for version, data in j[program].items():
                for item in data:
                    if item["action"] != "added":
                        matrix.changes[version].add(item["method"])

        return matrix


class GZoltarChangeMatrix(object):

    def __init__(self):
        self.changes = defaultdict(set)

    def get_changes(self, version: str) -> Generator[str]:
        for code_element in self.changes[version]:
            yield code_element

    @classmethod
    def load_from_directory(cls, directory: str, program: str):
        matrix = cls()

        files = glob(os.path.join(directory, f'{program}.*.buggy.lines'))

        p = re.compile(r'(?P<program>\w+)-(?P<version>\d+).buggy.lines')

        for path in files:
            m = p.match(path)

            version = m.groupdict()['version']

            with open(path, 'r') as file:
                for line in file:
                    java_file, line_num, _ = line.strip().split('#')

                    matrix.changes[version].add(f'{java_file}#{line_num}')

