from enum import Enum


class Answer(Enum):

    # Subject is faulty
    YES = 1
    FAULTY = 1  # introduced for Gong experiment
    # Subject is not faulty
    NO = 2
    CLEAN = 2  # introduced for Gong experiment
    # Subject is faulty but its neighbours are suspicious
    NO_BUT_SUSPICIOUS = 3
    # Neither the subject, nor its neighbours are faulty
    NO_AND_NOT_SUSPICIOUS = 4
