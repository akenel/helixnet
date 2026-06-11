#!/usr/bin/env python3
"""Cleo v2 — the mechanical UAT gate (Burst B).

Drives the things Angel couldn't easily eyeball himself (§5 dispatcher variety + grounding,
§6 scorecard rises, §7 saved-handoff data stays structured, §8 robustness) straight against
the live API with a real member token. Self-cleaning: every dispatch/save row it creates is
deleted at the end, so it leaves the demo account exactly as it found it.

    python tests/e2e/cleo_v2_checks.py            # local (https://helix.local)
    python tests/e2e/cleo_v2_checks.py local|hetzner

Exit 0 = all green; non-zero = a real regression. Reusable pre-stage gate.
"""
import os
import re
import sys
import json
import subprocess

import httpx

TARGET = sys.argv[1] if len(sys.argv) > 1 else "local"
ENVS = {
    "local":   {"app": "https://helix.local",         "kc": "https://keycloak.helix.local", "pg": "postgres"},
    "hetzner": {"app": "https://bottega.lapiazza.app", "kc": "https://keycloak.helix.local", "pg": "postgres"},
}
E = ENVS.get(TARGET)
if not E:
    print(f"unknown target {TARGET}", file=sys.stderr); sys.exit(2)

REALM = os.environ.get("LP_REALM", "lapiazza-realm-dev")
CLIENT = os.environ.get("LP_CLIENT", "lapiazza_web")
USER = os.environ.get("LP_TEST_USER", "angel")
PASS = os.environ.get("LP_TEST_PASS", "helix_pass")
BASE = E["app"] + "/api/v1/compute/bottega"

results = []   # (name, ok, detail)
created_refs = []     # dispatch ref_ids to clean
created_sessions = []  # saved session ids to clean


def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s or "").lower())


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"  {'✅' if ok else '❌'} {name}" + (f"  — {detail}" if detail else ""))


