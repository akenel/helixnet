# File: src/services/day_survey.py
# Purpose: the AI End-of-Day Survey recipe — "Banco drafts the day for you."
#
# At closeout the day's sales are ALREADY in the system. So instead of asking a tired
# cashier to fill a survey, Banco reads the day's numbers and DRAFTS it for them: a warm
# one-or-two-line note + a busy/steady/slow read + a rough footfall guess. The human just
# confirms or tweaks. Velocity-driven — the survey writes itself; the human signs off.
#
# Rides the EXISTING brain (src.llm.run_llm, BYO-brain via turbo_or_local) and the EXISTING
# tables (transactions + line_items). Capture-only: the confirmed text lands in the time
# entry's `description` — NO schema change, no new persistence.
#
# RESILIENT by design (the resilience acceptance test): if the brain is down or no key is
# set, we still return a clean deterministic draft built straight from the numbers. The
# survey NEVER blocks closeout — a cashier on a dead connection still closes their day.

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo
import os

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import (
    ProductModel,
    TransactionModel,
    LineItemModel,
    TransactionStatus,
    PaymentMethod,
)
from src.llm import run_llm, turbo_or_local

logger = logging.getLogger("helix.day_survey")

SHOP_TZ = ZoneInfo(os.environ.get("HX_SHOP_TZ", "Europe/Zurich"))

# Default brains (DATA — a recipe owns its model; backend chosen by turbo_or_local).
SURVEY_MODEL = os.getenv("LPCX_SURVEY_MODEL", os.getenv("LPCX_BIO_MODEL", "gpt-oss:120b"))
LOCAL_MODEL = os.getenv("OLLAMA_MODEL", "tinyllama:latest")

# The outbound Service Interface — ENFORCED on the model so the shape can't drift.
_SURVEY_SCHEMA = {
    "type": "object",
    "properties": {
        "busy_level": {"type": "string", "enum": ["busy", "steady", "slow"]},
        "footfall_estimate": {"type": "integer"},
        "summary": {"type": "string"},
        "highlight": {"type": "string"},
    },
    "required": ["busy_level", "footfall_estimate", "summary"],
}

_SYSTEM = (
    "You are Banco, a friendly Swiss head-shop till. At end of day you write the cashier's "
    "shift note FOR them from the day's numbers, so they just confirm it. Write in the FIRST "
    "PERSON, warm and plain, as the cashier would say it to the boss. One or two short "
    "sentences for the summary — no hype, no emojis, no markdown. Be honest to the numbers: "
    "a slow day is a slow day. Estimate footfall as roughly the number of sales (some people "
    "buy more than once, some browse and leave — a rough human guess is fine)."
)


async def gather_day_facts(db: AsyncSession, user_id: str, target_date: datetime | None = None) -> dict:
    """The hard numbers for ONE cashier's day — the raw material the survey is drafted from."""
    day = (target_date or datetime.now(SHOP_TZ)).date()
    start = datetime.combine(day, datetime.min.time(), tzinfo=SHOP_TZ)
    end = datetime.combine(day, datetime.max.time(), tzinfo=SHOP_TZ)

    rows = (await db.execute(select(TransactionModel).where(and_(
        TransactionModel.cashier_id == user_id,
        TransactionModel.status == TransactionStatus.COMPLETED,
        TransactionModel.completed_at >= start,
        TransactionModel.completed_at <= end,
    )))).scalars().all()

    count = len(rows)
    total = float(sum(float(t.total or 0) for t in rows))
    cash = float(sum(float(t.total or 0) for t in rows if t.payment_method == PaymentMethod.CASH))
    card = total - cash
    tx_ids = [t.id for t in rows]

    # Top sellers today (catalog name, else the custom-line note), free treats excluded.
    top_sellers: list[dict] = []
    items_sold = 0
    if tx_ids:
        name_expr = func.coalesce(ProductModel.name, LineItemModel.notes, "Item")
        lrows = (await db.execute(
            select(name_expr.label("name"), func.sum(LineItemModel.quantity).label("qty"))
            .join(ProductModel, ProductModel.id == LineItemModel.product_id, isouter=True)
            .where(and_(LineItemModel.transaction_id.in_(tx_ids), LineItemModel.is_giveaway == False))
            .group_by(name_expr)
            .order_by(func.sum(LineItemModel.quantity).desc())
        )).all()
        items_sold = sum(int(r.qty or 0) for r in lrows)
        top_sellers = [{"name": r.name, "quantity": int(r.qty or 0)} for r in lrows[:3]]

    # Span of the day (first → last sale) and the busiest hour — texture for the draft.
    first_sale = last_sale = busiest_hour = None
    times = [t.completed_at for t in rows if t.completed_at]
    if times:
        times.sort()
        first_sale = times[0].astimezone(SHOP_TZ).strftime("%H:%M")
        last_sale = times[-1].astimezone(SHOP_TZ).strftime("%H:%M")
        from collections import Counter
        h = Counter(t.astimezone(SHOP_TZ).hour for t in times).most_common(1)[0][0]
        busiest_hour = f"{h:02d}:00–{(h + 1) % 24:02d}:00"

    return {
        "date": day.isoformat(),
        "weekday": day.strftime("%A"),
        "transaction_count": count,
        "total_sales": round(total, 2),
        "cash_sales": round(cash, 2),
        "card_sales": round(card, 2),
        "items_sold": items_sold,
        "top_sellers": top_sellers,
        "first_sale": first_sale,
        "last_sale": last_sale,
        "busiest_hour": busiest_hour,
    }


