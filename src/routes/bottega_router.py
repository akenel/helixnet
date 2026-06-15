# File: src/routes/bottega_router.py
# Purpose: Bottega onboarding -- the "Pulse Check". Drop a CV -> AI proposes a profile
# (bio/tagline/skills/categories). ENRICH-SAFELY: /generate never persists; /apply
# snapshots the existing profile to history first, then writes. Nothing silently clobbered.

import asyncio
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
    BottegaProfileModel, BottegaProfileHistoryModel, BottegaSessionModel, BottegaTaskModel)
from src.db.models.backlog_model import (
    BacklogItemModel, BacklogItemType, BacklogPriority)
from src.core.constants import HelixApplication
from uuid import UUID, uuid4
from src.core.keycloak_auth import require_roles
from src.services.bottega_service import (
    extract_text, cv_to_bio, generate_cv, slugify, BrainUnavailable)
from src.services.compute_service import credit_balance, post_ledger, ensure_starter_grant
from src.db.models.compute_model import ComputeLedgerKind
from src.compute.recipes import RECIPES, menu as recipe_menu, run_recipe
from src.compute import concierge as cg
from src.compute import dispatcher as dsp

logger = logging.getLogger("helix.bottega_router")

# The Concierge stores ONE row per member on the shared session spine: the structured
# master-record + the running transcript, kept together (slug below).
CONCIERGE_SLUG = "concierge-record"
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
    """Slugify + guarantee uniqueness. Loops -2, -3 … until the slug is actually free, so two
    members with the same name (or a leftover/orphan profile) can't collide -> 500 on signup."""
    base = slugify(desired) or "member"
    candidate, n = base, 1
    while True:
        clash = (await db.execute(
            select(BottegaProfileModel).where(
                BottegaProfileModel.slug == candidate, BottegaProfileModel.username != username)
        )).scalar_one_or_none()
        if not clash:
            return candidate
        n += 1
        candidate = f"{base}-{n}"


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
                      tos_accepted: str = Form(""), age_confirmed: str = Form(""),
                      db: AsyncSession = Depends(get_db_session)):
    """PUBLIC. The whole onboarding in one breath: tell us your name, and EITHER drop a
    CV OR just say what you do -- you walk out WITH a Bottega (account + profile + logged
    in). No CV required (most real people don't have one ready); a few honest sentences
    are enough. The account is the empty room, your words furnish it, one motion."""
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="pick a password of at least 6 characters")
    # Age & Terms gate — foundational + SERVER-enforced (the UI checkboxes alone can be bypassed).
    _yes = ("1", "true", "on", "yes")
    if str(age_confirmed).strip().lower() not in _yes:
        raise HTTPException(status_code=400, detail="You must confirm you are 16 or older to join La Piazza.")
    if str(tos_accepted).strip().lower() not in _yes:
        raise HTTPException(status_code=400, detail="You must accept the Terms & Conditions to join.")
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
        # WW-1 — Warm welcome: Cleopatra greets the new member in their inbox right away,
        # referencing what she already learned from their CV/words and pointing to the next
        # step (the card she keeps fills via a short chat -> then she matches them to masters).
        _first = (name.strip().split() or [name])[0]
        _sk = proposal.get("skills", []) or []
        _seen = proposal.get("tagline") or (proposal.get("bio") or "")[:140] or "a real set of skills"
        _wbody = (
            f"Welcome to La Piazza, {_first}. I'm Cleopatra — your host here.\n\n"
            f"I read what you shared, and here's what I already see in you:\n"
            f"  • {_seen}\n"
            + (f"  • Strengths: {', '.join(_sk[:5])}\n" if _sk else "")
            + "\nYour profile is started. The real key is the card I keep on you — it's what lets "
            "every master here help you fast. Give me two minutes and we'll sharpen it together, "
            "then I'll point you to the masters who fit you best.\n\n"
            "I'm here to help you find your way — and you'll help me make this place better. Deal?\n\n"
            "When you're ready, tap 👑 Ask Cleo at the top and just tell me what you're after."
        )
        _deliver_message(db, to=username, sender="Cleopatra",
                         subject="Welcome — let's build your card", body=_wbody, icon="👑")
        await db.commit()
        await db.refresh(profile)
        token = await _member_token(c, username, password)   # auto-login: you're in
    profile_view = _view(profile)   # snapshot BEFORE write_concierge commits (else profile re-expires -> MissingGreenlet)
    # WW-4: seed Cleopatra's card from the CV so she starts off KNOWING the member — not a blank
    # "say hello". Same extraction the chat uses; empty transcript so her greeting still opens fresh,
    # but "What Cleopatra has learned" is already filled from what they gave at the door.
    try:
        extracted = await cg.extract_record([{"role": "member", "content": text}])
        seed = cg.merge_record(cg.blank_record(), extracted)
        seed = cg.stamp_provenance(seed, extracted)   # v2: every CV-seeded fact carries its source
        await write_concierge(db, username, seed, [])
    except Exception:  # noqa: BLE001 — card-seeding must NEVER break signup
        logger.warning("concierge card seed from CV failed for %s", username, exc_info=True)
    return {"username": username, "slug": slug, "token": token, "profile": profile_view}


@router.get("/recipes")
async def recipes():
    """The Chinese menu -- every recipe + its input spec. PUBLIC: the menu is a catalog (no
    user data), so anyone can see the smorgasbord without logging in -- 'look around free.'
    Running a recipe (/recipes/{slug}/run) stays gated; only browsing the menu is open."""
    return recipe_menu()


async def _house_map(db: AsyncSession) -> dict:
    """Load the cached {name: {house, canonical}} map from the spine (Legends-2)."""
    row = (await db.execute(select(BottegaSessionModel).where(
        BottegaSessionModel.username == "system",
        BottegaSessionModel.slug == "legend-houses"))).scalar_one_or_none()
    try:
        return json.loads(row.output) if row and row.output else {}
    except Exception:  # noqa: BLE001
        return {}


@router.get("/legends")
async def legends(q: str = "", house: str = "",
                  current_user: dict = Depends(require_bottega_access()),
                  db: AsyncSession = Depends(get_db_session)):
    """Legends-1/2: the Ask-a-Master cast (read via square_bridge), enriched with Houses +
    de-duplicated by canonical person (cached map from the spine). Optional q / house filter."""
    from src.services.square_bridge import list_legends, apply_houses
    cast = await list_legends(q=q or None, limit=500)
    enriched = apply_houses(cast, await _house_map(db))
    if house:
        enriched = [lg for lg in enriched if lg["house"] == house]
    return {"legends": enriched, "count": len(enriched)}


@router.get("/legends/houses")
async def legends_houses(current_user: dict = Depends(require_bottega_access()),
                         db: AsyncSession = Depends(get_db_session)):
    """The Houses + a live count each (for the picker drill-down)."""
    from src.services.square_bridge import list_legends, apply_houses, HOUSES
    enriched = apply_houses(await list_legends(limit=500), await _house_map(db))
    counts: dict = {}
    for lg in enriched:
        counts[lg["house"]] = counts.get(lg["house"], 0) + 1
    return {"houses": [{"name": n, "desc": d, "count": counts.get(n, 0)} for n, d in HOUSES],
            "total": len(enriched)}