def main():
    c = httpx.Client(verify=False, timeout=150.0)

    # --- auth ---
    r = c.post(f"{E['kc']}/realms/{REALM}/protocol/openid-connect/token",
               data={"grant_type": "password", "client_id": CLIENT, "username": USER, "password": PASS})
    if r.status_code != 200:
        record("auth: member token", False, f"KC {r.status_code}"); return
    tok = r.json()["access_token"]
    H = {"Authorization": "Bearer " + tok}
    record("auth: member token", True)

    # --- the board (for the grounding check) ---
    lg = c.get(f"{BASE}/legends", headers=H)
    board = {norm(x.get("name")) for x in (lg.json().get("legends") or [])} if lg.status_code == 200 else set()
    record("board: legends list loads", lg.status_code == 200 and len(board) > 0, f"{len(board)} masters")

    def on_board(master_name):
        n = norm(master_name)
        if n in board:
            return True
        # dispatcher matches on last-name containment too; accept a board name that contains/!= shares the surname
        return any(n and (n in b or b in n) for b in board if len(n) >= 4)

    # --- §6 scorecard baseline ---
    d0 = c.get(f"{BASE}/me/dashboard", headers=H)
    sc0 = (d0.json() or {}).get("scorecard") if d0.status_code == 200 else None
    base_handoffs = (sc0 or {}).get("handoffs")
    ok_sc = d0.status_code == 200 and isinstance(sc0, dict) and all(
        k in sc0 for k in ("portrait", "works", "handoffs", "masters_met"))
    record("§6 scorecard: present + 4 numeric fields", ok_sc, json.dumps(sc0) if sc0 else f"HTTP {d0.status_code}")

    # --- §5 variety + grounding: 3 different-topic dispatches ---
    topics = {
        "business": "How do I win customers and grow a small business from nothing?",
        "music":    "How do I learn to compose beautiful, moving music?",
        "health":   "How do I heal my body and build lasting physical strength?",
    }
    topic_masters = {}
    for label, q in topics.items():
        r = c.post(f"{BASE}/concierge/dispatch", headers=H, json={"question": q, "language": "en"})
        if r.status_code != 200:
            record(f"§5 dispatch [{label}]", False, f"HTTP {r.status_code}"); continue
        body = r.json()
        if body.get("ref_id"):
            created_refs.append(body["ref_id"])
        masters = body.get("masters") or []
        names = [m.get("name") for m in masters]
        all_real = all(on_board(n) for n in names) and len(masters) > 0
        topic_masters[label] = {norm(n) for n in names}
        record(f"§5 dispatch [{label}]: {len(masters)} masters, all on board", all_real, " + ".join(names))

    # variety: not the same pair every time
    if len(topic_masters) == 3:
        union = set().union(*topic_masters.values())
        all_identical = all(s == topic_masters["business"] for s in topic_masters.values())
        record("§5 variety: topics get different masters", (not all_identical) and len(union) > 2,
               f"{len(union)} distinct masters across 3 topics")

    # --- §8 robustness ---
    r = c.post(f"{BASE}/concierge/dispatch", headers=H, json={"question": "   "})
    record("§8 empty question → 422", r.status_code == 422, f"HTTP {r.status_code}")

    long_q = ("I have spent thirty years building things and now I want to start over; " * 40).strip()
    r = c.post(f"{BASE}/concierge/dispatch", headers=H, json={"question": long_q, "language": "en"})
    if r.status_code == 200 and r.json().get("ref_id"):
        created_refs.append(r.json()["ref_id"])
    record("§8 very long question → 200, handled", r.status_code == 200, f"HTTP {r.status_code} ({len(long_q)} chars)")

    # --- §6b scorecard rises (handoffs increment by the # of successful dispatches) ---
    d1 = c.get(f"{BASE}/me/dashboard", headers=H)
    sc1 = (d1.json() or {}).get("scorecard") if d1.status_code == 200 else {}
    if isinstance(base_handoffs, int) and isinstance(sc1.get("handoffs"), int):
        delta = sc1["handoffs"] - base_handoffs
        record("§6 scorecard: handoffs rose by # dispatches", delta == len(created_refs),
               f"{base_handoffs} → {sc1['handoffs']} (+{delta}, expected +{len(created_refs)})")
        record("§6 scorecard: masters_met > 0 after dispatch", (sc1.get("masters_met") or 0) > 0,
               f"masters_met={sc1.get('masters_met')}")

    # --- §7 saved handoff keeps STRUCTURED masters (the root cause of the [object Object] bug) ---
    if created_refs:
        r = c.post(f"{BASE}/concierge/dispatch", headers=H, json={"question": "How do I find courage to begin again at sixty?", "language": "en"})
        if r.status_code == 200:
            res = r.json()
            created_refs.append(res["ref_id"])
            save = c.post(f"{BASE}/sessions", headers=H, json={
                "slug": "cleo-v2-e2e-saved", "title": "E2E saved handoff", "inputs": {"q": "courage"},
                "output": json.dumps(res), "output_type": "json", "tags": "e2e"})
            if save.status_code == 200 and save.json().get("id"):
                sid = save.json()["id"]; created_sessions.append(sid)
                back = c.get(f"{BASE}/sessions/{sid}", headers=H)
                ok = False; detail = f"HTTP {back.status_code}"
                if back.status_code == 200:
                    out = back.json().get("output")
                    try:
                        parsed = json.loads(out) if isinstance(out, str) else out
                        ms = parsed.get("masters") or []
                        ok = isinstance(ms, list) and len(ms) > 0 and all(
                            isinstance(m, dict) and m.get("name") and m.get("answer") for m in ms)
                        detail = f"{len(ms)} structured master objects (name+answer), no stringify"
                    except Exception as ex:  # noqa: BLE001
                        detail = f"parse failed: {ex}"
                record("§7 saved handoff: masters stay structured (not [object Object])", ok, detail)
            else:
                record("§7 save handoff", False, f"save HTTP {save.status_code}")

    c.close()


def cleanup():
    """Delete every row this run created, so the demo account is untouched."""
    if not (created_refs or created_sessions):
        return
    conds = []
    for ref in created_refs:
        conds.append(f"slug='dispatch-{ref}'")
    for sid in created_sessions:
        conds.append(f"id='{sid}'")
    sql = "DELETE FROM bottega_sessions WHERE " + " OR ".join(conds) + ";"
    try:
        out = subprocess.run(
            ["docker", "exec", E["pg"], "psql", "-U", "helix_user", "-d", "helix_db", "-c", sql],
            capture_output=True, text=True, timeout=30)
        print(f"\n  🧹 cleanup: {out.stdout.strip() or out.stderr.strip()}")
    except Exception as ex:  # noqa: BLE001
        print(f"\n  ⚠ cleanup failed ({ex}); created refs={created_refs} sessions={created_sessions}")


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    print(f"\n════ CLEO v2 CHECKS — {TARGET} ({E['app']}) ════\n")
    try:
        main()
    finally:
        cleanup()
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n════ {passed}/{total} checks green ════")
    if passed != total:
        print("🔴 Cleo v2 gate FAILED"); sys.exit(1)
    print("🟢 Cleo v2 gate green")
