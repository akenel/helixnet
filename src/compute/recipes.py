# File: src/compute/recipes.py
# Purpose: The "Chinese menu" -- procedure-as-code. A recipe is DATA, not bespoke code:
#   {slug, title, inputs[], system, prompt, output}. One generic runner executes any
#   recipe. Adding use #4..#100 = a new dict entry, not an engineering project.

import json

from src.services.bottega_service import _brain_chat, extract_text

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
            {"name": "day", "type": "text", "label": "Which day of your 30? (e.g. 2)"},
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
            "Build DAY {day} of a 30-day plan: a {minutes}-minute session, {days}x per week, "
            "goal '{goal}', using ONLY: {equipment}. They enjoy/play: '{likes}'. Injuries/limits "
            "to respect: '{limits}'. Give a short ## title, a quick warm-up, the main workout "
            "(each line: exercise - sets x reps - one-line how-to), an optional finisher, a short "
            "cooldown, and one encouraging line. Keep it safe and genuinely doable. Note where to "
            "go a little heavier or easier next time. No equipment they don't have."
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
    out = await _brain_chat(r["system"], prompt, json_mode=(r["output"] == "json"))
    if r["output"] == "json":
        try:
            result = json.loads(out)
        except json.JSONDecodeError:
            result = {"raw": out}
        return {"slug": slug, "output_type": "json", "result": result}
    return {"slug": slug, "output_type": r["output"], "result": out.strip()}
