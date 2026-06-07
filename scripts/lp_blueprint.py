#!/usr/bin/env python3
"""Phase 0/1 -- the Survey & the Blueprint. The first DOer of the Legend Journey.

The AI runs a person's comeback like a master architect runs a cutover: survey the
site (CV + target), draw a 30-day plan of one real task a day, each task with three
attempts before we pivot. Measure twice, cut once. No fake events -- every task is a
real action the person actually does.

  python scripts/lp_blueprint.py --cv path/to/cv.pdf --target "Land a SAP contract"

CLAUDE.md rule 11: Python-first, httpx + Typer.
"""
import json
import os

import httpx
import typer

app = typer.Typer(add_completion=False)
KEY = os.getenv("LPCX_BRAIN_KEY") or os.getenv("BH_OLLAMA_KEY", "")
URL = os.getenv("LPCX_BRAIN_URL", "https://ollama.com").rstrip("/")
MODEL = os.getenv("LPCX_BRAIN_MODEL", "gpt-oss:120b")

SYSTEM = (
    "You are a master project architect AND a wise, kind mentor who runs a person's "
    "comeback like a cutover plan: measure twice, cut once. You read the WHOLE person, "
    "not just the resume -- their age, energy, what weighs on them, what they avoid and "
    "why, how they feel about themselves. You are honest and caring, never invent fake "
    "events or people. Output STRICT JSON only."
)

# The Human Check -- Phase 0's honest soil test. These answers are the baseline KPIs
# we come back to and re-measure: the real progress is human, not just tasks-done.
HUMAN_CHECK = [
    "age_and_shape: your age, physical condition, and honest daily energy",
    "whats_bothering: what's been weighing on you / keeping you up",
    "what_slows_me: what actually stops or slows you down",
    "procrastination: when you put things off, what are you avoiding -- and why",
    "how_i_feel: how you feel about yourself right now, honestly",
    "time_per_day: how much real time you can give this, each day",
    "the_one_thing: the one thing you'd revive or fix if you could",
]


def extract(path: str) -> str:
    if path.lower().endswith(".pdf"):
        import fitz  # PyMuPDF
        doc = fitz.open(path)
        return "\n".join(p.get_text() for p in doc).strip()
    return open(path, encoding="utf-8", errors="ignore").read().strip()


def blueprint(cv: str, target: str, days: int) -> dict:
    user = (
        f"TARGET (the go-live): {target}\n\n"
        f"From the CV below, produce a JSON cutover plan with EXACTLY these keys:\n"
        f'  "survey": {{"gifts":[3-6 real strengths], "gaps":[2-4 honest gaps to close], '
        f'"assets":[2-5 things they already have to use: skills, network, items]}},\n'
        f'  "north_star": one honest sentence naming the go-live,\n'
        f'  "plan": array of EXACTLY {days} objects, one per day: '
        f'{{"day":int, "task":"ONE concrete real-world action doable in a day", '
        f'"why":"one line", "proof":"how we verify it is truly done"}},\n'
        f'  "pivot_rule": one sentence on what to do after 3 failed attempts at a task.\n\n'
        f"RULES: tasks are REAL actions the person does in the world (send this email, "
        f"call this person, print this, post this, build this) -- never a fake event or "
        f"a fake person. Small daily cuts that build on each other toward the go-live. "
        f"Be specific to THIS person.\n\nCV:\n{cv[:8000]}"
    )
    r = httpx.post(f"{URL}/api/chat", timeout=240.0,
                   headers={"Authorization": f"Bearer {KEY}"},
                   json={"model": MODEL, "stream": False, "format": "json",
                         "messages": [{"role": "system", "content": SYSTEM},
                                      {"role": "user", "content": user}]})
    r.raise_for_status()
    return json.loads(r.json()["message"]["content"])


@app.command()
def main(cv: str = typer.Option(..., help="path to CV (pdf/txt)"),
         target: str = typer.Option(..., help="the go-live goal"),
         days: int = typer.Option(30)):
    if not KEY:
        raise typer.Exit("no brain key (BH_OLLAMA_KEY)")
    bp = blueprint(extract(cv), target, days)
    print(json.dumps(bp, indent=2))


if __name__ == "__main__":
    app()
