from scipy.spatial.distance import hamming

from framework.core.answer import Answer
from framework.core.mediator import Mediator
from framework.core.oracle import Oracle
from framework.core.questioner import Questioner
from framework.exception import InvalidAnswerException
from framework.experiment.experiment import SIRExperiment


class ExperimentTwo(SIRExperiment):

    class Questioner(Questioner):

        def __init__(self, context, distance_function, adjustment_function):
            self.context = context
            self.distance_function = distance_function
            self.adjustment_function = adjustment_function
            self.subject = None

        def next_subject(self):
            self.subject = sorted(self.context.statement_set.statements,
                             key=lambda stmt: (-stmt.score, stmt.file, stmt.line))[0]
            return self.subject

        def acknowledge(self, answer):
            if answer == Answer.NO:
                base_vector = self.context.coverage_matrix.get_coverage_for_code_element(self.subject.name)

                statements = self.context.statement_set.statements
                statements.remove(self.subject)

                self.subject.score = 0

                for statement in statements:
                    vector = self.context.coverage_matrix.get_coverage_for_code_element(statement.name)

                    distance = self.distance_function(base_vector, vector)
                    statement.score *= self.adjustment_function(distance)
            else:
                raise InvalidAnswerException(answer)

    class Oracle(Oracle):

        def __init__(self, context):
            self.context = context

        def ask_about(self, subject):
            if self.context.is_faulty(subject):
                return Answer.YES
            else:
                return Answer.NO

    def configure(self):
        questioner = ExperimentTwo.Questioner(self.context,
                                              lambda u, v: 1 - hamming(u, v),
                                              lambda x: 1.15 * x ** 3 - 2.66 * x ** 2 + 2 * x + 0.5)
        oracle = ExperimentTwo.Oracle(self.context)

        self.mediator = Mediator(self.context, questioner, oracle)
