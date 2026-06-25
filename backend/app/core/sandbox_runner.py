"""
sandbox_runner.py
------------------
Standalone, single-purpose script that executes a candidate Python function
inside a restricted environment. This file is ALWAYS invoked as a separate
OS subprocess (never imported into the FastAPI process). That separation is
the first layer of defense: even a successful escape only compromises a
short-lived, resource-capped child process with no inherited secrets.

Defense-in-depth layers implemented here:
  1. Process isolation       - runs as its own OS process (see core/sandbox.py)
  2. Resource limits         - CPU time, address space, no forking, no file writes
  3. Restricted builtins     - only a safe whitelist is exposed to candidate code
  4. Output size caps        - prevents memory-bomb via huge prints/return values
  5. Hard wall-clock timeout - enforced by the PARENT process via subprocess.run(timeout=...)

Protocol:
  stdin  : JSON  {"code": "<candidate source>", "entry_point": "fn_name",
                  "test_inputs": [[arg1, arg2, ...], ...]}
  stdout : JSON  {"success": bool, "results": [...], "trace": [...],
                  "stdout": "...", "error": "..." | null}

NOTE ON HONESTY (see SECURITY.md): this is a defense-in-depth sandbox
appropriate for a demo/hackathon-scale service with trusted-ish traffic
(rate-limited, no secrets in this process). It is NOT a substitute for
kernel-level isolation (gVisor / Firecracker / Docker+seccomp) and should
not be exposed to fully adversarial, high-volume, anonymous traffic in a
real production judge without that additional layer.
"""

import sys
import json
import io
import contextlib

try:
    import resource
    _HAS_RESOURCE_MODULE = True
except ImportError:
    # `resource` is POSIX-only (Linux/Mac) — it does not exist on Windows.
    # Without this guard, every single sandbox invocation crashed at import
    # time with ModuleNotFoundError before even reading stdin, which is
    # exactly the "ProcessTerminated(code=1)" failure on every test.
    #
    # The actual production deployment (Render's Docker container) runs
    # Linux, so the full CPU/memory resource-limit protection described
    # below IS active there. On Windows local dev, this specific layer
    # becomes a no-op — the wall-clock timeout enforced by the PARENT
    # process in sandbox.py (subprocess.run(..., timeout=...), which IS
    # cross-platform) is what backstops runaway code instead. See
    # docs/SECURITY.md for the honest platform-by-platform breakdown.
    _HAS_RESOURCE_MODULE = False


# ---- 1. Resource limits (POSIX only; no-op on Windows, see above) ---------
def _apply_resource_limits(cpu_seconds=4):
    if not _HAS_RESOURCE_MODULE:
        return
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
    except Exception:
        pass
    try:
        max_bytes = 256 * 1024 * 1024  # 256 MB address space
        resource.setrlimit(resource.RLIMIT_AS, (max_bytes, max_bytes))
    except Exception:
        pass
    try:
        resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))  # no forking/threading new procs
    except Exception:
        pass
    try:
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))  # no file writes
    except Exception:
        pass


# ---- 2. Restricted builtins whitelist --------------------------------------
_SAFE_BUILTINS = {
    "range": range, "len": len, "sorted": sorted, "list": list, "dict": dict,
    "set": set, "tuple": tuple, "str": str, "int": int, "float": float,
    "bool": bool, "min": min, "max": max, "sum": sum, "enumerate": enumerate,
    "zip": zip, "map": map, "filter": filter, "abs": abs, "round": round,
    "isinstance": isinstance, "type": type, "print": print, "reversed": reversed,
    "all": all, "any": any, "divmod": divmod, "pow": pow, "frozenset": frozenset,
    "ord": ord, "chr": chr, "repr": repr,
    "Exception": Exception, "ValueError": ValueError, "TypeError": TypeError,
    "IndexError": IndexError, "KeyError": KeyError, "StopIteration": StopIteration,
    "ZeroDivisionError": ZeroDivisionError, "RuntimeError": RuntimeError,
    "ArithmeticError": ArithmeticError, "AttributeError": AttributeError,
    "NotImplementedError": NotImplementedError,
}

_BLOCKED_NAMES = {
    "__import__", "open", "exec", "eval", "compile", "input", "globals",
    "locals", "vars", "dir", "getattr", "setattr", "delattr", "memoryview",
    "breakpoint", "help", "__build_class__",
}


def _build_safe_namespace():
    safe_builtins = dict(_SAFE_BUILTINS)
    for blocked in _BLOCKED_NAMES:
        safe_builtins.pop(blocked, None)
    return {"__builtins__": safe_builtins}


