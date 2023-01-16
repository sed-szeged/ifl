import argparse
from glob import glob
from os import listdir
from os import makedirs
from os.path import join as j, basename, sep
from subprocess import run

from natsort import natsorted
from tqdm.auto import tqdm

parser = argparse.ArgumentParser(description="Creates SoDA coverage and results binaries from raw data.")

parser.add_argument("-d", "--datadir", required=True,
                    help="the directory where the raw coverage and results data of SIR programs can be found")

args = parser.parse_args()

data_dir = args.datadir

for program in natsorted(listdir(data_dir)):
    program_dir = j(data_dir, program)
    results_dir = j(program_dir, "res")
    coverage_dir = j(program_dir, "cov")

    results_dirs = glob(j(results_dir, "*"))
    coverage_dirs = glob(j(coverage_dir, "*"))

    # Verify that there are the same versions both in results and coverage related data
    res_versions = set([dir.split(sep)[-1] for dir in results_dirs])
    cov_versions = set([dir.split(sep)[-1] for dir in coverage_dirs])
    versions = natsorted(res_versions & cov_versions)

    assert len(versions) == len(res_versions) == len(cov_versions)

    # First version ('0') is the original version, the rest are the faulty ones
    # TODO(hferenc): this applies only to SIR programs
    original_version = versions[0]
    faulty_versions = versions[1:]

    results_vector_base_dir = j(program_dir, "results_vector")
    base_results_dir = j(results_dir, original_version)

    # Create results vector in results.txt
    for version in tqdm(faulty_versions, desc="version"):
        version_results_dir = j(results_dir, version)
        version_vector_dir = j(results_vector_base_dir, version)
        makedirs(version_vector_dir, exist_ok=True)

        with open(j(version_vector_dir, "results.txt"), 'w') as vector_file:
            test_cases = glob(j(version_results_dir, "t*"))

            i = 1
            # bar = ProgressBar(max_value=len(test_cases))

            # Compare each output and return value to the original (base)
            for outfile in tqdm(natsorted(test_cases), desc="test", leave=False):
                test_case_name = basename(outfile)
                id = test_case_name[1:]

                return_file = j(version_results_dir, "%s.ret" % id)

                base_output_file = j(base_results_dir, test_case_name)
                base_return_file = j(base_results_dir, "%s.ret" % id)

                with open(base_return_file, 'r') as brf, open(return_file, 'r') as rf:
                    base_return_val = brf.read()
                    return_val = rf.read()

                    return_values_match = base_return_val == return_val

                diff = run(["diff", base_output_file, outfile])
                outputs_match = diff.returncode == 0

                # A test case is considered as passed only if the output and the return value are the same as the
                # original, otherwise it is failed
                row_data = {
                    "result": "PASS" if return_values_match and outputs_match else "FAIL",
                    "id": id
                }
                vector_file.write("%(result)s: %(id)s\n" % row_data)

                # bar.update(i)
                i += 1

            # bar.finish()

    # Create results matrix
    results_matix_path = j(program_dir, "%s.res.SoDA" % program)
    run(["rawDataReader",
         "-t", "results",
         "-m", "dejagnu-one-revision-per-file",
         "-p", results_vector_base_dir,
         "-o", results_matix_path],
        check=True)

    # Create coverage matrices for all versions
    for version in tqdm(versions):
        input_path = j(coverage_dir, version)
        output_path = j(program_dir, "%s.%s.cov.SoDA" % (program, version))

        run(["gunzip", "-r", input_path], check=True)

        run(["rawDataReader",
             "-t", "coverage",
             "-m", "gcov",
             "-g", "statement",
             "-p", input_path,
             "-o", output_path],
            check=True)

        run(["gzip", "-r", input_path], check=True)

    # Clean up the results and coverage fragments by zipping them
    # -r: recurse into subdirs, -m: move into zip i.e. delete original
    run(["zip", "-rm", "cov.zip", "cov"], cwd=program_dir, check=True)
    run(["zip", "-rm", "res.zip", "res", "results_vector"], cwd=program_dir, check=True)
