import argparse
from glob import glob
from os import listdir, makedirs
from os.path import join as j, sep
from subprocess import run

from natsort import natsorted
from progressbar import ProgressBar

from framework.utils import cp, rm

parser = argparse.ArgumentParser(description="Builds all versions (including the original); "
                                             "executes all test cases available in the 'runall.sh' script; "
                                             "measures statement level coverage using GCOV; "
                                             "saves outputs and return codes for further processing.")
parser.add_argument("-b", "--basedir", required=True, help="the directory where SIR programs can be found")
parser.add_argument("-o", "--outdir", required=True, help="output directory")

args = parser.parse_args()

base_dir = args.basedir
out_dir = args.outdir

for program in natsorted(listdir(base_dir)):
    program_dir = j(base_dir, program)
    scripts_dir = j(program_dir, "scripts")
    source_dir = j(program_dir, "source")
    outputs_dir = j(program_dir, "outputs")

    versions = glob(j(program_dir, "versions.alt", "versions.orig", "v*"))
    versions.append(j(program_dir, "source.alt", "source.orig"))

    for version_dir in natsorted(versions):
        # Determine version string: 'orig' -> '0', 'v1' -> '1', 'v2' -> '2', ...
        version = version_dir.split(sep)[-1].split('.')[-1]
        if version.startswith("v"):
            version = version[1:]
        elif version == "orig":
            version = "0"

        # Clean working directory
        rm(source_dir, "*")

        # Copy the build script to the working directory
        cp(scripts_dir, "build.sh", source_dir)
        # Copy the source files to the working directory
        cp(version_dir, "*.[ch]", source_dir)

        # Build (raise CalledProcessError if the build fails)
        run("./build.sh", cwd=source_dir, check=True)

        # Collect test cases (each non echo line in the runall.sh is a test case)
        with open(j(scripts_dir, "runall.sh"), 'r') as test_suite_file:
            test_cases = [test_case.strip() for test_case in test_suite_file if not test_case.startswith("echo")]

            i = 1
            tc_bar = ProgressBar(max_value=len(test_cases))

            for command in test_cases:
                # Run the test case (commands are relative to the directory containing the runall.sh script)
                process = run(command, cwd=scripts_dir, shell=True)

                # Save the return code
                with open(j(outputs_dir, "%d.ret" % i), 'w') as return_file:
                    return_file.write("%d" % process.returncode)

                # Calculate coverage
                with open(j(source_dir, "gcov.log"), 'w') as stdout:
                    run("gcov *.c", cwd=source_dir, shell=True, check=True, stdout=stdout)

                # Create directory for coverage data
                coverage_dir = j(out_dir, program, "cov", version, str(i))
                makedirs(coverage_dir, exist_ok=True)
                # Clean coverage results directory
                rm(coverage_dir, "*")

                # Save coverage result files
                cp(source_dir, "*.gcov", coverage_dir)

                # Reset coverage data
                rm(source_dir, "*.gcda")

                tc_bar.update(i)
                i += 1

            tc_bar.finish()

        # Create directory for results
        results_dir = j(out_dir, program, "res", version)
        makedirs(results_dir, exist_ok=True)

        # Clean results directory
        rm(results_dir, "*")

        # Copy output and .ret files
        cp(outputs_dir, "*", results_dir)
