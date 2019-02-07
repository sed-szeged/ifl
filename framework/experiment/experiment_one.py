from random import randint

from framework.core.answer import Answer
from framework.core.mediator import Mediator
from framework.core.oracle import Oracle
from framework.core.questioner import Questioner
from framework.exception import InvalidAnswerException
from framework.experiment.experiment import Experiment


class ExperimentOne(Experiment):

    class Questioner(Questioner):

        def __init__(self, context):
            self.context = context
            self.subject = None

        def next_subject(self):
            self.subject = sorted(self.context.code_element_set.code_elements,
                                  key=lambda ce: (-ce.score, ce.name))[0]
            return self.subject

        def acknowledge(self, answer):
            if answer == Answer.NO_BUT_SUSPICIOUS:
                self.subject.score = 0
            elif answer == Answer.NO_AND_NOT_SUSPICIOUS:
                for ce in self.context.get_neighbours(self.subject):
                    ce.score = 0
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


class ExperimentOneB(ExperimentOne):

    class Questioner(ExperimentOne.Questioner):

        def acknowledge(self, answer):
            neighbours = self.context.get_neighbours(self.subject)

            if answer == Answer.NO:
                self.subject.score *= (1 - self.context.confidence / 100)
            elif answer == Answer.NO_BUT_SUSPICIOUS:
                self.subject.score *= (1 - self.context.confidence / 100)

                for ce in self.context.code_element_set.code_elements:
                    if ce not in neighbours:
                        ce.score *= (1 - self.context.confidence / 100)
            elif answer == Answer.NO_AND_NOT_SUSPICIOUS:
                for ce in neighbours:
                    ce.score *= (1 - self.context.confidence / 100)
            else:
                raise InvalidAnswerException(answer)
