from enum import Enum

class ValidSatisfactionLevels(str, Enum):
    SATISFIED = "satisfied"
    NEUTRAL = "neutral"
    UNSATISFIED = "unsatisfied"


MIN_QUALITY_SCORE = 1
MAX_QUALITY_SCORE = 5