@router.post("/legends/classify")
async def legends_classify(current_user: dict = Depends(require_bottega_access()),
                           db: AsyncSession = Depends(get_db_session)):
    """Legends-2 one-time pass: AI assigns each legend a House + canonical name (dedupe),
    cached on the spine. Idempotent (re-runnable). Batched to keep prompts sane."""
    from src.services.square_bridge import list_legends, HOUSES, HOUSE_NAMES
    from src.services.bottega_service import _brain_chat
    cast = await list_legends(limit=500)
    if not cast:
        raise HTTPException(status_code=503, detail="couldn't read the cast from the Square")
    houses_txt = "; ".join(f"{n} ({d})" for n, d in HOUSES)

    def _parse(raw: str) -> dict:
        raw = re.sub(r"<think>.*?</think>", "", raw or "", flags=re.S)
        raw = re.sub(r"```(?:json)?", "", raw).strip()
        a, b = raw.find("{"), raw.rfind("}")
        return json.loads(raw[a:b + 1]) if a >= 0 and b > a else {}

    hmap: dict = {}
    BATCH = 40
    for i in range(0, len(cast), BATCH):
        chunk = cast[i:i + BATCH]
        listing = "\n".join(f"- {c['name']} — {(c.get('tagline') or '')[:80]}" for c in chunk)
        sys = ("Assign each historical figure/master to EXACTLY ONE House and give their canonical "
               "real-person name so duplicates merge (e.g. 'Ada King, Countess of Lovelace' and "
               "'Ada Lovelace' both -> 'Ada Lovelace'). Respond with ONLY JSON of the form "
               '{"assignments":[{"name":"<as given>","house":"<one House name>","canonical":"<real name>"}]}. '
               f"Use these EXACT House names: {houses_txt}.")
        usr = f"Classify:\n{listing}"
        try:
            data = _parse(await _brain_chat(sys, usr, json_mode=True))
            for a in data.get("assignments", []):
                nm = a.get("name")
                if nm:
                    h = a.get("house")
                    hmap[nm] = {"house": h if h in HOUSE_NAMES else None,
                                "canonical": a.get("canonical") or nm}
        except Exception:  # noqa: BLE001
            logger.warning("legends classify batch %d failed", i, exc_info=True)
    row = (await db.execute(select(BottegaSessionModel).where(
        BottegaSessionModel.username == "system",
        BottegaSessionModel.slug == "legend-houses"))).scalar_one_or_none()
    payload = json.dumps(hmap)
    if row:
        row.output = payload
    else:
        db.add(BottegaSessionModel(username="system", slug="legend-houses", title="Legend Houses",
                                   inputs="{}", output=payload, output_type="json", tags="legends,houses"))
    await db.commit()
    return {"classified": len(hmap), "of": len(cast)}


@router.get("/legends/questions")
async def legend_questions(name: str, current_user: dict = Depends(require_bottega_access()),
                           db: AsyncSession = Depends(get_db_session)):
    """Legends-4: 3 starter questions to ask THIS master (AI, lazily cached per master on the spine)."""
    from src.services.bottega_service import _brain_chat
    name = (name or "").strip()
    if not name:
        return {"questions": []}
    # Personalized (the pre-call): if we know the person, suggest questions that bridge THIS master
    # to THEIR real situation (cookie-seller -> cookie questions). Fresh, not cached. Newcomers -> generic.
    try:
        portrait = await _build_portrait(db, current_user["username"])
    except Exception:  # noqa: BLE001
        portrait = ""
    if portrait and not portrait.startswith("A newcomer"):
        try:
            raw = await _brain_chat(
                "Suggest what THIS specific person would bring to THIS historical master. Respond "
                'ONLY JSON: {"questions":["q1","q2","q3"]} -- exactly 3 short, first-person questions '
                "that connect the master's real craft/wisdom to the person's ACTUAL situation, work, "
                "or goal. Hand-picked for this person, never generic.",
                f"Master: {name}\nThe person: {portrait}", json_mode=True)
            raw = re.sub(r"<think>.*?</think>", "", raw or "", flags=re.S)
            a, b = raw.find("{"), raw.rfind("}")
            if a >= 0 and b > a:
                pq = [str(q).strip() for q in json.loads(raw[a:b + 1]).get("questions", [])
                      if str(q).strip()][:3]
                if pq:
                    return {"questions": pq, "personalized": True}
        except Exception:  # noqa: BLE001
            logger.warning("personalized legend_questions failed for %s", name, exc_info=True)
    row = (await db.execute(select(BottegaSessionModel).where(
        BottegaSessionModel.username == "system",
        BottegaSessionModel.slug == "legend-questions"))).scalar_one_or_none()
    try:
        cache = json.loads(row.output) if row and row.output else {}
    except Exception:  # noqa: BLE001
        cache = {}
    if cache.get(name):
        return {"questions": cache[name][:3], "cached": True}
    qs: list = []
    try:
        raw = await _brain_chat(
            "Suggest what a person would bring to a historical master for mentoring. Respond with "
            'ONLY JSON: {"questions":["...","...","..."]} -- exactly 3 short, specific, first-person '
            "questions someone would actually ask THIS master (grounded in their real craft).",
            f"Master: {name}", json_mode=True)
        raw = re.sub(r"<think>.*?</think>", "", raw or "", flags=re.S)
        a, b = raw.find("{"), raw.rfind("}")
        if a >= 0 and b > a:
            qs = [str(q).strip() for q in json.loads(raw[a:b + 1]).get("questions", []) if str(q).strip()][:3]
    except Exception:  # noqa: BLE001
        logger.warning("legend_questions gen failed for %s", name, exc_info=True)
    if not qs:
        qs = ["What's the one thing you wish someone had taught you early?",
              "What mistake should I avoid that you learned the hard way?",
              "Where should I even start?"]
    cache[name] = qs
    if row:
        row.output = json.dumps(cache)
    else:
        db.add(BottegaSessionModel(username="system", slug="legend-questions", title="Legend Questions",
                                   inputs="{}", output=json.dumps(cache), output_type="json", tags="legends,questions"))
    await db.commit()
    return {"questions": qs}


# --- The Concierge: persist (Phase 1) + the conversational endpoint (Phase 2) -----------------

async def read_concierge(db: AsyncSession, username: str) -> dict:
    """Read the member's Concierge state -- {record, transcript}. A blank, fully-defaulted record
    if they've never spoken to the Concierge."""
    # newest-wins: tolerate >1 row (legacy dup-write or a race) instead of 500ing on the member.
    row = (await db.execute(select(BottegaSessionModel).where(
        BottegaSessionModel.username == username,
        BottegaSessionModel.slug == CONCIERGE_SLUG)
        .order_by(BottegaSessionModel.created_at.desc()))).scalars().first()
    if row and row.output:
        try:
            data = json.loads(row.output)
            rec = cg.merge_record(cg.blank_record(), data.get("record") or {})
            # freshness: prefer the stamped updated_at, else fall back to the row's created_at
            updated = data.get("updated_at") or (row.created_at.isoformat() if row.created_at else "")
            return {"record": rec, "transcript": data.get("transcript") or [], "updated_at": updated}
        except Exception:  # noqa: BLE001
            logger.warning("concierge record parse failed for %s", username, exc_info=True)
    return {"record": cg.blank_record(), "transcript": [], "updated_at": ""}


async def write_concierge(db: AsyncSession, username: str, record: dict, transcript: list) -> None:
    """Upsert the member's Concierge row (record + transcript together) on the session spine."""
    payload = json.dumps({"record": record, "transcript": transcript[-60:],     # cap the tail
                          "updated_at": datetime.now(timezone.utc).isoformat()})  # freshness stamp (R0)
    # newest-wins + self-heal: if legacy duplicates exist, write the newest and drop the extras
    # so the (username, slug) invariant converges to one row on the next save.
    rows = (await db.execute(select(BottegaSessionModel).where(
        BottegaSessionModel.username == username,
        BottegaSessionModel.slug == CONCIERGE_SLUG)
        .order_by(BottegaSessionModel.created_at.desc()))).scalars().all()
    if rows:
        rows[0].output = payload
        for dup in rows[1:]:
            await db.delete(dup)
    else:
        db.add(BottegaSessionModel(
            username=username, slug=CONCIERGE_SLUG, title="Concierge Record",
            inputs="{}", output=payload, output_type="json", tags="concierge,memory"))
    await db.commit()


@router.get("/concierge/record")
async def concierge_record(current_user: dict = Depends(require_bottega_access()),
                           db: AsyncSession = Depends(get_db_session)):
    """The member's own master-record + transcript -- theirs to see (anti-Meta: it's their memory).
    Includes the R0 prep-scan: where the card stands (new?, completeness, host, freshness, must-do gaps)."""
    state = await read_concierge(db, current_user["username"])
    state["scan"] = cg.prep_scan(state)
    return state


