import os
import re
import tarfile
from functools import lru_cache
from typing import List
import pandas as pd

import networkx as nx

import trc2chains


class CoverageMatrix(object):

    def __init__(self):
        self.tests = {}
        self.test_to_ids = {}
        self.code_elements = {}
        self.code_elements_to_ids = {}
        self.data = []

    def get_coverage_for_code_element_id(self, code_element_id):
        return [row[code_element_id] for row in self.data]

    def get_coverage_for_code_element(self, code_element):
        ce_id = self.code_elements_to_ids[code_element]

        return self.get_coverage_for_code_element_id(ce_id)

    def get_coverage_for_test_id(self, test_id):
        return self.data[test_id]

    def get_coverage_for_test(self, test):
        test_id = self.test_to_ids[test]

        return self.get_coverage_for_test_id(test_id)

    @classmethod
    def load_from_file(cls, file_path):
        matrix = CoverageMatrix()

        with open(file_path, 'r', encoding='utf-8') as csvfile:
            tc_id = -1

            for line in csvfile:
                row = line.strip().split(';')

                if tc_id == -1:
                    for ce_id in range(0, len(row[1:])):
                        name = row[ce_id + 1]

                        matrix.code_elements[ce_id] = name
                        matrix.code_elements_to_ids[name] = ce_id
                else:
                    name = row[0]

                    matrix.tests[tc_id] = name
                    matrix.test_to_ids[name] = tc_id

                    matrix.data.append([int(x) for x in row[1:]])

                tc_id += 1

        return matrix


class TraceCoverageMatrix(object):

    ENCODING = 'utf-8'

    def __init__(self, granularity: str):
        self.granularity = granularity
        self.graph = nx.Graph()
        self.mapping = {}

    def _add_test(self, member: tarfile.TarInfo):
        file_name = os.path.basename(member.name)

        match = re.search(r'(?P<test>.*)-(?P<result>PASS|FAIL).(?P<thread>\d+).trc', file_name)

        test_name = match.group('test')
        test_result = match.group('result')

        self.graph.add_node(test_name, type='test', result=test_result)

        return test_name

    def _add_code_element(self, code_element: str):
        self.graph.add_node(code_element, type='code_element')

    def _add_coverage(self, test: str, code_element: str, **attr):
        self._add_code_element(code_element)

        self.graph.add_edge(test, code_element, **attr)

    def parse_traces(self, archive: tarfile.TarFile, members: List[tarfile.TarInfo]):
        for member in members:
            try:
                self.parse_trace(archive, member)
            except (OverflowError, IOError) as e:
                print('# {}: {}'.format(member.name, e))

    def parse_trace(self, archive: tarfile.TarFile, member: tarfile.TarInfo):
        test_name = self._add_test(member)

        with archive.extractfile(member) as file:
            if self.granularity == 'binary':
                for ce in trc2chains.read_binary_from_buffer(file):
                    self._add_coverage(test_name, ce)
            elif self.granularity == 'count':
                for ce, count in trc2chains.read_count_from_buffer(file):
                    self._add_coverage(test_name, ce, count=count)
            elif self.granularity == 'chain':
                for chain, count in trc2chains.read_chain_from_buffer(file):
                    for ce in chain:
                        self._add_coverage(test_name, ce, count=count)
            else:
                assert False

    def create_mapping(self, archive: tarfile.TarFile, member: tarfile.TarInfo):
        with archive.extractfile(member) as file:
            for line in file:
                parts = line.decode(self.ENCODING).strip().split(':')

                assert len(parts) == 2

                id = int(parts[0])
                name = parts[1]

                self.mapping[id] = name

    @lru_cache(maxsize=2)
    def get_code_elements(self, with_result=True):
        result = []

        for node, data in self.graph.nodes(data=True):
            if data['type'] == 'code_element':
                if with_result:
                    result.append((node, data))
                else:
                    result.append(node)

        return result

    @lru_cache(maxsize=2)
    def get_tests(self, with_result=True):
        result = []

        for node, data in self.graph.nodes(data=True):
            if data['type'] == 'test':
                if with_result:
                    result.append((node, data['result']))
                else:
                    result.append(node)

        return result

    @classmethod
    def load_from_file(cls, file_path, granularity='binary'):
        coverage = TraceCoverageMatrix(granularity)

        with tarfile.open(file_path) as archive:
            trace_files = []

            for member in archive:
                if member.name.endswith('trace.trc.names'):
                    coverage.create_mapping(archive, member)
                elif member.name.endswith('.trc'):
                    trace_files.append(member)

            coverage.parse_traces(archive, trace_files)

        return coverage


class GZoltarCoverageMatrix(object):

    def __init__(self):
        self.data = None

    def get_code_elements(self):
        return self.data.columns.to_list()[:-1]

    def get_tests(self):
        return self.data.index.to_list()

    def get_coverage_for_code_element(self, code_element):
        pass

    def get_coverage_for_test(self, test):
        row: pd.Series = self.data.loc[test, self.get_code_elements()]

        return row.mask(row).dropna().index.to_list()

    @classmethod
    def load_from_file(cls, file_path):
        matrix = cls()

        matrix.data = pd.read_csv(file_path, index_col='name')

        return matrix
