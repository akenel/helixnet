"""Postino — FastAPI CRM for postcard-led lead tracking."""
import csv
import io
import os
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import Base, SessionLocal, engine, get_db
from .models import (
    BOARD_STAGES,
    INTERACTION_KINDS,
    STAGE_LABELS,
    STAGES,
    Campaign,
    Interaction,
    Lead,
    now,
)
from .seed import seed_from_csv
from .sync import sync_events

APP_NAME = "Postino"
TAGLINE = "The postcard is the handshake."
# The campaign landing's events feed (Banco /kaffee/events?key=…) or a local path. Set per-env.
CAMPAIGN_EVENTS_SRC = os.environ.get("CAMPAIGN_EVENTS_SRC", "")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals.update(
    APP_NAME=APP_NAME,
    TAGLINE=TAGLINE,
    STAGES=STAGES,
    STAGE_LABELS=STAGE_LABELS,
    BOARD_STAGES=BOARD_STAGES,
    INTERACTION_KINDS=INTERACTION_KINDS,
)

app = FastAPI(title=APP_NAME)


@app.on_event("startup")
def _startup() -> None:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if db.scalar(select(func.count(Lead.id))) == 0:
            seed_from_csv(db)
    finally:
        db.close()


def _back(request: Request, fallback: str) -> RedirectResponse:
    target = request.headers.get("referer") or fallback
    return RedirectResponse(target, status_code=303)


# ---------------------------------------------------------------- views

@app.get("/", response_class=HTMLResponse)
def board(
    request: Request,
    tier: str = "",
    persona: str = "",
    db: Session = Depends(get_db),
):
    q = select(Lead)
    if tier:
        q = q.where(Lead.tier == tier)
    if persona:
        q = q.where(Lead.persona == persona)
    leads = db.scalars(q.order_by(Lead.qualify_score.desc())).all()

    columns = {s: [l for l in leads if l.stage == s] for s in BOARD_STAGES}
    stats = {s: sum(1 for l in leads if l.stage == s) for s in STAGES}
    postcards = sum(1 for l in leads if l.postcard_sent_on)
    a_left = sum(1 for l in leads if l.tier == "A" and l.stage == "to_contact")
    return templates.TemplateResponse(
        request,
        "board.html",
        {
            "columns": columns,
            "stats": stats,
            "postcards": postcards,
            "a_left": a_left,
            "total": len(leads),
            "tier": tier,
            "persona": persona,
        },
    )


@app.get("/table", response_class=HTMLResponse)
def table(
    request: Request,
    tier: str = "",
    persona: str = "",
    stage: str = "",
    city: str = "",
    db: Session = Depends(get_db),
):
    q = select(Lead)
    if tier:
        q = q.where(Lead.tier == tier)
    if persona:
        q = q.where(Lead.persona == persona)
    if stage:
        q = q.where(Lead.stage == stage)
    if city:
        q = q.where(Lead.city == city)
    leads = db.scalars(q.order_by(Lead.qualify_score.desc())).all()
    cities = db.scalars(select(Lead.city).distinct().order_by(Lead.city)).all()
    return templates.TemplateResponse(
        request,
        "table.html",
        {
            "leads": leads,
            "cities": [c for c in cities if c],
            "tier": tier,
            "persona": persona,
            "stage": stage,
            "city": city,
        },
    )


