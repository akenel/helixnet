# File: src/services/lp_publish.py
# Publish a Banco product into La Piazza as a DRAFT listing, under the shop's OWN business
# account (Artemis Premium — docs/BANCO-ARTEMIS-PREMIUM-CUTOVER-PLAN.md).
#
# PROVISIONED-CREDENTIAL PATH (chosen 2026-06-24): the shop's La Piazza identity is provisioned
# in this env's La Piazza realm (KC) and we act AS it via a held credential. The "less-clean"
# part — acquiring the business token — is isolated to _business_password/_business_token so the
# PRODUCTION hardening (KC token-exchange via a confidential client) swaps in without touching the
# rest. See the cutover plan §R4/ID5.
#
# Env parity (the box matrix): on the sandbox/staging containers LP_REALM=borrowhood-staging and
# SQUARE_API_URL -> borrowhood_staging, so this publishes to STAGING La Piazza. On a real prod
# Banco it repoints to the prod realm + marketplace. Nothing here is env-specific.
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

import httpx

from src.core.config import settings
from src.services.square_bridge import create_draft_listing, SquareBridgeError

logger = logging.getLogger("helix.lp_publish")

# The roles the shop's business identity holds on La Piazza (same as any member + the business marker).
_BIZ_ROLES = ["bh-member", "bh-lender", "lapiazza-user", "lapiazza-business"]


def _business_password() -> str:
    """The provisioned credential. Sandbox/PoC: a shared dev password (override via LP_BUSINESS_PASSWORD).
    PRODUCTION TODO: replace this whole acquisition path with KC token-exchange (a confidential client),
    or a per-shop generated secret stored ENCRYPTED on store_settings — never a shared constant in prod."""
    return getattr(settings, "LP_BUSINESS_PASSWORD", None) or "helix_pass"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-") or "shop"


async def _admin_token(c: httpx.AsyncClient) -> str:
    r = await c.post(f"{settings.KEYCLOAK_SERVER_URL}/realms/master/protocol/openid-connect/token",
                     data={"grant_type": "password", "client_id": "admin-cli",
                           "username": settings.KEYCLOAK_ADMIN_USER,
                           "password": settings.KEYCLOAK_ADMIN_PASSWORD.get_secret_value()})
    r.raise_for_status()
    return r.json()["access_token"]


async def ensure_business_identity(c: httpx.AsyncClient, store) -> tuple[str, str]:
    """Ensure the shop's La Piazza business account exists in this env's realm. Returns (username, uid).

    This IS the 'Enable La Piazza' internal-provisioning motion: a normal KC user keyed off the shop,
    carrying business_name + VAT as attributes + the lapiazza-business role. Idempotent (re-running
    just re-asserts the password, attributes and roles). NOTE: a KC user PUT is a full-rep update, so
    firstName/lastName MUST be resent or KC nulls them -> 'Account is not fully set up' on the grant."""
    realm = settings.LP_REALM
    biz_name = (getattr(store, "legal_name", None) or getattr(store, "store_name", None) or "Shop").strip()
    email = (getattr(store, "email", None) or f"{_slug(biz_name)}@lapiazza.local").strip()
    username = "biz-" + _slug(getattr(store, "store_name", None) or biz_name)
    vat = getattr(store, "vat_number", None) or ""
    pw = _business_password()
    attrs = {"account_type": ["business"], "business_name": [biz_name], "vat_number": [vat]}

    tok = await _admin_token(c)
    h = {"Authorization": f"Bearer {tok}"}
    base = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{realm}"

    if (await c.get(f"{base}/roles/lapiazza-business", headers=h)).status_code == 404:
        await c.post(f"{base}/roles", headers=h, json={"name": "lapiazza-business"})

    # MODEL A (owner-as-business): if the shop is already LINKED to a La Piazza account, publish AS
    # it — one account, no duplicate shop personas. Use it as-is: ensure the lapiazza-business role,
    # but DON'T reset its password or rewrite its name here (it's the owner's account). The token
    # comes via the provisioned credential (sandbox) / KC token-exchange (prod). A stale link (the
    # account was deleted) falls through to provision a fresh shop account + re-link.
    linked = getattr(store, "lapiazza_business_id", None)
    if linked:
        u = await c.get(f"{base}/users/{linked}", headers=h)
        if u.status_code == 200:
            uname = u.json().get("username")
            rb = await c.get(f"{base}/roles/lapiazza-business", headers=h)
            if rb.status_code == 200:
                await c.post(f"{base}/users/{linked}/role-mappings/realm", headers=h, json=[rb.json()])
            return uname, linked

    found = (await c.get(f"{base}/users", headers=h, params={"username": username, "exact": "true"})).json()
    if not found:
        cr = await c.post(f"{base}/users", headers=h, json={
            "username": username, "email": email, "enabled": True, "emailVerified": True,
            "firstName": biz_name[:60], "lastName": "Business", "requiredActions": [],
            "credentials": [{"type": "password", "value": pw, "temporary": False}]})
        if cr.status_code not in (201, 409):
            raise SquareBridgeError(f"couldn't create the shop's La Piazza account ({cr.status_code})")
        found = (await c.get(f"{base}/users", headers=h, params={"username": username, "exact": "true"})).json()
    uid = found[0]["id"]
    await c.put(f"{base}/users/{uid}", headers=h, json={
        "enabled": True, "emailVerified": True, "email": email,
        "firstName": biz_name[:60], "lastName": "Business", "requiredActions": [], "attributes": attrs})
    await c.put(f"{base}/users/{uid}/reset-password", headers=h,
                json={"type": "password", "value": pw, "temporary": False})
    for rn in _BIZ_ROLES:
        rr = await c.get(f"{base}/roles/{rn}", headers=h)
        if rr.status_code == 200:
            await c.post(f"{base}/users/{uid}/role-mappings/realm", headers=h, json=[rr.json()])
    return username, uid


