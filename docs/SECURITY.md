# Security

NEXUS executes LLM-generated and user-submitted Python code. That's the
single most security-sensitive thing this project does, so this document
is deliberately specific about what protects you, and equally specific
about what it does NOT protect you from.

## The sandbox (`backend/app/core/sandbox_runner.py` + `sandbox.py`)

Defense-in-depth, four layers:

1. **Process isolation** — candidate code never runs inside the FastAPI
   process. It runs in a freshly spawned subprocess with no inherited
   secrets (no API keys, no DB credentials — the subprocess only gets
   stdin/stdout).
2. **Resource limits** (Linux `resource.setrlimit`) — CPU time capped at
   4-6s, address space capped at 256MB, no forking, no file writes.
3. **Restricted builtins** — candidate code gets an explicit allow-list of
   builtins (arithmetic, collections, comparisons). `open`, `__import__`,
   `eval`, `exec`, `compile`, `input`, `os`, `sys`, and friends are all
   absent from its namespace — not blacklisted, *absent*, which is the
   stronger guarantee.
4. **Hard wall-clock timeout** in the parent process (`subprocess.run(...,
   timeout=8)`) as a backstop in case the in-process CPU limit doesn't fire
   for some reason (e.g. a pure-Python busy loop that's somehow IO-bound).

All four layers are tested in `backend/tests/test_sandbox_security.py`
against real escape attempts (`os.system`, `__import__('os')`, `open(...)`,
`eval`/`exec`, infinite loops, oversized payloads) — not just asserted in
prose.

## What this sandbox is NOT

This is a **defense-in-depth sandbox appropriate for a demo / portfolio /
hackathon-scale service**, not a hardened multi-tenant production judge.
Specifically:

- It is **not** kernel-level isolation. A sufficiently creative Python
  sandbox escape (e.g. via `__class__.__bases__` traversal trickery or a
  bug in restricted-builtins enforcement) is a known, hard, unsolved-in-
  general problem for pure-Python sandboxes. Real production code judges
  (Judge0, LeetCode, HackerEarth) use **gVisor, Firecracker microVMs, or
  Docker with seccomp profiles** for this reason — full OS/kernel-level
  isolation, not just a restricted namespace.
- It does **not** block network access at the OS level. Restricting
  `__import__` prevents the obvious `requests`/`socket` vectors from
  *inside this specific namespace*, but that's a namespace-level control,
  not a network-level one.
- The rate limiter (`slowapi`, 10 solves/minute/IP by default) and the
  8-second wall-clock cap exist specifically to bound the damage if any
  single layer above is bypassed — but they're mitigations, not proof.

**If you were taking this from a portfolio project to a real multi-tenant
production service handling adversarial, high-volume, anonymous traffic**,
the next engineering step would be replacing process-level isolation with
container/microVM-level isolation. That's a true statement to make in an
interview, not a hedge — and "I know exactly where the line is between
demo-grade and production-grade here" is a stronger answer than pretending
the sandbox is bulletproof.

## Other security measures

- **Input validation**: Pydantic models reject empty/oversized code (>8000
  chars) and malformed problem IDs before they ever reach the sandbox.
- **Request body size cap**: a transport-level middleware rejects bodies
  over 20KB with `413` before they're even parsed as JSON — defense-in-depth
  ahead of (not instead of) the per-field Pydantic validators.
- **Rate limiting**: a dependency-based fixed-window limiter (`/solve`:
  10/min, everything else: 60/min, per IP), with `X-RateLimit-Limit`,
  `X-RateLimit-Remaining`, `X-RateLimit-Reset`, and `Retry-After` headers on
  every response so a client can see exactly where it stands. This replaced
  an earlier slowapi-decorator-based implementation that worked fine on
  Linux but produced unexplained `422` responses specifically on Windows +
  Python 3.11 — rather than chase a third-party library's cross-platform
  signature-introspection behavior further, it was replaced with ~80 lines
  of explicit, fully-tested logic with zero magic.
- **CORS**: explicit allow-list of origins via `CORS_ALLOWED_ORIGINS`, not
  a wildcard.
- **Security headers** on every response: `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`,
  `Content-Security-Policy: default-src 'none'` (this API only ever returns
  JSON/SSE, never HTML, so the strictest possible CSP costs nothing),
  `Strict-Transport-Security` (meaningful once deployed behind HTTPS, which
  Render provides by default).
- **Request-ID tracing**: every response carries an `X-Request-ID` header
  (echoing the client's if supplied, otherwise generated) for debugging.
- **Configurable docs visibility**: `/docs`, `/redoc`, `/openapi.json` stay
  visible by default — a deliberate choice for a portfolio/demo API, where
  letting an interviewer poke at the schema directly is a feature, not a
  risk. Set `DISABLE_DOCS=true` if you ever deploy this somewhere that
  genuinely needs the schema hidden.
- **No secrets in the repo**: `.env` is gitignored; `.env.example` ships
  with empty values; `render.yaml` marks `GROQ_API_KEY` as `sync: false`
  so it must be set manually in the Render dashboard, never committed.

## Known dependency advisory

`npm audit` flags a moderate-severity advisory in `dompurify`, a *transitive*
dependency pulled in by `monaco-editor` (used to sanitize hover-tooltip
HTML inside the editor). We don't call `dompurify` directly, and the editor
only ever renders our own static hover content, not arbitrary user HTML —
so the practical exploitability here is low. Still listed here rather than
hidden, and worth re-running `npm audit` periodically as Monaco ships
updates.

## Reporting a concern

This is a portfolio/educational project, not a service handling real user
data. If you find a sandbox escape, open a GitHub issue — there's no bug
bounty, but it's genuinely useful feedback and will be credited.
