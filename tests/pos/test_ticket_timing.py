"""Hypercare SLA — unit tests for the ticket timing helpers.

Pure: no DB, no HTTP, no app boot (runs on the host .venv in ms, like test_vat_resolver).
Locks the number a steward shows a shop owner: report → fixed = "healed in 2h 37m".
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.services.ticket_timing import humanize_duration, ticket_timing  # noqa: E402

MIN = 60_000
HOUR = 60 * MIN
DAY = 24 * HOUR


# ── humanize_duration ────────────────────────────────────────────────────────
def test_humanize_buckets():
    assert humanize_duration(0) == "<1m"
    assert humanize_duration(30_000) == "<1m"
    assert humanize_duration(12 * MIN) == "12m"
    assert humanize_duration(59 * MIN) == "59m"
    assert humanize_duration(HOUR) == "1h"            # exact hour: no trailing 0m
    assert humanize_duration(2 * HOUR + 37 * MIN) == "2h 37m"   # the canonical example
    assert humanize_duration(DAY) == "1d"             # exact day: no trailing 0h
    assert humanize_duration(3 * DAY + 4 * HOUR) == "3d 4h"


def test_humanize_rounding_never_shows_60():
    # 1h 59m 40s rounds the minutes to 60 → must roll up to 2h, never "1h 60m".
    assert humanize_duration(HOUR + 59 * MIN + 40_000) == "2h"
    # 23h 59m 40s → rolls to 1d, never "23h 60m" or "0d 24h".
    assert humanize_duration(23 * HOUR + 59 * MIN + 40_000) == "1d"


def test_humanize_guards():
    assert humanize_duration(None) is None
    assert humanize_duration(-5) is None              # clock skew → hidden, not negative


# ── ticket_timing ──────────────────────────────────────────────────────────—
def test_healed_uses_fixed_moment():
    opened = datetime(2026, 6, 29, 12, 33, tzinfo=timezone.utc)
    fixed = opened + timedelta(hours=2, minutes=37)
    closed = opened + timedelta(hours=5)              # later — must NOT be the healed span
    t = ticket_timing(opened, fixed, closed, now=opened + timedelta(hours=6))
    assert t["healed_human"] == "2h 37m"
    assert t["healed_ms"] == 2 * HOUR + 37 * MIN
    assert t["fixed_at"] == fixed.isoformat()
    assert "open_human" not in t                      # resolved → no running age


def test_open_age_when_not_fixed():
    opened = datetime(2026, 6, 29, 9, 0, tzinfo=timezone.utc)
    now = opened + timedelta(hours=3)
    t = ticket_timing(opened, None, None, now=now)
    assert t["healed_human"] is None                  # not healed yet
    assert t["open_human"] == "3h"                    # but we show how long it's been open


def test_closed_without_fixed_falls_back_to_close():
    # rejected-then-agreed path: never a "done", but it did close — heal = opened → closed.
    opened = datetime(2026, 6, 29, 8, 0, tzinfo=timezone.utc)
    closed = opened + timedelta(minutes=45)
    t = ticket_timing(opened, None, closed, now=opened + timedelta(hours=2))
    assert t["healed_human"] == "45m"


def test_naive_datetimes_treated_as_utc():
    # DB rows can come back naive; mixing naive + aware must not raise.
    opened = datetime(2026, 6, 29, 12, 0)             # naive
    fixed = datetime(2026, 6, 29, 13, 30, tzinfo=timezone.utc)
    t = ticket_timing(opened, fixed, None, now=fixed)
    assert t["healed_human"] == "1h 30m"
