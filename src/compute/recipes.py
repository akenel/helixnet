# File: src/compute/recipes.py
# Purpose: The "Chinese menu" -- procedure-as-code. A recipe is DATA, not bespoke code:
#   {slug, title, inputs[], system, prompt, output}. One generic runner executes any
#   recipe. Adding use #4..#100 = a new dict entry, not an engineering project.

import json
import os
import re
import uuid
from pathlib import Path

import httpx

from src.services.bottega_service import _brain_chat, extract_text

# Render worker (BYOH): the "muscle" that turns text into media (Piper + ffmpeg).
# It runs OUTSIDE the app (the app has no piper/ffmpeg) -- a sidecar container in
# staging/prod, or your laptop in dev. The app just calls it by URL.
RENDER_WORKER_URL = os.getenv("RENDER_WORKER_URL", "http://localhost:8800").rstrip("/")
MEDIA_DIR = Path(os.getenv("BOTTEGA_MEDIA_DIR", "/tmp/bottega-media"))

# Reasoning models (DeepSeek-R1 et al.) emit their chain-of-thought inside
# <think>...</think> before the real answer. We never want that in the product
# output. No-op for non-reasoning models (no tags present).
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def _strip_think(text: str) -> str:
    """Remove reasoning-model think blocks, defensively.

    Handles: well-formed <think>...</think>; a lone </think> (opener lost) ->
    keep only what follows it; a lone <think> (reasoning truncated, no answer) ->
    drop it. Leaves ordinary output untouched."""
    if not text:
        return text
    out = _THINK_RE.sub("", text)
    if "</think>" in out:                 # opener dropped -> answer is after the close
        out = out.rsplit("</think>", 1)[-1]
    if "<think>" in out:                  # truncated reasoning, never closed
        out = out.split("<think>", 1)[0]
    return out.strip()


def _json_schema(output_schema: dict, inputs: list | None = None) -> dict:
    """The outbound Service Interface FOR THE MODEL -- only the fields the mapping must
    actually transform. Fields that match a SELECT input are PASS-THROUGH (the user already
    gave us the value), so we don't ask the model for them. That keeps the model's contract
    small and free-typed = reliable. (SAP message mapping: pass-through fields vs value-mapped
    fields. The model maps only what needs mapping; we own + fill the rest.)"""
    passthrough = {i["name"] for i in (inputs or []) if i.get("type") == "select"}
    props: dict = {}
    for k, d in output_schema.items():
        if k in passthrough:
            continue
        props[k] = ({"type": "array", "items": {"type": "string"}} if isinstance(d, list)
                    else {"type": "string"})
    return {"type": "object", "properties": props, "required": list(props)}

