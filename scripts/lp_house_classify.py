#!/usr/bin/env python3
"""AI House-refinement -- the cast-mind sorts itself.

Reads personas (JSON array of {name, bio} on stdin), asks the brain to place each
into its TRUE House (the seed skill-categories were too coarse -- 'art' lumped
painters+actors+writers). Prints {name: house_slug} JSON. Read-only: it proposes,
it does not write. The caller turns the proposal into UPDATEs after eyeballing it.

  ssh box 'psql ... json_agg(...)' | python scripts/lp_house_classify.py

CLAUDE.md rule 11: Python-first, httpx.
"""
import json
import os
import sys

import httpx

KEY = os.getenv("LPCX_BRAIN_KEY") or os.getenv("BH_OLLAMA_KEY", "")
URL = os.getenv("LPCX_BRAIN_URL", "https://ollama.com").rstrip("/")
MODEL = os.getenv("LPCX_BRAIN_MODEL", "gpt-oss:120b")

HOUSES = {
    "house-the-hearth": "everyday hands-on masters: cooking, baking, repair, building, woodworking, healing, farming, sewing",
    "house-the-lab": "science, invention, mathematics, engineering, technology, computing",
    "house-the-studio": "visual artists: painters, sculptors, photographers, designers",
    "house-the-stage": "performers: actors, dancers, filmmakers, directors, comedians",
    "house-the-song": "music: composers, musicians, singers",
    "house-the-word": "writers, poets, playwrights, philosophers, thinkers",
    "house-the-arena": "warriors, generals, strategists, athletes, leaders, explorers, activists, rulers",
}


def classify(people: list[dict]) -> dict:
    house_list = "\n".join(f"- {k}: {v}" for k, v in HOUSES.items())
    roster = "\n".join(f'{i+1}. {p["name"]} :: {(p.get("bio") or "")[:200]}'
                       for i, p in enumerate(people))
    system = ("You are a curator placing famous people into Houses by their PRIMARY "
              "life's work. Return STRICT JSON only: an object mapping each exact name "
              "to exactly one house slug from the list. No prose.")
    user = (f"Houses:\n{house_list}\n\nPlace each person into the single best House by "
            f"who they truly are (a writer goes to the-word even if tagged 'art'):\n{roster}")
    r = httpx.post(f"{URL}/api/chat", timeout=180.0,
                   headers={"Authorization": f"Bearer {KEY}"},
                   json={"model": MODEL, "stream": False, "format": "json",
                         "messages": [{"role": "system", "content": system},
                                      {"role": "user", "content": user}]})
    r.raise_for_status()
    return json.loads(r.json()["message"]["content"])


def main():
    people = json.load(sys.stdin)
    if not KEY:
        print("no brain key (LPCX_BRAIN_KEY / BH_OLLAMA_KEY)", file=sys.stderr)
        sys.exit(1)
    result = {}
    batch = 30
    for i in range(0, len(people), batch):
        chunk = people[i:i + batch]
        try:
            result.update(classify(chunk))
            print(f"  classified {min(i+batch,len(people))}/{len(people)}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"  batch @{i} failed: {e}", file=sys.stderr)
    print(json.dumps(result, indent=0))


if __name__ == "__main__":
    main()
