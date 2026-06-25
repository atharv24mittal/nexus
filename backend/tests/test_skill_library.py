"""test_skill_library.py — bug/fix pattern storage and TF-IDF retrieval."""

import pathlib
import tempfile

import pytest

from app.core.skill_library import SkillLibrary, BugFixPair


@pytest.fixture
def lib():
    tmp = pathlib.Path(tempfile.mktemp(suffix=".db"))
    library = SkillLibrary(db_path=tmp)
    yield library
    library.close()
    tmp.unlink(missing_ok=True)


def test_store_and_count(lib):
    assert lib.count() == 0
    lib.store(BugFixPair(
        problem_id="sort_list", bug_type="off_by_one", buggy_code="bad code",
        violated_constraint="output[i] <= output[i+1]", fix_explanation="fixed loop bound",
        fixed_code="good code", reward=0.7,
    ))
    assert lib.count() == 1


def test_low_reward_patterns_are_not_stored(lib):
    stored = lib.store(BugFixPair(
        problem_id="sort_list", bug_type="trivial", buggy_code="x", violated_constraint="y",
        fix_explanation="z", fixed_code="w", reward=0.1,
    ))
    assert stored is False
    assert lib.count() == 0


def test_retrieval_is_scoped_by_problem_id(lib):
    lib.store(BugFixPair(
        problem_id="sort_list", bug_type="off_by_one", buggy_code="sort bug",
        violated_constraint="output[i] <= output[i+1]", fix_explanation="fixed",
        fixed_code="ok", reward=1.0,
    ))
    lib.store(BugFixPair(
        problem_id="two_sum", bug_type="wrong_arithmetic", buggy_code="two sum bug",
        violated_constraint="arr[i]+arr[j]==target", fix_explanation="fixed arithmetic",
        fixed_code="ok", reward=1.0,
    ))
    results = lib.retrieve_similar("off_by_one bug", problem_id="sort_list", k=5)
    assert len(results) == 1
    assert results[0]["problem_id"] == "sort_list"


def test_few_shot_context_is_empty_when_no_patterns_exist(lib):
    assert lib.build_few_shot_context("anything", problem_id="sort_list") == ""


def test_few_shot_context_includes_fix_explanation(lib):
    lib.store(BugFixPair(
        problem_id="sort_list", bug_type="off_by_one", buggy_code="bad",
        violated_constraint="output[i] <= output[i+1]",
        fix_explanation="Loop bound was wrong",
        fixed_code="good", reward=0.7,
    ))
    ctx = lib.build_few_shot_context("off_by_one output[i] <= output[i+1]", problem_id="sort_list")
    assert "Loop bound was wrong" in ctx


def test_stats_groups_by_bug_type(lib):
    lib.store(BugFixPair(problem_id="a", bug_type="type_x", buggy_code="x",
                          violated_constraint="c", fix_explanation="e", fixed_code="f", reward=1.0))
    lib.store(BugFixPair(problem_id="a", bug_type="type_x", buggy_code="x",
                          violated_constraint="c", fix_explanation="e", fixed_code="f", reward=1.0))
    lib.store(BugFixPair(problem_id="a", bug_type="type_y", buggy_code="x",
                          violated_constraint="c", fix_explanation="e", fixed_code="f", reward=1.0))
    stats = lib.stats()
    assert stats["total_patterns"] == 3
    assert stats["by_bug_type"]["type_x"] == 2
    assert stats["by_bug_type"]["type_y"] == 1
