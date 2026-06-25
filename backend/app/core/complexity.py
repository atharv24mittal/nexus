"""
complexity.py
-------------
Some problems in the bank explicitly require a complexity bound (e.g.
binary_search must be O(log n), not a linear scan). Correctness checks
on a single input/output pair can't see that — a linear scan returns the
right ANSWER, just too slowly to satisfy the spec.

This module verifies the claim empirically: run the sandboxed candidate at
several geometrically-increasing input sizes, time it, and fit a log-log
regression to estimate the empirical complexity exponent. This is the same
technique used in real performance-regression test suites — not a proof
the way z3 is a proof, but a genuine measurement, reported as such.

Timing isolates pure algorithmic cost (see sandbox.benchmark_candidate):
the candidate is compiled once and called `repeats` times in a tight loop
INSIDE the sandboxed subprocess, so subprocess startup / JSON marshalling
overhead never enters the measurement.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from app.core.sandbox import benchmark_candidate


@dataclass
class ComplexityProbeResult:
    passed: bool
    estimated_exponent: float | None
    samples: list[dict]
    message: str


def _build_sorted_array(n: int, rng: random.Random) -> list[int]:
    return sorted(rng.sample(range(n * 4), n)) if n > 0 else []


def probe_binary_search_complexity(code: str, entry_point: str) -> ComplexityProbeResult:
    """
    Fits log(time) ~ k*log(n) across increasing n. A true O(log n) algorithm
    shows a near-flat curve (k well under 1.0); a linear scan grows close
    to k=1.0; an O(n^2) algorithm grows close to k=2.0.
    """
    rng = random.Random(7)
    sizes = [5_000, 50_000, 500_000]
    repeats = 300
    samples = []

    for n in sizes:
        arr = _build_sorted_array(n, rng)
        target = arr[rng.randint(0, n - 1)] if n > 0 else 0

        result = benchmark_candidate(code, entry_point, [arr, target], repeats=repeats)
        if not result.success:
            return ComplexityProbeResult(
                passed=False, estimated_exponent=None, samples=samples,
                message=f"Candidate failed to execute at n={n}: {result.error}",
            )
        samples.append({"n": n, "elapsed_seconds": result.elapsed_seconds,
                         "avg_call_seconds": result.elapsed_seconds / repeats})

    xs = [math.log(s["n"]) for s in samples]
    ys = [math.log(max(s["elapsed_seconds"], 1e-9)) for s in samples]
    mean_x, mean_y = sum(xs) / len(xs), sum(ys) / len(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs) or 1e-9
    k = num / den

    # O(log n) growth should be far flatter than O(n) across a 100x size
    # range. Threshold chosen with margin above the noise floor we measured
    # empirically for true binary search (k ~0.05-0.15) and well below
    # linear scan (k ~0.85-1.0).
    threshold = 0.5
    passed = k < threshold

    return ComplexityProbeResult(
        passed=passed,
        estimated_exponent=round(k, 3),
        samples=samples,
        message=(
            f"Estimated empirical growth exponent k≈{round(k, 3)} "
            f"(elapsed ~ n^k, fit across n={sizes}, {repeats} reps each). "
            + ("Consistent with O(log n)." if passed else
               "Growth too steep for O(log n) — looks closer to linear or worse.")
        ),
    )