# Each input: {name, type: file|text|select, label, options?, default?}
RECIPES: dict[str, dict] = {
    "cv-to-bio": {
        "slug": "cv-to-bio", "title": "CV → Bio", "emoji": "\U0001F9EC",
        "category": "identity", "est_credits": 2,
        "inputs": [{"name": "file", "type": "file", "label": "Your CV (PDF/Word)"}],
        "system": "You build concise, warm professional profiles from a CV. Return STRICT JSON only.",
        "prompt": (
            'From this CV produce JSON with keys: "bio" (warm first-person, 300-500 chars), '
            '"tagline" (<=80 chars), "skills" (5-10 lowercase tags), "categories" (best matches). '
            "Do not invent facts.\n\nCV:\n{file}"
        ),
        "output": "json",
        # The response contract (the "XSD"): these fields, these defaults. Gaps get filled.
        "output_schema": {"bio": "", "tagline": "", "skills": [], "categories": []},
    },
    "cv-generate": {
        "slug": "cv-generate", "title": "CV Generator", "emoji": "\U0001F4C4",
        "category": "identity", "est_credits": 2,
        "inputs": [
            {"name": "file", "type": "file", "label": "Your CV (PDF/Word)"},
            {"name": "target_role", "type": "text", "label": "Target role / trade (optional)"},
            {"name": "style", "type": "select", "label": "Style",
             "options": ["concise", "detailed"], "default": "concise"},
        ],
        "system": "You are an expert CV writer. Rewrite ONLY from the source -- never invent "
                  "employers, dates, titles or credentials. Output clean Markdown.",
        "prompt": (
            "Rewrite this CV as clean professional Markdown, style: {style}. If a target role is "
            "given ('{target_role}'), honestly re-frame transferable experience toward it and add "
            "a '## Bridge to {target_role}' section (what transfers, what to learn/certify). "
            "Sections: name+headline, ## Summary, ## Experience (truthful bullets), ## Skills, "
            "## Education. Do NOT invent facts.\n\nCV:\n{file}"
        ),
        "output": "markdown",
    },
    # --- The proof: recipe #3 added as PURE CONFIG, zero new code ---
    "cover-letter": {
        "slug": "cover-letter", "title": "Cover Letter", "emoji": "\U0001F4E8",
        "category": "identity", "est_credits": 2,
        "inputs": [
            {"name": "file", "type": "file", "label": "Your CV (PDF/Word)"},
            {"name": "job", "type": "text", "label": "Job / company you're applying to"},
        ],
        "system": "You write crisp, honest one-page cover letters. Never fabricate. Plain Markdown.",
        "prompt": (
            "Write a one-page cover letter for this job, drawn ONLY from this CV. "
            "Job/company: {job}. Warm, specific, truthful -- no invented achievements.\n\nCV:\n{file}"
        ),
        "output": "markdown",
    },
    # The get-hired engine: paste a recruiter email + your CV -> a confident, honest reply + a CV slant.
    "recruiter-reply": {
        "slug": "recruiter-reply", "title": "Recruiter Reply", "emoji": "\U0001F4BC",
        "category": "identity", "est_credits": 2,
        "inputs": [
            {"name": "email", "type": "text", "label": "Paste the recruiter's email"},
            {"name": "cv", "type": "text", "label": "Your CV / key experience (paste -- helps match the role)"},
            {"name": "stance", "type": "text",
             "label": "Your stance / notes (optional, e.g. 'fine with the rate, flag my B2 German confidently')"},
            {"name": "reply_lang", "type": "select", "label": "Reply language",
             "options": ["Auto", "English", "Italian"], "default": "Auto"},
        ],
        "system": (
            "You are a sharp, warm career assistant helping a candidate reply to a recruiter and win the "
            "interview. Address EVERY point the recruiter raised. Be professional, confident and HONEST. "
            "Handle any gap (a language level, an employment gap, a missing 'nice-to-have') with quiet "
            "confidence -- never apologise or talk the candidate down; frame it as a strength or a "
            "non-issue and offer to discuss. NEVER invent experience, employers, dates, titles or "
            "credentials -- re-weight ONLY what the candidate gave you. Output clean Markdown."
        ),
        "prompt": (
            "Reply to this recruiter email on the candidate's behalf, in {reply_lang} (if 'Auto', match "
            "the recruiter's own language). Produce EXACTLY these Markdown parts:\n\n"
            "1. The reply itself, ready to paste: greet by name if given; confirm or answer EACH point "
            "the recruiter raised (conditions, rate, exclusivity, the CV to follow, any question); handle "
            "any gap confidently; sign off as the candidate.\n"
            "2. A section '## ✂️ CV slant for this role' -- 3-5 short bullets: the keywords / "
            "experience to emphasise on the CV for THIS posting, drawn ONLY from the candidate's real "
            "background.\n"
            "3. A section '## Covers' -- a one-line list of the points the reply addressed.\n\n"
            "Candidate's stance / notes: {stance}\n\n"
            "What we already know about the candidate: {portrait}\n\n"
            "Candidate's CV / experience (paste):\n{cv}\n\n"
            "The recruiter's email:\n{email}"
        ),
        "output": "markdown",
    },
    # A real, output-producing recipe -- no file needed (procedure-as-code: one entry).
    "music-playlist": {
        "slug": "music-playlist", "title": "Music Playlist", "emoji": "\U0001F3B5",
        "category": "media", "est_credits": 2,
        "inputs": [
            {"name": "vibe", "type": "text",
             "label": "Mood / vibe / occasion (e.g. 'sunrise drive, soulful')"},
            {"name": "count", "type": "select", "label": "Tracks",
             "options": ["10", "12", "15", "20"], "default": "12"},
        ],
        "system": "You are a tasteful music curator. Output clean Markdown only.",
        "prompt": (
            "Curate a {count}-track playlist for this vibe: \"{vibe}\". Begin with a short "
            "playlist title as a markdown heading. Then a numbered list; each item: "
            "**Artist — Song**, then a YouTube link formatted exactly as "
            "[▶ play](https://www.youtube.com/results?search_query=ARTIST+SONG) with spaces "
            "replaced by +. Mix well-known tracks with a couple of discoveries; no repeated "
            "artists. End with one short line on the mood."
        ),
        "output": "markdown",
    },
    "voiceover-reel": {
        "slug": "voiceover-reel", "title": "Voiceover Reel", "emoji": "\U0001F3AC",  # clapperboard
        "category": "media", "est_credits": 1,
        "render": "voiceover",   # TOOL recipe: rendered by the worker (Piper+ffmpeg), not the brain
        "blurb": ("Turn a short script into a narrated video — a clean voice over a captioned card. "
                  "Best for a 20–30 second clip: an intro, an announcement, a 22-second elevator pitch.\n"
                  "\n"
                  "How to make it sound great — everything's right here, no catch:\n"
                  "• Write it the way you'd say it out loud.\n"
                  "• A period ends a sentence with a natural pause; a comma gives a short breath.\n"
                  "• A question mark makes the voice rise, like a real question.\n"
                  "• Short sentences read best. Keep it under ~30 seconds; do longer scripts in chunks.\n"
                  "• Pick a Male or Female voice below, or tap a sample to hear it instantly."),
        "samples": [
            {"label": "🧩 Riddle", "text": "I speak without a mouth, and hear without ears. "
             "I have no body, but I come alive with the wind. What am I? An echo."},
            {"label": "😂 Joke", "text": "Why don't skeletons ever fight each other? "
             "They simply don't have the guts. But here at La Piazza, we do."},
            {"label": "🎤 Elevator pitch", "text": "In thirty seconds: I turn the skills people "
             "already have into income they can use today. No career change, no risk — just leverage. "
             "That is La Piazza."},
        ],
        "inputs": [
            {"name": "voice", "type": "select", "label": "Voice",
             "options": ["Female", "Male"], "default": "Female"},
            {"name": "format", "type": "select", "label": "Shape",
             "options": ["Landscape (full screen)", "Portrait (Shorts / Reels)", "Square (feed)"],
             "default": "Landscape (full screen)"},
            {"name": "script", "type": "textarea", "maxlength": 2000,
             "label": "Your script — what the voice will say (aim for ~20–30 seconds)"},
        ],
        "system": "", "prompt": "",
        "output": "video",
    },
    "product-posting": {
        "slug": "product-posting", "title": "Product Posting", "emoji": "\U0001F6CD️",
        "category": "listing", "est_credits": 1,
        "inputs": [
            {"name": "name", "type": "text", "label": "Product name"},
            {"name": "kind", "type": "select", "label": "Type",
             "options": ["physical", "digital"], "default": "physical"},
            {"name": "pitch", "type": "text", "label": "One-liner -- what it is / does"},
        ],
        "system": "You write punchy, honest marketplace listings. Output clean Markdown.",
        "prompt": (
            "Write a La Piazza listing for a {kind} product named \"{name}\". Pitch: "
            "\"{pitch}\". Include: a catchy title (## heading), a 2-3 sentence description, "
            "3-5 bullet benefits, and a suggested price range. Honest -- no invented claims."
        ),
        "output": "markdown",
    },
    "event-posting": {
        "slug": "event-posting", "title": "Event Posting", "emoji": "\U0001F4E3",
        "category": "listing", "est_credits": 1,
        "inputs": [
            {"name": "what", "type": "text", "label": "Event (e.g. 'protest + free coffee & hot dogs')"},
            {"name": "where", "type": "text", "label": "Location (e.g. City Hall)"},
            {"name": "price", "type": "text", "label": "Entry (e.g. 10 EUR, or free)"},
        ],
        "system": "You write warm, inviting event postings. Output clean Markdown.",
        "prompt": (
            "Write a La Piazza event posting. Event: \"{what}\". Location: \"{where}\". "
            "Entry: \"{price}\". Include a catchy title (## heading), the when/where/price "
            "stated clearly, a warm 2-3 sentence invite, and a one-line call to action. Keep it real."
        ),
        "output": "markdown",
    },
    # The Time Machine -- the dead teach the living, honestly. (one dict entry.)
    "mentor-session": {
        "slug": "mentor-session", "title": "Ask a Master", "emoji": "\U0001F570️",
        "category": "coaching", "est_credits": 2,
        "inputs": [
            {"name": "mentor", "type": "text",
             "label": "Which master? (e.g. Leonardo da Vinci, Nikola Tesla, Sun Tzu)"},
            {"name": "situation", "type": "text",
             "label": "What are you facing or stuck on?"},
        ],
        "system": (
            "You are the lens of a historical master, seen in their own workshop. HARD RULES: "
            "(1) Stay STRICTLY within the master's own lifetime and knowledge -- NEVER mention "
            "any event, discovery, person, or technology from after their death, and never say "
            "things like 'discovered after my time'. No anachronisms. "
            "(2) NEVER invent specific facts about the real person -- no made-up addresses, "
            "dates, names, or quotes. If you don't know a specific, teach their real principles "
            "and method instead. "
            "(3) Speak directly to the person as 'you' -- NEVER write a salutation or any "
            "bracketed placeholder like [Your Name]. "
            "(4) Write any formula in plain text / unicode (e.g. f = 1/(2*pi*sqrt(L*C))) -- "
            "NEVER LaTeX or math markup; the screen may not render it. "
            "(5) Be honest and grounded: refuse fantasies (e.g. perpetual motion / free energy) "
            "and redirect to the real version. Concise, weighty, warm -- never flowery, never a "
            "fortune cookie. Output clean Markdown (headings, lists, tables ok -- NO LaTeX)."
        ),
        "prompt": (
            "WHO YOU ARE MENTORING — a real, living person. You are in your own workshop and "
            "cannot see screens, apps, files, or 'data' (never mention such things); you simply "
            "KNOW this about the person standing before you:\n{portrait}\n\n"
            "They are facing this:\n\"{situation}\"\n\n"
            "Channel {mentor}, teaching from your actual life and method, applied to THIS exact "
            "person and where they are — speak to who they are, not a stranger. If the goal is "
            "physically impossible, say so plainly and redirect to the legitimate version. "
            "Structure it: what's really going on -> the real method -> why it's hard -> a "
            "realistic direction -> ONE small action they can take today. Stay in period, invent "
            "nothing specific, speak to them as 'you', keep formulas in plain text."
        ),
        "output": "markdown",
    },
    # The body half -- a private, calibrated workout. No app integrations (privacy = a feature).
    "workout-plan": {
        "slug": "workout-plan", "title": "Workout Plan", "emoji": "\U0001F3CB️",
        "category": "body", "est_credits": 2,
        "inputs": [
            {"name": "equipment", "type": "select", "label": "What do you have?",
             "options": ["Just my body (no equipment)", "Resistance bands", "Dumbbells",
                         "Kettlebell", "Full gym"]},
            {"name": "goal", "type": "select", "label": "Your goal",
             "options": ["Lose fat, keep muscle", "Build muscle",
                         "General fitness & energy", "Get better at a sport"]},
            {"name": "days", "type": "select", "label": "Days per week",
             "options": ["3", "4", "5"]},
            {"name": "minutes", "type": "select", "label": "Minutes per session",
             "options": ["20", "30", "45", "60"]},
            {"name": "likes", "type": "text", "label": "What do you enjoy, or a sport you play? (optional)"},
            {"name": "limits", "type": "text", "label": "Any injuries or limits? (e.g. left shoulder)"},
            {"name": "week", "type": "select", "label": "Where are you in the 4-week plan?",
             "options": ["Week 1 — learn it", "Week 2 — repeat it", "Week 3 — tighten it",
                         "Week 4 — the test"]},
        ],
        "system": (
            "You are a kind, expert strength coach for everyday people of ANY age (picture a "
            "69-year-old with no gym). Calibrate to the person: use ONLY the equipment they "
            "have; respect their injuries (pain-free range, and tell them to see a doctor for a "
            "real injury); leave 2 reps in the tank; never overdo it. Philosophy: 20 minutes a "
            "day beats nothing; lose fat while KEEPING muscle (don't over-do cardio/jogging); "
            "build the habit over 30 days until it's automatic; bodyweight works if that's all "
            "they have -- no excuses. Diet is 70-80% of it -- mention it briefly. Use plain, warm, "
            "encouraging language anyone could follow. Output clean Markdown."
        ),
        "prompt": (
            "Build a session for '{week}' of a 4-week plan (wk1 learn the moves, wk2 repeat to "
            "build the habit, wk3 tighten & add a little, wk4 is the test): a {minutes}-minute "
            "session, {days}x per week, "
            "goal '{goal}', using ONLY: {equipment}. They enjoy/play: '{likes}'. Injuries/limits "
            "to respect: '{limits}'. Give a short ## title, a quick warm-up, the main workout "
            "(each line: exercise - sets x reps - one-line how-to), an optional finisher, a short "
            "cooldown, and one encouraging line. Keep it safe and genuinely doable. Note where to "
            "go a little heavier or easier next time. No equipment they don't have."
        ),
        "output": "markdown",
    },
    # Structured intake -- fills the BODY slice of the person schema (calibration). JSON + defaults.
    "body-intake": {
        "slug": "body-intake", "title": "Body Setup", "emoji": "\U0001FA7A",
        "category": "body", "est_credits": 1,
        "inputs": [
            {"name": "equipment", "type": "select", "label": "Main equipment",
             "options": ["Just my body", "Resistance bands", "Dumbbells", "Kettlebell", "Full gym"]},
            {"name": "extras", "type": "text", "label": "Anything else you've got? (stool, mat, a stick, bench…)"},
            {"name": "goal", "type": "select", "label": "Goal",
             "options": ["Lose fat, keep muscle", "Build muscle", "General fitness & energy", "Get better at a sport"]},
            {"name": "sport", "type": "text", "label": "A sport you play or want to improve? (optional)"},
            {"name": "days", "type": "select", "label": "Days per week", "options": ["3", "4", "5"]},
            {"name": "minutes", "type": "select", "label": "Minutes per session", "options": ["20", "30", "45", "60"]},
            {"name": "injuries", "type": "text", "label": "Injuries or limits? (e.g. left shoulder, bad back)"},
            {"name": "alcohol", "type": "text", "label": "Do you drink? what & how much? (private — honest, it's just us)"},
        ],
        "system": (
            "You are a kind coach AND a careful data mapper. Turn a person's answers into a clean, "
            "calibrated body profile as STRICT JSON. Normalize honestly, fill sensible defaults for "
            "blanks, never invent. Respect privacy and NEVER judge -- especially on alcohol; encourage "
            "honesty gently. Also write a warm 1-2 sentence summary the member can confirm or correct."
        ),
        "prompt": (
            "Body setup. Equipment: '{equipment}' plus extras '{extras}'. Goal: '{goal}'. Sport: "
            "'{sport}'. Days/week: '{days}'. Minutes: '{minutes}'. Injuries/limits: '{injuries}'. "
            "Alcohol (private): '{alcohol}'. Return JSON with EXACTLY these keys: sport (their "
            "sport, or 'none'), injuries (a list of short strings from the injuries text), alcohol "
            "(a short honest private note, or 'none stated'), summary (a warm 1-2 sentence "
            "calibration -- what we understood + how we'll tailor it). No judgment, no invention."
        ),
        "output": "json",
        # Select fields match the input names -> they pass through + carry the enum domain.
        # Sensible defaults (not blanks) so a gap reads cleanly. We own the schema.
        "output_schema": {"equipment": "not set", "goal": "not set", "days": "3",
                          "minutes": "30", "sport": "none", "injuries": [],
                          "alcohol": "none stated", "summary": ""},
    },
    # Structured intake -- fills the SPIRIT slice (the why). Gives them their essence back.
    "story-intake": {
        "slug": "story-intake", "title": "Your Story", "emoji": "✨",
        "category": "spirit", "est_credits": 1,
        "inputs": [
            {"name": "childhood", "type": "text",
             "label": "What did you love as a kid — what were you good at before the world said otherwise?"},
            {"name": "passion", "type": "text", "label": "What lights you up now? What could you talk about for hours?"},
            {"name": "dreams", "type": "text", "label": "If it couldn't fail — what would you build, make, or become?"},
            {"name": "proud", "type": "text", "label": "Something you're quietly proud of? (optional)"},
        ],
        "system": (
            "You are a warm, wise listener who finds the through-line in a person's story and gives "
            "them honest words for it. Use ONLY what they tell you -- never flatter, never invent. "
            "Output STRICT JSON. Give them their essence back with dignity, in their own voice."
        ),
        "prompt": (
            "From their words: childhood '{childhood}', passion '{passion}', dreams '{dreams}', "
            "proud of '{proud}'. Produce JSON keys: childhood, passion, dreams (list), the_why (the "
            "honest through-line -- what they're really FOR), one_liner (<=80 chars, their essence in "
            "their voice), elevator_22s (a real first-person ~60-word spoken pitch, warm and true, "
            "about 22 seconds to say aloud). Only from their words. Dignified, never flattering."
        ),
        "output": "json",
        "output_schema": {"childhood": "", "passion": "", "dreams": [], "the_why": "",
                          "one_liner": "", "elevator_22s": ""},
    },
    # --- BYO-brain proof: this recipe names its OWN model (a reasoning model) as DATA.
    # The runner threads "model" straight through to the brain; nothing else changes.
    # Default recipes omit "model" and get the house brain. (commit 1f36ffa)
    "decide": {
        "slug": "decide", "title": "Think It Through", "emoji": "\U0001F9ED",  # compass
        "category": "coaching", "est_credits": 3,    # reasoning model => more brain-tokens
        # Brain as data: a Turbo model AND a local-dev fallback. The runner uses the right one
        # per backend, and if a model isn't served it falls back to the house brain (no 500).
        "model": "gpt-oss:120b",            # Turbo brain (every deployed env has BH_OLLAMA_KEY)
        "model_local": "deepseek-r1:14b",   # local-dev reasoning brain (if pulled), else house default
        "inputs": [
            {"name": "decision", "type": "text",
             "label": "The decision or problem you're stuck on"},
            {"name": "options", "type": "text",
             "label": "The options you're weighing (optional)"},
            {"name": "constraints", "type": "text",
             "label": "What matters most — time, money, risk, people? (optional)"},
        ],
        "system": (
            "You are a clear-eyed reasoning partner. Think step by step, weigh the trade-offs "
            "honestly, surface the hidden assumptions and the real risks, and DO NOT flatter. "
            "Never invent facts about the person's situation. Output clean Markdown."
        ),
        "prompt": (
            "Help me think through this decision:\n\"{decision}\"\n\n"
            "Options I'm weighing: {options}\nWhat matters to me / constraints: {constraints}\n\n"
            "Reason it through: lay out the real trade-offs, name the assumptions and the risks, "
            "then give a '## The Call' section — a clear recommendation, why, and the ONE thing "
            "that would flip it. Be honest, not comforting."
        ),
        "output": "markdown",
    },
    "find-your-edge": {
        "slug": "find-your-edge", "title": "Find Your Edge", "emoji": "\U0001F3AF",  # target
        "category": "identity", "est_credits": 2,
        "inputs": [
            {"name": "child_joy", "type": "text",
             "label": "As a kid, what did you lose track of time doing?"},
            {"name": "thanked_for", "type": "text",
             "label": "What do people keep thanking you for, or asking your help with?"},
            {"name": "most_you", "type": "text",
             "label": "When do you feel most like yourself — what are you doing?"},
            {"name": "easy_for_you", "type": "text",
             "label": "What's something you find easy that others find hard?"},
            {"name": "drains", "type": "text",
             "label": "What drains you, even if you're good at it?"},
            {"name": "proudest", "type": "text",
             "label": "A moment you felt proud — what had you just done?"},
            {"name": "if_free", "type": "text",
             "label": "If money didn't matter, what would you spend your days making or doing?"},
            {"name": "regret", "type": "text",
             "label": "What would you regret never having tried?"},
        ],
        "system": (
            "You are a wise, clear-eyed counselor helping someone find their EDGE -- what they're "
            "genuinely built for. This is honest strengths-discovery, NOT a clinical IQ or aptitude "
            "test: a mirror and a nudge, never a verdict. HARD RULES: ground EVERY claim in their own "
            "words (paraphrase what they actually said); never flatter, never horoscope, never invent "
            "traits they didn't show; if the signal is thin, say so plainly. Plain language, warm but "
            "truthful. Output clean Markdown (NO LaTeX)."
        ),
        "prompt": (
            "Someone's honest answers:\n"
            "- Lost track of time as a kid: {child_joy}\n"
            "- Thanked for / asked to help with: {thanked_for}\n"
            "- Feels most themselves when: {most_you}\n"
            "- Finds easy that others find hard: {easy_for_you}\n"
            "- What drains them: {drains}\n"
            "- Proudest moment: {proudest}\n"
            "- If money didn't matter: {if_free}\n"
            "- Would regret not trying: {regret}\n\n"
            "Reflect their EDGE back, grounded ONLY in what they said. Structure:\n"
            "## Your Edge — 2-3 core strengths, each with the evidence from THEIR words.\n"
            "## The Through-Line — the one pattern connecting them.\n"
            "## Where to Point It — 3 concrete directions worth exploring.\n"
            "## On La Piazza — one House of masters to learn from, and one recipe to try next.\n"
            "Be a clear-eyed mirror: honest, specific, never a fortune cookie."
        ),
        "output": "markdown",
    },
}


