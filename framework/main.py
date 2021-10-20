import argparse
import sys
from os.path import join as j
from os import cpu_count
from multiprocessing import Pool

from framework.context.code_element import CodeElement
from framework.context.context import Defects4JContext
from framework.context.context import SIRContext
from framework.experiment.experiment_gong import ExperimentGong
from framework.experiment.experiment_one import Experiment
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
parser.add_argument("-p", "--projects", nargs="+", required=False, default=[],
                    help="Name of projects on which the experiments should run")
parser.add_argument("-t", "--threads", default=cpu_count() - 1, help="number of usable threads")
# introduced because concurrence breaks debugging traces, and makes debugging exceedingly difficult
parser.add_argument("-nc", "--no_concurrence", default=False, action="store_true",
                    help="remove any concurrence execution")

args = parser.parse_args()

CodeElement.SCORE_TYPE = args.score

# experiments = [
#     ExperimentOne("ex1", SIRContext),
#     ExperimentOneB("ex1b", SIRContext),
#     ExperimentTwo("ex2", SIRContext),
#     ExperimentThree("ex3", SIRContext)
# ]


def jobs():
    for knowledge in range(100, 101, 10):
        for iteration in range(0, 1, 1):
            for confidence in range(100, 101, 10):
                yield (knowledge, iteration, confidence)


def do(job):
    e = ExperimentGong("expgong", Defects4JContext)
    e.run(
        args.datadir,
        j(args.outdir, args.score, str(job[0]), str(job[1]), str(job[2])),
        knowledge=job[0],
        confidence=job[2],
        projects=args.projects,
    )


if __name__ == '__main__':
    if args.no_concurrence:
        print("running sequentially")
        for job in jobs():
            do(job)
    else:
        print("running concurrently")
        pool = Pool(processes=int(args.threads))
        pool.map(do, jobs())
        pool.close()
        pool.join()
