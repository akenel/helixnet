# Tests for src.compute.concierge + the persistence helpers in bottega_router.
# Pure/mocked: no network, no real brain. Locks the MEMORY-FIRST contract -- the merge
# must never clobber known facts with blanks, the extractor must survive messy model
# output, and the record must round-trip through the bottega_sessions spine.

import json
from unittest.mock import patch

import pytest

from src.compute import concierge as cg


# --- blank_record: the locked shape, every field present, never blank to the masters ----

def test_blank_record_has_every_field_and_is_a_deep_copy():
    r1 = cg.blank_record()
    r2 = cg.blank_record()
    assert set(r1.keys()) == set(cg.RECORD_FIELDS.keys())
    assert set(r1["riasec"].keys()) == {
        "realistic", "investigative", "artistic", "social", "enterprising", "conventional"}
    # mutating one copy must not bleed into the template or another copy
    r1["riasec"]["realistic"] = 99
    r1["aptitudes"].append("x")
    assert r2["riasec"]["realistic"] == 0
    assert r2["aptitudes"] == []
    assert cg.RECORD_FIELDS["riasec"]["realistic"] == 0


# --- merge_record: the data-integrity core -------------------------------------------------

def test_merge_does_not_clobber_known_with_blank():
    old = cg.merge_record(cg.blank_record(), {"goal": "teach kids", "background": "30 yrs"})
    # a later turn that knows nothing must NOT erase what we had
    merged = cg.merge_record(old, {"goal": "", "background": "unknown", "health_energy": "back pain"})
    assert merged["goal"] == "teach kids"
    assert merged["background"] == "30 yrs"
    assert merged["health_energy"] == "back pain"     # new fact written


def test_merge_unions_lists_dedup_case_insensitive_order_preserving():
    old = cg.merge_record(cg.blank_record(), {"aptitudes": ["Repair", "patience"]})
    merged = cg.merge_record(old, {"aptitudes": ["repair", "teaching"]})  # 'repair' dup (case)
    assert merged["aptitudes"] == ["Repair", "patience", "teaching"]


def test_merge_riasec_latest_nonzero_wins_clamped():
    old = cg.merge_record(cg.blank_record(), {"riasec": {"realistic": 80, "social": 50}})
    merged = cg.merge_record(old, {"riasec": {"realistic": 90, "artistic": 999, "social": 0}})
    assert merged["riasec"]["realistic"] == 90     # moved -> latest wins
    assert merged["riasec"]["social"] == 50        # 0 in new -> keep prior
    assert merged["riasec"]["artistic"] == 100     # clamped to 100
    assert merged["riasec"]["investigative"] == 0  # untouched default


def test_merge_conflicts_accumulate_without_duplicates():
    old = cg.merge_record(cg.blank_record(), {"conflicts": ["wants health, won't move"]})
    merged = cg.merge_record(old, {"conflicts": ["wants health, won't move", "loves outdoors, won't leave desk"]})
    assert merged["conflicts"] == ["wants health, won't move", "loves outdoors, won't leave desk"]


def test_merge_ignores_unknown_extra_keys_and_tolerates_none():
    base = cg.blank_record()
    merged = cg.merge_record(base, {"junk_key": "ignore me", "goal": None})
    assert "junk_key" not in merged
    assert merged["goal"] == ""                    # None is not meaningful -> default kept


def test_merge_from_empty_old_is_safe():
    merged = cg.merge_record({}, {"goal": "ship it"})
    assert merged["goal"] == "ship it"
    assert set(merged.keys()) == set(cg.RECORD_FIELDS.keys())


# --- record_to_portrait: closing the loop (Phase 3) ----------------------------------------

def test_record_to_portrait_renders_signal_and_skips_blanks():
    rec = cg.merge_record(cg.blank_record(), {
        "why_they_came": "wants a second act",
        "goal": "teach kids bike repair",
        "background": "30 years a mechanic",
        "current_seat": "semi-retired mechanic",
        "fit_insight": "would thrive teaching",
        "aptitudes": ["repair", "patience"],
        "conflicts": ["wants it but won't travel"],
        "life_stage": "legacy",
        "health_energy": "back pain",
    })
    parts = cg.record_to_portrait(rec)
    blob = " ".join(parts)
    assert "teach kids bike repair" in blob
    assert "30 years a mechanic" in blob
    assert "semi-retired mechanic" in blob and "would thrive teaching" in blob  # combined sentence
    assert "legacy" in blob
    assert "don't lecture" in blob.lower()          # conflicts framed as mirror, not finger


