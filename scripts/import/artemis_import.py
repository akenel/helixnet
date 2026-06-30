#!/usr/bin/env python3
"""
Artemis Luzern webshop -> Banco catalog importer  (sandbox / delta-safe).

WHAT THIS DOES
--------------
Pulls the live product catalog from the Artemis Luzern webshop
(https://www.artemisluzern.ch) into Banco's `products` table, using the
website's own category hierarchy as the merchandising skeleton. It is built to
be RE-RUN for deltas: it is an idempotent upsert keyed on SKU (the Artemis
`identifier`), and it keeps a local snapshot so each run can report exactly what
was added / changed / removed.

Rule #11 (Python first). Stdlib-only for the DRY-RUN path (argparse + urllib +
sqlite/json) so it runs ANYWHERE with no deps and no DB. SQLAlchemy/asyncpg are
imported lazily, only when you pass --commit (run that on the box).

SAFETY
------
DRY-RUN IS THE DEFAULT. Dry-run writes NOTHING to the DB and downloads NO
product images — it maps, counts, validates and prints a report. The real
import is gated behind --commit (a separate, human-reviewed step).

HOW THE ARTEMIS API IS REACHED  (all verified live, 2026-06-30)
--------------------------------------------------------------
1. Sitemap index   https://www.artemisluzern.ch/sitemap.xml
     -> child  siteMap-nav-de0.xml  = 392 category URLs (/de/{group}[/cat[/sub[/...]]])
     -> child  siteMap-pro-de*.xml  = ~6334 product URLs (not needed here; we
        enumerate products per category instead so we keep the category mapping).
2. Each category page embeds a hidden input that hands us the exact API call:
       <input id="productsApiUrl" value="/api/shop/products?...
              &navigationId=26169&hierarchicalCategoryId={GUID}..." />
   navigationId is a constant (the shop nav root); the hierarchicalCategoryId
   GUID is the per-category key. We extract that URL, force languageId to our
   language, and page it.
3. Products API (per category, 12/page, page while hasMore):
       GET /api/shop/products?loadingType=79&languageId={L}&navigationId=26169
           &filterByAllCategories=True&displayType=1
           &hierarchicalCategoryId={GUID}&page={n}
   Returns {products:[{id, identifier(=SKU), name, salesPriceText:"CHF 1.90",
            coverUrl:"/ProductImage.ashx?...", linkUrl:"/en/product/...-21577"}],
            hasMore, count(total in that category)}.

LANGUAGE  (languageId)
----------------------
Banco's source language is ENGLISH.  3=EN (primary/default), 2=DE (fallback),
4=FR.  1 and 5 are empty; Italian is not configured.  Artemis's English is
PARTIAL: product NAMES are brand-based and identical across languages (fine),
but some attribute/description text stays German. We pull EN; any field that
comes back empty falls back to DE and is flagged `needs_translation` so Banco's
LLM layer (src/llm/run_llm) can fill it later. The list API returns name + price
+ image + url only; DESCRIPTIONS live on the product detail page and are a later
enrichment pass (see --notes), not part of this import.

CATEGORY MAPPING  (Artemis 3-4 levels -> Banco Group -> Category)
-----------------------------------------------------------------
Artemis depth (from the nav sitemap): 7 groups (lvl1), 63 lvl2, 310 lvl3, 11 lvl4.
Banco's intended model is 2 levels: Group -> Category (docs/BANCO-CATEGORY-MANAGEMENT-PLAN.md).
We collapse:
    banco_group     = Artemis level 1   (headshop, cbd, lifestyle, shisha,
                                          vape-co, grow, papers-co)
    banco_category  = Artemis level 2    (the merchandising bucket)
    deeper levels (3,4) -> folded into the product's `tags` as a breadcrumb and
                           kept verbatim in the snapshot (`artemis_path`) so the
                           future `categories` table can recover full depth.
The live ProductModel today has only a single flat `category` String(100); we
set it to the level-2 name and carry group + breadcrumb in `tags`. When the
categories table lands (Phase A of the plan), group=lvl1 / category=lvl2 map
straight across — see "OPEN QUESTIONS" printed by --notes.

BEHAVIOUR CLASS  (money / law axis -- kept separate from merchandising)
-----------------------------------------------------------------------
Category (above) is merchandising only. The VAT / 18+ behaviour `product_class`
is derived independently via src/services/catalog_taxonomy.classify() on the
product name (with the Artemis group as a hint). This respects Banco's two-axis
design (BL-96): a category never sets tax/age. Flagged for human review on commit.

DELTAS
------
A snapshot file (JSON, default scripts/import/.artemis_snapshot.json or --snapshot)
maps SKU -> content hash + last-seen fields. Each run computes:
    ADD       SKU seen now, not in snapshot
    UPDATE    SKU in both, hash changed (price/name/category/image differ)
    UNCHANGED SKU in both, identical
    REMOVED   SKU in snapshot, not seen now  -> on commit, flagged is_active=False
                                                 (deactivated, never hard-deleted)
Hash covers (name, price, category, image_url, product_class, is_age_restricted).
The snapshot is only written on a real run (after a successful --commit), or with
--write-snapshot, so dry-runs never disturb delta state.

USAGE
-----
  # default dry-run, full catalog, English:
  python scripts/import/artemis_import.py

  # polite bounded validation run (sample N categories spread across groups):
  python scripts/import/artemis_import.py --max-categories 30

  # see model-integration open questions:
  python scripts/import/artemis_import.py --notes

  # the real import (DO NOT run casually -- human-reviewed; needs DB on the box):
  python scripts/import/artemis_import.py --commit --db-url postgresql+asyncpg://user:pw@host/banco_sandbox
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field, asdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, Iterator, Optional

# --------------------------------------------------------------------------- #
# Constants                                                                    #
# --------------------------------------------------------------------------- #
BASE = "https://www.artemisluzern.ch"
SITEMAP_INDEX = f"{BASE}/sitemap.xml"
USER_AGENT = "BancoCatalogImporter/1.0 (+Banco POS; polite; contact: angel.kenel@gmail.com)"

# languageId map. EN is Banco's source language; DE is the fallback for empty fields.
LANG_IDS = {"en": 3, "de": 2, "fr": 4}
FALLBACK_LANG = "de"

# Nice display names for the 7 Artemis top-level groups (banco_group).
GROUP_LABELS = {
    "headshop": "Headshop",
    "cbd": "CBD",
    "lifestyle": "Lifestyle",
    "shisha": "Shisha",
    "vape-co": "Vape & Co",
    "grow": "Grow",
    "papers-co": "Papers & Co",
}

DEFAULT_SNAPSHOT = Path(__file__).with_name(".artemis_snapshot.json")
DEFAULT_CACHE = Path(__file__).with_name(".artemis_cache")

# Fields hashed for delta detection (the ones a re-run should react to).
DELTA_FIELDS = ("name", "price", "category", "image_url", "product_class", "is_age_restricted")


# --------------------------------------------------------------------------- #
# HTTP -- retries, polite rate-limit, optional on-disk cache                   #
# --------------------------------------------------------------------------- #
class Http:
    def __init__(self, delay: float = 0.3, retries: int = 4, cache_dir: Optional[Path] = None,
                 timeout: int = 30):
        self.delay = delay
        self.retries = retries
        self.timeout = timeout
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
        self.n_requests = 0
        self._last = 0.0

    def _cache_path(self, url: str) -> Optional[Path]:
        if not self.cache_dir:
            return None
        h = hashlib.sha256(url.encode()).hexdigest()[:24]
        return self.cache_dir / f"{h}.bin"

    def get(self, url: str, *, cacheable: bool = True) -> bytes:
        cp = self._cache_path(url) if cacheable else None
        if cp and cp.exists():
            return cp.read_bytes()
        # polite spacing
        gap = self.delay - (time.monotonic() - self._last)
        if gap > 0:
            time.sleep(gap)
        last_err: Optional[Exception] = None
        for attempt in range(self.retries):
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": USER_AGENT,
                    "Accept-Encoding": "gzip",
                })
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                    if resp.headers.get("Content-Encoding") == "gzip":
                        raw = gzip.decompress(raw)
                self.n_requests += 1
                self._last = time.monotonic()
                if cp:
                    cp.write_bytes(raw)
                return raw
            except urllib.error.HTTPError as e:
                # 404 is a real signal (stale sitemap entry) -- bubble up, don't retry.
                if e.code == 404:
                    raise
                last_err = e
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                last_err = e
            time.sleep(self.delay * (2 ** attempt))  # backoff
            self._last = time.monotonic()
        raise RuntimeError(f"GET failed after {self.retries} tries: {url} :: {last_err}")

    def get_text(self, url: str, **kw) -> str:
        return self.get(url, **kw).decode("utf-8", "replace")


# --------------------------------------------------------------------------- #
# Category discovery (sitemap -> hierarchy)                                    #
# --------------------------------------------------------------------------- #
@dataclass
class Category:
    url: str                       # canonical /de/... URL
    segments: list[str]            # path after /de/, e.g. [headshop, aufbewahrung, drehboxen]
    nav_id: Optional[str] = None   # navigationId (constant 26169 in practice)
    cat_guid: Optional[str] = None # hierarchicalCategoryId
    stale: bool = False            # page 404'd / no products API
    is_leaf: bool = True           # set during tree build

    @property
    def depth(self) -> int:
        return len(self.segments)

    @property
    def banco_group(self) -> str:
        g = self.segments[0]
        return GROUP_LABELS.get(g, g.replace("-", " ").title())

    @property
    def banco_category(self) -> str:
        # level-2 is the merchandising bucket; if a group has no level-2, the
        # group itself is the category.
        if len(self.segments) >= 2:
            return self.segments[1].replace("-", " ").title()
        return self.banco_group

    @property
    def breadcrumb(self) -> str:
        return "/".join(self.segments)


def discover_categories(http: Http) -> list[Category]:
    """Sitemap index -> nav sitemap -> the 392 /de/ category URLs as a tree."""
    idx = http.get_text(SITEMAP_INDEX)
    nav_url_m = re.search(r"<loc>([^<]*siteMap-nav-de0[^<]*)</loc>", idx)
    if not nav_url_m:
        raise RuntimeError("Could not find siteMap-nav-de0 in the sitemap index")
    nav_xml = http.get_text(nav_url_m.group(1))
    locs = re.findall(r"<loc>(https://www\.artemisluzern\.ch/de/[^<]+)</loc>", nav_xml)
    cats: list[Category] = []
    seen = set()
    for u in locs:
        u = u.rstrip("/")
        if u in seen:
            continue
        seen.add(u)
        seg = u.split("/de/", 1)[1].split("/")
        cats.append(Category(url=u, segments=seg))
    # mark leaves: a category is a leaf if no other category extends its path
    paths = {tuple(c.segments) for c in cats}
    for c in cats:
        t = tuple(c.segments)
        c.is_leaf = not any(p != t and p[:len(t)] == t for p in paths)
    return cats


def resolve_category_api(http: Http, cat: Category) -> bool:
    """Fetch a category page and pull navigationId + hierarchicalCategoryId from the
    embedded productsApiUrl. Returns True if resolved; marks `stale` on 404 / no API."""
    try:
        html = http.get_text(cat.url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            cat.stale = True
            return False
        raise
    m = re.search(r'id="productsApiUrl"\s+value="([^"]+)"', html)
    if not m:
        # Group landing pages (e.g. /de/grow) sometimes omit it; their leaves carry it.
        cat.stale = True
        return False
    api = m.group(1).replace("&amp;", "&")
    nav = re.search(r"navigationId=(\d+)", api)
    guid = re.search(r"hierarchicalCategoryId=([0-9a-fA-F-]{36})", api)
    cat.nav_id = nav.group(1) if nav else None
    cat.cat_guid = guid.group(1) if guid else None
    return bool(cat.cat_guid)


def products_api_url(cat: Category, lang: str, page: int) -> str:
    L = LANG_IDS[lang]
    return (f"{BASE}/api/shop/products?loadingType=79&languageId={L}"
            f"&navigationId={cat.nav_id}&filterByAllCategories=True&displayType=1"
            f"&hierarchicalCategoryId={cat.cat_guid}&page={page}")


def iter_category_products(http: Http, cat: Category, lang: str,
                           max_pages: int = 200) -> Iterator[dict]:
    """Page the products API for one category until hasMore is false."""
    page = 1
    while page <= max_pages:
        data = json.loads(http.get_text(products_api_url(cat, lang, page), cacheable=False))
        for p in data.get("products", []):
            yield p
        if not data.get("hasMore"):
            return
        page += 1


# --------------------------------------------------------------------------- #
# Price parsing  ("CHF 1.90", "CHF 39.-", "CHF 1'234.50")                      #
# --------------------------------------------------------------------------- #
def parse_price(text: Optional[str]) -> Optional[Decimal]:
    s = (text or "").replace("CHF", "").strip()
    s = s.replace("’", "").replace("'", "")          # Swiss thousands apostrophe
    s = s.replace("–", "-").replace("—", "-").strip()  # en/em dash -> hyphen
    if s.endswith(".-"):       # "39.-" -> 39.00
        s = s[:-2] + ".00"
    elif s.endswith("-"):      # "39-" -> 39
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
# Behaviour class -- reuse Banco's taxonomy if importable, else a safe default #
# --------------------------------------------------------------------------- #
_GROUP_CLASS_HINT = {"cbd": "CBD"}  # Artemis group -> classify() ref_category hint


def _load_classifier():
    """Try to import Banco's real classifier so class/age match the live POS.
    Falls back to a no-op (standard / not age-restricted) so the dry-run is
    standalone-safe off the box."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from src.services.catalog_taxonomy import classify  # type: ignore
        return classify, True
    except Exception:
        def _fallback(title, ref_category=None, raw=None):
            return None, "standard", False
        return _fallback, False


