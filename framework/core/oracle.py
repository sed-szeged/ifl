from framework.context.code_element import CodeElement
from framework.core.answer import Answer


class Oracle:

    def ask_about(self, subject: CodeElement) -> Answer:
        raise NotImplementedError
