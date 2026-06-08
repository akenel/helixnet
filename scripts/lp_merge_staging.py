#!/usr/bin/env python3
"""BL-014 (staging): merge the Square realm into the Bottega realm so ONE realm serves both.
Replicates the marketplace client + migrates its users into lapiazza-realm-staging, and emits
an old->new KC-sub map (so bh_user.keycloak_id can be remapped). Idempotent. STAGING ONLY.
Runs inside a container that reaches keycloak:8080.  Usage: python lp_merge_staging.py
"""
import json
import sys
import urllib.parse
import urllib.request

KC = "http://keycloak:8080"
ADMIN_U, ADMIN_P, PW = "helix_user", "helix_pass", "helix_pass"
SRC = "borrowhood-staging"          # the Square realm (source)
DST = "lapiazza-realm-staging"      # the unified Bottega realm (target)
CLIENT_ID = "borrowhood-web"        # the marketplace client to bring over
EXTRA_REDIRECTS = ["https://staging.lapiazza.app/*", "https://staging-bottega.lapiazza.app/*"]


def req(method, path, body=None, tok=None):
    h = {"Content-Type": "application/json"}
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(f"{KC}{path}", data=data, headers=h, method=method)
    resp = urllib.request.urlopen(r)
    raw = resp.read()
    return json.loads(raw) if raw else None


def admin_token():
    r = urllib.request.Request(
        f"{KC}/realms/master/protocol/openid-connect/token",
        data=urllib.parse.urlencode({"grant_type": "password", "client_id": "admin-cli",
                                     "username": ADMIN_U, "password": ADMIN_P}).encode(),
        method="POST")
    return json.load(urllib.request.urlopen(r))["access_token"]


tok = admin_token()

# ---- 1) replicate the marketplace client into the unified realm ----
src_clients = req("GET", f"/admin/realms/{SRC}/clients?clientId={CLIENT_ID}", tok=tok)
if not src_clients:
    print(f"FATAL: client {CLIENT_ID} not found in {SRC}"); sys.exit(1)
sc = src_clients[0]
sc_secret = req("GET", f"/admin/realms/{SRC}/clients/{sc['id']}/client-secret", tok=tok).get("value")

dst_clients = req("GET", f"/admin/realms/{DST}/clients?clientId={CLIENT_ID}", tok=tok)
redirects = sorted(set((sc.get("redirectUris") or []) + EXTRA_REDIRECTS))
client_rep = {
    "clientId": CLIENT_ID, "enabled": True, "protocol": "openid-connect",
    "publicClient": sc.get("publicClient", False), "secret": sc_secret,
    "standardFlowEnabled": True, "directAccessGrantsEnabled": True,
    "redirectUris": redirects, "webOrigins": sc.get("webOrigins") or ["+"],
    "attributes": sc.get("attributes") or {},
}
if dst_clients:
    cid = dst_clients[0]["id"]
    req("PUT", f"/admin/realms/{DST}/clients/{cid}", {**dst_clients[0], **client_rep}, tok=tok)
    print(f"client {CLIENT_ID}: UPDATED in {DST}")
else:
    req("POST", f"/admin/realms/{DST}/clients", client_rep, tok=tok)
    print(f"client {CLIENT_ID}: CREATED in {DST}")

# ---- 2) migrate users (test users -> recreate w/ helix_pass + lapiazza-user) ----
role = req("GET", f"/admin/realms/{DST}/roles/lapiazza-user", tok=tok)
src_users = req("GET", f"/admin/realms/{SRC}/users?max=1000", tok=tok)
submap = {}      # old_sub -> {"email":..., "username":..., "new_sub":...}
created, existed = 0, 0
for u in src_users:
    uname = u.get("username")
    if not uname:
        continue
    found = req("GET", f"/admin/realms/{DST}/users?username={urllib.parse.quote(uname)}&exact=true", tok=tok)
    if found:
        existed += 1
        new = found[0]
    else:
        rep = {"username": uname, "email": u.get("email"), "enabled": u.get("enabled", True),
               "emailVerified": True, "firstName": u.get("firstName"), "lastName": u.get("lastName"),
               "requiredActions": [],
               "credentials": [{"type": "password", "value": PW, "temporary": False}]}
        try:
            req("POST", f"/admin/realms/{DST}/users", rep, tok=tok)
            created += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ! {uname}: {e}"); continue
        new = req("GET", f"/admin/realms/{DST}/users?username={urllib.parse.quote(uname)}&exact=true", tok=tok)[0]
    try:
        req("POST", f"/admin/realms/{DST}/users/{new['id']}/role-mappings/realm", [role], tok=tok)
    except Exception:  # noqa: BLE001
        pass
    submap[u["id"]] = {"email": u.get("email"), "username": uname, "new_sub": new["id"]}

print(f"users: created {created}, existed {existed}, total {len(src_users)}")
print("SUBMAP_JSON=" + json.dumps(submap))
