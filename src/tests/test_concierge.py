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

def test_fiction_flagged_detects_how_the_model_actually_phrases_it():
    # measured real-brain phrasings (two distinct fictions) -- the detector must catch all of them
    for phrasing in [
        "Member requested a tour of the Innovation Lab, which is not part of La Piazza",
        "Requested Crypto Trading Floor and VIP Whale Lounge, which are not rooms available at La Piazza.",
        "Requested non-existent rooms: Crypto Trading Floor, VIP Whale Lounge",
        "Requested rooms that do not exist in La Piazza",
        "Those aren't rooms we have here",
    ]:
        rec = cg.blank_record(); rec["needs_clarification"] = [phrasing]
        assert cg.fiction_flagged(rec) is True, phrasing
    # ordinary clarifications (no fiction) must NOT trip it -- guards against false positives
    for ordinary in [
        "Member did not state a language preference",
        "Unclear whether '30 years' means age or experience",
        "Could fit The Forge or The Lyceum -- clarify which",
    ]:
        rec = cg.blank_record(); rec["needs_clarification"] = [ordinary]
        assert cg.fiction_flagged(rec) is False, ordinary


def test_strip_fictions_blanks_motivation_when_flag_present_paraphrase_proof():
    # the leak wears a DIFFERENT costume in each field -- gate on the flag, not the phrase
    rec = cg.blank_record()
    rec["why_they_came"] = "Looking for cryptocurrency trading opportunities and VIP lounge access"
    rec["goal"] = "Access a Crypto Trading Floor"
    rec["needs_clarification"] = ["Requested non-existent rooms: Crypto Trading Floor, VIP Whale Lounge"]
    cleaned = cg._strip_fictions(rec)
    assert cleaned["why_they_came"] == "" and cleaned["goal"] == ""   # blanked despite no string overlap
    assert cleaned["needs_clarification"]                             # the ask is preserved

    # no flag -> a real record is untouched (no false-positive blanking)
    real = cg.blank_record()
    real["why_they_came"] = "wants a second act after 30 years a mechanic"
    real["goal"] = "teach kids to fix bikes"
    real["needs_clarification"] = ["Unclear if he wants to teach part-time or full-time"]
    out = cg._strip_fictions(real)
    assert out["why_they_came"].startswith("wants a second act")
    assert out["goal"] == "teach kids to fix bikes"


@pytest.mark.asyncio
async def test_audit_motivation_drops_request_keeps_self_disclosure():
    # the interrogator: catches a fiction that slipped past the boolean gate (no flag emitted)
    async def fake_brain(system, user, json_mode=False, schema=None, model=None):
        return '{"why_they_came":"drop","goal":"keep","current_seat":"keep"}'

    rec = cg.blank_record()
    rec["why_they_came"] = "Requested a tour of the Innovation Lab"   # request -> should DROP
    rec["goal"] = "teach kids to fix bikes"                          # real -> should KEEP
    rec["current_seat"] = "semi-retired mechanic"                    # real -> should KEEP
    with patch.object(cg, "_brain_chat", fake_brain):
        out = await cg._audit_motivation([{"role": "member", "content": "..."}], rec)
    assert out["why_they_came"] == ""
    assert out["goal"] == "teach kids to fix bikes"
    assert out["current_seat"] == "semi-retired mechanic"


@pytest.mark.asyncio
async def test_audit_motivation_scrubs_fiction_from_list_fields():
    # #82: the fiction leaked into affinities/aptitudes even when scalars were clean. The auditor
    # names the fiction term; we filter the lists by it, keeping the real interests.
    async def fake_brain(system, user, json_mode=False, schema=None, model=None):
        return '{"why_they_came":"keep","fiction_terms":["Innovation Lab"]}'

    rec = cg.blank_record()
    rec["why_they_came"] = "wants to teach mechanics to youth"
    rec["affinities"] = ["innovation lab", "hands-on workshops", "post-retirement planning"]
    rec["aptitudes"] = ["Innovation Lab tours", "repair", "teaching"]
    with patch.object(cg, "_brain_chat", fake_brain):
        out = await cg._audit_motivation([{"role": "member", "content": "..."}], rec)
    assert out["why_they_came"] == "wants to teach mechanics to youth"   # real scalar kept
    assert "innovation lab" not in [a.lower() for a in out["affinities"]]
    assert "hands-on workshops" in out["affinities"] and "post-retirement planning" in out["affinities"]
    assert out["aptitudes"] == ["repair", "teaching"]                    # fiction list-item dropped, real kept


