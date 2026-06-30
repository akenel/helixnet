#!/usr/bin/env python3
"""Artemis 'Papers & Co' ENRICHED LOAD — the thin enrichment → DB writer.

This is the COMMIT sibling of artemis_enrich_sample.py. Where the sample runner
builds a dry-run review HTML and writes NOTHING, this one runs the SAME enrichment
recipe per Papers & Co item and PERSISTS the full enriched record:

  * a `products` row  — name, clean Banco category + group, behaviour class, 18+ gate
        + auditable age_reason, price, a MINTED internal EAN-13 (barcode_is_internal=True),
        the normalized §6a attributes bag, the verbatim raw_facets, the enrichment_*
        provenance (confidence / flags / model+recipe), the source_* provenance
        (system/id/url/lang) + artemis_path, comma-joined tags, qr_url.
  * a `product_translations` EN row — name + description, provenance='source'
        (the feeder text; EN is Banco's primary language).

IDEMPOTENT by namespaced SKU `TAM-<id>` (matches the recipe). A re-run UPSERTS:
  * identity columns (barcode, barcode_is_internal, source_system/id) are INSERT-ONCE —
    a re-sync never re-mints the EAN or clobbers a manufacturer barcode added later.
  * a row with sync_override=True is left fully untouched (manager override wins).
  * REMOVED (a previously-loaded TAM- row not seen this run) is DEACTIVATED, never
    hard-deleted — but ONLY on a FULL run (no --max cap), because a capped sample is
    not an authority on what's gone. Capped runs skip deactivation (and say so).

REUSE: pull + enrichment come straight from artemis_enrich_sample.py (Artemis EN
languageId=3, Papers & Co group, the §6a detail-page rich-metadata pass) so the
loaded record is byte-identical to what the review HTML showed.

LLM (BYO-brain): the merchandising LLM step runs through src/llm/run_llm. Inside
helix-platform-sandbox on the box, BH_OLLAMA_KEY → Turbo gpt-oss:120b. The rules
half always runs; if the brain is unreachable the load still succeeds (descriptions
fall back to source text or a [LLM-pending] marker, exactly like the sample).

USAGE (run INSIDE the sandbox container — deployed code + Turbo key live there):
  /app/venv/bin/python /app/scripts/import/artemis_enrich_load.py --commit --max 50

  # dry-run (default): enrich + report counts, write NOTHING:
  /app/venv/bin/python /app/scripts/import/artemis_enrich_load.py --max 50

SAFETY: dry-run is the DEFAULT; --commit is the gate. Scope is Papers & Co only.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

# in-tree imports: repo root on path (for src.*) + this dir (for the sample runner)
_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Reuse the proven pull + enrichment from the sample runner (identical records).
import artemis_enrich_sample as sample  # pull_papers, enrich_all
try:
    from src.services.catalog_enrichment import mint_internal_ean13, SOURCE_PREFIX
except ImportError:  # box drop-beside fallback
    from catalog_enrichment import mint_internal_ean13, SOURCE_PREFIX  # type: ignore


# --------------------------------------------------------------------------- #
# Map an EnrichmentRecord -> the products row dict + the EN translation        #
# --------------------------------------------------------------------------- #
def record_to_rows(rec, now: datetime) -> tuple[dict, dict]:
    """Return (product_row, translation_en_row) plain dicts from an EnrichmentRecord."""
    src = rec.source
    # split the attributes bag: the §6a normalized keys go to `attributes`, the verbatim
    # source facets (nested under 'raw_facets' by the recipe) go to their own column.
    attrs = dict(rec.attributes or {})
    raw_facets = attrs.pop("raw_facets", None)

    # MINT the internal EAN-13 from the stable source identifier (deterministic → a
    # re-run yields the SAME code; insert-once so we never re-mint over a real barcode).
    seed = src.get("identifier")
    barcode = mint_internal_ean13(seed) if seed is not None else None

    name = (src.get("raw_name") or "").strip()[:255]
    price = Decimal(rec.price) if rec.price is not None else Decimal("0.00")
    needs_translation = "needs_translation" in (rec.flags or [])

    product = dict(
        sku=rec.sku,
        name=name,
        description=(rec.description or None),
        price=price,
        cost=None,
        stock_quantity=int(rec.stock_quantity or 1),
        category=(rec.category or None),
        product_group=(rec.group or None),
        tags=(",".join(rec.tags) if rec.tags else None),
        is_active=True,
        is_age_restricted=bool(rec.age_restricted),
        product_class=(rec.behavior_class or "standard"),
        age_reason=(rec.age_reason or None),
        # minted internal EAN-13 (insert-once)
        barcode=barcode,
        barcode_is_internal=True,
        # §6a rich metadata
        attributes=(attrs or None),
        raw_facets=(raw_facets or None),
        # enrichment provenance
        enrichment_confidence=(rec.confidence or None),
        enrichment_flags=(rec.flags or None),
        enrichment_meta=(rec.enriched_by or None),
        # source provenance / parity link
        source_system="artemis",
        source_id=(str(src.get("id")) if src.get("id") is not None else None),
        source_url=(src.get("url") or None),
        source_lang=(src.get("source_lang") or "en"),
        artemis_path=(src.get("artemis_path") or None),
        needs_translation=needs_translation,
        image_url=(src.get("image_url") or None),
        qr_url=None,
        # supplier link (un-namespaced source identifier)
        supplier_sku=(str(seed) if seed is not None else None),
        supplier_name="Artemis",
        last_sync_at=now,
    )
    translation = dict(
        lang="en",
        name=name,
        description=(rec.description or None),
        provenance="source",   # EN is the feeder's own text
        needs_review=False,
    )
    return product, translation


# Columns refreshed on a re-sync. Identity / insert-once columns (barcode,
# barcode_is_internal, source_system, source_id) are deliberately EXCLUDED so a
# re-run never re-mints the EAN or clobbers a later manufacturer barcode.
_UPDATE_COLS = [
    "name", "description", "price", "stock_quantity", "category", "product_group",
    "tags", "is_active", "is_age_restricted", "product_class", "age_reason",
    "attributes", "raw_facets", "enrichment_confidence", "enrichment_flags",
    "enrichment_meta", "source_url", "source_lang", "artemis_path",
    "needs_translation", "image_url", "qr_url", "supplier_sku", "supplier_name",
    "last_sync_at",
]


async def _persist(records, capped: bool, db_url: str | None) -> dict:
    from sqlalchemy import select, update as sa_update
    from src.db.models.product_model import ProductModel, ProductTranslationModel

    # Use the app's own engine/session when running inside the container; otherwise
    # honour an explicit --db-url / $BANCO_DB_URL.
    engine = None
    if db_url:
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        engine = create_async_engine(db_url)
        Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    else:
        from src.db.database import AsyncSessionLocal as Session  # the live app session

    now = datetime.now(timezone.utc)
    stats = {"inserted": 0, "updated": 0, "skipped_override": 0,
             "translations_inserted": 0, "translations_updated": 0,
             "deactivated": 0, "seen_skus": []}

    try:
        async with Session() as session:
            for rec in records:
                product_row, tr_row = record_to_rows(rec, now)
                sku = product_row["sku"]
                stats["seen_skus"].append(sku)

                existing = (await session.execute(
                    select(ProductModel).where(ProductModel.sku == sku)
                )).scalar_one_or_none()

                if existing is None:
                    prod = ProductModel(**product_row)
                    session.add(prod)
                    await session.flush()  # get prod.id for the translation FK
                    stats["inserted"] += 1
                    target = prod
                else:
                    if existing.sync_override:
                        stats["skipped_override"] += 1
                        continue
                    for col in _UPDATE_COLS:
                        setattr(existing, col, product_row[col])
                    stats["updated"] += 1
                    target = existing

                # upsert the EN translation skin keyed on (product_id, lang)
                existing_tr = (await session.execute(
                    select(ProductTranslationModel).where(
                        ProductTranslationModel.product_id == target.id,
                        ProductTranslationModel.lang == "en",
                    )
                )).scalar_one_or_none()
                if existing_tr is None:
                    session.add(ProductTranslationModel(product_id=target.id, **tr_row))
                    stats["translations_inserted"] += 1
                else:
                    existing_tr.name = tr_row["name"]
                    existing_tr.description = tr_row["description"]
                    existing_tr.provenance = tr_row["provenance"]
                    existing_tr.needs_review = tr_row["needs_review"]
                    stats["translations_updated"] += 1

            # DEACTIVATE removed — only on a FULL run (a capped sample is not authoritative).
            # Scope deactivation to exactly the groups this run pulled, so a headshop
            # run never deactivates Papers rows it simply didn't look at (and vice-versa).
            loaded_groups = sorted({rec.group for rec in records if rec.group})
            if not capped and stats["seen_skus"]:
                res = await session.execute(
                    sa_update(ProductModel)
                    .where(ProductModel.source_system == "artemis")
                    .where(ProductModel.product_group.in_(loaded_groups))
                    .where(ProductModel.sku.notin_(stats["seen_skus"]))
                    .where(ProductModel.sync_override.is_(False))
                    .where(ProductModel.is_active.is_(True))
                    .values(is_active=False, last_sync_at=now)
                )
                stats["deactivated"] = res.rowcount or 0

            await session.commit()
    finally:
        if engine is not None:
            await engine.dispose()
    return stats


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description="Artemis Papers & Co ENRICHED load (dry-run by default; --commit to write).")
    ap.add_argument("--commit", action="store_true",
                    help="GATED: write the enriched records to the Banco DB. Default = dry-run.")
    ap.add_argument("--max", type=int, default=50, help="cap products (default 50)")
    ap.add_argument("--lang", default="en", choices=list(sample.ai.LANG_IDS))
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--group", action="append", default=None,
                    help="Artemis level-1 group slug to load (repeatable). "
                         "e.g. --group headshop --group cbd --group vape-co. "
                         "Default: papers-co (the original Papers & Co subset).")
    ap.add_argument("--category", default=None,
                    help="narrow to leaves whose path contains this segment (e.g. bongs)")
    ap.add_argument("--no-detail", action="store_true",
                    help="skip the §6a detail-page rich-metadata fetch (faster, basics only)")
    ap.add_argument("--db-url", default=None,
                    help="async SQLAlchemy URL (default: the app's own engine inside the container)")
    args = ap.parse_args()

    capped = args.max is not None  # a --max cap means this run is NOT the full catalog

    http = sample.ai.Http(delay=args.delay, retries=4, cache_dir=None)
    groups = args.group if args.group else [sample.PAPERS_SLUG]
    raws = sample.pull_catalog(http, args.lang, args.max, group_slugs=groups,
                               cat_filter=args.category, with_detail=not args.no_detail)
    if not raws:
        print("No products pulled — aborting.", file=sys.stderr)
        sys.exit(2)

    records, meta = asyncio.run(sample.enrich_all(raws))

    print("\n" + "=" * 64)
    print(f" ENRICHED LOAD — Papers & Co  ({len(records)} products)")
    print("=" * 64)
    print(f" LLM         : {'ON ' + str(meta.get('llm_model')) if meta['llm_ok'] else 'RULES-ONLY (' + str(meta.get('llm_error')) + ')'}")
    print(f" LLM access  : {meta.get('llm_method')}")
    print(f" categories  : {sample._counter([r.category for r in records])}")
    print(f" age-restr.  : {sum(1 for r in records if r.age_restricted)}/{len(records)}")
    print(f" http reqs   : {http.n_requests}")

    if not args.commit:
        print("-" * 64)
        print(" DRY-RUN: nothing written. Re-run with --commit to persist.")
        print("=" * 64)
        return

    stats = asyncio.run(_persist(records, capped, args.db_url))
    print("-" * 64)
    print(" COMMITTED to banco DB:")
    print(f"   products inserted     : {stats['inserted']}")
    print(f"   products updated      : {stats['updated']}")
    print(f"   skipped (sync_override): {stats['skipped_override']}")
    print(f"   EN translations new   : {stats['translations_inserted']}")
    print(f"   EN translations upd   : {stats['translations_updated']}")
    print(f"   deactivated (removed) : {stats['deactivated']}"
          + ("  [capped run — deactivation skipped]" if capped else ""))
    print("=" * 64)


if __name__ == "__main__":
    main()
