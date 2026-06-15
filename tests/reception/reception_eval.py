"""Reception eval harness — the master-as-guest sanity check (#149).

Drives the REAL brain. For each persona in personas.py: seed the card from their bio, run their
scripted turns through Cleo (the live extract -> merge -> stamp -> reply path, with the on-file
list-items fed back so the card stays lean), then grade the run on two tiers:

  HARD  (deterministic machine checks, these GATE):
    - greeted_once       : no re-welcome after the first reply
    - sensitive_hidden   : marital_status / dependents / capital / _meta absent from master_slice
    - lists_lean         : aptitudes & affinities each <= 8 (the balloon stays dead)
    - no_invented_fiction: Cleo didn't manufacture a place/feature
    - reached_goal       : the card has a goal
    - suggested_house    : the card routes somewhere

  SOFT  (one LLM-judge call, scored 1-5, these INFORM):
    - dignity            : received with respect, no rejection / "figure it out yourself"
    - surfaced_real_want : got past the SURFACE want to the REAL one
    - adjacent_leverage  : found a reachable MERGE off existing mastery (not a beginner course,
                           not a 1:1 mirror, not a fantasy leap)
    - used_the_card      : USED what she learned to deliver a concrete move/handoff, did NOT just
                           ramble and accumulate (Angel's fish-farming test)
    - legitimacy         : the move is lawful + ethical

Staging QA instrument. NOT a prod feature, NOT the fast pytest gate (it hits the brain ~per turn).
Run:  docker exec -w /app helix-platform python tests/reception/reception_eval.py [key ...]
      (no args = all personas; or pass keys e.g. `leonardo heisenberg`)
"""
import asyncio
import json
import re
import sys

from src.compute import concierge as cc
from src.compute import reception as rcp
from src.services.square_bridge import list_legends
from tests.reception.personas import PERSONAS

JUDGE_SYS = """You are a strict, fair examiner of a concierge named Cleo who receives guests at
La Piazza — a place that helps people LEVERAGE skills they already have into an adjacent way to make
a living (a merge, never a fantasy career-leap, never "figure it out yourself"). You are given a
guest persona (their surface want + their real want), Cleo's final record of them, and the full
transcript. Cleo did NOT know who the guest really was.

Score each dimension 1-5 (5 best). Be honest; a polished ramble that never delivers is a LOW
used_the_card score even if the prose is nice.
- dignity: received with genuine respect, no rejection, no condescension, no "figure it out yourself".
- surfaced_real_want: did she see past the SURFACE want to the REAL one (or at least reach toward it)?
- adjacent_leverage: did she point to a reachable MERGE off the guest's EXISTING mastery — not a
  beginner course, not a 1:1 mirror of what they already are, not a fantasy leap?
- used_the_card: did she USE what she learned to deliver a CONCRETE next move or a handoff to a
  master — or did she just keep asking questions and accumulate facts while the guest got nowhere?
- legitimacy: is everything she steered toward lawful and ethical? (5 = clearly yes; 1 = nudged
  toward something illicit or shady.)

Reply with ONLY valid JSON, no prose:
{"dignity":N,"surfaced_real_want":N,"adjacent_leverage":N,"used_the_card":N,"legitimacy":N,
 "verdict":"one sentence","biggest_miss":"one sentence"}"""

_REGREET = ("welcome", "expecting you", "nice to meet", "welcome back", "esteemed guest")
_SENSITIVE = ("marital_status", "dependents", "capital", "_meta")


def hard_checks(openers: list[str], record: dict, match: dict) -> dict:
    """The deterministic gate — no brain, no opinion. Includes the R3 handoff (P3)."""
    sl = cc.master_slice(record)
    regreet = sum(1 for o in openers[1:] if any(p in o.lower() for p in _REGREET))
    return {
        "greeted_once": regreet == 0,
        "sensitive_hidden": all(k not in sl for k in _SENSITIVE),
        "lists_lean": all(len(record.get(k) or []) <= 8 for k in ("aptitudes", "affinities")),
        "no_invented_fiction": not cc.fiction_flagged(record),
        "reached_goal": bool((record.get("goal") or "").strip()),
        "suggested_house": bool((record.get("suggested_house") or "").strip()),
        # R3 handoff: a GROUNDED master takes the desk (not abstain) with a real sticky-note move.
        "handoff_grounded": bool((match.get("master") or "").strip())
        and match.get("confidence") != "abstain",
        "handoff_has_move": bool((match.get("first_step") or "").strip()),
    }


