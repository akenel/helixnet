# BL-CAT.4 — Category Funnel Plan (code changes, PLAN not ship)

*Authored 2026-07-16. Ships ONLY after Felix signs off the tree (BL-CAT.2 sheet), through the
normal gated ladder (`make deploy`, backup-gated, re-probed). This doc is the plan; nothing here
is committed yet.*

**Goal:** stop the leak. The 61-category mess happened because **four writer paths each invent
their own category vocabulary** and there's **no `categories` table** — `products.category` is free
text. Fixing the data (BL-CAT.3 migration) without fixing the writers means the mess grows back.
This plan funnels every writer onto the **one canonical tree** (English hub, 9 groups / 49 categories).

---

## 0. The canonical source of truth — a `categories` table

Per [[banco-category-management-plan]]. Create `categories (key, group_key, label_en, sort, active)`
seeded from `docs/banco-category-taxonomy-draft.json` → `canonical_categories`. `products.category`
becomes a FK-ish reference to `categories.key` (keep the string column for now; validate against the
table). New categories are a deliberate admin act, not a typo in a text field. **This is the keystone
— without it, every fix below is a patch that rots.**

## 1. Label coverage — `POS_CATEGORY_LABELS`  (`src/static/pos/pos-i18n.js:6693`)

Today it matches by exact string and has **no `en` block** (that's why 49 raw German strings render
raw). Add:
- an **`en` block** mapping every canonical `label_en` to itself (so the fallback is English, not German);
- **de / fr / it** translations for all **49** canonical labels (nl/es later — same batch move);
- **parity gate**: each canonical key × N langs, or it renders raw (the BL-28/29/30 bug class).

The map keys become the **canonical labels**, not the German slugs — so once the migration rewrites
`products.category`, the labels resolve cleanly in every language.

## 2. The four writer paths → canonical vocabulary

**(a) Vision / snap-fill prompt** — `src/services/vision.py:270`
Currently: `"category" one of: CBD, Flower, Vape, Accessories, Grow, Drinks, Cosmetics, Other` — an
**ad-hoc list that doesn't match the tree** ("Flower"/"Cosmetics"/"Drinks" are drift). Replace with
the **canonical category list** (or the 9 group names for a coarse first guess), and **specify output
language = English** (the hub). Add the "please check" nudge (spec §7). This is the biggest ongoing
leak — every snap-fill and born-once item flows through here.

**(b) Adopt path** — `src/routes/pos_router.py:1110`
`category=(ref.our_category or ref.category or "").strip() or "Other"` — writes a supplier's raw
category straight through. **Canonicalize it through the synonym map** before writing (reuse the
BL-CAT.3 `build_synonym_map`), and default to **"Unsorted"** (the landing zone), not "Other".

**(c) Quick-add / on-the-fly** — new/counter items must land in **"Unsorted"** (the deliberate landing
zone, per the `On the fly` mapping note), never a free-typed string. A manager sorts them later in the
Cockpit (BL-98 bench).

**(d) Enrichment map** — `src/services/catalog_taxonomy.py` + `catalog_enrichment.py`
Align its internal `CATEGORIES` / consolidation vocabulary to the canonical tree so the enrichment
pass and the migration agree. One vocabulary, four consumers.

## 3. `ensure_description` honesty — `src/services/product_translations.py:116`

Today `src_lang = product.source_lang or "en"` — it **assumes English** and can mint an *authoritative*
`en` skin from text that's actually German (the `source_lang` lies 'en' everywhere — see
[[banco-category-language-mess]]). Change: **don't stamp an authoritative `en` translation from
unverified text** — flag `needs_review`, and **stamp `source_lang` honestly** (detect or leave null,
never claim 'en' for German copy). This stops the description side of the same disease.

## 4. Search — category synonym layer

Category "Feuerzeuge" does nothing for an English "lighter" search. The name-synonym layer shipped
(BL-101); **categories never got one.** After the migration the canonical label *is* English, but keep
a **category synonym map** (de/fr/it → canonical) so a French "briquet" or German "feuerzeug" still
finds the **Lighters** shelf. Small, reuses the BL-101 synonym pattern.

---

## Order of operations (post-sign-off, gated ladder)

1. **Seed** the `categories` table (canonical tree). *[migration]*
2. **Migrate** `products.category` → canonical labels (BL-CAT.3 `--commit`, after Felix's final ticks
   are folded into the JSON). Tags already hold the `artemis:` breadcrumb — lossless. *[migration, backup-gated]*
3. **Ship the writer fixes** (§1–§4) so the mess can't regrow. *[code]*
4. **Verify:** re-run the BL-CAT.3 dry-run → 0 moves (everything already canonical), 0 gaps; snap-fill a
   test item → lands in a canonical category; search "lighter"/"briquet" → Lighters.

**Invariant, asserted at every step:** `product_class` / age-flags / VAT are the *separate locked axis*
and are **never** in any `SET` clause here. Category = the shelf sign only.

## Dry-run evidence (BL-CAT.3, prod read-only 2026-07-16)

`docs/testing/reports/prod/blcat3-migration-dryrun-2026-07-16.txt`:
5,175 active products · **4,984 would move** · **0 coverage gaps** · 61 raw → 49 canonical ·
product_class distribution unchanged (4,057 standard / 802 tobacco_nicotine / …).
