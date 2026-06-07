# File: src/routes/bottega_router.py
# Purpose: Bottega onboarding -- the "Pulse Check". Drop a CV -> AI proposes a profile
# (bio/tagline/skills/categories). ENRICH-SAFELY: /generate never persists; /apply
# snapshots the existing profile to history first, then writes. Nothing silently clobbered.

import json
import logging
import re
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings

from src.db.database import get_db_session
from src.db.models.bottega_model import (
    BottegaProfileModel, BottegaProfileHistoryModel, BottegaSessionModel)
from src.db.models.backlog_model import (
    BacklogItemModel, BacklogItemType, BacklogPriority)
from src.core.constants import HelixApplication
from uuid import UUID
from src.core.keycloak_auth import require_roles
from src.services.bottega_service import (
    extract_text, cv_to_bio, generate_cv, slugify, BrainUnavailable)
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


# ===== The one-motion Get Started: name + CV -> account + Bottega + auto-login =====
LP_REALM = settings.LP_REALM
LP_CLIENT = settings.LP_CLIENT


async def _kc_admin_token(c: httpx.AsyncClient) -> str:
    r = await c.post(f"{settings.KEYCLOAK_SERVER_URL}/realms/master/protocol/openid-connect/token",
                     data={"grant_type": "password", "client_id": "admin-cli",
                           "username": settings.KEYCLOAK_ADMIN_USER,
                           "password": settings.KEYCLOAK_ADMIN_PASSWORD.get_secret_value()})
    r.raise_for_status()
    return r.json()["access_token"]


async def _create_member(c: httpx.AsyncClient, tok: str, name: str, email: str, password: str) -> str:
    """Create a La Piazza member (the empty room). Returns the unique username."""
    h = {"Authorization": f"Bearer {tok}"}
    base = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{LP_REALM}"
    uname = root = slugify(name) or "member"
    n = 0
    while (await c.get(f"{base}/users", headers=h, params={"username": uname, "exact": "true"})).json():
        n += 1
        uname = f"{root}{n}"
    parts = name.strip().split()
    (await c.post(f"{base}/users", headers=h, json={
        "username": uname, "email": email or f"{uname}@lapiazza.local", "enabled": True,
        "emailVerified": True, "firstName": (parts[0] if parts else name)[:60],
        "lastName": (" ".join(parts[1:]) or "LaPiazza")[:60], "requiredActions": [],
        "credentials": [{"type": "password", "value": password, "temporary": False}],
    })).raise_for_status()
    uid = (await c.get(f"{base}/users", headers=h, params={"username": uname, "exact": "true"})).json()[0]["id"]
    role = (await c.get(f"{base}/roles/lapiazza-user", headers=h)).json()
    await c.post(f"{base}/users/{uid}/role-mappings/realm", headers=h, json=[role])
    return uname


async def _member_token(c: httpx.AsyncClient, username: str, password: str) -> str:
    r = await c.post(f"{settings.KEYCLOAK_SERVER_URL}/realms/{LP_REALM}/protocol/openid-connect/token",
                     data={"grant_type": "password", "client_id": LP_CLIENT, "username": username,
                           "password": password, "scope": "openid profile"})
    r.raise_for_status()
    return r.json()["access_token"]


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?<!\w)(?:\+\d{1,3}[\s.\-]?)?(?:\(?\d{2,4}\)?[\s.\-]?){2,4}\d{2,3}(?!\w)")
_URL_RE = re.compile(r"https?://[^\s)>\]]+")


def _scan_clues(text: str) -> dict:
    """Scan any input for clues worth keeping for later: emails, phones, links.
    (Skills + categories come from cv_to_bio.) This is the metadata the archive remembers."""
    emails = sorted(set(_EMAIL_RE.findall(text)))[:10]
    phones = []
    for m in _PHONE_RE.findall(text):
        if 7 <= len(re.sub(r"\D", "", m)) <= 15:
            phones.append(re.sub(r"\s+", " ", m).strip())
    links = [u for u in sorted(set(_URL_RE.findall(text))) if "lapiazza" not in u][:10]
    return {"emails": emails, "phones": sorted(set(phones))[:10], "links": links}


