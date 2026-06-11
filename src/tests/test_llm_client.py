# Tests for src.llm -- the single LLM entry point.
# Pure/mocked: no network, no real model. Locks the /api/chat contract so a future
# refactor can't silently change the request shape or break per-job model selection.

from unittest.mock import MagicMock, patch

import pytest

from src.llm import ModelTarget, run_llm, turbo_or_local

_ENV_KEYS = ("BH_OLLAMA_KEY", "OLLAMA_TURBO_URL", "OLLAMA_URL",
            "OLLAMA_MODEL", "LPCX_BIO_MODEL")


@pytest.fixture
def clean_env(monkeypatch):
    for k in _ENV_KEYS:
        monkeypatch.delenv(k, raising=False)
    return monkeypatch


# --- turbo_or_local: backend selection by presence of a Turbo key ----------------

def test_local_backend_when_no_key(clean_env):
    t = turbo_or_local("gpt-oss:120b", "tinyllama:latest")
    assert t.base_url == "http://ollama:11434"
    assert t.model == "tinyllama:latest"
    assert t.api_key == ""          # local => no auth


def test_turbo_backend_when_key_set(clean_env):
    clean_env.setenv("BH_OLLAMA_KEY", "sk-test")
    t = turbo_or_local("gpt-oss:120b", "tinyllama:latest")
    assert t.base_url == "https://ollama.com"
    assert t.model == "gpt-oss:120b"
    assert t.api_key == "sk-test"   # Turbo => Bearer


def test_per_job_override_wins_on_active_backend(clean_env):
    clean_env.setenv("BH_OLLAMA_KEY", "sk-test")
    # explicit model passed for both backends => the chosen brain regardless of default
    t = turbo_or_local("deepseek-r1:14b", "deepseek-r1:14b")
    assert t.model == "deepseek-r1:14b"
    assert t.base_url == "https://ollama.com"


def test_model_target_defaults_and_frozen():
    d = ModelTarget("m")
    assert d.base_url == "http://ollama:11434"
    assert d.timeout == 180.0
    with pytest.raises(Exception):
        d.model = "x"               # frozen dataclass


# --- run_llm: the /api/chat request contract + response parsing ------------------

class _FakeClient:
    """Captures the outbound request and returns a canned Ollama chat response."""
    captured: dict = {}

    def __init__(self, *a, **k):
        pass

    async def post(self, url, json=None, headers=None, timeout=None):
        _FakeClient.captured = {"url": url, "body": json, "headers": headers}
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json = MagicMock(return_value={
            "message": {"content": "hello world"},
            "prompt_eval_count": 12, "eval_count": 30,
        })
        return resp

    async def aclose(self):
        pass


@pytest.mark.asyncio
async def test_schema_takes_precedence_and_auth_and_tokens():
    schema = {"type": "object", "properties": {"bio": {"type": "string"}}}
    target = ModelTarget("deepseek-r1:14b", "https://ollama.com", api_key="sk-x")
    with patch("src.llm.client.httpx.AsyncClient", _FakeClient):
        res = await run_llm("u-prompt", target=target, system="s-prompt",
                            json_mode=True, schema=schema)
    b = _FakeClient.captured["body"]
    assert _FakeClient.captured["url"] == "https://ollama.com/api/chat"
    assert b["model"] == "deepseek-r1:14b"
    assert b["stream"] is False
    assert b["format"] == schema                       # schema wins over json_mode
    assert b["messages"] == [
        {"role": "system", "content": "s-prompt"},
        {"role": "user", "content": "u-prompt"},
    ]
    assert _FakeClient.captured["headers"] == {"Authorization": "Bearer sk-x"}
    assert res.text == "hello world"
    assert res.tokens == 42                             # 12 + 30 == brain-tokens
    assert res.model == "deepseek-r1:14b"


@pytest.mark.asyncio
async def test_local_no_auth_json_mode_only_user_turn():
    target = ModelTarget("tinyllama:latest")           # local default, no key
    with patch("src.llm.client.httpx.AsyncClient", _FakeClient):
        await run_llm("p", target=target, json_mode=True)
    b = _FakeClient.captured["body"]
    assert _FakeClient.captured["url"] == "http://ollama:11434/api/chat"
    assert b["format"] == "json"                        # json_mode, no schema
    assert b["messages"] == [{"role": "user", "content": "p"}]   # no system turn
    assert _FakeClient.captured["headers"] == {}        # local => no auth


