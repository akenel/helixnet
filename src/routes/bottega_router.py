# File: src/routes/bottega_router.py
# Purpose: Bottega onboarding -- the "Pulse Check". Drop a CV -> AI proposes a profile
# (bio/tagline/skills/categories). ENRICH-SAFELY: /generate never persists; /apply
# snapshots the existing profile to history first, then writes. Nothing silently clobbered.

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db_session
from src.db.models.bottega_model import BottegaProfileModel, BottegaProfileHistoryModel
from src.core.keycloak_auth import require_roles
from src.services.bottega_service import extract_text, cv_to_bio, generate_cv, slugify
from src.services.compute_service import credit_balance, post_ledger, ensure_starter_grant
from src.db.models.compute_model import ComputeLedgerKind
from src.compute.recipes import RECIPES, menu as recipe_menu, run_recipe

logger = logging.getLogger("helix.bottega_router")
router = APIRouter(prefix="/api/v1/compute/bottega", tags=["Bottega - Onboarding"])


def require_bottega_access():
    return require_roles(["camper-qa-tester", "camper-manager", "camper-admin",
                          "lapiazza-user", "lapiazza-admin"])


# Placeholder taxonomy -- snap to La Piazza's real listing categories later.
DEFAULT_CATEGORIES = [
    "enterprise integration", "software development", "cloud & devops",
    "technical consulting", "training & mentoring", "design",
    "photography", "decor & textile", "events", "translation",
]


class Proposal(BaseModel):
    bio: str = ""
    tagline: str = ""
    skills: list[str] = []
    categories: list[str] = []
    slug: str | None = None   # optional public handle (e.g. thesapspecialist)


class ProfileView(BaseModel):
    username: str
    slug: str | None = None
    bio: str | None = None
    tagline: str | None = None
    skills: list[str] = []
    categories: list[str] = []
    source: str = "manual"
    status: str = "applied"
    completeness: int = 0


def _view(p: BottegaProfileModel | None) -> ProfileView | None:
    if not p:
        return None
    return ProfileView(
        username=p.username, slug=p.slug, bio=p.bio, tagline=p.tagline,
        skills=json.loads(p.skills or "[]"), categories=json.loads(p.categories or "[]"),
        source=p.source, status=p.status, completeness=p.completeness,
    )


async def _unique_slug(db: AsyncSession, desired: str, username: str) -> str:
    """Slugify + guarantee uniqueness (append a suffix if another user owns it)."""
    base = slugify(desired)
    taken = (await db.execute(
        select(BottegaProfileModel).where(
            BottegaProfileModel.slug == base, BottegaProfileModel.username != username)
    )).scalar_one_or_none()
    return f"{base}-{slugify(username)[:6]}" if taken else base


async def _get(db: AsyncSession, username: str) -> BottegaProfileModel | None:
    return (await db.execute(
        select(BottegaProfileModel).where(BottegaProfileModel.username == username)
    )).scalar_one_or_none()


@router.get("/recipes")
async def recipes(current_user: dict = Depends(require_bottega_access())):
    """The Chinese menu -- every recipe + its input spec. Adding one = a dict entry."""
    return recipe_menu()


