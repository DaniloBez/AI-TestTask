from source.analyzer.analyzer_core import analyze
from source.tester.tester_core import test_for_mismatch_single
from source.tester.tester_core import compare_mismatches

if __name__ == "__main__":
    analyze()
    test_for_mismatch_single()
    analyze()
    test_for_mismatch_single()

    compare_mismatches()