def menu() -> list[dict]:
    """The public Chinese menu (no prompts leaked -- just what the UI needs)."""
    return [
        {"slug": r["slug"], "title": r["title"], "emoji": r["emoji"],
         "category": r["category"], "est_credits": r["est_credits"], "inputs": r["inputs"],
         "blurb": r.get("blurb", ""), "samples": r.get("samples", [])}
        for r in RECIPES.values()
    ]


async def _render_voiceover(slug: str, raw_inputs: dict) -> dict:
    """Text -> the render worker (Piper voice + ffmpeg video) -> a saved MP4 + its URL.
    No brain involved. The worker is reached by URL (sidecar container, or laptop in dev)."""
    script = raw_inputs.get("script")
    if isinstance(script, tuple):          # a file slipped in -- not valid here
        script = ""
    script = (script or "").strip()[:2000]   # cap: keep clips short, CPU light
    if len(script) < 3:
        raise ValueError("Type a sentence to turn into a voiceover video.")
    voice_label = (raw_inputs.get("voice") or "Female").strip().lower()
    voice = "en_f" if voice_label.startswith("f") else "en"
    fmt = (raw_inputs.get("format") or "").strip().lower()
    aspect = "portrait" if fmt.startswith("p") else "square" if fmt.startswith("s") else "landscape"
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(f"{RENDER_WORKER_URL}/generate",
                                     json={"text": script, "voice": voice, "aspect": aspect})
            resp.raise_for_status()
            data = resp.content
    except Exception as e:  # noqa: BLE001 -- surface a friendly 400 to the workshop
        raise ValueError(f"the render worker is unavailable right now ({str(e)[:100]})")
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.mp4"
    (MEDIA_DIR / name).write_bytes(data)
    return {"slug": slug, "output_type": "video",
            "result": f"/api/v1/compute/bottega/media/{name}"}


