import argparse

from framework.experiment.experiment_one import ExperimentOne
from framework.experiment.experiment_three import ExperimentThree
from framework.experiment.experiment_two import ExperimentTwo

parser = argparse.ArgumentParser(description="Executes experiments.")
parser.add_argument("-d", "--datadir", required=True,
                    help="the directory where the raw coverage and results data of SIR programs can be found")
parser.add_argument("-o", "--outdir", required=True, help="output directory")

args = parser.parse_args()

experiments = [
    ExperimentOne("ex1"),
    ExperimentTwo("ex2"),
    ExperimentThree("ex3")
]

for experiment in experiments:
    experiment.run(args.datadir, args.outdir)
