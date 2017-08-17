from csv import DictWriter
from os import makedirs
from os.path import dirname
from os.path import join

from framework.context.change import ChangeMatrix
from framework.context.coverage import CoverageMatrix
from framework.context.method import MethodSet
from framework.context.statement import StatementSet


class Context:

    def save_scores(self, base_path, iteration):
        raise NotImplementedError


class SIRContext:

    def __init__(self, score_csv_file, function_csv_file, change_csv_file, coverage_csv_file, program):
        self.statement_set = StatementSet.load_from_file(score_csv_file)
        self.method_set = MethodSet.load_from_file(function_csv_file)
        self.change_matrix = ChangeMatrix.load_from_file(change_csv_file)
        self.coverage_matrix = CoverageMatrix.load_from_file(coverage_csv_file)
        self.program = program

    def is_faulty(self, statement):
        for ce in self.change_matrix.get_changes(self.program["version"]):
            if statement.name == ce:
                return True
        return False

    def get_neighbours(self, statement, include_self=True):
        parent = self.method_set.get_parent(statement)

        neighbours = [statement for statement in self.statement_set.statements if statement in parent]

        if not include_self:
            neighbours.remove(statement)

        return neighbours

    def save_scores(self, base_path, iteration):
        file_path = join(base_path, self.program["name"], self.program["version"], "%d.csv" % iteration)

        makedirs(dirname(file_path), exist_ok = True)

        with open(file_path, 'w') as csvfile:
            fieldnames = ["Name", "Score", "Faulty"]
            writer = DictWriter(csvfile, fieldnames = fieldnames, delimiter = ';')

            writer.writeheader()

            for stmt in self.statement_set.statements:
                data = {
                    "Name" : str(stmt),
                    "Score" : stmt.score,
                    "Faulty" : self.is_faulty(stmt)
                }
                writer.writerow(data)