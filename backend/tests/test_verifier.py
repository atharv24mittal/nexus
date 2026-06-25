"""test_verifier.py — correctness of property-based and SMT-based verifiers."""

from app.core import verifier as v


class TestSorting:
    def test_correctly_sorted(self):
        assert v.verify_sorting([3, 1, 2], [1, 2, 3]).passed

    def test_wrong_order_fails(self):
        result = v.verify_sorting([3, 1, 2], [2, 1, 3])
        assert not result.passed
        assert "sorted" in result.message.lower()

    def test_dropped_element_fails(self):
        assert not v.verify_sorting([3, 1, 2], [1, 2]).passed

    def test_duplicated_element_fails(self):
        assert not v.verify_sorting([1, 2, 3], [1, 1, 2]).passed

    def test_empty_list(self):
        assert v.verify_sorting([], []).passed


class TestBinarySearch:
    def test_found_correctly(self):
        assert v.verify_binary_search_correctness([1, 3, 5, 7, 9], 5, 2).passed

    def test_correct_negative_one_when_absent(self):
        assert v.verify_binary_search_correctness([1, 3, 5, 7, 9], 4, -1).passed

    def test_wrong_negative_one_when_present(self):
        assert not v.verify_binary_search_correctness([1, 3, 5, 7, 9], 5, -1).passed

    def test_wrong_index_returned(self):
        assert not v.verify_binary_search_correctness([1, 3, 5, 7, 9], 5, 0).passed

    def test_out_of_bounds_index(self):
        assert not v.verify_binary_search_correctness([1, 3, 5], 3, 99).passed


class TestTwoSumSMT:
    def test_valid_pair_accepted(self):
        assert v.verify_two_sum_smt([2, 7, 11, 15], 9, [0, 1]).passed

    def test_wrong_pair_rejected(self):
        result = v.verify_two_sum_smt([2, 7, 11, 15], 9, [0, 2])
        assert not result.passed

    def test_correctly_proves_no_solution(self):
        assert v.verify_two_sum_smt([1, 1, 1], 100, []).passed

    def test_smt_catches_false_claim_of_no_solution(self):
        """The z3 proof should catch a candidate that wrongly claims no pair exists."""
        result = v.verify_two_sum_smt([2, 7, 11, 15], 9, [])
        assert not result.passed
        assert result.method == "smt_z3"
        assert "PROVED" in result.message

    def test_same_index_twice_rejected(self):
        assert not v.verify_two_sum_smt([3, 3, 3], 6, [0, 0]).passed


class TestPalindrome:
    def test_true_positive(self):
        assert v.verify_palindrome("racecar", True).passed

    def test_false_positive_caught(self):
        assert not v.verify_palindrome("hello", True).passed

    def test_empty_string_is_palindrome(self):
        assert v.verify_palindrome("", True).passed


class TestBalancedParens:
    def test_balanced(self):
        assert v.verify_balanced_parens("()()", True).passed

    def test_unbalanced_close_first(self):
        assert v.verify_balanced_parens(")(", False).passed

    def test_wrong_claim_caught(self):
        assert not v.verify_balanced_parens(")(", True).passed

    def test_unclosed(self):
        assert v.verify_balanced_parens("((()", False).passed


class TestMaxSubarray:
    def test_known_case(self):
        assert v.verify_max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4], 6).passed

    def test_wrong_answer_caught(self):
        assert not v.verify_max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4], 100).passed

    def test_all_negative(self):
        assert v.verify_max_subarray([-5, -2, -8, -1], -1).passed


def test_dispatcher_routes_correctly():
    assert v.verify("sorting", [[3, 1, 2]], [1, 2, 3]).passed
    assert v.verify("two_sum", [[2, 7], 9], [0, 1]).passed
