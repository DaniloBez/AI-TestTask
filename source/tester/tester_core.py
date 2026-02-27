import json
import glob
import os
from source.utils.logger_config import setup_logger

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
log_file_path = os.path.join(project_root, "logs", "tester.log")
logger = setup_logger(log_file_path, "source.tester")
iteration=1

def _load_json(path: str) -> dict | list:
    """
    Loads data from a JSON file.

    Args:
        path (str): The path to the JSON file.

    Returns:
        dict | list: The parsed JSON data.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _index_by_id(items: list) -> dict:
    """
    Creates a dictionary mapping IDs to their respective items.

    Args:
        items (list): A list of dictionaries representing items containing an 'id' key.

    Returns:
        dict: A dictionary where keys are item IDs and values are the corresponding dictionaries.
    """
    return {item["id"]: item for item in items}


def _compare_jsons(expected: list, actual: list) -> list:
    """
    Compares two JSON datasets containing expected and actual results.

    Args:
        expected (list): A list of dictionaries representing expected values (e.g., from validation).
        actual (list): A list of dictionaries representing actual values (e.g., from analysis results).

    Returns:
        list: A list of mismatch objects detailing differences between the expected and actual items.
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

        for field in ["satisfaction", "quality_score"]:
            if exp.get(field) != act.get(field):
                mismatches[field] = {}
                mismatches[field]["expected"] = exp[field]
                mismatches[field]["actual"] = act[field]
                mismatch_counter += 1

        if len(mismatches) > 1:
            results.append(mismatches)

    if len(results) != 0:
        logger.info(f"Found {mismatch_counter} mismatches between validation and result")

    return results

def test_for_mismatch_single() -> None:
    """
    Performs a single test iteration comparing validation and result JSON objects.

    Loads the validation reference from 'data_temp/validation.json' and the generated
    results from 'output/result.json', compares their records, and saves any found mismatches 
    into 'data_temp' prefixed by the current iteration number.

    Returns:
        None
    """

    validation_path = os.path.join(project_root, "data_temp", "validation.json")
    result_path = os.path.join(project_root, "output", "result.json")
    global iteration
    mismatch_path = os.path.join(project_root, "data_temp", f"mismatch_{iteration}.json")

    mismatch_res = _compare_jsons(_load_json(validation_path), _load_json(result_path))

    os.makedirs(os.path.dirname(mismatch_path), exist_ok=True)
    with open(mismatch_path, "w", encoding="utf-8") as f:
        json.dump(mismatch_res, f, indent=2, ensure_ascii=False)

    if len(mismatch_res)==0:
        logger.info("No mismatches found")
    else:
        logger.info(f"Mismatches saved to {mismatch_path}")

    iteration+=1

def compare_mismatches() -> bool:
    """
    Checks whether all generated mismatch files across multiple test iterations are identical.

    Returns:
        bool: True if and only if all generated mismatch records across the iterations match 
              (or there is only 1 iteration). False otherwise.
    """

    pattern = os.path.join(project_root, "data_temp", "mismatch_*.json")
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