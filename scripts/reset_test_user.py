#!/usr/bin/env python3
"""
reset_test_user.py — wipe a La Piazza test user so they become a clean first-timer.

PART OF THE TESTING STRATEGY (two modes):
  • WIPE / start-fresh  = run this tool (deletes the user across KC + both app DBs).
  • PERSIST / continue  = simply do NOT run it; log in as the existing test user.
artemisthinking@gmail.com is the standing test user (a real Gmail made for testing).

SAFETY:
  • EXACT match only — never substring. ("Mozart", "Bogart", "Spartacus" all contain "art"!)
  • DRY-RUN by default. Pass --confirm to actually delete.
  • Refuses to run unless the Keycloak realm looks like staging (override: --allow-nonstaging).

RUN INSIDE the staging app container (it already has httpx, asyncpg, and the env):
  docker cp scripts/reset_test_user.py helix-platform-staging:/tmp/r.py
  # dry-run (shows what WOULD be deleted, deletes nothing):
  docker exec helix-platform-staging python /tmp/r.py \
      --email artemisthinking@gmail.com --usernames art-ten-jun,artemisthinking-june13
  # real delete:
  docker exec helix-platform-staging python /tmp/r.py \
      --email artemisthinking@gmail.com --usernames art-ten-jun,artemisthinking-june13 --confirm
"""
import argparse
import asyncio
import os
import sys

import asyncpg
import httpx


def env(key: str, default=None):
    v = os.environ.get(key, default)
    if v is None:
        sys.exit(f"missing required env: {key}")
    return v


KC = env("KEYCLOAK_SERVER_URL")
KC_ADMIN = env("KEYCLOAK_ADMIN_USER")
KC_PASS = env("KEYCLOAK_ADMIN_PASSWORD")
REALM = os.environ.get("LP_REALM", "lapiazza-realm-staging")
HELIX_DB = env("ASYNC_DATABASE_URL").replace("+asyncpg", "")        # bottega (helix_db — SHARED w/ prod)
BH_DB = os.environ.get("BH_DATABASE_URL", "").replace("+asyncpg", "")  # marketplace (borrowhood_staging)


async def _kc_token(c: httpx.AsyncClient) -> str:
    r = await c.post(
        f"{KC}/realms/master/protocol/openid-connect/token",
        data={"grant_type": "password", "client_id": "admin-cli",
              "username": KC_ADMIN, "password": KC_PASS},
    )
    r.raise_for_status()
    return r.json()["access_token"]


async def main() -> None:
    ap = argparse.ArgumentParser(description="Wipe a La Piazza test user (EXACT match, dry-run by default).")
    ap.add_argument("--email", required=True, help="exact email (bh_user + KC lookup)")
    ap.add_argument("--usernames", default="", help="comma-separated EXACT bottega/KC usernames")
    ap.add_argument("--confirm", action="store_true", help="actually delete (default: dry-run)")
    ap.add_argument("--allow-nonstaging", action="store_true", help="permit a non-staging realm (DANGER)")
    a = ap.parse_args()

    usernames = [u.strip() for u in a.usernames.split(",") if u.strip()]
    mode = "DELETE" if a.confirm else "DRY-RUN"

    if "staging" not in REALM and not a.allow_nonstaging:
        sys.exit(f"REFUSING: realm '{REALM}' is not a staging realm. Pass --allow-nonstaging only if certain.")

    print(f"== reset_test_user [{mode}] ==")
    print(f"   realm    = {REALM}")
    print(f"   email    = {a.email}")
    print(f"   usernames= {usernames or '(none)'}")
    print(f"   bottega  = helix_db (SHARED with prod — exact-username scope only)")
    print(f"   market   = {BH_DB.rsplit('/', 1)[-1] if BH_DB else 'UNSET'}")
    print()

    # ---- Keycloak (the staging realm) ----
    async with httpx.AsyncClient(verify=False, timeout=30) as c:
        tok = await _kc_token(c)
        h = {"Authorization": f"Bearer {tok}"}
        matched: list[tuple] = []

        async def add_matches(params):
            rs = (await c.get(f"{KC}/admin/realms/{REALM}/users", headers=h, params=params)).json()
            for u in rs:
                if u["id"] not in {m[0] for m in matched}:
                    matched.append((u["id"], u.get("username"), u.get("email")))

        await add_matches({"email": a.email, "exact": "true"})
        for un in usernames:
            await add_matches({"username": un, "exact": "true"})

        print(f"Keycloak users matched: {[(un, em) for _, un, em in matched] or 'none'}")
        if a.confirm:
            for uid, un, _em in matched:
                r = await c.delete(f"{KC}/admin/realms/{REALM}/users/{uid}", headers=h)
                print(f"   - deleted KC user {un}: HTTP {r.status_code}")

    # ---- bottega rows in helix_db (exact usernames only) ----
    conn = await asyncpg.connect(HELIX_DB)
    try:
        for tbl in ("bottega_sessions", "bottega_profile_history", "bottega_tasks", "bottega_profiles"):
            if not await conn.fetchval("SELECT to_regclass($1)", tbl):
                continue
            n = await conn.fetchval(
                f"SELECT count(*) FROM {tbl} WHERE username = ANY($1::text[])", usernames) if usernames else 0
            print(f"helix_db.{tbl}: {n} row(s) for {usernames}")
            if a.confirm and usernames and n:
                print(f"   - {await conn.execute(f'DELETE FROM {tbl} WHERE username = ANY($1::text[])', usernames)}")
    finally:
        await conn.close()

    # ---- bh_user in the staging marketplace DB (exact email) ----
    if BH_DB:
        bc = await asyncpg.connect(BH_DB)
        try:
            rows = await bc.fetch("SELECT id, email, display_name FROM bh_user WHERE email = $1", a.email)
            print(f"bh_user: {len(rows)} row(s) for {a.email} -> {[r['display_name'] for r in rows]}")
            if a.confirm and rows:
                try:
                    print(f"   - {await bc.execute('DELETE FROM bh_user WHERE email = $1', a.email)}")
                except asyncpg.ForeignKeyViolationError as e:
                    print(f"   ! bh_user delete blocked by FK ({e}). Left in place; "
                          f"signup re-link avoided by deleting the KC user. Handle children later if needed.")
        finally:
            await bc.close()

    print()
    print("DONE — user wiped." if a.confirm
          else "DRY-RUN complete — nothing deleted. Re-run with --confirm to delete.")


if __name__ == "__main__":
    asyncio.run(main())
