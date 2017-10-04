from csv import DictWriter
from os import makedirs
from os.path import dirname
from os.path import join

from framework.context.change import ChangeMatrix
from framework.context.code_element import CodeElementSet
from framework.context.code_element import StatementSet
from framework.context.coverage import CoverageMatrix
from framework.context.method import MethodSet


class Context(object):

    def __init__(self, score_csv_file, change_csv_file, coverage_csv_file, program):
        self.code_element_set = CodeElementSet.load_from_file(score_csv_file)
        self.change_matrix = ChangeMatrix.load_from_file(change_csv_file)
        self.coverage_matrix = CoverageMatrix.load_from_file(coverage_csv_file)
        self.program = program
        self.faulty_map = {}

    def is_faulty(self, code_element):
        if code_element not in self.faulty_map:
            faulty = False

            for ce in self.change_matrix.get_changes(self.program["version"]):
                if code_element.name == ce:
                    faulty = True
                    break

            self.faulty_map[code_element] = faulty

        return self.faulty_map[code_element]

    def get_neighbours(self, code_element, include_self=True):
        raise NotImplementedError

    def save_scores(self, base_path, iteration):
        file_path = join(base_path, self.program["name"], self.program["version"], "%d.csv" % iteration)

        makedirs(dirname(file_path), exist_ok = True)

        with open(file_path, 'w', encoding='utf-8') as csvfile:
            fieldnames = ["Name", "Score", "Faulty"]
            writer = DictWriter(csvfile, fieldnames = fieldnames, delimiter = ';')

            writer.writeheader()

            for ce in self.code_element_set.code_elements:
                data = {
                    "Name" : ce.name,
                    "Score" : ce.score,
                    "Faulty" : self.is_faulty(ce)
                }
                writer.writerow(data)


class Defects4JContext(Context):

    def __init__(self, score_csv_file, change_csv_file, coverage_csv_file, program):
        super().__init__(score_csv_file, change_csv_file, coverage_csv_file, program)

    def get_neighbours(self, code_element, include_self=True):
        parent = Defects4JContext.get_parent(code_element)
        neighbours = [ce for ce in self.code_element_set.code_elements if Defects4JContext.get_parent(ce) == parent]

        if not include_self:
            neighbours.remove(code_element)

        return neighbours

    @staticmethod
    def get_parent(code_element):
        sep = '.'
        parts = code_element.name.split(sep)
        parent = sep.join(parts[:-1])

        return parent


class SIRContext(Context):

    def __init__(self, score_csv_file, function_csv_file, change_csv_file, coverage_csv_file, program):
        self.code_element_set = StatementSet.load_from_file(score_csv_file)
        self.method_set = MethodSet.load_from_file(function_csv_file)
        self.change_matrix = ChangeMatrix.load_from_file(change_csv_file)
        self.coverage_matrix = CoverageMatrix.load_from_file(coverage_csv_file)
        self.program = program
        self.faulty_map = {}

    def get_neighbours(self, code_element, include_self=True):
        parent = self.method_set.get_parent(code_element)
        neighbours = [ce for ce in self.code_element_set.code_elements if ce in parent]

        if not include_self:
            neighbours.remove(code_element)

        return neighbours
