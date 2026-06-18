#!/usr/bin/env python3
"""STAGING chain test: Block 4 (draft-a-listing recipe writes the listing) ->
Block 5 (/square/draft-listing pushes it into La Piazza as a draft). As mike."""
import json
import sys
import httpx

BOT = "https://staging-bottega.lapiazza.app"
KC = f"{BOT}/realms/borrowhood-staging/protocol/openid-connect/token"
c = httpx.Client(verify=False, timeout=120.0)

tok = c.post(KC, data={"grant_type": "password", "client_id": "lapiazza_web",
                       "username": "mike", "password": "helix_pass", "scope": "openid"}).json()["access_token"]
h = {"Authorization": f"Bearer {tok}"}
print("token OK\n")

print("[Block 4] run draft-a-listing recipe (member types a little)…")
r = c.post(f"{BOT}/api/v1/compute/bottega/recipes/draft-a-listing/run", headers=h, data={
    "kind": "A service I provide",
    "offering": "I fix and service bicycles, I come to you anywhere in town",
    "included": "tune-up, brakes, gears, puncture repair; for commuters and families",
    "price_hint": "",
})
if r.status_code != 200:
    print(f"  FAIL run {r.status_code}: {r.text[:300]}"); sys.exit(1)
res = r.json().get("result", {})
print(json.dumps(res, indent=2)[:900])

print("\n[Block 5] send the AI draft to La Piazza as a DRAFT listing…")
body = {
    "name": res.get("name", ""), "description": res.get("description", ""),
    "story": res.get("story", ""), "item_type": res.get("item_type", "service"),
    "listing_type": res.get("listing_type", "service"), "category": res.get("category", "services"),
    "subcategory": res.get("subcategory", ""), "condition": res.get("condition") or None,
    "tags": res.get("tags", ""), "price": res.get("suggested_price") or None,
    "price_unit": res.get("price_unit", ""), "currency": res.get("currency", "EUR"),
}
r = c.post(f"{BOT}/api/v1/compute/bottega/square/draft-listing", headers=h, json=body)
print(f"  HTTP {r.status_code}")
if r.status_code != 200:
    print(f"  FAIL: {r.text[:300]}"); sys.exit(1)
out = r.json()
print(json.dumps(out, indent=2))
print(f"\n✅ CHAIN PROVEN: a sentence -> AI listing -> live DRAFT in La Piazza")
print(f"   title: {res.get('name')!r}  price: {res.get('suggested_price')} {res.get('price_unit')}")
print(f"   view:  {out.get('view_url')}")
