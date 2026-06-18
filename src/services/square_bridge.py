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

import httpx
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

# The board is masters only. badge_tier='LEGEND' marks every seeded master persona (all carry
# synthetic @borrowhood.local emails; no real signup is ever LEGEND). But a few REAL people were
# seeded as LEGEND personas -- Angel's family. Legends to him, not public master-board figures.
# Governed denylist (master-data discipline): explicit, honest, extend as curation finds more.
# NOTE (v3, banked): living members could one day be dispatch targets by demonstrated expertise
# (e.g. ask Sally the cook for a recipe) -- with consent + a reply loop. Out of scope for now.
REAL_PEOPLE_EMAILS = {
    "dave.kenel@borrowhood.local",
    "mario.kenel@borrowhood.local",
    "paul.kenel@borrowhood.local",
}


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


async def list_legends(q: str | None = None, limit: int = 400, masters_only: bool = True) -> list[dict]:
    """The cast: La Piazza legend personas to pick from in Ask-a-Master / the dispatcher.
    masters_only (default True): only badge_tier='LEGEND' personas, minus REAL_PEOPLE_EMAILS
    (family seeded as legends). This is THE board -- the dispatcher must never route elsewhere.
    Returns [{name, workshop, tagline, bio, ref}]. Read-only; never raises (returns [] on error)."""
    sql = (
        "SELECT display_name, workshop_name, tagline, bio, keycloak_id::text, email "
        "FROM bh_user WHERE display_name IS NOT NULL AND display_name <> '' "
    )
    params: dict = {}
    if masters_only:
        sql += "AND badge_tier::text = 'LEGEND' "
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
    deny = REAL_PEOPLE_EMAILS if masters_only else set()
    return [
        {"name": r[0], "workshop": r[1] or "", "tagline": r[2] or "", "bio": r[3] or "", "ref": r[4]}
        for r in rows
        if (r[5] or "").lower() not in deny
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


# --- WRITE side: the Cleo draft-listing bridge (per-user, identity-linked) -------------------
# This is the "later slice" the header promised. We call the marketplace API server-to-server,
# carrying the MEMBER's own token (principal propagation) -- valid cross-app because both apps
# now share ONE Keycloak realm (borrowhood). BorrowHood verifies the token + acts as the user,
# JIT-relinking by username. Output is always a DRAFT (invisible) with a default cover, so the
# member opens La Piazza to a tidy, image-bearing listing ready to review and publish.

class SquareBridgeError(Exception):
    """A friendly, surfaced failure from the marketplace write bridge."""


async def create_draft_listing(user_token: str, d: dict) -> dict:
    """Create item -> default cover -> DRAFT listing in La Piazza, AS the member (their token).
    `d` carries the listing fields (name/description/story/item_type/listing_type/category/
    subcategory/condition/tags/price/price_unit/currency/cover_url/content_language).
    Returns {item_id, listing_id, slug, status, view_url, cover}. Raises SquareBridgeError."""
    if not (user_token or "").strip():
        raise SquareBridgeError("not signed in")
    name = (d.get("name") or "").strip()
    if len(name) < 2:
        raise SquareBridgeError("the listing needs a name")
    h = {"Authorization": f"Bearer {user_token}"}
    cover = (d.get("cover_url") or "").strip() or f"{settings.SQUARE_PUBLIC_URL}/static/og-default.png"
    item_body = {
        "name": name[:200],
        "description": (d.get("description") or "")[:5000],
        "story": (d.get("story") or "")[:5000],
        "content_language": (d.get("content_language") or "en")[:5],
        "item_type": d.get("item_type") or "service",
        "category": (d.get("category") or "services")[:50],
        "subcategory": (d.get("subcategory") or "")[:50],
        "tags": (d.get("tags") or "")[:300],
    }
    if d.get("condition"):
        item_body["condition"] = d["condition"]
    listing_body = {
        "item_id": None,  # filled after item create
        "listing_type": d.get("listing_type") or "service",
        "status": "draft",
        "currency": (d.get("currency") or "EUR")[:3],
        "notes": (d.get("notes") or "Drafted by Cleo — review and publish when you're ready.")[:500],
    }
    if d.get("price") not in (None, ""):
        try:
            listing_body["price"] = float(d["price"])
            if d.get("price_unit"):
                listing_body["price_unit"] = str(d["price_unit"])[:20]
        except (TypeError, ValueError):
            pass
    try:
        async with httpx.AsyncClient(base_url=settings.SQUARE_API_URL, verify=False, timeout=30.0) as c:
            r = await c.post("/api/v1/items", headers=h, json=item_body)
            if r.status_code == 401:
                raise SquareBridgeError("your session can't post to La Piazza yet — try signing in again")
            if r.status_code != 201:
                raise SquareBridgeError(f"couldn't create the listing ({r.status_code})")
            item = r.json()
            iid, slug = item.get("id"), item.get("slug")
            # cover is best-effort: a draft without it is still fine, just plainer
            try:
                await c.post(f"/api/v1/items/{iid}/media", headers=h,
                             json={"url": cover, "alt_text": "Replace with your photo", "media_type": "photo"})
            except Exception:  # noqa: BLE001
                logger.warning("square_bridge: cover attach failed for item %s", iid, exc_info=True)
            listing_body["item_id"] = iid
            r = await c.post("/api/v1/listings", headers=h, json=listing_body)
            if r.status_code != 201:
                raise SquareBridgeError(f"created the item but couldn't draft the listing ({r.status_code})")
            listing = r.json()
    except SquareBridgeError:
        raise
    except Exception as e:  # noqa: BLE001
        logger.warning("square_bridge.create_draft_listing failed", exc_info=True)
        raise SquareBridgeError(f"the marketplace is unreachable right now ({str(e)[:80]})")
    return {
        "item_id": iid, "listing_id": listing.get("id"), "slug": slug, "status": "draft",
        "view_url": f"{settings.SQUARE_PUBLIC_URL}/items/{slug}", "cover": cover,
    }
