"""The shape of a lead, a campaign, and every touch in between."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

# The pipeline, in order. The board shows the first five; lost/dropped live in the table.
STAGES = ["to_contact", "contacted", "postcard_sent", "replied", "won", "lost", "dropped"]
STAGE_LABELS = {
    "to_contact": "To Contact",
    "contacted": "Contacted",
    "postcard_sent": "Postcard Sent",
    "replied": "Replied",
    "won": "Won",
    "lost": "Lost",
    "dropped": "Dropped",
}
BOARD_STAGES = ["to_contact", "contacted", "postcard_sent", "replied", "won"]

INTERACTION_KINDS = ["call", "email", "postcard", "visit", "note"]

# The full lead→close journey — a per-lead guided checklist (richer than the coarse `stage`).
# (key, label, hint) — the hint tells Angel what to DO / CAPTURE at that step.
JOURNEY_STEPS = [
    ("scope_out",  "Scope-out visit",             "Walk in as a customer, buy a pack of papers. CAPTURE: front photo, counter photo, 20s video. READ it — parking, vibe, owner, fit FOR YOU? (or strike off → Dropped)"),
    ("review",     "Honest Google review",        "Leave a genuine review. Paste the link in the note."),
    ("postcard",   "Personalized postcard mailed","Card with the visit line + the shop photo. Note the date + which card."),
    ("response",   "Response received",           "Scan / Ja / call-in (the QR auto-logs it). Note it."),
    ("call",       "Phone / follow-up",           "The in-language call or drop-in. Note the outcome."),
    ("discovery",  "Discovery meeting",           "First official look at his books + work processes. When + what you saw."),
    ("offer",      "Offer made",                  "Terms / price. Note what you offered."),
    ("migration",  "Migration & cutover plan",    "How we move him over. Website: tie-in / improve / new / none?"),
    ("contract",   "Contract signed — CLOSED",    "Terms agreed, signed. The win."),
    ("onboarding", "Up & running",                "Onboarded, live. Beyond the close."),
]


def now() -> datetime:
    return datetime.now(timezone.utc)


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    client: Mapped[str] = mapped_column(String(200), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    leads: Mapped[list["Lead"]] = relationship(back_populates="campaign")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    ext_id: Mapped[str] = mapped_column(String(20), default="")

    # identity
    name: Mapped[str] = mapped_column(String(200))
    chain: Mapped[str] = mapped_column(String(120), default="")
    category: Mapped[str] = mapped_column(String(60), default="")
    city: Mapped[str] = mapped_column(String(120), default="")

    # contact / postcard target
    phone: Mapped[str] = mapped_column(String(60), default="")
    street_address: Mapped[str] = mapped_column(String(200), default="")
    postal_code: Mapped[str] = mapped_column(String(20), default="")
    canton: Mapped[str] = mapped_column(String(4), default="")
    website: Mapped[str] = mapped_column(String(200), default="")
    email: Mapped[str] = mapped_column(String(200), default="")

    # discovery provenance (from the search.ch sweep — unverified until enrich)
    contact_hint: Mapped[str] = mapped_column(String(200), default="")  # raw "person" field
    directory_url: Mapped[str] = mapped_column(String(300), default="")
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    sources: Mapped[str] = mapped_column(Text, default="")

    # qualification
    legal_entity: Mapped[str] = mapped_column(String(60), default="")
    manager_name: Mapped[str] = mapped_column(String(120), default="")
    manager_role: Mapped[str] = mapped_column(String(120), default="")
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    reviews: Mapped[int] = mapped_column(Integer, default=0)
    qualify_score: Mapped[int] = mapped_column(Integer, default=0)
    tier: Mapped[str] = mapped_column(String(10), default="")
    persona: Mapped[str] = mapped_column(String(30), default="")

    # campaign generation (enrich + render)
    language: Mapped[str] = mapped_column(String(4), default="de")     # de/fr/it/en — region drives card+landing
    scoop_line: Mapped[str] = mapped_column(String(300), default="")   # warm personalization hook (empathic, not a dossier)

    # pipeline
    stage: Mapped[str] = mapped_column(String(20), default="to_contact")
    postcard_sent_on: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    journey: Mapped[str] = mapped_column(Text, default="{}")   # per-step checklist JSON: {key:{done,on,note}}

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    campaign: Mapped["Campaign"] = relationship(back_populates="leads")
    interactions: Mapped[list["Interaction"]] = relationship(
        back_populates="lead", cascade="all, delete-orphan"
    )

    @property
    def stage_label(self) -> str:
        return STAGE_LABELS.get(self.stage, self.stage)

    @property
    def full_address(self) -> str:
        parts = [self.street_address, f"{self.postal_code} {self.city}".strip()]
        return ", ".join(p for p in parts if p)

    @property
    def artifact_prefix(self) -> str:
        """Object-store prefix for this lead's blobs (photos, logo, cards, enrichment.json)."""
        return f"leads/{self.ext_id or ('id-' + str(self.id))}/"

    @property
    def journey_state(self) -> dict:
        import json
        try:
            return json.loads(self.journey or "{}")
        except Exception:
            return {}

    @property
    def next_step_key(self) -> str:
        state = self.journey_state
        for key, _label, _hint in JOURNEY_STEPS:
            if not state.get(key, {}).get("done"):
                return key
        return ""

    @property
    def has_address(self) -> bool:
        return bool(self.street_address and self.postal_code)


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"))
    kind: Mapped[str] = mapped_column(String(20), default="note")
    body: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    lead: Mapped["Lead"] = relationship(back_populates="interactions")