@router.get("/concierge/sharpen")
async def concierge_sharpen(request: Request,
                           current_user: dict = Depends(require_bottega_access()),
                           db: AsyncSession = Depends(get_db_session)):
    """The Sharpen pass: a few RANKED either/or questions that tighten the member's RIASEC, the
    member's own ask ("narrow it down, make it more accurate"). Gated on a base portrait existing
    (nothing to sharpen on a blank). Answers are tapped back through /concierge/chat, so extraction
    re-scores RIASEC -- no separate scoring path. Query: ?language=&n=. Best-effort: [] on failure."""
    state = await read_concierge(db, current_user["username"])
    record = state["record"]
    completeness = cg.portrait_completeness(record)
    # Ready once we actually know *something* about them -- otherwise there's nothing to sharpen yet.
    ready = completeness["filled"] >= 2
    if not ready:
        return {"ready": False, "completeness": completeness, "questions": []}

    language = (request.query_params.get("language") or "").strip()
    try:
        n = max(1, min(3, int(request.query_params.get("n") or 3)))
    except (TypeError, ValueError):
        n = 3
    try:
        questions = await cg.personality_questions(record, language, n)
    except Exception:  # noqa: BLE001
        logger.warning("concierge_sharpen failed for %s", current_user["username"], exc_info=True)
        questions = []
    return {"ready": True, "completeness": completeness, "questions": questions}


@router.post("/concierge/chat")
async def concierge_chat(request: Request,
                         current_user: dict = Depends(require_bottega_access()),
                         db: AsyncSession = Depends(get_db_session)):
    """One concierge turn. Body: {message?, language?}. Empty message on a fresh member -> the
    opening greeting. Otherwise: reply (Cleopatra) -> extract -> merge -> persist. Returns the
    reply + the language (so the widget can read it aloud in the right voice) + the live record."""
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    message = (body.get("message") or "").strip()
    language = (body.get("language") or "").strip()

    state = await read_concierge(db, current_user["username"])
    record, transcript = state["record"], state["transcript"]

    # Fresh member, no message yet -> the front-door greeting (no brain call, Angel's copy).
    if not message and not transcript:
        greeting = cg.opening()  # one of the four five-star flavours, fresh each visit
        transcript.append({"role": "concierge", "content": greeting})
        await write_concierge(db, current_user["username"], record, transcript)
        # the opening is the English hub greeting; voice reads it in English
        return {"reply": greeting, "language": "en", "record": record, "opening": True}

    if message:
        transcript.append({"role": "member", "content": message})

    try:
        reply = await cg.concierge_reply(transcript, record, language)
    except BrainUnavailable:
        raise HTTPException(status_code=503,
                            detail="Cleopatra stepped away for a second -- try again in a moment.")
    transcript.append({"role": "concierge", "content": reply})

    # Voice AND the next-move chips follow the actual reply language: an explicit pick is
    # authoritative; in Auto we detect what the master actually wrote (the masters' rule).
    reply_lang = language if (language and language.lower() not in ("", "auto")) else cg.detect_lang(reply)

    # Every turn: update the record (extraction) AND propose next-move chips (suggestions),
    # concurrently -- both best-effort, neither can break the chat (return_exceptions). Chips
    # are generated in reply_lang so they don't come back English under an Italian conversation.
    fresh, suggestions = await asyncio.gather(
        cg.extract_record(transcript, record), cg.suggest_next(transcript, record, reply_lang),
        return_exceptions=True)
    if isinstance(fresh, dict):
        record = cg.merge_record(record, fresh)
        record = cg.stamp_provenance(record, fresh)   # v2: stamp each fact stated/inferred this turn
    else:
        logger.warning("concierge extraction failed for %s: %s", current_user["username"], fresh)
    if not isinstance(suggestions, list):
        suggestions = []
    # when a guest-planted fiction is live, the model's chips can't be trusted (they parrot it) --
    # serve safe, grounded fallback chips instead of reinforcing the invention.
    if cg.fiction_flagged(record):
        suggestions = cg.safe_chips(reply_lang)

    await write_concierge(db, current_user["username"], record, transcript)
    return {"reply": reply, "language": reply_lang, "record": record, "suggestions": suggestions}


@router.post("/concierge/dispatch")
async def concierge_dispatch(request: Request,
                             current_user: dict = Depends(require_bottega_access()),
                             db: AsyncSession = Depends(get_db_session)):
    """The HANDOFF (Concierge v2). Body: {question, question_type?, priority?, language?}. Cleo
    packages the question as a work order and dispatches it to the 2 best masters ON THE BOARD --
    hard-grounded (no invented masters). Each handoff is logged as a named history entry (so it
    shows in My Blueprint + the scorecard). Returns the outbound Service Interface."""
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    question = (body.get("question") or body.get("message") or "").strip()
    if not question:
        raise HTTPException(status_code=422, detail="A question is required to dispatch.")
    language = (body.get("language") or "").strip()
    question_type = (body.get("question_type") or "auto").strip()
    priority = (body.get("priority") or "normal").strip()

    # The board: masters only (badge_tier=LEGEND minus the family denylist), enriched with Houses.
    from src.services.square_bridge import list_legends, apply_houses
    roster = apply_houses(await list_legends(masters_only=True, limit=500), await _house_map(db))

    ref_id = uuid4().hex[:12]
    wp = dsp.build_work_package(question, ref_id=ref_id, source="guest",
                                question_type=question_type, language=language or "auto",
                                priority=priority)
    result = await dsp.dispatch(wp, roster, language=language,
                                timestamp=datetime.now(timezone.utc).isoformat())

    # Log the handoff on the spine -- a named job in the member's history (Block B / scorecard read it).
    db.add(BottegaSessionModel(
        username=current_user["username"], slug=f"dispatch-{ref_id}",
        title=("Asked: " + question)[:90], inputs=json.dumps(wp),
        output=json.dumps(result), output_type="json", tags="dispatch,concierge"))
    await db.commit()
    return result


async def _build_portrait(db: AsyncSession, username: str) -> str:
    """A plain-language human portrait of the member -- the CONTEXT a master/coach reads so it
    mentors the REAL person. Framed for a historical master: their life + situation, NEVER apps."""
    from datetime import date as _date
    profile = await _get(db, username)
    rows = (await db.execute(
        select(BottegaSessionModel).where(BottegaSessionModel.username == username)
        .order_by(BottegaSessionModel.created_at.desc()).limit(60))).scalars().all()

    def _out(slug):
        s = next((x for x in rows if x.slug == slug), None)
        if not s:
            return None
        if s.output_type == "json":
            try:
                return json.loads(s.output)
            except Exception:  # noqa: BLE001
                return None
        return s.output

    parts = []
    if profile and profile.tagline:
        parts.append(f'In their own words: "{profile.tagline}".')
    if profile and profile.bio:
        parts.append(f"About them: {profile.bio}")
    if profile and profile.skills:
        try:
            sk = json.loads(profile.skills)
            if sk:
                parts.append("Their strengths: " + ", ".join(sk[:8]) + ".")
        except Exception:  # noqa: BLE001
            pass
    body = _out("body-intake")
    if isinstance(body, dict):
        bits = []
        if body.get("goal"):
            bits.append(f"their goal is {body['goal']}")
        if body.get("days"):
            bits.append(f"they committed to {body['days']} sessions a week")
        if bits:
            parts.append("On their body: " + "; ".join(bits) + ".")
    spirit = _out("story-intake")
    if isinstance(spirit, dict):
        ol = spirit.get("one_liner") or spirit.get("oneLiner") or spirit.get("why")
        if ol:
            parts.append(f'Their deeper purpose: "{ol}".')
    if profile and profile.journey_start:
        dn = (_date.today() - profile.journey_start).days + 1
        if dn >= 1:
            dip = (dn - 1) % 30 + 1
            parts.append(
                f"They are on Day {dip} of a 30-day stretch of rebuilding themselves -- the "
                "habit-making phase, on a year-long road to becoming who they mean to be.")
    trows = (await db.execute(
        select(BottegaTaskModel).where(BottegaTaskModel.username == username)
        .order_by(BottegaTaskModel.created_at.desc()).limit(40))).scalars().all()
    if trows:
        done = sum(1 for t in trows if t.status == "done")
        parts.append(
            f"Lately they set themselves {len(trows)} tasks and finished {done} -- read that "
            "honestly (steady follow-through, or slipping and discouraged).")
    # Close the loop: whatever the Concierge has learned through conversation enriches the portrait
    # every master reads. Highest-signal context, so it leads.
    crow = next((x for x in rows if x.slug == CONCIERGE_SLUG), None)
    if crow and crow.output:
        try:
            crec = json.loads(crow.output).get("record") or {}
            parts = cg.record_to_portrait(crec) + parts
        except Exception:  # noqa: BLE001
            logger.warning("concierge portrait fold failed for %s", username, exc_info=True)
    if not parts:
        return ("A newcomer who hasn't told us much yet -- draw them out; ask who they are "
                "and what they want.")
    return " ".join(parts)


