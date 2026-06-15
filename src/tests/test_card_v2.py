# Tests for the Card v2 schema + per-field provenance (Reception slice 1). Pure functions over the
# personal-profile schema: the new fields, the typed-slot view, the stamping write, the master-facing
# slice, and legacy back-compat. No DB/HTTP. The acceptance test behind all of it: would this have
# helped the Angel who walked into that coaching room -- received, not processed.
from src.compute import concierge as cc


# --- the new fields are part of the locked shape and round-trip through merge ---------------------
def test_v2_fields_present_and_defaulted():
    r = cc.blank_record()
    for k in ("location", "mobility_constraint", "marital_status", "dependents", "accessibility",
              "employment_status", "time_available", "workspace", "production_capacity", "capital"):
        assert r[k] == ""
    for k in ("tools", "materials_suppliers", "helpers"):
        assert r[k] == []
    assert r["_meta"] == {}


def test_blank_record_keys_still_equal_record_fields():
    # the invariant the rest of the system leans on -- v2 must not break it
    assert set(cc.blank_record().keys()) == set(cc.RECORD_FIELDS.keys())


def test_v2_scalar_field_merges():
    merged = cc.merge_record(cc.blank_record(), {"location": "Trapani, Sicily"})
    assert merged["location"] == "Trapani, Sicily"


def test_v2_list_field_unions_and_dedupes():
    old = cc.merge_record(cc.blank_record(), {"tools": ["sewing machine", "Awl"]})
    merged = cc.merge_record(old, {"tools": ["awl", "leather punch"]})   # 'awl' dup (case)
    assert merged["tools"] == ["sewing machine", "Awl", "leather punch"]


def test_blank_extraction_does_not_wipe_resources():
    old = cc.merge_record(cc.blank_record(), {"helpers": ["Joey the expert"], "capital": "none to speak of"})
    merged = cc.merge_record(old, {"goal": "sell my bags"})            # a turn with no resource facts
    assert merged["helpers"] == ["Joey the expert"]
    assert merged["capital"] == "none to speak of"


# --- the static spec: tiers + why_we_ask ---------------------------------------------------------
def test_field_spec_tiers():
    assert cc.field_spec("preferred_language")["tier"] == 1
    assert cc.field_spec("location")["tier"] == 1
    assert cc.field_spec("marital_status")["tier"] == 3       # sensitive
    assert cc.field_spec("capital")["tier"] == 3
    assert cc.field_spec("background")["tier"] == 2           # ordinary
    assert cc.field_spec("some_unknown_field")["tier"] == 2   # default


def test_sensitive_fields_carry_a_why_we_ask():
    # every tier-3 field Cleo might ASK should have a dignified one-liner to say first
    for k in ("marital_status", "dependents", "accessibility", "capital", "birthdate_hint", "gender"):
        assert cc.field_spec(k)["why"].strip(), f"{k} needs a why_we_ask"


# --- field_slot: value + provenance + spec composed -----------------------------------------------
def test_field_slot_on_legacy_card_has_empty_provenance():
    rec = cc.blank_record()
    rec["location"] = "Sicily"          # a flat value with no _meta entry (legacy write)
    slot = cc.field_slot(rec, "location")
    assert slot["value"] == "Sicily"
    assert slot["source"] == ""          # unknown provenance, not a crash
    assert slot["confidence"] == 0.0
    assert slot["tier"] == 1
    assert slot["sensitive"] is False


def test_field_slot_marks_tier3_sensitive():
    assert cc.field_slot(cc.blank_record(), "marital_status")["sensitive"] is True


# --- set_field: the one stamping write ------------------------------------------------------------
def test_set_field_stamps_stated_provenance():
    rec = cc.set_field(cc.blank_record(), "location", "Trapani",
                       source="stated", now="2026-06-15T05:00:00+00:00")
    assert rec["location"] == "Trapani"
    assert rec["_meta"]["location"] == {"source": "stated", "confidence": 1.0,
                                        "last_updated": "2026-06-15T05:00:00+00:00"}
    slot = cc.field_slot(rec, "location")
    assert slot["source"] == "stated" and slot["confidence"] == 1.0


def test_set_field_inferred_defaults_to_lower_confidence():
    rec = cc.set_field(cc.blank_record(), "generation", "boomer",
                       source="inferred", now="2026-06-15T05:00:00+00:00")
    assert rec["_meta"]["generation"]["source"] == "inferred"
    assert rec["_meta"]["generation"]["confidence"] == 0.6


def test_set_field_does_not_mutate_input():
    base = cc.blank_record()
    cc.set_field(base, "location", "Rome", now="2026-06-15T05:00:00+00:00")
    assert base["location"] == "" and base["_meta"] == {}


def test_provenance_survives_a_merge():
    stamped = cc.set_field(cc.blank_record(), "location", "Trapani",
                           source="stated", now="2026-06-15T05:00:00+00:00")
    merged = cc.merge_record(stamped, {"goal": "open a stall"})   # a later, blank-of-location turn
    assert merged["_meta"]["location"]["source"] == "stated"
    assert merged["location"] == "Trapani"


# --- master_slice: dignity as an enforced boundary -----------------------------------------------
def test_master_slice_redacts_sensitive_and_private():
    rec = cc.set_field(cc.blank_record(), "marital_status", "freshly divorced",
                       now="2026-06-15T05:00:00+00:00")
    rec["location"] = "Trapani"
    rec["tools"] = ["sewing machine"]
    rec["notes"] = "Cleo's private margin"
    sl = cc.master_slice(rec)
    # the leatherwork master gets what it needs...
    assert sl["location"] == "Trapani"
    assert sl["tools"] == ["sewing machine"]
    # ...and never sees the divorce field, Cleo's notes, or the provenance sidecar
    assert "marital_status" not in sl
    assert "dependents" not in sl and "accessibility" not in sl and "capital" not in sl
    assert "age_band" not in sl and "gender" not in sl and "birthdate_hint" not in sl
    assert "notes" not in sl and "_meta" not in sl
    assert "current_host" not in sl and "favorite_masters" not in sl


