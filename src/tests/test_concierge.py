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


def test_merge_collapses_reworded_near_duplicates_and_caps():
    # the real UAT bug: the extractor rewords the same idea each turn -> exact dedupe let lists balloon.
    old = cg.merge_record(cg.blank_record(), {"conflicts": ["Initially claimed to be a retired baker from Trapani"]})
    merged = cg.merge_record(old, {"conflicts": [
        "Initially claimed to be a retired baker, later clarified a developer",
        "Initially claimed to be a retired baker then said he is a developer",
        "Asked for profile retrieval despite lacking the login",
    ]})
    # the three baker rewordings collapse to ONE (shared 40-char prefix); the distinct one survives
    assert len(merged["conflicts"]) == 2
    # and lists are hard-capped at 12
    big = cg.merge_record(cg.blank_record(), {"affinities": [f"distinct skill number {i}" for i in range(30)]})
    assert len(big["affinities"]) == 12


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


# --- portrait_completeness: the scorecard axis ---------------------------------------------

def test_portrait_completeness_blank_is_zero():
    s = cg.portrait_completeness(cg.blank_record())
    assert s["filled"] == 0 and s["pct"] == 0
    assert s["total"] == len(cg.PORTRAIT_KEYS)


def test_portrait_completeness_counts_lists_and_riasec():
    rec = cg.merge_record(cg.blank_record(), {
        "goal": "teach", "aptitudes": ["repair"], "riasec": {"realistic": 80}})
    s = cg.portrait_completeness(rec)
    assert s["filled"] == 3                       # goal + aptitudes(list) + riasec(nonzero)
    assert 0 < s["pct"] < 100


def test_portrait_completeness_full_is_hundred():
    rec = cg.blank_record()
    for k in cg.PORTRAIT_KEYS:
        if k == "riasec":
            rec[k] = {"realistic": 50}
        elif k in ("aptitudes", "affinities"):
            rec[k] = ["x"]
        else:
            rec[k] = "set"
    assert cg.portrait_completeness(rec)["pct"] == 100


def test_portrait_completeness_none_safe():
    assert cg.portrait_completeness({})["pct"] == 0
    assert cg.portrait_completeness(None)["pct"] == 0


# --- language clause: voice follows language -----------------------------------------------

def test_lang_clause_auto_mirrors_explicit_forces():
    # the masters' rule: auto/empty -> mirror the member's tongue and stay in it
    for auto in ("", "auto", "AUTO"):
        c = cg._lang_clause(auto)
        assert "SAME language" in c and "STAY" in c
    # explicit English -> forces English
    assert "English" in cg._lang_clause("en") and "English" in cg._lang_clause("English")
    # explicit Italian -> forces Italian
    it = cg._lang_clause("it")
    assert "ITALIAN" in it and "RESPOND ENTIRELY" in it
    # unknown code still produces a forced clause using the raw code
    assert "ZZ" in cg._lang_clause("zz").upper()


def test_detect_lang_en_vs_it():
    assert cg.detect_lang("I want to teach kids how to fix bikes") == "en"
    assert cg.detect_lang("ciao, vorrei insegnare ai bambini come si fa") == "it"
    assert cg.detect_lang("") == "en"  # nothing -> default hub


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


@pytest.mark.asyncio
async def test_concierge_tolerates_and_self_heals_duplicate_rows(db_session):
    # The staging 500: a legacy/race left TWO concierge-record rows for one member, and
    # scalar_one_or_none() raised MultipleResultsFound. read must newest-win (not 500),
    # and the next write must collapse the dups back to a single row.
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select
    from src.db.models.bottega_model import BottegaSessionModel
    from src.routes import bottega_router as br

    older = datetime(2026, 1, 1, tzinfo=timezone.utc)
    newer = older + timedelta(days=1)
    db_session.add(BottegaSessionModel(
        username="dup", slug=br.CONCIERGE_SLUG, title="Concierge Record", inputs="{}",
        output=json.dumps({"record": {"goal": "OLD goal"}, "transcript": []}),
        output_type="json", tags="concierge", created_at=older))
    db_session.add(BottegaSessionModel(
        username="dup", slug=br.CONCIERGE_SLUG, title="Concierge Record", inputs="{}",
        output=json.dumps({"record": {"goal": "NEW goal"}, "transcript": [{"role": "member", "content": "hi"}]}),
        output_type="json", tags="concierge", created_at=newer))
    await db_session.commit()

    # read must not raise, and newest wins
    state = await br.read_concierge(db_session, "dup")
    assert state["record"]["goal"] == "NEW goal"
    assert state["transcript"] == [{"role": "member", "content": "hi"}]

    # write self-heals: collapses to exactly one row, keeping the newest, applying the update
    rec = cg.merge_record(cg.blank_record(), {"goal": "NEW goal", "background": "30 yrs"})
    await br.write_concierge(db_session, "dup", rec, [{"role": "member", "content": "hi"}])
    rows = (await db_session.execute(select(BottegaSessionModel).where(
        BottegaSessionModel.username == "dup",
        BottegaSessionModel.slug == br.CONCIERGE_SLUG))).scalars().all()
    assert len(rows) == 1                              # the duplicate was dropped
    assert json.loads(rows[0].output)["record"]["background"] == "30 yrs"