async def set_lp_business_profile(token: str, store) -> None:
    """Fill the shop's La Piazza PUBLIC business profile — the dashboard's Seller Type=Business +
    Business Name + VAT/Tax ID. Crucially sets display_name = the business name, so every listing
    shows the SHOP (e.g. 'Artemis GmbH'), not a person. This is the 'call to LP' that makes the
    provisioned account look like a real verified business. Best-effort — a profile hiccup must
    never block the publish."""
    biz_name = (getattr(store, "legal_name", None) or getattr(store, "store_name", None) or "Shop").strip()
    vat = getattr(store, "vat_number", None) or ""
    body = {
        "display_name": biz_name[:120],      # the seller name shown on listings + the Locandina
        "seller_type": "business",
        "business_name": biz_name[:200],
        "vat_number": str(vat)[:50],
    }
    try:
        async with httpx.AsyncClient(base_url=settings.SQUARE_API_URL, verify=False, timeout=20.0) as c:
            r = await c.patch("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}, json=body)
            if r.status_code >= 300:
                logger.warning("lp_publish: set business profile -> %s %s", r.status_code, r.text[:120])
    except Exception:  # noqa: BLE001
        logger.warning("lp_publish: set business profile failed", exc_info=True)


async def _business_token(c: httpx.AsyncClient, username: str) -> str:
    r = await c.post(f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.LP_REALM}/protocol/openid-connect/token",
                     data={"grant_type": "password", "client_id": settings.LP_CLIENT,
                           "username": username, "password": _business_password(),
                           "scope": "openid profile"})
    if r.status_code != 200:
        raise SquareBridgeError("couldn't sign in the shop's La Piazza account")
    return r.json()["access_token"]


def product_to_listing(product, store) -> dict:
    """THE canonical Banco-product -> La Piazza-listing mapping. Do-it-right-but-simple:
    PULL the four essentials (title - image - description - price); DEFAULT the rest.
    No per-product category guessing -- 'other' until BorrowHood adds a Health & Wellness category
    (docs/TODO-BORROWHOOD-HEALTH-WELLNESS-CATEGORY.md). A manager can refine any field on La Piazza."""
    currency = (getattr(store, "currency", None) or "CHF")
    return {
        "name": product.name,
        "description": product.description or "",
        # cover is NOT set here — product.image_url is a relative Banco path La Piazza can't render.
        # The real photo is UPLOADED to La Piazza after create (decoupled) by _carry_product_image.
        "cover_url": "",
        "price": product.price,
        "currency": str(currency)[:3],
        "item_type": "physical",                     # head-shop goods
        "listing_type": "sell",                      # sell today; raffle/giveaway/rent is a later choice
        "category": "other",                         # never guess; see TODO doc
        "content_language": "en",
        "tags": (product.barcode or ""),
    }


async def _carry_product_image(token: str, item_id: str, product) -> None:
    """Carry the product photo onto the listing — DECOUPLED. Fetch the bytes from THIS Banco's own
    image endpoint (localhost, inside the container) and UPLOAD them to La Piazza so the listing owns
    its copy (survives a Banco reset / product change). Best-effort: a missing/failed image must
    NEVER block the publish."""
    img = getattr(product, "image_url", None)
    if not img or not item_id:
        return
    try:
        src = img if str(img).startswith("http") else f"http://localhost:8000{img}"
        async with httpx.AsyncClient(verify=False, timeout=30.0) as c:
            r = await c.get(src)
        if r.status_code != 200 or not r.content:
            logger.info("lp_publish: no product image to carry (%s -> %s)", src, r.status_code)
            return
        ct = r.headers.get("content-type", "image/jpeg")
        ext = "png" if "png" in ct else ("webp" if "webp" in ct else "jpg")
        async with httpx.AsyncClient(base_url=settings.SQUARE_API_URL, verify=False, timeout=30.0) as lc:
            up = await lc.post(f"/api/v1/items/{item_id}/upload",
                               headers={"Authorization": f"Bearer {token}"},
                               files={"file": (f"product.{ext}", r.content, ct)})
            if up.status_code not in (200, 201):
                logger.warning("lp_publish: image upload -> %s %s", up.status_code, up.text[:120])
    except Exception:  # noqa: BLE001
        logger.warning("lp_publish: carry product image failed", exc_info=True)


async def publish_product(db, product, store) -> dict:
    """Publish ONE Banco product as a La Piazza draft under the shop, and record the push on the
    product (push-once-then-decouple, D3 — re-publishing makes a NEW listing, never an update).
    Returns the bridge result {item_id, listing_id, slug, status, view_url, cover}."""
    async with httpx.AsyncClient(verify=False, timeout=30.0) as c:
        username, uid = await ensure_business_identity(c, store)
        token = await _business_token(c, username)
    # fill the LP business profile FIRST (display_name = business name) so the listing is born
    # showing the shop as a verified business, not a person.
    await set_lp_business_profile(token, store)
    res = await create_draft_listing(token, product_to_listing(product, store))
    await _carry_product_image(token, res.get("item_id"), product)   # decoupled: upload the real photo

    product.lapiazza_listing_id = res.get("listing_id")
    product.lapiazza_slug = res.get("slug")
    product.lapiazza_pushed_at = datetime.now(timezone.utc)
    if getattr(store, "lapiazza_business_id", None) != uid:
        store.lapiazza_business_id = uid
    await db.commit()
    logger.info("published product %s -> La Piazza listing %s (%s)", product.id, res.get("listing_id"), res.get("slug"))
    return res
