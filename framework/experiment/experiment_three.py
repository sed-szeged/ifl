from scipy.spatial.distance import hamming

from framework.core.answer import Answer
from framework.core.mediator import Mediator
from framework.core.oracle import Oracle
from framework.core.questioner import Questioner
from framework.exception import InvalidAnswerException
from framework.experiment.experiment import SIRExperiment


class ExperimentThree(SIRExperiment):

    class Questioner(Questioner):

        def __init__(self, context, distance_function):
            self.context = context
            self.distance_function = distance_function
            self.subject = None

        def next_subject(self):
            self.subject = sorted(self.context.statement_set.statements,
                             key=lambda stmt: (-stmt.score, stmt.file, stmt.line))[0]
            return self.subject

        def acknowledge(self, answer):
            if answer == Answer.NO_AND_NOT_SUSPICIOUS:
                neighbours = self.context.get_neighbours(self.subject)

                for statement in neighbours:
                    statement.score = 0
            elif answer == Answer.NO_BUT_SUSPICIOUS:
                base_vector = self.context.coverage_matrix.get_coverage_for_code_element(self.subject.name)

                neighbours = self.context.get_neighbours(self.subject)
                neighbours.remove(self.subject)

                sum_scores = sum([statement.score for statement in neighbours])

                for statement in neighbours:
                    vector = self.context.coverage_matrix.get_coverage_for_code_element(statement.name)
                    distance = self.distance_function(base_vector, vector)

                    share = self.subject.score * (statement.score / sum_scores) * (1 - distance)

                    statement.score = min([1, statement.score + share])

                self.subject.score = 0
            else:
                raise InvalidAnswerException(answer)

    class Oracle(Oracle):

        def __init__(self, context):
            self.context = context

        def ask_about(self, subject):
            if self.context.is_faulty(subject):
                return Answer.YES
            else:
                neighbours = self.context.get_neighbours(subject)
                faulty_neighbours = [statement for statement in neighbours if self.context.is_faulty(statement)]

                if len(faulty_neighbours) == 0:
                    return Answer.NO_AND_NOT_SUSPICIOUS
                else:
                    return Answer.NO_BUT_SUSPICIOUS

    def configure(self):
        questioner = ExperimentThree.Questioner(self.context, lambda u, v: 1 - hamming(u, v))
        oracle = ExperimentThree.Oracle(self.context)

        self.mediator = Mediator(self.context, questioner, oracle)
