# File: src/compute/concierge.py
# Purpose: The Concierge (task #74) -- Heisenberg, the assigned front-door host of the Bottega
# who builds a member's master-control-record through friendly chat. Both halves proven in the
# terminal POC (2026-06-11): the BRAIN talks right (warm, dry, proposes-and-waits, reads between
# the lines, honesty filter, RIASEC + W5+H discovery) and the MEMORY remembers right (chat ->
# structured record, no invention). This module is the wiring of that POC.
#
# It routes EVERY brain call through the single src.llm wrapper (_brain_chat) -- the BYO-brain
# rule: one place an LLM call happens. The prototype poked /api/chat directly for multi-turn;
# here we flatten the transcript into one user turn instead, so we keep the 404-fallback +
# BrainUnavailable resilience for free.

import json
import logging
import re

from src.services.bottega_service import _brain_chat  # resilient single-brain wrapper

logger = logging.getLogger("helix.concierge")

# --- The persona / brain -------------------------------------------------------------------
# Encodes Angel's full spec: an assigned, NAMED host (Heisenberg) who carries every master's
# skill, reads between the lines, asks only what HELPS (framed by why, always optional),
# PROPOSES then WAITS, and -- crucially -- runs the honesty filter (name a contradiction kindly,
# a mirror not a finger) plus quiet RIASEC / W5+H discovery. Short replies (2-5 sentences).
BRAIN = """You are the CONCIERGE of La Piazza's Bottega -- the maitre d' at the front door,
assigned BY NAME to this one member as their personal guide. Your name for them is Heisenberg:
calm, precise, warm, with a little dry wit. You carry every master's skill (Da Vinci, Sherlock
and the rest are in your back pocket) and you READ BETWEEN THE LINES. You are a friend, never a
form.

How you work:
- Keep every reply SHORT -- 2 to 5 sentences. One idea, one gentle next step.
- You PROPOSE, then you WAIT. Offer a small next move and let them say yes / no / something else.
- Ask only what HELPS them, and say WHY it helps. Everything is optional -- never demand a
  birthdate or a number; "born before or after 2000? it changes how I help" is enough.
- Gently draw out who they are: what's on their mind, what they came here for, what lights them
  up versus what they actually do all day (that gap is often the whole point), their energy and
  health if it shapes the help, the skills and people who shaped them.
- THE HONESTY FILTER: if they contradict themselves -- a goal that fights their own behaviour, or
  two things that can't both be true -- do NOT just nod and file it. Hold up a MIRROR, kindly and
  a touch dryly: name the tension and ask which one is the real priority. Curious, never preachy.
  Observation, not rebuke. You refuse to quietly record nonsense.
- You are here to help them find the work and the life they are truly made for -- surface
  options and ways forward, but the choice is always theirs."""

# The opening for a brand-new member (empty profile) -- Angel's copy, kept verbatim-ish.
OPENING = (
    "You've just stepped into the imagination machine -- in here you can make almost anything you "
    "can picture. I'm Heisenberg, your guide, and I've got Da Vinci and Sherlock in my back "
    "pocket. Thing is, I know nothing about you yet, so I can't put any of that to work. Help me "
    "help you: born before 2000, or after? It changes how I steer. If you're useful to me, I'm "
    "useful to you. So -- in the door, or out the door?"
)

# --- The memory / extraction ---------------------------------------------------------------
# ONE universal master-control-record (the locked design): layers L0-L4 + RIASEC + conflicts +
# affinities, filled inside-out as trust grows. Defaults below mean a field is never blank --
# "unknown" / [] / 0 -- so the masters always read a complete shape.
RECORD_FIELDS: dict = {
    "language": "",            # L0 -- preferred reply language (ISO-ish: en, it, de...)
    "generation": "unknown",   # L0 -- boomer / gen-x / millennial / gen-z (derived, never demanded)
    "age_band": "unknown",     # L0 -- "before-2000" | "after-2000" | unknown (sets the life lens)
    "gender": "unknown",       # L0
    "health_energy": "",       # L1 -- anything that shapes the help (injuries, energy, mobility)
    "why_they_came": "",       # L1 -- the Hotel California question: why are you here
    "goal": "",                # L1 -- what they want
    "background": "",          # L2 -- history / trade / years
    "current_seat": "",        # L2 -- what they actually do today
    "aptitudes": [],           # L2 -- what they're good at / drawn to
    "certificates_or_teachers": [],  # L2 -- certs + the people who shaped them
    "riasec": {                # L1 -- Holland interest themes 0-100 (INTEREST, not aptitude)
        "realistic": 0, "investigative": 0, "artistic": 0,
        "social": 0, "enterprising": 0, "conventional": 0,
    },
    "top_holland_code": "",    # L1 -- e.g. "RIA"
    "fit_insight": "",         # L1 -- where they'd THRIVE vs where they ARE (the mismatch)
    "conflicts": [],           # honesty filter -- self-contradictions, recorded not resolved
    "life_stage": "unknown",   # L3 lens -- launching / building / peak / transitioning / legacy
    "affinities": [],          # the team they build: masters/houses they gravitate to
    "suggested_house": "",     # which of the 15 Houses fits (blank until clear)
    "needs_clarification": [], # open questions the concierge still wants to resolve
    "notes": "",               # free margin -- the narrative the boxes can't hold
}

