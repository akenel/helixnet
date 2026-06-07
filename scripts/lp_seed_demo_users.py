#!/usr/bin/env python3
"""Seed a handful of demo login users into a Keycloak realm (password helix_pass + the
lapiazza-user role) so you can test the Bottega as different people. Idempotent.
Runs INSIDE a container that can reach keycloak:8080.  Usage: python lp_seed_demo_users.py <realm>
"""
import json
import sys
import urllib.parse
import urllib.request

KC = "http://keycloak:8080"
ADMIN_U, ADMIN_P, PW = "helix_user", "helix_pass", "helix_pass"
realm = sys.argv[1]

# A small, diverse demo crew (username, full name) -- the Wolf + everyday masters + a legend
DEMO = [
    ("angel", "Angel Kenel"), ("superman", "Clark Kent"), ("flora", "Flora Ferrara"),
    ("marco", "Marco Vitale"), ("mike", "Mike Kenel"), ("sally", "Sally Thompson"),
    ("nino", "Nino Cassisa"), ("ada", "Ada Lovelace"),
]


def j(req):
    return json.load(urllib.request.urlopen(req))


tok = j(urllib.request.Request(
    f"{KC}/realms/master/protocol/openid-connect/token",
    data=urllib.parse.urlencode({"grant_type": "password", "client_id": "admin-cli",
                                 "username": ADMIN_U, "password": ADMIN_P}).encode(),
    method="POST"))["access_token"]
h = {"Authorization": f"Bearer {tok}"}
role = j(urllib.request.Request(f"{KC}/admin/realms/{realm}/roles/lapiazza-user", headers=h))

created, existed = [], []
for uname, name in DEMO:
    found = j(urllib.request.Request(
        f"{KC}/admin/realms/{realm}/users?username={uname}&exact=true", headers=h))
    if found:
        existed.append(uname)
        uid = found[0]["id"]
    else:
        parts = name.split()
        body = json.dumps({
            "username": uname, "email": f"{uname}@lapiazza.local", "enabled": True,
            "emailVerified": True, "firstName": parts[0],
            "lastName": " ".join(parts[1:]) or "LaPiazza", "requiredActions": [],
            "credentials": [{"type": "password", "value": PW, "temporary": False}]}).encode()
        try:
            urllib.request.urlopen(urllib.request.Request(
                f"{KC}/admin/realms/{realm}/users", data=body,
                headers={**h, "Content-Type": "application/json"}, method="POST"))
            created.append(uname)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {uname}: {e}")
            continue
        uid = j(urllib.request.Request(
            f"{KC}/admin/realms/{realm}/users?username={uname}&exact=true", headers=h))[0]["id"]
    try:
        urllib.request.urlopen(urllib.request.Request(
            f"{KC}/admin/realms/{realm}/users/{uid}/role-mappings/realm",
            data=json.dumps([role]).encode(),
            headers={**h, "Content-Type": "application/json"}, method="POST"))
    except Exception:  # noqa: BLE001
        pass

print(f"{realm}: created {created}, existed {existed}, password={PW}")