def test_record_to_portrait_empty_record_is_empty():
    assert cg.record_to_portrait(cg.blank_record()) == []
    assert cg.record_to_portrait({}) == []


# --- language clause: voice follows language -----------------------------------------------

def test_lang_clause_only_for_non_english():
    assert cg._lang_clause("") == ""
    assert cg._lang_clause("en") == ""
    assert cg._lang_clause("English") == ""
    it = cg._lang_clause("it")
    assert "ITALIAN" in it and "RESPOND ENTIRELY" in it
    # unknown code still produces a clause using the raw code
    assert "ZZ" in cg._lang_clause("zz").upper()


# --- concierge_reply: flattens transcript + threads language through the single brain ------

@pytest.mark.asyncio
async def test_concierge_reply_flattens_and_passes_language():
    seen = {}

    async def fake_brain(system, user, json_mode=False, schema=None, model=None):
        seen["system"], seen["user"] = system, user
        return "<think>hmm</think>Ciao, benvenuto!"

    transcript = [{"role": "member", "content": "ciao"}]
    with patch.object(cg, "_brain_chat", fake_brain):
        out = await cg.concierge_reply(transcript, cg.blank_record(), language="it")
    assert out == "Ciao, benvenuto!"                # <think> stripped
    assert "MEMBER: ciao" in seen["user"]           # transcript flattened
    assert "ITALIAN" in seen["system"]              # language clause appended to persona


# --- extract_record: survives messy model output (the proven gotcha-proof path) ------------

@pytest.mark.asyncio
async def test_extract_record_pulls_json_from_noisy_output():
    async def fake_brain(system, user, json_mode=False, schema=None, model=None):
        return ('<think>let me think</think>Sure, here is the record:\n'
                '{"goal": "teach", "riasec": {"realistic": 90}}\nHope that helps!')

    with patch.object(cg, "_brain_chat", fake_brain):
        rec = await cg.extract_record([{"role": "member", "content": "..."}])
    assert rec["goal"] == "teach"
    assert rec["riasec"]["realistic"] == 90


@pytest.mark.asyncio
async def test_extract_record_raises_when_no_json():
    async def fake_brain(system, user, json_mode=False, schema=None, model=None):
        return "I could not extract anything useful."

    with patch.object(cg, "_brain_chat", fake_brain):
        with pytest.raises(ValueError):
            await cg.extract_record([{"role": "member", "content": "x"}])


# --- persistence round-trip: the record survives the bottega_sessions spine ----------------

@pytest.mark.asyncio
async def test_concierge_persistence_round_trip(db_session):
    from src.routes import bottega_router as br

    # empty -> blank record + empty transcript
    state0 = await br.read_concierge(db_session, "marco")
    assert state0["transcript"] == []
    assert set(state0["record"].keys()) == set(cg.RECORD_FIELDS.keys())

    rec = cg.merge_record(cg.blank_record(), {"goal": "teach kids", "riasec": {"realistic": 90}})
    transcript = [{"role": "member", "content": "hi"}, {"role": "concierge", "content": "ciao"}]
    await br.write_concierge(db_session, "marco", rec, transcript)

    state1 = await br.read_concierge(db_session, "marco")
    assert state1["record"]["goal"] == "teach kids"
    assert state1["record"]["riasec"]["realistic"] == 90
    assert state1["transcript"] == transcript

    # upsert (not duplicate): a second write updates the same row
    rec2 = cg.merge_record(state1["record"], {"background": "30 yrs"})
    await br.write_concierge(db_session, "marco", rec2, transcript)
    from sqlalchemy import select
    from src.db.models.bottega_model import BottegaSessionModel
    rows = (await db_session.execute(select(BottegaSessionModel).where(
        BottegaSessionModel.username == "marco",
        BottegaSessionModel.slug == br.CONCIERGE_SLUG))).scalars().all()
    assert len(rows) == 1                            # upserted, not duplicated
    assert json.loads(rows[0].output)["record"]["background"] == "30 yrs"


@pytest.mark.asyncio
async def test_read_concierge_recovers_from_corrupt_row(db_session):
    from sqlalchemy import select
    from src.db.models.bottega_model import BottegaSessionModel
    from src.routes import bottega_router as br

    db_session.add(BottegaSessionModel(
        username="bad", slug=br.CONCIERGE_SLUG, title="Concierge Record",
        inputs="{}", output="{not valid json", output_type="json", tags="concierge"))
    await db_session.commit()
    state = await br.read_concierge(db_session, "bad")   # must not raise
    assert state["transcript"] == []
    assert set(state["record"].keys()) == set(cg.RECORD_FIELDS.keys())
