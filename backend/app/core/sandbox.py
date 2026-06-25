"""
sandbox.py
----------
Public interface used by the rest of the app to execute untrusted candidate
code. Internally spawns `sandbox_runner.py` as an isolated subprocess and
enforces a hard wall-clock timeout as a backstop on top of the in-process
resource limits already applied inside the runner (see sandbox_runner.py
for the full defense-in-depth explanation).
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_RUNNER_PATH = Path(__file__).parent / "sandbox_runner.py"

# Hard wall-clock backstop. The runner's own RLIMIT_CPU is 4s of *CPU* time;
# this is wall-clock time, set higher to tolerate normal process startup
# overhead while still killing anything that hangs.
WALL_CLOCK_TIMEOUT_SECONDS = 8

MAX_CODE_LENGTH = 8000  # characters; prevents absurdly large payloads


@dataclass
class TraceStep:
    line: int
    locals: dict


@dataclass
class CaseResult:
    input: list
    output: Any
    error: str | None


@dataclass
class SandboxResult:
    success: bool
    results: list[CaseResult] = field(default_factory=list)
    trace: list[TraceStep] = field(default_factory=list)
    stdout: str = ""
    error: str | None = None
    timed_out: bool = False


class SandboxExecutionError(Exception):
    """Raised only for infrastructure failures, never for candidate-code bugs."""


def run_candidate(code: str, entry_point: str, test_inputs: list[list]) -> SandboxResult:
    """
    Execute `code` (which must define a function named `entry_point`) against
    each argument list in `test_inputs`, inside the isolated subprocess.

    This function NEVER executes candidate code in-process. A timeout or
    crash in the subprocess is reported as a normal SandboxResult, never
    raised into the caller as an unhandled exception from candidate code.
    """
    if len(code) > MAX_CODE_LENGTH:
        return SandboxResult(success=False, error="CodeTooLong")

    payload = json.dumps({
        "code": code,
        "entry_point": entry_point,
        "test_inputs": test_inputs,
    })

    try:
        proc = subprocess.run(
            [sys.executable, str(_RUNNER_PATH)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=WALL_CLOCK_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return SandboxResult(success=False, error="WallClockTimeoutExceeded", timed_out=True)
    except OSError as e:
        # Infrastructure failure (e.g. couldn't spawn the process at all).
        raise SandboxExecutionError(str(e)) from e

    if proc.returncode != 0:
        # Killed by a signal (e.g. -9 SIGKILL from RLIMIT_CPU/RLIMIT_AS),
        # or some other non-zero exit. Either way: report, don't crash.
        return SandboxResult(
            success=False,
            error=f"ProcessTerminated(code={proc.returncode})",
            timed_out=True,
        )

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return SandboxResult(success=False, error="MalformedSandboxOutput")

    results = [
        CaseResult(input=r["input"], output=r["output"], error=r["error"])
        for r in data.get("results", [])
    ]
    trace = [TraceStep(line=t["line"], locals=t["locals"]) for t in data.get("trace", [])]

    return SandboxResult(
        success=data.get("success", False),
        results=results,
        trace=trace,
        stdout=data.get("stdout", ""),
        error=data.get("error"),
    )


@dataclass
class BenchmarkResult:
    success: bool
    elapsed_seconds: float = 0.0
    sample_output: str = ""
    error: str | None = None


def benchmark_candidate(
    code: str, entry_point: str, args: list, repeats: int = 200,
    cpu_limit_seconds: int = 6, wall_clock_timeout: int = 15,
) -> BenchmarkResult:
    """
    Time `repeats` calls to the candidate, isolating algorithmic cost from
    subprocess/compile/IPC overhead (see sandbox_runner._run_benchmark).
    Used by complexity.py to empirically verify complexity-class claims.
    """
    if len(code) > MAX_CODE_LENGTH:
        return BenchmarkResult(success=False, error="CodeTooLong")

    payload = json.dumps({
        "mode": "benchmark",
        "code": code,
        "entry_point": entry_point,
        "args": args,
        "repeats": repeats,
        "cpu_limit_seconds": cpu_limit_seconds,
    })

    try:
        proc = subprocess.run(
            [sys.executable, str(_RUNNER_PATH)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=wall_clock_timeout,
        )
    except subprocess.TimeoutExpired:
        return BenchmarkResult(success=False, error="WallClockTimeoutExceeded")
    except OSError as e:
        raise SandboxExecutionError(str(e)) from e

    if proc.returncode != 0:
        return BenchmarkResult(success=False, error=f"ProcessTerminated(code={proc.returncode})")

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return BenchmarkResult(success=False, error="MalformedSandboxOutput")

    return BenchmarkResult(
        success=data.get("success", False),
        elapsed_seconds=data.get("elapsed_seconds", 0.0),
        sample_output=data.get("sample_output", ""),
        error=data.get("error"),
    )
