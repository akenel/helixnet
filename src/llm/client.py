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

import asyncio
import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger("helix.llm")

DEFAULT_TIMEOUT = 180.0

# Transient failures worth retrying: rate-limit + the 5xx family + network blips. A throttled
# Turbo (429) was the single point of failure we hit in practice -- ride it out with bounded backoff
# instead of failing the whole call. NOT retried: 4xx other than 429 (e.g. 404 wrong-model, which
# the caller handles by falling back to the house brain).
_RETRY_STATUSES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 2                       # 3 attempts total
_BACKOFF_BASE = 0.6                    # seconds: 0.6, 1.2 (short -- these calls are interactive)


def _retry_delay(resp: "httpx.Response | None", attempt: int) -> float:
    """Honour a Retry-After header if the server sent one, else exponential backoff (capped)."""
    if resp is not None:
        ra = resp.headers.get("retry-after")
        if ra:
            try:
                return max(0.0, min(float(ra), 10.0))   # cap so we never hang an interactive turn
            except ValueError:
                pass
    return _BACKOFF_BASE * (2 ** attempt)


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
        data = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                r = await client.post(url, json=body, headers=headers, timeout=target.timeout)
            except (httpx.TimeoutException, httpx.TransportError) as e:
                if attempt < _MAX_RETRIES:
                    delay = _retry_delay(None, attempt)
                    logger.warning("brain %s transient %s; retry %d/%d in %.1fs",
                                   target.model, type(e).__name__, attempt + 1, _MAX_RETRIES, delay)
                    await asyncio.sleep(delay)
                    continue
                raise
            if r.status_code in _RETRY_STATUSES and attempt < _MAX_RETRIES:
                delay = _retry_delay(r, attempt)
                logger.warning("brain %s transient %s; retry %d/%d in %.1fs",
                               target.model, r.status_code, attempt + 1, _MAX_RETRIES, delay)
                await asyncio.sleep(delay)
                continue
            r.raise_for_status()      # raises on 4xx (incl. final 429) / unretried 5xx
            data = r.json()
            break
    finally:
        if owns:
            await client.aclose()

    return LLMResult(
        text=data.get("message", {}).get("content", ""),
        tokens=int(data.get("eval_count", 0)) + int(data.get("prompt_eval_count", 0)),
        model=target.model,
    )