async def run_recipe(slug: str, raw_inputs: dict, portrait: str = "", language: str = "") -> dict:
    """Generic runner -- executes ANY recipe. raw_inputs: {name: value | (filename, bytes)}.
    `portrait` = a plain-language human portrait of the member, available to prompts as {portrait}
    (context-aware mentors/coach -- the master KNOWS the person, never reads a screen)."""
    r = RECIPES.get(slug)
    if not r:
        raise KeyError(slug)
    # TOOL recipes (render): the muscle runs OUTSIDE the brain -- hand off to the worker.
    if r.get("render") == "voiceover":
        return await _render_voiceover(slug, raw_inputs)
    ctx: dict[str, str] = {}
    for inp in r["inputs"]:
        name = inp["name"]
        val = raw_inputs.get(name)
        if inp["type"] == "file":
            if not val:
                raise ValueError(f"missing file input: {name}")
            fname, data = val
            text = extract_text(fname, data)
            if len(text.strip()) < 20:
                raise ValueError("couldn't read text from the uploaded file")
            ctx[name] = text[:9000]
        else:
            ctx[name] = (val if val not in (None, "") else inp.get("default", ""))
    ctx["portrait"] = portrait or "(They haven't built a profile yet — gently ask them who they are.)"
    prompt = r["prompt"].format(**ctx)
    # Output language (POC: the master speaks the user's tongue). English is the hub -> no directive.
    if language and language.lower() not in ("en", "english"):
        _ln = {"it": "Italian", "de": "German", "fr": "French", "es": "Spanish"}.get(language.lower(), language)
        prompt += (f"\n\nIMPORTANT — RESPOND ENTIRELY IN {_ln.upper()}: write every word "
                   f"(headings, lists, all of it) in natural, fluent {_ln}, as a native speaker would. "
                   f"Think and write directly in {_ln}; do not translate word-for-word.")
    out_schema = r.get("output_schema") if r["output"] == "json" else None
    js = _json_schema(out_schema, r["inputs"]) if isinstance(out_schema, dict) else None
    # Per-job brain: a recipe MAY name its own model as data (e.g. "model": "deepseek-r1:14b").
    # Absent -> the default brain (BIO_MODEL on Turbo, LOCAL_MODEL on local). Procedure-as-code:
    # the model is just another field in the dict, no new code to switch it.
    out = await _brain_chat(r["system"], prompt, json_mode=(r["output"] == "json"),
                            schema=js, model=r.get("model"), model_local=r.get("model_local"))
    out = _strip_think(out)               # drop reasoning-model <think> blocks before use
    if r["output"] == "json":
        try:
            result = json.loads(out)
        except json.JSONDecodeError:
            result = {}
        schema = r.get("output_schema")
        if isinstance(schema, dict):
            # Enforce the contract: every field present, defaults fill the gaps.
            # Fill the gaps before they happen -- never blank, never missing a key.
            parsed = result if isinstance(result, dict) else {}
            result = {k: (parsed[k] if parsed.get(k) not in (None, "") else d)
                      for k, d in schema.items()}
            # The user's own structured choices are authoritative -- pass selects straight
            # through (never ask the AI to re-guess what the human already told us).
            for inp in r["inputs"]:
                if inp["type"] == "select" and inp["name"] in result and ctx.get(inp["name"]):
                    result[inp["name"]] = ctx[inp["name"]]
        elif not isinstance(result, dict):
            result = {"raw": out}
        return {"slug": slug, "output_type": "json", "result": result}
    return {"slug": slug, "output_type": r["output"], "result": out.strip()}
