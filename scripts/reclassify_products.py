"""reclassify_products.py — re-run classify() on imported products IN PLACE.

After refining the rules in src/services/catalog_taxonomy.py, re-derive the compliance
axis (product_class + is_age_restricted) for already-imported supplier products WITHOUT
re-crawling the webshop. Mirrors the Artemis importer's call exactly:
    classify(name, "CBD" if product_group == "CBD" else None)
Only touches product_class + is_age_restricted (NOT category/name/price); skips rows a
manager froze via sync_override. Idempotent.

⚠️ classify() is NAME-ONLY. On a LIVE catalog it CAN un-gate items whose 18+ came from the
   supplier CATEGORY, not the title (CBD flower/hash, context-classified nicotine) — this bit
   us on 2026-07-08. For any live compliance sweep:
     * use **--gate-only** (never REMOVES a gate — the safe sweep), and/or
     * use **--dry-run** first to review the flips before writing.

Run inside a banco container (scripts/ isn't mounted — docker cp it in first):
    docker exec -w /app -e PYTHONPATH=/app <container> \
        python /app/scripts/reclassify_products.py [PREFIX] [--gate-only] [--dry-run]
    PREFIX defaults to 'TAM-' (Artemis/Tamar); '' (empty) = ALL products.
"""
import argparse
import asyncio
from collections import Counter

from sqlalchemy import select

from src.db.database import get_db_session_context
from src.db.models.product_model import ProductModel
from src.services.catalog_taxonomy import classify


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("prefix", nargs="?", default="TAM-", help="SKU prefix ('' = ALL products)")
    ap.add_argument("--gate-only", action="store_true",
                    help="compliance-safe: never REMOVE a gate (skip any change that would un-gate)")
    ap.add_argument("--dry-run", action="store_true", help="report the flips, do NOT write")
    args = ap.parse_args()

    n = changed = ungate_skipped = 0
    cls_ct: Counter = Counter()
    age_total = 0
    flips: list[str] = []
    kept: list[str] = []

    async with get_db_session_context() as db:
        rows = (await db.execute(
            select(ProductModel).where(ProductModel.sku.like(f"{args.prefix}%"))
        )).scalars().all()
        for p in rows:
            n += 1
            if getattr(p, "sync_override", False):   # a manager froze this row — never clobber
                cls_ct[p.product_class] += 1
                age_total += 1 if p.is_age_restricted else 0
                continue
            hint = "CBD" if (p.product_group or "") == "CBD" else None
            _, cls, age = classify(p.name, hint)
            would_ungate = bool(p.is_age_restricted) and not bool(age)
            if args.gate_only and would_ungate:
                # keep the existing gate: a name-only pass can't SEE the supplier-category signal
                # that gated it. Safe sweep = only ADD gates, never remove one.
                ungate_skipped += 1
                if len(kept) < 25:
                    kept.append(f"  KEPT {p.product_class} 18+ (name→{cls})  {p.name[:50]}")
                cls_ct[p.product_class] += 1
                age_total += 1 if p.is_age_restricted else 0
                continue
            if p.product_class != cls or bool(p.is_age_restricted) != bool(age):
                if len(flips) < 25:
                    tag = "⚠UNGATE " if would_ungate else "        "
                    flips.append(f"  {tag}{p.product_class}->{cls} 18+{p.is_age_restricted}->{age}  {p.name[:48]}")
                p.product_class = cls
                p.is_age_restricted = bool(age)
                changed += 1
            cls_ct[cls] += 1
            age_total += 1 if age else 0

        if args.dry_run:
            await db.rollback()
        else:
            await db.commit()

    mode = ("DRY-RUN " if args.dry_run else "") + ("GATE-ONLY " if args.gate_only else "")
    print(f"\n=== {mode}RECLASSIFIED {n} '{args.prefix}' products — changed {changed}"
          + (f", kept-gated {ungate_skipped}" if args.gate_only else "") + " ===")
    print("BY CLASS:")
    for c, k in cls_ct.most_common():
        print(f"  {k:5}  {c}")
    print(f"18+ AGE-RESTRICTED: {age_total}")
    if kept:
        print("\nGATES KEPT (name-only would have un-gated — exactly why --gate-only exists):")
        for u in kept:
            print(u)
    if flips:
        print("\nSAMPLE OF CHANGES (⚠UNGATE = a gate was REMOVED; re-run with --gate-only to prevent):")
        for f in flips:
            print(f)


if __name__ == "__main__":
    asyncio.run(main())
