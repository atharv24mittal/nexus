"""routes.py — all NEXUS API endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

from app.config import settings
from app.core.agent import NexusAgent
from app.core.history import HistoryStore
from app.core.llm_client import NexusLLMClient
from app.core.problems import list_problems, get_problem
from app.core.response_cache import ResponseCache
from app.core.skill_library import SkillLibrary
from app.models.schemas import (
    ProblemSummary, SolveRequest, SolveResponse, AttemptOut,
    CustomCodeRequest, CustomCodeResponse, CustomCodeCheckOut,
    StatsResponse, HealthResponse, ExplainRequest, ExplainResponse,
    HintRequest, HintResponse, HistoryItem, HistoryStatsResponse,
    SharedResultResponse,
)
from app.security.rate_limit import rate_limit_solve, rate_limit_default

router = APIRouter()

# Singletons shared across requests within this process. SkillLibrary and
# HistoryStore are backed by SQLite on disk, so data persists across
# restarts (and across requests within a single Render instance) without
# needing a separate DB service.
_llm_client = NexusLLMClient()
_skill_library = SkillLibrary()
_history = HistoryStore()
_response_cache = ResponseCache()
_agent = NexusAgent(llm_client=_llm_client, skill_library=_skill_library,
                     max_attempts=settings.MAX_REPAIR_ATTEMPTS)


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", version="1.0.0")


@router.get("/problems", response_model=list[ProblemSummary])
def get_problems():
    # The problem bank is fixed for the lifetime of a deployment, so it's
    # safe to tell browsers/CDNs to cache this response — a real, free
    # latency win on every repeat visit.
    response = JSONResponse(content=[p for p in list_problems()])
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


def _solve_problem_or_404(problem_id: str):
    try:
        return get_problem(problem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown problem_id: {problem_id}")


def _persist_and_attach_id(result_dict: dict) -> dict:
    clean = {k: v for k, v in result_dict.items() if k != "event"}
    record_id = _history.store(
        problem_id=clean["problem_id"],
        success=clean["success"],
        attempts_count=len(clean["attempts"]),
        elapsed_seconds=clean["elapsed_seconds"],
        reward=clean["reward"],
        llm_provider=clean["llm_provider"],
        full_result=clean,
    )
    return {**result_dict, "result_id": record_id}


@router.post("/solve", response_model=SolveResponse, dependencies=[Depends(rate_limit_solve)])
def solve(body: SolveRequest):
    """
    Runs the full NEXUS loop: LLM generates code -> sandbox executes it ->
    verifier checks correctness (+ complexity where applicable) -> on
    failure, retrieve similar past fixes and repair -> repeat. Every run is
    persisted to history (see GET /history, GET /result/{id}).
    """
    _solve_problem_or_404(body.problem_id)

    result = _agent.solve(body.problem_id)
    result_dict = {
        "success": result.success,
        "problem_id": result.problem_id,
        "final_code": result.final_code,
        "attempts": [a.__dict__ for a in result.attempts],
        "reward": result.reward,
        "elapsed_seconds": result.elapsed_seconds,
        "skill_library_hits_used": result.skill_library_hits_used,
        "llm_provider": result.llm_provider,
    }
    persisted = _persist_and_attach_id(result_dict)
    return SolveResponse(
        success=result.success, problem_id=result.problem_id, final_code=result.final_code,
        attempts=[AttemptOut(**a.__dict__) for a in result.attempts],
        reward=result.reward, elapsed_seconds=result.elapsed_seconds,
        skill_library_hits_used=result.skill_library_hits_used, llm_provider=result.llm_provider,
        result_id=persisted["result_id"],
    )


@router.post("/solve/stream", dependencies=[Depends(rate_limit_solve)])
def solve_stream(body: SolveRequest):
    """
    Server-Sent Events version of /solve: emits each real event (generation
    started, code came back, sandbox ran, verification result, etc.) the
    MOMENT it happens, instead of returning one big JSON blob at the end.
    The frontend's LiveSolvePanel consumes this directly — what you see
    animate on screen is the actual server-side timeline, not a replay.
    """
    _solve_problem_or_404(body.problem_id)

    def event_stream():
        final_result_dict = None
        for event in _agent.solve_stream(body.problem_id):
            if event["event"] == "final_result":
                final_result_dict = event
                event = _persist_and_attach_id(event)
            yield f"data: {json.dumps(event)}\n\n"
        if final_result_dict is None:
            # Defensive: solve_stream() always yields a final_result, but if
            # that contract is ever violated, tell the client explicitly
            # rather than leaving the connection hanging silently.
            yield f"data: {json.dumps({'event': 'stream_error', 'message': 'No final result produced'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/check", response_model=CustomCodeResponse, dependencies=[Depends(rate_limit_default)])
def check_custom_code(body: CustomCodeRequest):
    """
    Verify a user-supplied (not LLM-generated) solution against a problem's
    checks. Useful as a teaching tool / 'why did my code fail' debugger,
    independent of the AI-generation loop.
    """
    _solve_problem_or_404(body.problem_id)

    result = _agent.solve_custom_code(body.problem_id, body.code)
    if "error" in result and result.get("error") and not result.get("checks"):
        return CustomCodeResponse(passed=False, error=result["error"])

    return CustomCodeResponse(
        passed=result["passed"],
        checks=[CustomCodeCheckOut(**c) for c in result["checks"]],
        complexity_check=result.get("complexity_check"),
        trace=result.get("trace", []),
        stdout=result.get("stdout", ""),
    )


@router.post("/explain", response_model=ExplainResponse, dependencies=[Depends(rate_limit_default)])
def explain_solution(body: ExplainRequest):
    """Plain-English walkthrough of a working (or any) solution."""
    problem = _solve_problem_or_404(body.problem_id)
    cache_key = _response_cache.make_key("explain", body.problem_id, body.code)
    cached = _response_cache.get(cache_key)
    if cached is not None:
        return ExplainResponse(explanation=cached, cached=True)

    explanation = _llm_client.explain_solution(problem.description, body.code)
    _response_cache.set(cache_key, explanation)
    return ExplainResponse(explanation=explanation, cached=False)


@router.post("/hint", response_model=HintResponse, dependencies=[Depends(rate_limit_default)])
def get_hint(body: HintRequest):
    """A nudge toward the fix, deliberately NOT the full solution."""
    problem = _solve_problem_or_404(body.problem_id)
    cache_key = _response_cache.make_key("hint", body.problem_id, body.code, body.error_message or "")
    cached = _response_cache.get(cache_key)
    if cached is not None:
        return HintResponse(hint=cached, cached=True)

    hint = _llm_client.generate_hint(problem.description, body.code, body.error_message)
    _response_cache.set(cache_key, hint)
    return HintResponse(hint=hint, cached=False)


@router.get("/history", response_model=list[HistoryItem])
def get_history(limit: int = 20):
    limit = max(1, min(limit, 100))  # clamp to a sane range regardless of what's requested
    return _history.list_recent(limit=limit)


@router.get("/history/stats", response_model=HistoryStatsResponse)
def get_history_stats():
    return _history.aggregate_stats()


@router.get("/result/{result_id}", response_model=SharedResultResponse)
def get_shared_result(result_id: str):
    full = _history.get_full_result(result_id)
    if full is None:
        raise HTTPException(status_code=404, detail="No result found with that ID")
    return SharedResultResponse(id=result_id, result=full)


@router.get("/stats", response_model=StatsResponse)
def stats():
    return StatsResponse(
        skill_library=_skill_library.stats(),
        llm_provider=_llm_client.provider_name,
        llm_is_live=_llm_client.is_live,
    )
