# File: src/services/compute_seeding_service.py
# Purpose: Give demo/test users their starter credit grant so the LPCX dashboard
#          shows real balances. Idempotent: ensure_starter_grant only grants once.

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.compute_model import ComputeTemplateModel
from src.services.compute_service import ensure_starter_grant

logger = logging.getLogger("helix.compute_seeding")

# Demo personas + the camper-realm test users. Each gets one starter grant.
SEED_ACCOUNTS = [
    "angel", "nino", "sebastino", "johnny", "frank",
    "pam", "ralph", "michael", "felix",
]

# Template catalog -- the approved SOP allowlist. (slug, title, description, category, emoji, est_credits)
SEED_TEMPLATES = [
    ("print-card", "Print Card", "Generate a print-ready postcard (the UFA dialect): full-bleed image, overlay title, duplex back.", "print", "\U0001F5A8️", 2),
    ("locandina", "Locandina Poster", "Turn any listing into a shareable Locandina poster -- data ribbon, type badge, QR.", "print", "\U0001F3AD", 3),
    ("music-playlist", "Music Playlist", "Curate a themed playlist (sunrise-chain style) from a mood or region.", "media", "\U0001F3B5", 2),
    ("2d-to-3d", "2D → 3D Model", "Turn a 2D image into a printable 3D model file (the steampunk-submarine job).", "modeling", "\U0001F9CA", 8),
    ("doc-summary", "Doc Summary", "Summarize a document into a tight brief -- the SOP way, low token cost.", "text", "\U0001F4DD", 1),
    ("image-gen", "Image Generation", "Text-to-image generation from a short prompt.", "media", "\U0001F3A8", 4),
]


async def seed_compute_data(db: AsyncSession) -> None:
    for account in SEED_ACCOUNTS:
        await ensure_starter_grant(db, account)
    logger.info(f"LPCX compute seeded: starter grants ensured for {len(SEED_ACCOUNTS)} accounts")

    # Seed the template catalog (idempotent: insert by slug if missing)
    existing = set((await db.execute(select(ComputeTemplateModel.slug))).scalars().all())
    added = 0
    for slug, title, desc, category, emoji, est in SEED_TEMPLATES:
        if slug in existing:
            continue
        db.add(ComputeTemplateModel(
            slug=slug, title=title, description=desc,
            category=category, emoji=emoji, est_credits=est, enabled=True,
        ))
        added += 1
    if added:
        await db.commit()
    logger.info(f"LPCX template catalog: {added} new, {len(SEED_TEMPLATES)} total")