# Enrichment helpers (namespaced SKU + minted internal EAN-13). The canonical home is
# src/services/catalog_enrichment.py; a tiny stdlib fallback keeps the dry-run standalone
# off the box. Both produce IDENTICAL codes (same prefix + check-digit math).
try:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.services.catalog_enrichment import (  # type: ignore
        make_sku as _make_sku, mint_internal_ean13 as _mint_ean13, SOURCE_PREFIX,
    )
except Exception:  # pragma: no cover - off-box standalone fallback
    SOURCE_PREFIX = "TAM"

    def _make_sku(identifier, prefix=SOURCE_PREFIX):
        return f"{prefix}-{str(identifier).strip()}"

    def _mint_ean13(seed, prefix="20"):
        try:
            n = int(str(seed).strip())
        except (TypeError, ValueError):
            n = int(hashlib.sha256(str(seed).encode()).hexdigest(), 16)
        payload = f"{prefix}{n % (10 ** 10):010d}"           # 12 data digits
        chk = sum((1 if i % 2 == 0 else 3) * int(d) for i, d in enumerate(payload))
        return payload + str((10 - (chk % 10)) % 10)


# --------------------------------------------------------------------------- #
# Mapping Artemis product -> Banco product fields                              #
# --------------------------------------------------------------------------- #
@dataclass
class MappedProduct:
    sku: str                       # NAMESPACED, e.g. "TAM-21577" (§9.4 — no demo collision)
    name: str
    price: Optional[str]           # Decimal as string (money-as-string discipline)
    category: str                  # flat ProductModel.category (= banco_category, lvl2)
    banco_group: str               # -> products.product_group (flat lvl1, §9.1)
    artemis_path: str              # full breadcrumb (for the future categories table)
    tags: str                      # "artemis:headshop/aufbewahrung/drehboxen"
    image_url: Optional[str]       # full Artemis image URL (NOT downloaded in dry-run)
    source_url: str                # Artemis product page ("View on Artemis", §9.6)
    source_lang: str
    product_class: str
    is_age_restricted: bool
    supplier_sku: str              # Artemis raw identifier (un-namespaced)
    barcode: Optional[str] = None  # §6b minted internal EAN-13 (no source EAN exists)
    barcode_is_internal: bool = True
    age_reason: Optional[str] = None  # auditable LAW-axis trail (the rule that set 18+)
    needs_translation: bool = False
    artemis_id: Optional[str] = None  # Artemis product GUID (source_id / image source key)

    def delta_hash(self) -> str:
        payload = "|".join(str(getattr(self, f)) for f in DELTA_FIELDS)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