@app.get("/lead/{lead_id}", response_class=HTMLResponse)
def lead_detail(lead_id: int, request: Request, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if lead is None:
        return RedirectResponse("/", status_code=303)
    interactions = sorted(lead.interactions, key=lambda i: i.created_at, reverse=True)
    return templates.TemplateResponse(
        request,
        "lead.html",
        {"lead": lead, "interactions": interactions},
    )


# ---------------------------------------------------------------- mutations

@app.post("/lead/{lead_id}/update")
def update_lead(
    lead_id: int,
    request: Request,
    name: str = Form(""),
    chain: str = Form(""),
    category: str = Form(""),
    city: str = Form(""),
    phone: str = Form(""),
    street_address: str = Form(""),
    postal_code: str = Form(""),
    website: str = Form(""),
    email: str = Form(""),
    legal_entity: str = Form(""),
    manager_name: str = Form(""),
    manager_role: str = Form(""),
    tier: str = Form(""),
    persona: str = Form(""),
    qualify_score: int = Form(0),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    lead = db.get(Lead, lead_id)
    if lead is None:
        return RedirectResponse("/", status_code=303)
    for field, value in {
        "name": name.strip(),
        "chain": chain.strip(),
        "category": category.strip(),
        "city": city.strip(),
        "phone": phone.strip(),
        "street_address": street_address.strip(),
        "postal_code": postal_code.strip(),
        "website": website.strip(),
        "email": email.strip(),
        "legal_entity": legal_entity.strip(),
        "manager_name": manager_name.strip(),
        "manager_role": manager_role.strip(),
        "tier": tier.strip(),
        "persona": persona.strip(),
        "qualify_score": qualify_score,
        "notes": notes.strip(),
    }.items():
        setattr(lead, field, value)
    db.commit()
    return RedirectResponse(f"/lead/{lead_id}", status_code=303)


@app.post("/lead/{lead_id}/stage")
def change_stage(
    lead_id: int,
    request: Request,
    stage: str = Form(...),
    db: Session = Depends(get_db),
):
    lead = db.get(Lead, lead_id)
    if lead and stage in STAGES:
        lead.stage = stage
        if stage == "postcard_sent" and not lead.postcard_sent_on:
            lead.postcard_sent_on = now().date().isoformat()
        db.commit()
    return _back(request, f"/lead/{lead_id}")


@app.post("/lead/{lead_id}/interaction")
def add_interaction(
    lead_id: int,
    request: Request,
    kind: str = Form("note"),
    body: str = Form(""),
    db: Session = Depends(get_db),
):
    lead = db.get(Lead, lead_id)
    if lead is None:
        return RedirectResponse("/", status_code=303)
    db.add(Interaction(lead_id=lead.id, kind=kind, body=body.strip()))

    # gentle auto-advance so the board stays honest
    if kind == "postcard":
        lead.postcard_sent_on = now().date().isoformat()
        if lead.stage in ("to_contact", "contacted"):
            lead.stage = "postcard_sent"
    elif kind in ("call", "email", "visit") and lead.stage == "to_contact":
        lead.stage = "contacted"
    db.commit()
    return RedirectResponse(f"/lead/{lead_id}", status_code=303)


# ---------------------------------------------------------------- create

@app.get("/new", response_class=HTMLResponse)
def new_lead_form(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "lead_form.html", {})


@app.post("/new")
def create_lead(
    request: Request,
    name: str = Form(...),
    city: str = Form(""),
    category: str = Form(""),
    phone: str = Form(""),
    website: str = Form(""),
    email: str = Form(""),
    manager_name: str = Form(""),
    street_address: str = Form(""),
    postal_code: str = Form(""),
    tier: str = Form("B"),
    persona: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    campaign = db.query(Campaign).first()
    if campaign is None:
        campaign = Campaign(name="Leads", client="", notes="")
        db.add(campaign)
        db.flush()
    lead = Lead(
        campaign_id=campaign.id,
        name=name.strip(),
        city=city.strip(),
        category=category.strip(),
        phone=phone.strip(),
        website=website.strip(),
        email=email.strip(),
        manager_name=manager_name.strip(),
        street_address=street_address.strip(),
        postal_code=postal_code.strip(),
        tier=tier.strip(),
        persona=persona.strip(),
        notes=notes.strip(),
        stage="to_contact",
    )
    db.add(lead)
    db.commit()
    return RedirectResponse(f"/lead/{lead.id}", status_code=303)


# ---------------------------------------------------------------- export

@app.get("/export.csv")
def export_csv(db: Session = Depends(get_db)):
    leads = db.scalars(select(Lead).order_by(Lead.qualify_score.desc())).all()
    buf = io.StringIO()
    cols = [
        "ext_id", "name", "chain", "category", "city", "rating", "reviews",
        "phone", "street_address", "postal_code", "website", "email",
        "legal_entity", "manager_name", "manager_role", "qualify_score",
        "tier", "persona", "stage", "postcard_sent_on", "notes",
    ]
    w = csv.writer(buf)
    w.writerow(cols)
    for l in leads:
        w.writerow([getattr(l, c) if getattr(l, c) is not None else "" for c in cols])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=postino-leads.csv"},
    )


# ---------------------------------------------------------------- campaign sync (web → CRM loop)

@app.post("/sync")
def sync(request: Request, src: str = Form(""), db: Session = Depends(get_db)):
    """Pull scan/„Ja" events from the landing and fold them into the board (join by ext_id=token).
    Uses `src` (form) or CAMPAIGN_EVENTS_SRC env. A „Ja" advances the lead to `replied`."""
    source = (src or CAMPAIGN_EVENTS_SRC).strip()
    if source:
        try:
            sync_events(db, source)
        except Exception:
            pass  # a sync hiccup never breaks the board
    return _back(request, "/")
