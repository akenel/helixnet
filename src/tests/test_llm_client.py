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
