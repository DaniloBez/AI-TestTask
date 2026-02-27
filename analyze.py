from source.analyzer.analyzer_core import analyze
from source.tester.tester_core import test_for_mismatch_single
from source.tester.tester_core import compare_mismatches
from source.utils.app_config import TESTS_NUM

if __name__ == "__main__":
    for _ in range(TESTS_NUM):
        analyze()
        test_for_mismatch_single()

    compare_mismatches()