def map_product(p: dict, cat: Category, lang: str, classify) -> Optional[MappedProduct]:
    ident = p.get("identifier")
    raw_sku = str(ident).strip() if ident is not None else ""
    name = (p.get("name") or "").strip()
    if not raw_sku or not name:
        return None
    price = parse_price(p.get("salesPriceText"))
    cover = p.get("coverUrl") or ""
    image_url = (BASE + cover) if cover.startswith("/") else (cover or None)
    link = p.get("linkUrl") or ""
    source_url = (BASE + link) if link.startswith("/") else link

    # behaviour class (money/law axis) from the name + group hint; category stays Artemis-driven
    _, our_class, age = classify(name, _GROUP_CLASS_HINT.get(cat.segments[0]))
    # auditable age trail (§3): a substance rule wins; else the group default raised the gate.
    if age:
        age_reason = (f"class:{our_class}" if our_class and our_class != "standard"
                      else f"group:{cat.segments[0]}")
    else:
        age_reason = None
    return MappedProduct(
        sku=_make_sku(raw_sku),                     # TAM-<id> (§9.4, matches the enrichment recipe)
        name=name[:255],
        price=str(price) if price is not None else None,
        category=cat.banco_category[:100],
        banco_group=cat.banco_group,
        artemis_path=cat.breadcrumb,
        tags=f"artemis:{cat.breadcrumb}",
        image_url=(image_url[:500] if image_url else None),
        source_url=source_url,
        source_lang=lang,
        product_class=our_class or "standard",
        is_age_restricted=bool(age),
        supplier_sku=raw_sku,
        barcode=_mint_ean13(raw_sku),               # §6b minted internal EAN-13 (scannable, no source EAN)
        barcode_is_internal=True,
        age_reason=age_reason,
        needs_translation=False,  # names are brand-based; set True when a DE-fallback fills a field
        artemis_id=p.get("id"),
    )


