#!/usr/bin/env python3
"""Banco B2 offsite — turn ON Object-Lock retention + lifecycle for the backup bucket.

This is the ONE-TIME setup that makes Backblaze B2 a ransomware-proof offsite copy.
It makes every uploaded backup **immutable** for B2_LOCK_DAYS (Object-Lock: can't be
overwritten or deleted during the window — so a box compromise, ransomware, or a
fat-fingered delete cannot erase your recovery point), and adds a lifecycle rule that
auto-deletes objects B2_KEEP_DAYS after upload (so the bucket doesn't grow forever;
cleanup happens B2-side, which is WHY the box's upload key never needs delete rights).

Run this ONCE, from the LAPTOP, with a MASTER/admin B2 key (needs writeBuckets). The
box then uploads with a separate WRITE-ONLY key (see banco_b2_push.py + the runbook).
Idempotent — safe to re-run to change the retention/keep windows.

    python3 banco_b2_setup.py --env-file /path/to/banco-b2.env

Prereq (cannot be fixed after the fact): the bucket MUST have been created with
**Object Lock ENABLED** — that is a create-time checkbox in the B2 console and cannot
be turned on later. If retention doesn't apply, the bucket was made without it; make a
new bucket with Object Lock checked. Full steps: docs/BANCO-B2-BACKUP-SETUP.md.

Python-first (CLAUDE.md #11), stdlib only (urllib) — no rclone, no b2 CLI, no pip.
Ported from freehold/ops/b2-immutable.py.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# B2 sunsetting v2 (newer/restricted keys → HTTP 400); v4 nests apiUrl/allowed under apiInfo.storageApi.
AUTH_URL = "https://api.backblazeb2.com/b2api/v4/b2_authorize_account"


def load_env(env_file: Path | None) -> dict:
    """Merge a KEY=VALUE file (if present) under the real environment (env wins)."""
    data: dict[str, str] = {}
    if env_file and env_file.exists():
        for raw in env_file.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            data[k.strip()] = v.strip().strip('"').strip("'")
    data.update({k: v for k, v in os.environ.items() if k.startswith("B2_")})
    return data


def _post(url, token, data):
    req = urllib.request.Request(
        url, data=json.dumps(data).encode(),
        headers={"Authorization": token, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read())


def main() -> int:
    ap = argparse.ArgumentParser(description="Enable B2 Object-Lock + lifecycle on the Banco backup bucket.")
    ap.add_argument("--env-file", type=Path, default=Path("/root/.banco-b2.env"),
                    help="KEY=VALUE file with B2_* creds/settings (default /root/.banco-b2.env)")
    args = ap.parse_args()
    env = load_env(args.env_file)

    kid, app_key = env.get("B2_KEY_ID", "").strip(), env.get("B2_APP_KEY", "").strip()
    bucket = env.get("B2_BUCKET", "").strip()
    lock_days = int(env.get("B2_LOCK_DAYS", "14") or 14)
    keep_days = int(env.get("B2_KEEP_DAYS", "90") or 90)
    # governance = a bypass-capable key can still delete; compliance = NOBODY can delete
    # a locked object until it expires (truly ransomware-proof, but irreversible).
    lock_mode = (env.get("B2_LOCK_MODE", "governance").strip().lower() or "governance")
    if lock_mode not in ("governance", "compliance"):
        print(f"ERROR: B2_LOCK_MODE must be governance or compliance (got '{lock_mode}')"); return 1
    if not (kid and app_key and bucket):
        print("ERROR: B2_KEY_ID / B2_APP_KEY / B2_BUCKET must be set (env or --env-file)"); return 1
    if keep_days <= lock_days:
        print(f"ERROR: B2_KEEP_DAYS ({keep_days}) must exceed B2_LOCK_DAYS ({lock_days})"); return 1

    # 1) authorize (this needs a MASTER key with writeBuckets — not the box's write-only key)
    basic = base64.b64encode(f"{kid}:{app_key}".encode()).decode()
    req = urllib.request.Request(AUTH_URL, headers={"Authorization": f"Basic {basic}"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            a = json.loads(r.read())
    except urllib.error.HTTPError as e:
        print("ERROR: B2 authorize failed —", e.read().decode()[:200]); return 1
    _storage = (a.get("apiInfo") or {}).get("storageApi") or {}   # v4 nests it here
    api_url = _storage.get("apiUrl") or a.get("apiUrl")           # v4, else legacy v2
    account_id = a["accountId"]
    _allowed = _storage.get("allowed") or a.get("allowed") or {}
    bucket_id = _allowed.get("bucketId")
    if not bucket_id:  # key not bucket-scoped — look it up (needs listBuckets)
        try:
            lb = _post(f"{api_url}/b2api/v4/b2_list_buckets", a["authorizationToken"],
                       {"accountId": account_id, "bucketName": bucket})
            bucket_id = lb["buckets"][0]["bucketId"]
        except (urllib.error.HTTPError, IndexError, KeyError):
            print(f"ERROR: could not find bucket '{bucket}' — is the key a master/admin key?"); return 1

    # 2) set default retention + lifecycle in one update
    try:
        res = _post(f"{api_url}/b2api/v4/b2_update_bucket", a["authorizationToken"], {
            "accountId": account_id, "bucketId": bucket_id,
            "defaultRetention": {"mode": lock_mode,
                                 "period": {"duration": lock_days, "unit": "days"}},
            "lifecycleRules": [{"fileNamePrefix": "",
                                "daysFromUploadingToHiding": keep_days,
                                "daysFromHidingToDeleting": 1}],
        })
    except urllib.error.HTTPError as e:
        print("ERROR: b2_update_bucket failed —", e.read().decode()[:300]); return 1

    # Read back the applied retention (nested under fileLockConfiguration).
    dr = (((res.get("fileLockConfiguration") or {}).get("value") or {}).get("defaultRetention") or {})
    mode, period = dr.get("mode"), dr.get("period") or {}
    if mode != lock_mode:
        print(f"⚠️  retention not applied as '{lock_mode}' (got '{mode}') — was the bucket "
              f"created with Object Lock ENABLED? (can't be turned on after creation)"); return 1
    print(f"✅ B2 '{bucket}': backups IMMUTABLE for {period.get('duration')} {period.get('unit')} "
          f"({mode}), auto-deleted ~{keep_days}d after upload (lifecycle).")
    print("   Cleanup is B2-side now — the box uploads with a WRITE-ONLY key (banco_b2_push.py).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
