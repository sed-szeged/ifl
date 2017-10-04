from scipy.spatial.distance import hamming

from framework.core.answer import Answer
from framework.core.mediator import Mediator
from framework.core.oracle import Oracle
from framework.core.questioner import Questioner
from framework.exception import InvalidAnswerException
from framework.experiment.experiment import Experiment


class ExperimentTwo(Experiment):

    class Questioner(Questioner):

        def __init__(self, context, distance_function, adjustment_function):
            self.context = context
            self.distance_function = distance_function
            self.adjustment_function = adjustment_function
            self.subject = None
            self.distance_map = {}

        def next_subject(self):
            self.subject = sorted(self.context.code_element_set.code_elements,
                                  key=lambda ce: (-ce.score, ce.name))[0]
            return self.subject

        def acknowledge(self, answer):
            if answer == Answer.NO:
                subject_name = self.subject.name
                base_vector = self.context.coverage_matrix.get_coverage_for_code_element(subject_name)
                if subject_name not in self.distance_map:
                    self.distance_map[subject_name] = {}

                ces = self.context.code_element_set.code_elements
                ces.remove(self.subject)

                self.subject.score = 0

                for ce in ces:
                    if ce.name not in self.distance_map[subject_name]:
                        vector = self.context.coverage_matrix.get_coverage_for_code_element(ce.name)
                        distance = self.distance_function(base_vector, vector)
                        self.distance_map[subject_name][ce.name] = distance

                    ce.score *= self.adjustment_function(self.distance_map[subject_name][ce.name])
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
        questioner = self.Questioner(self.context,
                                     lambda u, v: 1 - hamming(u, v),
                                     lambda x: 1.15 * x ** 3 - 2.66 * x ** 2 + 2 * x + 0.5)
        oracle = self.Oracle(self.context)

        self.mediator = Mediator(self.context, questioner, oracle)
