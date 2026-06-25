# NEXUS — Execution-Aware Code Intelligence Engine

NEXUS doesn't trust the code it generates. It runs every candidate in an
isolated sandbox, checks correctness with property-based tests and a real
z3 SMT solver, empirically verifies algorithmic complexity claims, and
repairs its own bugs using a memory of fixes it's seen before — streamed
live over Server-Sent Events, not faked for the demo.

Built as a portfolio-grade systems project: a self-correcting pipeline with
real engineering decisions at every layer. See
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for why each verification
technique was chosen for each problem type, and
[`docs/SECURITY.md`](docs/SECURITY.md) for an honest accounting of what the
sandbox does and doesn't protect against.

**Stack:** FastAPI + z3 + scikit-learn (backend) · React + Vite + Tailwind
v4 + Monaco + Framer Motion (frontend) · Groq for free LLM inference ·
123 backend tests · deployable entirely on free tiers (Render + Vercel).

---

## What it actually does

1. Pick a problem (14 in the bank — sorting, search, string/array
   algorithms, number theory) or paste your own solution.
2. **Generate mode**: an LLM writes a candidate solution. Every step —
   generation, sandbox execution, verification, repair — streams to the UI
   in real time over SSE as it actually happens on the server.
3. The candidate runs in a sandboxed subprocess with resource limits and a
   restricted builtins namespace — real isolation, not a `try/except`.
4. Verification picks the right tool for the problem: property-based
   invariants (is it sorted? a permutation?), a z3 SMT proof of existence
   (does a valid two-sum pair exist at all?), or an empirical complexity
   probe (does it *actually* run in O(log n), not just return the right
   answer slowly?).
5. On failure, NEXUS retrieves similar past bugs from memory (SQLite +
   TF-IDF) and feeds them into the next attempt. On success, the fix gets
   stored for next time.
6. Every run is persisted — browse history, see aggregate success rates
   per problem, or share a permalink to a specific result.

## Feature tour

**Core engine**
- 14 verified problems spanning sorting, search, two-sum (z3 SMT), string/array algorithms, and number theory
- Real-time SSE streaming of the full generate → execute → verify → repair loop
- Sandboxed execution: subprocess isolation, resource limits, restricted builtins (tested against real escape attempts)
- z3-based existence proofs where that's genuinely the right tool (not decoration)
- Empirical Big-O complexity probing (catches a disguised O(n) linear scan masquerading as O(log n) binary search)
- TF-IDF-based skill library — learns from its own past bugs
- AI-generated plain-English explanations of working solutions
- AI hints (not full answers) when you're stuck in custom-code mode
- Solve history persistence + aggregate stats (success rate, avg attempts per problem)
- Shareable permalinks to any past result
- In-memory response caching for explain/hint (saves latency + free-tier API calls)

**Security**
- Defense-in-depth sandbox: process isolation + resource limits + restricted builtins + wall-clock timeout
- Dependency-based rate limiting (10 solves/min, 60 checks/min per IP) with `X-RateLimit-*` headers
- Request body size cap (413 before parsing even starts)
- CSP, HSTS, X-Frame-Options, X-Content-Type-Options on every response
- Request-ID tracing on every response for debugging
- Configurable docs visibility for production hardening

**Performance**
- Gzip compression on responses over 1KB (SSE stays unbuffered)
- Browser-level caching (`Cache-Control`) on the static problem bank
- React Query caching with deliberate per-endpoint staleTime tuning
- Monaco editor lazy-loaded and code-split into its own chunk
- History/Stats panels lazy-loaded — never downloaded until opened
- localStorage-backed session continuity (remembers your last problem/mode/code)

**UX & design**
- Light/dark theme with zero flash-of-wrong-theme (synchronous pre-paint detection)
- Confetti + optional sound effects (synthesized via Web Audio, zero audio file bytes) on success
- Toast notifications for errors and rate limits
- Keyboard shortcuts (Ctrl/Cmd+Enter to solve, Esc to reset)
- Diff viewer between consecutive repair attempts
- Searchable/filterable problem picker
- Copy-to-clipboard and download-as-.py for any generated solution
- Subtle CSS-only animated background (zero per-frame JS cost)

## Quickstart (local)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

A `.env` file is already included with sensible defaults — just open it and
paste in a Groq key (free, ~30 seconds at https://console.groq.com):

```bash
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API docs.

Run the test suite (123 tests covering sandbox security, every verifier,
the complexity probe, rate limiting, history, streaming, and the API):

```bash
pytest -v
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`.

## Deployment (both free tier)

### Backend → Render

1. Push this repo to GitHub.
2. On [Render](https://render.com), **New +** → **Blueprint**, point it at
   your repo. It reads `backend/render.yaml` automatically.
3. Set `GROQ_API_KEY` in the Render dashboard (intentionally left out of
   `render.yaml` so it's never committed).
4. Update `CORS_ALLOWED_ORIGINS` to your Vercel URL once you have it.
5. Deploy. Health check is `/health`.

Render's free tier spins down after inactivity — first request after
idling takes ~30-50s to cold-start. That's Render, not NEXUS.

### Frontend → Vercel

1. New Project → import repo → **Root Directory** = `frontend`.
2. Add env var `VITE_API_URL` = your Render backend URL.
3. Deploy. `vercel.json` is already configured for Vite's build output.
4. Update `CORS_ALLOWED_ORIGINS` on the backend to your real Vercel URL and
   redeploy.

## Training / research (optional, separate from the deployed app)

`backend/training/nexus_rl_training.ipynb` is a Colab-ready notebook that
fine-tunes a small open code model using **GRPO with verifiable rewards
(RLVR)** — the same verification logic the backend uses, not a learned
reward model. See `backend/training/README.md` for the honesty checklist
before putting any resulting numbers on a resume.

## Project structure

```
nexus/
├── backend/
│   ├── app/
│   │   ├── core/          # sandbox, verifier, complexity probe, skill library,
│   │   │                  # history, response cache, agent (streaming), LLM client
│   │   ├── api/           # FastAPI routes (solve, solve/stream, check, explain,
│   │   │                  # hint, history, result, stats)
│   │   ├── models/        # Pydantic schemas
│   │   ├── security/      # dependency-based rate limiting
│   │   └── main.py        # app entrypoint - CORS, gzip, security headers
│   ├── tests/              # 123 tests
│   ├── training/            # Colab RL notebook + standalone evaluation scripts
│   ├── .env                 # ready to use - just add GROQ_API_KEY
│   ├── Dockerfile, render.yaml, requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # 25+ UI components
│   │   ├── hooks/          # SSE streaming, theme, sound, toast, keyboard shortcuts
│   │   ├── api/, lib/      # API client (incl. SSE consumption) + query cache config
│   ├── vercel.json
└── docs/
    ├── ARCHITECTURE.md      # why each verification technique was chosen
    └── SECURITY.md           # honest sandbox capabilities/limitations
```

## Extending it

Adding a new problem is two steps: a description + sample-input generator
in `core/problems.py`, and a verifier function in `core/verifier.py`. The
sandbox, agent loop, skill library, streaming, and UI need zero changes.

## License

MIT — see [`LICENSE`](LICENSE).

---

Built by [Atharv Mittal](https://github.com/atharv24mittal).
