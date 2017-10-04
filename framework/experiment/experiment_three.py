from scipy.spatial.distance import hamming

from framework.core.answer import Answer
from framework.core.mediator import Mediator
from framework.core.oracle import Oracle
from framework.core.questioner import Questioner
from framework.exception import InvalidAnswerException
from framework.experiment.experiment import Experiment


class ExperimentThree(Experiment):

    class Questioner(Questioner):

        def __init__(self, context, distance_function):
            self.context = context
            self.distance_function = distance_function
            self.subject = None

        def next_subject(self):
            self.subject = sorted(self.context.code_element_set.code_elements,
                                  key=lambda ce: (-ce.score, ce.name))[0]
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

                sum_scores = sum([ce.score for ce in neighbours])

                for ce in neighbours:
                    vector = self.context.coverage_matrix.get_coverage_for_code_element(ce.name)
                    distance = self.distance_function(base_vector, vector)

                    share = self.subject.score * (ce.score / sum_scores) * (1 - distance)

                    ce.score = min([1, ce.score + share])

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
                faulty_neighbours = [ce for ce in neighbours if self.context.is_faulty(ce)]

                if len(faulty_neighbours) == 0:
                    return Answer.NO_AND_NOT_SUSPICIOUS
                else:
                    return Answer.NO_BUT_SUSPICIOUS

    def configure(self):
        questioner = self.Questioner(self.context, lambda u, v: 1 - hamming(u, v))
        oracle = self.Oracle(self.context)

        self.mediator = Mediator(self.context, questioner, oracle)
