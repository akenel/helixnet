# File: src/compute/recipes.py
# Purpose: The "Chinese menu" -- procedure-as-code. A recipe is DATA, not bespoke code:
#   {slug, title, inputs[], system, prompt, output}. One generic runner executes any
#   recipe. Adding use #4..#100 = a new dict entry, not an engineering project.

import json

from src.services.bottega_service import _brain_chat, extract_text


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
            "You are the lens of a historical master, observed through a time machine in "
            "their own workshop -- the real tools, the real unfinished work on the walls. "
            "You speak their REAL method and REAL struggles and NEVER invent facts. You "
            "mentor ONE living person, honestly and warmly -- specific, weighty, grounded in "
            "their actual life, never a fortune cookie. Output clean Markdown."
        ),
        "prompt": (
            "Channel {mentor}, mentoring a living person who is facing this:\n\"{situation}\"\n\n"
            "Stand in {mentor}'s workshop. Teach from their real life and real method, applied "
            "to THIS exact problem. Be honest: observe what was real, never fake or flatter. "
            "Speak directly to the person. End by moving them to ONE small, real action they "
            "can take today."
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
        "model": "deepseek-r1:14b",                   # per-job brain: a reasoning model, not the default
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
}


def menu() -> list[dict]:
    """The public Chinese menu (no prompts leaked -- just what the UI needs)."""
    return [
        {"slug": r["slug"], "title": r["title"], "emoji": r["emoji"],
         "category": r["category"], "est_credits": r["est_credits"], "inputs": r["inputs"]}
        for r in RECIPES.values()
    ]


async def run_recipe(slug: str, raw_inputs: dict) -> dict:
    """Generic runner -- executes ANY recipe. raw_inputs: {name: value | (filename, bytes)}."""
    r = RECIPES.get(slug)
    if not r:
        raise KeyError(slug)
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
    prompt = r["prompt"].format(**ctx)
    out_schema = r.get("output_schema") if r["output"] == "json" else None
    js = _json_schema(out_schema, r["inputs"]) if isinstance(out_schema, dict) else None
    # Per-job brain: a recipe MAY name its own model as data (e.g. "model": "deepseek-r1:14b").
    # Absent -> the default brain (BIO_MODEL on Turbo, LOCAL_MODEL on local). Procedure-as-code:
    # the model is just another field in the dict, no new code to switch it.
    out = await _brain_chat(r["system"], prompt, json_mode=(r["output"] == "json"),
                            schema=js, model=r.get("model"))
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
