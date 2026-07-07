#!/usr/bin/env python3
"""Artemis delta-watch — scheduled, ZERO-WRITE change detector for the Artemis webshop.

Runs the importer in DRY-RUN (never --commit, never touches a DB), then diffs the fresh
snapshot against the previous one to report exactly what changed on the shop since last run:
new products, price/category/class changes, and removed items — with names, not just counts.

This is the safe half of the supplier-sync vision: it tells a human WHEN to re-import; the
actual commit stays one-click + backup-gated (a scheduled auto-commit would drop unreviewed,
rules-classified items straight onto the live till). Writes a status file + a dated report so
it slots into the same pull-status pattern as the daily smoke (push-alerting = separate P6).

Cron (box, weekly — Monday 06:30):
    30 6 * * 1  python3 /opt/helix-sandbox-tree/scripts/ops/artemis_delta_watch.py \
                  >> /opt/ops/artemis-watch/watch.log 2>&1

Env: ARTEMIS_WATCH_DIR (default /opt/ops/artemis-watch) · WATCH_DELAY (default 0.25).
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TREE = Path(__file__).resolve().parents[2]              # repo root (has scripts/ + src/)
IMPORTER = TREE / "scripts" / "import" / "artemis_import.py"
WATCH_DIR = Path(os.environ.get("ARTEMIS_WATCH_DIR", "/opt/ops/artemis-watch"))
SNAPSHOT = WATCH_DIR / "snapshot.json"
PREV = WATCH_DIR / "snapshot.prev.json"
LATEST = WATCH_DIR / "latest.txt"
DELAY = os.environ.get("WATCH_DELAY", "0.25")
_EXAMPLES = 15                                           # cap the per-bucket name lists


def _load(p: Path) -> dict:
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def main() -> None:
    WATCH_DIR.mkdir(parents=True, exist_ok=True)
    first_run = not SNAPSHOT.exists()
    if SNAPSHOT.exists():                                # keep the old baseline to diff against
        PREV.write_text(SNAPSHOT.read_text())

    cmd = [sys.executable, str(IMPORTER), "--snapshot", str(SNAPSHOT),
           "--write-snapshot", "--sample", "0", "--delay", DELAY]
    proc = subprocess.run(cmd, cwd=str(TREE), capture_output=True, text=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    new = _load(SNAPSHOT)
    if not new:
        msg = f"[{ts}] Artemis delta-watch: FAILED (importer exit {proc.returncode}) — see report"
        LATEST.write_text(msg + "\n\n" + (proc.stdout + proc.stderr)[-3000:])
        print(msg)
        sys.exit(1)

    if first_run:
        summary = f"[{ts}] Artemis delta-watch: BASELINE established — {len(new)} products now tracked."
        LATEST.write_text(summary + "\n")
        print(summary)
        return

    old = _load(PREV)
    old_k, new_k = set(old), set(new)
    added = sorted(new_k - old_k)
    removed = sorted(old_k - new_k)
    changed = []                                         # (sku, [fields], name)
    for sku in (new_k & old_k):
        if old[sku].get("hash") != new[sku].get("hash"):
            fields = [f for f in ("name", "price", "category", "product_class", "is_age_restricted", "image_url")
                      if str(old[sku].get(f)) != str(new[sku].get(f))]
            changed.append((sku, fields, new[sku].get("name", sku)))

    n_add, n_chg, n_rem = len(added), len(changed), len(removed)
    quiet = (n_add + n_chg + n_rem) == 0
    head = ("✅ no change" if quiet
            else f"⚠ {n_add} new · {n_chg} changed · {n_rem} gone")
    summary = f"[{ts}] Artemis delta-watch: {head}  (total {len(new)})"

    lines = [summary, ""]
    if added:
        lines.append(f"NEW ({n_add}):")
        lines += [f"  + {new[s].get('name','?')}  [{s}]  {new[s].get('price','')} CHF" for s in added[:_EXAMPLES]]
        if n_add > _EXAMPLES:
            lines.append(f"  … +{n_add - _EXAMPLES} more")
    if changed:
        lines.append(f"CHANGED ({n_chg}):")
        lines += [f"  ~ {name}  [{sku}]  ({', '.join(fields)})" for sku, fields, name in changed[:_EXAMPLES]]
        if n_chg > _EXAMPLES:
            lines.append(f"  … +{n_chg - _EXAMPLES} more")
    if removed:
        lines.append(f"GONE ({n_rem}):")
        lines += [f"  - {old[s].get('name','?')}  [{s}]" for s in removed[:_EXAMPLES]]
        if n_rem > _EXAMPLES:
            lines.append(f"  … +{n_rem - _EXAMPLES} more")
    if not quiet:
        lines += ["", "→ Review, then re-import when ready (gated): "
                  "artemis_import.py --commit (sandbox → review → prod, backup-gated)."]

    report = "\n".join(lines) + "\n"
    LATEST.write_text(report)
    (WATCH_DIR / f"report-{datetime.now(timezone.utc):%Y%m%d}.txt").write_text(report)
    print(summary)


if __name__ == "__main__":
    main()
