"""
main.py
-------
FastAPI application entrypoint. Wires up CORS, gzip compression, request-ID
tracing, a request body size cap, rate limiting (via plain dependencies —
see app/security/rate_limit.py), security headers, and the API router.

Run with:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config import settings

# Docs stay visible by default — for THIS project that's a deliberate
# choice, not an oversight: a portfolio/demo API is more useful when an
# interviewer or judge can poke at /docs directly. Set DISABLE_DOCS=true
# in your environment if you ever deploy this somewhere that genuinely
# needs the schema hidden.
_docs_url = None if settings.DISABLE_DOCS else "/docs"
_redoc_url = None if settings.DISABLE_DOCS else "/redoc"
_openapi_url = None if settings.DISABLE_DOCS else "/openapi.json"

app = FastAPI(
    title="NEXUS — Execution-Aware Code Intelligence Engine",
    description=(
        "Self-correcting code generation: generate -> sandboxed execute -> "
        "formally verify -> repair using a memory of past fixes."
    ),
    version="1.0.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset",
                     "X-Request-ID", "Retry-After"],
)

# Gzip compresses response bodies over the size threshold — a real, free
# latency/bandwidth win on the larger JSON payloads (/solve, /history).
# minimum_size is set above typical individual SSE event sizes so
# /solve/stream's real-time delivery isn't affected by compression buffering.
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def enforce_max_body_size(request: Request, call_next):
    """
    Defense-in-depth against oversized request bodies, ahead of (and
    independent from) the per-field max_length validators already on
    individual Pydantic models — this catches an oversized payload before
    it's even parsed as JSON, at the transport level.
    """
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.MAX_REQUEST_BODY_BYTES:
        return JSONResponse(
            status_code=413,
            content={"detail": f"Request body exceeds {settings.MAX_REQUEST_BODY_BYTES} byte limit"},
        )
    return await call_next(request)


@app.middleware("http")
async def add_request_id_and_security_headers(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    # This API only ever returns JSON/SSE, never renders HTML — a maximally
    # strict CSP costs nothing functionally and removes an entire class of
    # injection concerns if a response is ever embedded somewhere unexpected.
    if not request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
        response.headers["Content-Security-Policy"] = "default-src 'none'"
    # HSTS only has teeth over an actual HTTPS connection (which is what
    # Render serves in production); harmless to set unconditionally.
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


app.include_router(router)


@app.get("/")
def root():
    return {
        "name": "NEXUS API",
        "docs": _docs_url or "disabled",
        "health": "/health",
        "environment": settings.ENVIRONMENT,
    }
