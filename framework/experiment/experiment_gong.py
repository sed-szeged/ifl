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

        def next_subject(self):
            pass

        def acknowledge(self, answer: Answer):
            pass

    class Oracle(Oracle):

        def __init__(self, context: Context):
            self.context = context

        def ask_about(self, subject):
            pass

    def configure(self):
        questioner = self.Questioner(self.context)
        oracle = self.Oracle(self.context)

        self.mediator = Mediator(self.context, questioner, oracle)
