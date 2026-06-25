"""test_verifier_extended.py — the 8 problems added in the feature expansion."""

from app.core import verifier as v


class TestReverseString:
    def test_correct(self):
        assert v.verify_reverse_string("hello", "olleh").passed

    def test_wrong(self):
        assert not v.verify_reverse_string("hello", "hello").passed

    def test_empty(self):
        assert v.verify_reverse_string("", "").passed


class TestCountVowels:
    def test_correct(self):
        assert v.verify_count_vowels("hello world", 3).passed

    def test_wrong(self):
        assert not v.verify_count_vowels("hello world", 0).passed

    def test_no_vowels(self):
        assert v.verify_count_vowels("xyz", 0).passed


class TestFibonacci:
    def test_base_cases(self):
        assert v.verify_fibonacci(0, 0).passed
        assert v.verify_fibonacci(1, 1).passed

    def test_known_value(self):
        assert v.verify_fibonacci(10, 55).passed

    def test_wrong(self):
        assert not v.verify_fibonacci(10, 50).passed


class TestGcd:
    def test_correct(self):
        assert v.verify_gcd(48, 18, 6).passed

    def test_coprime(self):
        assert v.verify_gcd(7, 13, 1).passed

    def test_wrong(self):
        assert not v.verify_gcd(48, 18, 1).passed


class TestIsPrime:
    def test_primes(self):
        for p in [2, 3, 5, 7, 11, 17, 97]:
            assert v.verify_is_prime(p, True).passed

    def test_non_primes(self):
        for n in [0, 1, 4, 6, 8, 9, 100]:
            assert v.verify_is_prime(n, False).passed

    def test_wrong_claim(self):
        assert not v.verify_is_prime(17, False).passed


class TestRemoveDuplicates:
    def test_correct(self):
        assert v.verify_remove_duplicates([1, 2, 1, 3, 2], [1, 2, 3]).passed

    def test_wrong_order(self):
        assert not v.verify_remove_duplicates([1, 2, 1, 3, 2], [1, 3, 2]).passed

    def test_no_duplicates(self):
        assert v.verify_remove_duplicates([1, 2, 3], [1, 2, 3]).passed

    def test_empty(self):
        assert v.verify_remove_duplicates([], []).passed


class TestValidAnagram:
    def test_true_case(self):
        assert v.verify_valid_anagram("listen", "silent", True).passed

    def test_false_case(self):
        assert v.verify_valid_anagram("abc", "abd", False).passed

    def test_wrong_claim(self):
        assert not v.verify_valid_anagram("abc", "abd", True).passed


class TestFindMinMax:
    def test_correct(self):
        assert v.verify_find_min_max([3, 1, 4, 1, 5, 9, 2, 6], [1, 9]).passed

    def test_wrong(self):
        assert not v.verify_find_min_max([3, 1, 4, 1, 5, 9, 2, 6], [0, 9]).passed

    def test_single_element(self):
        assert v.verify_find_min_max([5], [5, 5]).passed


def test_all_14_problems_dispatch_correctly():
    from app.core.problems import PROBLEMS
    assert len(PROBLEMS) == 14
    for problem_id, problem in PROBLEMS.items():
        # Each problem's verifier_key must be registered in the dispatcher
        assert problem.verifier_key in v._DISPATCH, f"{problem_id} has unregistered verifier_key"
