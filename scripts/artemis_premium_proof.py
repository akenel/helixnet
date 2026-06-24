#!/usr/bin/env python3
"""Artemis Premium — end-to-end staging PROOF (run INSIDE helix-platform-sandbox).

Proves the whole wiring of the cutover (docs/BANCO-ARTEMIS-PREMIUM-CUTOVER-PLAN.md)
on the only both-sides-clean environment (the sandbox): app DB banco_sandbox,
publishes into borrowhood_staging, realm borrowhood-staging. Zero prod touched.

The chain:
  1. Provision the shop's La Piazza BUSINESS ACCOUNT in borrowhood-staging
     (a normal KC user + VAT/business attributes + the lapiazza-business role).
  2. Mint that account's own token (principal propagation — the bridge posts AS it).
  3. Publish a Banco product as a DRAFT listing via the REAL square_bridge.
  4. Report the listing id/slug — it now rests in La Piazza staging under the shop,
     ready for the owner to publish (push-once-then-decouple, decision D3).

Run (from a laptop):
  cat scripts/artemis_premium_proof.py | ssh root@<box> \
      "docker exec -i -w /app helix-platform-sandbox python -"

Idempotent: re-running reuses the business account, makes a fresh draft each time
(re-push = a new product, never an update — decision D3).
"""
import asyncio

import httpx

from src.core.config import settings
from src.services.square_bridge import create_draft_listing, SquareBridgeError

REALM = settings.LP_REALM            # borrowhood-staging (this env's La Piazza realm)
CLIENT = settings.LP_CLIENT          # lapiazza_web (has direct-access grants)
KC = settings.KEYCLOAK_SERVER_URL
ADMIN_U = settings.KEYCLOAK_ADMIN_USER
ADMIN_P = settings.KEYCLOAK_ADMIN_PASSWORD.get_secret_value()

# The shop's business identity (keyed by a verifiable email — decision D2/R4).
BIZ_USER, BIZ_PASS = "biz-artemis", "helix_pass"
BIZ_EMAIL, BIZ_NAME, BIZ_VAT = "artemis@artemis.example", "Artemis Store", "CHE-123.456.789"
ROLES = ["bh-member", "bh-lender", "lapiazza-user", "lapiazza-business"]
ATTRS = {"account_type": ["business"], "business_name": [BIZ_NAME], "vat_number": [BIZ_VAT]}

# The Banco product to publish — the Born Once star, framed as a marketplace good.
PRODUCT = {
    "name": "Hemp Sana CBD Cream 40ml",
    "description": "Swiss-made CBD cream, 40ml. Soothing hemp balm for tired muscles and joints.",
    "story": "The star of Banco's first sale ever — published straight from the Artemis head-shop counter.",
    # BorrowHood enums: item_type physical|digital|service|space|made_to_order;
    # listing_type rent|sell|commission|offer|service|training|auction|giveaway|event|raffle
    # (a head-shop item can be ANY of these — sell today, raffle/giveaway tomorrow, decision in the data).
    "item_type": "physical", "listing_type": "sell",
    "category": "wellness", "subcategory": "cbd", "tags": "cbd,hemp,wellness,swiss",
    "price": 40, "price_unit": "each", "currency": "CHF", "content_language": "en",
}


async def main():
    print(f"env: realm={REALM}  client={CLIENT}  publish_to={settings.SQUARE_API_URL}  public={settings.SQUARE_PUBLIC_URL}")
    async with httpx.AsyncClient(verify=False, timeout=30.0) as c:
        tok = (await c.post(f"{KC}/realms/master/protocol/openid-connect/token", data={
            "grant_type": "password", "client_id": "admin-cli",
            "username": ADMIN_U, "password": ADMIN_P})).json()["access_token"]
        h = {"Authorization": f"Bearer {tok}"}
        base = f"{KC}/admin/realms/{REALM}"

        # 1a) ensure the lapiazza-business role exists (the verified-business marker)
        if (await c.get(f"{base}/roles/lapiazza-business", headers=h)).status_code == 404:
            await c.post(f"{base}/roles", headers=h, json={"name": "lapiazza-business"})
            print("  + role lapiazza-business created")

        # 1b) ensure the business account — basic fields first (the proven signup shape;
        # custom attributes are added best-effort below so a strict user-profile can't block us)
        found = (await c.get(f"{base}/users", headers=h, params={"username": BIZ_USER, "exact": "true"})).json()
        if not found:
            cr = await c.post(f"{base}/users", headers=h, json={
                "username": BIZ_USER, "email": BIZ_EMAIL, "enabled": True, "emailVerified": True,
                "firstName": BIZ_NAME, "lastName": "Business", "requiredActions": [],
                "credentials": [{"type": "password", "value": BIZ_PASS, "temporary": False}]})
            if cr.status_code not in (201, 409):
                print(f"  ! user create failed ({cr.status_code}): {cr.text[:200]}")
                return
            found = (await c.get(f"{base}/users", headers=h, params={"username": BIZ_USER, "exact": "true"})).json()
            print(f"  + business account {BIZ_USER} created")
        uid = found[0]["id"]
        await c.put(f"{base}/users/{uid}/reset-password", headers=h,
                    json={"type": "password", "value": BIZ_PASS, "temporary": False})
        # business attributes (VAT, name) — best-effort. NOTE: a KC user PUT is a FULL-rep update,
        # so firstName/lastName MUST be included or KC nulls them → "Account is not fully set up".
        ar = await c.put(f"{base}/users/{uid}", headers=h, json={
            "enabled": True, "emailVerified": True, "email": BIZ_EMAIL,
            "firstName": BIZ_NAME, "lastName": "Business", "requiredActions": [],
            "attributes": ATTRS})
        print(f"  {'= business attributes set (VAT/name)' if ar.status_code < 300 else f'~ attributes skipped ({ar.status_code}) — user-profile is strict, not needed for the proof'}")
        for rn in ROLES:
            rr = await c.get(f"{base}/roles/{rn}", headers=h)
            if rr.status_code == 200:
                await c.post(f"{base}/users/{uid}/role-mappings/realm", headers=h, json=[rr.json()])
        print(f"  = business account ready  uid={uid}  roles={ROLES}  VAT={BIZ_VAT}")

        # 2) mint the business account's own token (the bridge posts AS this identity)
        tr = (await c.post(f"{KC}/realms/{REALM}/protocol/openid-connect/token", data={
            "grant_type": "password", "client_id": CLIENT, "username": BIZ_USER,
            "password": BIZ_PASS, "scope": "openid profile"})).json()
        if "access_token" not in tr:
            print(f"  ! could not mint business token: {tr}")
            return
        token = tr["access_token"]
        print("  = minted business-account token")

    # 3) publish via the REAL bridge — exactly what the Banco feature will call
    print("\npublishing the Banco product as a La Piazza draft...")
    try:
        res = await create_draft_listing(token, PRODUCT)
    except SquareBridgeError as e:
        print(f"  ❌ bridge error: {e}")
        return
    print("  ✅ DRAFT LISTING CREATED — it rests in La Piazza staging under the shop:")
    for k, v in res.items():
        print(f"       {k}: {v}")


asyncio.run(main())
