"""Tests for the Reception matcher + packet (R3) -- src/compute/reception.py.

Deterministic: the single brain call is mocked (we test the GROUNDING + packet assembly, not the
model). Mirrors the concierge test mock pattern. The brain's placement quality is measured separately,
live, by tests/reception/reception_eval.py.
"""
import json
from unittest.mock import patch

import pytest

from src.compute import concierge as cg
from src.compute import reception as rcp

ROSTER = [
    {"name": "Marie Curie", "house": "The Lyceum", "tagline": "radioactivity, two Nobels", "ref": "r1"},
    {"name": "Leonardo da Vinci", "house": "The Forge", "tagline": "art + invention", "ref": "r2"},
    {"name": "Niccolo Machiavelli", "house": "The Strategoi", "tagline": "statecraft, strategy", "ref": "r3"},
]


def _brain_returning(payload: dict):
    async def fake_brain(system, user, json_mode=False, schema=None, model=None):
        return json.dumps(payload)
    return fake_brain


@pytest.mark.asyncio
async def test_match_returns_grounded_master_with_board_house():
    """A pick that is on the board survives -- canonical name + board house + the sticky-note."""
    brain = _brain_returning({
        "house": "wrong-house-the-model-guessed", "master": "leonardo da vinci",  # sloppy case
        "alternate": "", "confidence": "high",
        "why": "His breadth bridges art and engineering.",
        "first_step": "Sketch one kinetic-sculpture prototype this week.",
    })
    with patch.object(rcp, "_brain_chat", brain):
        m = await rcp.match_reception(cg.blank_record(), ROSTER)
    assert m["master"] == "Leonardo da Vinci"          # canonical board spelling, not the model's
    assert m["house"] == "The Forge"                   # house from the board, not the model's guess
    assert m["confidence"] == "high"
    assert m["first_step"].startswith("Sketch one kinetic")


@pytest.mark.asyncio
async def test_match_drops_invented_master_and_abstains():
    """ANTI-HALLUCINATION: a master not on the board is dropped -> the guest stays with Cleo."""
    brain = _brain_returning({
        "house": "The Atelier", "master": "Master Aurelio Verdi",  # invented
        "alternate": "", "confidence": "high", "why": "...", "first_step": "...",
    })
    with patch.object(rcp, "_brain_chat", brain):
        m = await rcp.match_reception(cg.blank_record(), ROSTER)
    assert m["master"] == ""
    assert m["confidence"] == "abstain"
    assert "note" in m


@pytest.mark.asyncio
async def test_match_torn_keeps_a_grounded_alternate():
    """torn + a different grounded runner-up -> the alternate is kept (the peek-at-each fork)."""
    brain = _brain_returning({
        "house": "The Strategoi", "master": "Niccolo Machiavelli",
        "alternate": "Marie Curie", "confidence": "torn",
        "why": "Strategist's read of people.", "first_step": "Draft a one-page advisory brief.",
    })
    with patch.object(rcp, "_brain_chat", brain):
        m = await rcp.match_reception(cg.blank_record(), ROSTER)
    assert m["master"] == "Niccolo Machiavelli"
    assert m["confidence"] == "torn"
    assert m["alternate"] == "Marie Curie"


@pytest.mark.asyncio
async def test_match_torn_with_invented_alternate_downgrades_to_high():
    """torn but the runner-up is invented (or the same master) -> not really torn; downgrade clean."""
    brain = _brain_returning({
        "house": "The Forge", "master": "Leonardo da Vinci",
        "alternate": "Some Imaginary Master", "confidence": "torn",
        "why": "...", "first_step": "...",
    })
    with patch.object(rcp, "_brain_chat", brain):
        m = await rcp.match_reception(cg.blank_record(), ROSTER)
    assert m["confidence"] == "high"
    assert m["alternate"] == ""


@pytest.mark.asyncio
async def test_match_no_roster_abstains():
    m = await rcp.match_reception(cg.blank_record(), [])
    assert m["master"] == "" and m["confidence"] == "abstain"


@pytest.mark.asyncio
async def test_match_brain_failure_abstains_gracefully():
    async def boom(system, user, json_mode=False, schema=None, model=None):
        raise RuntimeError("brain down")
    with patch.object(rcp, "_brain_chat", boom):
        m = await rcp.match_reception(cg.blank_record(), ROSTER)
    assert m["master"] == "" and m["confidence"] == "abstain"


def test_build_packet_redacts_tier3_and_carries_the_sticky_note():
    """The packet's card_slice is the dignity-walled projection; the sticky-note + objective travel."""
    rec = cg.blank_record()
    rec["goal"] = "Turn deep chemistry into a legitimate adjacent income."
    rec["capital"] = "about 5000 euro saved"      # tier-3 -- must NOT reach the master
    rec["marital_status"] = "divorced"            # tier-3 -- must NOT reach the master
    rec["aptitudes"] = ["theoretical physics", "chemistry"]
    match = {"house": "The Lyceum", "master": "Marie Curie", "confidence": "high",
             "why": "Adjacent: instrumentation and materials science.",
             "first_step": "List three local labs that buy instrumentation expertise.",
             "alternate": "", "language": "en"}
    pkt = rcp.build_reception_packet(rec, match)
    assert pkt["objective"] == rec["goal"]
    assert pkt["master"] == "Marie Curie" and pkt["house"] == "The Lyceum"
    assert pkt["first_step"].startswith("List three local labs")
    assert pkt["boundaries"]                       # the master inherits the guards
    # the dignity wall holds inside the packet:
    assert "goal" in pkt["card_slice"]
    assert "capital" not in pkt["card_slice"]
    assert "marital_status" not in pkt["card_slice"]
    assert "_meta" not in pkt["card_slice"]


def test_build_packet_objective_falls_back_to_why_they_came():
    rec = cg.blank_record()
    rec["why_they_came"] = "I lost my job and need a new direction."
    pkt = rcp.build_reception_packet(rec, {"master": "Leonardo da Vinci"})
    assert pkt["objective"] == rec["why_they_came"]
