# Banco — Category Management Plan (hierarchy + emoji CRUD)

*2026-06-28. Born out of the Product Sales report work: making the "By category" pills
tappable + giving each an emoji surfaced a real gap — **category management**. This is the
spec for where it goes. Not built yet beyond the server-owned emoji seam (see "Already shipped").*

*Pairs with: [BANCO-DAY-ONE-WISHLIST.md](BANCO-DAY-ONE-WISHLIST.md) · taxonomy source-of-truth `src/services/catalog_taxonomy.py`.*

---

## The problem (Angel, while testing TEST-B02)

- Categories today are **flat + free-text**. The catalog screen's category field is *"Pick
  existing or type new"* — so Felix can spin up a category on the fly. Good for freedom, bad
  for consistency and scale.
- **Emoji can-of-worms:** if every category shows an emoji but a typed-on-the-fly one has none
  (or a generic 🏷️), the wall "looks like hell." Some pretty, some bare.
- **Scale:** "I can see that if you've got 3,000 products." A flat list of 40+ sibling
  categories has no rollup, no way to collapse "all the smoking stuff." SAP solved this with a
  **product/material hierarchy** — powerful but over-complex. We want the *sorting power*
  without the consultant.

## The decision

1. **Emoji is mandatory + consistent + server-owned** — every category always shows an
   intentional icon, including ones typed on the fly. (DONE — see below.)
2. **Categories become a managed hierarchy**, not free-text strings. Two levels is enough:
   **Group → Category** (e.g. *Smoking* → Papers, Lighters, Grinders, Pipes; *CBD* → CBD & Hemp,
   Edibles, Creams; *Café* → Drinks, Food; *Retail* → Merch, Accessories).
3. **A Category CRUD** (manager tool) manages the tree + picks an emoji from a curated pool
   (~120 unique). Maintaining categories is itself a first-class tool, not a side effect of
   creating a product.

## ✅ Already shipped (the seam) — 2026-06-28

Server-owned emoji so nothing here is wasted when the table lands:

- `src/services/catalog_taxonomy.py` → `category_emoji(category, override=None)`:
  1. `override` wins (the future CRUD stores a chosen emoji → passes it here),
  2. curated map for known categories (skeleton + common aliases),
  3. **stable deterministic** pick from `_EMOJI_POOL` (~120) for anything else — same name → same
     emoji forever, never blank.
- The product-sales report + `/reports/category-sales` endpoints return `emoji` per category;
  the template just displays it. **When the Category table arrives, only step 1 changes** —
  callers and UI stay put.

## The build (later — phased, don't over-engineer)

- **Phase A — `categories` table.** `id, name, parent_id (null=root), emoji, sort_order, active`.
  Self-referencing → arbitrary depth, but **use 2 levels** (group → category). Seed from the
  current `CATEGORIES` skeleton, grouped.
- **Phase B — Products reference `category_id`.** Migrate free-text `product.category` → FK.
  Keep a denormalized display string to avoid a big-bang. Backfill via the existing classifier
  (`reclassify_reference.py`).
- **Phase C — Category CRUD UI** (manager-gated): manage the tree (add/rename/move/retire),
  reorder, pick emoji from the pool. `override` feeds `category_emoji`.
- **Phase D — Reports + catalog roll up by group.** "By category" pills become collapsible
  *group → category*; product list filters by group or leaf. Falls out almost free once the
  tree exists.

## Guardrails (so we don't rebuild SAP)

- **Two levels in practice.** The table *can* nest deeper; the UI shouldn't encourage it.
- **Category = merchandising only.** It does NOT drive money/law — that's **class** (controlled:
  VAT, age-gate, compliance), and class stays separate and locked. Don't entangle the two.
- **Free-text stays as a fallback**, but a typed category should drop into "Other / unsorted"
  under a root until a manager files it — never a silent new root.
- Standard term: SAP calls this a **product hierarchy / material group**. Ours is a lighter
  **category tree**. (Flag for Angel's vocabulary: "hierarchy" + "rollup" are the real words.)

---

*"Categories is gonna have what we call a hierarchy — kind of like the product hierarchy. SAP did
that, but it was pretty complex. We need something like that for 3,000 products." — Angel, 2026-06-28*
