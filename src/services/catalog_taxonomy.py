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
import html
import re

# --- CATEGORIES (merchandising skeleton — seeded, extensible) --------------------------------
CATEGORIES = [
    "CBD & Hemp", "Edibles", "Creams & Topicals", "Papers & Filters", "Grinders",
    "Lighters", "Pipes & Bongs", "Vaporizers", "E-Liquids", "Tobacco & Cigarettes",
    "Grow Supplies", "Café", "Merch", "Accessories", "Other",
]

# --- CATEGORY EMOJI (display only — never behaviour) -----------------------------------------
# One server-owned place so every category ALWAYS shows a consistent emoji, including ones a
# shop types on the fly. Resolution order:
#   1. an explicit override (the future Category-CRUD will store a chosen emoji → pass it here)
#   2. a curated emoji for a known category (skeleton + common aliases) — looks "right"
#   3. a STABLE deterministic pick from the pool (same name → same emoji, forever; never blank)
# When the Category table + emoji-picker build lands, only step 1 changes — callers/UI stay put.
CATEGORY_EMOJI = {
    # skeleton (CATEGORIES above)
    "CBD & Hemp": "🌿", "Edibles": "🍬", "Creams & Topicals": "🧴", "Papers & Filters": "📄",
    "Grinders": "⚙️", "Lighters": "🔥", "Pipes & Bongs": "🌀", "Vaporizers": "💨",
    "E-Liquids": "🧪", "Tobacco & Cigarettes": "🚬", "Grow Supplies": "🌱", "Café": "☕",
    "Merch": "👕", "Accessories": "🎒", "Other": "🏷️",
    # common aliases / demo-seed names so existing data also looks right
    "CBD": "🌿", "Hemp": "🌿", "Cafe": "☕", "Coffee": "☕", "Bar": "🍺", "Beer": "🍺",
    "Wine": "🍷", "Drinks": "🥤", "Beverages": "🥤", "Food": "🍴", "Bakery": "🥐",
    "Snacks": "🍫", "Equipment": "⚙️", "Tobacco": "🚬", "Papers": "📄", "Vape": "💨",
}

# A pool of distinct, retail-neutral emojis for categories with no curated entry. Deterministic
# indexing means a typed-on-the-fly category gets a stable, intentional-looking icon every time.
_EMOJI_POOL = [
    "🛍️", "📦", "🎁", "🏷️", "🧺", "🧴", "🧪", "⚗️", "🔮", "💎", "🪙", "🔑", "🧰", "🛠️",
    "🔧", "🔩", "🧲", "🔋", "💡", "🕯️", "🔦", "📐", "📎", "✂️", "🖊️", "📒", "📕", "📗",
    "📘", "📙", "🗂️", "📌", "🧷", "🎒", "👜", "👛", "🧳", "👕", "👖", "🧢", "🧤", "🧣",
    "👟", "🕶️", "⌚", "💍", "🌿", "🍃", "🌱", "🌵", "🌴", "🌷", "🌹", "🌻", "🍀", "🍄",
    "🌰", "🫘", "🌶️", "🫚", "🧄", "🧅", "🥕", "🌽", "🥔", "🍅", "🍆", "🥑", "🍇", "🍈",
    "🍉", "🍊", "🍋", "🍌", "🍍", "🥭", "🍎", "🍐", "🍑", "🍒", "🍓", "🫐", "🥝", "🥥",
    "🍫", "🍬", "🍭", "🍯", "🍪", "🥐", "🥨", "🥯", "🧀", "🍵", "☕", "🧃", "🥤", "🧉",
    "🍶", "🍷", "🍸", "🍹", "🍺", "🥃", "🧊", "🍴", "🥢", "🧫", "🔬", "🧯", "🪔", "🎨",
    "🖌️", "🪕", "🎲", "🧩", "🎯", "🪀", "🪁", "🎏", "🎐", "🪴",
]


