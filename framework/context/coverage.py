import os
import re
import tarfile
from functools import lru_cache
from typing import List, Optional, Union, Tuple

import networkx
import networkx as nx

import trc2chains
from framework.context.code_element import CodeElement


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
        self.key_mapping = {}
        self.name_mapping = {}

    def _add_test(self, member: tarfile.TarInfo):
        file_name = os.path.basename(member.name)

        match = re.search(r'(?P<test>.*)-(?P<result>PASS|FAIL).(?P<thread>\d+).trc', file_name)

        test_name = match.group('test')
        test_result = match.group('result')

        self.graph.add_node(test_name, type='test', result=test_result)

        return test_name

    def _add_code_element(self, code_element: str):
        self.graph.add_node(code_element, type='code_element', name=self.key_mapping[code_element])

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

                self.key_mapping[id] = name
                self.name_mapping[name] = id

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

    OR_OPERATOR = 'or'
    AND_OPERATOR = 'and'

    @lru_cache(maxsize=2)
    def query(
            self,
            operator: str,
            test_result: Optional[str] = None,
            type_of: Optional[str] = None,
            neighbor_of_every: Tuple[Union[CodeElement, str, int], ...] = (),
            neighbor_of_any: Tuple[Union[CodeElement, str, int], ...] = ()
    ):
        result = []

        for node, data in self.graph.nodes(data=True):
            type_filter = type_of is None or data.get('type', None) == type_of
            result_filter = test_result is None or data.get('result', None) == test_result
            neighbors = self.graph.neighbors(node)
            neighbor_every_filter =\
                neighbor_of_every == () or all([n in neighbors for n in self.get_graph_key(*neighbor_of_every)])
            neighbor_any_filter =\
                neighbor_of_any == () or any([n in neighbors for n in self.get_graph_key(*neighbor_of_any)])

            if operator == TraceCoverageMatrix.OR_OPERATOR:
                if type_filter or result_filter or neighbor_every_filter or neighbor_any_filter:
                    result.append((node, data))
            elif operator == TraceCoverageMatrix.AND_OPERATOR:
                if type_filter and result_filter and neighbor_every_filter and neighbor_any_filter:
                    result.append((node, data))
            else:
                raise ValueError(f'unsupported operator: {operator}')

        return result

    def get_graph_key(self, *items: Union[CodeElement, str, int]):
        keys = []
        for item in items:
            if isinstance(item, CodeElement):
                keys.append(self.name_mapping[item.name])
            elif isinstance(item, str):
                keys.append(self.name_mapping[item])
            elif isinstance(item, int):
                keys.append(item)
            else:
                raise ValueError("unsupported type")
        return keys

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
