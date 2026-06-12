# Tests for Reception R0 -- the prep scan + the duty checklist (the "control data" a host settles
# before handoff). Pure functions over the personal profile schema; no DB/HTTP.
import datetime as _dt
from types import SimpleNamespace

from src.compute import concierge as cc
from src.routes import bottega_router as br


def _blank():
    return cc.blank_record()


# --- must_do_readiness: done / gaps / what BLOCKS -----------------------------------------
def test_empty_card_blocks_on_language_and_house_only():
    r = cc.must_do_readiness(_blank())
    assert r["ready"] is False
    # all four are gaps...
    assert {g["key"] for g in r["gaps"]} == {"language", "house", "age", "why"}
    # ...but only language(hard) + house(produce) BLOCK the handoff; age/why are soft
    assert {g["key"] for g in r["blocking"]} == {"language", "house"}


def test_language_plus_house_is_enough_to_hand_off():
    rec = _blank()
    rec["preferred_language"] = "it"
    rec["suggested_house"] = "The Forge"
    r = cc.must_do_readiness(rec)
    assert r["ready"] is True                      # soft gaps don't block
    assert r["blocking"] == []
    assert {g["key"] for g in r["gaps"]} == {"age", "why"}   # still tracked, just not blocking


def test_missing_language_always_blocks_even_when_everything_else_is_set():
    rec = _blank()
    rec["suggested_house"] = "The Atelier"
    rec["age_band"] = "before-2000"
    rec["why_they_came"] = "start over at 60"
    r = cc.must_do_readiness(rec)
    assert r["ready"] is False
    assert [g["key"] for g in r["blocking"]] == ["language"]


def test_age_satisfied_by_birthdate_hint_and_house_by_riasec_is_not_selection():
    rec = _blank()
    rec["birthdate_hint"] = "Jan 1964"          # age soft-gap closes
    rec["riasec"]["realistic"] = 40              # signal exists, but house is not SELECTED yet
    keys = {g["key"] for g in cc.must_do_readiness(rec)["gaps"]}
    assert "age" not in keys
    assert "house" in keys                        # produce gate needs an actual suggested_house pick


# --- prep_scan: the fresh state a host reads before speaking ------------------------------
def test_prep_scan_brand_new_visitor():
    scan = cc.prep_scan({"record": _blank(), "transcript": []})
    assert scan["is_new"] is True
    assert scan["current_host"] == "Cleopatra"        # no host yet -> Cleo holds the desk
    assert scan["favorite_masters"] == []
    assert scan["ready_to_handoff"] is False
    assert {g["key"] for g in scan["blocking_gaps"]} == {"language", "house"}


def test_prep_scan_returning_visitor_with_standing_host_and_freshness():
    rec = _blank()
    rec["current_host"] = "Leonardo da Vinci"
    rec["favorite_masters"] = ["Leonardo da Vinci", "Tesla"]
    rec["preferred_language"] = "en"
    rec["suggested_house"] = "The Atelier"
    state = {"record": rec, "transcript": [{"role": "member", "content": "hi"}],
             "updated_at": "2026-06-12T12:00:00+00:00"}
    scan = cc.prep_scan(state)
    assert scan["is_new"] is False
    assert scan["current_host"] == "Leonardo da Vinci"   # opens with your master, not Cleo
    assert scan["favorite_masters"] == ["Leonardo da Vinci", "Tesla"]
    assert scan["updated_at"] == "2026-06-12T12:00:00+00:00"   # timestamped, not three years old
    assert scan["ready_to_handoff"] is True


def test_prep_scan_survives_a_malformed_card():
    # a corrupt riasec blob must not crash the scan
    rec = _blank()
    rec["riasec"] = "not a dict"
    scan = cc.prep_scan({"record": rec, "transcript": []})
    assert "ready_to_handoff" in scan and "blocking_gaps" in scan


# --- the new schema fields round-trip through merge_record --------------------------------
def test_current_host_and_favorites_survive_a_merge():
    old = _blank()
    old["current_host"] = "Tesla"
    old["favorite_masters"] = ["Tesla"]
    # a fresh extraction (no host/favorites in it) must NOT clobber the standing host
    merged = cc.merge_record(old, {"goal": "build something"})
    assert merged["current_host"] == "Tesla"
    assert merged["favorite_masters"] == ["Tesla"]
    assert merged["goal"] == "build something"


# --- recipe-run ledger (#119): derive {slug: count/last_run/last_id} from the session spine --------
def _sess(slug, day, rid):
    return SimpleNamespace(slug=slug, id=rid,
                           created_at=_dt.datetime(2026, 6, day, 12, 0, tzinfo=_dt.timezone.utc))


def test_recipe_runs_counts_and_keeps_the_latest():
    rows = [_sess("cv-to-bio", 10, "a"), _sess("cv-to-bio", 12, "b"), _sess("music-playlist", 11, "c")]
    runs = br._recipe_runs(rows)
    assert runs["cv-to-bio"]["count"] == 2
    assert runs["cv-to-bio"]["last_id"] == "b"          # day 12 is the latest run
    assert runs["music-playlist"]["count"] == 1


def test_recipe_runs_excludes_plumbing_and_dispatch():
    rows = [_sess("message", 10, "m"), _sess("notification", 10, "n"),
            _sess("concierge-record", 10, "c"), _sess("dispatch-abc123", 10, "d"),
            _sess("cv-to-bio", 10, "x")]
    runs = br._recipe_runs(rows)
    assert set(runs.keys()) == {"cv-to-bio"}            # only real recipe runs count