# --------------------------------------------------------------------------- #
# Snapshot / delta engine                                                      #
# --------------------------------------------------------------------------- #
def load_snapshot(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}
    return {}


def compute_deltas(mapped: dict[str, MappedProduct], snapshot: dict) -> dict:
    now_skus = set(mapped)
    prev_skus = set(snapshot)
    adds, updates, unchanged = [], [], []
    for sku in now_skus:
        h = mapped[sku].delta_hash()
        prev = snapshot.get(sku)
        if prev is None:
            adds.append(sku)
        elif prev.get("hash") != h:
            changed = [f for f in DELTA_FIELDS
                       if str(prev.get(f)) != str(getattr(mapped[sku], f))]
            updates.append((sku, changed))
        else:
            unchanged.append(sku)
    removed = sorted(prev_skus - now_skus)
    return {"add": sorted(adds), "update": updates, "unchanged": unchanged, "removed": removed}


def snapshot_entry(mp: MappedProduct) -> dict:
    e = {f: getattr(mp, f) for f in DELTA_FIELDS}
    e["hash"] = mp.delta_hash()
    return e


# --------------------------------------------------------------------------- #
# Image storage design (NOT executed in dry-run)                              #
# --------------------------------------------------------------------------- #
IMAGE_STORAGE_NOTE = """\
IMAGE STEP (designed; runs ONLY on --commit --with-images, never in dry-run):
  For each product with an image_url:
    1. GET the full image  (https://www.artemisluzern.ch/ProductImage.ashx?...)
    2. run it through src/services/image_intake.process(bytes, PRODUCT)
       (EXIF-orient -> downscale 1024px long edge -> autocontrast -> JPEG, +256px thumb)
    3. put the bytes in MinIO at key  pos-products/{product_id}/{image_id}.jpg
       (minio_service.client.put_object, bucket minio_service.bucket_name)
    4. insert a ProductImageModel row (product_id, sort_order=0)
    5. set products.image_url = /api/v1/pos/products/{product_id}/images/{image_id}
  This mirrors pos_router._copy_external_image_to_storage exactly, so imported
  images behave identically to a cashier-uploaded photo. Best-effort per image:
  a failed download must NOT fail the product upsert (keep the external URL).
"""


