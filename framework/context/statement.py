from csv import DictReader


class Statement:

    SCORE_TYPE = "ochiai"
    SEPARATOR = ':'

    def __init__(self, file, line, score, name):
        self.score = score
        self.file = file
        self.line = line
        self.name = name

    def __eq__(self, other):
        return self.file == other.file and self.line == other.line

    def __hash__(self):
        return hash((self.file, self.line))

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return "%(score).5f %(name)s" % self.__dict__

    @classmethod
    def create_from_row(cls, row):
        parts = row["name"].split(Statement.SEPARATOR)

        assert len(parts) == 2

        return Statement(parts[0], int(parts[1]), float(row[Statement.SCORE_TYPE]), row["name"])


class StatementSet:

    def __init__(self):
        self.statements = set()

    @classmethod
    def load_from_file(cls, filepath):
        statement_set = StatementSet()

        with open(filepath, 'r') as csv_file:
            reader = DictReader(csv_file, delimiter = ';')

            for row in reader:
                statement = Statement.create_from_row(row)
                statement_set.statements.add(statement)

        return statement_set
