#!/usr/bin/env python3
"""Wipe specific TEST-user accounts from a KC realm by email/username substring -- for fresh
end-user testing. NEVER deletes the protected user (angel). Prints every account it removes.
Runs inside a container reaching keycloak:8080.
Usage: python lp_wipe_test_users.py <realm> <substr1> [<substr2> ...]
"""
import json
import sys
import urllib.parse
import urllib.request

KC = "http://keycloak:8080"
ADMIN_U, ADMIN_P = "helix_user", "helix_pass"
PROTECT = {"angel", "angel.kenel"}        # usernames never deleted
PROTECT_EMAIL_PREFIX = "angel.kenel@"     # this email is always kept

realm = sys.argv[1]
needles = [s.lower() for s in sys.argv[2:]]


def j(req):
    r = urllib.request.urlopen(req)
    raw = r.read()
    return json.loads(raw) if raw else None


tok = j(urllib.request.Request(
    f"{KC}/realms/master/protocol/openid-connect/token",
    data=urllib.parse.urlencode({"grant_type": "password", "client_id": "admin-cli",
                                 "username": ADMIN_U, "password": ADMIN_P}).encode(),
    method="POST"))["access_token"]
h = {"Authorization": f"Bearer {tok}"}
users = j(urllib.request.Request(f"{KC}/admin/realms/{realm}/users?max=1000", headers=h))

deleted = []
for u in users:
    un = (u.get("username") or "").lower()
    em = (u.get("email") or "").lower()
    if un in PROTECT or em.startswith(PROTECT_EMAIL_PREFIX):
        continue
    if any(n in (un + " " + em) for n in needles):
        try:
            urllib.request.urlopen(urllib.request.Request(
                f"{KC}/admin/realms/{realm}/users/{u['id']}", headers=h, method="DELETE"))
            deleted.append(u.get("username") or em)
            print(f"deleted KC user: {u.get('username')} <{u.get('email')}>")
        except Exception as e:  # noqa: BLE001
            print(f"  ! failed {un}: {e}")

print("DELETED_USERNAMES=" + json.dumps(deleted))