# --------------------------------------------------------------------------- #
# Core run                                                                     #
# --------------------------------------------------------------------------- #
def select_categories(cats: list[Category], max_categories: Optional[int]) -> list[Category]:
    """We enumerate products via LEAF categories (most-specific). If --max-categories
    is set, spread the sample across all groups so the dry-run is representative."""
    leaves = [c for c in cats if c.is_leaf]
    if not max_categories or max_categories >= len(leaves):
        return leaves
    # round-robin across groups
    by_group: dict[str, list[Category]] = {}
    for c in leaves:
        by_group.setdefault(c.segments[0], []).append(c)
    out: list[Category] = []
    groups = list(by_group.values())
    i = 0
    while len(out) < max_categories and any(groups):
        g = groups[i % len(groups)]
        if g:
            out.append(g.pop(0))
        i += 1
        if all(not g for g in groups):
            break
    return out[:max_categories]


def run(args) -> dict:
    http = Http(delay=args.delay, retries=args.retries,
                cache_dir=(None if args.no_cache else Path(args.cache_dir)))
    classify, real_classifier = _load_classifier()

    print(f"[1/4] discovering categories from sitemap ...", flush=True)
    cats = discover_categories(http)
    leaves = [c for c in cats if c.is_leaf]
    print(f"      {len(cats)} categories  "
          f"(groups={sum(c.depth==1 for c in cats)}, lvl2={sum(c.depth==2 for c in cats)}, "
          f"lvl3={sum(c.depth==3 for c in cats)}, lvl4={sum(c.depth>=4 for c in cats)}, "
          f"leaves={len(leaves)})", flush=True)

    targets = select_categories(cats, args.max_categories)
    print(f"[2/4] resolving product-API ids for {len(targets)} leaf categories "
          f"({'SAMPLE' if args.max_categories else 'FULL'}) ...", flush=True)
    resolved, stale = [], []
    for i, c in enumerate(targets, 1):
        ok = resolve_category_api(http, c)
        (resolved if ok else stale).append(c)
        if i % 25 == 0:
            print(f"      resolved {i}/{len(targets)} ...", flush=True)

    print(f"      resolved={len(resolved)}  stale/404={len(stale)}", flush=True)

    print(f"[3/4] enumerating products ({args.lang.upper()}) per category, dedup by SKU ...",
          flush=True)
    mapped: dict[str, MappedProduct] = {}
    multi_listed = 0
    per_cat_counts: dict[str, int] = {}
    cat_errors = []
    for i, c in enumerate(resolved, 1):
        try:
            n = 0
            for p in iter_category_products(http, c, args.lang, max_pages=args.max_pages):
                mp = map_product(p, c, args.lang, classify)
                if not mp:
                    continue
                n += 1
                if mp.sku in mapped:
                    # product cross-listed; keep the DEEPER (more specific) category
                    prev = mapped[mp.sku]
                    multi_listed += 1
                    if c.depth > prev_depth_of(prev):
                        mapped[mp.sku] = mp
                else:
                    mapped[mp.sku] = mp
            per_cat_counts[c.breadcrumb] = n
        except Exception as e:
            cat_errors.append((c.breadcrumb, str(e)))
        if i % 25 == 0:
            print(f"      {i}/{len(resolved)} categories, {len(mapped)} unique SKUs ...",
                  flush=True)

    # delta vs snapshot
    snapshot = load_snapshot(Path(args.snapshot))
    deltas = compute_deltas(mapped, snapshot)

    print(f"[4/4] building report ...", flush=True)
    report = {
        "lang": args.lang,
        "real_classifier": real_classifier,
        "n_categories_total": len(cats),
        "n_leaves": len(leaves),
        "n_targets": len(targets),
        "n_resolved": len(resolved),
        "n_stale": len(stale),
        "stale_examples": [c.breadcrumb for c in stale[:15]],
        "n_unique_products": len(mapped),
        "n_multi_listed_hits": multi_listed,
        "n_with_price": sum(1 for m in mapped.values() if m.price is not None),
        "n_without_price": sum(1 for m in mapped.values() if m.price is None),
        "n_with_image": sum(1 for m in mapped.values() if m.image_url),
        "n_age_restricted": sum(1 for m in mapped.values() if m.is_age_restricted),
        "class_breakdown": _counter([m.product_class for m in mapped.values()]),
        "group_breakdown": _counter([m.banco_group for m in mapped.values()]),
        "deltas": {
            "snapshot_exists": bool(snapshot),
            "add": len(deltas["add"]),
            "update": len(deltas["update"]),
            "unchanged": len(deltas["unchanged"]),
            "removed": len(deltas["removed"]),
        },
        "cat_errors": cat_errors[:15],
        "http_requests": http.n_requests,
    }

    _print_report(report, cats, mapped, sample_n=args.sample)

    # snapshot is only persisted on an explicit request or a real commit
    if args.write_snapshot and not args.commit:
        _write_snapshot(Path(args.snapshot), mapped)
        print(f"\n[snapshot] wrote {len(mapped)} SKUs -> {args.snapshot}")

    if args.commit:
        do_commit(args, mapped, deltas)
    else:
        print("\n*** DRY-RUN: nothing written to the DB, no images downloaded. ***")
        print("*** Re-run with --commit (human-reviewed, needs --db-url on the box) to import. ***")

    return report


