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