EXTRACT_SYS = """You are the MEMORY of the Concierge. Read the conversation and extract the
member's master-control-record. Extract ONLY what they revealed or clearly implied -- NEVER
invent; use "" or [] or "unknown" when you do not know. Restraint matters as much as accuracy.

Do these expert jobs as you go:
1. SCORE RIASEC (Holland interest themes) 0-100 from what they revealed -- this measures INTEREST,
   not raw skill: realistic (hands/tools/outdoors/animals), investigative (analysis/ideas),
   artistic (creative/design/expression), social (helping/teaching/people), enterprising
   (leading/selling/persuading), conventional (organising/data/structure/routine).
2. top_holland_code: the 2-3 strongest themes as letters, e.g. "RIA".
3. fit_insight: name honestly where they'd likely THRIVE versus where they currently ARE -- the
   mismatch, if one exists. That gap is the point. "" if there is genuinely no signal.
4. conflicts: list any self-contradictions they expressed (a goal that fights their behaviour, or
   two claims that can't both be true). RECORD them, do not resolve them. [] if none.
5. life_stage: launching / building / peak / transitioning / legacy -- the lens, from age_band +
   what they said. "unknown" if unclear.

Output ONLY one valid JSON object with EXACTLY these keys (no prose, no markdown, no code fence):
language, generation, age_band, gender, health_energy, why_they_came, goal, background,
current_seat, aptitudes, certificates_or_teachers, riasec (object: realistic, investigative,
artistic, social, enterprising, conventional as integers), top_holland_code, fit_insight,
conflicts (array), life_stage, affinities (array), suggested_house, needs_clarification (array),
notes."""

_LANG_NAMES = {"it": "Italian", "de": "German", "fr": "French", "es": "Spanish",
               "pt": "Portuguese", "nl": "Dutch", "en": "English"}


def _strip_think(s: str) -> str:
    return re.sub(r"<think>.*?</think>", "", s or "", flags=re.S).strip()


def blank_record() -> dict:
    """A fresh record with every field present and safely defaulted (never blank to the masters)."""
    return json.loads(json.dumps(RECORD_FIELDS))  # deep copy of the locked shape


def _transcript_block(transcript: list[dict]) -> str:
    """Flatten the turn list into a readable MEMBER/YOU transcript for a single brain turn."""
    lines = []
    for m in transcript:
        who = "MEMBER" if m.get("role") == "member" else "YOU"
        lines.append(f"{who}: {m.get('content', '').strip()}")
    return "\n".join(lines)


def _known_block(record: dict) -> str:
    """A compact summary of what we already know -- so the concierge doesn't re-ask answered things."""
    if not record:
        return "(nothing yet)"
    bits = []
    for k in ("generation", "age_band", "goal", "why_they_came", "background", "current_seat",
              "health_energy", "top_holland_code", "fit_insight", "life_stage", "suggested_house"):
        v = record.get(k)
        if v and v != "unknown":
            bits.append(f"{k.replace('_', ' ')}: {v}")
    for k in ("aptitudes", "affinities", "conflicts", "certificates_or_teachers"):
        v = record.get(k)
        if v:
            bits.append(f"{k.replace('_', ' ')}: {', '.join(str(x) for x in v)}")
    return "; ".join(bits) if bits else "(nothing yet)"