@router.get("/portrait")
async def portrait(current_user: dict = Depends(require_bottega_access()),
                   db: AsyncSession = Depends(get_db_session)):
    """The plain-language context a master/coach reads about you -- shown + EDITABLE in the UI.
    Transparency: the wrapper isn't buried; it's yours to see and steer before you ask."""
    return {"portrait": await _build_portrait(db, current_user["username"])}


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
    # Transparency: if the user edited the visible wrapper, THEIR text wins; else auto-build it.
    portrait = (form.get("portrait") or "").strip()
    if not portrait and slug in ("mentor-session", "find-your-edge", "decide"):
        try:
            portrait = await _build_portrait(db, owner)
        except Exception:  # noqa: BLE001
            portrait = ""
    language = (form.get("language") or "").strip()
    try:
        result = await run_recipe(slug, raw, portrait=portrait, language=language)
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
        sess = BottegaSessionModel(
            username=owner, slug=slug, title=RECIPES[slug].get("title", slug),
            inputs=json.dumps({k: v for k, v in raw.items() if isinstance(v, str)}),
            output=json.dumps(result.get("result", {})), output_type="json", tags="intake")
        db.add(sess)
        await db.commit()
        await db.refresh(sess)
        result["saved_id"] = str(sess.id)
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
    """My Blueprint Folder -- newest first. Ada's 'fold': CURRENT versions only -- superseded
    versions (an id that is some live row's parent) + soft-deleted tombstones are hidden, never lost."""
    uname = current_user["username"]
    superseded = (select(BottegaSessionModel.parent_id)
                  .where(BottegaSessionModel.username == uname,
                         BottegaSessionModel.parent_id.is_not(None),
                         BottegaSessionModel.deleted_at.is_(None)))
    rows = (await db.execute(
        select(BottegaSessionModel)
        .where(BottegaSessionModel.username == uname,
               BottegaSessionModel.deleted_at.is_(None),
               BottegaSessionModel.id.not_in(superseded))
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


# ===== Cards CRUD: every saved output is a card you can preview/edit/delete/pin =====
def _tags_set(tags: str | None) -> set:
    return {t.strip() for t in (tags or "").split(",") if t.strip()}


def _tags_str(s: set) -> str | None:
    return ",".join(sorted(s)) or None


async def _own_session(db: AsyncSession, session_id: str, username: str) -> BottegaSessionModel:
    try:
        s = await db.get(BottegaSessionModel, UUID(session_id))
    except Exception:  # noqa: BLE001
        s = None
    if not s or s.username != username:
        raise HTTPException(status_code=404, detail="not found")
    return s


class EditSession(BaseModel):
    title: str | None = None
    output: str | None = None
    tags: str | None = None


@router.patch("/sessions/{session_id}")
async def edit_session(session_id: str, body: EditSession,
                       current_user: dict = Depends(require_bottega_access()),
                       db: AsyncSession = Depends(get_db_session)):
    """Ada's ledger: editing APPENDS a new version (parent_id chain, version+1). The original is
    NEVER mutated -- the trace of who you were when you began is never lost. list_sessions 'folds'
    the chain so only the latest version shows; older ones stay recorded, reachable as history."""
    s = await _own_session(db, session_id, current_user["username"])
    new = BottegaSessionModel(
        username=s.username, slug=s.slug,
        title=(body.title if body.title is not None else (s.title or ""))[:160],
        inputs=s.inputs,
        output=(body.output if body.output is not None else (s.output or ""))[:200000],
        output_type=s.output_type,
        tags=(body.tags if body.tags is not None else s.tags),
        version=(s.version or 1) + 1, parent_id=s.id)
    db.add(new)
    await db.commit()
    await db.refresh(new)
    return {"id": str(new.id), "saved": True, "version": new.version, "supersedes": str(s.id)}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str,
                         current_user: dict = Depends(require_bottega_access()),
                         db: AsyncSession = Depends(get_db_session)):
    """Ada's tombstone: SOFT-delete -- hidden from the Blueprint, but the row + its full version
    history remain recorded. Never lose the trace of what was once said."""
    s = await _own_session(db, session_id, current_user["username"])
    s.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"deleted": True}


@router.post("/sessions/{session_id}/pin")
async def pin_session(session_id: str,
                      current_user: dict = Depends(require_bottega_access()),
                      db: AsyncSession = Depends(get_db_session)):
    """Pin this card as the CANONICAL one for its type (e.g. 'my story'). Unpins its siblings
    -- so the dashboard + the masters read this one. One pinned per (user, slug)."""
    user = current_user["username"]
    s = await _own_session(db, session_id, user)
    sibs = (await db.execute(select(BottegaSessionModel).where(
        BottegaSessionModel.username == user, BottegaSessionModel.slug == s.slug))).scalars().all()
    for x in sibs:
        t = _tags_set(x.tags)
        t.discard("pinned")
        x.tags = _tags_str(t)
    t = _tags_set(s.tags)
    t.add("pinned")
    s.tags = _tags_str(t)
    await db.commit()
    return {"pinned": True, "slug": s.slug}


@router.get("/cards")
async def cards(current_user: dict = Depends(require_bottega_access()),
                db: AsyncSession = Depends(get_db_session)):
    """The Blueprint as cards, grouped by type, newest first; the pinned one is canonical.
    Excludes inbox plumbing (message/notification). Each card carries its Markdown + serial."""
    rows = (await db.execute(
        select(BottegaSessionModel)
        .where(BottegaSessionModel.username == current_user["username"],
               BottegaSessionModel.slug.notin_(["message", "notification"]))
        .order_by(BottegaSessionModel.created_at.desc()).limit(300))).scalars().all()
    groups: dict = {}
    for s in rows:
        groups.setdefault(s.slug, []).append({
            "id": str(s.id), "slug": s.slug, "title": s.title, "output": s.output or "",
            "output_type": s.output_type or "markdown", "version": s.version or 1,
            "serial": str(s.id)[:8].upper(),
            "created_at": s.created_at.strftime("%d %b %Y") if s.created_at else "",
            "pinned": "pinned" in _tags_set(s.tags)})
    return {"groups": [{"slug": k, "count": len(v), "cards": v} for k, v in groups.items()]}


@router.get("/me")
async def me(current_user: dict = Depends(require_bottega_access()),
             db: AsyncSession = Depends(get_db_session)):
    return {"profile": _view(await _get(db, current_user["username"]))}


# --- Recipe-run ledger (#119): "has this been done? how many times? where are the records?" -------
# DRY -- every run is already a bottega_sessions row (slug=recipe + timestamp); derive the summary
# instead of keeping a parallel ledger. Powers done-checks (generalize the CV-banner-hide), visitor-mode.
_PLUMBING_SLUGS = {"message", "notification", CONCIERGE_SLUG, "legend-houses", "legend-questions"}


def _recipe_runs(rows) -> dict:
    """Group a member's session rows by recipe slug -> {slug: {count, last_run, last_id}}. Plumbing
    rows (inbox/concierge/legend cache) and per-ref dispatch rows are excluded. Pure + testable."""
    out: dict = {}
    for s in rows:
        slug = getattr(s, "slug", "") or ""
        if slug in _PLUMBING_SLUGS or slug.startswith("dispatch-"):
            continue
        ts = s.created_at.isoformat() if getattr(s, "created_at", None) else ""
        cur = out.get(slug)
        if cur is None:
            out[slug] = {"count": 1, "last_run": ts, "last_id": str(s.id)}
        else:
            cur["count"] += 1
            if ts > (cur["last_run"] or ""):
                cur["last_run"], cur["last_id"] = ts, str(s.id)
    return out


