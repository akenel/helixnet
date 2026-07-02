"""Fold campaign scan/„Ja" events into the board — join by ext_id = the card's token.

Source can be a URL (the Banco landing's /kaffee/events?key=…) or a local path (a combined
events.json, a directory holding coffee_visits.jsonl + coffee_leads.jsonl, or a single leads
jsonl). Idempotent: a „Ja" advances the lead to `replied` and logs it once; repeat scans keep a
single rolling „[scan] N" note. The token is the whole join — the web and the CRM become one loop.
"""
import json
import os
import urllib.request

from sqlalchemy import select

from .models import Interaction, Lead


def _fetch(src: str) -> dict:
    if src.startswith("http"):
        with urllib.request.urlopen(src, timeout=15) as r:
            return json.load(r)
    if os.path.isdir(src):
        def rd(name):
            f = os.path.join(src, name)
            return [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()] if os.path.exists(f) else []
        return {"visits": rd("coffee_visits.jsonl"), "leads": rd("coffee_leads.jsonl")}
    data = open(src, encoding="utf-8").read()
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return {"visits": [], "leads": [json.loads(l) for l in data.splitlines() if l.strip()]}


def sync_events(db, src: str) -> dict:
    ev = _fetch(src)
    by_token = {l.ext_id: l for l in db.scalars(select(Lead)).all() if l.ext_id}
    out = {"replied": 0, "scans_noted": 0, "no_lead": 0, "already": 0}

    # scans → one rolling "[scan] N" note (a mere scan doesn't advance the stage)
    counts: dict[str, int] = {}
    for v in ev.get("visits", []):
        counts[v.get("token")] = counts.get(v.get("token"), 0) + 1
    for tok, n in counts.items():
        lead = by_token.get(tok)
        if not lead:
            out["no_lead"] += 1
            continue
        existing = next((i for i in lead.interactions if i.kind == "note" and i.body.startswith("[scan]")), None)
        if existing:
            existing.body = f"[scan] {n} Seitenbesuch(e)"
        else:
            db.add(Interaction(lead_id=lead.id, kind="note", body=f"[scan] {n} Seitenbesuch(e)"))
            out["scans_noted"] += 1

    # „Ja" → advance to replied + log once (dedup by token+timestamp)
    for L in ev.get("leads", []):
        lead = by_token.get(L.get("token"))
        if not lead:
            out["no_lead"] += 1
            continue
        at = L.get("at", "")
        if any(i.body.startswith("[Ja]") and at and at in i.body for i in lead.interactions):
            out["already"] += 1
            continue
        db.add(Interaction(lead_id=lead.id, kind="note",
                           body=f"[Ja] Einladung/Kaffee angefragt via Karte ({at}). Kontakt: {L.get('contact') or '—'}"))
        if lead.stage in ("to_contact", "contacted", "postcard_sent"):
            lead.stage = "replied"
        out["replied"] += 1

    db.commit()
    return out
