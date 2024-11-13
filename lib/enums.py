from enum import Enum, auto



class LoadHint(Enum):
    NEW = auto()
    NEW_TRC = auto()
    NEW_OCR = auto()
    LOAD = auto()
    NEW_CLIP = auto()
    LOAD_CLIP = auto()

class TrcT(Enum):
    FACE = auto()
    DTL = auto()