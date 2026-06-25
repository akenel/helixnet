"""reclassify_reference.py — re-runnable reference-catalogue enricher (BL-96).

Maps the 7,272 FourTwenty reference items onto our skeleton: our_category + our_class +
age_restricted, via src/services/catalog_taxonomy.classify(). Idempotent — refine the rules in
catalog_taxonomy.py and re-run as often as you like ("mass update"). Prints a report + the 18+
review list so the mapping quality is visible, not assumed.

Run inside a banco container:
    docker exec -i helix-platform-banco-staging python scripts/reclassify_reference.py
"""
import asyncio
from collections import Counter

from sqlalchemy import select

from src.db.database import get_db_session_context
from src.db.models.reference_product_model import ReferenceProductModel
from src.services.catalog_taxonomy import classify, PRODUCT_CLASSES


async def main() -> None:
    cat_counts: Counter = Counter()
    cls_counts: Counter = Counter()
    age_samples: list[str] = []
    age_total = 0
    n = 0

    async with get_db_session_context() as db:
        rows = (await db.execute(select(ReferenceProductModel))).scalars().all()
        for r in rows:
            cat, cls, age = classify(r.title, r.category, r.raw)
            r.our_category, r.our_class, r.age_restricted = cat, cls, age
            cat_counts[cat] += 1
            cls_counts[cls] += 1
            if age:
                age_total += 1
                if len(age_samples) < 40:
                    age_samples.append(f"  [{cls}] {r.title}")
            n += 1
        await db.commit()

    print(f"\n=== RECLASSIFIED {n} reference items ===")
    print("\nBY CATEGORY:")
    for c, k in cat_counts.most_common():
        print(f"  {k:5}  {c}")
    print("\nBY CLASS:")
    for c, k in cls_counts.most_common():
        flag = PRODUCT_CLASSES.get(c, {}).get("age_restricted")
        print(f"  {k:5}  {c}  (18+={flag})")
    print(f"\n=== 18+ AGE-RESTRICTED: {age_total} items — FELIX REVIEW LIST (first 40) ===")
    for s in age_samples:
        print(s)
    print("\n(re-run after refining rules in src/services/catalog_taxonomy.py)")


if __name__ == "__main__":
    asyncio.run(main())
