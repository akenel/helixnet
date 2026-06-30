"""Banco catalog ENRICHMENT recipe — the 90% that has value.

Turns a *normalized raw product record* (from any feeder: Artemis first, FourTwenty
next) into the enrichment record described in docs/BANCO-ARTEMIS-ENRICHMENT-RECIPE.md §3.

THE TWO AXES (the most important rule — §2):
  * COMPLIANCE  (behavior_class, age_restricted, age_reason) = money + LAW.
        RULES decide. The LLM never sets a legal flag. Deterministic + auditable:
        every age flag carries the rule that set it (`age_reason`).
  * MERCHANDISING (category, tags, description) = how it's found + shown.
        LLM + a mapping table, bounded by a STRICT schema. A wrong category is a
        fixable UX annoyance, never illegal.

This module is the recipe as procedure-as-code (§7). Deterministic steps are pure +
idempotent; the LLM step (`llm_enrich_batch`) is schema-bounded and only touches the
merchandising axis. The raw source + full artemis_path are kept LOSSLESS so any later
decision (build the categories table, re-map, re-translate) re-derives from source.

Source-agnostic by design: the input is `RawProduct`; importers normalize, the recipe
enriches. The ONE place an LLM call happens is src/llm/run_llm (BYO-brain).

No DB writes happen here. The sample runner (scripts/import/artemis_enrich_sample.py)
drives this for a dry-run review.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Optional

# Banco's live two-axis rules (catalog_taxonomy.classify drives the LAW axis).
from src.services.catalog_taxonomy import classify

# --------------------------------------------------------------------------- #
# Recipe identity                                                             #
# --------------------------------------------------------------------------- #
RECIPE_VERSION = "1.0"

# SKU namespace. Each SOURCE gets its OWN 3-char prefix so feeds never collide
# with each other or with demo SKUs. Artemis runs on the **Tamar** retail platform
# → "TAM". We deliberately do NOT use "ART" (too easily read as "article"/"art.").
#   Future feeders pick their own 3-char prefix, e.g. FourTwenty → "FTW".
SOURCE_PREFIX = "TAM"


def make_sku(identifier: str | int, prefix: str = SOURCE_PREFIX) -> str:
    """Namespaced SKU, e.g. 'TAM-21577'."""
    return f"{prefix}-{str(identifier).strip()}"


# --------------------------------------------------------------------------- #
# §6b Minted internal EAN-13.  Artemis carries NO manufacturer barcode, so we   #
# mint our own private, scannable code per product (BL-97 extended to the whole #
# catalog). We use the GS1 "restricted distribution / in-store" prefix range    #
# 20–29 — codes that are reserved for internal use and never collide with a     #
# real retail EAN. The code is DETERMINISTIC from a stable integer seed (the    #
# Artemis numeric id for imports; a DB max+1 for hand-added products) so a       #
# re-run mints the SAME code and never double-assigns.                          #
# --------------------------------------------------------------------------- #
INTERNAL_EAN_PREFIX = "20"   # GS1 internal/restricted-distribution range (20–29)


def ean13_check_digit(twelve: str) -> int:
    """Standard EAN-13 check digit for a 12-digit payload (odd*1 + even*3 from left)."""
    s = sum((1 if i % 2 == 0 else 3) * int(d) for i, d in enumerate(twelve))
    return (10 - (s % 10)) % 10


def mint_internal_ean13(seed: int | str, prefix: str = INTERNAL_EAN_PREFIX) -> str:
    """Mint a scannable internal EAN-13 from a stable integer seed.

    Layout: <prefix (2)> + <seed zero-padded to 10 digits> + <check digit> = 13.
    The seed is the source numeric id (unique per product) so the code is stable
    and unique. Seeds wider than 10 digits are reduced mod 10**10 (defensive)."""
    try:
        n = int(str(seed).strip())
    except (TypeError, ValueError):
        # non-numeric source id -> derive a stable 10-digit seed from its hash
        import hashlib
        n = int(hashlib.sha256(str(seed).encode()).hexdigest(), 16)
    payload = f"{prefix}{n % (10 ** 10):010d}"   # 12 digits
    return payload + str(ean13_check_digit(payload))


# --------------------------------------------------------------------------- #
# §5 Compliance policy (DRAFT — pending Treuhänder / Felix sign-off)          #
# Per Artemis group: a DEFAULT age gate + the expected behaviour class.        #
# Rules run first; this table can only FORCE THE AGE GATE *UP*, never down,    #
# and flags a class that looks looser than the group expects for human review. #
# --------------------------------------------------------------------------- #
GROUP_POLICY: dict[str, dict] = {
    "Headshop":    {"age": True,  "age_reason": "headshop-smoking-paraphernalia", "expect_class": "standard"},
    "Papers & Co": {"age": True,  "age_reason": "papers-co-smoking-accessory",    "expect_class": "standard"},
    "Shisha":      {"age": True,  "age_reason": "shisha-tobacco-context",         "expect_class": "tobacco_nicotine"},
    "Vape & Co":   {"age": True,  "age_reason": "vape-nicotine-context",          "expect_class": "tobacco_nicotine"},
    "CBD":         {"age": True,  "age_reason": "cbd-18plus-default",             "expect_class": "cbd_hemp"},
    "Lifestyle":   {"age": False, "age_reason": "lifestyle-no-default-gate",      "expect_class": "standard"},
    "Grow":        {"age": False, "age_reason": "grow-equipment-no-default-gate", "expect_class": "standard"},
}

# Artemis group slug -> classify() ref_category hint (so CBD items split open/18+ correctly).
_GROUP_CLASS_HINT = {"cbd": "CBD"}


# --------------------------------------------------------------------------- #
# §4 Clean level-2 consolidation (we do NOT inherit Artemis's 4-level mess).   #
# Maps an Artemis lvl2 slug to a tidy, shopper-friendly Banco category.        #
# Keyed on substrings so DE/EN variants both land. Anything unmatched ->       #
# llm_needed=True (the LLM picks from the group's allowed set) or "Unsorted".  #
# --------------------------------------------------------------------------- #
_CONSOLIDATE_PAPERS = [
    (re.compile(r"\bblunts?\b|\bwraps?\b|fronto|backwood", re.I),                            "Blunts & Wraps"),
    # Cigarette tubes ("Zigaretten Hülsen/Huelsen") — empty filter tubes you stuff. A
    # distinct Papers sub-slug that previously fell through to needs_review.
    (re.compile(r"h[uü]lsen|huelsen|cigarette.?tube|zigaretten.?h", re.I),                   "Cigarette Tubes"),
    # Pre-rolled joint packs ("Jointpack") — ready-rolled, sold by the pack. Kept apart
    # from empty Cones; this slug also used to hit needs_review.
    (re.compile(r"jointpack|joint.?pack|pre.?rolled?.?joint", re.I),                         "Pre-rolled"),
    (re.compile(r"\bcones?\b|fertighül|pre.?roll",                 re.I),                    "Cones"),
    (re.compile(r"drehpap|rolling.?paper|\bpapers?\b|bl[aä]ttchen|king.?size|\brolls?\b", re.I), "Rolling Papers"),
    (re.compile(r"\bfilter|\btips?\b|\broach", re.I),                                        "Filters & Tips"),
    (re.compile(r"drehmaschin|rolling.?machine|\broller\b|stopf",  re.I),                    "Rolling Machines"),
    (re.compile(r"feuerzeug|lighter|clipper|sturmfeuer",           re.I),                    "Lighters"),
    (re.compile(r"etui|aufbewahr|\bbox\b|\bcase\b|dose|tabaktasche|portemonnaie", re.I),     "Storage"),
    (re.compile(r"zubeh|accessor|\bmisc",                          re.I),                    "Accessories"),
]
# The allowed clean categories the LLM may choose from for an ambiguous Papers & Co item.
_ALLOWED_PAPERS = ["Rolling Papers", "Filters & Tips", "Rolling Machines", "Cones",
                   "Pre-rolled", "Cigarette Tubes", "Blunts & Wraps", "Lighters",
                   "Storage", "Accessories"]

# Per-group consolidation table + allowed set. (Papers & Co is built out for the
# sample; other groups fall through to title-cased lvl2 + LLM assist — extend here.)
_GROUP_CONSOLIDATION = {
    "Papers & Co": (_CONSOLIDATE_PAPERS, _ALLOWED_PAPERS),
}


# --------------------------------------------------------------------------- #
# Step 1 — parse_price (RULE).  "CHF 1.90" / "CHF 39.-" / "CHF 1'234.50"       #
# (Same Swiss-format logic as the importer; kept here so the recipe owns it.)  #
# --------------------------------------------------------------------------- #
def parse_price(text: Optional[str]) -> Optional[Decimal]:
    s = (text or "").replace("CHF", "").strip()
    s = s.replace("’", "").replace("'", "")          # Swiss thousands apostrophe
    s = s.replace("–", "-").replace("—", "-").strip()  # en/em dash -> hyphen
    if s.endswith(".-"):
        s = s[:-2] + ".00"
    elif s.endswith("-"):
        s = s[:-1]
    s = s.replace(",", ".").strip().rstrip(".")
    if not s:
        return None
    try:
        d = Decimal(s).quantize(Decimal("0.01"))
        return d if d >= 0 else None
    except (InvalidOperation, ValueError):
        return None


# --------------------------------------------------------------------------- #
# Step 4 — mine_tags (RULE).  brand / material / size from name + path + facets #
# --------------------------------------------------------------------------- #
# Known brands in the rolling-paper / headshop world. Matched case-insensitively
# as whole words; the canonical casing is emitted in the tag.
_BRANDS = [
    "RAW", "OCB", "Smoking", "Rizla", "Clipper", "Juicy Jay", "Juicy Jays", "Elements",
    "Zig-Zag", "Zig Zag", "Gizeh", "Mascotte", "Bob Marley", "Purize", "Actitube",
    "Kavatza", "Pay-Pay", "Greengo", "Jware", "Blazy", "Snail", "Bull Brand", "Hornet",
    "King Palm", "Cones", "Swan", "Moon", "Cyclones", "Vibes", "DOMO", "Brotherhood",
    "The Bulldog", "Camel", "Marlboro", "Lion Rolling Circus",
]
_BRAND_RX = [(b, re.compile(r"(?<![\w])" + re.escape(b) + r"(?![\w])", re.I)) for b in _BRANDS]

_MATERIAL_RX = [
    ("hemp",       re.compile(r"\bhemp\b|\bhanf", re.I)),
    ("rice",       re.compile(r"\brice\b|\breis\b", re.I)),
    ("cellulose",  re.compile(r"cellulos|zellulose|transparent|clear", re.I)),
    ("flax",       re.compile(r"\bflax\b|\blein\b", re.I)),
    ("bamboo",     re.compile(r"bamboo|bambus", re.I)),
    ("wood-pulp",  re.compile(r"wood.?pulp|holz", re.I)),
    ("unbleached", re.compile(r"unbleach|ungebleicht|brown|natur(al)?", re.I)),
    ("organic",    re.compile(r"\borganic\b|\bbio\b", re.I)),
    ("activated-carbon", re.compile(r"aktivkohle|activated.?carbon|charcoal", re.I)),
    ("ceramic",    re.compile(r"ceramic|keramik", re.I)),
    ("glass",      re.compile(r"\bglass\b|\bglas\b", re.I)),
]

_SIZE_RX = [
    ("kingsize",     re.compile(r"king.?size|\bks\b", re.I)),
    ("slim",         re.compile(r"\bslim\b", re.I)),
    ("1-1/4",        re.compile(r"1\s*1/4|1[¼]|\b1\.25\b|\bmedium\b", re.I)),
    ("single-wide",  re.compile(r"single.?wide|\bregular\b|\bsw\b", re.I)),
    ("6mm",          re.compile(r"\b6\s*mm\b", re.I)),
    ("8mm",          re.compile(r"\b8\s*mm\b", re.I)),
    ("slim-6mm",     re.compile(r"slim.?line", re.I)),
]
# generic "NNg" / "NNmm" / "NN x NN" measurement capture
_MEASURE_RX = re.compile(r"\b\d+(?:[.,]\d+)?\s?(?:g|kg|ml|mm|cm)\b", re.I)


def mine_tags(name: str, group: str, category: str, artemis_path: str,
              facets: Optional[dict] = None) -> tuple[list[str], dict]:
    """Return (tags[], attributes{}). The full artemis_path is kept VERBATIM as a
    tag (lossless breadcrumb); brand/material/size are mined from name + path + facets."""
    facets = facets or {}
    tags: list[str] = []
    attrs: dict = {}

    # lossless breadcrumb (e.g. "artemis:papers-co/drehpapier/raw")
    if artemis_path:
        tags.append(f"artemis:{artemis_path}")

    hay = " ".join([name, artemis_path.replace("/", " "), " ".join(str(v) for v in facets.values())])

    # brand
    for canonical, rx in _BRAND_RX:
        if rx.search(hay):
            attrs["brand"] = canonical
            tags.append(f"brand:{canonical}")
            break

    # material(s)
    mats = [label for label, rx in _MATERIAL_RX if rx.search(hay)]
    if mats:
        attrs["material"] = mats[0]
        for m in mats:
            tags.append(f"material:{m}")

    # size
    for label, rx in _SIZE_RX:
        if rx.search(hay):
            attrs["size"] = label
            tags.append(f"size:{label}")
            break
    # a literal measurement, if present, is a useful attribute even when no size class hit
    meas = _MEASURE_RX.search(name)
    if meas:
        attrs.setdefault("measure", meas.group(0).replace(" ", ""))
        tags.append(f"measure:{attrs['measure']}")

    # any deeper Artemis levels (lvl3, lvl4) fold into tags as breadcrumb facets (lossless)
    segs = [s for s in artemis_path.split("/") if s]
    for deeper in segs[2:]:
        t = f"path:{deeper}"
        if t not in tags:
            tags.append(t)

    # explicit facet pass-through (normalized keys win where rules missed) + tag the
    # high-value ones so they're searchable (brand / flavor / material / size / color).
    for k, v in facets.items():
        attrs.setdefault(k, v)
        if k in ("brand", "flavor", "material", "size", "color") and v:
            t = f"{k}:{v}"
            if t not in tags:
                tags.append(t)

    # de-dup, keep order
    seen, uniq = set(), []
    for t in tags:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq, attrs


# --------------------------------------------------------------------------- #
# Step 2 — classify_compliance (RULE).  behavior_class + age + age_reason      #
# --------------------------------------------------------------------------- #
def classify_compliance(name: str, group: str, group_slug: str) -> dict:
    """LAW axis. Deterministic. Returns behavior_class, age_restricted, age_reason,
    plus a `class_review` flag when the rule's class looks looser than the group expects.

    Precedence:
      1. catalog_taxonomy.classify() reads the NAME (the real, live rules).
      2. The §5 group policy can only RAISE the age gate (never lower it).
      3. A class looser than the group's expected class -> flag for human review
         (we do NOT silently tighten the legal class from a group hint)."""
    _cat, cls, rule_age = classify(name, _GROUP_CLASS_HINT.get(group_slug))
    policy = GROUP_POLICY.get(group, {"age": False, "age_reason": "no-group-policy",
                                      "expect_class": "standard"})

    if rule_age:
        age = True
        age_reason = f"class:{cls}"            # a substance rule set it (auditable)
    elif policy["age"]:
        age = True
        age_reason = policy["age_reason"]      # group default raised the gate
    else:
        age = False
        age_reason = "none"

    # rank classes by strictness so we only ever flag (never auto-tighten) the LAW axis
    _strict = {"standard": 0, "cbd_open": 1, "cbd_hemp": 2, "alcohol": 3, "tobacco_nicotine": 3}
    class_review = _strict.get(cls, 0) < _strict.get(policy.get("expect_class", "standard"), 0)

    return {
        "behavior_class": cls,
        "age_restricted": age,
        "age_reason": age_reason,
        "class_review": class_review,
        "expected_class": policy.get("expect_class", "standard"),
    }


# --------------------------------------------------------------------------- #
# Step 3a — map_category (RULE half).  group + clean lvl2; flag the ambiguous   #
# --------------------------------------------------------------------------- #
def map_category_rule(group: str, artemis_segments: list[str]) -> dict:
    """Consolidate Artemis lvl2 into a clean Banco category. Returns the category,
    a confidence, whether the LLM is needed, and the allowed-category set for the LLM."""
    table, allowed = _GROUP_CONSOLIDATION.get(group, (None, None))
    lvl2_slug = artemis_segments[1] if len(artemis_segments) >= 2 else ""
    deeper = " ".join(artemis_segments[1:])  # consider lvl2..lvl4 for the match

    if table:
        for rx, clean in table:
            if rx.search(deeper):
                return {"category": clean, "confidence": 0.9, "llm_needed": False,
                        "allowed": allowed, "source": "rule"}
        # group is known but lvl2 didn't map -> let the LLM choose from the allowed set
        prov = lvl2_slug.replace("-", " ").title() or "Unsorted"
        return {"category": prov, "confidence": 0.4, "llm_needed": True,
                "allowed": allowed, "source": "provisional"}

    # group with no consolidation table yet: title-case lvl2, ask LLM to confirm
    prov = lvl2_slug.replace("-", " ").title() or group
    return {"category": prov, "confidence": 0.5, "llm_needed": True,
            "allowed": None, "source": "provisional"}


# --------------------------------------------------------------------------- #
# Raw input + enrichment record (the §3 shape)                                #
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# §6a Rich-metadata facet normalization. The Artemis DETAIL page carries a       #
# <table class="Categorization"> of Title/Name rows (Manufacturer, Taste,        #
# Length, ...). We keep them VERBATIM (raw_facets, lossless) AND normalize the    #
# keys to a queryable canonical set so faceted search / analytics work later.    #
# --------------------------------------------------------------------------- #
_FACET_KEY_MAP = {
    "manufacturer": "brand", "brand": "brand", "marke": "brand", "hersteller": "brand",
    "taste": "flavor", "flavour": "flavor", "flavor": "flavor", "geschmack": "flavor", "aroma": "flavor",
    "length": "length", "länge": "length", "laenge": "length",
    "width": "width", "breite": "width",
    "height": "height", "höhe": "height", "hoehe": "height",
    "diameter": "diameter", "durchmesser": "diameter",
    "size": "size", "grösse": "size", "groesse": "size", "größe": "size", "format": "size",
    "material": "material", "content": "count", "inhalt": "count", "quantity": "count",
    "menge": "count", "stück": "count", "stueck": "count", "pieces": "count", "anzahl": "count",
    "color": "color", "colour": "color", "farbe": "color",
    "weight": "weight", "gewicht": "weight",
}


def normalize_facets(raw_facets: dict) -> dict:
    """Map verbatim Artemis facet titles -> canonical attribute keys. Unknown keys are
    snake-cased and kept (nothing discarded)."""
    norm: dict = {}
    for k, v in (raw_facets or {}).items():
        key = str(k).strip().lower()
        canon = _FACET_KEY_MAP.get(key)
        if not canon:
            canon = re.sub(r"[^a-z0-9]+", "_", key).strip("_") or "misc"
        # first value wins for a canonical key (detail tables rarely duplicate)
        norm.setdefault(canon, str(v).strip())
    return norm


@dataclass
class RawProduct:
    """Normalized feeder record. Importers produce this; the recipe consumes it."""
    identifier: str                 # source product identifier (e.g. Artemis 'identifier')
    name: str
    price_text: Optional[str]
    group: str                      # Banco group label (Artemis lvl1 display name)
    group_slug: str                 # Artemis lvl1 slug (for class hint)
    artemis_path: str               # full breadcrumb verbatim, e.g. "papers-co/drehpapier/raw"
    artemis_segments: list[str]
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    source_lang: str = "en"
    source_id: Optional[str] = None  # source GUID
    facets: dict = field(default_factory=dict)           # raw detail-page facets (verbatim, lossless)
    detail_description: Optional[str] = None             # full description scraped from the detail page


@dataclass
class EnrichmentRecord:
    sku: str
    source: dict
    group: str
    category: str
    tags: list[str]
    description: str
    attributes: dict
    behavior_class: str
    age_restricted: bool
    age_reason: str
    price: Optional[str]
    cost: Optional[str]
    stock_quantity: int
    confidence: dict
    flags: list[str]
    enriched_by: dict

    def to_dict(self) -> dict:
        return self.__dict__.copy()


# --------------------------------------------------------------------------- #
# Steps 1-4 + 6 assembled — the RULES pass (no LLM, fully deterministic)       #
# --------------------------------------------------------------------------- #
def enrich_rules(raw: RawProduct) -> EnrichmentRecord:
    """Run the deterministic half of the recipe. Description is left empty + the
    record is flagged needs_description until the LLM pass fills it (or it stays
    [LLM-pending] if the brain is unreachable)."""
    price = parse_price(raw.price_text)
    comp = classify_compliance(raw.name, raw.group, raw.group_slug)
    catmap = map_category_rule(raw.group, raw.artemis_segments)
    # §6a: normalize the rich detail-page facets, mine from them, keep raw verbatim.
    norm_facets = normalize_facets(raw.facets)
    tags, attrs = mine_tags(raw.name, raw.group, catmap["category"], raw.artemis_path, norm_facets)
    if raw.facets:
        attrs["raw_facets"] = dict(raw.facets)   # lossless verbatim source facets

    # description: the scraped detail-page text is authoritative; the LLM only drafts when absent.
    detail_desc = (raw.detail_description or "").strip()
    has_detail_desc = len(detail_desc) >= 20

    flags: list[str] = [] if has_detail_desc else ["needs_description"]
    if catmap["llm_needed"] or catmap["category"] == "Unsorted":
        flags.append("needs_review")
    if comp["class_review"]:
        flags.append("needs_review")
    # EN source with an obviously-German name fragment -> flag for translation review
    if raw.source_lang == "en" and re.search(r"[äöüÄÖÜ]|drehpap|bl[aä]ttchen|feuerzeug|zubeh", raw.name, re.I):
        flags.append("needs_translation")
    flags = list(dict.fromkeys(flags))

    return EnrichmentRecord(
        sku=make_sku(raw.identifier),
        source={
            "system": "artemis", "platform": "tamar", "id": raw.source_id,
            "identifier": raw.identifier, "url": raw.source_url,
            "artemis_path": raw.artemis_path, "source_lang": raw.source_lang,
            "image_url": raw.image_url, "raw_name": raw.name,
            "raw_price_text": raw.price_text,
        },
        group=raw.group,
        category=catmap["category"],
        tags=tags,
        description=detail_desc if has_detail_desc else "",   # scraped wins; else LLM drafts
        attributes=attrs,
        behavior_class=comp["behavior_class"],
        age_restricted=comp["age_restricted"],
        age_reason=comp["age_reason"],
        price=str(price) if price is not None else None,
        cost=None,                            # not in source
        stock_quantity=1,                     # zero-perpetual: the shelf is the stock check
        confidence={
            "category": catmap["confidence"],
            "class": 1.0,                     # rule-derived, deterministic
            "description": 1.0 if has_detail_desc else 0.0,  # 1.0 = from source detail page
        },
        flags=flags,
        enriched_by={"model": None, "recipe_version": RECIPE_VERSION, "run_id": None},
        # carried for the LLM pass (not persisted):
    )


# Attach the per-item LLM context the runner needs (allowed categories + whether the
# LLM must resolve the category). Kept off the dataclass so the record stays clean.
def llm_context(raw: RawProduct) -> dict:
    catmap = map_category_rule(raw.group, raw.artemis_segments)
    return {
        "allowed": catmap.get("allowed"),
        "must_resolve_category": catmap["llm_needed"],
        "rule_category": catmap["category"],
    }


# --------------------------------------------------------------------------- #
# Step 3b + 5 — the LLM pass (MERCHANDISING ONLY).  Schema-bounded; batched.    #
# Never touches behavior_class / age_restricted / age_reason.                   #
# --------------------------------------------------------------------------- #
_LLM_SYSTEM = (
    "You are a retail catalog merchandiser for a Swiss head-shop POS. "
    "You ONLY do merchandising: pick the best shopper-facing CATEGORY for each item "
    "from the allowed list, and write a SHORT factual description (1-2 sentences) from "
    "the item name and facets. You NEVER decide age limits, tax, or legal class. "
    "Do not invent specifications you cannot see. Output JSON only, matching the schema."
)


def _batch_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "sku": {"type": "string"},
                        "category": {"type": "string"},
                        "description": {"type": "string"},
                        "category_confidence": {"type": "number"},
                    },
                    "required": ["sku", "category", "description", "category_confidence"],
                },
            }
        },
        "required": ["items"],
    }


def _build_batch_prompt(batch: list[dict]) -> str:
    lines = ["Enrich these catalog items. For EACH, return its sku, the best category "
             "(choose from that item's allowed_categories — if none fit choose the closest), "
             "a 1-2 sentence description, and a 0..1 category_confidence.\n"]
    for it in batch:
        allowed = it.get("allowed") or ["(no constraint — use a short sensible noun phrase)"]
        lines.append(
            f"- sku: {it['sku']}\n"
            f"  name: {it['name']}\n"
            f"  group: {it['group']}\n"
            f"  breadcrumb: {it['artemis_path']}\n"
            f"  facets: {it.get('attributes') or {}}\n"
            f"  allowed_categories: {allowed}\n"
        )
    return "\n".join(lines)


async def llm_enrich_batch(batch: list[dict], target, client=None) -> dict:
    """One schema-bounded LLM call for a batch of items. Returns {sku: {category,
    description, category_confidence}}. `batch` items are dicts with sku/name/group/
    artemis_path/attributes/allowed. Raises on transport/HTTP error (caller decides
    whether to fall back to rules-only)."""
    from src.llm.client import run_llm  # local import keeps this module importable w/o httpx
    res = await run_llm(
        _build_batch_prompt(batch),
        target=target,
        system=_LLM_SYSTEM,
        schema=_batch_schema(),
        client=client,
    )
    import json as _json
    text = res.text.strip()
    # strip any <think> blocks defensively (reasoning models); run_llm usually handles it
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    try:
        data = _json.loads(text)
    except Exception:
        # last-ditch: pull the first {...} object or [...] array
        m = re.search(r"[\{\[].*[\}\]]", text, re.S)
        data = _json.loads(m.group(0)) if m else {"items": []}
    # the model may return a bare array, an {items:[...]} object, or {results:[...]}
    if isinstance(data, list):
        rows_in = data
    elif isinstance(data, dict):
        rows_in = data.get("items") or data.get("results") or data.get("products") or []
    else:
        rows_in = []
    out: dict = {}
    for row in rows_in:
        if not isinstance(row, dict):
            continue
        sku = str(row.get("sku", "")).strip()
        if sku:
            out[sku] = {
                "category": str(row.get("category", "")).strip(),
                "description": str(row.get("description", "")).strip(),
                "category_confidence": float(row.get("category_confidence", 0.0) or 0.0),
            }
    return out, res.model


# --------------------------------------------------------------------------- #
# Step 6 — finalize: merge the LLM pass onto a rules record                    #
# --------------------------------------------------------------------------- #
def apply_llm(rec: EnrichmentRecord, llm_row: Optional[dict], model: Optional[str],
              ctx: dict) -> EnrichmentRecord:
    """Fold an LLM result onto a rules record. The LLM may set the description always,
    and may set the category ONLY when the rule flagged it ambiguous (must_resolve)."""
    has_source_desc = bool(rec.description.strip())   # scraped detail-page description

    if llm_row is None:
        # brain unreachable — keep the structure honest + reviewable
        if not has_source_desc:
            rec.description = "[LLM-pending: no detail-page description and brain unreachable]"
        rec.enriched_by["model"] = "[LLM-pending]"
        return rec

    # description: a scraped detail-page description is authoritative; LLM only fills a gap.
    if not has_source_desc:
        desc = (llm_row.get("description") or "").strip()
        if desc:
            rec.description = desc
            rec.confidence["description"] = round(min(0.9, max(0.5, 0.7)), 2)
            if "needs_description" in rec.flags:
                rec.flags.remove("needs_description")
        else:
            rec.description = "[LLM-pending: empty description returned]"

    # category: LLM resolves ONLY the ambiguous ones; confident rule mappings stand.
    if ctx.get("must_resolve_category"):
        cat = (llm_row.get("category") or "").strip()
        allowed = ctx.get("allowed")
        if cat and (not allowed or cat in allowed):
            rec.category = cat
            rec.confidence["category"] = round(
                min(0.9, max(0.5, llm_row.get("category_confidence", 0.6))), 2)
            if "needs_review" in rec.flags and rec.confidence["category"] >= 0.75:
                rec.flags.remove("needs_review")
        # if the LLM returned something outside the allowed set, keep the rule value +
        # leave needs_review on (we never let the model invent a category off-list)

    rec.enriched_by["model"] = model
    rec.flags = list(dict.fromkeys(rec.flags))
    return rec
