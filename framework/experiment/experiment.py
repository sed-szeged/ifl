from glob import glob
from os.path import join as j, sep
from natsort import natsorted
from framework.context.context import SIRContext
from framework.utils import rm


class Experiment:

    def __init__(self, name):
        self.name = name

    def run(self, data_dir, output_dir):
        raise NotImplementedError


class SIRExperiment(Experiment):

    def __init__(self, name):
        super().__init__(name)

        self.context = None
        self.mediator = None

    def configure(self):
        raise NotImplementedError

    def run(self, data_dir, output_dir):
        output_dir = j(output_dir, self.name)
        rm(output_dir, "*")

        fl_score_files = natsorted(glob(j(data_dir, "*", "fl", "*", "result.csv")))

        for score_csv in fl_score_files:
            parts = score_csv.split(sep)

            program = {
                "name": parts[-4],
                "version": parts[-2]
            }
            print(program)

            function_csv = j(data_dir, program["name"], "%(name)s.%(version)s.function.csv" % program)
            change_csv = j(data_dir, program["name"], "%(name)s.faults.chg.csv" % program)
            coverage_csv = j(data_dir, program["name"], "%(name)s.%(version)s.cov.csv" % program)

            self.context = SIRContext(score_csv, function_csv, change_csv, coverage_csv, program)

            changes = list(self.context.change_matrix.get_changes(program["version"]))
            print(changes)
            if len(changes) != 1:
                continue

            self.configure()

            self.mediator.run(output_dir)
