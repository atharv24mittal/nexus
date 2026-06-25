"""
test_sandbox_security.py
-------------------------
The sandbox is the most safety-critical component in NEXUS: it executes
arbitrary, untrusted, LLM-generated code. These tests assert the security
boundary holds against common escape attempts, not just that "normal" code
works.
"""

from app.core.sandbox import run_candidate


def test_normal_code_executes_correctly():
    r = run_candidate("def add(a, b):\n    return a + b", "add", [[2, 3], [10, 20]])
    assert r.success
    assert [c.output for c in r.results] == [5, 30]


def test_os_module_is_unreachable():
    r = run_candidate(
        "def f(a, b):\n    os.system('echo pwned')\n    return a + b", "f", [[1, 2]],
    )
    assert r.success  # sandbox process itself didn't crash
    assert r.results[0].error is not None
    assert "NameError" in r.results[0].error


def test_dunder_import_is_blocked():
    r = run_candidate(
        "def f(a, b):\n    m = __import__('os')\n    return a + b", "f", [[1, 2]],
    )
    assert r.results[0].error is not None
    assert "NameError" in r.results[0].error


def test_open_builtin_is_blocked():
    r = run_candidate(
        "def f(a, b):\n    fh = open('/etc/passwd')\n    return fh.read()", "f", [[1, 2]],
    )
    assert r.results[0].error is not None
    assert "NameError" in r.results[0].error


def test_eval_and_exec_are_blocked():
    r1 = run_candidate("def f(a, b):\n    return eval('a+b')", "f", [[1, 2]])
    assert r1.results[0].error is not None and "NameError" in r1.results[0].error

    r2 = run_candidate("def f(a, b):\n    exec('x=1')\n    return a+b", "f", [[1, 2]])
    assert r2.results[0].error is not None and "NameError" in r2.results[0].error


def test_infinite_loop_is_killed_by_resource_limit():
    r = run_candidate("def f(a, b):\n    while True:\n        pass", "f", [[1, 2]])
    assert r.success is False
    assert r.timed_out is True


def test_missing_entry_point_reports_clean_error():
    r = run_candidate("def wrong_name(a, b):\n    return a + b", "expected_name", [[1, 2]])
    assert r.results[0].error is not None
    assert "expected_name" in r.results[0].error


def test_oversized_code_is_rejected_before_execution():
    huge_code = "def f(a, b):\n    " + "x = 1\n    " * 5000
    r = run_candidate(huge_code, "f", [[1, 2]])
    assert r.success is False
    assert r.error == "CodeTooLong"


def test_runtime_exceptions_in_candidate_are_caught_not_propagated():
    r = run_candidate("def f(a, b):\n    return a[100]", "f", [[[1, 2, 3], 0]])
    assert r.success is True  # sandbox itself didn't crash
    assert "IndexError" in r.results[0].error


def test_syntax_error_in_candidate_is_reported_cleanly():
    r = run_candidate("def f(a, b)\n    return a + b", "f", [[1, 2]])
    # The sandbox PROCESS doesn't crash — it reports the SyntaxError as a
    # per-case error, the same way it reports any other candidate exception.
    assert r.success is True
    assert r.results[0].error is not None
    assert "SyntaxError" in r.results[0].error
