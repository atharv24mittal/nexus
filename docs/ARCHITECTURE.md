# Architecture

## The loop

```
 generate (LLM)  →  execute (sandbox)  →  verify (z3 / property-based)
       ▲                                          │
       │                                          │ fail
       └──────── repair, using retrieved past fixes ◄┘
                          │
                       success → store the (bug, fix) pattern
```

Every box in that diagram is a real module with its own tests — this isn't
a framework hiding the logic, it's a plain Python loop in `agent.py` that
you can read top to bottom.

## Component map

| Layer | File | What it does | Why this tool |
|---|---|---|---|
| Generation | `core/llm_client.py` | Calls Groq (free, OpenAI-compatible) for code completions, explanations, hints | Free tier, fast inference, swappable provider |
| Execution | `core/sandbox.py` + `sandbox_runner.py` | Runs candidate code in an isolated, resource-limited subprocess; captures a line-by-line execution trace | The only safe way to run untrusted code; see `SECURITY.md` |
| Verification (structural) | `core/verifier.py` | Property-based checks (sorted? permutation? matches ground truth?) | The right tool for checking a concrete input/output pair against a structural invariant |
| Verification (existence) | `core/verifier.py` (`verify_two_sum_smt`) | z3 SMT solver proves whether a valid index pair exists | The right tool when the question is "does a solution exist in this search space," not just "is this one output correct" |
| Verification (complexity) | `core/complexity.py` | Empirically benchmarks the candidate at increasing input sizes and fits a log-log regression to estimate the Big-O exponent | Correctness checks on one input/output pair can't see "ran in O(n) instead of O(log n)" — that's a claim about behavior *across* sizes |
| Memory | `core/skill_library.py` | TF-IDF + cosine similarity retrieval over a SQLite-backed store of past (bug, fix) pairs | Lightweight enough for Render's free tier; no GPU, no vector-DB service, no embedding API cost |
| History | `core/history.py` | Persists every solve, exposes aggregate stats and shareable result lookups | Append-mostly access pattern, deliberately separate from skill_library's similarity-search pattern |
| Response cache | `core/response_cache.py` | In-memory cache for /explain and /hint (never for /solve — generation must always be fresh) | Saves latency + free-tier API calls on repeated identical requests |
| Orchestration | `core/agent.py` | `solve_stream()` is a generator yielding real-time events; `solve()` is a thin non-streaming wrapper over it | One source of truth for the loop logic; streaming isn't a separate reimplementation |
| API | `api/routes.py`, `main.py` | FastAPI app: `/solve`, `/solve/stream` (SSE), `/check`, `/explain`, `/hint`, `/history`, `/result/{id}`, `/stats`, `/health` | — |
| Rate limiting | `security/rate_limit.py` | Dependency-based fixed-window limiter with `X-RateLimit-*` headers | Replaced an earlier slowapi-decorator version after it produced unexplained cross-platform 422s — see git history / SECURITY.md |

## Why streaming, not a single JSON response

The first version of NEXUS had the frontend pace through a client-side
replay of an already-complete `/solve` response — true data, but revealed
on a timer rather than as it happened. `/solve/stream` removes that
distinction entirely: `agent.solve_stream()` is a Python generator that
`yield`s an event the moment each real thing occurs (LLM call returned,
sandbox finished, verifier decided pass/fail), and the FastAPI endpoint
forwards each one over Server-Sent Events as it's yielded. What animates in
the browser **is** the server's timeline, not a reconstruction of it.

## Why two different verification strategies (and why that's the point)

A common mistake in "AI + formal methods" student projects is reaching for
z3 everywhere because it sounds impressive. NEXUS deliberately does NOT do
that:

- **Sorting, palindrome, balanced parens, max-subarray**: correctness for a
  *concrete* input/output pair is a directly-checkable predicate or a
  cheap ground-truth computation. Wrapping that in an SMT query adds
  ceremony, not power — the same logic Hypothesis/QuickCheck-style property
  testing uses is the textbook right tool here.
- **Two Sum**: this is fundamentally an *existence* question over a
  discrete search space — "does there exist a valid index pair?" That's
  exactly what SMT solvers exist for. When a candidate claims no solution
  exists, NEXUS asks z3 to either find a counterexample (proving the
  candidate wrong) or return UNSAT (proving it right) — a genuine
  correctness *proof*, not "we didn't find one in our test cases."
- **Binary search**: the spec requires O(log n) behavior, which isn't a
  property of any single input/output pair at all — it's a claim about
  growth across input sizes. Neither property-testing nor z3 fits; an
  empirical complexity probe (benchmark at increasing n, fit a log-log
  regression) is the textbook right tool, the same technique behind
  real performance-regression test suites.

Being able to explain *why* a given verification technique was chosen for
a given problem — not just that all three are "used somewhere" — is the
actual engineering judgment this project is meant to demonstrate.

## Why Groq instead of a self-hosted model in production

Self-hosting a code-gen model would need a GPU, which doesn't exist on
Render's free tier. Groq's hosted inference is free-tier-friendly, fast,
and OpenAI-API-compatible, so the production deployment stays $0/month.
The RL fine-tuning work (see `backend/training/`) is the genuinely
research-flavored part of the project — it's deliberately kept separate
from the production serving path, the same way a real ML team would keep
training infrastructure separate from a serving API.

## Why SQLite + TF-IDF instead of a vector DB + embeddings API

A "real" production version of the skill library would likely use a vector
database (Qdrant, Pinecone) and a proper sentence-transformer or embedding
API. For this project's scale (a curated problem bank, not millions of
documents) and budget ($0), TF-IDF + cosine similarity over SQLite gives
genuinely useful retrieval — short, code-shaped text like constraint names
and error messages is exactly the kind of input TF-IDF handles well — at
zero infrastructure cost and zero GPU requirement. This is documented as a
deliberate scoping decision, not a corner cut without realizing it.

## Frontend architecture notes

- **Code-splitting**: Monaco editor, framer-motion, and React Query are
  each their own chunk (`vite.config.js` `manualChunks`), and Monaco's
  *editor* component is additionally `React.lazy`-loaded so the initial
  bundle never blocks on it.
- **Caching**: `/problems` is fetched once and cached indefinitely (it's a
  fixed bank for the lifetime of a deployment); `/stats` is cached for 60s
  and explicitly invalidated after every successful solve, so the skill-
  library counter updates promptly without polling.
- **Genuinely live, not paced**: `LiveSolvePanel` is driven by
  `useSolveStream`, which consumes `/solve/stream`'s Server-Sent Events
  directly via `fetch`'s streaming body reader (not the native
  `EventSource` API, which can't send a POST body). Every state update
  corresponds to a real server-side event arriving over the wire — there is
  no client-side timer pacing a reconstruction of an already-finished
  response (an earlier version of this UI worked that way; see git history
  if curious what that looked like and why it was replaced).
- **State reset via remount, not effects**: `LiveSolvePanel` is keyed by
  `solveStream.sessionId` (incremented on each new solve) so React tears
  down and recreates its local view state — to scrub through attempts —
  automatically on every new run, rather than syncing it with a
  `useEffect`. Same idea in `App.jsx`: the default selected problem is a
  derived value (`selectedProblemId ?? problems?.[0]?.id`), not state set
  inside an effect once the query resolves.
