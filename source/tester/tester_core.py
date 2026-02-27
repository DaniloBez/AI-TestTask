import json
import glob
import os
from source.utils.logger_config import setup_logger

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
log_file_path = os.path.join(project_root, "", "tester.log")
logger = setup_logger(log_file_path)
iteration=1

def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _index_by_id(items):
    return {item["id"]: item for item in items}


def _compare_jsons(expected, actual):
    """
    Args: validation json, result json
    """
    results = []
    mismatch_counter=0

    expected_index = _index_by_id(expected)
    actual_index = _index_by_id(actual)

    common_ids = set(expected_index.keys()) & set(actual_index.keys())

    for item_id in sorted(common_ids):
        exp = expected_index[item_id]
        act = actual_index[item_id]

        mismatches = {"id": item_id}

        # Compare simple fields (no intent for now)
        for field in ["satisfaction", "quality_score"]:
            if exp.get(field) != act.get(field):
                mismatches[field] = {}
                mismatches[field]["expected"] = exp[field]
                mismatches[field]["actual"] = act[field]
                mismatch_counter += 1

        # Compare agent_mistakes as unordered lists

        if len(mismatches) > 1:  # more than just id
            results.append(mismatches)

    if len(results) != 0:
        logger.info(f"Found {mismatch_counter} mismatches between validation and result")

    return results

def test_for_mismatch_single():
    """
    Returns mistmatches in format like

    [
        {
            id:1,
            "mismatched_field_1":["expected", "actual"],
            "mismatched_field_2":["expected", "actual"],
            "agent_mistakes": [
                ["missing expected 1", "missing expected 2"],
                ["unexpected actual 1"]
            ]
        }
    ]
    """

    validation_path = os.path.join(project_root, "data", "validation.json")
    result_path = os.path.join(project_root, "data", "result.json")
    global iteration
    mismatch_path = os.path.join(project_root, "data", f"mismatch_{iteration}.json")

    mismatch_res = _compare_jsons(_load_json(validation_path), _load_json(result_path))

    with open(mismatch_path, "w", encoding="utf-8") as f:
        json.dump(mismatch_res, f, indent=2, ensure_ascii=False)

    if len(mismatch_res)==0:
        logger.info("No mismatches found")
    else:
        logger.info(f"Mismatches saved to {mismatch_path}")

    iteration+=1

def compare_mismatches():
    """
    Returns:
        True  -> all mismatch_*.json files are identical
        False -> at least one file differs
    """

    pattern = os.path.join(project_root, "data", "mismatch_*.json")
    paths = sorted(glob.glob(pattern))

    if len(paths) <= 1:
        return True

    base_content = _load_json(paths[0])

    for path in paths[1:]:
        current_content = _load_json(path)
        if current_content != base_content:
            logger.error("Differences between analyzer-tester iterations found - mismatches aren't equal")
            return False

    logger.info("All analyzer iterations worked out identically - mismatches are equal")
    return True