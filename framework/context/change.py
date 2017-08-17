
class ChangeMatrix:

    def __init__(self):
        self.versions = []
        self.code_elements = []
        self.changes = dict()

    def get_changes(self, version):
        for index, value in enumerate(self.changes[version]):
            if value == "1":
                yield self.code_elements[index]

    @classmethod
    def load_from_file(cls, csv_file_path, separator=';'):
        matrix = ChangeMatrix()

        with open(csv_file_path, 'r') as csv_file:
            i = 1

            for line in csv_file:
                parts = line.strip().split(separator)

                # header
                if i == 1:
                    matrix.code_elements = parts[1:]
                else:
                    version = parts[0]

                    matrix.versions.append(version)
                    matrix.changes[version] = parts[1:]

                i += 1

        return matrix
