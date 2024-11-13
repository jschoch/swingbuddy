from enum import Enum, auto



class LoadHint(Enum):
    NEW = auto()
    NEW_DTL_TRC = auto()
    NEW_FACE_TRC = auto()
    NEW_OCR = auto()
    LOAD = auto()
    NEW_CLIP = auto()
    LOAD_CLIP = auto()

class TrcT(Enum):
    FACE = auto()
    DTL = auto()