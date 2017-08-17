class CoverageMatrix:

    def __init__(self):
        self.tests = dict()
        self.test_to_ids = dict()
        self.code_elements = dict()
        self.code_elements_to_ids = dict()
        self.data = list()

    def get_coverage_for_code_element_id(self, code_element_id):
        return [row[code_element_id] for row in self.data]

    def get_coverage_for_code_element(self, code_element):
        ce_id = self.code_elements_to_ids[code_element]

        return self.get_coverage_for_code_element_id(ce_id)

    def get_coverage_for_test_id(self, test_id):
        return self.data[test_id]

    def get_coverage_for_test(self, test):
        test_id = self.test_to_ids[test]

        return self.get_coverage_for_test_id(test_id)

    @classmethod
    def load_from_file(cls, file_path):
        matrix = CoverageMatrix()

        with open(file_path, 'r') as csvfile:
            tc_id = -1

            for line in csvfile:
                row = line.strip().split(';')

                if tc_id == -1:
                    for ce_id in range(0, len(row[1:])):
                        name = row[ce_id + 1]

                        matrix.code_elements[ce_id] = name
                        matrix.code_elements_to_ids[name] = ce_id
                else:
                    name = row[0]

                    matrix.tests[tc_id] = name
                    matrix.test_to_ids[name] = tc_id

                    matrix.data.append([int(x) for x in row[1:]])

                tc_id += 1

        return matrix
