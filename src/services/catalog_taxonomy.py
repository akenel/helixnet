"""Catalog taxonomy — the single source of truth for product CATEGORY and CLASS.

Two axes, two jobs (BL-96):
  * CATEGORY = merchandising. What the thing IS — for the wall + reports. A seeded skeleton
    that can grow freely (taste).
  * CLASS = behaviour. How the till TREATS it — age gate, VAT, compliance. A CONTROLLED set,
    because it drives money + law (a cashier can't invent a tax class).

`is_age_restricted` on a product is DERIVED from its class (set on save) so it can never drift
out of sync — but stays overridable via CRUD for an oddball.

This module also holds the rules-based classifier that maps the 7,272 FourTwenty reference items
onto the skeleton. It is re-runnable (scripts/reclassify_reference.py) — refine the rules here,
re-run, done.
"""
import re

# --- CATEGORIES (merchandising skeleton — seeded, extensible) --------------------------------
CATEGORIES = [
    "CBD & Hemp", "Edibles", "Creams & Topicals", "Papers & Filters", "Grinders",
    "Lighters", "Pipes & Bongs", "Vaporizers", "E-Liquids", "Tobacco & Cigarettes",
    "Grow Supplies", "Café", "Merch", "Accessories", "Other",
]

# --- CLASSES (behaviour — controlled; each drives age / VAT / compliance) ---------------------
# vat: "standard" = 8.1% · "reduced" = 2.6% · "cafe_split" = dine-in 8.1% / takeaway 2.6% (asked at sale)
# promo_restricted: True = promotional discounts + loyalty-credit redemption are restricted.
#   * Tobacco / Nicotine — sales-promotion restrictions (Tabakproduktegesetz + cantonal rules).
#   * Alcohol — no below-cost / loss-leader / giveaway promos (Alkoholgesetz).
#   CBD / Hemp / standard / café are NOT promo-regulated — discount freely.
#   (Flag only — enforcement (warn-on-discount + block credit redemption) lands in Phase F.
#    Exact scope still needs Felix's Treuhänder/lawyer sign-off.)
PRODUCT_CLASSES = {
    "standard":         {"label": "Standard goods",      "age_restricted": False, "vat": "standard",   "compliance": None,         "promo_restricted": False},
    "tobacco_nicotine": {"label": "Tobacco / Nicotine",  "age_restricted": True,  "vat": "standard",   "compliance": None,         "promo_restricted": True},
    "alcohol":          {"label": "Alcohol",             "age_restricted": True,  "vat": "standard",   "compliance": None,         "promo_restricted": True},
    "cbd_hemp":         {"label": "CBD / Hemp",          "age_restricted": True,  "vat": "standard",   "compliance": "thc_report", "promo_restricted": False},
    "cafe_food":        {"label": "Café food & drink",   "age_restricted": False, "vat": "cafe_split", "compliance": None,         "promo_restricted": False},
}
DEFAULT_CLASS = "standard"


def class_meta(cls: str | None) -> dict:
    return PRODUCT_CLASSES.get(cls or DEFAULT_CLASS, PRODUCT_CLASSES[DEFAULT_CLASS])


def class_is_age_restricted(cls: str | None) -> bool:
    """Single rule: a product is 18+ iff its class says so (the till + receiving read this)."""
    return class_meta(cls)["age_restricted"]


def class_promo_restricted(cls: str | None) -> bool:
    """True iff promotional discounts / loyalty-credit redemption are restricted (tobacco, alcohol)."""
    return class_meta(cls).get("promo_restricted", False)


# --- CLASSIFIER: (title + FourTwenty category) -> (our_category, our_class, age_restricted) ---

# Negative guard so "tobacco-free" / "nikotinfrei" / "0mg" never trip the 18+ flag.
_AGE_NEG = re.compile(r"tabakfrei|tobacco.?free|nikotinfrei|nicotine.?free|ohne\s+nikotin|0\s*mg|alkoholfrei|alcohol.?free|kräuter.?mischung|herbal", re.I)
_TOBACCO = re.compile(r"tabak|tobacco|zigar|cigaret|nikotin|nicotin\b|\bsnus\b", re.I)
_ALCOHOL = re.compile(r"alkohol|alcohol|vodka|\brum\b|whisky|whiskey|\bgin\b|liqueur|likör|absinth|\bbier\b|\bwein\b", re.I)
# Looks like tobacco/alcohol but is an ACCESSORY (a bag / holder / case), not the 18+ substance —
# so it never gets the age gate. (Kavatza Tabaktasche, Zigarettenhalter, Tabakbefeuchter…)
_SUBSTANCE_ACCESSORY = re.compile(r"tasche|portemonnaie|portmonnaie|halter|befeuchter|\betui\b|humidor|aufbewahr", re.I)
# Rum / whisky etc. as a FLAVOUR on papers/wraps/blunts — not alcohol. (Juicy Jay's Rum papers…)
_FLAVOUR_PAPER = re.compile(r"paper|\bwrap|blunt|blättchen|\bcone|juicy\s*jay", re.I)

