"""
problems.py
-----------
The curated problem bank. Each problem has:
  - a natural-language description (used as the LLM prompt)
  - an entry_point (the function name the generated code must define)
  - sample test inputs (used to actually run the candidate via the sandbox)
  - a `verifier_key` pointing to a property-based / z3 verifier in verifier.py

Deliberately scoped to problem classes where correctness is a property that
can be *checked*, not just *guessed from a couple of examples* — that's the
whole point of NEXUS. Adding a new problem = writing a new description +
a new verifier function; the agent loop, sandbox, and skill library don't change.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random


@dataclass
class Problem:
    id: str
    title: str
    description: str
    entry_point: str
    verifier_key: str
    difficulty: str
    sample_input_generator: callable = field(repr=False)

    def generate_test_inputs(self, n: int = 8, seed: int = 42) -> list[list]:
        rng = random.Random(seed)
        return [self.sample_input_generator(rng) for _ in range(n)]


def _gen_sort_input(rng: random.Random):
    n = rng.randint(0, 15)
    return [[rng.randint(-100, 100) for _ in range(n)]]


def _gen_binary_search_input(rng: random.Random):
    n = rng.randint(1, 20)
    arr = sorted(rng.randint(-50, 50) for _ in range(n))
    # 50% chance the target actually exists in the array
    target = rng.choice(arr) if (arr and rng.random() < 0.5) else rng.randint(-60, 60)
    return [arr, target]


def _gen_two_sum_input(rng: random.Random):
    n = rng.randint(2, 12)
    arr = [rng.randint(-50, 50) for _ in range(n)]
    if rng.random() < 0.6:
        i, j = rng.sample(range(n), 2)
        target = arr[i] + arr[j]
    else:
        target = rng.randint(-100, 100)
    return [arr, target]


def _gen_palindrome_input(rng: random.Random):
    import string
    n = rng.randint(0, 12)
    if rng.random() < 0.4:
        half = "".join(rng.choice(string.ascii_lowercase) for _ in range(n // 2))
        s = half + (half[::-1] if n % 2 == 0 else rng.choice(string.ascii_lowercase) + half[::-1])
    else:
        s = "".join(rng.choice(string.ascii_lowercase) for _ in range(n))
    return [s]


def _gen_balanced_parens_input(rng: random.Random):
    chars = "()"
    n = rng.randint(0, 16)
    s = "".join(rng.choice(chars) for _ in range(n))
    return [s]


def _gen_max_subarray_input(rng: random.Random):
    n = rng.randint(1, 15)
    return [[rng.randint(-30, 30) for _ in range(n)]]


def _gen_reverse_string_input(rng: random.Random):
    import string
    n = rng.randint(0, 15)
    return ["".join(rng.choice(string.ascii_lowercase) for _ in range(n))]


def _gen_count_vowels_input(rng: random.Random):
    import string
    n = rng.randint(0, 20)
    return ["".join(rng.choice(string.ascii_lowercase) for _ in range(n))]


def _gen_fibonacci_input(rng: random.Random):
    return [rng.randint(0, 25)]


def _gen_gcd_input(rng: random.Random):
    return [rng.randint(1, 500), rng.randint(1, 500)]


def _gen_is_prime_input(rng: random.Random):
    return [rng.randint(0, 200)]


def _gen_remove_duplicates_input(rng: random.Random):
    n = rng.randint(0, 15)
    return [[rng.randint(0, 6) for _ in range(n)]]  # small range forces real duplicates


def _gen_valid_anagram_input(rng: random.Random):
    import string
    n = rng.randint(0, 10)
    base = "".join(rng.choice(string.ascii_lowercase[:6]) for _ in range(n))
    if rng.random() < 0.5:
        other = "".join(rng.sample(base, len(base))) if base else ""
    else:
        other = "".join(rng.choice(string.ascii_lowercase[:6]) for _ in range(n))
    return [base, other]


def _gen_find_min_max_input(rng: random.Random):
    n = rng.randint(1, 15)
    return [[rng.randint(-100, 100) for _ in range(n)]]


PROBLEMS: dict[str, Problem] = {
    "sort_list": Problem(
        id="sort_list",
        title="Sort a list of integers",
        description=(
            "Write a Python function `sort_list(arr)` that takes a list of integers "
            "and returns a NEW list containing the same integers sorted in non-decreasing order. "
            "Do not use the built-in sorted() or .sort() — implement the sorting logic yourself "
            "(any correct algorithm: bubble, insertion, merge, quick, etc.)."
        ),
        entry_point="sort_list",
        verifier_key="sorting",
        difficulty="easy",
        sample_input_generator=_gen_sort_input,
    ),
    "binary_search": Problem(
        id="binary_search",
        title="Binary search in a sorted array",
        description=(
            "Write a Python function `binary_search(arr, target)` that takes a list of integers "
            "SORTED in non-decreasing order and an integer target. Return the index of `target` "
            "in `arr` if it exists, otherwise return -1. Must run in O(log n) time using binary search "
            "(not a linear scan)."
        ),
        entry_point="binary_search",
        verifier_key="binary_search",
        difficulty="easy",
        sample_input_generator=_gen_binary_search_input,
    ),
    "two_sum": Problem(
        id="two_sum",
        title="Two Sum",
        description=(
            "Write a Python function `two_sum(arr, target)` that takes a list of integers and a target "
            "integer. Return a list [i, j] of two DISTINCT indices such that arr[i] + arr[j] == target, "
            "with i < j. If no such pair exists, return an empty list []. If multiple pairs exist, "
            "returning any valid one is acceptable."
        ),
        entry_point="two_sum",
        verifier_key="two_sum",
        difficulty="medium",
        sample_input_generator=_gen_two_sum_input,
    ),
    "is_palindrome": Problem(
        id="is_palindrome",
        title="Check if a string is a palindrome",
        description=(
            "Write a Python function `is_palindrome(s)` that takes a string `s` (lowercase letters only) "
            "and returns True if it reads the same forwards and backwards, otherwise False. "
            "Empty string and single-character strings are palindromes."
        ),
        entry_point="is_palindrome",
        verifier_key="palindrome",
        difficulty="easy",
        sample_input_generator=_gen_palindrome_input,
    ),
    "balanced_parens": Problem(
        id="balanced_parens",
        title="Validate balanced parentheses",
        description=(
            "Write a Python function `balanced_parens(s)` that takes a string `s` containing only "
            "'(' and ')' characters, and returns True if the parentheses are balanced "
            "(every open paren has a matching close paren, and they are properly nested), otherwise False."
        ),
        entry_point="balanced_parens",
        verifier_key="balanced_parens",
        difficulty="medium",
        sample_input_generator=_gen_balanced_parens_input,
    ),
    "max_subarray": Problem(
        id="max_subarray",
        title="Maximum subarray sum (Kadane's algorithm)",
        description=(
            "Write a Python function `max_subarray(arr)` that takes a non-empty list of integers "
            "and returns the maximum possible sum of a CONTIGUOUS subarray (at least one element). "
            "Must run in O(n) time."
        ),
        entry_point="max_subarray",
        verifier_key="max_subarray",
        difficulty="medium",
        sample_input_generator=_gen_max_subarray_input,
    ),
    "reverse_string": Problem(
        id="reverse_string",
        title="Reverse a string",
        description=(
            "Write a Python function `reverse_string(s)` that takes a string and returns it reversed. "
            "Do not use slicing tricks like s[::-1] or the built-in reversed() — implement the "
            "reversal logic yourself (e.g. with a loop or swapping)."
        ),
        entry_point="reverse_string",
        verifier_key="reverse_string",
        difficulty="easy",
        sample_input_generator=_gen_reverse_string_input,
    ),
    "count_vowels": Problem(
        id="count_vowels",
        title="Count vowels in a string",
        description=(
            "Write a Python function `count_vowels(s)` that takes a lowercase string and returns "
            "the number of vowels (a, e, i, o, u) it contains."
        ),
        entry_point="count_vowels",
        verifier_key="count_vowels",
        difficulty="easy",
        sample_input_generator=_gen_count_vowels_input,
    ),
    "fibonacci": Problem(
        id="fibonacci",
        title="Nth Fibonacci number",
        description=(
            "Write a Python function `fibonacci(n)` that returns the nth Fibonacci number, where "
            "fibonacci(0) = 0, fibonacci(1) = 1, and fibonacci(n) = fibonacci(n-1) + fibonacci(n-2) "
            "for n >= 2. n is a non-negative integer."
        ),
        entry_point="fibonacci",
        verifier_key="fibonacci",
        difficulty="easy",
        sample_input_generator=_gen_fibonacci_input,
    ),
    "gcd": Problem(
        id="gcd",
        title="Greatest common divisor",
        description=(
            "Write a Python function `gcd(a, b)` that returns the greatest common divisor of two "
            "positive integers a and b. Do not use math.gcd — implement it yourself "
            "(e.g. via the Euclidean algorithm)."
        ),
        entry_point="gcd",
        verifier_key="gcd",
        difficulty="easy",
        sample_input_generator=_gen_gcd_input,
    ),
    "is_prime": Problem(
        id="is_prime",
        title="Check if a number is prime",
        description=(
            "Write a Python function `is_prime(n)` that takes a non-negative integer and returns "
            "True if it's prime, otherwise False. 0 and 1 are not prime."
        ),
        entry_point="is_prime",
        verifier_key="is_prime",
        difficulty="easy",
        sample_input_generator=_gen_is_prime_input,
    ),
    "remove_duplicates": Problem(
        id="remove_duplicates",
        title="Remove duplicates, preserve order",
        description=(
            "Write a Python function `remove_duplicates(arr)` that takes a list of integers and "
            "returns a NEW list containing only the first occurrence of each value, preserving the "
            "original relative order (e.g. [1,2,1,3,2] -> [1,2,3])."
        ),
        entry_point="remove_duplicates",
        verifier_key="remove_duplicates",
        difficulty="medium",
        sample_input_generator=_gen_remove_duplicates_input,
    ),
    "valid_anagram": Problem(
        id="valid_anagram",
        title="Valid anagram",
        description=(
            "Write a Python function `valid_anagram(s1, s2)` that takes two lowercase strings and "
            "returns True if they're anagrams of each other (same letters, same counts, any order), "
            "otherwise False."
        ),
        entry_point="valid_anagram",
        verifier_key="valid_anagram",
        difficulty="easy",
        sample_input_generator=_gen_valid_anagram_input,
    ),
    "find_min_max": Problem(
        id="find_min_max",
        title="Find min and max in one pass",
        description=(
            "Write a Python function `find_min_max(arr)` that takes a non-empty list of integers "
            "and returns [min_value, max_value] in a single pass through the list (don't call the "
            "built-in min() and max() separately — track both while iterating once)."
        ),
        entry_point="find_min_max",
        verifier_key="find_min_max",
        difficulty="easy",
        sample_input_generator=_gen_find_min_max_input,
    ),
}


def get_problem(problem_id: str) -> Problem:
    if problem_id not in PROBLEMS:
        raise KeyError(f"Unknown problem id: {problem_id}")
    return PROBLEMS[problem_id]


def list_problems() -> list[dict]:
    return [
        {"id": p.id, "title": p.title, "difficulty": p.difficulty}
        for p in PROBLEMS.values()
    ]