def category_emoji(category, override=None):
    """Display emoji for a category name. Never returns blank; stable for a given name.
    `override` (future Category-CRUD) wins so a shop can curate its own icon later."""
    if override:
        return override
    if not category:
        return "🏷️"
    name = str(category).strip()
    if name in CATEGORY_EMOJI:
        return CATEGORY_EMOJI[name]
    h = 0
    for ch in name:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return _EMOJI_POOL[h % len(_EMOJI_POOL)]


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
    # Neutral 18+ bucket for on-the-fly quick-adds: the cashier's "18+?" toggle needs a class that
    # ACTUALLY drives the checkout age gate (which reads product_class, not the is_age_restricted
    # column) without wrongly restricting discounts (tobacco/alcohol) or triggering a THC report
    # (cbd_hemp). A manager can re-class it precisely later in the cleanup cockpit.
    "age_restricted":   {"label": "Age-restricted 18+",  "age_restricted": True,  "vat": "standard",   "compliance": None,         "promo_restricted": False},
    "tobacco_nicotine": {"label": "Tobacco / Nicotine",  "age_restricted": True,  "vat": "standard",   "compliance": None,         "promo_restricted": True},
    "alcohol":          {"label": "Alcohol",             "age_restricted": True,  "vat": "standard",   "compliance": None,         "promo_restricted": True},
    "cbd_hemp":         {"label": "CBD / Hemp — 18+ (flower·hash·vape·edibles)", "age_restricted": True,  "vat": "standard",   "compliance": "thc_report", "promo_restricted": False},
    "cbd_open":         {"label": "CBD / Hemp — open (oils·seeds·cosmetics)",     "age_restricted": False, "vat": "standard",   "compliance": "thc_report", "promo_restricted": False},
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


def reconcile_age(product_class: str | None, is_age_restricted: bool | None) -> tuple[str, bool]:
    """Keep product_class (the source of truth) and the is_age_restricted flag consistent.

    The checkout age gate reads product_class, NOT the boolean column — so a bare "18+" toggle
    must land on a class that actually gates. If the caller flipped 18+ on an otherwise unclassed
    item (the on-the-fly quick-add, the cleanup cockpit), file it under the neutral "age_restricted"
    class; a manager can re-class it precisely (tobacco/cbd/…) later. Then always DERIVE the flag
    from the (possibly updated) class so the two can never drift.

    The toggle is BIDIRECTIONAL for the NEUTRAL bucket: flipping 18+ OFF on an "age_restricted"
    item demotes it back to standard (field 2026-07-08: editing 18+ off "saved" but stayed 18+,
    because the flag was re-derived from the unchanged class). It never un-gates a REAL substance
    class (tobacco/alcohol/cbd_hemp) via the toggle — those stay gated; reclass them explicitly.
    Returns (class, flag)."""
    cls = product_class or DEFAULT_CLASS
    if is_age_restricted and not class_is_age_restricted(cls):
        cls = "age_restricted"            # toggle ON a plain item → the neutral 18+ bucket
    elif is_age_restricted is False and cls == "age_restricted":
        cls = DEFAULT_CLASS               # toggle OFF the NEUTRAL bucket → standard (the fix)
    return cls, class_is_age_restricted(cls)


# --- CLASSIFIER: (title + FourTwenty category) -> (our_category, our_class, age_restricted) ---

