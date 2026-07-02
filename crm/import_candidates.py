#!/usr/bin/env python3
"""Load the discovery sweep CSV into Postino — idempotent upsert by normalized name.

Ensures the hand-qualified baseline (the original 20 from headshop-leads.csv) is present,
then merges in the discovered candidates. A discovered shop whose normalized name already
exists only *fills gaps* (address, canton, provenance) — it never clobbers qualification
data (tier / score / manager) you set by hand.

    cd crm && ./.venv/bin/python import_candidates.py
    cd crm && ./.venv/bin/python import_candidates.py path/to/other.csv
"""
import csv
import re
import sys
from pathlib import Path

from postino.db import Base, SessionLocal, engine
from postino.models import Campaign, Lead
from postino.seed import seed_from_csv

DEFAULT_CSV = (
    Path(__file__).resolve().parent.parent
    / "docs/business/headshop-crm/discovered-candidates.csv"
)

_UML = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "ae", "Ö": "oe",
                      "Ü": "ue", "é": "e", "è": "e", "ê": "e", "à": "a",
                      "â": "a", "ç": "c", "ß": "ss", "ô": "o", "î": "i"})


def _norm(s: str) -> str:
    s = (s or "").lower().strip().translate(_UML)
    s = re.sub(r"\b(gmbh|ag|sa|sarl|sagl|the|der|die|das)\b", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def _int(v: str) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def main(csv_path: Path) -> None:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        # 1. guarantee the hand-qualified baseline exists
        seed_from_csv(db)
        campaign = db.query(Campaign).first()

        # 2. index existing leads by normalized name
        existing = {_norm(l.name): l for l in db.query(Lead).all()}

        added = updated = 0
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name = (row.get("name") or "").strip()
                if not name:
                    continue
                k = _norm(name)
                disc = dict(
                    street_address=(row.get("street") or "").strip(),
                    postal_code=(row.get("zip") or "").strip(),
                    city=(row.get("city") or "").strip(),
                    canton=(row.get("canton") or "").strip(),
                    phone=(row.get("phone") or "").strip(),
                    website=(row.get("website") or "").strip(),
                    contact_hint=(row.get("person") or "").strip(),
                    directory_url=(row.get("url") or "").strip(),
                    source_count=_int(row.get("source_count")),
                    sources=(row.get("sources") or "").strip(),
                )
                if k in existing:
                    lead = existing[k]
                    # fill gaps ONLY — never overwrite hand-set qualification data
                    for fld, val in disc.items():
                        if val and not getattr(lead, fld):
                            setattr(lead, fld, val)
                    updated += 1
                else:
                    lead = Lead(campaign_id=campaign.id, name=name, stage="to_contact", **disc)
                    db.add(lead)
                    existing[k] = lead
                    added += 1
        db.commit()
        total = db.query(Lead).count()
        print(f"imported {csv_path.name}: +{added} new, {updated} matched/filled  "
              f"-> {total} leads total in Postino")
    finally:
        db.close()


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    if not path.exists():
        sys.exit(f"CSV not found: {path}")
    main(path)