@router.post("/recipes/{slug}/run")
async def recipes_run(slug: str, request: Request,
                      current_user: dict = Depends(require_bottega_access()),
                      db: AsyncSession = Depends(get_db_session)):
    """Generic recipe runner -- one endpoint executes any recipe. UNIFIED ECONOMY:
    a recipe run is charged its fair price (est_credits) through the same ledger as
    jobs, so making things costs the same everywhere."""
    if slug not in RECIPES:
        raise HTTPException(status_code=404, detail=f"unknown recipe '{slug}'")
    owner = current_user["username"]
    price = int(RECIPES[slug].get("est_credits", 1))
    await ensure_starter_grant(db, owner)
    bal = await credit_balance(db, owner)
    if bal < price:
        raise HTTPException(status_code=402,
                            detail=f"not enough credits -- '{slug}' costs {price}, you have {bal}")
    form = await request.form()
    raw: dict = {}
    for inp in RECIPES[slug]["inputs"]:
        name = inp["name"]
        if inp["type"] == "file":
            up = form.get(name)
            if up is not None and hasattr(up, "read"):
                raw[name] = (up.filename or "upload", await up.read())
        else:
            raw[name] = form.get(name)
    try:
        result = await run_recipe(slug, raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # charge the fair price (only after a successful run) -- same ledger as jobs
    note = f"recipe · {slug}"
    await post_ledger(db, owner, ComputeLedgerKind.SPEND, -price, counterparty="la-bottega", note=note)
    await post_ledger(db, "la-bottega", ComputeLedgerKind.EARN, price, counterparty=owner, note=note)
    await db.commit()
    result["charged"] = price
    result["balance"] = await credit_balance(db, owner)
    return result


@router.get("/me")
async def me(current_user: dict = Depends(require_bottega_access()),
             db: AsyncSession = Depends(get_db_session)):
    return {"profile": _view(await _get(db, current_user["username"]))}


@router.post("/generate")
async def generate(file: UploadFile = File(...),
                   current_user: dict = Depends(require_bottega_access()),
                   db: AsyncSession = Depends(get_db_session)):
    """Read the CV, propose a profile. Does NOT persist -- returns proposal + current
    so the UI can show current-vs-proposed before the user confirms."""
    data = await file.read()
    text = extract_text(file.filename or "cv", data)
    if len(text.strip()) < 20:
        raise HTTPException(status_code=400, detail="couldn't read any text from that file")
    result = await cv_to_bio(text, DEFAULT_CATEGORIES)
    return {
        "current": _view(await _get(db, current_user["username"])),
        "proposed": result,
    }


@router.post("/generate-cv")
async def generate_cv_ep(file: UploadFile = File(...),
                         target_role: str = Form(""),
                         style: str = Form("concise"),
                         current_user: dict = Depends(require_bottega_access()),
                         db: AsyncSession = Depends(get_db_session)):
    """Recipe cv-generate: source CV (+ optional target role) -> tailored CV Markdown.
    Supports career pivots (re-frames transferable experience, names the gaps)."""
    data = await file.read()
    text = extract_text(file.filename or "cv", data)
    if len(text.strip()) < 20:
        raise HTTPException(status_code=400, detail="couldn't read any text from that file")
    md = await generate_cv(text, target_role, style)
    return {"target_role": target_role or None, "cv_markdown": md}


@router.post("/apply")
async def apply(payload: Proposal,
                current_user: dict = Depends(require_bottega_access()),
                db: AsyncSession = Depends(get_db_session)):
    """Confirm: snapshot the existing profile (undo), then write the new one."""
    username = current_user["username"]
    existing = await _get(db, username)
    if existing:
        # NEVER silently clobber -- snapshot first.
        db.add(BottegaProfileHistoryModel(
            username=username,
            snapshot=json.dumps(_view(existing).model_dump()),
            reason="pre-apply snapshot (cv-to-bio)",
        ))
        existing.bio = payload.bio
        existing.tagline = payload.tagline
        existing.skills = json.dumps(payload.skills)
        existing.categories = json.dumps(payload.categories)
        existing.source = "cv"
        existing.status = "applied"
        existing.completeness = min(100, max(existing.completeness, 70))
        profile = existing
    else:
        profile = BottegaProfileModel(
            username=username, bio=payload.bio, tagline=payload.tagline,
            skills=json.dumps(payload.skills), categories=json.dumps(payload.categories),
            source="cv", status="applied", completeness=70,
        )
        db.add(profile)
    # handle/slug: custom if given, else slugified username (kept once set)
    if payload.slug or not profile.slug:
        profile.slug = await _unique_slug(db, payload.slug or username, username)
    await db.commit()
    await db.refresh(profile)
    return {"profile": _view(profile), "points": profile.completeness,
            "slug": profile.slug, "url": f"/u/{profile.slug}"}


@router.post("/undo")
async def undo(current_user: dict = Depends(require_bottega_access()),
               db: AsyncSession = Depends(get_db_session)):
    """Restore the most recent snapshot (the never-clobber promise, made real)."""
    username = current_user["username"]
    snap = (await db.execute(
        select(BottegaProfileHistoryModel)
        .where(BottegaProfileHistoryModel.username == username)
        .order_by(BottegaProfileHistoryModel.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    if not snap:
        raise HTTPException(status_code=404, detail="nothing to undo")
    prior = json.loads(snap.snapshot)
    profile = await _get(db, username)
    if profile:
        profile.bio = prior.get("bio")
        profile.tagline = prior.get("tagline")
        profile.skills = json.dumps(prior.get("skills", []))
        profile.categories = json.dumps(prior.get("categories", []))
        await db.commit()
        await db.refresh(profile)
    return {"profile": _view(profile), "restored_from": snap.created_at.isoformat()}
