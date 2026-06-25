"""
llm_client.py
-------------
Wraps whichever LLM provider generates candidate code. Defaults to Groq
(free tier, OpenAI-compatible API, fast inference on open models like
Llama 3.3 70B) since this project is designed to run entirely on free
infrastructure. The client is provider-agnostic: swap GROQ_API_KEY for
OPENAI_API_KEY + a different base_url and model name in config.py and
nothing else in the codebase needs to change.

If no API key is configured at all, NexusLLMClient falls back to a tiny
deterministic template generator so the rest of the system (sandbox,
verifier, skill library) is still fully demoable and testable offline —
clearly labeled as a fallback, never silently pretending to be a real model.
"""

from __future__ import annotations

import re
from openai import OpenAI

from app.config import settings


_CODE_FENCE_RE = re.compile(r"```(?:python)?\s*([\s\S]*?)```")


def _strip_code_fences(text: str) -> str:
    match = _CODE_FENCE_RE.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()


class NexusLLMClient:
    def __init__(self):
        self._client = None
        self._provider_name = "offline-template-fallback"
        if settings.GROQ_API_KEY:
            self._client = OpenAI(api_key=settings.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
            self._provider_name = f"groq:{settings.LLM_MODEL}"
        elif settings.OPENAI_API_KEY:
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self._provider_name = f"openai:{settings.LLM_MODEL}"

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def is_live(self) -> bool:
        return self._client is not None

    def generate_code(self, prompt: str, temperature: float = 0.2) -> str:
        if self._client is None:
            return self._offline_fallback(prompt)

        response = self._client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": (
                    "You are a precise Python coding assistant. Respond with ONLY "
                    "a single Python function definition that satisfies the spec. "
                    "No explanations, no markdown prose — code only, optionally in "
                    "a ```python fenced block."
                )},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=600,
        )
        raw = response.choices[0].message.content or ""
        return _strip_code_fences(raw)

    def explain_fix(self, problem: str, buggy_code: str, violated_constraint: str, fixed_code: str) -> str:
        """Ask the LLM for a one-sentence explanation of what the fix changed (for the skill library)."""
        if self._client is None:
            return f"Adjusted logic to satisfy constraint: {violated_constraint}"
        prompt = (
            f"Problem: {problem}\n\nBuggy code:\n{buggy_code}\n\n"
            f"This violated the constraint: {violated_constraint}\n\n"
            f"Fixed code:\n{fixed_code}\n\n"
            "In ONE short sentence, explain what the bug was and how the fix addressed it."
        )
        response = self._client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=80,
        )
        return (response.choices[0].message.content or "").strip()

    def explain_solution(self, problem: str, code: str) -> str:
        """Plain-English walkthrough of a working solution, for the 'Explain this' UI button."""
        if self._client is None:
            return "No LLM provider configured — set GROQ_API_KEY to enable explanations."
        prompt = (
            f"Problem: {problem}\n\nSolution:\n{code}\n\n"
            "Explain how this solution works in 2-4 short sentences, plain English, "
            "as if to someone learning to code. Don't repeat the code verbatim, "
            "describe the approach and why it's correct."
        )
        response = self._client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )
        return (response.choices[0].message.content or "").strip()

    def generate_hint(self, problem: str, current_code: str, error_message: str | None) -> str:
        """A nudge toward the fix, NOT the full solution — for the 'Get a hint' UI button
        in custom-code mode. Explicitly prompted to withhold complete code."""
        if self._client is None:
            return "No LLM provider configured — set GROQ_API_KEY to enable hints."
        context = f"\n\nIt currently fails with: {error_message}" if error_message else ""
        prompt = (
            f"Problem: {problem}\n\nThe person's current attempt:\n{current_code}{context}\n\n"
            "Give ONE short, specific hint (1-2 sentences) about what's wrong or what to "
            "think about next. Do NOT write corrected code or the full solution — point "
            "at the issue, let them fix it themselves."
        )
        response = self._client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=120,
        )
        return (response.choices[0].message.content or "").strip()

    def _offline_fallback(self, prompt: str) -> str:
        """
        No API key configured. Returns a clearly-labeled placeholder so the
        rest of the pipeline (sandbox, verifier, skill library, UI) remains
        fully runnable and testable without any external dependency — this
        keeps `docker run` / `pytest` working out of the box for anyone
        cloning the repo before they've set up a Groq key.
        """
        return (
            "def _nexus_offline_placeholder(*args, **kwargs):\n"
            "    raise NotImplementedError(\n"
            "        'No LLM provider configured. Set GROQ_API_KEY (free at "
            "console.groq.com) or OPENAI_API_KEY in your .env file.'\n"
            "    )\n"
        )
