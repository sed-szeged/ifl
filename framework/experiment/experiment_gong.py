from random import randint
from typing import Dict, Tuple

import networkx

from framework.context.code_element import CodeElement
from framework.context.context import Context
from framework.context.coverage import TraceCoverageMatrix
from framework.core.answer import Answer
from framework.core.mediator import Mediator
from framework.core.oracle import Oracle
from framework.core.questioner import Questioner
from framework.experiment.experiment import Experiment
import tqdm


def root_likelihood(symptom, cause, context, d: int) -> float:
    tests = context.coverage_matrix.query(
        TraceCoverageMatrix.AND_OPERATOR,
        test_result="FAIL",
        type_of="test",
        neighbor_of_every=(symptom, cause),
    )
    p = 0
    for t in tests:
        t_name = t[0]
        s_marks = context.coverage_matrix.query(
            TraceCoverageMatrix.AND_OPERATOR,
            type_of="code_element",
            neighbor_of_every=(t_name,),
        )
        p += d / len(s_marks)
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
            self.subject = sorted(
                self.context.code_element_set.code_elements,
                key=lambda ce: (-ce.score, ce.name),
            )[0]
            return self.subject

        def acknowledge(self, answer: Answer):
            if answer == Answer.CLEAN:
                print("the answer was CLEAN, propagating scores to root cause...")
                root_cause = self._get_root_cause()
                print(f"the most probable root cause is {root_cause}")

                covering_profiles = self.context.coverage_matrix.query(
                    TraceCoverageMatrix.AND_OPERATOR,
                    type_of="test",
                    neighbor_of_every=(root_cause[0],),
                )
                relevant_sub_matrix = self._get_sub_matrix(covering_profiles)
                relevant_sub_matrix.calculate_scores()
                networkx.write_graphml(relevant_sub_matrix.graph, 'relevant.dump.graphml')

                not_covering_profiles = self.context.coverage_matrix.query(
                    TraceCoverageMatrix.AND_OPERATOR,
                    type_of="test",
                    not_neighbor_of_any=(root_cause[0],),
                )
                irrelevant_sub_matrix = self._get_sub_matrix(not_covering_profiles)
                irrelevant_sub_matrix.calculate_scores()
                networkx.write_graphml(irrelevant_sub_matrix.graph, 'irrelevant.dump.graphml')

                raise NotImplementedError()
            elif answer == Answer.FAULTY:
                print("Doing nothing, going to stop anyway.")
            else:
                raise ValueError("Gong experiment do not use code-context.")
            print("propagation finished, scores updated")

        def _get_sub_matrix(self, profiles):
            covered_by_profiles = self.context.coverage_matrix.query(
                TraceCoverageMatrix.AND_OPERATOR,
                type_of="code_element",
                neighbor_of_any=tuple(item[0] for item in profiles),
            )
            relevant_nodes = set(
                item[0] for item in profiles
            ) | set(
                item[0] for item in covered_by_profiles
            )
            relevant_sub_matrix = self.context.coverage_matrix.sub(tuple(relevant_nodes))
            return relevant_sub_matrix

        def _get_root_cause(self) -> Tuple[CodeElement, float]:
            code_elements = self.context.code_element_set.code_elements - {self.subject}
            d = len(self.context.code_element_set.code_elements)
            causes: Dict[CodeElement, float] = {}
            progress_bar = tqdm.tqdm(
                code_elements, desc="cause probability", unit="code element"
            )
            for code_element in progress_bar:
                causes[code_element] = root_likelihood(
                    self.subject, code_element, self.context, d
                )
            root_cause = max(causes.items(), key=lambda item: item[1])
            # 2021-09-29: PyCharm type checking is incorrect for this
            # noinspection PyTypeChecker
            return root_cause

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
