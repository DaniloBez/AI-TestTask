from source.utils.app_config import ValidSatisfactionLevels, MIN_QUALITY_SCORE, MAX_QUALITY_SCORE

def is_valid_output(data: dict) -> bool:
    required_keys = {"intent", "satisfaction", "quality_score"}
    if not required_keys.issubset(data.keys()):
        return False

    score = data.get("quality_score")
    if not (isinstance(score, int) and MIN_QUALITY_SCORE <= score <= MAX_QUALITY_SCORE):
        return False

    satisfaction = data.get("satisfaction")
    valid_values = [lvl.value for lvl in ValidSatisfactionLevels]
    if satisfaction not in valid_values:
        return False

    intent = data.get("intent")
    if not isinstance(intent, str) or intent.strip() == "":
        return False

    return True