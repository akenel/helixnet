"""Seed Postino from the qualified head-shop CSV. Idempotent — safe to re-run."""
import csv
from pathlib import Path

from sqlalchemy.orm import Session

from .models import Campaign, Lead

CSV_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs/business/headshop-crm/headshop-leads.csv"
)

# CSV contact_status -> pipeline stage
STATUS_MAP = {
    "todo": "to_contact",
    "enriched": "to_contact",
    "drop": "dropped",
    "called": "contacted",
    "emailed": "contacted",
    "reached": "replied",
}


def _int(v: str, default: int = 0) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def _float(v: str):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def seed_from_csv(db: Session, csv_path: Path = CSV_PATH) -> int:
    """Create the default campaign and load any leads not already present."""
    campaign = db.query(Campaign).first()
    if campaign is None:
        campaign = Campaign(
            name="Swiss Head-Shops — Postcard Campaign 1",
            client="UFA / Postino",
            notes="Batch 1: 20 CH head-shops qualified 2026-07-01.",
        )
        db.add(campaign)
        db.flush()

    if not csv_path.exists():
        db.commit()
        return 0

    added = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ext = (row.get("id") or "").strip()
            if ext:
                exists = (
                    db.query(Lead)
                    .filter(Lead.ext_id == ext, Lead.campaign_id == campaign.id)
                    .first()
                )
                if exists:
                    continue
            db.add(
                Lead(
                    campaign_id=campaign.id,
                    ext_id=ext,
                    name=(row.get("name") or "").strip(),
                    chain=(row.get("chain") or "").strip(),
                    category=(row.get("category") or "").strip(),
                    city=(row.get("city") or "").strip(),
                    rating=_float(row.get("rating")),
                    reviews=_int(row.get("reviews")),
                    phone=(row.get("phone") or "").strip(),
                    street_address=(row.get("street_address") or "").strip(),
                    postal_code=(row.get("postal_code") or "").strip(),
                    website=(row.get("website") or "").strip(),
                    email=(row.get("email") or "").strip(),
                    legal_entity=(row.get("legal_entity") or "").strip(),
                    manager_name=(row.get("manager_name") or "").strip(),
                    manager_role=(row.get("manager_role") or "").strip(),
                    qualify_score=_int(row.get("qualify_score")),
                    tier=(row.get("tier") or "").strip(),
                    persona=(row.get("persona") or "").strip(),
                    stage=STATUS_MAP.get(
                        (row.get("contact_status") or "").strip().lower(), "to_contact"
                    ),
                    postcard_sent_on=(row.get("postcard_sent") or "").strip() or None,
                    notes=(row.get("notes") or "").strip(),
                )
            )
            added += 1

    db.commit()
    return added
