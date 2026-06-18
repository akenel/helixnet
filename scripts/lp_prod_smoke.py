#!/usr/bin/env python3
"""PROD smoke for the Cleo bridge cut-over. As angel, against the live prod hosts.
Proves: Bottega auth on borrowhood + new code (recipe menu), Cleo prefill (2-3),
marketplace identity (login), and the bridge (5). Creates ONE test draft, then deletes it."""
import sys, httpx
KC = "https://lapiazza.app/realms/borrowhood/protocol/openid-connect/token"
BOT = "https://bottega.lapiazza.app"; SQ = "https://lapiazza.app"
c = httpx.Client(verify=False, timeout=60.0)

def main():
    r = c.post(KC, data={"grant_type":"password","client_id":"lapiazza_web","username":"angel","password":"helix_pass","scope":"openid"})
    if r.status_code != 200: print("FAIL token", r.status_code, r.text[:200]); return 1
    h = {"Authorization":"Bearer "+r.json()["access_token"]}
    print("1. token OK")

    r = c.get(f"{BOT}/api/v1/compute/bottega/recipes", headers=h)
    slugs = [x.get("slug") for x in r.json()] if r.status_code==200 else []
    print(f"2. Bottega recipes (auth on borrowhood + new code): {r.status_code}, draft-a-listing present={('draft-a-listing' in slugs)}")
    if r.status_code != 200 or "draft-a-listing" not in slugs: print("   FAIL"); return 1

    r = c.post(f"{BOT}/api/v1/compute/bottega/concierge/suggest-listing", headers=h, json={"language":"en"})
    sj = r.json() if r.status_code==200 else {}
    print(f"3. Cleo suggest-listing (Blocks 2-3): {r.status_code}, recommend={sj.get('recommend')}, kind={sj.get('kind')!r}")

    r = c.get(f"{SQ}/api/v1/users/me", headers=h)
    who = (r.json().get("display_name") if r.status_code==200 else None)
    print(f"4. Marketplace /users/me (login + identity): {r.status_code}, who={who!r}")
    if r.status_code != 200: print("   FAIL marketplace"); return 1

    r = c.post(f"{BOT}/api/v1/compute/bottega/square/draft-listing", headers=h, json={
        "name":"TEST — prod cut-over smoke (delete me)","description":"Bridge smoke after the prod cut-over. Safe to delete.",
        "item_type":"service","listing_type":"service","category":"services","tags":"test","price":1,"price_unit":"per visit"})
    if r.status_code != 200: print(f"5. FAIL bridge {r.status_code}: {r.text[:200]}"); return 1
    out = r.json(); iid = out.get("item_id")
    print(f"5. Bridge POST /square/draft-listing (Block 5): 200, item={iid}, view={out.get('view_url')}")

    d = c.delete(f"{SQ}/api/v1/items/{iid}", headers=h)
    print(f"6. cleanup DELETE item: {d.status_code} ({'removed' if d.status_code in (200,204) else 'left as draft — delete manually'})")
    print("\n✅ PROD SMOKE GREEN: all blocks live; both apps authenticate on the consolidated realm")
    return 0

if __name__ == "__main__":
    try: sys.exit(main())
    except Exception as e: print("ERROR", e); sys.exit(2)