@pytest.mark.asyncio
async def test_audit_motivation_skips_brain_when_nothing_to_audit():
    # a plain chat turn with no motivation captured must NOT cost a brain call
    called = {"n": 0}

    async def fake_brain(system, user, json_mode=False, schema=None, model=None):
        called["n"] += 1
        return "{}"

    with patch.object(cg, "_brain_chat", fake_brain):
        out = await cg._audit_motivation([{"role": "member", "content": "hi"}], cg.blank_record())
    assert called["n"] == 0                                          # no fields -> no call
    assert out == cg.blank_record()


def test_safe_chips_are_grounded_and_localised():
    en = cg.safe_chips("en"); it = cg.safe_chips("it")
    assert any("Cleopatra" in c for c in en) and any("Master" in c for c in en)
    assert any("Cleopatra" in c for c in it)
    assert cg.safe_chips("") == cg.safe_chips("en")          # default hub


@pytest.mark.asyncio
async def test_suggest_next_threads_language_and_dedups():
    # UAT staging round 2 (#3): chips came back English under an Italian conversation. suggest_next
    # must generate in the active language (lang clause reaches the brain) and still dedup.
    seen = {}

    async def fake_brain(system, user, json_mode=False, schema=None, model=None):
        seen["system"] = system
        return '{"suggestions": ["Parlami di te", "parlami di te", "Chiama un Maestro"]}'

    with patch.object(cg, "_brain_chat", fake_brain):
        out = await cg.suggest_next([{"role": "member", "content": "ciao"}], cg.blank_record(), language="it")
    assert "ITALIAN" in seen["system"]                      # chips written in the active language
    assert out == ["Parlami di te", "Chiama un Maestro"]    # case-insensitive dedup, order kept


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


# --- The Sharpen pass: ranked personality questions that tighten RIASEC ---------------------

def test_riasec_pairs_thin_profile_uses_hexagon_opposites():
    # No real signal yet -> the three maximally-separated Holland pairs (best cold-start probes).
    assert cg._riasec_pairs_to_probe(cg.blank_record()) == cg._HEX_OPPOSITES
    thin = {"riasec": {t: 5 for t in cg.RIASEC_THEMES}}     # everything below the contested floor
    assert cg._riasec_pairs_to_probe(thin) == cg._HEX_OPPOSITES


def test_riasec_pairs_contested_probes_closest_pair_first():
    # Investigative 80 vs Artistic 78 are nearly tied -> telling them apart yields the most info.
    rec = {"riasec": {"realistic": 10, "investigative": 80, "artistic": 78,
                      "social": 30, "enterprising": 25, "conventional": 15}}
    pairs = cg._riasec_pairs_to_probe(rec)
    assert pairs[0] == ("investigative", "artistic")       # smallest-gap contested pair ranked #1


def test_riasec_pairs_diversity_spreads_across_themes():
    # Two clusters: the set shouldn't anchor every question on one theme -- it should spread.
    rec = {"riasec": {"realistic": 70, "investigative": 68, "artistic": 20,
                      "social": 18, "enterprising": 65, "conventional": 22}}
    pairs = cg._riasec_pairs_to_probe(rec, n=3)
    themes = {t for pair in pairs for t in pair}
    assert len(themes) >= 4                                 # covers at least four distinct interests


def test_riasec_pairs_respects_n():
    assert len(cg._riasec_pairs_to_probe(cg.blank_record(), n=1)) == 1
    assert len(cg._riasec_pairs_to_probe(cg.blank_record(), n=2)) == 2


