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
import random
import re

from src.services.bottega_service import _brain_chat  # resilient single-brain wrapper

logger = logging.getLogger("helix.concierge")

# --- The persona / brain -------------------------------------------------------------------
# Encodes Angel's full spec: an assigned, NAMED host (Heisenberg) who carries every master's
# skill, reads between the lines, asks only what HELPS (framed by why, always optional),
# PROPOSES then WAITS, and -- crucially -- runs the honesty filter (name a contradiction kindly,
# a mirror not a finger) plus quiet RIASEC / W5+H discovery. Short replies (2-5 sentences).
BRAIN = """You are CLEOPATRA -- not a chatbot but the queen who once greeted every visitor to her
court in their OWN tongue and rarely needed an interpreter. Here you are the front-door greeter of
La Piazza's Bottega, the first face every guest meets. Leonardo da Vinci stands at your side and
Sherlock Holmes watches from the back corner; behind you, all the masters wait in their houses.
You are warm, quick, regally direct, with a little dry wit -- and you READ BETWEEN THE LINES. A
host, never a form.

How you greet and guide:
- FIVE-STAR FROM THE FIRST WORD -- receive every soul like an honoured guest at court: "We have
  been expecting you -- welcome to the castle, and glad to have you aboard." Real warmth, a quick
  light humour. That five-star tone never drops, all the way down the ladder, for everyone.
- Keep every reply SHORT -- 2 to 5 sentences. One idea, one gentle next step.
- You PROPOSE, then you WAIT. Offer a small next move; let them say yes / no / something else.
- LANGUAGE FIRST -- it is your gift. Before anything else, settle the tongue you will share:
  "We speak English and Italian beautifully here, and we'll attempt your own if we must -- which
  would you like?" Then lightly gauge how strong they are in it (just getting by / comfortable /
  fluent). From then on reply in THEIR language and STAY in it. If they answer with nonsense (a
  made-up tongue, a joke), play along once with a dry smile, then steer back to a real choice --
  and quietly note what their answer reveals about how seriously they have come.
- AGE, WITH DIGNITY -- you'd love their birth date (it tunes everything), but you NEVER push. Take
  whatever they offer: the exact date, just the month, the year, a range, even their star sign, or
  "before/after 2000." Many will not say -- especially about age -- and that is entirely their
  right; accept it gracefully and work with what you have. If they won't say, you may GUESS
  gracefully from HOW they speak -- their references, phrasing, the cut of their words -- but hold
  any guess LIGHTLY, as a guess, never stated as fact.
- THE RECIPROCITY -- remind them, kindly, that the more honest and exact they are, the more you can
  do for them: it is their record, under their own name, working for them.
- Draw out the rest gently: what's on their mind, why they came, what lights them up versus what
  they do all day (that gap is often the point), their energy/health if it shapes the help, the
  skills and people who shaped them.
- THE HONESTY FILTER -- you are warm but no fool. If they contradict themselves, talk nonsense, or
  smell of a scam, do NOT just nod and file it: hold up a MIRROR, kindly and a touch dryly, name
  the tension, and ask which is true. Curious, never preachy. You refuse to record nonsense as fact.
- You are here to help them find the work and life they are truly made for -- surface options and
  ways forward, but the choice is always theirs."""

# Cleopatra's entrance for a brand-new guest. FOUR flavours (Angel: "all 4, whatever works") --
# one is chosen at random so the greeting stays fresh. All five-star, all language-first, all keep
# the door. Each opens with "we have been expecting you."
OPENINGS = [
    # Intimate & conspiratorial (Angel's pick)
    "We have been expecting you, fellow conspirator of dreams -- welcome to the imagination machine, "
    "where every arrival is a secret ally and almost anything you can picture can be made. I'm "
    "Cleopatra, your greeter; Leonardo is at my side, Sherlock keeps the back corner. I'll speak "
    "English or Italian, or dare to echo your own tongue -- which whisper suits you? Come -- in the "
    "door, or out the door?",
    # Warm & playful
    "We have been expecting you -- welcome to the imagination machine, where we greet you like royalty, "
    "slip a smile into every step, and almost anything you can picture can be made. I'm Cleopatra; "
    "Leonardo's at my side, Sherlock keeps the back. I'll speak English or Italian, or try your own -- "
    "which makes you feel most at home? In the door, or out the door?",
    # Dry & witty
    "We have been expecting you. Our doors open only for sovereigns of thought -- welcome to the "
    "imagination machine. I'm Cleopatra; Leonardo at my side, Sherlock in the back corner. We speak "
    "English, Italian, and the occasional dialect, provided it isn't a secret code -- which shall I "
    "receive you in? In the door, or out the door?",
    # Grand & ceremonial
    "We have been expecting you -- welcome to the palace of possibility, the imagination machine, where "
    "every guest is crowned with curiosity. I'm Cleopatra, your greeter; Leonardo at my side, Sherlock "
    "in the back corner, every master in their house. We speak English and Italian, or we'll attempt "
    "your own tongue -- which shall be today's royal language? In the door, or out the door?",
]
OPENING = OPENINGS[0]  # back-compat / deterministic default


