# File: src/services/compute_seeding_service.py
# Purpose: Give demo/test users their starter credit grant so the LPCX dashboard
#          shows real balances. Idempotent: ensure_starter_grant only grants once.

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.compute_service import ensure_starter_grant

logger = logging.getLogger("helix.compute_seeding")

# Demo personas + the camper-realm test users. Each gets one starter grant.
SEED_ACCOUNTS = [
    "angel", "nino", "sebastino", "johnny", "frank",
    "pam", "ralph", "michael", "felix",
]


async def seed_compute_data(db: AsyncSession) -> None:
    granted = 0
    for account in SEED_ACCOUNTS:
        before = await ensure_starter_grant(db, account)
        # ensure_starter_grant commits on first grant; count freshly-granted accounts
        if before > 0:
            granted += 1
    logger.info(f"LPCX compute seeded: starter grants ensured for {len(SEED_ACCOUNTS)} accounts")
