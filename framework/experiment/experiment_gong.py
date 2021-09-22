from random import randint

from framework.context.context import Context
from framework.core.answer import Answer
from framework.core.mediator import Mediator
from framework.core.oracle import Oracle
from framework.core.questioner import Questioner
from framework.experiment.experiment import Experiment


class ExperimentGong(Experiment):
    """
    Experiment implementing the algorithm proposed by
    Gong et.al. 'Interactive fault localization leveraging simple user feedback'
    """

    class Questioner(Questioner):

        def __init__(self, context: Context):
            self.context = context
            self.subject = None

        def next_subject(self):
            self.subject = sorted(self.context.code_element_set.code_elements,
                                  key=lambda ce: (-ce.score, ce.name))[0]
            return self.subject

        def acknowledge(self, answer: Answer):
            pass  # TODO set the new score here

    class Oracle(Oracle):
        def __init__(self, context: Context):
            self.context = context

        def ask_about(self, subject):
            if self.context.is_faulty(subject):
                return Answer.YES
            else:
                neighbours = self.context.get_neighbours(subject)
                faulty_neighbours = [ce for ce in neighbours if self.context.is_faulty(ce)]

                r = randint(0, 100)

                if r > self.context.knowledge:
                    return Answer.NO
                else:
                    if len(faulty_neighbours) == 0:
                        return Answer.NO_AND_NOT_SUSPICIOUS
                    else:
                        return Answer.NO_BUT_SUSPICIOUS

    def configure(self):
        questioner = self.Questioner(self.context)
        oracle = self.Oracle(self.context)

        self.mediator = Mediator(self.context, questioner, oracle)
