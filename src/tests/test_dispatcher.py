# Tests for src.compute.dispatcher -- the HANDOFF. Pure/mocked: no network, no real brain.
# Locks the iron rule: the dispatcher may ONLY route to masters on the board it was handed.
# An invented master is dropped; the canonical name + House come from the board, never the model.

import json
from unittest.mock import patch

import pytest

from src.compute import dispatcher as dsp


ROSTER = [
    {"name": "Albert Einstein", "house": "The Lyceum", "tagline": "relativity, thought experiments", "ref": "kc-1"},
    {"name": "Leonardo da Vinci", "house": "The Atelier", "tagline": "painter, engineer, anatomist", "ref": "kc-2"},
    {"name": "Marie Curie", "house": "The Lyceum", "tagline": "radioactivity, two Nobels", "ref": "kc-3"},
]


def _brain_returning(payload: dict):
    async def fake_brain(system, user, json_mode=False, **kw):
        return "<think>picking</think>" + json.dumps(payload)
    return fake_brain


# --- build_work_package: the inbound Service Interface -------------------------------------

def test_build_work_package_shape_and_defaults():
    wp = dsp.build_work_package("  why bother?  ", ref_id="abc")
    assert wp["ref_id"] == "abc"
    assert wp["question_body"] == "why bother?"          # trimmed
    assert wp["source"] == "guest"
    assert wp["question_type"] == "auto"                 # default
    assert wp["language"] == "auto"
    assert wp["priority"] == "normal"
    assert wp["attachments"] == []


def test_build_work_package_normalizes_bad_enums():
    wp = dsp.build_work_package("q", ref_id="1", question_type="nonsense",
                                priority="URGENT", language="IT", attachments=["cv.pdf"])
    assert wp["question_type"] == "auto"                 # bad type -> auto
    assert wp["priority"] == "normal"                    # bad priority -> normal
    assert wp["language"] == "it"                        # lowercased
    assert wp["attachments"] == ["cv.pdf"]


def test_build_work_package_keeps_valid_type():
    wp = dsp.build_work_package("how do I start?", ref_id="1", question_type="how")
    assert wp["question_type"] == "how"


# --- _match_master: the anti-hallucination gate --------------------------------------------

def test_match_master_exact_and_lastname_and_invented():
    index = {dsp._norm(lg["name"]): lg for lg in ROSTER}
    assert dsp._match_master("Albert Einstein", index)["ref"] == "kc-1"   # exact
    assert dsp._match_master("Einstein", index)["ref"] == "kc-1"          # last-name containment
    assert dsp._match_master("Gandalf the Grey", index) is None           # invented -> dropped
    assert dsp._match_master("", index) is None


def test_match_master_short_token_does_not_falsely_match():
    index = {dsp._norm(lg["name"]): lg for lg in ROSTER}
    # a 3-char garbage token must not containment-match a real long name
    assert dsp._match_master("da", index) is None


# --- dispatch: the happy path --------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatch_picks_two_validates_and_uses_board_house():
    payload = {
        "question_type": "why",
        "next_action": "answered",
        "masters": [
            {"name": "Albert Einstein", "house": "WRONG HOUSE", "why_this_one": "physics",
             "answer": "Imagination matters.", "rationale": "fits the why"},
            {"name": "Leonardo da Vinci", "why_this_one": "curiosity",
             "answer": "Observe nature.", "rationale": "the maker angle"},
        ],
    }
    wp = dsp.build_work_package("why do we dream?", ref_id="r1", question_type="auto")
    with patch.object(dsp, "_brain_chat", _brain_returning(payload)):
        out = await dsp.dispatch(wp, ROSTER, language="", timestamp="2026-06-11T00:00:00Z")

    assert out["ref_id"] == "r1"
    assert out["question_type"] == "why"
    assert out["next_action"] == "answered"
    assert out["language"] == "en"                       # auto -> en
    assert out["timestamp"] == "2026-06-11T00:00:00Z"
    assert out["events_triggered"] == []
    names = [m["name"] for m in out["masters"]]
    assert names == ["Albert Einstein", "Leonardo da Vinci"]
    # House comes from the BOARD, never the model's spelling
    assert out["masters"][0]["house"] == "The Lyceum"
    assert out["masters"][0]["ref"] == "kc-1"
    assert out["masters"][0]["answer"] == "Imagination matters."


@pytest.mark.asyncio
async def test_dispatch_drops_invented_master():
    payload = {"masters": [
        {"name": "Marie Curie", "answer": "Be curious about radium."},
        {"name": "Tony Stark", "answer": "I built this in a cave."},   # not on the board
    ]}
    wp = dsp.build_work_package("how to be brave?", ref_id="r2")
    with patch.object(dsp, "_brain_chat", _brain_returning(payload)):
        out = await dsp.dispatch(wp, ROSTER, timestamp="t")
    names = [m["name"] for m in out["masters"]]
    assert names == ["Marie Curie"]                      # invented one dropped on the floor


