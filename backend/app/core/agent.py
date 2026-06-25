"""
agent.py
--------
The orchestrator. Ties together:
  generate (llm_client) -> execute (sandbox) -> verify (verifier) ->
  on failure: retrieve similar past fixes (skill_library) -> repair -> repeat
  on success: store the (bug, fix) pattern if any repairs were needed.

This is intentionally a plain Python loop, not a hidden framework — every
step is inspectable, which matters both for debugging and for explaining
the system in an interview.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app.core import verifier as verifier_module
from app.core.complexity import probe_binary_search_complexity, ComplexityProbeResult
from app.core.llm_client import NexusLLMClient
from app.core.problems import Problem, get_problem
from app.core.sandbox import run_candidate
from app.core.skill_library import SkillLibrary, BugFixPair

# Problems where a complexity probe (not just correctness) is part of the spec.
_COMPLEXITY_CHECKED_PROBLEMS = {"binary_search": probe_binary_search_complexity}


@dataclass
class AttemptRecord:
    attempt_number: int
    code: str
    trace: list[dict]
    stdout: str
    sandbox_error: str | None
    verification_passed: bool
    verification_message: str
    verification_method: str
    violated_constraint: str | None
    counterexample: dict | None
    complexity_check: dict | None = None


@dataclass
class SolveResult:
    success: bool
    problem_id: str
    final_code: str | None
    attempts: list[AttemptRecord] = field(default_factory=list)
    reward: float = 0.0
    elapsed_seconds: float = 0.0
    skill_library_hits_used: int = 0
    llm_provider: str = ""


def _bug_type_from_constraint(constraint: str | None) -> str:
    if not constraint:
        return "runtime_error"
    return constraint.replace(" ", "_")[:40]


def _reward_for_attempts(attempts: int, success: bool) -> float:
    if not success:
        return 0.0
    return {1: 1.0, 2: 0.7, 3: 0.5}.get(attempts, 0.3)


class NexusAgent:
    def __init__(self, llm_client: NexusLLMClient | None = None, skill_library: SkillLibrary | None = None,
                 max_attempts: int = 5):
        self.llm = llm_client or NexusLLMClient()
        self.skills = skill_library or SkillLibrary()
        self.max_attempts = max_attempts

    def _build_generation_prompt(self, problem: Problem, few_shot: str, prior_failure: AttemptRecord | None) -> str:
        prompt = f"Problem:\n{problem.description}\n\n"
        if few_shot:
            prompt += few_shot + "\n\n"
        if prior_failure:
            prompt += (
                "YOUR PREVIOUS ATTEMPT FAILED:\n"
                f"```python\n{prior_failure.code}\n```\n"
                f"Violated constraint: {prior_failure.violated_constraint}\n"
                f"Details: {prior_failure.verification_message}\n"
            )
            if prior_failure.counterexample:
                prompt += f"Counterexample: {prior_failure.counterexample}\n"
            prompt += "\nFix this specific issue. Return the corrected function.\n"
        return prompt

    def _run_complexity_check(self, problem_id: str, code: str, entry_point: str) -> dict | None:
        probe_fn = _COMPLEXITY_CHECKED_PROBLEMS.get(problem_id)
        if probe_fn is None:
            return None
        result: ComplexityProbeResult = probe_fn(code, entry_point)
        return {
            "passed": result.passed,
            "estimated_exponent": result.estimated_exponent,
            "message": result.message,
            "samples": result.samples,
        }

    def solve_stream(self, problem_id: str):
        """
        Generator version of the agent loop: yields an event dict the MOMENT
        each real thing happens (generation started, code came back, sandbox
        ran, verification finished, etc.) instead of building the whole
        result and returning it at the end. This is what /solve/stream uses
        to drive genuine real-time updates over Server-Sent Events — no
        "replay of an already-complete response," the frontend sees each
        step exactly as it occurs on the server.

        `solve()` below is a thin wrapper that exhausts this generator and
        returns the final SolveResult, for callers that don't need streaming
        (the non-streaming /solve endpoint, evaluate_baseline.py).
        """
        problem = get_problem(problem_id)
        start = time.time()
        test_inputs = problem.generate_test_inputs(n=10)

        attempts: list[AttemptRecord] = []
        few_shot = ""
        prior_failure: AttemptRecord | None = None
        skill_hits_used = 0

        for attempt_num in range(1, self.max_attempts + 1):
            yield {"event": "attempt_start", "attempt_number": attempt_num}
            yield {"event": "generating", "attempt_number": attempt_num}

            prompt = self._build_generation_prompt(problem, few_shot, prior_failure)
            code = self.llm.generate_code(prompt)
            yield {"event": "code_generated", "attempt_number": attempt_num, "code": code}

            yield {"event": "executing", "attempt_number": attempt_num}
            sandbox_result = run_candidate(code, problem.entry_point, test_inputs)
            trace = [{"line": t.line, "locals": t.locals} for t in sandbox_result.trace]
            yield {"event": "execution_complete", "attempt_number": attempt_num,
                   "trace": trace, "stdout": sandbox_result.stdout}

            if not sandbox_result.success or any(r.error for r in sandbox_result.results):
                first_error = sandbox_result.error or next(
                    (r.error for r in sandbox_result.results if r.error), "Unknown sandbox error"
                )
                record = AttemptRecord(
                    attempt_number=attempt_num, code=code, trace=trace,
                    stdout=sandbox_result.stdout, sandbox_error=first_error,
                    verification_passed=False, verification_message=f"Execution failed: {first_error}",
                    verification_method="sandbox", violated_constraint="no_runtime_error",
                    counterexample=None,
                )
                attempts.append(record)
                yield {"event": "attempt_complete", "attempt_number": attempt_num, "passed": False,
                       "attempt": record.__dict__}

                if attempt_num < self.max_attempts:
                    yield {"event": "retrieving_fixes", "attempt_number": attempt_num}
                few_shot = self.skills.build_few_shot_context(
                    f"runtime_error {first_error}", problem_id=problem_id, k=2
                )
                if few_shot:
                    skill_hits_used += 1
                prior_failure = record
                continue

            yield {"event": "verifying", "attempt_number": attempt_num}

            all_passed = True
            failing_result = None
            for case, test_input in zip(sandbox_result.results, test_inputs):
                if case.error:
                    all_passed = False
                    failing_result = verifier_module.VerificationResult(
                        False, "no_runtime_error", {"input": test_input}, case.error, "sandbox"
                    )
                    break
                vr = verifier_module.verify(problem.verifier_key, test_input, case.output)
                if not vr.passed:
                    all_passed = False
                    failing_result = vr
                    break

            complexity_info = None
            if all_passed:
                complexity_info = self._run_complexity_check(problem_id, code, problem.entry_point)
                if complexity_info is not None and not complexity_info["passed"]:
                    all_passed = False
                    failing_result = verifier_module.VerificationResult(
                        False, "time_complexity_bound", {"complexity_samples": complexity_info["samples"]},
                        complexity_info["message"], "empirical_complexity_probe",
                    )
                if complexity_info is not None:
                    yield {"event": "complexity_check", "attempt_number": attempt_num,
                           "complexity_check": complexity_info}

            record = AttemptRecord(
                attempt_number=attempt_num, code=code, trace=trace,
                stdout=sandbox_result.stdout, sandbox_error=None,
                verification_passed=all_passed,
                verification_message=failing_result.message if failing_result else "All checks passed",
                verification_method=failing_result.method if failing_result else "property_based",
                violated_constraint=failing_result.violated_constraint if failing_result else None,
                counterexample=failing_result.counterexample if failing_result else None,
                complexity_check=complexity_info,
            )
            attempts.append(record)
            yield {"event": "verification_result", "attempt_number": attempt_num,
                   "passed": all_passed, "message": record.verification_message,
                   "method": record.verification_method,
                   "violated_constraint": record.violated_constraint,
                   "counterexample": record.counterexample}
            yield {"event": "attempt_complete", "attempt_number": attempt_num, "passed": all_passed,
                   "attempt": record.__dict__}

            if all_passed:
                reward = _reward_for_attempts(attempt_num, True)
                if attempt_num > 1:
                    last_failure = next((a for a in reversed(attempts[:-1]) if not a.verification_passed), None)
                    if last_failure:
                        explanation = self.llm.explain_fix(
                            problem.description, last_failure.code,
                            last_failure.violated_constraint or "unknown", code,
                        )
                        self.skills.store(BugFixPair(
                            problem_id=problem_id,
                            bug_type=_bug_type_from_constraint(last_failure.violated_constraint),
                            buggy_code=last_failure.code,
                            violated_constraint=last_failure.violated_constraint or "unknown",
                            fix_explanation=explanation,
                            fixed_code=code,
                            reward=reward,
                        ))
                yield {
                    "event": "final_result", "success": True, "problem_id": problem_id,
                    "final_code": code, "attempts": [a.__dict__ for a in attempts],
                    "reward": reward, "elapsed_seconds": time.time() - start,
                    "skill_library_hits_used": skill_hits_used, "llm_provider": self.llm.provider_name,
                }
                return

            if attempt_num < self.max_attempts:
                yield {"event": "retrieving_fixes", "attempt_number": attempt_num}
            query_text = f"{record.violated_constraint} {record.verification_message}"
            few_shot = self.skills.build_few_shot_context(query_text, problem_id=problem_id, k=2)
            if few_shot:
                skill_hits_used += 1
            prior_failure = record

        yield {
            "event": "final_result", "success": False, "problem_id": problem_id,
            "final_code": None, "attempts": [a.__dict__ for a in attempts],
            "reward": 0.0, "elapsed_seconds": time.time() - start,
            "skill_library_hits_used": skill_hits_used, "llm_provider": self.llm.provider_name,
        }

    def solve(self, problem_id: str) -> SolveResult:
        """Non-streaming convenience wrapper around solve_stream(), for callers
        that just want the final result (the plain /solve endpoint,
        evaluate_baseline.py)."""
        final_event = None
        for event in self.solve_stream(problem_id):
            if event["event"] == "final_result":
                final_event = event

        return SolveResult(
            success=final_event["success"],
            problem_id=final_event["problem_id"],
            final_code=final_event["final_code"],
            attempts=[AttemptRecord(**a) for a in final_event["attempts"]],
            reward=final_event["reward"],
            elapsed_seconds=final_event["elapsed_seconds"],
            skill_library_hits_used=final_event["skill_library_hits_used"],
            llm_provider=final_event["llm_provider"],
        )

    def solve_custom_code(self, problem_id: str, candidate_code: str) -> dict:
        """
        Verify a user-PROVIDED piece of code (not LLM-generated) against a
        problem's checks. Used by the 'paste your own code' mode in the UI —
        lets a person see NEXUS's verification layer applied to their own
        solution, e.g. for learning/teaching use.
        """
        problem = get_problem(problem_id)
        test_inputs = problem.generate_test_inputs(n=10)
        sandbox_result = run_candidate(candidate_code, problem.entry_point, test_inputs)

        if not sandbox_result.success:
            return {"passed": False, "error": sandbox_result.error, "trace": [], "checks": []}

        checks = []
        for case, test_input in zip(sandbox_result.results, test_inputs):
            if case.error:
                checks.append({"input": test_input, "passed": False, "message": case.error})
                continue
            vr = verifier_module.verify(problem.verifier_key, test_input, case.output)
            checks.append({"input": test_input, "passed": vr.passed, "message": vr.message,
                            "method": vr.method, "counterexample": vr.counterexample})

        complexity_info = self._run_complexity_check(problem_id, candidate_code, problem.entry_point)

        return {
            "passed": all(c["passed"] for c in checks) and (complexity_info is None or complexity_info["passed"]),
            "checks": checks,
            "complexity_check": complexity_info,
            "trace": [{"line": t.line, "locals": t.locals} for t in sandbox_result.trace],
            "stdout": sandbox_result.stdout,
        }
