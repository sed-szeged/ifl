class Questioner:

    def next_subject(self):
        raise NotImplementedError

    def acknowledge(self, answer):
        raise NotImplementedError
