from source.analyzer.analyzer_core import analyze
from source.tester.tester_core import test_for_mismatch

if __name__ == "__main__":
    analyze()
    test_for_mismatch()