# ---- 3. Tracer: captures a line-by-line execution trace --------------------
class _Tracer:
    MAX_STEPS = 200
    MAX_VAR_REPR = 120

    def __init__(self):
        self.steps = []

    def trace_fn(self, frame, event, arg):
        if event == "line" and len(self.steps) < self.MAX_STEPS:
            local_vars = {}
            for k, v in frame.f_locals.items():
                if k.startswith("__"):
                    continue
                try:
                    r = repr(v)
                except Exception:
                    r = "<unrepr-able>"
                if len(r) > self.MAX_VAR_REPR:
                    r = r[: self.MAX_VAR_REPR] + "...(truncated)"
                local_vars[k] = r
            self.steps.append({"line": frame.f_lineno, "locals": local_vars})
        return self.trace_fn


def _run_one(code, entry_point, args, tracer):
    namespace = _build_safe_namespace()
    compiled = compile(code, "<candidate>", "exec")

    stdout_buf = io.StringIO()
    with contextlib.redirect_stdout(stdout_buf):
        exec(compiled, namespace)  # defines entry_point inside `namespace`
        fn = namespace.get(entry_point)
        if fn is None or not callable(fn):
            raise NameError(f"Function '{entry_point}' was not defined by the candidate code.")

        if tracer is not None:
            sys.settrace(tracer.trace_fn)
        try:
            result = fn(*args)
        finally:
            sys.settrace(None)

    out = stdout_buf.getvalue()
    if len(out) > 4000:
        out = out[:4000] + "...(truncated)"
    return result, out


def _run_benchmark(code, entry_point, args, repeats):
    """
    Compile and define the candidate EXACTLY ONCE, then call it `repeats`
    times in a tight loop, timing only the call loop itself. This isolates
    algorithmic cost from interpreter/compile/IPC overhead, which is what
    makes the empirical complexity probe (complexity.py) meaningful instead
    of just measuring JSON and subprocess startup noise.
    """
    import time

    namespace = _build_safe_namespace()
    compiled = compile(code, "<candidate>", "exec")
    stdout_buf = io.StringIO()
    with contextlib.redirect_stdout(stdout_buf):
        exec(compiled, namespace)
        fn = namespace.get(entry_point)
        if fn is None or not callable(fn):
            raise NameError(f"Function '{entry_point}' was not defined by the candidate code.")

        sample_output = fn(*args)  # warm-up + sanity call (also catches errors early)

        start = time.perf_counter()
        for _ in range(repeats):
            fn(*args)
        elapsed = time.perf_counter() - start

    try:
        sample_repr = repr(sample_output)
    except Exception:
        sample_repr = "<unrepr-able>"
    return elapsed, sample_repr


def main():
    raw = sys.stdin.read()
    response = {"success": False, "results": [], "trace": [], "stdout": "", "error": None}

    try:
        payload = json.loads(raw)
        mode = payload.get("mode", "test")
        code = payload["code"]
        entry_point = payload["entry_point"]

        if mode == "benchmark":
            cpu_limit = payload.get("cpu_limit_seconds", 6)
            _apply_resource_limits(cpu_seconds=cpu_limit)
            args = payload["args"]
            repeats = payload.get("repeats", 1)
            elapsed, sample_repr = _run_benchmark(code, entry_point, args, repeats)
            response["success"] = True
            response["elapsed_seconds"] = elapsed
            response["sample_output"] = sample_repr
        else:
            _apply_resource_limits()
            test_inputs = payload.get("test_inputs", [])
            results = []
            all_stdout = []
            trace_steps = []

            for i, args in enumerate(test_inputs):
                tracer = _Tracer() if i == 0 else None  # only trace the first case (cheap + representative)
                try:
                    result, out = _run_one(code, entry_point, args, tracer)
                    results.append({"input": args, "output": result, "error": None})
                    if out:
                        all_stdout.append(out)
                    if tracer:
                        trace_steps = tracer.steps
                except Exception as e:  # noqa: BLE001 - intentionally broad: candidate code is untrusted
                    results.append({"input": args, "output": None, "error": f"{type(e).__name__}: {e}"})

            response["success"] = True
            response["results"] = results
            response["trace"] = trace_steps
            response["stdout"] = "\n".join(all_stdout)

    except MemoryError:
        response["error"] = "MemoryLimitExceeded"
    except Exception as e:  # noqa: BLE001
        response["error"] = f"{type(e).__name__}: {e}"

    sys.stdout.write(json.dumps(response))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
