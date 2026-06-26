#!/usr/bin/env python3
"""Proof: one account in a unified realm carries BOTH a workforce role and a public tier.

Seeds a user with `pos-cashier` (workforce) + `member` (public tier) in the target realm,
gets a token via the POS client, and decodes it to show both roles ride on the one account.
This is the "Pam = cashier + member, one login" acceptance check (token-level, non-disruptive).
Admin pass via $KC_ADMIN_PASSWORD.
"""
import base64
import json
import os
import sys
import httpx

REALM = sys.argv[1] if len(sys.argv) > 1 else "kc-sandbox"
KC = os.environ.get("KC_URL", "http://keycloak:8080")
ADMIN_USER = os.environ.get("KC_ADMIN_USER", "helix_user")
ADMIN_PASS = os.environ["KC_ADMIN_PASSWORD"]
CLIENT = "helix_pos_web"
USER, PW = "pam", "helix_pass"
WANT = {"pos-cashier", "member"}


def jwt_roles(token):
    mid = token.split(".")[1]
    mid += "=" * (-len(mid) % 4)
    payload = json.loads(base64.urlsafe_b64decode(mid))
    return set(payload.get("realm_access", {}).get("roles", [])), payload.get("preferred_username")


with httpx.Client(verify=False, timeout=30.0) as c:
    tok = c.post(f"{KC}/realms/master/protocol/openid-connect/token",
                 data={"grant_type": "password", "client_id": "admin-cli",
                       "username": ADMIN_USER, "password": ADMIN_PASS}).json()["access_token"]
    c.headers["Authorization"] = f"Bearer {tok}"
    base = f"{KC}/admin/realms/{REALM}"

    # ensure user
    found = c.get(f"{base}/users", params={"username": USER, "exact": "true"}).json()
    profile = {"enabled": True, "emailVerified": True, "requiredActions": [],
               "email": "pam@example.com", "firstName": "Pam", "lastName": "Cashier"}
    if found:
        uid = found[0]["id"]
        print(f"  = user {USER} exists (uid {uid[:8]}…)")
    else:
        c.post(f"{base}/users", json={"username": USER, **profile}).raise_for_status()
        uid = c.get(f"{base}/users", params={"username": USER, "exact": "true"}).json()[0]["id"]
        print(f"  + created user {USER} (uid {uid[:8]}…)")
    c.put(f"{base}/users/{uid}/reset-password",
          json={"type": "password", "value": PW, "temporary": False}).raise_for_status()
    # full profile so KC's Verify-Profile action doesn't block direct-grant login
    c.put(f"{base}/users/{uid}", json=profile).raise_for_status()

    # assign pos-cashier + member
    reps = [c.get(f"{base}/roles/{r}").json() for r in ("pos-cashier", "member")]
    c.post(f"{base}/users/{uid}/role-mappings/realm", json=reps).raise_for_status()
    print(f"  + assigned roles: pos-cashier (workforce) + member (public tier)")

    # token via the POS client
    r = c.post(f"{KC}/realms/{REALM}/protocol/openid-connect/token",
               data={"grant_type": "password", "client_id": CLIENT, "username": USER, "password": PW})
    if r.status_code != 200:
        print(f"\n  ❌ token request failed ({r.status_code}): {r.text[:200]}")
        sys.exit(1)
    roles, who = jwt_roles(r.json()["access_token"])
    app_roles = {x for x in roles if not x.startswith("default-roles") and x not in ("offline_access", "uma_authorization")}
    print(f"\n  token issued by realm '{REALM}' for '{who}'")
    print(f"  app/tier roles in token: {sorted(app_roles)}")

    print("\n" + "=" * 62)
    if WANT <= roles:
        print(f"  ✅ PROOF: ONE account carries BOTH hats in '{REALM}' —")
        print(f"     pos-cashier (Banco) + member (La Piazza), one login.")
    else:
        print(f"  ❌ missing: {WANT - roles}")
    print("=" * 62)
    sys.exit(0 if WANT <= roles else 1)