@router.post("/get-started")
async def get_started(name: str = Form(...), email: str = Form(""), password: str = Form(...),
                      about: str = Form(""), file: UploadFile = File(None),
                      db: AsyncSession = Depends(get_db_session)):
    """PUBLIC. The whole onboarding in one breath: tell us your name, and EITHER drop a
    CV OR just say what you do -- you walk out WITH a Bottega (account + profile + logged
    in). No CV required (most real people don't have one ready); a few honest sentences
    are enough. The account is the empty room, your words furnish it, one motion."""
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="pick a password of at least 6 characters")
    if file is not None and getattr(file, "filename", ""):
        source, text = "cv", extract_text(file.filename, await file.read())
    else:
        source, text = "about", (about or "").strip()
    if len(text.strip()) < 20:
        raise HTTPException(status_code=400,
                            detail="tell us a little more about what you do (a sentence or two), or drop a CV")
    proposal = await cv_to_bio(text, DEFAULT_CATEGORIES)   # bio/tagline/skills/categories
    async with httpx.AsyncClient(verify=False, timeout=30.0) as c:
        tok = await _kc_admin_token(c)
        try:
            username = await _create_member(c, tok, name, email, password)
        except httpx.HTTPStatusError as e:
            code = 409 if e.response.status_code == 409 else 400
            raise HTTPException(status_code=code, detail="couldn't create your account (name/email may be taken)")
        slug = await _unique_slug(db, slugify(name), username)
        profile = BottegaProfileModel(
            username=username, bio=proposal.get("bio"), tagline=proposal.get("tagline"),
            skills=json.dumps(proposal.get("skills", [])),
            categories=json.dumps(proposal.get("categories", [])),
            source="cv", status="applied", completeness=70, slug=slug)
        db.add(profile)
        # Block A: archive the raw input + scanned clues into the Blueprint Folder.
        # The first entry in the member's history -- the clues kept for later.
        clues = _scan_clues(text)
        db.add(BottegaSessionModel(
            username=username, slug="blueprint-archive",
            title=f"Onboarding archive · {name}"[:160],
            inputs=json.dumps({"raw": text[:8000], "source": source}),
            output=json.dumps({
                "bio": proposal.get("bio"), "tagline": proposal.get("tagline"),
                "skills": proposal.get("skills", []), "categories": proposal.get("categories", []),
                "emails": clues["emails"] or ([email] if email else []),
                "phones": clues["phones"], "links": clues["links"], "chars": len(text)}),
            output_type="json", tags="archive,onboarding"))
        await db.commit()
        await db.refresh(profile)
        token = await _member_token(c, username, password)   # auto-login: you're in
    return {"username": username, "slug": slug, "token": token, "profile": _view(profile)}


@router.get("/recipes")
async def recipes(current_user: dict = Depends(require_bottega_access())):
    """The Chinese menu -- every recipe + its input spec. Adding one = a dict entry."""
    return recipe_menu()


@router.get("/legends")
async def legends(q: str = "", current_user: dict = Depends(require_bottega_access())):
    """Legends-1: the Ask-a-Master cast, read from the Square via the square_bridge interface
    (read-only marketplace DB today; the marketplace API key later -- consumer unchanged)."""
    from src.services.square_bridge import list_legends
    items = await list_legends(q=q or None)
    return {"legends": items, "count": len(items)}


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
    except BrainUnavailable:
        raise HTTPException(status_code=503,
                            detail="This recipe's brain is busy right now — give it a moment and try again. (We're on it.)")
    # charge the fair price (only after a successful run) -- same ledger as jobs
    note = f"recipe · {slug}"
    await post_ledger(db, owner, ComputeLedgerKind.SPEND, -price, counterparty="la-bottega", note=note)
    await post_ledger(db, "la-bottega", ComputeLedgerKind.EARN, price, counterparty=owner, note=note)
    await db.commit()
    # Auto-save the structured intakes to the Blueprint spine -- the dashboard reads these
    # (the person-schema slices, not throwaway). One row per run; the dashboard takes latest.
    if slug in ("body-intake", "story-intake") and result.get("output_type") == "json":
        db.add(BottegaSessionModel(
            username=owner, slug=slug, title=RECIPES[slug].get("title", slug),
            inputs=json.dumps({k: v for k, v in raw.items() if isinstance(v, str)}),
            output=json.dumps(result.get("result", {})), output_type="json", tags="intake"))
        await db.commit()
    result["charged"] = price
    result["balance"] = await credit_balance(db, owner)
    return result


