#!/usr/bin/env python3
"""Emit UPDATE SQL to relink bh_user.keycloak_id from each migrated user's OLD sub to their NEW
sub in the unified realm. Re-derives old->new by USERNAME (SRC realm has the old sub, DST has the
new), then keys the UPDATE on the old keycloak_id (what bh_user currently holds). Idempotent.
Runs in a container reaching keycloak:8080; pipe output into psql on the marketplace DB.
Usage: python lp_remap_sql.py [src_realm] [dst_realm]
"""
import json
import sys
import urllib.parse
import urllib.request

KC = "http://keycloak:8080"
ADMIN_U, ADMIN_P = "helix_user", "helix_pass"
SRC = sys.argv[1] if len(sys.argv) > 1 else "borrowhood-staging"
DST = sys.argv[2] if len(sys.argv) > 2 else "lapiazza-realm-staging"


def users(realm, tok):
    return json.load(urllib.request.urlopen(urllib.request.Request(
        f"{KC}/admin/realms/{realm}/users?max=1000",
        headers={"Authorization": f"Bearer {tok}"})))


tok = json.load(urllib.request.urlopen(urllib.request.Request(
    f"{KC}/realms/master/protocol/openid-connect/token",
    data=urllib.parse.urlencode({"grant_type": "password", "client_id": "admin-cli",
                                 "username": ADMIN_U, "password": ADMIN_P}).encode(),
    method="POST")))["access_token"]

dst_by_uname = {u["username"].lower(): u["id"] for u in users(DST, tok) if u.get("username")}
for u in users(SRC, tok):
    un, old = (u.get("username") or "").lower(), u.get("id")
    new = dst_by_uname.get(un)
    if un and old and new and old != new:
        print(f"UPDATE bh_user SET keycloak_id='{new}' WHERE keycloak_id='{old}';")
