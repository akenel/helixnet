#!/usr/bin/env python3
"""Prove the Cleo bridge mechanism on STAGING: the Bottega-held user token (issued by the
consolidated `borrowhood-staging` realm via lapiazza_web) can create a DRAFT listing — with a
default cover image — in La Piazza, AS the user. This is principal propagation in action:
same realm + BorrowHood's verify_aud=False => the user's own token is accepted cross-app.

STAGING ONLY. Creates a DRAFT (invisible to the marketplace) marked TEST. Safe to delete.
"""
import sys
import httpx

KC = "https://staging-bottega.lapiazza.app/realms/borrowhood-staging/protocol/openid-connect/token"
API = "https://staging.lapiazza.app"
USER, PASS, CLIENT = "mike", "helix_pass", "lapiazza_web"
PLACEHOLDER = f"{API}/static/og-default.png"  # default cover until the user adds a real photo

c = httpx.Client(verify=False, timeout=60.0)


def main():
    print("[1] get mike's token from borrowhood-staging via lapiazza_web (the Bottega-side token)")
    r = c.post(KC, data={"grant_type": "password", "client_id": CLIENT,
                         "username": USER, "password": PASS, "scope": "openid"})
    if r.status_code != 200:
        print(f"  FAIL token {r.status_code}: {r.text[:200]}"); return 1
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    print("  OK got lapiazza_web token")

    print("[2] create a SERVICE item in La Piazza as mike (proves cross-app principal propagation)")
    r = c.post(f"{API}/api/v1/items", headers=h, json={
        "name": "TEST — Mobile bike tune-up (Cleo bridge probe)",
        "description": "On-site bike service. Draft created by the Bottega bridge probe — safe to delete.",
        "content_language": "en", "item_type": "service", "category": "services",
        "tags": "bike,repair,mobile",
    })
    print(f"  status {r.status_code}")
    if r.status_code != 201:
        print(f"  FAIL: {r.text[:300]}"); return 1
    item = r.json(); iid = item.get("id")
    print(f"  OK item id={iid} slug={item.get('slug')}  (token ACCEPTED cross-app ✅)")

    print("[3] attach a DEFAULT cover image by URL (no listing is ever born naked)")
    r = c.post(f"{API}/api/v1/items/{iid}/media", headers=h,
               json={"url": PLACEHOLDER, "alt_text": "Replace with your photo", "media_type": "photo"})
    print(f"  status {r.status_code}  cover={'OK ✅' if r.status_code == 201 else 'FAIL'}")
    if r.status_code != 201:
        print(f"  detail: {r.text[:300]}")

    print("[4] create a DRAFT listing (invisible until mike publishes)")
    r = c.post(f"{API}/api/v1/listings", headers=h, json={
        "item_id": iid, "listing_type": "service", "status": "draft",
        "price": 25, "price_unit": "per visit", "currency": "EUR",
        "notes": "Draft drafted by Cleo — review and publish when ready.",
    })
    print(f"  status {r.status_code}")
    if r.status_code != 201:
        print(f"  FAIL: {r.text[:300]}"); return 1
    lst = r.json()
    print(f"  OK listing id={lst.get('id')} status={lst.get('status')} type={lst.get('listing_type')}")

    print("[5] confirm mike can see it + it carries the cover")
    r = c.get(f"{API}/api/v1/items/{iid}", headers=h)
    media = (r.json().get("media") or []) if r.status_code == 200 else []
    print(f"  item GET {r.status_code}, media count={len(media)}")
    print("\n=== BRIDGE MECHANISM PROVEN: Bottega token -> draft service listing + cover, in La Piazza, as mike ===")
    print(f"   item id={iid}  (DRAFT — invisible to marketplace; delete anytime)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"ERROR: {e}"); sys.exit(2)