# ===== Blueprint Folder: a user's saved sessions (their cutover list) =====
class SaveSession(BaseModel):
    slug: str
    title: str
    inputs: dict = {}
    output: str = ""
    output_type: str = "markdown"
    tags: str | None = None
    parent_id: str | None = None


@router.post("/sessions")
async def save_session(body: SaveSession,
                       current_user: dict = Depends(require_bottega_access()),
                       db: AsyncSession = Depends(get_db_session)):
    """Save a session to my Blueprint Folder. parent_id => a new version (edit-and-rerun)."""
    version, parent = 1, None
    if body.parent_id:
        try:
            parent = UUID(body.parent_id)
            prev = await db.get(BottegaSessionModel, parent)
            if prev and prev.username == current_user["username"]:
                version = (prev.version or 1) + 1
        except Exception:  # noqa: BLE001
            parent = None
    s = BottegaSessionModel(
        username=current_user["username"], slug=body.slug, title=body.title[:160],
        inputs=json.dumps(body.inputs or {}), output=(body.output or "")[:200000],
        output_type=body.output_type, tags=body.tags, version=version, parent_id=parent)
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return {"id": str(s.id), "version": s.version, "saved": True}


@router.get("/sessions")
async def list_sessions(current_user: dict = Depends(require_bottega_access()),
                        db: AsyncSession = Depends(get_db_session)):
    """My Blueprint Folder -- newest first (lean: titles + questions, no full output)."""
    rows = (await db.execute(
        select(BottegaSessionModel)
        .where(BottegaSessionModel.username == current_user["username"])
        .order_by(BottegaSessionModel.created_at.desc()).limit(100))).scalars().all()
    return [{"id": str(s.id), "slug": s.slug, "title": s.title,
             "inputs": json.loads(s.inputs or "{}"), "version": s.version,
             "created_at": s.created_at.isoformat()} for s in rows]


@router.get("/sessions/{session_id}")
async def get_session(session_id: str,
                      current_user: dict = Depends(require_bottega_access()),
                      db: AsyncSession = Depends(get_db_session)):
    try:
        s = await db.get(BottegaSessionModel, UUID(session_id))
    except Exception:  # noqa: BLE001
        s = None
    if not s or s.username != current_user["username"]:
        raise HTTPException(status_code=404, detail="not found")
    return {"id": str(s.id), "slug": s.slug, "title": s.title,
            "inputs": json.loads(s.inputs or "{}"), "output": s.output,
            "output_type": s.output_type, "version": s.version,
            "created_at": s.created_at.isoformat()}


@router.get("/me")
async def me(current_user: dict = Depends(require_bottega_access()),
             db: AsyncSession = Depends(get_db_session)):
    return {"profile": _view(await _get(db, current_user["username"]))}


@router.get("/me/dashboard")
async def me_dashboard(current_user: dict = Depends(require_bottega_access()),
                       db: AsyncSession = Depends(get_db_session)):
    """The member's rebuild hub: profile + the person-schema slices (body/spirit) + the journey
    (workouts, mentors). Aggregated from the profile + the Blueprint spine. Read-only."""
    user = current_user["username"]
    rows = (await db.execute(
        select(BottegaSessionModel).where(BottegaSessionModel.username == user)
        .order_by(BottegaSessionModel.created_at.desc()).limit(200))).scalars().all()

    def _parse(s):
        out = s.output or ""
        if s.output_type == "json":
            try:
                out = json.loads(out)
            except Exception:  # noqa: BLE001
                out = {}
        return {"id": str(s.id), "slug": s.slug, "title": s.title,
                "created_at": s.created_at.isoformat() if s.created_at else "", "output": out}

    def latest(slug):
        return next((_parse(s) for s in rows if s.slug == slug), None)

    def all_of(slug):
        return [_parse(s) for s in rows if s.slug == slug]

    return {
        "username": user,
        "profile": _view(await _get(db, user)),
        "body": latest("body-intake"),
        "spirit": latest("story-intake"),
        "workouts": all_of("workout-plan"),
        "mentors": all_of("mentor-session"),
        "archive": latest("blueprint-archive"),
        "total": len(rows),
    }


# ===== Blocks C + D: notifications + messages (the dark-workshop social layer, on the spine) =====
class Message(BaseModel):
    to: str
    body: str
    subject: str = ""


