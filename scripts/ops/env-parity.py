#!/usr/bin/env python3
"""env-parity — one-glance "are we in the same picture?" check across the box trees.

Angel's recurring question is really "same SHA, anything dirty, any leftover overlays?"
Byte-count is the wrong proxy (DBs/pyc/.bak skew it); the exact invariant is
**git SHA + clean working tree + no .bak overlays**. This prints exactly that, per tree,
read-only (no checkout, no deploy, no mutation — safe to run while a deploy terminal is live).

Usage:
    python3 scripts/ops/env-parity.py                 # ssh to the box, check Banco trio + friends
    python3 scripts/ops/env-parity.py --host 1.2.3.4  # different box
    python3 scripts/ops/env-parity.py --local         # also show this machine's main vs origin/main

The Banco trio (sandbox -> staging -> prod) is what go-live cares about; bottega + legacy
are shown dimmed for context. A clean baseline = the trio on the SAME sha, all CLEAN, 0 .bak.
"""
from __future__ import annotations

import argparse
import subprocess
import sys

# (label, path, role)  — role drives the grouping/verdict. Order = display order.
TREES = [
    ("sandbox",        "/opt/helix-sandbox-tree",        "banco"),
    ("banco-staging",  "/opt/helix-banco-staging-tree",  "banco"),
    ("banco-prod",     "/opt/helix-banco-tree",          "banco"),
    ("bottega-staging","/opt/helix-staging-tree",        "other"),
    ("bottega-prod",   "/opt/helixnet",                  "other"),
]

# One remote shell that emits a parseable block per tree. Read-only git/find only.
_REMOTE = r'''
for spec in {specs}; do
  label="${{spec%%:*}}"; d="${{spec#*:}}"
  sha=$(git -C "$d" rev-parse --short HEAD 2>/dev/null || echo "?")
  br=$(git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")
  mod=$(git -C "$d" status --porcelain --untracked-files=no 2>/dev/null | wc -l | tr -d " ")
  new=$(git -C "$d" ls-files --others --exclude-standard 2>/dev/null | grep -vc "\.bak$")
  baks=$(find "$d/src" -name "*.bak" 2>/dev/null | wc -l | tr -d " ")
  echo "PARITY|$label|$br|$sha|$mod|$new|$baks"
done
'''


def run_remote(host: str) -> list[dict]:
    specs = " ".join(f"{label}:{path}" for label, path, _ in TREES)
    cmd = ["ssh", "-o", "ConnectTimeout=15", "-o", "StrictHostKeyChecking=accept-new",
           f"root@{host}", _REMOTE.format(specs=specs)]
    try:
        out = subprocess.check_output(cmd, text=True, timeout=60, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(f"ssh failed:\n{e.output}", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("ssh timed out (box unreachable?)", file=sys.stderr)
        sys.exit(1)
    rows = {}
    for line in out.splitlines():
        if not line.startswith("PARITY|"):
            continue
        _, label, br, sha, mod, new, baks = line.split("|")
        rows[label] = {"branch": br, "sha": sha, "mod": int(mod), "new": int(new),
                       "baks": int(baks)}
    # preserve TREES order
    role = {label: r for label, _, r in TREES}
    return [{"label": l, "role": role[l], **rows[l]} for l, _, _ in TREES if l in rows]


def local_main() -> tuple[str, str]:
    def sh(args):
        return subprocess.check_output(["git", *args], text=True).strip()
    try:
        head = sh(["rev-parse", "--short", "main"])
        origin = sh(["rev-parse", "--short", "origin/main"])
        return head, origin
    except Exception:  # noqa: BLE001
        return "?", "?"


def main() -> int:
    ap = argparse.ArgumentParser(description="Read-only SHA/dirty/.bak parity across box trees.")
    ap.add_argument("--host", default="46.62.138.218", help="box IP (default: helixnet-uat)")
    ap.add_argument("--local", action="store_true", help="also show local main vs origin/main")
    args = ap.parse_args()

    rows = run_remote(args.host)

    print(f"\n  ENV PARITY  —  root@{args.host}  (read-only)\n")
    print(f"  {'':<3}{'tree':<16}{'branch':<8}{'sha':<10}{'mod':>5}{'new':>5}{'.bak':>6}  state")
    print("  " + "-" * 64)
    banco_shas = set()
    issues = []
    for r in rows:
        # 'mod' = tracked drift, '.bak' = leftover overlays → the real signal.
        # 'new' = untracked scratch (e.g. sandbox TEST sheets) → noted, not a failure.
        clean = r["mod"] == 0 and r["baks"] == 0
        flag = "CLEAN" if clean else "DRIFT"
        if clean and r["new"]:
            flag = "CLEAN*"          # clean tracked, has untracked scratch
        mark = "OK " if clean else "** "
        dim = "" if r["role"] == "banco" else "  (context)"
        print(f"  {mark:<3}{r['label']:<16}{r['branch']:<8}{r['sha']:<10}"
              f"{r['mod']:>5}{r['new']:>5}{r['baks']:>6}  {flag}{dim}")
        if r["role"] == "banco":
            banco_shas.add(r["sha"])
            if not clean:
                issues.append(f"{r['label']}: {r['mod']} tracked-modified + {r['baks']} .bak")

    print("  " + "-" * 66)
    if args.local:
        h, o = local_main()
        synced = "in sync" if h == o else f"AHEAD/behind (local {h} vs origin {o})"
        print(f"  local main: {h}   origin/main: {o}   -> {synced}")

    # Verdict on the Banco trio.
    if len(banco_shas) == 1 and not issues:
        print(f"\n  VERDICT: Banco trio is in the SAME picture — all on {next(iter(banco_shas))}, clean. ✅\n")
    else:
        print("\n  VERDICT: Banco trio NOT uniform yet:")
        if len(banco_shas) > 1:
            print(f"    - SHAs differ across trio: {sorted(banco_shas)}")
        for i in issues:
            print(f"    - {i}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
