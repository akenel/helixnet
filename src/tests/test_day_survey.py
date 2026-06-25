# Tests for the AI End-of-Day Survey recipe (src/services/day_survey.py).
# Pure-logic + the resilient draft path (brain mocked) — no DB needed.

import json

import pytest

from src.services import day_survey as ds


# --- the honest rule of thumb ----------------------------------------------------
def test_busy_level_thresholds():
    assert ds._busy_level(0) == "slow"
    assert ds._busy_level(7) == "slow"
    assert ds._busy_level(8) == "steady"
    assert ds._busy_level(24) == "steady"
    assert ds._busy_level(25) == "busy"


# --- the deterministic fallback (used when no brain is reachable) ----------------
def test_fallback_draft_quiet_day():
    out = ds._fallback_draft({"transaction_count": 0, "total_sales": 0.0, "top_sellers": []})
    assert out["busy_level"] == "slow"
    assert out["footfall_estimate"] == 0
    assert out["ai"] is False
    assert "no sales" in out["summary"].lower()


def test_fallback_draft_names_top_seller():
    out = ds._fallback_draft({
        "transaction_count": 12, "total_sales": 340.5,
        "top_sellers": [{"name": "Hemp Sana cream", "quantity": 4}],
    })
    assert out["busy_level"] == "steady"
    assert "Hemp Sana cream" in out["summary"]
    assert out["highlight"] == "Hemp Sana cream"


# --- compose_note: one human-readable line for Felix, never JSON -----------------
def test_compose_note_full():
    note = ds.compose_note("busy", 28, "sunny", "Good Monday, regulars in.")
    assert note == "Busy · ~28 customers\nWeather: sunny\nGood Monday, regulars in."


def test_compose_note_sparse_skips_empty_parts():
    assert ds.compose_note("", None, "", "Just a note.") == "Just a note."
    assert ds.compose_note("slow", None, "", "") == "Slow"
    assert ds.compose_note("", 0, "", "") == ""  # footfall 0 is not "approx N customers"


# --- draft_day_survey: zero-sales short-circuits the brain (no wasted call) -------
@pytest.mark.asyncio
async def test_draft_skips_brain_on_empty_day(monkeypatch):
    async def fake_facts(db, user_id, target_date=None):
        return {"transaction_count": 0, "total_sales": 0.0, "top_sellers": [],
                "weekday": "Monday", "items_sold": 0, "cash_sales": 0.0, "card_sales": 0.0,
                "first_sale": None, "last_sale": None, "busiest_hour": None}

    called = {"n": 0}

    async def boom(*a, **k):
        called["n"] += 1
        raise AssertionError("brain must not be called on an empty day")

    monkeypatch.setattr(ds, "gather_day_facts", fake_facts)
    monkeypatch.setattr(ds, "run_llm", boom)
    out = await ds.draft_day_survey(db=None, user_id="u")
    assert out["ai"] is False
    assert out["facts"]["transaction_count"] == 0
    assert called["n"] == 0


# --- draft_day_survey: uses the brain when there are sales -----------------------
@pytest.mark.asyncio
async def test_draft_uses_brain_when_sales(monkeypatch):
    facts = {"transaction_count": 14, "total_sales": 412.0, "cash_sales": 300.0,
             "card_sales": 112.0, "items_sold": 20, "weekday": "Saturday",
             "top_sellers": [{"name": "Gizeh papers", "quantity": 6}],
             "first_sale": "09:10", "last_sale": "18:40", "busiest_hour": "17:00–18:00"}

    async def fake_facts(db, user_id, target_date=None):
        return facts

    class FakeRes:
        text = json.dumps({"busy_level": "busy", "footfall_estimate": 30,
                           "summary": "Solid Saturday, papers flew off the shelf.",
                           "highlight": "Gizeh papers"})

    async def fake_run_llm(user, **k):
        return FakeRes()

    monkeypatch.setattr(ds, "gather_day_facts", fake_facts)
    monkeypatch.setattr(ds, "run_llm", fake_run_llm)
    out = await ds.draft_day_survey(db=None, user_id="u")
    assert out["ai"] is True
    assert out["busy_level"] == "busy"
    assert out["footfall_estimate"] == 30
    assert "Saturday" in out["summary"]


# --- draft_day_survey: brain failure degrades to the honest fallback -------------
@pytest.mark.asyncio
async def test_draft_falls_back_on_brain_error(monkeypatch):
    facts = {"transaction_count": 9, "total_sales": 88.0, "cash_sales": 88.0,
             "card_sales": 0.0, "items_sold": 9, "weekday": "Tuesday",
             "top_sellers": [{"name": "Lighter", "quantity": 3}],
             "first_sale": "10:00", "last_sale": "16:00", "busiest_hour": "12:00–13:00"}

    async def fake_facts(db, user_id, target_date=None):
        return facts

    async def boom(*a, **k):
        raise RuntimeError("brain down")

    monkeypatch.setattr(ds, "gather_day_facts", fake_facts)
    monkeypatch.setattr(ds, "run_llm", boom)
    out = await ds.draft_day_survey(db=None, user_id="u")
    assert out["ai"] is False                 # degraded, but still usable
    assert out["busy_level"] == "steady"      # 9 sales
    assert out["summary"]
