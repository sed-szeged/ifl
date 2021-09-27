from random import randint
from typing import Dict

from framework.context.code_element import CodeElement
from framework.context.context import Context
from framework.context.coverage import TraceCoverageMatrix
from framework.core.answer import Answer
from framework.core.mediator import Mediator
from framework.core.oracle import Oracle
from framework.core.questioner import Questioner
from framework.experiment.experiment import Experiment


def root_likelihood(symptom, cause, context) -> float:
    d = len(context.code_element_set.code_elements)
    tests = context.coverage_matrix.query(
        TraceCoverageMatrix.AND_OPERATOR,
        test_result='FAIL',
        type_of='test',
        neighbor_of_every=(symptom, cause)
    )
    p = 0
    for t in tests:
        t_name = t[0]
        s_marks = context.coverage_matrix.query(
            TraceCoverageMatrix.AND_OPERATOR,
            type_of='code_element',
            neighbor_of_every=(t_name,)
        )
        p += d/len(s_marks)
    return p


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
            if answer == Answer.CLEAN:
                code_elements = self.context.code_element_set.code_elements - {self.subject}
                causes: Dict[CodeElement, float] = {}
                for code_element in code_elements:
                    causes[code_element] = root_likelihood(self.subject, code_element, self.context)
            elif answer == Answer.FAULTY:
                print("Doing nothing, going to stop anyway.")
            else:
                raise ValueError('Gong experiment do not use code-context.')

    class Oracle(Oracle):
        def __init__(self, context: Context):
            self.context = context

        def ask_about(self, subject):
            if self.context.is_faulty(subject):
                return Answer.FAULTY
            else:
                r = randint(0, 100)

                if r > self.context.knowledge:
                    return Answer.FAULTY
                else:
                    return Answer.CLEAN

    def configure(self):
        questioner = self.Questioner(self.context)
        oracle = self.Oracle(self.context)

        self.mediator = Mediator(self.context, questioner, oracle)