def _lang_clause(language: str) -> str:
    lang = (language or "").strip().lower()
    if not lang or lang in ("en", "english"):
        return ""
    name = _LANG_NAMES.get(lang, language)
    return (f"\n\nIMPORTANT -- RESPOND ENTIRELY IN {name.upper()}: every word of your reply in "
            f"{name}, natural and warm, as a native speaker would say it. The member reads {name}.")


async def concierge_reply(transcript: list[dict], record: dict, language: str = "") -> str:
    """One Heisenberg turn. The transcript ends with the member's latest message; we return the
    concierge's next reply. Flattened to a single brain call (BYO-brain rule)."""
    user = (f"What you already know about this member:\n{_known_block(record)}\n\n"
            f"The conversation so far:\n{_transcript_block(transcript)}\n\n"
            "Reply now, as Heisenberg -- one short turn (2-5 sentences). If they just contradicted "
            "themselves or what they do clashes with what they want, gently hold up the mirror.")
    reply = await _brain_chat(BRAIN + _lang_clause(language), user)
    return _strip_think(reply)


async def extract_record(transcript: list[dict]) -> dict:
    """Second pass: read the whole transcript -> a structured record. JSON-mode + prompt + regex
    (the proven gotcha-proof path: gpt-oss did not honour the format param alone)."""
    raw = await _brain_chat(EXTRACT_SYS, _transcript_block(transcript), json_mode=True)
    raw = _strip_think(raw)
    a, b = raw.find("{"), raw.rfind("}")
    if a < 0 or b <= a:
        raise ValueError("extractor returned no JSON object")
    parsed = json.loads(raw[a:b + 1])
    return parsed if isinstance(parsed, dict) else {}


def _meaningful(v) -> bool:
    """Is this newly-extracted value worth writing over what we had?"""
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip() != "" and v.strip().lower() != "unknown"
    if isinstance(v, (list, dict)):
        return len(v) > 0
    if isinstance(v, (int, float)):
        return v != 0
    return True


def merge_record(old: dict, new: dict) -> dict:
    """Fold a fresh extraction into the standing record WITHOUT clobbering known facts with blanks.
    Scalars: new wins only if meaningful. Lists: union (order-preserving, deduped). riasec: take the
    latest scores (more conversation = better signal) for any theme that moved off zero."""
    out = blank_record()
    out.update({k: v for k, v in (old or {}).items() if k in out})
    for k, default in RECORD_FIELDS.items():
        nv = (new or {}).get(k)
        if k == "riasec":
            cur = dict(out.get("riasec") or {})
            for theme in RECORD_FIELDS["riasec"]:
                score = (nv or {}).get(theme) if isinstance(nv, dict) else None
                try:
                    score = int(score)
                except (TypeError, ValueError):
                    score = 0
                if score:
                    cur[theme] = max(0, min(100, score))
            out["riasec"] = cur
        elif isinstance(default, list):
            seen, merged = set(), []
            for item in list(out.get(k) or []) + (list(nv) if isinstance(nv, list) else []):
                key = str(item).strip().lower()
                if key and key not in seen:
                    seen.add(key)
                    merged.append(item)
            out[k] = merged
        elif _meaningful(nv):
            out[k] = nv
    return out


def record_to_portrait(record: dict) -> list[str]:
    """Render the record into plain-language sentences a historical master reads (Phase 3 -- close
    the loop). Returns a list of sentence fragments to fold into _build_portrait. Never apps/jargon."""
    if not record:
        return []
    out = []
    if record.get("why_they_came"):
        out.append(f"Why they came: {record['why_they_came']}")
    if record.get("goal"):
        out.append(f"What they want: {record['goal']}.")
    if record.get("background"):
        out.append(f"Their background: {record['background']}.")
    if record.get("current_seat") and record.get("fit_insight"):
        out.append(f"Today they sit in {record['current_seat']}, but {record['fit_insight']}.")
    elif record.get("fit_insight"):
        out.append(record["fit_insight"])
    apt = record.get("aptitudes") or []
    if apt:
        out.append("What lights them up: " + ", ".join(str(a) for a in apt[:6]) + ".")
    conf = record.get("conflicts") or []
    if conf:
        out.append("Tensions to hold gently (don't lecture): " + "; ".join(str(c) for c in conf[:3]) + ".")
    if record.get("life_stage") and record["life_stage"] != "unknown":
        out.append(f"They are in their {record['life_stage']} stage of life.")
    if record.get("health_energy"):
        out.append(f"On their body/energy: {record['health_energy']}.")
    return out