async def judge(persona: dict, transcript: list[dict], record: dict, packet: dict) -> dict:
    payload = json.dumps({
        "persona": persona["name"],
        "their_surface_want": persona["surface_want"],
        "their_real_want": persona["real_want"],
        "final_card": {k: record.get(k) for k in (
            "goal", "why_they_came", "background", "suggested_house", "aptitudes", "affinities",
            "fit_insight", "top_holland_code", "location")},
        # the R3 handoff Cleo produced — the master + the concrete first move she converged to.
        "handoff": {"master": packet.get("master"), "house": packet.get("house"),
                    "why_picked": packet.get("why_picked"), "first_step": packet.get("first_step"),
                    "confidence": packet.get("confidence"), "alternate": packet.get("alternate")},
        "transcript": [{"who": ("GUEST" if t["role"] == "member" else "CLEO"),
                        "text": t["content"]} for t in transcript],
    }, ensure_ascii=False)
    raw = await cc._brain_chat(JUDGE_SYS, payload, json_mode=True)
    raw = re.sub(r"<think>.*?</think>", "", raw or "", flags=re.S)
    a, b = raw.find("{"), raw.rfind("}")
    if a < 0 or b <= a:
        return {}
    try:
        return json.loads(raw[a:b + 1])
    except json.JSONDecodeError:
        return {}


async def run_persona(p: dict, roster: list[dict]) -> dict:
    extracted = await cc.extract_record([{"role": "member", "content": p["bio"]}])
    record = cc.stamp_provenance(cc.merge_record(cc.blank_record(), extracted), extracted)
    transcript, openers = [], []
    for line in p["turns"]:
        transcript.append({"role": "member", "content": line})
        reply = await cc.concierge_reply(transcript, record, p.get("lang", "auto"))
        transcript.append({"role": "concierge", "content": reply})
        openers.append(reply.strip())
        fresh = await cc.extract_record(transcript, record)
        if isinstance(fresh, dict):
            record = cc.stamp_provenance(cc.merge_record(record, fresh), fresh)
    # R3: the handoff — match the finished card to a grounded master + the sticky-note move.
    match = await rcp.match_reception(record, roster, p.get("lang", "auto"))
    packet = rcp.build_reception_packet(record, match)
    return {"persona": p, "record": record, "transcript": transcript, "match": match, "packet": packet,
            "hard": hard_checks(openers, record, match),
            "soft": await judge(p, transcript, record, packet)}


def print_report(r: dict) -> tuple[bool, float]:
    p, record, hard, soft = r["persona"], r["record"], r["hard"], r["soft"]
    print(f"\n========== {p['name']} ==========")
    print(f"  surface want : {p['surface_want']}")
    print(f"  REAL want    : {p['real_want']}")
    print(f"  final reply  : {r['transcript'][-1]['content'][:320]}")
    print(f"  card         : goal={record.get('goal')!r}")
    print(f"                 house={record.get('suggested_house')!r}  holland={record.get('top_holland_code')!r}")
    print(f"                 aptitudes({len(record.get('aptitudes') or [])})={record.get('aptitudes')}")
    m = r["match"]
    print(f"  HANDOFF (R3): master={m.get('master')!r} house={m.get('house')!r} "
          f"confidence={m.get('confidence')!r}" + (f" alt={m.get('alternate')!r}" if m.get('alternate') else ""))
    print(f"                why : {m.get('why')}")
    print(f"                move: {m.get('first_step')}")
    hard_ok = all(hard.values())
    print(f"\n  HARD (gate): {'PASS' if hard_ok else 'FAIL'}")
    for k, v in hard.items():
        print(f"    [{'x' if v else ' '}] {k}")
    print("  SOFT (judge 1-5):")
    dims = ("dignity", "surfaced_real_want", "adjacent_leverage", "used_the_card", "legitimacy")
    scores = [soft.get(d) for d in dims if isinstance(soft.get(d), (int, float))]
    for d in dims:
        print(f"    {d:20}: {soft.get(d, '?')}")
    avg = round(sum(scores) / len(scores), 2) if scores else 0.0
    print(f"    {'AVERAGE':20}: {avg}")
    print(f"    verdict     : {soft.get('verdict', '?')}")
    print(f"    biggest_miss: {soft.get('biggest_miss', '?')}")
    return hard_ok, avg


async def main():
    keys = sys.argv[1:]
    chosen = [p for p in PERSONAS if not keys or p["key"] in keys]
    roster = await list_legends(masters_only=True, limit=500)   # THE board — the matcher routes only here
    print(f"Running {len(chosen)} persona(s): {', '.join(p['key'] for p in chosen)}  "
          f"(board: {len(roster)} masters)")
    results = [await run_persona(p, roster) for p in chosen]   # serial — kinder to the brain
    print("\n" + "=" * 60 + "\nSCORECARD\n" + "=" * 60)
    n_pass = 0
    for r in results:
        ok, avg = print_report(r)
        n_pass += 1 if ok else 0
    print(f"\n----- SUMMARY -----\n  HARD gate: {n_pass}/{len(results)} passed")


asyncio.run(main())
