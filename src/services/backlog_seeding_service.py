# File: src/services/backlog_seeding_service.py
# Purpose: Seed initial backlog items so the board isn't empty.
# Idempotent: checks if data exists before seeding.

import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.backlog_model import (
    BacklogItemModel, BacklogItemType, BacklogStatus, BacklogPriority,
)
from src.core.constants import HelixApplication

logger = logging.getLogger("helix.backlog_seeding")

# ================================================================
# Seed Data -- real work items from recent history
# (item_type, application, status, priority, title, description, assigned_to, tags)
# ================================================================
SEED_ITEMS = [
    (
        BacklogItemType.DEV_TASK, HelixApplication.HELIXNET, BacklogStatus.DONE, BacklogPriority.HIGH,
        "HelixEnum migration (all models)",
        "Migrate all models to use HelixEnum base class for case-insensitive enum handling.",
        "Tigs", "enum,migration,models",
    ),
    (
        BacklogItemType.BUG_FIX, HelixApplication.HELIXNET, BacklogStatus.DONE, BacklogPriority.HIGH,
        "BUG-010 upload images (MinIO + auth)",
        "Fix document preview auth -- use JS fetch with Bearer token for all doc ops.",
        "Tigs", "bug,minio,auth",
    ),
    (
        BacklogItemType.DEV_TASK, HelixApplication.HELIXNET, BacklogStatus.DONE, BacklogPriority.MEDIUM,
        "Multi-commit tracking for bugs",
        "BUG -> many commits tracking. BugCommitRead before BugReportRead (forward reference fix).",
        "Tigs", "qa,git,tracking",
    ),
    (
        BacklogItemType.DEV_TASK, HelixApplication.HELIXNET, BacklogStatus.DONE, BacklogPriority.MEDIUM,
        "Tigs Telegram bot",
        "Personal AI co-pilot via Telegram. Send messages, get responses.",
        "Tigs", "telegram,bot,ai",
    ),
    (
        BacklogItemType.BUSINESS_OPS, HelixApplication.ISOTTO, BacklogStatus.PENDING, BacklogPriority.MEDIUM,
        "Pizza Planet postcard print run",
        "4-UP portrait + landscape postcards for Ciccio's place. Ready for ISOTTO print.",
        "Angel", "postcard,isotto,pizza-planet",
    ),
    (
        BacklogItemType.BUSINESS_OPS, HelixApplication.ISOTTO, BacklogStatus.PENDING, BacklogPriority.MEDIUM,
        "Color Clean card set",
        "Design and print postcard set for Color Clean lavanderia, Via Virgilio.",
        "Angel", "postcard,isotto,color-clean",
    ),
    (
        BacklogItemType.BUSINESS_OPS, HelixApplication.ISOTTO, BacklogStatus.PENDING, BacklogPriority.LOW,
        "Piccolo Bistratto card set",
        "Design postcard set for Giovanni's place. Jonathan the chef, Paolo (friend).",
        "Angel", "postcard,isotto,piccolo-bistratto",
    ),
    (
        BacklogItemType.DEV_TASK, HelixApplication.HELIXNET, BacklogStatus.IN_PROGRESS, BacklogPriority.HIGH,
        "Unified backlog module",
        "One board to track everything: dev tasks, camper shop, business ops, bug fixes. Kanban + list view.",
        "Tigs", "backlog,kanban,dashboard",
    ),
]


async def seed_backlog_data(db: AsyncSession) -> None:
    """Seed initial backlog items. Idempotent -- skips if data exists."""
    count_result = await db.execute(
        select(func.count()).select_from(BacklogItemModel)
    )
    existing_count = count_result.scalar() or 0

    if existing_count > 0:
        logger.info(f"Backlog already seeded ({existing_count} items). Skipping.")
        return

    for idx, (item_type, application, status, priority, title, description, assigned_to, tags) in enumerate(SEED_ITEMS, start=1):
        item = BacklogItemModel(
            item_number=idx,
            item_type=item_type,
            application=application,
            status=status,
            priority=priority,
            title=title,
            description=description,
            assigned_to=assigned_to,
            tags=tags,
            created_by="Angel",
        )
        db.add(item)

    await db.flush()
    logger.info(f"Backlog seeded: {len(SEED_ITEMS)} items")
