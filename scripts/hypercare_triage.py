#!/usr/bin/env python3
"""Hypercare Triage runner (PoC-1) — run the triage brain over a real backlog ticket.

Loads one feedback ticket from the Backlog, runs the AI triage (vision + LLM rewrite), stores
the clean version as a BacklogActivity (dual-version — the original is never touched), and prints
messy-in / clean-out so you can SEE it work.

Run INSIDE the app container (it needs the DB + the Ollama/vision providers):
    docker exec helix-platform-sandbox python -m scripts.hypercare_triage          # latest w/ screenshot
    docker exec helix-platform-sandbox python -m scripts.hypercare_triage 137       # a specific BL number

PoC-2 wraps this in a per-env cadence cron; PoC-3 adds the cockpit + notifications + dedup.
"""
import asyncio
import base64
import json
import re
import sys

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import get_settings
from src.db.models.backlog_model import (
    BacklogActivityModel,
    BacklogActivityType,
    BacklogItemModel,
)
from src.services.feedback_triage import triage_feedback


def _decode_shot(data_url):
    m = re.match(r"data:(image/[^;]+);base64,(.*)", data_url or "", re.S)
    if not m:
        return None, None
    try:
        return base64.b64decode(m.group(2)), m.group(1)
    except Exception:
        return None, None


async def main(item_number=None):
    # Build a fresh async engine INSIDE the running loop (a module-level engine made at
    # import time binds its pool to no-loop → greenlet error in a standalone script).
    engine = create_async_engine(get_settings().POSTGRES_ASYNC_URI)
    Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as db:
        q = select(BacklogItemModel)
        if item_number:
            q = q.where(BacklogItemModel.item_number == int(item_number))
        else:
            q = q.where(BacklogItemModel.screenshot_data.isnot(None)).order_by(
                desc(BacklogItemModel.created_at))
        item = (await db.execute(q.limit(1))).scalar_one_or_none()
        if not item:
            print("No ticket found (need a backlog item; --with-screenshot if no number given).")
            return

        shot, mime = _decode_shot(item.screenshot_data)
        print("=" * 64)
        print(f"BL-{item.item_number}  — RAW (as the user filed it)")
        print(f"  title : {item.title}")
        print(f"  desc  : {(item.description or '')[:240]}")
        print(f"  shot  : {'yes (' + (mime or '?') + ')' if shot else 'none'}")

        res = await triage_feedback(
            title=item.title, description=item.description or "", metadata=None,
            screenshot=shot, screenshot_mime=mime or "image/png")
        clean = res["clean"]

        print("-" * 64)
        print(f"AI TRIAGE  (model={res['model'] or 'fallback'}  ai={res['ai']}  tokens={res['tokens']})")
        if res.get("vision"):
            print(f"  vision: {res['vision']}")
        print(f"  ▶ title       : {clean['title']}")
        print(f"  ▶ description : {clean['description']}")
        print(f"  ▶ type/sev    : {clean['type']} / {clean['severity']}   confidence={clean.get('confidence')}")
        print(f"  ▶ area        : {clean.get('area','')}")
        print(f"  ▶ decipherable: {clean.get('decipherable')}")
        if clean.get("questions"):
            print(f"  ▶ questions   : {clean['questions']}")
        if res.get("note"):
            print(f"  ! note        : {res['note']}")

        # Store the clean version as an activity — dual-version audit, original untouched.
        db.add(BacklogActivityModel(
            item_id=item.id,
            activity_type=BacklogActivityType.COMMENT,
            actor="ai-triage",
            old_value=json.dumps({"title": item.title, "description": item.description})[:4000],
            new_value=json.dumps(clean)[:4000],
            comment=f"AI triage (model={res['model'] or 'fallback'}, ai={res['ai']})",
        ))
        await db.commit()
        print("-" * 64)
        print(f"✓ stored AI triage as a BacklogActivity on BL-{item.item_number} (original untouched)")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else None))
