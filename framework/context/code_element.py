from csv import DictReader


class CodeElement(object):

    SCORE_TYPE = "ochiai"

    def __init__(self, name, score):
        self.name = name
        self.score = score

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return "%(score).5f %(name)s" % self.__dict__

    @classmethod
    def create_from_row(cls, row):
        return CodeElement(row["name"], float(row[CodeElement.SCORE_TYPE]))


class Statement(CodeElement):

    SEPARATOR = ':'

    def __init__(self, name, score, file, line):
        super().__init__(name, score)
        self.file = file
        self.line = line

    def __eq__(self, other):
        return self.file == other.file and self.line == other.line

    def __hash__(self):
        return hash((self.file, self.line))

    @classmethod
    def create_from_row(cls, row):
        parts = row["name"].split(Statement.SEPARATOR)

        assert len(parts) == 2

        return Statement(row["name"], float(row[CodeElement.SCORE_TYPE]), parts[0], int(parts[1]))


class CodeElementSet(object):

    def __init__(self):
        self.code_elements = set()

    @classmethod
    def load_from_file(cls, filepath, creator=CodeElement.create_from_row):
        ce_set = cls()

        with open(filepath, 'r', encoding="utf-8") as csv_file:
            reader = DictReader(csv_file, delimiter=';')

            for row in reader:
                ce = creator(row)
                ce_set.code_elements.add(ce)

        return ce_set


class StatementSet(CodeElementSet):

    @classmethod
    def load_from_file(cls, filepath, creator=Statement.create_from_row):
        return super().load_from_file(filepath, creator)