# --- per-job model: the recipe runner threads "model" through to the brain ---------

@pytest.mark.asyncio
async def test_recipe_threads_per_job_model(monkeypatch):
    """The 'decide' recipe names its own brain as DATA (Turbo gpt-oss:120b + a local-dev
    fallback deepseek-r1:14b); a default recipe passes model=None. Both reach the brain
    unchanged -- the BYO-brain contract, end to end through run_recipe."""
    import src.compute.recipes as rc

    seen = []

    async def fake_brain(system, user, json_mode=False, schema=None, model=None, model_local=None):
        seen.append((model, model_local))
        return '{"x":1}' if json_mode else "## The Call\nDo it."

    monkeypatch.setattr(rc, "_brain_chat", fake_brain)

    # 'decide' carries a per-job brain (both Turbo + local) -> must reach the brain unchanged
    out = await rc.run_recipe("decide", {"decision": "take the contract or not"})
    assert seen[-1] == ("gpt-oss:120b", "deepseek-r1:14b")
    assert out["output_type"] == "markdown"

    # a recipe with no "model" key -> default brain (None, None)
    await rc.run_recipe("music-playlist", {"vibe": "sunrise drive", "count": "10"})
    assert seen[-1] == (None, None)


def test_menu_does_not_leak_model():
    """menu() is the public surface -- it must not expose the internal brain choice."""
    import src.compute.recipes as rc
    assert all("model" not in entry for entry in rc.menu())


# --- reasoning-model <think> stripping --------------------------------------------

def test_strip_think_cases():
    from src.compute.recipes import _strip_think
    # well-formed block removed, answer kept
    assert _strip_think("<think>weighing it</think>## The Call\nDo it.") == "## The Call\nDo it."
    # multiline + case-insensitive
    assert _strip_think("<THINK>\na\nb\n</THINK>\n\nAnswer") == "Answer"
    # lone closing tag (opener lost) -> keep what's after it
    assert _strip_think("reasoning...\n</think>\nFinal") == "Final"
    # truncated reasoning, never closed -> nothing usable
    assert _strip_think("<think>still thinking") == ""
    # ordinary output untouched
    assert _strip_think("just a normal answer") == "just a normal answer"
    assert _strip_think("") == ""


@pytest.mark.asyncio
async def test_run_recipe_strips_think(monkeypatch):
    """A reasoning model's <think> block must never reach the recipe result."""
    import src.compute.recipes as rc

    async def fake_brain(system, user, json_mode=False, schema=None, model=None, model_local=None):
        return "<think>weigh contract vs no contract, money vs risk</think>## The Call\nTake it."

    monkeypatch.setattr(rc, "_brain_chat", fake_brain)
    out = await rc.run_recipe("decide", {"decision": "take the contract?"})
    assert "<think>" not in out["result"] and "</think>" not in out["result"]
    assert out["result"] == "## The Call\nTake it."


# --- retry-with-backoff on transient errors (the Turbo-throttle single-point-of-failure) ----

@pytest.mark.asyncio
async def test_run_llm_retries_429_then_succeeds(monkeypatch):
    import httpx
    from src.llm import client as llm
    monkeypatch.setattr(llm.asyncio, "sleep", _no_sleep)   # don't actually wait in tests
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429, headers={"retry-after": "0"}, text="slow down")
        return httpx.Response(200, json={"message": {"content": "ok"}, "eval_count": 1, "prompt_eval_count": 1})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as c:
        res = await llm.run_llm("hi", target=llm.ModelTarget("m", "http://x"), client=c)
    assert res.text == "ok"
    assert calls["n"] == 3                 # two 429s rode out, third succeeded


@pytest.mark.asyncio
async def test_run_llm_raises_after_exhausting_retries(monkeypatch):
    import httpx
    from src.llm import client as llm
    monkeypatch.setattr(llm.asyncio, "sleep", _no_sleep)

    def handler(request):
        return httpx.Response(503, text="down")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as c:
        with pytest.raises(httpx.HTTPStatusError):
            await llm.run_llm("hi", target=llm.ModelTarget("m", "http://x"), client=c)


async def _no_sleep(*a, **k):
    return None
