#!/usr/bin/env python3
"""Banco B2 offsite push — ship an encrypted backup blob to Backblaze B2 (immutable).

Runs ON THE BOX, right after banco_backup.sh makes an encrypted .sql.gz.gpg. Uploads
the blob to B2 over the native B2 API (stdlib urllib — no rclone, no b2 CLI, no pip),
using a WRITE-ONLY, bucket-scoped key. The bucket has Object-Lock default retention
(banco_b2_setup.py), so each upload is immutable for the lock window: a compromised
box can APPEND recovery points but can NOT read, list, overwrite, or delete them.
That is the ransomware-proof property — and it's exactly why a B2 write-only key is
safe to keep on a public web box (unlike a whole-Drive OAuth token, which is why the
Google-Drive copy is pulled by the laptop instead — see banco_offsite_pull.py).

The blobs are already GPG/AES256 ciphertext (banco_backup.sh), so B2 only ever holds
opaque bytes; recovery needs the passphrase from /root/.banco-backup-key, which Angel
also keeps in KeePass. Ciphertext offsite + passphrase in KeePass = a real DR pair.

Idempotency without list rights: a write-only key can't ask "is this already there?",
so we keep a local ledger (BACKUP_DIR/.b2-synced) of uploaded names and skip repeats.
That's why re-running is cheap and the nightly cron won't re-ship the whole pile.

    python3 banco_b2_push.py /opt/backups/banco/banco_prod_20260705_0300.sql.gz.gpg
    python3 banco_b2_push.py            # scan BACKUP_DIR, upload any un-synced blobs

Exit 0 on success OR clean skip (B2 not configured) so the nightly job stays green
when offsite isn't wired yet; non-zero only on a real upload failure (for alerting).

Python-first (CLAUDE.md #11), stdlib only.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# B2 migrated newer/restricted keys to v4-only (v2/v3 → HTTP 400). v4 also nests the
# storage apiUrl + the key's bucketId under apiInfo.storageApi instead of at the top level.
AUTH_URL = "https://api.backblazeb2.com/b2api/v4/b2_authorize_account"
DEFAULT_BACKUP_DIR = Path("/opt/backups/banco")
PATTERN = "banco_prod_*.sql.gz.gpg"
LEDGER_NAME = ".b2-synced"


def load_env(env_file: Path | None) -> dict:
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


def _authorize(kid: str, app_key: str) -> dict:
    basic = base64.b64encode(f"{kid}:{app_key}".encode()).decode()
    req = urllib.request.Request(AUTH_URL, headers={"Authorization": f"Basic {basic}"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read())


def _post(url: str, token: str, data: dict) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(data).encode(),
        headers={"Authorization": token, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read())


def _get_upload_url(api_url: str, token: str, bucket_id: str) -> dict:
    return _post(f"{api_url}/b2api/v4/b2_get_upload_url", token, {"bucketId": bucket_id})


def _upload(up: dict, remote_name: str, blob: bytes, sha1: str) -> None:
    req = urllib.request.Request(
        up["uploadUrl"], data=blob, method="POST",
        headers={
            "Authorization": up["authorizationToken"],
            "X-Bz-File-Name": urllib.parse.quote(remote_name),
            "Content-Type": "application/octet-stream",
            "Content-Length": str(len(blob)),
            "X-Bz-Content-Sha1": sha1,
        })
    with urllib.request.urlopen(req, timeout=120) as r:
        r.read()  # drain; a non-2xx raises HTTPError


def main() -> int:
    ap = argparse.ArgumentParser(description="Push Banco encrypted backup(s) to Backblaze B2 (immutable).")
    ap.add_argument("blob", nargs="?", type=Path, help="specific .sql.gz.gpg to push (default: scan for un-synced)")
    ap.add_argument("--env-file", type=Path, default=Path("/root/.banco-b2.env"),
                    help="KEY=VALUE file with B2_* creds (default /root/.banco-b2.env)")
    ap.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    args = ap.parse_args()

    env = load_env(args.env_file)
    kid, app_key, bucket = env.get("B2_KEY_ID", "").strip(), env.get("B2_APP_KEY", "").strip(), env.get("B2_BUCKET", "").strip()
    prefix = env.get("B2_PREFIX", "banco/").strip()
    if not (kid and app_key and bucket):
        print("[b2] not configured (B2_KEY_ID/B2_APP_KEY/B2_BUCKET) — skipped, LOCAL+Drive only")
        return 0  # clean skip keeps the nightly job green

    backup_dir: Path = args.backup_dir
    ledger = backup_dir / LEDGER_NAME
    synced = set(ledger.read_text().split()) if ledger.exists() else set()

    if args.blob:
        blobs = [args.blob]
    else:
        blobs = sorted(p for p in backup_dir.glob(PATTERN) if p.name not in synced)
    todo = [p for p in blobs if p.name not in synced]
    if not todo:
        print("[b2] nothing new to push (all local blobs already offsite)")
        return 0

    # authorize once; the write-only bucket-scoped key hands us the bucketId directly
    try:
        a = _authorize(kid, app_key)
    except urllib.error.HTTPError as e:
        print("[b2] ERROR authorize failed —", e.read().decode()[:200]); return 1
    _storage = (a.get("apiInfo") or {}).get("storageApi") or {}   # v4 nests it here
    api_url = _storage.get("apiUrl") or a.get("apiUrl")           # v4, else legacy v2
    token = a["authorizationToken"]
    # a bucket-scoped key hands us its bucketId via `allowed` (v4: under storageApi; v2: top-level).
    # An explicit B2_BUCKET_ID in the env wins (covers a write-only key not scoped to one bucket).
    _allowed = _storage.get("allowed") or a.get("allowed") or {}
    bucket_id = env.get("B2_BUCKET_ID", "").strip() or _allowed.get("bucketId")
    if not bucket_id:
        try:
            lb = _post(f"{api_url}/b2api/v4/b2_list_buckets", token,
                       {"accountId": a["accountId"], "bucketName": bucket})
            bucket_id = lb["buckets"][0]["bucketId"]
        except Exception:
            print(f"[b2] ERROR: key is not scoped to a bucket and can't list — scope the key to '{bucket}'"); return 1

    up = _get_upload_url(api_url, token, bucket_id)
    pushed = 0
    for blob in todo:
        if not blob.exists():
            print(f"[b2] skip missing {blob}"); continue
        data = blob.read_bytes()
        sha1 = hashlib.sha1(data).hexdigest()
        remote = f"{prefix}{blob.name}"
        for attempt in (1, 2):  # one retry on an expired upload URL / transient 5xx
            try:
                _upload(up, remote, data, sha1)
                break
            except urllib.error.HTTPError as e:
                if attempt == 1 and e.code in (401, 408, 429, 500, 503):
                    up = _get_upload_url(api_url, token, bucket_id)  # fresh URL + token
                    continue
                print(f"[b2] ERROR upload {blob.name} —", e.read().decode()[:200]); return 1
            except urllib.error.URLError as e:
                if attempt == 1:
                    up = _get_upload_url(api_url, token, bucket_id); continue
                print(f"[b2] ERROR upload {blob.name} — {e}"); return 1
        synced.add(blob.name)
        pushed += 1
        print(f"[b2] ✅ {remote}  ({len(data):,} bytes, sha1 {sha1[:12]}…) — immutable offsite")

    # append-only ledger update (write-only key can't list, so we track locally)
    ledger.write_text("\n".join(sorted(synced)) + "\n")
    print(f"[b2] DONE: {pushed} blob(s) shipped to B2 '{bucket}' (immutable); ledger {len(synced)} total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
