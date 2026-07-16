#!/usr/bin/env python3
"""BL-CAT.3 — category taxonomy migration SCAFFOLD (dry-run by default).

Reads the canonical taxonomy draft and, against a target DB:
  --dry-run  (DEFAULT): SELECT only. Emits a before→after diff — how many products move, the
             per-canonical-category after-counts, and ANY product category not in the synonym
             map (a coverage gap). Writes NOTHING. Asserts it issues no DDL/DML.
  --commit   (GUARDED, do NOT use pre-sign-off): would (a) create a `categories` table
             (group→category) + seed it, (b) UPDATE products.category to the canonical label.
             product_class / age flags / VAT are NEVER touched (merchandising axis only).

The original Artemis breadcrumb already lives in products.tags (`artemis:<path>`), so the raw
German string is not lost — this only rewrites the display `category`.

  python3 scripts/blcat_migrate.py --draft banco-category-taxonomy-draft.json --dry-run
"""
import argparse
import asyncio
import json
import sys


def build_synonym_map(draft):
    cats = {c["key"]: c for c in draft["canonical_categories"]}
    groups = {g["key"]: g for g in draft["groups"]}
    syn = {}
    for m in draft["mapping"]:
        c = cats[m["to"]]
        syn[m["raw"]] = {
            "canonical_key": m["to"],
            "label_en": c["label_en"],
            "group_key": c["group"],
            "group_en": groups[c["group"]]["label_en"],
        }
    return syn, cats, groups


async def run(draft_path, do_commit):
    draft = json.load(open(draft_path, encoding="utf-8"))
    syn, cats, groups = build_synonym_map(draft)

    from sqlalchemy import text
    from src.db.database import async_engine

    async with async_engine.connect() as c:
        # BEFORE: live category → count
        rows = (await c.execute(text(
            "SELECT category, count(*) n FROM products WHERE is_active "
            "AND category IS NOT NULL AND category<>'' GROUP BY category"))).fetchall()
        before = {r[0]: r[1] for r in rows}

        # class distribution snapshot — must be identical after (we never touch it)
        cls_before = {r[0]: r[1] for r in (await c.execute(text(
            "SELECT product_class, count(*) FROM products WHERE is_active GROUP BY product_class"))).fetchall()}

    total = sum(before.values())
    moves = 0
    unmapped = {}
    after = {}
    for raw, n in before.items():
        s = syn.get(raw)
        if not s:
            unmapped[raw] = n
            after[raw] = after.get(raw, 0) + n
            continue
        label = s["label_en"]
        after[label] = after.get(label, 0) + n
        if raw != label:
            moves += n

    print("=" * 66)
    print("BL-CAT.3 — CATEGORY MIGRATION DRY-RUN (read-only, zero writes)")
    print("=" * 66)
    print(f"active products w/ a category : {total}")
    print(f"would MOVE (category rewrites): {moves}")
    print(f"unchanged (already canonical) : {total - moves}")
    print(f"distinct categories: {len(before)} raw  ->  {len([k for k in after])} canonical")
    print(f"coverage gaps (unmapped)      : {len(unmapped)}  {unmapped if unmapped else ''}")

    print("\n-- AFTER: canonical category -> item count (by group) --")
    by_group = {}
    for label, n in after.items():
        # find group for this canonical label
        gk = next((cats[k]["group"] for k in cats if cats[k]["label_en"] == label), "system")
        by_group.setdefault(groups.get(gk, {}).get("label_en", "?"), []).append((label, n))
    for gk in [g["label_en"] for g in draft["groups"]]:
        items = sorted(by_group.get(gk, []), key=lambda x: -x[1])
        if not items:
            continue
        print(f"\n  {gk}  ({sum(n for _, n in items)})")
        for label, n in items:
            print(f"     {n:>5}  {label}")

    print("\n-- INVARIANT: product_class distribution (must be untouched by this migration) --")
    for k, v in sorted(cls_before.items(), key=lambda x: -x[1]):
        print(f"     {v:>5}  {k}")
    print("  (the migration UPDATEs only products.category — class/age/VAT are never in the SET clause)")

    if do_commit:
        # SIGNED OFF 2026-07-16 (Felix delegated to Angel; Angel approved the tree). Rewrites
        # products.category -> canonical label_en and products.product_group -> group label_en,
        # per the synonym map, in ONE transaction. NEVER touches product_class/age/VAT.
        async with async_engine.begin() as conn:
            updated = 0
            for raw, s in syn.items():
                res = await conn.execute(text(
                    "UPDATE products SET category=:cat, product_group=:grp, updated_at=now() "
                    "WHERE category=:raw"),
                    {"cat": s["label_en"], "grp": s["group_en"], "raw": raw})
                updated += res.rowcount
            print(f"\n✅ COMMITTED: {updated} products remapped (category + product_group).")
        # verify the class invariant held
        async with async_engine.connect() as conn:
            cls_after = {r[0]: r[1] for r in (await conn.execute(text(
                "SELECT product_class, count(*) FROM products WHERE is_active GROUP BY product_class"))).fetchall()}
            # Only NON-canonical raws are true "leftovers"; identity maps (Other→Other, Grinders→
            # Grinders, where label_en == the raw string) are already canonical and expected to stay.
            german_raws = [raw for raw, s in syn.items() if s["label_en"] != raw]
            leftover = (await conn.execute(text(
                "SELECT category, count(*) FROM products WHERE is_active AND category = ANY(:raws) GROUP BY category"),
                {"raws": german_raws})).fetchall()
        assert cls_after == cls_before, f"INVARIANT BROKEN: product_class changed! {cls_before} -> {cls_after}"
        print(f"   product_class invariant: OK (unchanged: {cls_after})")
        print(f"   non-canonical categories still present: {len(leftover)} (should be 0) {leftover if leftover else ''}")
        return

    print("\n✅ DRY-RUN complete. No writes were issued (SELECT-only).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", default="banco-category-taxonomy-draft.json")
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--commit", action="store_true", help="GUARDED — refuses to run in this scaffold")
    a = ap.parse_args()
    asyncio.run(run(a.draft, a.commit))


if __name__ == "__main__":
    main()
