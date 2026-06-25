"""schemas.py — Pydantic models for API request/response validation."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ProblemSummary(BaseModel):
    id: str
    title: str
    difficulty: str


class SolveRequest(BaseModel):
    problem_id: str = Field(..., description="One of the problem IDs from GET /problems")

    @field_validator("problem_id")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or len(v) > 64:
            raise ValueError("problem_id must be non-empty and under 64 characters")
        return v


class CustomCodeRequest(BaseModel):
    problem_id: str
    code: str = Field(..., max_length=8000)

    @field_validator("code")
    @classmethod
    def non_trivial(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("code must not be empty")
        return v


class AttemptOut(BaseModel):
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


class SolveResponse(BaseModel):
    success: bool
    problem_id: str
    final_code: str | None
    attempts: list[AttemptOut]
    reward: float
    elapsed_seconds: float
    skill_library_hits_used: int
    llm_provider: str
    result_id: str


class CustomCodeCheckOut(BaseModel):
    input: list
    passed: bool
    message: str
    method: str | None = None
    counterexample: dict | None = None


class CustomCodeResponse(BaseModel):
    passed: bool
    checks: list[CustomCodeCheckOut] = []
    complexity_check: dict | None = None
    trace: list[dict] = []
    stdout: str = ""
    error: str | None = None


class StatsResponse(BaseModel):
    skill_library: dict
    llm_provider: str
    llm_is_live: bool


class HealthResponse(BaseModel):
    status: str
    version: str


class ExplainRequest(BaseModel):
    problem_id: str
    code: str = Field(..., max_length=8000)


class ExplainResponse(BaseModel):
    explanation: str
    cached: bool = False


class HintRequest(BaseModel):
    problem_id: str
    code: str = Field(..., max_length=8000)
    error_message: str | None = None


class HintResponse(BaseModel):
    hint: str
    cached: bool = False


class HistoryItem(BaseModel):
    id: str
    problem_id: str
    success: bool
    attempts_count: int
    elapsed_seconds: float
    reward: float
    llm_provider: str
    created_at: float


class ProblemAggregateStats(BaseModel):
    total_solves: int
    success_rate: float
    avg_attempts: float | None
    avg_elapsed_seconds: float | None


class HistoryStatsResponse(BaseModel):
    total_solves: int
    overall_success_rate: float
    per_problem: dict[str, ProblemAggregateStats]


class SharedResultResponse(BaseModel):
    id: str
    result: dict
