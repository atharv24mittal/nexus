"""
evaluate_baseline.py
---------------------
Run NEXUS's full agent loop (generation -> sandbox -> verify -> repair)
against every problem in the bank and print real pass-rate numbers —
with and without the self-repair loop, and with and without the skill
library — so you have honest ablation numbers for your README/resume
instead of invented ones.

Usage:
    cd backend
    python -m training.evaluate_baseline --runs-per-problem 5

Requires GROQ_API_KEY (or OPENAI_API_KEY) set in your environment / .env,
since this exercises the real LLM-generation path, not the offline fallback.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.agent import NexusAgent
from app.core.llm_client import NexusLLMClient
from app.core.problems import PROBLEMS
from app.core.skill_library import SkillLibrary


def run_eval(runs_per_problem: int, max_attempts: int, fresh_skill_library: bool):
    llm = NexusLLMClient()
    if not llm.is_live:
        print("ERROR: no LLM provider configured. Set GROQ_API_KEY or OPENAI_API_KEY.")
        sys.exit(1)
    print(f"LLM provider: {llm.provider_name}\n")

    db_path = Path("data/eval_skill_library.db")
    if fresh_skill_library and db_path.exists():
        db_path.unlink()
    skills = SkillLibrary(db_path=db_path)
    agent = NexusAgent(llm_client=llm, skill_library=skills, max_attempts=max_attempts)

    results = {}
    overall_first_try = 0
    overall_eventual = 0
    overall_total = 0
    t0 = time.time()

    for problem_id in PROBLEMS:
        first_try_pass = 0
        eventual_pass = 0
        attempts_used = []

        for run in range(runs_per_problem):
            solve_result = agent.solve(problem_id)
            if solve_result.success:
                eventual_pass += 1
                attempts_used.append(len(solve_result.attempts))
                if len(solve_result.attempts) == 1:
                    first_try_pass += 1

        results[problem_id] = {
            "first_try_pass_rate": first_try_pass / runs_per_problem,
            "eventual_pass_rate": eventual_pass / runs_per_problem,
            "avg_attempts_when_solved": (sum(attempts_used) / len(attempts_used)) if attempts_used else None,
        }
        overall_first_try += first_try_pass
        overall_eventual += eventual_pass
        overall_total += runs_per_problem

        print(f"{problem_id:20s}  first-try: {first_try_pass}/{runs_per_problem}   "
              f"eventual (<= {max_attempts} attempts): {eventual_pass}/{runs_per_problem}")

    elapsed = time.time() - t0
    print()
    print(f"OVERALL first-try pass rate: {overall_first_try}/{overall_total} "
          f"= {overall_first_try/overall_total:.1%}")
    print(f"OVERALL eventual pass rate (self-repair loop): {overall_eventual}/{overall_total} "
          f"= {overall_eventual/overall_total:.1%}")
    print(f"Skill library size after run: {skills.count()} stored patterns")
    print(f"Total wall-clock time: {elapsed:.1f}s")
    print()
    print(">>> These are the real numbers from this run. Use them as-is in your README. <<<")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-per-problem", type=int, default=5)
    parser.add_argument("--max-attempts", type=int, default=5)
    parser.add_argument("--fresh-skill-library", action="store_true",
                         help="Wipe the skill library before this run, to measure the repair loop in isolation.")
    args = parser.parse_args()
    run_eval(args.runs_per_problem, args.max_attempts, args.fresh_skill_library)
