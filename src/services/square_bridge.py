# File: src/services/square_bridge.py
# The Bottega <-> Square interface (read side) -- the iFlow between the two modules.
#
# ONE swappable boundary: today this reads the marketplace DB (`borrowhood`) read-only over
# the same Postgres instance; tomorrow it calls the marketplace API with a service key. The
# CONSUMER (routers, the Legends picker) never changes -- only the body of these functions.
# Reading the cast needs NO per-user identity link (it's a public browse); per-user writes
# (profile/items) need the identity link and live in a later slice (see SPEC-interface).

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import settings

logger = logging.getLogger("helix.square_bridge")

_engine = None


def _ro_engine():
    """Lazy read-only-by-discipline async engine to the marketplace DB (small pool)."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.SQUARE_ASYNC_URI, pool_size=2, max_overflow=2, pool_pre_ping=True,
        )
    return _engine


async def list_legends(q: str | None = None, limit: int = 400) -> list[dict]:
    """The cast: La Piazza legend personas to pick from in Ask-a-Master.
    Returns [{name, workshop, tagline, bio, ref}]. Read-only; never raises (returns [] on error)."""
    sql = (
        "SELECT display_name, workshop_name, tagline, bio, keycloak_id::text "
        "FROM bh_user WHERE display_name IS NOT NULL AND display_name <> '' "
    )
    params: dict = {}
    if q:
        sql += ("AND (display_name ILIKE :q OR workshop_name ILIKE :q "
                "OR bio ILIKE :q OR tagline ILIKE :q) ")
        params["q"] = f"%{q}%"
    sql += "ORDER BY display_name LIMIT :lim"
    params["lim"] = max(1, min(int(limit), 500))
    try:
        async with _ro_engine().connect() as conn:
            rows = (await conn.execute(text(sql), params)).fetchall()
    except Exception:  # noqa: BLE001
        logger.warning("square_bridge.list_legends failed", exc_info=True)
        return []
    return [
        {"name": r[0], "workshop": r[1] or "", "tagline": r[2] or "", "bio": r[3] or "", "ref": r[4]}
        for r in rows
    ]
