
class InvalidAnswerException(Exception):

    def __init__(self, answer):
        super().__init__("This questioner cannot understand the actual answer '%s'" % answer)
