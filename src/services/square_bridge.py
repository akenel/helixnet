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
import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import settings

logger = logging.getLogger("helix.square_bridge")

_engine = None

# Legends-2: the fixed House taxonomy (the model ASSIGNS into these; it doesn't invent houses).
HOUSES = [
    ("The Forge", "engineers, inventors, makers"),
    ("The Atelier", "artists, designers, architects, filmmakers"),
    ("The Lyceum", "scientists, mathematicians, philosophers"),
    ("The Strategoi", "strategists, leaders, warriors"),
    ("The Scriptorium", "writers, poets, storytellers"),
    ("The Agora", "merchants, entrepreneurs, builders of commerce"),
    ("The Hearth", "everyday masters: cooks, gardeners, craftspeople"),
    ("The Observatory", "explorers, navigators, astronomers"),
    ("The Conservatory", "musicians, composers, performers"),
    ("The Sanctuary", "healers, teachers, spiritual guides"),
]
HOUSE_NAMES = [h[0] for h in HOUSES]
DEFAULT_HOUSE = "The Hearth"


def _norm(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def apply_houses(legends: list[dict], hmap: dict) -> list[dict]:
    """Enrich each legend with its House + dedupe by canonical person (keep the richest bio).
    hmap: {legend_name: {"house":.., "canonical":..}}. Empty hmap => all default house, dedupe by name."""
    seen: dict[str, dict] = {}
    for lg in legends:
        meta = hmap.get(lg["name"]) or {}
        house = meta.get("house") if meta.get("house") in HOUSE_NAMES else DEFAULT_HOUSE
        canon = meta.get("canonical") or lg["name"]
        out = {**lg, "house": house, "canonical": canon}
        key = _norm(canon)
        if key and (key not in seen or len(out["bio"]) > len(seen[key]["bio"])):
            seen[key] = out
    return sorted(seen.values(), key=lambda x: x["name"])


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


async def get_square_profile(keycloak_id: str | None) -> dict | None:
    """State-2 import: read a member's existing Square (marketplace) profile by their KC sub,
    so the Bottega can be seeded from it. Returns None if no profile / on error."""
    if not keycloak_id:
        return None
    try:
        async with _ro_engine().connect() as conn:
            row = (await conn.execute(text(
                "SELECT display_name, slug, workshop_name, tagline, bio, city "
                "FROM bh_user WHERE keycloak_id = :kid LIMIT 1"), {"kid": keycloak_id})).fetchone()
    except Exception:  # noqa: BLE001
        logger.warning("square_bridge.get_square_profile failed", exc_info=True)
        return None
    if not row:
        return None
    return {"display_name": row[0] or "", "slug": row[1] or "", "workshop": row[2] or "",
            "tagline": row[3] or "", "bio": row[4] or "", "city": row[5] or ""}