def _busy_level(count: int) -> str:
    """A simple, honest rule of thumb for the fallback draft (and a sanity floor for the LLM)."""
    if count >= 25:
        return "busy"
    if count >= 8:
        return "steady"
    return "slow"


def _fallback_draft(facts: dict) -> dict:
    """Deterministic draft straight from the numbers — used when no brain is available.
    The survey must NEVER block closeout, so this is always a clean, usable answer."""
    count = facts["transaction_count"]
    level = _busy_level(count)
    tops = facts.get("top_sellers") or []
    if count == 0:
        summary = "Quiet one — no sales rang through on my till today."
    else:
        lead = {"busy": "Good busy day", "steady": "Steady day", "slow": "Slow day"}[level]
        money = f"CHF {facts['total_sales']:.2f} across {count} sale{'s' if count != 1 else ''}"
        tail = f"; {tops[0]['name']} moved best." if tops else "."
        summary = f"{lead} — {money}{tail}"
    return {
        "busy_level": level,
        "footfall_estimate": count,
        "summary": summary,
        "highlight": (tops[0]["name"] if tops else ""),
        "ai": False,
    }


def _facts_prompt(facts: dict) -> str:
    tops = ", ".join(f"{t['name']} (x{t['quantity']})" for t in facts.get("top_sellers") or []) or "none"
    span = (f"{facts['first_sale']}–{facts['last_sale']}" if facts.get("first_sale") else "no sales")
    return (
        f"Here is my day at the till ({facts['weekday']}):\n"
        f"- Sales rung up: {facts['transaction_count']}\n"
        f"- Takings: CHF {facts['total_sales']:.2f} (cash CHF {facts['cash_sales']:.2f}, "
        f"card CHF {facts['card_sales']:.2f})\n"
        f"- Items sold: {facts['items_sold']}\n"
        f"- Top sellers: {tops}\n"
        f"- Active span: {span}; busiest around {facts.get('busiest_hour') or 'n/a'}\n\n"
        "Write my end-of-day note as JSON with keys: busy_level (busy|steady|slow), "
        "footfall_estimate (integer), summary (1–2 first-person sentences), highlight "
        "(the day's standout product or moment, short — '' if nothing stands out)."
    )


async def _shop_weather(db: AsyncSession) -> str:
    """Today's weather at the shop, from its own address — so the note's weather is REAL, not typed.
    Angel: "when it's a rainy day and only two sales, she shouldn't have to fake it." Never raises."""
    try:
        from sqlalchemy import select as _select
        from src.db.models.store_settings_model import StoreSettingsModel
        from src.services.weather import daily_weather_line
        store = (await db.execute(
            _select(StoreSettingsModel).order_by(StoreSettingsModel.store_number))).scalars().first()
        if not store or not (getattr(store, "city", "") or "").strip():
            return ""
        return await daily_weather_line(store.city, getattr(store, "country", "") or "")
    except Exception:
        return ""


async def draft_day_survey(db: AsyncSession, user_id: str, target_date: datetime | None = None) -> dict:
    """The recipe: gather the day's facts → ask the brain to draft the survey → resilient
    fallback. Returns {busy_level, footfall_estimate, summary, highlight, weather, ai, facts}.
    `weather` is auto-fetched from the shop's address (free, keyless) so the operator never types it."""
    facts = await gather_day_facts(db, user_id, target_date)
    weather = await _shop_weather(db)

    # No sales = nothing for the brain to say better than the honest fallback. Skip the call.
    if facts["transaction_count"] == 0:
        out = _fallback_draft(facts)
        out["facts"] = facts
        out["weather"] = weather
        return out

    try:
        target = turbo_or_local(SURVEY_MODEL, LOCAL_MODEL)
        res = await run_llm(_facts_prompt(facts), target=target, system=_SYSTEM, schema=_SURVEY_SCHEMA)
        import json
        data = json.loads(res.text)
        draft = {
            "busy_level": (data.get("busy_level") or _busy_level(facts["transaction_count"])).strip().lower(),
            "footfall_estimate": int(data.get("footfall_estimate") or facts["transaction_count"]),
            "summary": (data.get("summary") or "").strip(),
            "highlight": (data.get("highlight") or "").strip(),
            "ai": True,
        }
        if draft["busy_level"] not in ("busy", "steady", "slow"):
            draft["busy_level"] = _busy_level(facts["transaction_count"])
        if not draft["summary"]:
            draft = _fallback_draft(facts)
        draft["facts"] = facts
        draft["weather"] = weather
        return draft
    except Exception:  # noqa: BLE001 — any brain failure degrades to the honest fallback.
        logger.warning("day-survey brain call failed; using deterministic draft", exc_info=True)
        out = _fallback_draft(facts)
        out["facts"] = facts
        out["weather"] = weather
        out["weather"] = weather
        return out


# Levels → the chip label the cashier sees. Kept here so the note composer and the UI agree.
_LEVEL_LABEL = {"busy": "Busy", "steady": "Steady", "slow": "Slow"}


def compose_note(busy_level: str, footfall: int | None, weather: str, summary: str) -> str:
    """Fold the confirmed survey into ONE human-readable note for the time entry's
    `description` (what Felix reads next to the hard numbers). No JSON in the books."""
    bits = []
    lvl = _LEVEL_LABEL.get((busy_level or "").lower())
    head = []
    if lvl:
        head.append(lvl)
    if footfall:
        head.append(f"~{int(footfall)} customers")
    if head:
        bits.append(" · ".join(head))
    if (weather or "").strip():
        bits.append(f"Weather: {weather.strip()}")
    if (summary or "").strip():
        bits.append(summary.strip())
    return "\n".join(bits)