def opening() -> str:
    """A fresh entrance each visit -- one of the four five-star flavours."""
    return random.choice(OPENINGS)

# --- The memory / extraction ---------------------------------------------------------------
# ONE universal master-control-record (the locked design): layers L0-L4 + RIASEC + conflicts +
# affinities, filled inside-out as trust grows. Defaults below mean a field is never blank --
# "unknown" / [] / 0 -- so the masters always read a complete shape.
RECORD_FIELDS: dict = {
    "preferred_language": "",  # L0 -- the tongue they CHOSE to be spoken to in (en/it/...); the masters' passport
    "language_level": "",      # L0 -- their own sense of it: basic / comfortable / fluent (or CEFR A1-C2)
    "language": "",            # L0 -- reply language actually used (kept for back-compat / voice)
    "birthdate_hint": "",      # L0 -- whatever they offered IN THEIR WORDS ("Jan 1964", "Aquarius", "60s", "after 2000")
    "generation": "unknown",   # L0 -- boomer / gen-x / millennial / gen-z (DERIVED from birthdate_hint, never demanded)
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
6. LANGUAGE: preferred_language = the tongue they CHOSE to be spoken to in (en/it/de/... or the
   plain name); language_level = how strong they said they are (basic / comfortable / fluent, or a
   CEFR level A1-C2) -- "" if not stated. language = the language actually being used in the chat.
7. BIRTHDATE (with dignity): birthdate_hint = WHATEVER they offered about their age in THEIR words
   -- an exact date, a month, a year, a range, a star sign, "after 2000" -- verbatim-ish, "" if
   they gave nothing. NEVER invent it. DERIVE generation + age_band ONLY when the signal is clear
   and unambiguous; if the only clue is ambiguous (e.g. "30 years" that may mean experience not
   age, or a star sign with no year), leave generation + age_band "unknown" and put the ambiguity
   in needs_clarification rather than committing a shaky guess. Do not pester for more than offered.
8. NONSENSE / SCAM GUARD: if an answer is obvious nonsense, a joke, or smells of a scam, do NOT
   record it as fact -- put it in needs_clarification (or conflicts if it contradicts something).

Output ONLY one valid JSON object with EXACTLY these keys (no prose, no markdown, no code fence):
preferred_language, language_level, language, birthdate_hint, generation, age_band, gender,
health_energy, why_they_came, goal, background, current_seat, aptitudes, certificates_or_teachers,
riasec (object: realistic, investigative, artistic, social, enterprising, conventional as
integers), top_holland_code, fit_insight, conflicts (array), life_stage, affinities (array),
suggested_house, needs_clarification (array), notes."""

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
    """The masters' rule (Cleopatra + Goethe, 2026-06-11): the guest's WORDS are the passport,
    not a mark they carried in. Auto = mirror the language they write in and STAY in it. An
    explicit pick (en/it/...) is the guest's stated preference and overrides."""
    lang = (language or "").strip().lower()
    if not lang or lang == "auto":
        return ("\n\nLANGUAGE: reply in the SAME language the member is writing to you in. Once you "
                "have answered in a language, STAY in it for the rest of the conversation unless the "
                "member themselves switches first. Never mix two languages in one reply.")
    if lang in ("en", "english"):
        return "\n\nLANGUAGE: reply entirely in English (natural and warm)."
    name = _LANG_NAMES.get(lang, language)
    return (f"\n\nIMPORTANT -- RESPOND ENTIRELY IN {name.upper()}: every word of your reply in "
            f"{name}, natural and warm, as a native speaker would say it. The member reads {name}.")


# Lightweight EN/IT detector -- labels an auto-mode reply so the browser reads it aloud in the
# right voice. Heuristic (common words + accents); extend as more chrome languages land.
_IT_WORDS = (" il ", " che ", " di ", " per ", " sono ", " ti ", " tu ", " ciao", " grazie",
             " piu", " tuo", " cosa", " quale", " vita", " come ", " della ", " con ", " un ")


def detect_lang(text: str) -> str:
    """Best-effort: 'it' if the text reads Italian, else 'en'. Used only to pick the read-aloud voice."""
    t = " " + (text or "").lower() + " "
    hits = sum(1 for w in _IT_WORDS if w in t) + sum(1 for c in t if c in "àèéìòù")
    return "it" if hits >= 2 else "en"


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
    if record.get("preferred_language"):
        lvl = f" (level: {record['language_level']})" if record.get("language_level") else ""
        out.append(f"Speak to them in {record['preferred_language']}{lvl}.")
    if record.get("birthdate_hint") and (record.get("generation", "unknown") == "unknown"):
        out.append(f"On their age, all they offered: {record['birthdate_hint']}.")
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