# Ordered keyword -> category; first match wins. CBD checked before creams so "CBD oil" lands in CBD.
_CATEGORY_RULES = [
    (re.compile(r"grinder|mühle|mill\b", re.I),                                   "Grinders"),
    (re.compile(r"clipper|feuerzeug|lighter|sturmfeuer|\bbic\b|jet\s?flame", re.I), "Lighters"),
    (re.compile(r"bong|beaker|glaskopf|\bglas\b|pfeife|\bpipe|bubbler|chillum|\bdab|nektar|recycler", re.I), "Pipes & Bongs"),
    (re.compile(r"vapo|vaporiz|crafty|mighty|\bpax\b|dynavap|volcano", re.I),     "Vaporizers"),
    (re.compile(r"e-?liquid|\bliquid\b|\bbase\b|aroma|shake.?&.?vape", re.I),     "E-Liquids"),
    (re.compile(r"paper|blättchen|king\s?size|\bfilter|\btips?\b|\bcone|roach|rolling|drehmaschine|rolls?\b", re.I), "Papers & Filters"),
    (re.compile(r"cbd|cannabidiol|\bhanf|\bhemp", re.I),                          "CBD & Hemp"),
    (re.compile(r"creme|cream|salbe|\bbalm|lotion|topical|massage", re.I),        "Creams & Topicals"),
    (re.compile(r"edible|gummi|schoko|chocolate|cookie|keks|\btee\b|\btea\b|honig|honey|lutsch|sirup", re.I), "Edibles"),
    (re.compile(r"\bgrow|dünger|substrat|\berde\b|\bseed|\bsamen|\bzelt|grow.?lamp|nährstoff", re.I), "Grow Supplies"),
    (re.compile(r"shirt|hoodie|\bcap\b|mütze|sticker|poster|patch|\bpin\b", re.I),     "Merch"),
    (re.compile(r"tray|ashtray|aschenbecher|storage|\bbox\b|\betui|stash|waage|scale|brush|reinig|tasche|portemonnaie|\bhalter\b|befeuchter|humidor", re.I), "Accessories"),
]

# FourTwenty's own clean buckets we trust as-is (only "Accessories"/"Themed"/"Promotions" are the dump).
_REF_CATEGORY_MAP = {
    "CBD": "CBD & Hemp",
    "Vaporizers": "Vaporizers",
    "E-Liquids": "E-Liquids",
}


def classify(title: str | None, ref_category: str | None = None, raw=None) -> tuple[str, str, bool]:
    """Map a reference item to (our_category, our_class, age_restricted). Pure + deterministic."""
    t = title or ""

    # CLASS first (it drives the age flag).
    cls = DEFAULT_CLASS
    if _TOBACCO.search(t) and not _AGE_NEG.search(t) and not _SUBSTANCE_ACCESSORY.search(t):
        cls = "tobacco_nicotine"
    elif _ALCOHOL.search(t) and not _AGE_NEG.search(t) and not _SUBSTANCE_ACCESSORY.search(t) and not _FLAVOUR_PAPER.search(t):
        cls = "alcohol"
    elif ref_category == "CBD" or re.search(r"cbd|cannabidiol", t, re.I):
        cls = "cbd_hemp"

    # CATEGORY: honour FourTwenty's clean buckets, else keyword-classify the dump.
    cat = _REF_CATEGORY_MAP.get(ref_category or "")
    if cat is None:
        for rx, c in _CATEGORY_RULES:
            if rx.search(t):
                cat = c
                break
    if cat is None:
        cat = "Accessories" if ref_category == "Accessories" else "Other"

    # A real cigarette/tobacco product belongs in its own category, not "Papers".
    if cls == "tobacco_nicotine" and re.search(r"zigar|cigaret|tabak\b|tobacco|\bsnus\b", t, re.I):
        cat = "Tobacco & Cigarettes"

    return cat, cls, class_meta(cls)["age_restricted"]
