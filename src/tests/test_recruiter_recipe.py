# Tests for the recruiter-reply recipe (#120): shape, prompt formatting, menu presence,
# and a run_recipe smoke with a monkeypatched brain (no real LLM call).
import pytest

from src.compute import recipes as rc


def test_recruiter_recipe_shape():
    r = rc.RECIPES["recruiter-reply"]
    assert r["category"] == "identity"
    assert r["output"] == "markdown"
    assert r["est_credits"] == 2
    names = [i["name"] for i in r["inputs"]]
    assert names == ["email", "cv", "stance", "reply_lang"]
    lang = next(i for i in r["inputs"] if i["name"] == "reply_lang")
    assert lang["type"] == "select" and lang["default"] == "Auto"
    assert "Italian" in lang["options"]


def test_recruiter_prompt_formats_with_all_placeholders():
    # .format must succeed with exactly the keys run_recipe provides (inputs + portrait) -- no
    # stray braces, no missing keys.
    r = rc.RECIPES["recruiter-reply"]
    ctx = {"email": "EMAIL", "cv": "CVTEXT", "stance": "STANCE", "reply_lang": "English", "portrait": "PORT"}
    out = r["prompt"].format(**ctx)
    for piece in ("EMAIL", "CVTEXT", "STANCE", "English", "PORT"):
        assert piece in out
    assert "CV slant" in out and "Covers" in out


def test_recruiter_in_menu():
    assert "recruiter-reply" in [m["slug"] for m in rc.menu()]


@pytest.mark.asyncio
async def test_run_recipe_recruiter_smoke(monkeypatch):
    captured = {}

    async def fake_brain(system, prompt, **kw):
        captured["system"] = system
        captured["prompt"] = prompt
        return ("Dear Katarzyna,\n\nHappy to confirm...\n\n"
                "## ✂️ CV slant for this role\n- SAP Basis\n\n## Covers\nexclusivity, rate, CV")

    monkeypatch.setattr(rc, "_brain_chat", fake_brain)
    res = await rc.run_recipe(
        "recruiter-reply",
        {"email": "Hi, please send your CV. Rate 90/hr. Exclusive representation?",
         "cv": "15 years SAP PI/PO + Basis integration", "stance": "fine with the rate",
         "reply_lang": "English"})

    assert res["slug"] == "recruiter-reply"
    assert res["output_type"] == "markdown"
    assert "CV slant" in res["result"]
    # the recruiter email + the candidate's CV were substituted into the prompt the brain saw
    assert "90/hr" in captured["prompt"] and "SAP PI/PO" in captured["prompt"]
    # the honest-but-confident persona is in force
    assert "honest" in captured["system"].lower() and "invent" in captured["system"].lower()
