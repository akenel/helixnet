#!/usr/bin/env python3
"""Bump a Keycloak realm's access-token lifespan so a work session doesn't expire mid-use.
Runs INSIDE a container that can reach the keycloak service (http://keycloak:8080).
Usage:  python set_token_lifespan.py <realm> [seconds]   (default 28800 = 8h)
"""
import json
import sys
import urllib.parse
import urllib.request

KC = "http://keycloak:8080"
USER = "helix_user"
PW = "helix_pass"
realm = sys.argv[1]
secs = int(sys.argv[2]) if len(sys.argv) > 2 else 28800


def _json(req):
    return json.load(urllib.request.urlopen(req))


# admin token
tok = _json(urllib.request.Request(
    f"{KC}/realms/master/protocol/openid-connect/token",
    data=urllib.parse.urlencode({
        "grant_type": "password", "client_id": "admin-cli",
        "username": USER, "password": PW}).encode(),
    method="POST"))["access_token"]
h = {"Authorization": f"Bearer {tok}"}

rep = _json(urllib.request.Request(f"{KC}/admin/realms/{realm}", headers=h))
old = rep.get("accessTokenLifespan")
rep["accessTokenLifespan"] = secs
# SSO session must outlive the access token so re-auth works silently
rep["ssoSessionIdleTimeout"] = max(int(rep.get("ssoSessionIdleTimeout") or 0), secs)
rep["ssoSessionMaxLifespan"] = max(int(rep.get("ssoSessionMaxLifespan") or 0), secs * 2)

urllib.request.urlopen(urllib.request.Request(
    f"{KC}/admin/realms/{realm}", data=json.dumps(rep).encode(),
    headers={**h, "Content-Type": "application/json"}, method="PUT"))
print(f"{realm}: accessTokenLifespan {old} -> {secs}s, ssoSessionIdleTimeout {rep['ssoSessionIdleTimeout']}s")