@router.get("/me/activity")
async def me_activity(current_user: dict = Depends(require_bottega_access()),
                      db: AsyncSession = Depends(get_db_session)):
    """The recipe-run ledger: {recipe_runs: {slug: {count, last_run, last_id}}} -- what this member has
    run, how many times, and where the latest record is. Powers done-checks (CV/etc.) + visitor-mode."""
    user = current_user["username"]
    rows = (await db.execute(select(BottegaSessionModel).where(
        BottegaSessionModel.username == user))).scalars().all()
    return {"recipe_runs": _recipe_runs(rows)}


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

    # --- the scorecard: three honest numbers so the member sees where they're at ---
    # plumbing rows don't count as "works" the member made
    NOISE = {"message", "notification", CONCIERGE_SLUG, "legend-houses"}
    dispatch_rows = [s for s in rows if (s.slug or "").startswith("dispatch-")]
    works = [s for s in rows if s.slug not in NOISE and not (s.slug or "").startswith("dispatch-")]
    masters_met = set()
    for s in dispatch_rows:
        try:
            for m in (json.loads(s.output) or {}).get("masters", []):
                if m.get("name"):
                    masters_met.add(m["name"])
        except Exception:  # noqa: BLE001
            pass
    crec = (await read_concierge(db, user)).get("record", {})
    scorecard = {
        "portrait": cg.portrait_completeness(crec),   # {filled,total,pct}
        "works": len(works),                          # things they've made/saved
        "handoffs": len(dispatch_rows),               # questions sent to the court
        "masters_met": len(masters_met),              # distinct masters consulted
    }

    return {
        "username": user,
        "profile": _view(await _get(db, user)),
        "body": latest("body-intake"),
        "spirit": latest("story-intake"),
        "workouts": all_of("workout-plan"),
        "mentors": all_of("mentor-session"),
        "archive": latest("blueprint-archive"),
        "scorecard": scorecard,
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


# --- Keystone (#107): a thread is a chain of bottega_sessions rows linked by parent_id ----------
# The root is a message row (parent_id IS NULL); each reply is a child row. Every turn stashes
# {author, role} in `inputs` (already a JSON field) -- role 'member' if the owner wrote it, else
# 'master'. These pure helpers turn the row chain into the engine's transcript shape; no schema
# change (parent_id already exists + is indexed). Tested in test_thread_engine.py.
def _turn_author(s, owner: str) -> tuple[str, str]:
    """(author, role) for one thread row. Prefer the explicit role we write; fall back to inferring
    from the author vs the thread owner (legacy nudge rows carry only `from`)."""
    try:
        inp = json.loads(s.inputs or "{}")
    except Exception:  # noqa: BLE001
        inp = {}
    author = inp.get("author") or inp.get("from") or ""
    role = inp.get("role")
    if role not in ("member", "master"):
        role = "member" if author and author == owner else "master"
    return author, role


def _thread_transcript(rows: list, owner: str) -> list[dict]:
    """Ordered rows (root first) -> the engine transcript [{role: member|master, content, author}].
    role maps straight onto the concierge engine's MEMBER/YOU split."""
    out = []
    for s in rows:
        author, role = _turn_author(s, owner)
        out.append({"role": role, "content": s.output or "", "author": author})
    return out


def _deliver_message(db: AsyncSession, *, to: str, sender: str, body: str,
                     subject: str = "", icon: str = "💬") -> None:
    """Drop a message + its notification into a member's inbox (the one spine). Shared by the
    member-to-member send, the equalizer nudge, AND the master/Cleo nudges (A — the living crew)."""
    db.add(BottegaSessionModel(
        username=to, slug="message", title=(subject or f"Message from {sender}")[:160],
        inputs=json.dumps({"from": sender, "read": False}), output=(body or "")[:8000],
        output_type="text", tags="message"))
    db.add(BottegaSessionModel(
        username=to, slug="notification", title=f"{icon} {sender}"[:160],
        inputs=json.dumps({"read": False}), output=(subject or (body or "")[:80]),
        output_type="text", tags="notification"))


@router.post("/message")
async def send_message(m: Message, current_user: dict = Depends(require_bottega_access()),
                       db: AsyncSession = Depends(get_db_session)):
    """Send a member a message (+ a notification). The equalizer's nudge runs through here too."""
    sender = current_user["username"]
    _deliver_message(db, to=m.to, sender=sender, body=m.body, subject=m.subject)
    await db.commit()
    return {"sent": True, "to": m.to}


@router.get("/me/inbox")
async def me_inbox(current_user: dict = Depends(require_bottega_access()),
                   db: AsyncSession = Depends(get_db_session)):
    """My messages + notifications (newest first) + unread count. Only thread ROOTS show here
    (parent_id IS NULL) -- thread replies live inside their thread, not as loose inbox items."""
    user = current_user["username"]
    rows = (await db.execute(
        select(BottegaSessionModel)
        .where(BottegaSessionModel.username == user,
               BottegaSessionModel.slug.in_(["message", "notification"]),
               BottegaSessionModel.parent_id.is_(None))
        .order_by(BottegaSessionModel.created_at.desc()).limit(100))).scalars().all()
    # reply counts per root (one grouped query) so the inbox can show a 💬 thread affordance
    root_ids = [s.id for s in rows if s.slug == "message"]
    counts: dict = {}
    if root_ids:
        crows = (await db.execute(
            select(BottegaSessionModel.parent_id, func.count())
            .where(BottegaSessionModel.parent_id.in_(root_ids))
            .group_by(BottegaSessionModel.parent_id))).all()
        counts = {pid: n for pid, n in crows}
    items = []
    for s in rows:
        if s.slug != "message":
            continue  # WW-2: notifications are the unread SIGNAL (the badge), not separate inbox
            # rows. Showing both made a handled item's notification linger as "undone" (Angel's flag).
        b = _inbox_brief(s)
        b["replies"] = int(counts.get(s.id, 0))
        items.append(b)
    unread = sum(1 for i in items if not i["read"])
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


# ===== Keystone (#107): a message is a replyable THREAD on the concierge engine =====
class ThreadReply(BaseModel):
    message: str
    language: str = ""


def _thread_turn_view(s, owner: str) -> dict:
    author, role = _turn_author(s, owner)
    return {"id": str(s.id), "author": author, "role": role, "body": s.output or "",
            "created_at": s.created_at.isoformat() if s.created_at else ""}


def _persona_for(author: str, role: str) -> str:
    """Resolve the speaker's persona = its Service-Interface definition. v1: every thread speaks in
    Cleopatra's voice. The protocol turn (slice 2) swaps THIS ONE LINE for load(master_definition)
    keyed by the author -- the author=master_id seam, persona-as-data. The runtime never changes."""
    return cg.BRAIN


def _mark_read_inplace(s) -> None:
    """Flip a row's inputs.read=True without a round-trip (caller commits)."""
    try:
        inp = json.loads(s.inputs or "{}")
    except Exception:  # noqa: BLE001
        inp = {}
    if not inp.get("read"):
        inp["read"] = True
        s.inputs = json.dumps(inp)


async def _load_thread(db: AsyncSession, root_id: UUID, owner: str):
    """Load a thread the member owns: (root, [children oldest-first]). A root is a message row with
    no parent (a nudge, or any message). (None, []) if missing / not theirs / not a root."""
    root = await db.get(BottegaSessionModel, root_id)
    if not root or root.username != owner or root.parent_id is not None or root.slug != "message":
        return None, []
    children = (await db.execute(
        select(BottegaSessionModel)
        .where(BottegaSessionModel.parent_id == root_id)
        .order_by(BottegaSessionModel.created_at.asc()))).scalars().all()
    return root, list(children)


@router.get("/me/thread/{root_id}")
async def get_thread(root_id: str, current_user: dict = Depends(require_bottega_access()),
                     db: AsyncSession = Depends(get_db_session)):
    """Read one thread (root + replies, oldest first). Opening it marks the root read."""
    owner = current_user["username"]
    try:
        rid = UUID(root_id)
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(status_code=404, detail="Thread not found.")
    root, children = await _load_thread(db, rid, owner)
    if not root:
        raise HTTPException(status_code=404, detail="Thread not found.")
    _mark_read_inplace(root)
    await db.commit()
    turns = [_thread_turn_view(s, owner) for s in [root] + children]
    return {"id": str(root.id), "title": root.title, "turns": turns}


@router.post("/me/thread/{root_id}/reply")
async def reply_to_thread(root_id: str, body: ThreadReply,
                          current_user: dict = Depends(require_bottega_access()),
                          db: AsyncSession = Depends(get_db_session)):
    """The keystone loop: a member replies into a thread, and the thread's master answers in-thread,
    grounded in the member's record -- the concierge engine, reused (not a new one-shot endpoint).
    v1 the master is Cleopatra; the persona is a parameter (author=master_id), so another master can
    take the thread over later by changing only _persona_for."""
    owner = current_user["username"]
    try:
        rid = UUID(root_id)
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(status_code=404, detail="Thread not found.")
    root, children = await _load_thread(db, rid, owner)
    if not root:
        raise HTTPException(status_code=404, detail="Thread not found.")
    msg = (body.message or "").strip()
    if not msg:
        raise HTTPException(status_code=422, detail="An empty reply has nothing to say.")

    # 1) the member's turn -> a child row on the spine
    member_turn = BottegaSessionModel(
        username=owner, slug="message", parent_id=rid, title=("You: " + msg)[:160],
        inputs=json.dumps({"author": owner, "role": "member", "read": True}),
        output=msg[:8000], output_type="text", tags="message,thread")
    db.add(member_turn)
    _mark_read_inplace(root)

    # 2) the thread's master speaks -- same engine, persona = the root's author (author=master_id)
    author, _role = _turn_author(root, owner)
    speaker = author or "Cleopatra"
    transcript = _thread_transcript([root] + children + [member_turn], owner)
    state = await read_concierge(db, owner)
    try:
        reply = await cg.thread_reply(transcript, state["record"],
                                      persona=_persona_for(author, _role),
                                      language=(body.language or "").strip())
    except BrainUnavailable:
        await db.commit()  # keep the member's turn even if the master stepped away
        raise HTTPException(status_code=503,
                            detail=f"{speaker} stepped away for a second -- try again in a moment.")

    # 3) the reply -> a child row too (no separate notification: the member is already in the thread)
    master_turn = BottegaSessionModel(
        username=owner, slug="message", parent_id=rid, title=(speaker + ": " + reply)[:160],
        inputs=json.dumps({"author": speaker, "role": "master", "read": True}),
        output=reply[:8000], output_type="text", tags="message,thread")
    db.add(master_turn)
    await db.commit()

    turns = [_thread_turn_view(s, owner) for s in [root] + children + [member_turn, master_turn]]
    return {"id": str(root.id), "title": root.title, "turns": turns,
            "reply": {"author": speaker, "body": reply}}


# ===== A: the living crew -- Cleo reads your board and nudges (summary + next move) =====
CLEO_NUDGE_SYS = (
    "You are Cleopatra, the warm host of La Piazza and this member's guide. Write ONE short note "
    "for their inbox about today's work board. 2-4 sentences, ~60 words max. First, celebrate what "
    "is DONE -- name one or two real items. Then point at the single most useful NEXT move, taken "
    "from what is still OPEN or waiting (unassigned/TBD). "
    "HARD RULES: use ONLY the facts given below. NEVER invent a task, a person, a date, a number, "
    "or a booking. Do not promise to do anything yourself. Warm, specific, a little spark. "
    "Plain text, at most one emoji."
)


def _board_facts(tasks: list[dict], day: str) -> str:
    tops = [t for t in tasks if not t.get("parent_id")]
    done = [t for t in tops if t.get("status") == "done"]
    opent = [t for t in tops if t.get("status") != "done"]
    tbd = [t for t in opent if not t.get("assignee") and not t.get("house")]
    steps = [t for t in tasks if t.get("parent_id")]
    steps_done = sum(1 for s in steps if s.get("status") == "done")
    est = sum((t.get("estimate_min") or 0) for t in tasks)

    def line(t):
        bits = []
        if t.get("task_key"):
            bits.append(t["task_key"])
        if t.get("assignee"):
            bits.append("by " + t["assignee"])
        elif t.get("house"):
            bits.append("House: " + t["house"])
        else:
            bits.append("unassigned/TBD")
        return f"  - {t.get('title','')} ({'; '.join(bits)})"

    out = [f"Day: {day}"]
    out.append(f"DONE ({len(done)}):")
    out += [line(t) for t in done] or ["  (nothing checked off yet)"]
    out.append(f"OPEN ({len(opent)}):")
    out += [line(t) for t in opent] or ["  (none)"]
    if tbd:
        out.append("WAITING / unassigned: " + ", ".join(t.get("title", "") for t in tbd))
    if steps:
        out.append(f"Breakdown steps: {steps_done} of {len(steps)} done")
    if est:
        out.append(f"Planned time today: {est} min")
    if not done and not opent:
        out.append("The board is empty -- gently invite them to add a first task or a small win.")
    return "\n".join(out)


@router.post("/me/nudge")
async def me_nudge(day: str | None = None,
                   current_user: dict = Depends(require_bottega_access()),
                   db: AsyncSession = Depends(get_db_session)):
    """A — the first living-crew touch: Cleopatra looks at the member's board for `day`, writes a
    grounded summary + one next move, and delivers it to their own inbox (message + notification)."""
    from datetime import date as _date
    user = current_user["username"]
    the_day = day or _date.today().isoformat()
    rows = (await db.execute(select(BottegaTaskModel).where(
        BottegaTaskModel.username == user, BottegaTaskModel.day == the_day))).scalars().all()
    tasks = [_task_view(t) for t in rows]
    facts = _board_facts(tasks, the_day)
    try:
        from src.services.bottega_service import _brain_chat
        note = (await _brain_chat(CLEO_NUDGE_SYS, facts)).strip()
        note = cg._strip_think(note) if hasattr(cg, "_strip_think") else note
    except Exception:  # noqa: BLE001 -- brain down: still deliver a useful, honest note
        done_n = sum(1 for t in tasks if not t.get("parent_id") and t.get("status") == "done")
        open_n = sum(1 for t in tasks if not t.get("parent_id") and t.get("status") != "done")
        note = (f"Nice work — {done_n} done today, {open_n} still open. "
                "Pick the one that matters most and give it the next hour. 🐺") if (done_n or open_n) \
            else "Fresh page today. Drop in the one thing that would make today a win, and we'll go from there."
    note = (note or "")[:1200]
    _deliver_message(db, to=user, sender="Cleopatra", body=note,
                     subject="👑 A note from Cleopatra", icon="👑")
    await db.commit()
    return {"posted": True, "note": note, "day": the_day}


# ===== A: Cleo picks your Top 10 (the morning bookend -- triage open work toward your goals) =====
PICK_SYS = (
    "You are Cleopatra, the member's host at La Piazza. From their OPEN tasks listed below, choose "
    "up to TEN to focus on TODAY and put them in priority order -- the ones that move their GOALS "
    "(projects) forward the most, plus anything stale that needs unsticking. "
    "HARD RULES: pick ONLY from the ids given -- never invent a task. Prefer a spread across goals "
    "over ten items from one. Return STRICT JSON only:\n"
    '{"picks":[{"id":"<id>","why":"<=8 words"}], "note":"<one warm line, plain text>"}'
)


@router.post("/me/pick-top10")
async def pick_top10(day: str | None = None,
                     current_user: dict = Depends(require_bottega_access()),
                     db: AsyncSession = Depends(get_db_session)):
    """Cleo triages the member's OPEN top-level tasks (any day) and promotes up to 10 onto `day`'s
    Top 10 in priority order. Grounded: she may only choose ids that exist; hallucinated ids drop."""
    from datetime import date as _date
    user = current_user["username"]
    the_day = day or _date.today().isoformat()
    cands = (await db.execute(select(BottegaTaskModel).where(
        BottegaTaskModel.username == user, BottegaTaskModel.status != "done",
        BottegaTaskModel.parent_id.is_(None))
        .order_by(BottegaTaskModel.day).limit(60))).scalars().all()
    if not cands:
        return {"picked": [], "note": "Nothing open to pick from yet — add a task or set a goal and "
                "I'll build the list with you.", "day": the_day}
    by_id = {str(c.id): c for c in cands}
    lines = [f"- id={cid} | {c.title} | goal={c.project or '-'} | key={c.task_key or '-'} | on={c.day}"
             for cid, c in by_id.items()]
    facts = f"Member: {user}\nToday: {the_day}\nOPEN TASKS ({len(by_id)}):\n" + "\n".join(lines)

    ordered_ids, note = [], ""
    try:
        from src.services.bottega_service import _brain_chat
        raw = await _brain_chat(PICK_SYS, facts, json_mode=True)
        raw = cg._strip_think(raw) if hasattr(cg, "_strip_think") else raw
        data = json.loads(raw)
        for p in (data.get("picks") or []):
            pid = str(p.get("id", "")).strip()
            if pid in by_id and pid not in ordered_ids:
                ordered_ids.append(pid)
            if len(ordered_ids) >= 10:
                break
        note = (data.get("note") or "").strip()
    except Exception:  # noqa: BLE001 -- brain down: fall back to the 10 oldest-open, still grounded
        ordered_ids = list(by_id.keys())[:10]
        note = "Cleo's brain is napping — here's your oldest-open ten to start with."

    if not ordered_ids:                               # model returned nothing usable
        ordered_ids = list(by_id.keys())[:10]
    picked = []
    for i, pid in enumerate(ordered_ids):
        t = by_id[pid]
        if t.day != the_day or t.section != "top10":
            _log_history(t, "day" if t.day != the_day else "section",
                         t.day if t.day != the_day else t.section, the_day, by="Cleopatra")
        t.day, t.section, t.sort_order = the_day, "top10", i
        picked.append({"id": pid, "title": t.title, "task_key": t.task_key})
    await db.commit()
    return {"picked": picked, "note": (note or "Here's your Top 10 — in the order I'd tackle them.")[:600],
            "day": the_day}


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
    # Gamification: filing feedback EARNS a small credit -- contribution counts (good or bad),
    # but capped so it can't be farmed (up to FEEDBACK_DAILY_CAP rewarded per user per day).
    FEEDBACK_REWARD, FEEDBACK_DAILY_CAP = 2, 5
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    prior = (await db.execute(select(func.count(BacklogItemModel.id)).where(
        BacklogItemModel.created_by == user,
        BacklogItemModel.tags.like("%feedback%"),
        BacklogItemModel.created_at >= start))).scalar() or 0
    rewarded = prior < FEEDBACK_DAILY_CAP

    item = BacklogItemModel(
        item_number=next_number, title=title[:200], description=desc,
        item_type=item_type, application=HelixApplication.HELIXNET,
        priority=BacklogPriority.MEDIUM, created_by=user,
        tags=f"bottega,feedback,{kind}")
    db.add(item)
    if rewarded:
        await ensure_starter_grant(db, user)
        await post_ledger(db, user, ComputeLedgerKind.EARN, FEEDBACK_REWARD,
                          counterparty="la-bottega", note="feedback reward")
        await post_ledger(db, "la-bottega", ComputeLedgerKind.SPEND, -FEEDBACK_REWARD,
                          counterparty=user, note="feedback reward")
    await db.commit()
    bal = await credit_balance(db, user)
    logger.info(f"BL-{next_number:03d} filed from Bottega by {user}: {title} (rewarded={rewarded})")
    return {"ok": True, "item_number": next_number, "ref": f"BL-{next_number:03d}",
            "rewarded": rewarded, "credits_earned": FEEDBACK_REWARD if rewarded else 0, "balance": bal}


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


@router.get("/square-profile")
async def square_profile(current_user: dict = Depends(require_bottega_access()),
                         db: AsyncSession = Depends(get_db_session)):
    """State-2: does this member already have a La Piazza (Square) profile we can import from?
    Drives the 'Welcome back — build your Bottega from your La Piazza profile' banner."""
    from src.services.square_bridge import get_square_profile
    sub = current_user.get("sub")
    sq = await get_square_profile(sub) if sub else None
    existing = await _get(db, current_user["username"])
    return {"found": bool(sq), "has_bottega": bool(existing and existing.status == "applied"),
            "square": sq}


@router.post("/import-from-square")
async def import_from_square(current_user: dict = Depends(require_bottega_access()),
                            db: AsyncSession = Depends(get_db_session)):
    """State-2: seed the member's Bottega FROM their existing Square profile -- the BL-014 payoff.
    A returning La Piazza member never faces a blank workshop; their storefront seeds the bench."""
    from src.services.square_bridge import get_square_profile
    sub = current_user.get("sub")
    sq = await get_square_profile(sub) if sub else None
    if not sq:
        raise HTTPException(status_code=404, detail="no La Piazza profile found to import")
    username = current_user["username"]
    bio = sq["bio"] or ((f"{sq['display_name']} — {sq['workshop']}").strip(" —")
                        if sq["workshop"] else sq["display_name"])
    tagline = sq["tagline"] or ""
    existing = await _get(db, username)
    if existing:
        db.add(BottegaProfileHistoryModel(
            username=username, snapshot=json.dumps(_view(existing).model_dump()),
            reason="pre-import snapshot (from Square)"))
        existing.bio, existing.tagline = bio, tagline
        existing.source, existing.status = "square-import", "applied"
        existing.completeness = min(100, max(existing.completeness, 60))
        profile = existing
    else:
        profile = BottegaProfileModel(
            username=username, bio=bio, tagline=tagline, skills="[]", categories="[]",
            source="square-import", status="applied", completeness=60)
        db.add(profile)
    if not profile.slug:
        profile.slug = await _unique_slug(db, sq["slug"] or username, username)
    await db.commit()
    await db.refresh(profile)
    return {"imported": True, "profile": _view(profile), "slug": profile.slug,
            "url": f"/u/{profile.slug}",
            "from": {"display_name": sq["display_name"], "city": sq["city"]}}


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


# ---------------------------------------------------------------------------
# Daily One-Pager — the habit-making checklist (Top 10 + Bonus Round). Lego-simple:
# a line, a checkbox, a note. Keyed by the LOCAL date; the browser owns the timezone.
# ---------------------------------------------------------------------------
class TaskIn(BaseModel):
    day: str
    section: str = "top10"
    title: str
    notes: str | None = None
    parent_id: str | None = None       # set => this is a sub-task (a breakdown step)
    estimate_min: int | None = None    # planned minutes (the "time")
    assignee: str | None = None        # lead; defaults to the owner ("" => TBD/unassigned)
    house: str | None = None           # resolution group / House when no specific person
    collaborators: list[dict] | None = None   # the crew: [{who, role}] (Tesla=idea, Da Vinci=art)
    project: str | None = None         # epic/project slug; mints the EPIC-n key at creation


class TaskPatch(BaseModel):
    title: str | None = None
    notes: str | None = None
    status: str | None = None
    section: str | None = None
    sort_order: int | None = None
    day: str | None = None
    estimate_min: int | None = None
    assignee: str | None = None
    house: str | None = None           # resolution group / House
    collaborators: list[dict] | None = None    # full replace of the crew list
    project: str | None = None         # set/change the epic; mints the EPIC-n key on first assignment


class ReorderIn(BaseModel):
    ids: list[str]                     # the new top-to-bottom order; index => sort_order


class JourneyStartIn(BaseModel):
    date: str


def _clean_collaborators(raw) -> list[dict]:
    """Normalise the crew list to [{who, role}] with non-empty 'who'. Accepts dicts or strings."""
    out = []
    for c in (raw or [])[:20]:
        if isinstance(c, str):
            who, role = c.strip(), ""
        elif isinstance(c, dict):
            who, role = str(c.get("who", "")).strip(), str(c.get("role", "")).strip()
        else:
            continue
        if who:
            out.append({"who": who[:100], "role": role[:80]})
    return out


def _task_view(t: BottegaTaskModel) -> dict:
    try:
        hist = json.loads(t.history) if t.history else []
    except (ValueError, TypeError):
        hist = []
    try:
        crew = json.loads(t.collaborators) if t.collaborators else []
    except (ValueError, TypeError):
        crew = []
    return {"id": str(t.id), "day": t.day, "section": t.section, "title": t.title,
            "notes": t.notes or "", "status": t.status, "sort_order": t.sort_order,
            "parent_id": str(t.parent_id) if t.parent_id else None,
            "estimate_min": t.estimate_min, "assignee": t.assignee, "house": t.house,
            "collaborators": crew, "project": t.project, "task_key": t.task_key,
            "history": hist}


async def _next_task_key(db: AsyncSession, username: str, project: str) -> str:
    """EPIC-n: next number in this member's project (e.g. BOTTEGA-12). Per-user, per-project."""
    n = (await db.execute(select(func.count()).where(
        BottegaTaskModel.username == username,
        BottegaTaskModel.project == project,
        BottegaTaskModel.task_key.isnot(None)))).scalar() or 0
    return f"{project.strip().upper().replace(' ', '-')[:24]}-{n + 1}"


_HISTORY_CAP = 50  # keep the last N edits per task -- "a little version control", not a black hole


def _log_history(t: BottegaTaskModel, field: str, old, new, *, by: str) -> None:
    """Append one append-only edit row to the task's history JSON (bounded)."""
    if old == new:
        return
    try:
        hist = json.loads(t.history) if t.history else []
    except (ValueError, TypeError):
        hist = []
    hist.append({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "by": by, "field": field, "from": old, "to": new})
    t.history = json.dumps(hist[-_HISTORY_CAP:], ensure_ascii=False)


async def _own_task(db: AsyncSession, task_id: str, username: str) -> BottegaTaskModel:
    t = (await db.execute(
        select(BottegaTaskModel).where(BottegaTaskModel.id == task_id))).scalar_one_or_none()
    if not t or t.username != username:
        raise HTTPException(status_code=404, detail="task not found")
    return t


@router.get("/today")
async def today(day: str, current_user: dict = Depends(require_bottega_access()),
                db: AsyncSession = Depends(get_db_session)):
    """The daily page for `day` (YYYY-MM-DD = the user's LOCAL date) + their journey start.
    The browser computes the phase header from journey_start (it owns the timezone)."""
    username = current_user["username"]
    rows = (await db.execute(
        select(BottegaTaskModel).where(
            BottegaTaskModel.username == username, BottegaTaskModel.day == day)
        .order_by(BottegaTaskModel.sort_order, BottegaTaskModel.created_at))).scalars().all()
    profile = await _get(db, username)
    js = None
    if profile and profile.journey_start:
        js = profile.journey_start.isoformat()
    elif profile and profile.created_at:
        js = profile.created_at.date().isoformat()
    return {"day": day, "journey_start": js, "tasks": [_task_view(t) for t in rows]}


@router.post("/today/tasks")
async def create_task(t: TaskIn, current_user: dict = Depends(require_bottega_access()),
                      db: AsyncSession = Depends(get_db_session)):
    username = current_user["username"]
    title = (t.title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="give the task a few words")
    section = t.section if t.section in ("top10", "bonus") else "top10"
    n = (await db.execute(select(func.coalesce(func.max(BottegaTaskModel.sort_order), 0)).where(
        BottegaTaskModel.username == username,
        BottegaTaskModel.day == t.day, BottegaTaskModel.section == section))).scalar() + 1
    # a sub-task must point at a real task this member owns
    parent = None
    if t.parent_id:
        parent = await _own_task(db, t.parent_id, username)
    project = (t.project or (parent.project if parent else None) or None)
    if project:
        project = project.strip().lower()[:40] or None
    task = BottegaTaskModel(
        username=username, day=t.day, section=section, title=title[:300],
        notes=(t.notes or None), status="open", sort_order=n,
        parent_id=parent.id if parent else None,
        estimate_min=t.estimate_min if (t.estimate_min and t.estimate_min > 0) else None,
        assignee=(t.assignee if t.assignee is not None else username),  # owner first; ""/null => TBD
        house=(t.house.strip()[:60] or None) if t.house else None,
        collaborators=(json.dumps(_clean_collaborators(t.collaborators), ensure_ascii=False)
                       if t.collaborators else None),
        project=project,
        task_key=(await _next_task_key(db, username, project) if (project and not parent) else None))
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return _task_view(task)


@router.patch("/today/tasks/{task_id}")
async def update_task(task_id: str, p: TaskPatch,
                      current_user: dict = Depends(require_bottega_access()),
                      db: AsyncSession = Depends(get_db_session)):
    username = current_user["username"]
    t = await _own_task(db, task_id, username)
    if p.title is not None:
        nv = p.title.strip()[:300]
        _log_history(t, "title", t.title, nv, by=username)
        t.title = nv
    if p.notes is not None:
        nv = p.notes or None
        _log_history(t, "notes", t.notes, nv, by=username)
        t.notes = nv
    if p.status in ("open", "done"):
        _log_history(t, "status", t.status, p.status, by=username)
        t.status = p.status
    if p.section in ("top10", "bonus"):
        t.section = p.section
    if p.sort_order is not None:
        t.sort_order = p.sort_order
    if p.day is not None:
        _log_history(t, "day", t.day, p.day, by=username)
        t.day = p.day
    if p.estimate_min is not None:
        nv = p.estimate_min if p.estimate_min > 0 else None
        _log_history(t, "estimate_min", t.estimate_min, nv, by=username)
        t.estimate_min = nv
    if p.assignee is not None:
        nv = p.assignee.strip()[:100] or None   # "" => TBD/unassigned (the auto-router can claim it)
        _log_history(t, "assignee", t.assignee, nv, by=username)
        t.assignee = nv
    if p.house is not None:
        nv = p.house.strip()[:60] or None
        _log_history(t, "house", t.house, nv, by=username)
        t.house = nv
    if p.collaborators is not None:
        crew = _clean_collaborators(p.collaborators)
        nv = json.dumps(crew, ensure_ascii=False) if crew else None
        if nv != t.collaborators:
            _log_history(t, "collaborators", None, [c["who"] for c in crew], by=username)
        t.collaborators = nv
    if p.project is not None:
        nv = (p.project.strip().lower()[:40] or None)
        if nv != t.project:
            _log_history(t, "project", t.project, nv, by=username)
            t.project = nv
            # mint a key the first time a (top-level) task joins a project; keep it once minted
            if nv and not t.task_key and not t.parent_id:
                t.task_key = await _next_task_key(db, username, nv)
    await db.commit()
    await db.refresh(t)
    return _task_view(t)


@router.delete("/today/tasks/{task_id}")
async def delete_task(task_id: str, current_user: dict = Depends(require_bottega_access()),
                      db: AsyncSession = Depends(get_db_session)):
    t = await _own_task(db, task_id, current_user["username"])
    # cascade: deleting a task takes its breakdown steps with it
    kids = (await db.execute(select(BottegaTaskModel).where(
        BottegaTaskModel.parent_id == t.id))).scalars().all()
    for k in kids:
        await db.delete(k)
    await db.delete(t)
    await db.commit()
    return {"deleted": True, "with_subtasks": len(kids)}


@router.post("/today/reorder")
async def reorder_tasks(r: ReorderIn, current_user: dict = Depends(require_bottega_access()),
                        db: AsyncSession = Depends(get_db_session)):
    """Set sort_order from the given top-to-bottom id list (drag/▲▼ result). Owns-check each."""
    username = current_user["username"]
    rows = (await db.execute(select(BottegaTaskModel).where(
        BottegaTaskModel.username == username,
        BottegaTaskModel.id.in_(r.ids)))).scalars().all()
    by_id = {str(x.id): x for x in rows}
    for i, tid in enumerate(r.ids):
        if tid in by_id:
            by_id[tid].sort_order = i
    await db.commit()
    return {"reordered": len(by_id)}


@router.post("/today/tasks/{task_id}/move")
async def move_task(task_id: str, current_user: dict = Depends(require_bottega_access()),
                    db: AsyncSession = Depends(get_db_session)):
    """Move an unfinished task to tomorrow (day + 1)."""
    from datetime import date as _date, timedelta
    t = await _own_task(db, task_id, current_user["username"])
    try:
        nxt = (_date.fromisoformat(t.day) + timedelta(days=1)).isoformat()
    except ValueError:
        raise HTTPException(status_code=400, detail="bad day")
    t.day, t.status = nxt, "open"
    await db.commit()
    return {"moved_to": nxt}


@router.post("/today/carry")
async def carry_forward(from_day: str, to_day: str,
                        current_user: dict = Depends(require_bottega_access()),
                        db: AsyncSession = Depends(get_db_session)):
    """Pull every UNFINISHED task from one day onto another (carry yesterday's open tasks)."""
    rows = (await db.execute(select(BottegaTaskModel).where(
        BottegaTaskModel.username == current_user["username"],
        BottegaTaskModel.day == from_day, BottegaTaskModel.status == "open"))).scalars().all()
    for t in rows:
        t.day = to_day
    await db.commit()
    return {"carried": len(rows), "to": to_day}


@router.patch("/today/journey-start")
async def set_journey_start(j: JourneyStartIn,
                            current_user: dict = Depends(require_bottega_access()),
                            db: AsyncSession = Depends(get_db_session)):
    """Set Day 1 of the journey (e.g. 2026-06-01)."""
    from datetime import date as _date
    profile = await _get(db, current_user["username"])
    if not profile:
        raise HTTPException(status_code=404, detail="no profile")
    try:
        profile.journey_start = _date.fromisoformat(j.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    await db.commit()
    return {"journey_start": profile.journey_start.isoformat()}