def prev_depth_of(mp: MappedProduct) -> int:
    return mp.artemis_path.count("/") + 1


def _counter(items: Iterable[str]) -> dict:
    out: dict[str, int] = {}
    for x in items:
        out[x] = out.get(x, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def _write_snapshot(path: Path, mapped: dict[str, MappedProduct]):
    path.write_text(json.dumps({sku: snapshot_entry(mp) for sku, mp in mapped.items()},
                               ensure_ascii=False, indent=0))


# --------------------------------------------------------------------------- #
# Report printing                                                             #
# --------------------------------------------------------------------------- #
def _print_report(r: dict, cats: list[Category], mapped: dict[str, MappedProduct], sample_n: int):
    print("\n" + "=" * 72)
    print(" ARTEMIS -> BANCO  IMPORT  DRY-RUN REPORT")
    print("=" * 72)
    print(f" language pulled        : {r['lang'].upper()}  "
          f"(fallback {FALLBACK_LANG.upper()} for empty fields)")
    print(f" Banco classifier       : {'LIVE (src.services.catalog_taxonomy)' if r['real_classifier'] else 'fallback stub (off-box)'}")
    print(f" HTTP requests made     : {r['http_requests']}")
    print("-" * 72)
    print(" CATEGORY SKELETON")
    print(f"   categories in sitemap: {r['n_categories_total']}  (leaves {r['n_leaves']})")
    print(f"   leaves targeted      : {r['n_targets']}  ({'FULL' if r['n_targets']==r['n_leaves'] else 'SAMPLE'})")
    print(f"   resolved API ids     : {r['n_resolved']}")
    print(f"   stale / 404 / no-API : {r['n_stale']}   e.g. {', '.join(r['stale_examples'][:6])}")
    print("-" * 72)
    print(" PRODUCTS (deduped by SKU)")
    print(f"   unique products      : {r['n_unique_products']}")
    print(f"   cross-listing hits   : {r['n_multi_listed_hits']} (kept most-specific category)")
    print(f"   with price           : {r['n_with_price']}")
    print(f"   WITHOUT price        : {r['n_without_price']}")
    print(f"   with image URL       : {r['n_with_image']}  (images NOT downloaded in dry-run)")
    print(f"   age-restricted (18+) : {r['n_age_restricted']}")
    print(f"   class breakdown      : {r['class_breakdown']}")
    print(f"   group breakdown      : {r['group_breakdown']}")
    print("-" * 72)
    print(" DELTAS (vs snapshot)")
    d = r["deltas"]
    if not d["snapshot_exists"]:
        print("   no prior snapshot -> a first real run would ADD everything.")
    print(f"   add={d['add']}  update={d['update']}  unchanged={d['unchanged']}  removed={d['removed']}")
    print("-" * 72)
    print(" CATEGORY TREE (Banco Group -> Category, sample)")
    _print_tree(cats)
    print("-" * 72)
    print(f" SAMPLE OF {sample_n} MAPPED PRODUCTS (Banco fields)")
    for mp in list(mapped.values())[:sample_n]:
        print(f"   SKU {mp.sku:>7} | {mp.name[:42]:42} | CHF {str(mp.price):>7} | "
              f"{mp.banco_group} > {mp.category}")
        print(f"             class={mp.product_class} 18+={mp.is_age_restricted} "
              f"img={'yes' if mp.image_url else 'no'} lang={mp.source_lang}")
        print(f"             tags={mp.tags}")
    if r["cat_errors"]:
        print("-" * 72)
        print(" CATEGORY FETCH ERRORS (first 15)")
        for bc, e in r["cat_errors"]:
            print(f"   {bc}: {e}")
    print("=" * 72)


def _print_tree(cats: list[Category], limit_groups: int = 7, cats_per_group: int = 4):
    by_group: dict[str, list[Category]] = {}
    for c in cats:
        if c.depth == 2:
            by_group.setdefault(c.banco_group, []).append(c)
    for gi, (g, members) in enumerate(by_group.items()):
        if gi >= limit_groups:
            break
        print(f"   {g}")
        for c in members[:cats_per_group]:
            print(f"     - {c.banco_category}")
        if len(members) > cats_per_group:
            print(f"     ... (+{len(members) - cats_per_group} more)")


# --------------------------------------------------------------------------- #
# Commit (gated -- lazy DB import; run on the box)                            #
# --------------------------------------------------------------------------- #
def do_commit(args, mapped: dict[str, MappedProduct], deltas: dict):
    print("\n*** --commit: writing to the Banco DB. This is the gated, real import. ***")
    import asyncio

    async def _go():
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from datetime import datetime, timezone
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from src.db.models.product_model import ProductModel

        db_url = args.db_url or os.environ.get("BANCO_DB_URL")
        if not db_url:
            raise SystemExit("--commit requires --db-url (or $BANCO_DB_URL), e.g. "
                             "postgresql+asyncpg://user:pw@host/banco_sandbox")
        engine = create_async_engine(db_url)
        now = datetime.now(timezone.utc)
        rows = []
        for mp in mapped.values():
            rows.append(dict(
                sku=mp.sku, name=mp.name,
                price=Decimal(mp.price) if mp.price is not None else Decimal("0.00"),
                category=mp.category, product_group=mp.banco_group,
                tags=mp.tags, image_url=mp.image_url,
                product_class=mp.product_class, is_age_restricted=mp.is_age_restricted,
                age_reason=mp.age_reason,
                # §6b minted internal EAN-13 — set ONCE on insert, never clobbered on re-sync
                barcode=mp.barcode, barcode_is_internal=mp.barcode_is_internal,
                # source provenance / parity link (§9.6) + §6d translation seam
                source_system="artemis", source_id=mp.artemis_id, source_url=mp.source_url,
                source_lang=mp.source_lang, artemis_path=mp.artemis_path,
                needs_translation=mp.needs_translation,
                supplier_sku=mp.supplier_sku, supplier_name="Artemis",
                is_active=True, last_sync_at=now,
                # NB: attributes / raw_facets / enrichment_* are filled by the ENRICHMENT
                # pass (src/services/catalog_enrichment via the admin job), not this basic
                # importer — left at their column defaults here.
            ))
        # upsert keyed on the namespaced sku; the whole row is frozen when sync_override is
        # True (§9.7: a manager override is preserved + visibly "diverged"). Identity columns
        # (barcode, barcode_is_internal, source_system/id) are insert-once — NOT in update_cols,
        # so a re-sync never regenerates the minted EAN or clobbers a later manufacturer barcode.
        update_cols = ["name", "price", "category", "product_group", "tags", "image_url",
                       "product_class", "is_age_restricted", "age_reason",
                       "source_url", "source_lang", "artemis_path", "needs_translation",
                       "last_sync_at"]
        try:
            async with engine.begin() as conn:
                for s in range(0, len(rows), 500):
                    chunk = rows[s:s + 500]
                    stmt = pg_insert(ProductModel).values(chunk)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["sku"],
                        set_={c: getattr(stmt.excluded, c) for c in update_cols},
                        where=(ProductModel.sync_override.is_(False)),
                    )
                    await conn.execute(stmt)
                # deactivate removed SKUs (never hard-delete)
                if deltas["removed"]:
                    from sqlalchemy import update as sa_update
                    await conn.execute(
                        sa_update(ProductModel)
                        .where(ProductModel.sku.in_(deltas["removed"]))
                        .where(ProductModel.sync_override.is_(False))
                        .values(is_active=False, last_sync_at=now)
                    )
        finally:
            await engine.dispose()
        return len(rows)

    n = asyncio.run(_go())
    _write_snapshot(Path(args.snapshot), mapped)
    print(f"*** committed {n} products; deactivated {len(deltas['removed'])} removed; "
          f"snapshot updated. ***")


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
OPEN_QUESTIONS = """\
OPEN QUESTIONS for Banco-model integration (resolve before --commit):

1. CATEGORY MODEL.  ProductModel.category is a single flat String(100) today;
   there is NO categories table yet (Phase A of BANCO-CATEGORY-MANAGEMENT-PLAN
   is unbuilt). This importer sets category = Artemis level-2 and carries
   group + full breadcrumb in `tags`. DECISION NEEDED: (a) ship flat now and
   migrate to the categories table later, or (b) build the categories table
   first and import straight into Group->Category FK. The snapshot already
   stores banco_group + artemis_path so a later backfill is lossless.

2. BEHAVIOUR CLASS.  product_class / is_age_restricted are derived from the
   product NAME via catalog_taxonomy.classify() (FourTwenty-tuned). Artemis is
   a head/CBD shop so most items SHOULD be age-gated, but name-based rules will
   miss some. Treuhaender / Felix should review the 18+ set before go-live.
   Safer default option: force is_age_restricted=True for the whole headshop +
   cbd groups, then exception-list the open forms (oils/seeds/cosmetics).

3. IMAGES.  image_url is set to the live Artemis URL in dry-run. On --commit
   --with-images we copy bytes into MinIO (pos-products/{pid}/{img}.jpg) +
   a ProductImageModel row, exactly like pos_router._copy_external_image_to_storage.
   CONFIRM the MinIO bucket on banco_sandbox + whether hotlinking the Artemis
   URL temporarily is acceptable for a first pass.

4. PRICE = sales price only.  The list API gives salesPriceText (gross CHF).
   No cost / margin, no stock. cost stays NULL; stock_quantity defaults to 1
   (zero-perpetual: the shelf is the stock check). Confirm that's intended.

5. DESCRIPTIONS.  The list API has none; they live on each product page. A
   second enrichment pass (per linkUrl, EN with DE fallback, flag
   needs_translation) can fill description later via src/llm/run_llm. Out of
   scope for this importer.

6. SKU COLLISION.  We key on Artemis `identifier`. If banco_sandbox already has
   demo products with numeric SKUs, confirm no overlap, or namespace the
   imported SKU (e.g. "ART-21577"). Currently imported raw.
"""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Import the Artemis Luzern webshop catalog into Banco (dry-run by default).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=OPEN_QUESTIONS,
    )
    p.add_argument("--lang", default="en", choices=list(LANG_IDS),
                   help="source language (default en; de/fr available)")
    p.add_argument("--max-categories", type=int, default=None,
                   help="sample only N leaf categories (spread across groups) for a polite run")
    p.add_argument("--max-pages", type=int, default=200,
                   help="safety cap on pages per category (default 200)")
    p.add_argument("--sample", type=int, default=10,
                   help="how many mapped products to print in the report (default 10)")
    p.add_argument("--snapshot", default=str(DEFAULT_SNAPSHOT),
                   help="delta snapshot JSON path")
    p.add_argument("--write-snapshot", action="store_true",
                   help="persist the snapshot from a dry-run (default: only on --commit)")
    p.add_argument("--cache-dir", default=str(DEFAULT_CACHE),
                   help="on-disk HTTP cache dir (category pages/sitemaps); product API is never cached")
    p.add_argument("--no-cache", action="store_true", help="disable the HTTP cache")
    p.add_argument("--delay", type=float, default=0.3, help="polite delay between requests (s)")
    p.add_argument("--retries", type=int, default=4, help="HTTP retry attempts")
    p.add_argument("--commit", action="store_true",
                   help="GATED: actually write to the DB (needs --db-url). NOT a dry-run.")
    p.add_argument("--with-images", action="store_true",
                   help="(commit only) also download + store product images in MinIO")
    p.add_argument("--db-url", default=None,
                   help="SQLAlchemy async URL for --commit (postgresql+asyncpg://.../banco_sandbox)")
    p.add_argument("--notes", action="store_true",
                   help="print the image-storage design + open questions and exit")
    return p


def main():
    args = build_parser().parse_args()
    if args.notes:
        print(IMAGE_STORAGE_NOTE)
        print(OPEN_QUESTIONS)
        return
    run(args)


if __name__ == "__main__":
    main()
