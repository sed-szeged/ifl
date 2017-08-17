import argparse
import json
from csv import DictWriter
from glob import glob
from os import listdir, rename
from os.path import join as j, splitext
from subprocess import run

from natsort import natsorted

from framework.context.change import ChangeMatrix
from framework.utils import rm

parser = argparse.ArgumentParser(description="Creates basic score data from SoDA binaries.")

parser.add_argument("-d", "--datadir", required=True,
                    help="the directory where the raw coverage and results data of SIR programs can be found")
parser.add_argument("-c", "--cluster", default="full",
                    help="determines which cluster's data should be retrieved from fl data")

args = parser.parse_args()

data_dir = args.datadir
cluster = args.cluster


for program in natsorted(listdir(data_dir)):
    program_dir = j(data_dir, program)
    # Skip the original version as it does not have related change data
    coverage_matrices = natsorted(glob(j(program_dir, "*.*.cov.SoDA")))[1:]
    results_binary = j(program_dir, "%s.res.SoDA" % program)
    change_binary = j(program_dir, "%s.faults.chg.SoDA" % program)
    change_csv = "%s.csv" % splitext(change_binary)[0]

    # Export the change set to text format
    run(["binaryDump",
         "-w",
         "-x", change_binary,
         "--dump-changes", splitext(change_csv)[0]],
        check=True)
    # Import the change data from text
    change_matrix = ChangeMatrix.load_from_file(change_csv)

    for coverage_matrix in coverage_matrices:
        coverage_csv = "%s.ce.csv" % splitext(coverage_matrix)[0]

        version = coverage_matrix.split('.')[-3]
        output_dir = j(program_dir, "fl", version)
        output_json = j(output_dir, "result-%s.json" % version)
        consolidated_json = j(output_dir, "result.json")

        # Export the code elements (id and name) from the coverage matrix
        run(["binaryDump",
             "-c", coverage_matrix,
             "--dump-coverage-code-elements", splitext(coverage_csv)[0]],
            check=True)

        # Parse code elements from csv
        code_elements = dict()
        with open(coverage_csv, 'r') as coverage_file:
            for line in coverage_file:
                parts = line.strip().split(':')
                code_elements[parts[0]] = ':'.join(parts[1:])

        # Calculate the scores based on the available binaries using the fl-score SoDA tool
        run(["fl-score",
             "-f",
             "-c", coverage_matrix,
             "-r", results_binary,
             "-d", change_binary,
             "-o", output_dir],
            check=True)

        # The fl-score tool calculates scores for all version that are in the change binary,
        # therefore the relevant json is renamed and other ones are deleted
        rename(output_json, consolidated_json)
        rm(output_dir, "result-*.json")

        # Due to the special format of the JSON file
        # here it gets transformed to an easily accessible format
        # while each code element is augmented with one bit which indicates whether the actual item is faulty or not
        with open(consolidated_json, 'r') as json_file:
            fldata = json.load(json_file)
            scores = dict()

            for ce_id, data in fldata[cluster].items():
                # Score values are assigned to code element names
                scores[code_elements[ce_id]] = data

            with open("%s.csv" % splitext(consolidated_json)[0], 'w') as score_csv:
                field_names = ["name", "tarantula", "ochiai", "faulty"]
                writer = DictWriter(score_csv, fieldnames=field_names, delimiter=';')
                writer.writeheader()

                for ce_name, data in scores.items():
                    data = {
                        "name": ce_name,
                        "tarantula": data["tarantula"],
                        "ochiai": data["ochiai"],
                        "faulty": ce_name in change_matrix.get_changes(version)
                    }
                    writer.writerow(data)
