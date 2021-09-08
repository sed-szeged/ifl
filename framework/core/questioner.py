from framework.core.answer import Answer
from framework.context.code_element import CodeElement


class Questioner:

    def next_subject(self) -> CodeElement:
        raise NotImplementedError

    def acknowledge(self, answer: Answer):
        raise NotImplementedError
