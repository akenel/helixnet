"""Hypercare SLA on screen — how fast did the loop heal a ticket?

Pure functions, no DB/HTTP (tested on the host .venv like vat_resolver). Built straight
off the append-only activity timestamps the timeline already renders — no new data, just
the math: report → fixed → "healed in 2h 37m". This is the number that proves the loop
is fast, and the one a steward shows a shop owner to say "look how quick we turn things".
"""
from datetime import timezone


def humanize_duration(ms):
    """Milliseconds → a glanceable human span: '<1m', '12m', '2h 37m', '3d 4h'.
    None for missing/negative (clock skew) so the UI just hides it."""
    if ms is None or ms < 0:
        return None
    total_min = int(round(ms / 60000))  # round to whole minutes first → no float-branch edges
    if total_min < 1:
        return "<1m"
    if total_min < 60:
        return f"{total_min}m"
    if total_min < 1440:  # under a day
        h, m = divmod(total_min, 60)
        return f"{h}h {m}m" if m else f"{h}h"
    d, rem = divmod(total_min, 1440)
    h = rem // 60
    return f"{d}d {h}h" if h else f"{d}d"


def ticket_timing(opened_at, fixed_at, closed_at, *, now=None):
    """Pure SLA summary from milestone datetimes. 'healed' = opened → fixed (the moment
    the fix shipped); if not fixed yet we expose the running 'open' age so the card can say
    'open 3h'. Naive datetimes are read as UTC so the math never blows up across envs."""
    def aware(d):
        return d.replace(tzinfo=timezone.utc) if (d and d.tzinfo is None) else d

    opened_at, fixed_at, closed_at, now = map(aware, (opened_at, fixed_at, closed_at, now))

    def iso(d):
        return d.isoformat() if d else None

    def span(a, b):
        return int((b - a).total_seconds() * 1000) if (a and b) else None

    end = fixed_at or closed_at
    healed_ms = span(opened_at, end)
    out = {
        "opened_at": iso(opened_at),
        "fixed_at": iso(fixed_at),
        "closed_at": iso(closed_at),
        "healed_ms": healed_ms,
        "healed_human": humanize_duration(healed_ms),
    }
    if end is None and opened_at and now:
        open_ms = span(opened_at, now)
        out["open_ms"] = open_ms
        out["open_human"] = humanize_duration(open_ms)
    return out
