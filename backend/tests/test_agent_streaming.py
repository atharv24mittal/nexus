"""test_agent_streaming.py — solve_stream() emits the right real-time event sequence."""

import pathlib
import tempfile

import pytest

from app.core.agent import NexusAgent
from app.core.skill_library import SkillLibrary


class _AlwaysCorrectLLM:
    provider_name = "mock:always-correct"

    def generate_code(self, prompt, temperature=0.2):
        return (
            "def is_palindrome(s):\n"
            "    return s == s[::-1]\n"
        )

    def explain_fix(self, *args, **kwargs):
        return "n/a"


class _AlwaysBrokenLLM:
    provider_name = "mock:always-broken"

    def generate_code(self, prompt, temperature=0.2):
        return "def is_palindrome(s):\n    return True\n"  # wrong on non-palindromes

    def explain_fix(self, *args, **kwargs):
        return "n/a"


@pytest.fixture
def skills():
    tmp = pathlib.Path(tempfile.mktemp(suffix=".db"))
    lib = SkillLibrary(db_path=tmp)
    yield lib
    lib.close()
    tmp.unlink(missing_ok=True)


def test_successful_first_try_event_sequence(skills):
    agent = NexusAgent(llm_client=_AlwaysCorrectLLM(), skill_library=skills, max_attempts=5)
    events = list(agent.solve_stream("is_palindrome"))
    event_types = [e["event"] for e in events]

    assert event_types == [
        "attempt_start", "generating", "code_generated", "executing",
        "execution_complete", "verifying", "verification_result",
        "attempt_complete", "final_result",
    ]
    assert events[-1]["success"] is True
    assert events[-1]["attempts"][0]["attempt_number"] == 1


def test_exhausted_attempts_event_sequence_has_no_retrieving_fixes_after_last(skills):
    agent = NexusAgent(llm_client=_AlwaysBrokenLLM(), skill_library=skills, max_attempts=3)
    events = list(agent.solve_stream("is_palindrome"))

    assert events[-1]["event"] == "final_result"
    assert events[-1]["success"] is False
    assert len(events[-1]["attempts"]) == 3

    # "retrieving_fixes" should appear after attempts 1 and 2, but NOT after
    # attempt 3 (there's no attempt 4 to prepare a few-shot prompt for).
    retrieving_indices = [i for i, e in enumerate(events) if e["event"] == "retrieving_fixes"]
    assert len(retrieving_indices) == 2


def test_solve_and_solve_stream_agree_on_final_outcome(skills):
    agent_a = NexusAgent(llm_client=_AlwaysCorrectLLM(), skill_library=skills, max_attempts=5)
    result = agent_a.solve("is_palindrome")

    agent_b = NexusAgent(llm_client=_AlwaysCorrectLLM(), skill_library=skills, max_attempts=5)
    stream_events = list(agent_b.solve_stream("is_palindrome"))
    final = stream_events[-1]

    assert result.success == final["success"]
    assert result.final_code == final["final_code"]
    assert len(result.attempts) == len(final["attempts"])