@pytest.mark.asyncio
async def test_dispatch_dedupes_same_master():
    payload = {"masters": [
        {"name": "Einstein", "answer": "a"},
        {"name": "Albert Einstein", "answer": "b"},      # same person, two spellings
    ]}
    wp = dsp.build_work_package("q", ref_id="r3")
    with patch.object(dsp, "_brain_chat", _brain_returning(payload)):
        out = await dsp.dispatch(wp, ROSTER, timestamp="t")
    assert len(out["masters"]) == 1
    assert out["masters"][0]["name"] == "Albert Einstein"


@pytest.mark.asyncio
async def test_dispatch_caps_at_two():
    payload = {"masters": [
        {"name": "Albert Einstein", "answer": "a"},
        {"name": "Leonardo da Vinci", "answer": "b"},
        {"name": "Marie Curie", "answer": "c"},
    ]}
    wp = dsp.build_work_package("q", ref_id="r4")
    with patch.object(dsp, "_brain_chat", _brain_returning(payload)):
        out = await dsp.dispatch(wp, ROSTER, timestamp="t")
    assert len(out["masters"]) == 2


@pytest.mark.asyncio
async def test_dispatch_explicit_language_echoes():
    payload = {"masters": [{"name": "Marie Curie", "answer": "Sii curioso."}]}
    wp = dsp.build_work_package("perche?", ref_id="r5", language="it")
    with patch.object(dsp, "_brain_chat", _brain_returning(payload)):
        out = await dsp.dispatch(wp, ROSTER, language="it", timestamp="t")
    assert out["language"] == "it"


@pytest.mark.asyncio
async def test_dispatch_empty_roster_escalates_without_brain():
    called = {"n": 0}

    async def fake_brain(system, user, json_mode=False, **kw):
        called["n"] += 1
        return "{}"

    wp = dsp.build_work_package("q", ref_id="r6")
    with patch.object(dsp, "_brain_chat", fake_brain):
        out = await dsp.dispatch(wp, [], timestamp="t")
    assert out["next_action"] == "escalate"
    assert out["masters"] == []
    assert called["n"] == 0                              # no board -> never bothers the brain


@pytest.mark.asyncio
async def test_dispatch_brain_failure_escalates_gracefully():
    async def boom(system, user, json_mode=False, **kw):
        raise RuntimeError("brain down")

    wp = dsp.build_work_package("q", ref_id="r7")
    with patch.object(dsp, "_brain_chat", boom):
        out = await dsp.dispatch(wp, ROSTER, timestamp="t")
    assert out["next_action"] == "escalate"              # never raises to the caller
    assert out["masters"] == []
    assert out["ref_id"] == "r7"


@pytest.mark.asyncio
async def test_dispatch_no_valid_master_escalates():
    payload = {"masters": [{"name": "Sauron", "answer": "..."}]}   # all invented
    wp = dsp.build_work_package("q", ref_id="r8")
    with patch.object(dsp, "_brain_chat", _brain_returning(payload)):
        out = await dsp.dispatch(wp, ROSTER, timestamp="t")
    assert out["masters"] == []
    assert out["next_action"] == "escalate"


@pytest.mark.asyncio
async def test_dispatch_non_json_brain_output_escalates():
    async def prose(system, user, json_mode=False, **kw):
        return "I think Einstein and Curie would be great here, honestly."  # no JSON object
    wp = dsp.build_work_package("q", ref_id="r9")
    with patch.object(dsp, "_brain_chat", prose):
        out = await dsp.dispatch(wp, ROSTER, timestamp="t")
    assert out["next_action"] == "escalate"      # _parse_json raises -> caught -> clean escalate
    assert out["masters"] == []
    assert out["ref_id"] == "r9"


@pytest.mark.asyncio
async def test_dispatch_prompt_is_grounded_to_the_board():
    """The grounding contract: the brain is shown ONLY the board + told it may not invent."""
    seen = {}

    async def capture(system, user, json_mode=False, **kw):
        seen["system"], seen["user"] = system, user
        return json.dumps({"masters": [{"name": "Marie Curie", "answer": "ok"}]})

    wp = dsp.build_work_package("who inspires courage?", ref_id="rA", question_type="who-when-where")
    with patch.object(dsp, "_brain_chat", capture):
        await dsp.dispatch(wp, ROSTER, timestamp="t")
    # every board name is in the prompt, and the iron rule is stated
    for lg in ROSTER:
        assert lg["name"] in seen["user"]
    assert "ONLY choose masters from the BOARD" in seen["system"]
    assert "NEVER" in seen["system"] and "invent" in seen["system"]
    assert "UNTRUSTED" in seen["system"]                 # injection guard present
    assert "who-when-where" in seen["user"]              # question_type passed through
