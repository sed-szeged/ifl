import argparse

from framework.context.code_element import CodeElement
from framework.context.context import SIRContext
from framework.experiment.experiment_one import ExperimentOne
from framework.experiment.experiment_one import ExperimentOneB
from framework.experiment.experiment_three import ExperimentThree
from framework.experiment.experiment_two import ExperimentTwo

parser = argparse.ArgumentParser(description="Executes experiments.")
parser.add_argument("-d", "--datadir", required=True,
                    help="the directory where the raw coverage and results data of SIR programs can be found")
parser.add_argument("-o", "--outdir", required=True, help="output directory")
parser.add_argument("-s", "--score", choices=["dstar", "ochiai", "tarantula"], default="tarantula",
                    help="short name of the algorithm that is used to calculate the score")

args = parser.parse_args()

CodeElement.SCORE_TYPE = args.score

experiments = [
    ExperimentOne("ex1", SIRContext),
    ExperimentOneB("ex1b", SIRContext),
    ExperimentTwo("ex2", SIRContext),
    ExperimentThree("ex3", SIRContext)
]

for experiment in experiments:
    experiment.run(args.datadir, args.outdir)
