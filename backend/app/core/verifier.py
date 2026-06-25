"""
verifier.py
-----------
NEXUS verifies candidate solutions two different ways, and is deliberate
about which tool fits which problem — that judgment call is the point:

  1. PROPERTY-BASED VERIFICATION (sorting, palindrome, balanced_parens,
     max_subarray): for a CONCRETE input/output pair, correctness is a
     directly-checkable predicate (e.g. "is the output sorted AND a
     permutation of the input?"). Computing a ground truth and comparing,
     or scanning the structural invariant directly, is the textbook right
     tool here — the same approach used by Hypothesis/QuickCheck-style
     property testing. Dressing this up as an SMT query would add
     ceremony without adding power.

  2. SMT-BASED VERIFICATION (two_sum): this is fundamentally an EXISTENCE
     question over a discrete search space ("does there exist a valid
     index pair?"), which is exactly what SMT solvers are built for. When
     the candidate claims "no solution exists", NEXUS asks z3 to either
     find a satisfying assignment (proving the candidate wrong) or return
     UNSAT (proving the candidate right) — a genuine correctness PROOF,
     not just "we didn't find one in our test cases."

binary_search additionally gets an empirical time-complexity probe
(see complexity.py) since "runs in O(log n)" is a claim about *behavior
across input sizes*, not about any single input/output pair.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import z3


@dataclass
class VerificationResult:
    passed: bool
    violated_constraint: Optional[str]
    counterexample: Optional[dict]
    message: str
    method: str  # "property_based" | "smt_z3" | "ground_truth"


# ───────────────────────── Property-based verifiers ─────────────────────────

def verify_sorting(arr: list[int], output: Any) -> VerificationResult:
    if not isinstance(output, list):
        return VerificationResult(False, "output must be a list", {"got_type": str(type(output))},
                                   "Output is not a list", "property_based")
    if len(output) != len(arr):
        return VerificationResult(False, "len(output) == len(input)", {"input": arr, "output": output},
                                   f"Length mismatch: expected {len(arr)}, got {len(output)}", "property_based")
    for i in range(len(output) - 1):
        if output[i] > output[i + 1]:
            return VerificationResult(
                False, "output[i] <= output[i+1] for all i",
                {"input": arr, "output": output, "violation_index": i},
                f"Not sorted at index {i}: {output[i]} > {output[i + 1]}", "property_based",
            )
    if sorted(output) != sorted(arr):
        return VerificationResult(
            False, "multiset(output) == multiset(input)",
            {"input": arr, "output": output},
            "Output is not a permutation of the input (elements changed)", "property_based",
        )
    return VerificationResult(True, None, None, "Sorted correctly and is a valid permutation", "property_based")


def verify_binary_search_correctness(arr: list[int], target: int, output: Any) -> VerificationResult:
    if not isinstance(output, int):
        return VerificationResult(False, "output must be an int", {"got_type": str(type(output))},
                                   "Output is not an integer index", "property_based")
    ground_truth = -1
    for i, v in enumerate(arr):
        if v == target:
            ground_truth = i
            break
    if output == -1:
        if target not in arr:
            return VerificationResult(True, None, None, "Correctly reported absence", "ground_truth")
        return VerificationResult(
            False, "output == -1 implies target not in arr",
            {"arr": arr, "target": target, "output": output},
            f"Target {target} IS in arr but candidate returned -1", "ground_truth",
        )
    if not (0 <= output < len(arr)):
        return VerificationResult(False, "0 <= output < len(arr)", {"arr": arr, "output": output},
                                   "Returned index is out of bounds", "property_based")
    if arr[output] != target:
        return VerificationResult(
            False, "arr[output] == target", {"arr": arr, "target": target, "output": output},
            f"arr[{output}] = {arr[output]}, but target was {target}", "ground_truth",
        )
    return VerificationResult(True, None, None, "Returned a valid index for the target", "ground_truth")


def verify_palindrome(s: str, output: Any) -> VerificationResult:
    expected = s == s[::-1]
    if output != expected:
        return VerificationResult(
            False, "output == (s == reversed(s))", {"input": s, "expected": expected, "got": output},
            f"For '{s}', expected {expected} but got {output}", "ground_truth",
        )
    return VerificationResult(True, None, None, "Matches ground truth", "ground_truth")


def verify_balanced_parens(s: str, output: Any) -> VerificationResult:
    depth = 0
    expected = True
    for ch in s:
        depth += 1 if ch == "(" else -1
        if depth < 0:
            expected = False
            break
    expected = expected and depth == 0
    if output != expected:
        return VerificationResult(
            False, "output == ground_truth_stack_check", {"input": s, "expected": expected, "got": output},
            f"For '{s}', expected {expected} but got {output}", "ground_truth",
        )
    return VerificationResult(True, None, None, "Matches ground truth", "ground_truth")


def verify_max_subarray(arr: list[int], output: Any) -> VerificationResult:
    # Ground truth via Kadane's algorithm
    best = cur = arr[0]
    for x in arr[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    if output != best:
        return VerificationResult(
            False, "output == max_contiguous_sum(arr)", {"input": arr, "expected": best, "got": output},
            f"Expected max subarray sum {best}, got {output}", "ground_truth",
        )
    return VerificationResult(True, None, None, "Matches Kadane's ground truth", "ground_truth")


def verify_reverse_string(s: str, output: Any) -> VerificationResult:
    expected = s[::-1]
    if output != expected:
        return VerificationResult(
            False, "output == reversed(s)", {"input": s, "expected": expected, "got": output},
            f"For '{s}', expected '{expected}' but got '{output}'", "ground_truth",
        )
    return VerificationResult(True, None, None, "Matches ground truth", "ground_truth")


def verify_count_vowels(s: str, output: Any) -> VerificationResult:
    expected = sum(1 for c in s if c in "aeiou")
    if output != expected:
        return VerificationResult(
            False, "output == count(c in s if c is a vowel)", {"input": s, "expected": expected, "got": output},
            f"For '{s}', expected {expected} vowels but got {output}", "ground_truth",
        )
    return VerificationResult(True, None, None, "Matches ground truth", "ground_truth")


def verify_fibonacci(n: int, output: Any) -> VerificationResult:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    expected = a
    if output != expected:
        return VerificationResult(
            False, "output == fibonacci(n)", {"input": n, "expected": expected, "got": output},
            f"fibonacci({n}) should be {expected}, got {output}", "ground_truth",
        )
    return VerificationResult(True, None, None, "Matches ground truth", "ground_truth")


def verify_gcd(a: int, b: int, output: Any) -> VerificationResult:
    import math
    expected = math.gcd(a, b)
    if output != expected:
        return VerificationResult(
            False, "output == gcd(a, b)", {"input": [a, b], "expected": expected, "got": output},
            f"gcd({a}, {b}) should be {expected}, got {output}", "ground_truth",
        )
    return VerificationResult(True, None, None, "Matches ground truth", "ground_truth")


def verify_is_prime(n: int, output: Any) -> VerificationResult:
    def _is_prime(k):
        if k < 2:
            return False
        for i in range(2, int(k ** 0.5) + 1):
            if k % i == 0:
                return False
        return True
    expected = _is_prime(n)
    if output != expected:
        return VerificationResult(
            False, "output == is_prime(n)", {"input": n, "expected": expected, "got": output},
            f"is_prime({n}) should be {expected}, got {output}", "ground_truth",
        )
    return VerificationResult(True, None, None, "Matches ground truth", "ground_truth")


def verify_remove_duplicates(arr: list[int], output: Any) -> VerificationResult:
    if not isinstance(output, list):
        return VerificationResult(False, "output must be a list", {"got_type": str(type(output))},
                                   "Output is not a list", "property_based")
    seen = set()
    expected = []
    for x in arr:
        if x not in seen:
            seen.add(x)
            expected.append(x)
    if output != expected:
        return VerificationResult(
            False, "output == first_occurrence_dedup(arr)", {"input": arr, "expected": expected, "got": output},
            f"Expected {expected} (order-preserving dedup), got {output}", "ground_truth",
        )
    return VerificationResult(True, None, None, "Matches ground truth", "ground_truth")


def verify_valid_anagram(s1: str, s2: str, output: Any) -> VerificationResult:
    from collections import Counter
    expected = Counter(s1) == Counter(s2)
    if output != expected:
        return VerificationResult(
            False, "output == (Counter(s1) == Counter(s2))", {"input": [s1, s2], "expected": expected, "got": output},
            f"For '{s1}' vs '{s2}', expected {expected} but got {output}", "ground_truth",
        )
    return VerificationResult(True, None, None, "Matches ground truth", "ground_truth")


def verify_find_min_max(arr: list[int], output: Any) -> VerificationResult:
    expected = [min(arr), max(arr)]
    if output != expected:
        return VerificationResult(
            False, "output == [min(arr), max(arr)]", {"input": arr, "expected": expected, "got": output},
            f"Expected {expected}, got {output}", "ground_truth",
        )
    return VerificationResult(True, None, None, "Matches ground truth", "ground_truth")


# ───────────────────────── SMT (z3) verifier ─────────────────────────

def verify_two_sum_smt(arr: list[int], target: int, output: Any) -> VerificationResult:
    """
    Genuine SMT use: encode "does a valid index pair exist?" as a z3
    satisfiability query, independent of whatever the candidate returned.
    Then check the candidate's claim against that proof.
    """
    n = len(arr)
    i, j = z3.Int("i"), z3.Int("j")
    solver = z3.Solver()
    solver.add(i >= 0, i < n, j >= 0, j < n, i != j)
    # Encode arr[i] + arr[j] == target via a disjunction over concrete indices
    # (arr is concrete data, not a z3 array — this is the correct encoding
    # for a *fixed* input, since z3's job here is the EXISTENTIAL search
    # over (i, j), not modeling unknown array contents).
    clauses = []
    for a in range(n):
        for b in range(n):
            if a != b and arr[a] + arr[b] == target:
                clauses.append(z3.And(i == a, j == b))
    if clauses:
        solver.add(z3.Or(*clauses))
    else:
        solver.add(z3.BoolVal(False))

    smt_result = solver.check()
    solution_exists = smt_result == z3.sat
    proof_pair = None
    if solution_exists:
        model = solver.model()
        proof_pair = [model[i].as_long(), model[j].as_long()]

    # Now check the candidate's claim against the SMT-proven ground truth
    if not isinstance(output, list):
        return VerificationResult(False, "output must be a list", {"got_type": str(type(output))},
                                   "Output is not a list", "smt_z3")

    if len(output) == 0:
        if solution_exists:
            return VerificationResult(
                False, "exists i,j: arr[i]+arr[j]==target (SMT-proven SAT)",
                {"arr": arr, "target": target, "smt_found_pair": proof_pair},
                f"z3 PROVED a valid pair exists {proof_pair}, but candidate claimed none", "smt_z3",
            )
        return VerificationResult(True, None, None, "z3 PROVED (UNSAT) that no valid pair exists — candidate correctly returned []", "smt_z3")

    if len(output) != 2:
        return VerificationResult(False, "output has exactly 2 indices or is empty", {"output": output},
                                   "Output must be [] or a 2-element list", "property_based")

    oi, oj = output
    if not (isinstance(oi, int) and isinstance(oj, int) and 0 <= oi < n and 0 <= oj < n and oi != oj):
        return VerificationResult(False, "valid distinct in-bounds indices", {"output": output},
                                   "Indices out of bounds or not distinct", "property_based")
    if arr[oi] + arr[oj] != target:
        return VerificationResult(
            False, "arr[i]+arr[j]==target", {"arr": arr, "target": target, "output": output},
            f"arr[{oi}]+arr[{oj}] = {arr[oi] + arr[oj]} != {target}", "ground_truth",
        )
    return VerificationResult(True, None, None, f"Valid pair {output}, consistent with z3 SAT proof", "smt_z3")


# ───────────────────────── Dispatcher ─────────────────────────

_DISPATCH = {
    "sorting": lambda inp, out: verify_sorting(inp[0], out),
    "binary_search": lambda inp, out: verify_binary_search_correctness(inp[0], inp[1], out),
    "two_sum": lambda inp, out: verify_two_sum_smt(inp[0], inp[1], out),
    "palindrome": lambda inp, out: verify_palindrome(inp[0], out),
    "balanced_parens": lambda inp, out: verify_balanced_parens(inp[0], out),
    "max_subarray": lambda inp, out: verify_max_subarray(inp[0], out),
    "reverse_string": lambda inp, out: verify_reverse_string(inp[0], out),
    "count_vowels": lambda inp, out: verify_count_vowels(inp[0], out),
    "fibonacci": lambda inp, out: verify_fibonacci(inp[0], out),
    "gcd": lambda inp, out: verify_gcd(inp[0], inp[1], out),
    "is_prime": lambda inp, out: verify_is_prime(inp[0], out),
    "remove_duplicates": lambda inp, out: verify_remove_duplicates(inp[0], out),
    "valid_anagram": lambda inp, out: verify_valid_anagram(inp[0], inp[1], out),
    "find_min_max": lambda inp, out: verify_find_min_max(inp[0], out),
}


def verify(verifier_key: str, test_input: list, output: Any) -> VerificationResult:
    if verifier_key not in _DISPATCH:
        raise KeyError(f"No verifier registered for key: {verifier_key}")
    return _DISPATCH[verifier_key](test_input, output)
