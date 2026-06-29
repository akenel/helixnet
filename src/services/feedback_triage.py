"""Hypercare Triage Brain (PoC-1) — turn a messy user feedback ticket into a clean one.

A user fires the 💬 button with a half-formed title, a vague description and a screenshot.
This reads all of it (text + metadata + a VISION scan of the screenshot) and rewrites it into
ONE clean ticket: a sharp title, a clear description, a type + severity guess, a confidence, and
— if it can't tell what they mean — `decipherable=false` + a list of questions to send back.

The original is NEVER touched; the caller stores this as a BacklogActivity (dual-version audit).

Uses the existing BYO-brain (`src/llm.run_llm`, Ollama local/Turbo) + vision engine
(`src/services/vision`). Degrades gracefully: if a brain is unavailable, returns a clearly-marked
fallback so the cron never crashes and the human just reads the raw ticket.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

from src.llm import run_llm
from src.llm.targets import turbo_or_local
from src.services.vision import VisionDomain, analyze_image

logger = logging.getLogger(__name__)

# Triage rewrites text + reads one screenshot — a capable model on Turbo if configured,
# else whatever local Ollama has. The recipe owns its default model (BYO-brain rule).
_TRIAGE_MODEL_TURBO = "gpt-oss:120b"
_TRIAGE_MODEL_LOCAL = "llama3.2:3b"

# --- VISION lens: describe a POS screenshot for a bug report (not a product photo) ----------
def _coerce_shot(d: dict) -> dict:
    g = lambda k: (str(d.get(k) or "").strip())[:600]
    return {"screen": g("screen"), "visible": g("visible"), "anomalies": g("anomalies")}

TRIAGE_VISION = VisionDomain(
    name="feedback_triage",
    prompt=(
        "You are looking at a screenshot from the 'Banco' point-of-sale web app, attached to a "
        "user bug report. Reply with ONLY a JSON object: "
        '{"screen": which screen/area this is (e.g. Catalog, Receipt, Checkout, Reports), '
        '"visible": a one-line summary of what is on screen, '
        '"anomalies": anything that looks WRONG, broken, misaligned, an error message, an empty '
        "state, or off — or empty string if nothing looks wrong}."
    ),
    coerce=_coerce_shot,
)

# --- Structured output schema for the clean ticket (Ollama enforces this) -------------------
_CLEAN_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "type": {"type": "string", "enum": ["bug", "idea", "question", "cosmetic", "other"]},
        "severity": {"type": "string", "enum": ["blocking", "annoying", "cosmetic"]},
        "area": {"type": "string"},
        "confidence": {"type": "number"},
        "decipherable": {"type": "boolean"},
        "questions": {"type": "array", "items": {"type": "string"}},
        "duplicate_of": {"type": "integer"},
    },
    "required": ["title", "description", "type", "severity", "confidence", "decipherable",
                 "duplicate_of"],
}

_SYSTEM = (
    "You are the QA triage assistant for the Banco point-of-sale app. Users (cashiers, the shop "
    "owner) fire quick feedback with a rough title, a vague description, and usually a screenshot. "
    "Rewrite their report into ONE clean, professional ticket an engineer can act on. Rules: keep "
    "their MEANING, never invent features they didn't ask for; write a crisp imperative title and "
    "a clear 2-4 sentence description; classify type + severity; set `area` to the screen if known; "
    "give a 0..1 confidence. If you genuinely can't tell what they want, set decipherable=false and "
    "put 1-3 specific questions in `questions`. "
    "DEDUP: you may be given a list of EXISTING OPEN tickets. If this report is essentially the "
    "SAME underlying problem as one of them, set `duplicate_of` to that ticket's number; otherwise "
    "set `duplicate_of` to 0. Only call it a duplicate if it's clearly the same issue, not merely "
    "the same screen. Output JSON only."
)


def _fmt_meta(metadata: Any) -> str:
    if not metadata:
        return ""
    if isinstance(metadata, str):
        return metadata[:800]
    try:
        keep = {k: metadata[k] for k in ("path", "env", "build", "user", "platform", "viewport",
                                         "sales_today", "health", "online") if k in metadata}
        return json.dumps(keep)[:800]
    except Exception:
        return str(metadata)[:800]


async def triage_feedback(
    *,
    title: str,
    description: str = "",
    metadata: Any = None,
    screenshot: Optional[bytes] = None,
    screenshot_mime: str = "image/png",
    existing: Optional[list] = None,
) -> dict:
    """Messy ticket in → clean ticket out. Returns:
        {clean: {...schema...}, vision: {screen,visible,anomalies}|None,
         model, tokens, ai: bool, note: str|None}
    Never raises for brain/transport issues — returns ai=False + a note instead."""
    # 1) VISION scan of the screenshot (best-effort).
    vision = None
    if screenshot:
        try:
            # Vision provider is configurable; default Gemini (the shop's Snap-&-fill provider).
            # Lights up when BH_GOOGLE_API_KEY is set; degrades gracefully otherwise. (Turbo
            # hosts the text model but not a vision one, so ollama isn't a working default here.)
            res = await analyze_image(screenshot, screenshot_mime, domain=TRIAGE_VISION,
                                      provider=os.getenv("BANCO_VISION_PROVIDER", "gemini"))
            vision = res.get("data")
            if res.get("note"):
                logger.info("triage vision note: %s", res["note"])
        except Exception as e:  # noqa: BLE001
            logger.warning("triage vision failed: %s", e)

    # 2) Build the rewrite prompt from everything we know.
    parts = [f"RAW TITLE: {title or '(none)'}", f"RAW DESCRIPTION: {description or '(none)'}"]
    meta = _fmt_meta(metadata)
    if meta:
        parts.append(f"SYSTEM METADATA: {meta}")
    if vision:
        parts.append("SCREENSHOT (vision): " + json.dumps(vision))
    if existing:
        listing = "; ".join(f"[#{e['n']}] {e['title']}" for e in existing[:30])
        parts.append("EXISTING OPEN TICKETS (for dedup): " + listing)
    user_prompt = "\n".join(parts) + "\n\nReturn the clean ticket as JSON."

    # 3) Rewrite via the BYO-brain with an enforced schema.
    try:
        target = turbo_or_local(_TRIAGE_MODEL_TURBO, _TRIAGE_MODEL_LOCAL)
        result = await run_llm(user_prompt, target=target, system=_SYSTEM, schema=_CLEAN_SCHEMA)
        clean = json.loads(result.text)
        return {"clean": clean, "vision": vision, "model": result.model,
                "tokens": result.tokens, "ai": True, "note": None}
    except Exception as e:  # noqa: BLE001 — brain down / bad JSON → graceful fallback
        logger.warning("triage rewrite failed: %s", e)
        return {
            "clean": {
                "title": (title or "Untitled feedback")[:120],
                "description": description or "(no description)",
                "type": "other", "severity": "annoying",
                "area": (vision or {}).get("screen", ""),
                "confidence": 0.0, "decipherable": False,
                "questions": ["AI triage was unavailable — please review the raw ticket by hand."],
                "duplicate_of": 0,
            },
            "vision": vision, "model": "", "tokens": 0, "ai": False,
            "note": f"AI unavailable ({type(e).__name__})",
        }


# --- Resolution summary: the whole ticket as a 3-4 sentence story a busy owner can skim ------
_RESOLUTION_SYSTEM = (
    "You write the RESOLUTION for a small shop's feedback ticket — so a busy owner can read 3-4 "
    "short sentences and understand the whole story without digging into the details. Use plain, "
    "concrete, friendly words. NO jargon, NO bullet points — ONE short paragraph. Cover, in order: "
    "what the person reported, what we understood/decided, what was actually done (mention the code "
    "change / commit short-hash if there was one), and the outcome (fixed and confirmed, or no "
    "change was needed, or it was withdrawn). Write it like a little story someone can read at a "
    "glance. 3-4 sentences, nothing more. Stick to the facts in the history — never invent a step "
    "(like a confirmation or a close) that isn't there."
)


async def summarize_resolution(story_lines: list) -> dict:
    """Turn an ordered list of plain story beats → one Lego-language resolution paragraph.
    Always returns SOMETHING readable: falls back to joining the beats if the brain is down."""
    beats = [s for s in (story_lines or []) if s]
    story = "\n".join(f"- {s}" for s in beats)
    try:
        target = turbo_or_local(_TRIAGE_MODEL_TURBO, _TRIAGE_MODEL_LOCAL)
        result = await run_llm("Ticket history (oldest first):\n" + story +
                               "\n\nWrite the resolution paragraph.",
                               target=target, system=_RESOLUTION_SYSTEM)
        text = (result.text or "").strip()
        if text:
            return {"text": text, "model": result.model, "ai": True}
    except Exception as e:  # noqa: BLE001 — brain down → a plain, still-useful fallback
        logger.warning("resolution summary failed: %s", e)
    return {"text": " ".join(beats) or "This report has been closed.", "model": "", "ai": False}
