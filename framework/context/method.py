from csv import DictReader


class MethodDefinition(object):

    def __init__(self, name, file, begin_line, end_line):
        self.name = name
        self.file = file
        self.begin_line = begin_line
        self.end_line = end_line

    def __contains__(self, statement):
        return self.file.endswith(statement.file) and self.begin_line <= statement.line <= self.end_line

    @classmethod
    def create_from_row(cls, row):
        return MethodDefinition(row["LongName"], row["Path"], int(row["Line"]), int(row["EndLine"]))


class MethodSet(object):

    def __init__(self):
        self.methods = set()

    def get_parent(self, statement):
        for method in self.methods:
            if statement in method:
                return method

    @classmethod
    def load_from_file(cls, filepath):
        method_set = MethodSet()

        with open(filepath, 'r', encoding='utf-8') as csvfile:
            reader = DictReader(csvfile)

            for row in reader:
                if row.get("RealizationLevel") == "definition":
                    method = MethodDefinition.create_from_row(row)
                    method_set.methods.add(method)

        return method_set
