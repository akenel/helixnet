"""reclassify_products.py — re-run classify() on imported products IN PLACE.

After refining the rules in src/services/catalog_taxonomy.py, re-derive the compliance
axis (product_class + is_age_restricted) for already-imported supplier products WITHOUT
re-crawling the webshop. Mirrors the Artemis importer's call exactly:
    classify(name, "CBD" if product_group == "CBD" else None)
so the result matches a fresh import. Only touches product_class + is_age_restricted
(NOT category/name/price); skips rows a manager froze via sync_override. Idempotent.

Run inside a banco container (scripts/ isn't mounted — docker cp it in first):
    docker exec -w /app -e PYTHONPATH=/app <container> python /app/scripts/reclassify_products.py [SKU_PREFIX]
    (SKU_PREFIX defaults to 'TAM-' = Artemis/Tamar)
"""
import asyncio
import sys
from collections import Counter

from sqlalchemy import select

from src.db.database import get_db_session_context
from src.db.models.product_model import ProductModel
from src.services.catalog_taxonomy import classify


async def main() -> None:
    prefix = sys.argv[1] if len(sys.argv) > 1 else "TAM-"
    n = changed = 0
    cls_ct: Counter = Counter()
    age_total = 0
    flips: list[str] = []

    async with get_db_session_context() as db:
        rows = (await db.execute(
            select(ProductModel).where(ProductModel.sku.like(f"{prefix}%"))
        )).scalars().all()
        for p in rows:
            n += 1
            if getattr(p, "sync_override", False):   # a manager froze this row — never clobber
                cls_ct[p.product_class] += 1
                age_total += 1 if p.is_age_restricted else 0
                continue
            hint = "CBD" if (p.product_group or "") == "CBD" else None
            _, cls, age = classify(p.name, hint)
            if p.product_class != cls or bool(p.is_age_restricted) != bool(age):
                if len(flips) < 25:
                    flips.append(f"  {p.product_class}->{cls} 18+{p.is_age_restricted}->{age}  {p.name[:52]}")
                p.product_class = cls
                p.is_age_restricted = bool(age)
                changed += 1
            cls_ct[cls] += 1
            age_total += 1 if age else 0
        await db.commit()

    print(f"\n=== RECLASSIFIED {n} '{prefix}' products — changed {changed} ===")
    print("BY CLASS:")
    for c, k in cls_ct.most_common():
        print(f"  {k:5}  {c}")
    print(f"18+ AGE-RESTRICTED: {age_total}")
    if flips:
        print("\nSAMPLE OF CHANGES:")
        for f in flips:
            print(f)


if __name__ == "__main__":
    asyncio.run(main())
