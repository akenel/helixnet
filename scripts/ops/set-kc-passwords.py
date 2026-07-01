#!/usr/bin/env python3
"""Rotate Keycloak user passwords off the shared demo password — safely.

Sets a NEW password (typed once at a hidden prompt) for a named set of users across
one or more realms, via the KC admin REST API. The password NEVER appears on the
command line, in shell history, or in any log — it's read with getpass and sent only
in the reset-password request body. Refuses 'helix_pass' outright so the shared-demo
flaw can't be re-entered.

Designed to run INSIDE an app container (reaches keycloak:8080, and reads the KC admin
creds already in the container env). Example (from your laptop, interactive TTY):

  ssh -t root@46.62.138.218 \
    'docker exec -it helix-platform-banco python3 /tmp/set-kc-passwords.py \
       --realms borrowhood,borrowhood-staging --users felix,akenel,angel,pam,ralph'

Only your handful of named accounts are touched; unknown users are reported and skipped.
CLAUDE.md rule 11: Python + getpass, stdlib only (no pip needed in the container).
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def _env(*names: str, default: str | None = None) -> str | None:
    for n in names:
        v = os.getenv(n)
        if v:
            return v
    return default


KC = (_env("KC_BASE_URL_INTERNAL", "KEYCLOAK_BASE_URL",
           "KEYCLOAK_HELIX_REALM_INTERNAL_URL", default="http://keycloak:8080") or "").rstrip("/")
ADMIN_USER = _env("KEYCLOAK_ADMIN_USER", default="helix_user")
MASTER = _env("KEYCLOAK_MASTER_REALM", default="master")
BANNED = {"helix_pass", "helix_user", "password", "changeme"}


def _req(method: str, url: str, token: str | None = None, data=None, form=False):
    hdr = {}
    body = None
    if token:
        hdr["Authorization"] = "Bearer " + token
    if data is not None:
        if form:
            body = urllib.parse.urlencode(data).encode()
            hdr["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(data).encode()
            hdr["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, headers=hdr, method=method)
    with urllib.request.urlopen(r, timeout=30) as resp:
        raw = resp.read().decode()
        return resp.status, (json.loads(raw) if raw.strip() else None)


def _admin_token(admin_pass: str) -> str:
    st, j = _req("POST", f"{KC}/realms/{MASTER}/protocol/openid-connect/token",
                 data={"grant_type": "password", "client_id": "admin-cli",
                       "username": ADMIN_USER, "password": admin_pass}, form=True)
    return j["access_token"]


def main() -> None:
    ap = argparse.ArgumentParser(description="Rotate KC user passwords off the shared demo password.")
    ap.add_argument("--realms", required=True, help="comma-separated realms, e.g. borrowhood,borrowhood-staging")
    ap.add_argument("--users", required=True, help="comma-separated usernames, e.g. felix,akenel,angel,pam,ralph")
    ap.add_argument("--temporary", action="store_true", help="force the user to change it at next login (default: no)")
    args = ap.parse_args()
    realms = [r.strip() for r in args.realms.split(",") if r.strip()]
    users = [u.strip() for u in args.users.split(",") if u.strip()]

    admin_pass = _env("KEYCLOAK_ADMIN_PASSWORD") or getpass.getpass(f"KC admin password ({ADMIN_USER}): ")
    try:
        token = _admin_token(admin_pass)
    except urllib.error.HTTPError as e:
        sys.exit(f"✗ admin login failed ({e.code}). Check KEYCLOAK_ADMIN_PASSWORD.")
    print(f"✓ admin auth OK  ({KC}, realms={realms})")

    # New password — hidden, entered twice, guard-railed.
    pw = getpass.getpass("NEW password for these accounts (hidden): ")
    pw2 = getpass.getpass("Repeat it: ")
    if pw != pw2:
        sys.exit("✗ passwords did not match — nothing changed.")
    if pw.strip().lower() in BANNED:
        sys.exit("✗ that's a banned/shared password — pick a real one. Nothing changed.")
    if len(pw) < 10:
        sys.exit("✗ too short (min 10 chars) — nothing changed.")

    total = 0
    for realm in realms:
        print(f"\n— realm {realm} —")
        for u in users:
            try:
                st, found = _req("GET",
                    f"{KC}/admin/realms/{realm}/users?username={urllib.parse.quote(u)}&exact=true",
                    token=token)
            except urllib.error.HTTPError as e:
                print(f"  ! {u}: lookup failed ({e.code})"); continue
            if not found:
                print(f"  – {u}: not in {realm} (skipped)"); continue
            uid = found[0]["id"]
            try:
                _req("PUT", f"{KC}/admin/realms/{realm}/users/{uid}/reset-password", token=token,
                     data={"type": "password", "value": pw, "temporary": bool(args.temporary)})
                print(f"  ✓ {u}: password rotated")
                total += 1
            except urllib.error.HTTPError as e:
                print(f"  ✗ {u}: set failed ({e.code}) {e.read().decode()[:120]}")
    print(f"\nDone — {total} account(s) rotated across {len(realms)} realm(s). "
          f"helix_pass no longer opens them. (Sandbox left as-is.)")


if __name__ == "__main__":
    main()
