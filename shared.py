from enum import Enum

class Action(Enum):
    EXITED = 0
    JOINED = 1
    ATTACK = 2
    PLACE = 3
    REMOVE = 4
    RESET = 5
    READY = 6
    UPDATE = 7