def _inbox_brief(s: BottegaSessionModel) -> dict:
    try:
        inp = json.loads(s.inputs or "{}")
    except Exception:  # noqa: BLE001
        inp = {}
    return {"id": str(s.id), "kind": s.slug, "title": s.title, "from": inp.get("from", ""),
            "read": bool(inp.get("read", False)), "body": s.output,
            "created_at": s.created_at.isoformat() if s.created_at else ""}


@router.post("/message")
async def send_message(m: Message, current_user: dict = Depends(require_bottega_access()),
                       db: AsyncSession = Depends(get_db_session)):
    """Send a member a message (+ a notification). The equalizer's nudge runs through here too."""
    sender = current_user["username"]
    db.add(BottegaSessionModel(
        username=m.to, slug="message", title=(m.subject or f"Message from {sender}")[:160],
        inputs=json.dumps({"from": sender, "read": False}), output=(m.body or "")[:8000],
        output_type="text", tags="message"))
    db.add(BottegaSessionModel(
        username=m.to, slug="notification", title=f"💬 {sender}",
        inputs=json.dumps({"read": False}), output=(m.subject or (m.body or "")[:80]),
        output_type="text", tags="notification"))
    await db.commit()
    return {"sent": True, "to": m.to}


@router.get("/me/inbox")
async def me_inbox(current_user: dict = Depends(require_bottega_access()),
                   db: AsyncSession = Depends(get_db_session)):
    """My messages + notifications (newest first) + unread count."""
    user = current_user["username"]
    rows = (await db.execute(
        select(BottegaSessionModel)
        .where(BottegaSessionModel.username == user,
               BottegaSessionModel.slug.in_(["message", "notification"]))
        .order_by(BottegaSessionModel.created_at.desc()).limit(100))).scalars().all()
    items = [_inbox_brief(s) for s in rows]
    unread = sum(1 for i in items if i["kind"] == "message" and not i["read"])
    return {"items": items, "unread": unread}


@router.post("/me/inbox/{item_id}/read")
async def mark_read(item_id: str, current_user: dict = Depends(require_bottega_access()),
                    db: AsyncSession = Depends(get_db_session)):
    try:
        s = await db.get(BottegaSessionModel, UUID(item_id))
    except Exception:  # noqa: BLE001
        s = None
    if s and s.username == current_user["username"]:
        try:
            inp = json.loads(s.inputs or "{}")
        except Exception:  # noqa: BLE001
            inp = {}
        inp["read"] = True
        s.inputs = json.dumps(inp)
        await db.commit()
    return {"ok": True}


# ===== Block G: Feedback widget -> files into the Backlog (BL) board =====
class Feedback(BaseModel):
    kind: str = "other"      # bug | idea | other
    title: str
    body: str = ""


@router.post("/feedback")
async def feedback(f: Feedback, current_user: dict = Depends(require_bottega_access()),
                   db: AsyncSession = Depends(get_db_session)):
    """The seatback card, built in. A member reports a bug/idea from inside the workshop;
    it lands as a real item on the existing Backlog board (/backlog) for Angel to triage."""
    title = (f.title or "").strip()
    if len(title) < 3:
        raise HTTPException(status_code=400, detail="give it a short title (3+ characters)")
    user = current_user["username"]
    kind = (f.kind or "other").lower()
    if kind not in ("bug", "idea", "other"):
        kind = "other"
    item_type = BacklogItemType.BUG_FIX if kind == "bug" else BacklogItemType.BUSINESS_OPS
    # next BL number -- same scheme as backlog_router.create_item
    next_number = (await db.execute(
        select(func.coalesce(func.max(BacklogItemModel.item_number), 0)))).scalar() + 1
    body = (f.body or "").strip()
    desc = (f"{body}\n\n— filed from Bottega by {user}" if body
            else f"Filed from Bottega by {user}")
    item = BacklogItemModel(
        item_number=next_number, title=title[:200], description=desc,
        item_type=item_type, application=HelixApplication.HELIXNET,
        priority=BacklogPriority.MEDIUM, created_by=user,
        tags=f"bottega,feedback,{kind}")
    db.add(item)
    await db.commit()
    logger.info(f"BL-{next_number:03d} filed from Bottega by {user}: {title}")
    return {"ok": True, "item_number": next_number, "ref": f"BL-{next_number:03d}"}


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
