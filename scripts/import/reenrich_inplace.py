#!/usr/bin/env python3
"""In-place RE-ENRICH of already-loaded catalog rows — the §6e "fix the recipe, re-run
is the mass update" engine, applied to the rows we already have (no Artemis pull, no LLM).

WHY (not a fresh pull): the merchandising CATEGORY and the LAW-axis AGE gate are
DETERMINISTIC functions of fields we already store on every product — `product_group`,
`artemis_path` (the breadcrumb), and `name`. So when the recipe's consolidation tables /
age policy change, we re-derive category + age + age_reason DIRECTLY from the stored
fields and UPDATE in place. This re-enriches EXACTLY the existing rows (no round-robin
set-drift from a re-pull), needs no network, and needs no brain (the new allowlists make
the RULE resolve every category confidently — the LLM only ever drafted descriptions,
which already exist as provenance='source').

IDEMPOTENT + delta-aware: a row already on the right category/age is left untouched; a
row with sync_override=True (a manager edit) is skipped entirely.

USAGE (run INSIDE helix-platform-sandbox — the app session points at banco_sandbox):
  /app/venv/bin/python /app/scripts/import/reenrich_inplace.py            # dry-run (default)
  /app/venv/bin/python /app/scripts/import/reenrich_inplace.py --commit   # write

SAFETY: dry-run is the DEFAULT; --commit is the gate. Scope = the TAM-* catalog namespace.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))

try:
    from src.services.catalog_enrichment import map_category_rule, classify_compliance
except ImportError:  # box drop-beside fallback
    from catalog_enrichment import map_category_rule, classify_compliance  # type: ignore


def _segments(artemis_path: str | None, group_slug_fallback: str) -> list[str]:
    segs = [s for s in (artemis_path or "").split("/") if s]
    return segs or [group_slug_fallback]


async def run(commit: bool, sku_like: str) -> dict:
    from sqlalchemy import select
    from src.db.database import AsyncSessionLocal
    from src.db.models.product_model import ProductModel

    now = datetime.now(timezone.utc)
    stats = {"seen": 0, "cat_changed": 0, "age_changed": 0, "updated": 0,
             "skipped_override": 0, "unchanged": 0,
             "cat_before": {}, "cat_after": {}, "age_before": 0, "age_after": 0,
             "samples": []}

    async with AsyncSessionLocal() as session:
        rows = (await session.execute(
            select(ProductModel).where(ProductModel.sku.like(sku_like))
        )).scalars().all()

        for p in rows:
            stats["seen"] += 1
            stats["cat_before"][p.category] = stats["cat_before"].get(p.category, 0) + 1
            stats["age_before"] += 1 if p.is_age_restricted else 0

            group = p.product_group or ""
            segs = _segments(p.artemis_path, group.lower())
            # group_slug for the class hint = first path segment (e.g. 'cbd')
            group_slug = segs[0] if segs else ""

            catmap = map_category_rule(group, segs)
            # Mirror apply_llm: a CONFIDENT rule mapping (llm_needed=False) is authoritative
            # and collapses junk; an AMBIGUOUS one (llm_needed=True) must NOT clobber the
            # existing category with a raw provisional slug — the prior LLM already resolved
            # it into the allowed set, so that value stands (we have no brain here to re-pick).
            confident = not catmap["llm_needed"]
            new_cat = catmap["category"] if confident else (p.category or catmap["category"])
            effective_cat = new_cat  # what the age carve-out sees
            comp = classify_compliance(p.name or "", group, group_slug, category=effective_cat)
            new_age = bool(comp["age_restricted"])
            new_reason = comp["age_reason"]

            stats["cat_after"][new_cat] = stats["cat_after"].get(new_cat, 0) + 1
            stats["age_after"] += 1 if new_age else 0

            if p.sync_override:
                stats["skipped_override"] += 1
                continue

            changed = False
            if confident and new_cat and new_cat != p.category:
                if len(stats["samples"]) < 25:
                    stats["samples"].append((p.category, new_cat, p.name or ""))
                p.category = new_cat
                stats["cat_changed"] += 1
                changed = True
            if new_age != bool(p.is_age_restricted):
                p.is_age_restricted = new_age
                p.age_reason = new_reason
                stats["age_changed"] += 1
                changed = True
            elif new_reason and new_reason != p.age_reason:
                p.age_reason = new_reason
                changed = True

            if changed:
                p.last_sync_at = now
                stats["updated"] += 1
            else:
                stats["unchanged"] += 1

        if commit:
            await session.commit()
        else:
            await session.rollback()
    return stats


def _fmt(d: dict) -> str:
    return ", ".join(f"{k}={v}" for k, v in sorted(d.items(), key=lambda kv: -kv[1]))


def main() -> None:
    ap = argparse.ArgumentParser(description="In-place re-enrich (category + age) of TAM-* rows.")
    ap.add_argument("--commit", action="store_true", help="GATED: write changes. Default = dry-run.")
    ap.add_argument("--sku-like", default="TAM-%", help="SKU filter (default TAM-%%).")
    args = ap.parse_args()

    stats = asyncio.run(run(args.commit, args.sku_like))

    print("\n" + "=" * 64)
    print(f" IN-PLACE RE-ENRICH ({stats['seen']} products, sku LIKE {args.sku_like})")
    print("=" * 64)
    print(f" distinct categories : {len(stats['cat_before'])} -> {len(stats['cat_after'])}")
    print(f" 18+ count           : {stats['age_before']} -> {stats['age_after']}")
    print(f" category changed    : {stats['cat_changed']}")
    print(f" age changed         : {stats['age_changed']}")
    print(f" rows updated        : {stats['updated']}")
    print(f" skipped (override)  : {stats['skipped_override']}")
    print(f" unchanged           : {stats['unchanged']}")
    print("-" * 64)
    print(" AFTER categories    :", _fmt(stats["cat_after"]))
    if stats["samples"]:
        print("-" * 64)
        print(" sample collapses (old -> new):")
        for old, new, name in stats["samples"]:
            print(f"   {str(old)[:34]:34} -> {new:20}  [{name[:30]}]")
    print("=" * 64)
    if not args.commit:
        print(" DRY-RUN: nothing written. Re-run with --commit to persist.")
    else:
        print(" COMMITTED to the banco DB.")


if __name__ == "__main__":
    main()
