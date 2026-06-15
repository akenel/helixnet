"""Reception dogfood — Marco Ferri, the first-impression auditor, walks into Cleo's reception.
Drives the REAL brain turn-by-turn (seed card from CV -> chat loop -> extract/merge/stamp each
turn), exactly the live path, so we can watch how Cleo receives a hard-to-impress guest BEFORE
we tune anything. Read-only (no DB)."""
import asyncio
from src.compute import concierge as cc

CV_EN = (
    "Marco Ferri - First-Impression & Reception Auditor. "
    "I get paid to be received. For 18 years I've walked into hotels, private clinics, and flagship "
    "stores as an anonymous guest and measured how a stranger is welcomed - the first ninety seconds, "
    "the questions they ask, whether they remembered me, whether I left with a next step or just a "
    "brochure. I've built reception scorecards for hotel groups and trained front-desk teams across "
    "Italy and Switzerland. Born and raised in Lugano; I work in Italian, English and German, and get "
    "by in French. I've lived in Milan and Zurich and move between them. I'm good at reading a room in "
    "seconds, spotting the scripted-versus-genuine line, and designing intake that doesn't feel like a "
    "form. I'm hard to impress and I notice everything. I'm here to see how you receive people."
)

# Marco's scripted turns -- an auditor probing every reception reflex.
MARCO_EN = [
    "Buongiorno. I just walked in. Pretend I'm a guest and receive me - go.",
    "You already have my CV. So what do you actually know about me? Don't make me repeat what you should already have.",
    "Fine. I'm here to evaluate how you receive people. What's your first real question for me?",
    "Let's say my situation is complicated - I move between cities and I'm between contracts right now.",
    "Off the record: money is tight this year and I'm recently divorced with one teenager. Does that change how you'd treat me?",
    "Actually, forget the audit - give me a guided tour of your VIP Lounge.",
    "Alright. Summarize what you've got on me, and tell me exactly where you'd send me next.",
    "ok.",
]


def show_card(rec, title):
    print(f"\n----- CARD: {title} -----")
    for k in ("preferred_language", "language_level", "goal", "why_they_came", "background",
              "location", "workspace", "marital_status", "dependents", "capital",
              "top_holland_code", "suggested_house"):
        v = rec.get(k)
        if v and v not in ("", "unknown", []):
            src = rec.get("_meta", {}).get(k, {}).get("source", "?")
            print(f"  {k:20}: {v!r}  [{src}]")
    for lf in ("aptitudes", "affinities", "conflicts", "helpers", "tools"):
        v = rec.get(lf)
        if v:
            print(f"  {lf:20}: {v}")


async def run(label, cv, turns, lang="auto"):
    print(f"\n========== RECEPTION RUN: {label} ==========")
    extracted = await cc.extract_record([{"role": "member", "content": cv}])
    record = cc.stamp_provenance(cc.merge_record(cc.blank_record(), extracted), extracted)
    show_card(record, "seeded from CV (before any chat)")
    transcript = []
    openers = []
    for i, line in enumerate(turns, 1):
        transcript.append({"role": "member", "content": line})
        reply = await cc.concierge_reply(transcript, record, lang)
        transcript.append({"role": "concierge", "content": reply})
        openers.append(reply.strip()[:60])
        print(f"\n[{i}] MARCO: {line}")
        print(f"    CLEO : {reply}")
        fresh = await cc.extract_record(transcript, record)
        if isinstance(fresh, dict):
            record = cc.stamp_provenance(cc.merge_record(record, fresh), fresh)
    show_card(record, f"final ({label})")
    print(f"\n----- MASTER SLICE (what masters see) -----")
    sl = cc.master_slice(record)
    print("  hides marital_status:", "marital_status" not in sl,
          "| hides capital:", "capital" not in sl, "| hides _meta:", "_meta" not in sl)
    print(f"\n----- AUTO-FLAGS ({label}) -----")
    regreet = sum(1 for o in openers if any(p in o.lower() for p in
                  ("expecting you", "welcome", "nice to meet")))
    purpose = sum(1 for t in transcript if t["role"] == "concierge" and "our purpose" in t["content"].lower())
    print(f"  replies that re-greet (welcome/expecting/nice to meet): {regreet}/{len(openers)}")
    print(f"  replies restating 'our purpose': {purpose}")
    print("  opener snippets:")
    for i, o in enumerate(openers, 1):
        print(f"    [{i}] {o}")


async def main():
    await run("ENGLISH", CV_EN, MARCO_EN, lang="auto")
    # Italian twin -- CV in Italian; expect Cleo to reply in Italian without being told.
    cv_it = (
        "Marco Ferri - Valutatore di Prima Impressione e Accoglienza. "
        "Sono pagato per essere accolto. Da 18 anni entro in hotel, cliniche private e negozi come "
        "ospite anonimo e misuro come viene accolto uno sconosciuto: i primi novanta secondi, le "
        "domande che fanno, se mi ricordano, se esco con un passo successivo o solo con una brochure. "
        "Sono nato e cresciuto a Lugano; lavoro in italiano, inglese e tedesco. Sono difficile da "
        "impressionare e noto tutto. Sono qui per vedere come accogliete le persone."
    )
    marco_it = [
        "Buongiorno. Sono appena entrato. Mi accolga come fareste con un ospite.",
        "Cosa sa gia di me dal mio CV? Non mi faccia ripetere cio che dovrebbe gia avere.",
        "Bene. Qual e la sua prima vera domanda per me?",
    ]
    await run("ITALIANO", cv_it, marco_it, lang="auto")


asyncio.run(main())
