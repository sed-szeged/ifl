from glob import glob
from os.path import join as j, sep

from natsort import natsorted

from framework.context.context import Defects4JContext
from framework.context.context import SIRContext
from framework.utils import rm


class Experiment(object):

    def __init__(self, name, context_type):
        self.name = name
        self.context_type = context_type
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

            if self.context_type is SIRContext:
                self.context = SIRContext(score_csv, function_csv, change_csv, coverage_csv, program)
            elif self.context_type is Defects4JContext:
                self.context = Defects4JContext(score_csv, change_csv, coverage_csv, program)
            else:
                raise Exception("Unknown context_type '%s'" % self.context_type)

            changes = list(self.context.change_matrix.get_changes(program["version"]))
            if len(changes) != 1:
                print("INAPPROPRIATE NUMBER OF CHANGED CODE ELEMENTS '%s' IN VERSION '%s'" % (changes, program["version"]))
                continue

            faulty_ces = set()
            for ce in self.context.code_element_set.code_elements:
                if ce.name in changes:
                    faulty_ces.add(ce)
            print(faulty_ces)
            sum_score = sum([ce.score for ce in faulty_ces])
            if not sum_score > 0:
                print("NONE OF THE CHANGED CODE ELEMENTS '%s' HAS NON-ZERO SCORE" % (faulty_ces))
                continue

            self.configure()

            self.mediator.run(output_dir)