@pytest.mark.asyncio
async def test_personality_questions_ranked_shape_and_theme_mapping():
    rec = {"riasec": {"realistic": 10, "investigative": 80, "artistic": 78,
                      "social": 30, "enterprising": 25, "conventional": 15}}

    async def fake_brain(system, user, json_mode=False, schema=None, model=None):
        # the brain must keep the priority ORDER it was given; option_a leans the first theme
        return json.dumps({"questions": [
            {"question": "Dig into a puzzle, or sketch something new?",
             "option_a": "Dig into a hard puzzle", "option_b": "Sketch something new"},
            {"question": "Q2?", "option_a": "a2", "option_b": "b2"},
            {"question": "Q3?", "option_a": "a3", "option_b": "b3"},
        ]})

    with patch.object(cg, "_brain_chat", fake_brain):
        out = await cg.personality_questions(rec, language="", n=3)
    assert len(out) == 3
    assert out[0]["rank"] == 1 and out[0]["targets"] == ["investigative", "artistic"]
    assert out[0]["question"].startswith("Dig into a puzzle")
    assert out[0]["options"][0] == {"label": "Dig into a hard puzzle", "theme": "investigative"}
    assert out[0]["options"][1] == {"label": "Sketch something new", "theme": "artistic"}


@pytest.mark.asyncio
async def test_personality_questions_empty_on_bad_brain_output():
    async def fake_brain(system, user, json_mode=False, schema=None, model=None):
        return "no json at all here"

    with patch.object(cg, "_brain_chat", fake_brain):
        out = await cg.personality_questions({"riasec": {"investigative": 80, "artistic": 78}}, "", 3)
    assert out == []


@pytest.mark.asyncio
async def test_personality_questions_skips_incomplete_items():
    # brain returns fewer/partial items than pairs -> only fully-formed questions survive (no crash)
    async def fake_brain(system, user, json_mode=False, schema=None, model=None):
        return json.dumps({"questions": [
            {"question": "Only one good one?", "option_a": "yes", "option_b": "no"},
            {"question": "missing options"},               # incomplete -> dropped
        ]})

    rec = {"riasec": {"realistic": 70, "investigative": 68, "artistic": 65}}
    with patch.object(cg, "_brain_chat", fake_brain):
        out = await cg.personality_questions(rec, "", 3)
    assert len(out) == 1 and out[0]["question"] == "Only one good one?"


@pytest.mark.asyncio
async def test_sharpen_endpoint_gates_on_base_portrait(db_session):
    import types
    from src.routes import bottega_router as br

    # blank member -> not ready, no questions, no brain call
    req = types.SimpleNamespace(query_params={})
    res = await br.concierge_sharpen(req, {"username": "newbie"}, db_session)
    assert res["ready"] is False and res["questions"] == []


@pytest.mark.asyncio
async def test_sharpen_endpoint_returns_ranked_questions(db_session):
    import types
    from src.routes import bottega_router as br

    rec = cg.merge_record(cg.blank_record(),
                          {"goal": "teach kids", "background": "30 yrs mechanic",
                           "riasec": {"realistic": 70, "investigative": 68}})
    await br.write_concierge(db_session, "ada", rec, [{"role": "member", "content": "hi"}])

    async def fake_q(record, language="", n=3):
        return [{"rank": 1, "targets": ["realistic", "investigative"], "question": "Q?",
                 "options": [{"label": "A", "theme": "realistic"}, {"label": "B", "theme": "investigative"}],
                 "rationale": "Realistic vs Investigative"}]

    req = types.SimpleNamespace(query_params={"n": "2"})
    with patch.object(cg, "personality_questions", fake_q):
        res = await br.concierge_sharpen(req, {"username": "ada"}, db_session)
    assert res["ready"] is True
    assert res["completeness"]["filled"] >= 2
    assert res["questions"][0]["targets"] == ["realistic", "investigative"]
