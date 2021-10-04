"""
WARNING: Add the directory containing the 3_run-sm.sh helper script to the PATH.
"""

import argparse
from glob import glob
from os import listdir, makedirs
from os.path import join as j, sep
from subprocess import run

from natsort import natsorted

from framework.util.os_helpers import cp, rm

parser = argparse.ArgumentParser(description="Builds all versions (including the original); "
                                             "utilizes SourceMeter to analyze the structure of the program; "
                                             "saves the results into the directory specified by outdir.")
parser.add_argument("-b", "--basedir", required=True, help="the directory where SIR programs can be found")
parser.add_argument("-o", "--outdir", required=True, help="output directory")

args = parser.parse_args()

base_dir = args.basedir
out_dir = args.outdir

for program in natsorted(listdir(base_dir)):
    program_dir = j(base_dir, program)
    scripts_dir = j(program_dir, "scripts")
    source_dir = j(program_dir, "source")

    versions = glob(j(program_dir, "versions.alt", "versions.orig", "v*"))
    versions.append(j(program_dir, "source.alt", "source.orig"))

    for versiondir in natsorted(versions):
        # Determine version string: 'orig' -> '0', 'v1' -> '1', 'v2' -> '2', ...
        version = versiondir.split(sep)[-1].split('.')[-1]
        if version.startswith("v"):
            version = version[1:]
        elif "orig" == version:
            version = "0"

        # Clean working directory
        rm(source_dir, "*")

        # Copy the build script to the working directory
        cp(scripts_dir, "build.sh", source_dir)
        # Copy the source files to the working directory
        cp(versiondir, "*.[ch]", source_dir)

        # Run SM, raise CalledProcessError if the build fails
        run(["3_run-sm.sh", program, "build.sh", "sm-results"], cwd=source_dir, check=True)

        # Create directory for the results
        results_dir = j(out_dir, program)
        makedirs(results_dir, exist_ok=True)

        # Copy Function.csv to results
        cp(j(source_dir, "sm-results", program, "cpp"), j("*", "*-Function.csv"),
           j(results_dir, "%s.%s.function.csv" % (program, version)))
