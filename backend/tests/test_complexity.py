"""test_complexity.py — empirical Big-O verification."""

from app.core.complexity import probe_binary_search_complexity

REAL_BINARY_SEARCH = """
def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
"""

LINEAR_SCAN_DISGUISED = """
def binary_search(arr, target):
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1
"""


def test_real_binary_search_passes_complexity_probe():
    result = probe_binary_search_complexity(REAL_BINARY_SEARCH, "binary_search")
    assert result.passed is True
    assert result.estimated_exponent < 0.5


def test_linear_scan_fails_complexity_probe():
    result = probe_binary_search_complexity(LINEAR_SCAN_DISGUISED, "binary_search")
    assert result.passed is False
    assert result.estimated_exponent > 0.5


def test_broken_candidate_reports_failure_not_crash():
    result = probe_binary_search_complexity("def binary_search(arr, target):\n    return undefined_var", "binary_search")
    assert result.passed is False
    assert result.estimated_exponent is None