# Negative guard so "tobacco-free" / "nikotinfrei" / "0mg" / herbal substitute never trip 18+.
# NOTE the \b0\s*mg\b boundary: without it, "20mg" (a NICOTINE e-cig) contains "0mg" and would be
# falsely cleared. "tabakersatz"/"kräutermischung" = herbal tobacco-substitute (no nicotine) = open.
_AGE_NEG = re.compile(r"tabakfrei|tobacco.?free|nikotinfrei|nicotine.?free|ohne\s+nikotin|\bno\s*nic\b|\b0\s*mg\b|null\s*nikotin|alkoholfrei|alcohol.?free|kräuter.?mischung|\bherbal\b|tabakersatz", re.I)
_TOBACCO = re.compile(r"tabak|tabacc|tobacco|zigar|sigaret|cigaret|nikotin|nicotin|\bsnus\b|nikotinbeutel|nicotine\s*pouch", re.I)
# Branded cigarettes + pack tokens the plain-tobacco regex misses. FourTwenty ships real cigarette
# packs titled "Marlboro Gold 10x20cig" / "Parisienne Jaune 8x25cig" — no "tabak"/"zigarette" in the
# title at all, so they leaked through as un-gated "standard" goods. Catch the brands + the NNxNNcig
# pack pattern + MYO/RYO loose-tobacco + HEETS/IQOS.
_CIG = re.compile(r"\bmarlboro\b|\bparisienne\b|\bcamel\b|\bwinston\b|gauloises|lucky\s*strike|\bchesterfield\b|american\s*spirit|\bpueblo\b|\bphilip\s*morris\b|\d+\s*x?\s*\d*\s*cig\b|\bcig\b|\bmyo\b|\bryo\b|\bheets\b|\biqos\b", re.I)
# Cigars / cigarillos / blunt wraps — tobacco products the cigarette rules miss (field 2026-07-08:
# "Swisher Sweets" + "Smock Woods … Cigars" leaked as un-gated 'standard'). Brands (Swisher,
# Backwoods) + generic cigar/cigarillo terms + "blunt wrap" (a tobacco-leaf wrap). "blunt wrap" is
# narrow on purpose so plain rolling "papers" stay open. Blunt wraps are gated CONSERVATIVELY —
# over-gating a tobacco wrap is the safe error; Felix/Treuhänder can confirm the CH line. 0mg/herbal
# still veto via _AGE_NEG.
_CIGAR = re.compile(r"\bswisher\b|backwoods|cigarillo|zigarillo|\bcigars?\b|\bzigarre\b|\bzigarren\b|stumpen|\bcheroot\b|black\s*&?\s*mild|smock\s*woods|blunt\s*wraps?", re.I)
_ALCOHOL = re.compile(r"alkohol|alcohol|vodka|\brum\b|whisky|whiskey|\bgin\b|liqueur|likör|absinth|\bbier\b|\bwein\b", re.I)
# Shisha bucket is MIXED: molasses tobacco (18+) sits beside hoses/charcoal/foil/adapters (open).
# These markers make a shisha line the actual 18+ substance — the brands are ALWAYS molasses
# tobacco, so they gate off the title alone even when the supplier category is a generic dump.
_SHISHA_TOBACCO = re.compile(r"shisha\s*tabak|shishatabak|\btabak\b|molasse|al\s*fakher|\badalya\b|\bnakhla\b|serbetli|\bstarbuzz\b|\bfumari\b", re.I)
# Nicotine e-cigarettes: a vape context + a NON-ZERO nicotine strength ("20mg"). The (?!0) keeps
# "0mg" / nicotine-free out; the mg is 1–2 digits so CBD's 100/500/1000mg never trips it. Vape
# context (device words or the vape category) scopes it so a "CBD 20mg" edible isn't caught.
_ECIG_CONTEXT = re.compile(r"disposable|\bpod\b|\bvape\b|e-?zigar|\bpuff\b|elf\s*bar|elfbar|\bvozol\b|\bhoke\b|lost\s*mary|maryliq|geek\s*bar|\belux\b|\bwaka\b|\baisu\b|nic\s*salt|\bnicsalt\b|vaporiz|e-?liquid|\bliquids?\b|\b\d{1,3}\s*ml\b", re.I)
_NIC_MG = re.compile(r"\b(?!0\b)\d{1,2}\s*mg\b", re.I)
# Disposable-vape brands: their consumables (refill / prefilled pod / nachfüllbehälter) are nicotine
# by default — Artemis names them "…Refill Blueberry Ice" / "…Nachfüllbehälter …20mg" (no "disposable"
# word), which the FourTwenty-tuned rules missed. A "refill" ONLY counts as nicotine next to one of
# these brands, so a lighter's "gas refill" is never caught. 0mg / OHNE NIKOTIN still veto (via _AGE_NEG).
_VAPE_BRAND = re.compile(r"elf\s*bar|elfbar|lost\s*mary|maryliq|\bvozol\b|geek\s*bar|\belux\b|\bwaka\b|\bhoke\b|\baisu\b", re.I)
_VAPE_REFILL = re.compile(r"\brefill\b|nachf(?:ü|ue)ll", re.I)
# The FORM carries nicotine by default: a "disposable" or a "prefilled pod" ships with e-liquid,
# and in CH/EU that's nicotine unless the title explicitly says "No Nic" / "0mg" (caught by _AGE_NEG).
# This catches the pods/disposables that carry no "NNmg" token in the title at all. Empty hardware
# (refillable / replacement / bare "…Ohm" pods, kits with no liquid) has neither word → stays open.
_ECIG_FORM = re.compile(r"\bdisposable\b|prefilled\s*pod", re.I)
# Inside the tobacco/cigarette category group, these titles are ACCESSORIES/herbal, not the substance
# (filling machines, filter tubes, papers). They must NOT inherit the group's 18+ flag.
_TOBACCO_ACCESSORY = re.compile(r"filling|filter|stopf|maschine|machine|hülse|\btube\b|papier|\bpaper|\btips?\b|\bkulu\b", re.I)
# Looks like tobacco/alcohol but is an ACCESSORY (a bag / holder / case), not the 18+ substance —
# so it never gets the age gate. (Kavatza Tabaktasche, Zigarettenhalter, Tabakbefeuchter…)
_SUBSTANCE_ACCESSORY = re.compile(r"tasche|portemonnaie|portmonnaie|halter|befeuchter|\betui\b|humidor|aufbewahr|löffel|\bspoon\b", re.I)
# Rum / whisky etc. as a FLAVOUR on papers/wraps/blunts — not alcohol. (Juicy Jay's Rum papers…)
_FLAVOUR_PAPER = re.compile(r"paper|\bwrap|blunt|blättchen|\bcone|juicy\s*jay", re.I)
# CBD in a NON-smokable, non-recreational form (oil / tincture / drops / seeds / cosmetics) — NOT
# age-gated (Angel: "the oils are not"). Everything else CBD (flower, hash, vape, edibles) stays 18+.
# Conservative on purpose: only CLEAR open forms land here, because this is the one no-ID class.
_CBD_OPEN = re.compile(r"\böl\b|\boil\b|\boel\b|tinktur|tincture|\bdrops?\b|tropfen|\bseed\b|\bseeds\b|\bsamen\b|kosmetik|cosmetic|creme|cream|salbe|\bbalm\b|lotion|serum", re.I)

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