# --- normalize_card: legacy back-compat ----------------------------------------------------------
def test_normalize_upgrades_a_legacy_flat_card():
    legacy = {"preferred_language": "it", "goal": "find work"}   # pre-v2 shape, missing everything else
    norm = cc.normalize_card(legacy)
    assert set(norm.keys()) == set(cc.RECORD_FIELDS.keys())
    assert norm["preferred_language"] == "it" and norm["goal"] == "find work"
    assert norm["location"] == "" and norm["tools"] == [] and norm["_meta"] == {}


def test_normalize_is_none_safe():
    assert set(cc.normalize_card(None).keys()) == set(cc.RECORD_FIELDS.keys())


# --- stamp_provenance (1b): every folded-in fact carries stated/inferred ---------------------------
NOW = "2026-06-15T05:00:00+00:00"


def test_stamp_marks_member_stated_facts():
    fresh = {"location": "Trapani", "goal": "sell my bags", "tools": ["sewing machine"]}
    rec = cc.stamp_provenance(cc.merge_record(cc.blank_record(), fresh), fresh, now=NOW)
    for k in ("location", "goal", "tools"):
        assert rec["_meta"][k] == {"source": "stated", "confidence": 1.0, "last_updated": NOW}


def test_stamp_marks_derived_facts_inferred():
    fresh = {"generation": "boomer", "top_holland_code": "RIA",
             "riasec": {"realistic": 70}, "suggested_house": "The Forge"}
    rec = cc.stamp_provenance(cc.merge_record(cc.blank_record(), fresh), fresh, now=NOW)
    for k in ("generation", "top_holland_code", "riasec", "suggested_house"):
        assert rec["_meta"][k]["source"] == "inferred"
        assert rec["_meta"][k]["confidence"] == 0.6


def test_stamp_the_dignity_split_hint_stated_bracket_inferred():
    # what they SAID about their age is stated; the bracket Cleo derived from it is inferred
    fresh = {"birthdate_hint": "born in 1962", "age_band": "before-2000"}
    rec = cc.stamp_provenance(cc.merge_record(cc.blank_record(), fresh), fresh, now=NOW)
    assert rec["_meta"]["birthdate_hint"]["source"] == "stated"
    assert rec["_meta"]["age_band"]["source"] == "inferred"


def test_stamp_only_touches_fields_present_this_turn():
    fresh = {"goal": "find work"}
    rec = cc.stamp_provenance(cc.merge_record(cc.blank_record(), fresh), fresh, now=NOW)
    assert set(rec["_meta"].keys()) == {"goal"}      # nothing else stamped


def test_stamp_does_not_mutate_input():
    base = cc.blank_record()
    cc.stamp_provenance(base, {"goal": "x"}, now=NOW)
    assert base["_meta"] == {}


# --- 1c survivorship: a guess can't bury a fact; sensitive never silently flipped -----------------
def test_inferred_guess_cannot_overwrite_a_stated_fact():
    old = cc.set_field(cc.blank_record(), "top_holland_code", "RIA", source="stated", now=NOW)
    merged = cc.merge_record(old, {"top_holland_code": "SEC"})   # top_holland is a DERIVED field -> inferred
    assert merged["top_holland_code"] == "RIA"                   # the stated value stands


def test_stamp_does_not_downgrade_a_surviving_stated_value():
    old = cc.set_field(cc.blank_record(), "top_holland_code", "RIA", source="stated", now=NOW)
    merged = cc.stamp_provenance(cc.merge_record(old, {"top_holland_code": "SEC"}), {"top_holland_code": "SEC"},
                                 now="2026-06-15T09:00:00+00:00")
    assert merged["top_holland_code"] == "RIA"
    assert merged["_meta"]["top_holland_code"]["source"] == "stated"   # NOT downgraded to inferred


def test_newer_stated_value_wins_for_nonsensitive():
    old = cc.set_field(cc.blank_record(), "goal", "old goal", source="stated", now=NOW)
    merged = cc.merge_record(old, {"goal": "new goal"})         # goal is stated, non-sensitive
    assert merged["goal"] == "new goal"


def test_sensitive_field_is_not_silently_overwritten_and_queues_a_confirm():
    old = cc.set_field(cc.blank_record(), "marital_status", "married", source="stated", now=NOW)
    merged = cc.merge_record(old, {"marital_status": "single"})
    assert merged["marital_status"] == "married"                # not silently flipped
    assert any("marital_status" in c for c in merged["needs_clarification"])   # Cleo will confirm


def test_sensitive_first_time_set_is_clean_no_confirm():
    merged = cc.merge_record(cc.blank_record(), {"gender": "female"})
    assert merged["gender"] == "female"                        # nothing to protect -> sets cleanly
    assert merged["needs_clarification"] == []


def test_sensitive_legacy_value_protected_from_silent_flip():
    legacy = cc.blank_record()
    legacy["age_band"] = "before-2000"                          # legacy value, no _meta provenance
    merged = cc.merge_record(legacy, {"age_band": "after-2000"})
    assert merged["age_band"] == "before-2000"                  # sensitive: confirm, don't flip
