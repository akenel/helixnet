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
        await db.commit()
        await db.refresh(profile)
        token = await _member_token(c, username, password)   # auto-login: you're in
    return {"username": username, "slug": slug, "token": token, "profile": _view(profile)}


@router.get("/recipes")
async def recipes(current_user: dict = Depends(require_bottega_access())):
    """The Chinese menu -- every recipe + its input spec. Adding one = a dict entry."""
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
    row = (await db.execute(select(BottegaSessionModel).where(
        BottegaSessionModel.username == username,
        BottegaSessionModel.slug == CONCIERGE_SLUG))).scalar_one_or_none()
    if row and row.output:
        try:
            data = json.loads(row.output)
            rec = cg.merge_record(cg.blank_record(), data.get("record") or {})
            return {"record": rec, "transcript": data.get("transcript") or []}
        except Exception:  # noqa: BLE001
            logger.warning("concierge record parse failed for %s", username, exc_info=True)
    return {"record": cg.blank_record(), "transcript": []}


async def write_concierge(db: AsyncSession, username: str, record: dict, transcript: list) -> None:
    """Upsert the member's Concierge row (record + transcript together) on the session spine."""
    payload = json.dumps({"record": record, "transcript": transcript[-60:]})  # cap the tail
    row = (await db.execute(select(BottegaSessionModel).where(
        BottegaSessionModel.username == username,
        BottegaSessionModel.slug == CONCIERGE_SLUG))).scalar_one_or_none()
    if row:
        row.output = payload
    else:
        db.add(BottegaSessionModel(
            username=username, slug=CONCIERGE_SLUG, title="Concierge Record",
            inputs="{}", output=payload, output_type="json", tags="concierge,memory"))
    await db.commit()


@router.get("/concierge/record")
async def concierge_record(current_user: dict = Depends(require_bottega_access()),
                           db: AsyncSession = Depends(get_db_session)):
    """The member's own master-record + transcript -- theirs to see (anti-Meta: it's their memory)."""
    return await read_concierge(db, current_user["username"])


@router.post("/concierge/chat")
async def concierge_chat(request: Request,
                         current_user: dict = Depends(require_bottega_access()),
                         db: AsyncSession = Depends(get_db_session)):
    """One concierge turn. Body: {message?, language?}. Empty message on a fresh member -> the
    opening greeting. Otherwise: reply (Heisenberg) -> extract -> merge -> persist. Returns the
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

    # Every turn: update the record (extraction) AND propose next-move chips (suggestions),
    # concurrently -- both best-effort, neither can break the chat (return_exceptions).
    fresh, suggestions = await asyncio.gather(
        cg.extract_record(transcript), cg.suggest_next(transcript, record),
        return_exceptions=True)
    if isinstance(fresh, dict):
        record = cg.merge_record(record, fresh)
    else:
        logger.warning("concierge extraction failed for %s: %s", current_user["username"], fresh)
    if not isinstance(suggestions, list):
        suggestions = []

    await write_concierge(db, current_user["username"], record, transcript)
    # Voice follows the actual reply language: an explicit pick is authoritative; in Auto we
    # detect what the master actually wrote (the masters' rule -- the words decide).
    reply_lang = language if (language and language.lower() not in ("", "auto")) else cg.detect_lang(reply)
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


class TaskPatch(BaseModel):
    title: str | None = None
    notes: str | None = None
    status: str | None = None
    section: str | None = None
    sort_order: int | None = None
    day: str | None = None


class JourneyStartIn(BaseModel):
    date: str


def _task_view(t: BottegaTaskModel) -> dict:
    return {"id": str(t.id), "day": t.day, "section": t.section, "title": t.title,
            "notes": t.notes or "", "status": t.status, "sort_order": t.sort_order}


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
    title = (t.title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="give the task a few words")
    section = t.section if t.section in ("top10", "bonus") else "top10"
    n = (await db.execute(select(func.coalesce(func.max(BottegaTaskModel.sort_order), 0)).where(
        BottegaTaskModel.username == current_user["username"],
        BottegaTaskModel.day == t.day, BottegaTaskModel.section == section))).scalar() + 1
    task = BottegaTaskModel(username=current_user["username"], day=t.day, section=section,
                            title=title[:300], notes=(t.notes or None), status="open", sort_order=n)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return _task_view(task)


@router.patch("/today/tasks/{task_id}")
async def update_task(task_id: str, p: TaskPatch,
                      current_user: dict = Depends(require_bottega_access()),
                      db: AsyncSession = Depends(get_db_session)):
    t = await _own_task(db, task_id, current_user["username"])
    if p.title is not None:
        t.title = p.title.strip()[:300]
    if p.notes is not None:
        t.notes = p.notes or None
    if p.status in ("open", "done"):
        t.status = p.status
    if p.section in ("top10", "bonus"):
        t.section = p.section
    if p.sort_order is not None:
        t.sort_order = p.sort_order
    if p.day is not None:
        t.day = p.day
    await db.commit()
    await db.refresh(t)
    return _task_view(t)


@router.delete("/today/tasks/{task_id}")
async def delete_task(task_id: str, current_user: dict = Depends(require_bottega_access()),
                      db: AsyncSession = Depends(get_db_session)):
    t = await _own_task(db, task_id, current_user["username"])
    await db.delete(t)
    await db.commit()
    return {"deleted": True}


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