def _reftags(raw, ref_category) -> str:
    """The supplier's OWN taxonomy, html-unescaped + lowercased into one searchable string.

    The title alone can't tell a Marlboro pack from a lighter, but FourTwenty files it under
    "Tabak, ... Zigaretten"; a CBD flower under "CBD Blüten"; a nicotine e-cig under "Disposable
    Einweg E-Zigaretten". The importer stows every feed column in `raw`, so we read the structured
    category groups straight from there — the strong, non-guessy signal. Empty for feeds without
    these columns, in which case classify() just leans on the title (unchanged behaviour)."""
    parts = []
    if isinstance(raw, dict):
        parts = [raw.get(k) for k in
                 ("categorygroup_1", "categorygroup_2", "categorygroup_3", "productcategory")]
    if ref_category:
        parts.append(ref_category)
    return html.unescape(" | ".join(p for p in parts if p)).lower()


def classify(title: str | None, ref_category: str | None = None, raw=None) -> tuple[str, str, bool]:
    """Map a reference item to (our_category, our_class, age_restricted). Pure + deterministic.

    CLASS is decided in three layers, most-certain first: (1) the TITLE says it outright (real
    tobacco / cigarette brand / alcohol); (2) the SUPPLIER CATEGORY says it (the reliable signal
    the title hides — nicotine e-cigs, shisha tobacco, CBD flower/pollen); (3) a TITLE-CBD
    fallback. The negative guards (0mg / nikotinfrei / herbal / tabakersatz) and the
    accessory guards veto at every layer, so a filling machine or a 0mg pod never gets gated."""
    t = title or ""
    tags = _reftags(raw, ref_category)
    neg = _AGE_NEG.search(t)

    # CLASS first (it drives the age flag).
    cls = DEFAULT_CLASS
    is_cbd = bool(re.search(r"cbd|cannabidiol", t, re.I))
    # (1) TITLE is decisive: named tobacco/cigarette, shisha molasses, or a nicotine e-cig — unless
    #     it's an accessory/herbal. Shisha brands + the mg-in-vape signal gate off the title alone,
    #     so they hold up even when the supplier category is a coarse dump ("Accessories"/"Vaporizers").
    if (_TOBACCO.search(t) or _CIG.search(t) or _CIGAR.search(t) or _SHISHA_TOBACCO.search(t)) and not neg and not _SUBSTANCE_ACCESSORY.search(t):
        cls = "tobacco_nicotine"
    elif (_NIC_MG.search(t) or _ECIG_FORM.search(t)
          or (_VAPE_BRAND.search(t) and _VAPE_REFILL.search(t))) \
            and not is_cbd and not neg and not _SUBSTANCE_ACCESSORY.search(t):
        # A non-CBD NNmg nicotine strength gates ON ITS OWN — no ecig-context word required.
        # (field 2026-07-09: "VAAL E-Pack 20mg" / "Instaflow O Pro Starterkit … 20mg" had no
        # disposable/pod/vape token → leaked as un-gated standard.) CBD (100/500/1000mg = 3-digit,
        # excluded by _NIC_MG's 1-2 digit cap + the is_cbd guard) and 0mg / no-nic still veto.
        cls = "tobacco_nicotine"                   # nicotine strength, a liquid-bearing form, or a brand refill
    elif _ALCOHOL.search(t) and not neg and not _SUBSTANCE_ACCESSORY.search(t) and not _FLAVOUR_PAPER.search(t):
        cls = "alcohol"
    # (2) SUPPLIER CATEGORY closes the leaks the title can't see. A tobacco GROUP still can't
    #     override the accessory guards: a pouch/holder/case (_SUBSTANCE_ACCESSORY) or a
    #     machine/filter/paper (_TOBACCO_ACCESSORY) stays open even under "Tabak…Zigaretten".
    elif tags:
        tobacco_ok = not neg and not _SUBSTANCE_ACCESSORY.search(t) and not _TOBACCO_ACCESSORY.search(t)
        if ("cbd blüten" in tags or "cbd pollen" in tags or "blüten" in tags) and not _CBD_OPEN.search(t):
            cls = "cbd_hemp"                       # flower / trim / pollen (hash) = 18+
        elif "cbd samen" in tags:
            cls = "cbd_open"                       # seeds = open (no ID)
        elif "disposable" in tags and "zigaret" in tags and tobacco_ok:
            cls = "tobacco_nicotine"               # nicotine disposables (0mg vetoed above)
        elif ("zigaretten" in tags or "tabak," in tags or tags.startswith("tabak")) and tobacco_ok:
            cls = "tobacco_nicotine"               # the tobacco/cigarette group, minus machines/filters
        elif "shisha" in tags and _SHISHA_TOBACCO.search(t) and tobacco_ok:
            cls = "tobacco_nicotine"               # shisha molasses tobacco only (not hoses/charcoal)
        elif ref_category == "CBD" or re.search(r"cbd|cannabidiol", t, re.I):
            cls = "cbd_open" if _CBD_OPEN.search(t) else "cbd_hemp"
    # (3) TITLE-CBD fallback (no supplier tags).
    elif re.search(r"cbd|cannabidiol", t, re.I):
        cls = "cbd_open" if _CBD_OPEN.search(t) else "cbd_hemp"

    # CATEGORY: honour FourTwenty's clean buckets, else keyword-classify the dump.
    cat = _REF_CATEGORY_MAP.get(ref_category or "")
    if cat is None:
        for rx, c in _CATEGORY_RULES:
            if rx.search(t):
                cat = c
                break
    if cat is None:
        cat = "Accessories" if ref_category == "Accessories" else "Other"

    # A real cigarette/tobacco product belongs in its own category, not "Papers"/"Other".
    # Any tobacco_nicotine line qualifies now (branded packs like "Marlboro 10x20cig", disposable
    # nicotine e-cigs, and shisha tobacco all lack a "tabak"/"zigarette" token in the title).
    if cls == "tobacco_nicotine":
        cat = "Tobacco & Cigarettes"

    return cat, cls, class_meta(cls)["age_restricted"]


def resolve_class_on_create(name: str | None, product_class: str | None,
                            is_age_restricted: bool | None) -> tuple[str, bool]:
    """The on-the-fly / quick-create rule (compliance safety net).

    Honour the operator's explicit choice first (a picked class or the 18+ toggle, via
    reconcile_age). THEN, if the item is still plain 'standard', run the title classifier —
    and if the NAME is an age-restricted substance (tobacco/nicotine, alcohol, CBD flower),
    upgrade to that class so it can NEVER be sold un-gated (field 2026-07-08: a cashier who
    forgot the 18+ toggle on "Swisher Sweets" was ringing it with no ID gate). The net only
    ever makes an item MORE restrictive — it never un-gates an operator's choice. A manager
    can re-class precisely later in the cleanup cockpit. Returns (class, flag)."""
    cls, flag = reconcile_age(product_class, is_age_restricted)
    if cls == DEFAULT_CLASS:
        _, suggested, _ = classify(name or "")
        if suggested in ("tobacco_nicotine", "alcohol", "cbd_hemp"):
            return suggested, True
    return cls, flag
