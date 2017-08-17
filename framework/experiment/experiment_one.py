from framework.core.answer import Answer
from framework.core.mediator import Mediator
from framework.core.oracle import Oracle
from framework.core.questioner import Questioner
from framework.exception import InvalidAnswerException
from framework.experiment.experiment import SIRExperiment


class ExperimentOne(SIRExperiment):

    class Questioner(Questioner):

        def __init__(self, context):
            self.context = context
            self.subject = None

        def next_subject(self):
            self.subject = sorted(self.context.statement_set.statements,
                             key=lambda stmt: (-stmt.score, stmt.file, stmt.line))[0]
            return self.subject

        def acknowledge(self, answer):
            if answer == Answer.NO:
                self.subject.score = 0
            elif answer == Answer.NO_AND_NOT_SUSPICIOUS:
                for statement in self.context.get_neighbours(self.subject):
                    statement.score = 0
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
                    return Answer.NO

    def configure(self):
        questioner = ExperimentOne.Questioner(self.context)
        oracle = ExperimentOne.Oracle(self.context)

        self.mediator = Mediator(self.context, questioner, oracle)
