# File: src/llm/client.py
# Purpose: run_llm -- the ONE place an LLM call happens in the app.
#
# Every recipe / job routes through run_llm so the model is *data*, not a hardcoded
# string. Pass a ModelTarget (where the brain lives + which model) and you've chosen
# the brain: local Ollama, Ollama Turbo, or a per-user worker -- same call shape.
# This is the procedure-as-code thesis applied to the brain itself: swap the target,
# swap the model, no code change. (CLAUDE.md: full libs, no shortcuts -- httpx, the
# real Ollama /api/chat contract, structured outputs via `format`.)
#
# Self-contained on purpose: only httpx + stdlib, no src.core imports, so the same
# module is safe to lift into any in-tree caller without dragging the app with it.

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger("helix.llm")

DEFAULT_TIMEOUT = 180.0


@dataclass(frozen=True)
class ModelTarget:
    """Where a job's brain lives + which model runs -- the choosable part.

    Swap the target -> swap the brain. This is the "model field in the recipe":
      ModelTarget("gpt-oss:120b", "https://ollama.com", api_key=KEY)   # Turbo
      ModelTarget("deepseek-r1:14b", "http://ollama:11434")            # local
    api_key set  => Bearer auth (Turbo / remote worker).
    api_key empty => local Ollama, no auth.
    """
    model: str
    base_url: str = "http://ollama:11434"
    api_key: str = ""
    timeout: float = DEFAULT_TIMEOUT


@dataclass(frozen=True)
class LLMResult:
    text: str
    tokens: int            # prompt_eval_count + eval_count == LPCX brain-tokens (for billing/eval)
    model: str             # what actually answered -- for logging, A/B, credit accounting


async def run_llm(
    user: str,
    *,
    target: ModelTarget,
    system: str = "",
    json_mode: bool = False,
    schema: dict | None = None,
    client: httpx.AsyncClient | None = None,
) -> LLMResult:
    """One async chat call to an Ollama-compatible /api/chat endpoint.

    user    -- the user-turn prompt
    system  -- optional system prompt
    json_mode -- ask for free-form JSON (`format: "json"`)
    schema  -- a JSON Schema ENFORCED on the model (Ollama structured outputs);
               takes precedence over json_mode so the outbound shape can't drift
    client  -- pass an open AsyncClient to reuse a connection across calls; if
               omitted, a client is created and closed for this single call.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})

    body: dict = {"model": target.model, "messages": messages, "stream": False}
    if schema is not None:
        body["format"] = schema          # enforce the outbound Service Interface
    elif json_mode:
        body["format"] = "json"

    headers = {"Authorization": f"Bearer {target.api_key}"} if target.api_key else {}
    url = f"{target.base_url.rstrip('/')}/api/chat"

    owns = client is None
    if owns:
        client = httpx.AsyncClient(timeout=target.timeout)
    try:
        r = await client.post(url, json=body, headers=headers, timeout=target.timeout)
        r.raise_for_status()
        data = r.json()
    finally:
        if owns:
            await client.aclose()

    return LLMResult(
        text=data.get("message", {}).get("content", ""),
        tokens=int(data.get("eval_count", 0)) + int(data.get("prompt_eval_count", 0)),
        model=target.model,
    )
