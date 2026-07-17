"""BL-132 — brands and their OFFICIAL sites. The metadata that makes a search land on the real pack.

Angel, working the sheet: "we know all of them have a brand name… if we can refine the search so it
gives the brand name first, that's where you get the real proper pictures, not so much gibberish. When
I go into images there's tons to pick from — I don't know which is from the official websites. So
that's maybe something we should put in our repository. The more metadata we have, the better long term."

Exactly right, and it does two jobs:
  1. BRAND-FIRST QUERIES — "GIZEH King Size Slim Extra Fine" beats "King Size Slim Extra Fine", which
     drags in every other brand's look-alike.
  2. SITE-SCOPED IMAGE SEARCH — `site:gizeh.com` means every result IS the official pack shot. The
     machine can surface hundreds; only the person holding the box can pick the right one — so hand
     them a shortlist that's already clean.

EVERY DOMAIN HERE WAS FETCH-VERIFIED (2026-07-17), not recalled. That mattered:
  • gizeh.de → redirects to gizeh.com (the real one)
  • wolkenkraft.net dead → wolkenkraft.de; satya.com dead → satyaincense.com; goloka.com → goloka.in
  • ocb.net looked dead but was BLOCKING our bot UA — a 403 is not a missing site
  • ocbpapers.com / golokaincense.com return HTTP 200 but are PARKED DOMAINS FOR SALE (HugeDomains).
    A 200 does not mean it's the brand's site — that's the trap this list exists to keep out.
  • elfbar.com redirects to instavape.shop (a reseller) and actitube.de to smart-smoking.de — omitted
    rather than point an operator at someone else's shop and call it official.
Unverified brands are simply ABSENT: they still get brand-first search, just no site scoping. An absent
brand costs a little noise; a WRONG official site costs a wrong picture, and that's the expensive one.

▶ NEXT ROUND (Angel, same conversation): "the supplier list could be populated with these sites too, or
a section for brand IDs with metadata we pre-program and config for our LOCAL MARKET." Correct — this
dict is code, and it should be DATA: a brand table (id, name, aliases, official_site, market, supplier
links) editable per market without a deploy, with suppliers carrying their own sites. This module is
the working proof; the table is the destination. Keep the function surface (detect_brand / official_site
/ search_query / image_query) so the swap is a storage change, not a rewrite.
"""
from __future__ import annotations

import re
from typing import Optional

# brand -> official domain (fetch-verified; see module docstring)
BRAND_SITES: dict[str, str] = {
    # --- papers, filters, rolling ---
    "RAW": "rawthentic.com",
    "OCB": "ocb.net",
    "GIZEH": "gizeh.com",
    "Elements": "elementspapers.com",
    "Smoking": "smokingpaper.com",
    "Purize": "purize-filters.com",
    "Rizla": "rizla.com",
    "Juicy Jay's": "juicyjays.com",
    "Greengo": "greengo.eco",
    "G-Rollz": "g-rollz.com",
    "Mascotte": "mascotte.com",
    # --- vaporizers / vape ---
    "Storz & Bickel": "storz-bickel.com",
    "DynaVap": "dynavap.com",
    "PAX": "pax.com",
    "Wolkenkraft": "wolkenkraft.de",
    "Lost Mary": "lostmary.com",
    "VOZOL": "vozol.com",
    "Innokin": "innokin.com",
    "Aspire": "aspirecig.com",
    "Wotofo": "wotofo.com",
    # --- lighters ---
    "Clipper": "clipper.com",
    "Zippo": "zippo.com",
    "BIC": "bic.com",
    # --- grow ---
    "BioBizz": "biobizz.com",
    "Plagron": "plagron.com",
    # --- incense ---
    "Goloka": "goloka.in",
    "Satya": "satyaincense.com",
    # --- tobacco ---
    "Backwoods": "backwoodscigars.com",
    "Swisher": "swisher.com",
    # --- misc / glass / scales ---
    "Boveda": "bovedainc.com",
    "My Weigh": "myweigh.com",
    "Black Leaf": "blackleaf.eu",
    # --- Swiss suppliers & houses (not brands, but the right place to look up their own lines) ---
    "Green Passion": "greenpassion.ch",
    "FourTwenty": "fourtwenty.ch",
    "Tamar": "tamar.ch",
}

# Brands we know by name but have NO verified official site for. Listed so brand-FIRST search still
# works (job 1) without pretending we know where their pictures live (job 2).
KNOWN_BRANDS_NO_SITE = [
    "RIPS", "GeekVape", "Kavatza", "Grace Glass", "Actitube", "Elf Bar", "ELFLIQ",
    "CTIP", "Medusa", "Hybrid", "OPRO", "Rockies", "Sasso", "Qualicann", "BLOW", "SWEED",
    "Local Weed", "Hanfmacher", "CBDeluxe", "Starbuds", "Kannabia", "Tycoon", "Amy", "Kaya",
    "Hellvape", "DOVPO", "InSmoke", "xTar", "Hohm", "SWAG", "UD", "Best Buds", "Breit",
]

_ALL_BRANDS = list(BRAND_SITES.keys()) + KNOWN_BRANDS_NO_SITE
# longest first: "Lost Mary" must win over a bare "Mary"; "Green Passion" over "Green"
_BRAND_PATTERNS = sorted(_ALL_BRANDS, key=len, reverse=True)


def detect_brand(name: str) -> Optional[str]:
    """The brand named in a product title, or None. Word-boundary matched so 'RAW' doesn't fire on
    'drawer' and 'PAX' doesn't fire on 'paxton'."""
    n = (name or "")
    if not n:
        return None
    for b in _BRAND_PATTERNS:
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(b)}(?![A-Za-z0-9])", n, re.I):
            return b
    return None


def official_site(brand: Optional[str]) -> Optional[str]:
    if not brand:
        return None
    return BRAND_SITES.get(brand)


def search_query(name: str) -> str:
    """Brand-first: the brand is the strongest disambiguator a head-shop product has. If the name
    already leads with it, leave it alone."""
    brand = detect_brand(name)
    n = (name or "").strip()
    if not brand or n.lower().startswith(brand.lower()):
        return n
    return f"{brand} {n}"


def image_query(name: str) -> str:
    """Brand-first AND scoped to the official site when we know it — so every image on that results
    page is the real pack, not a reseller's re-shoot or a look-alike."""
    q = search_query(name)
    site = official_site(detect_brand(name))
    return f"{q} site:{site}" if site else q
