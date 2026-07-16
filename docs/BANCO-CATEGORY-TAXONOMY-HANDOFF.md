# Banco — Category Taxonomy Cleanup (BL-CAT) · HANDOFF

**Authored 2026-07-15 by Tig, from the prod audit of 2026-07-14.**
**Status: PROPOSAL. Nothing here touches prod until Felix signs off on the tree.**

This is a self-contained task packet for the second terminal. Read this file, then the
memory `banco-category-language-mess`, then execute the task list at the bottom. **Stop at
the sign-off gate — do not deploy, do not write prod.**

---

## 1. THE PROBLEM IN ONE PARAGRAPH

The Artemis importer named every category by title-casing the **German URL slug** off the
German sitemap (`/de/aufbewahrung/` → category "Aufbewahrung"). So prod has **61 category
strings, 49 of them raw German** the translation map has never heard of (`POS_CATEGORY_LABELS`
matches by exact string and has no `en` block). "Papers" is scattered across **10** categories
in two languages. Descriptions are ~96% fine — **this is a category problem, not a data
catastrophe.** Underneath it: **four competing category vocabularies** (importer slugs,
`catalog_taxonomy.CATEGORIES`, `catalog_enrichment` consolidation, the vision-prompt list) and
**no categories table** — `products.category` is free text. Full detail + file:line in the
memory file.

## 2. THE FIX SHAPE (the doctrine, already agreed)

- **ONE canonical 2-level tree** (Group → Category), **English as the hub** — DE/FR/IT/NL/ES are
  *translations* of the canonical category, never separate category *values*.
- The 61 messy strings become **synonyms** that map INTO the canonical tree. Lossless: the
  original Artemis breadcrumb already lives in `products.tags` (`artemis:<path>`).
- **Category = merchandising ONLY.** The 18+/VAT axis (`product_class`) is separate and locked —
  this remap must NOT touch age flags or tax class.

## 3. THE DRAFT TREE (9 groups, ~50 categories) — for Felix to react to

Machine-readable version (the executor consumes this): **`docs/banco-category-taxonomy-draft.json`.**
Counts are live prod item counts; they sum to exactly 5,170 (validated).

| Group (items) | Canonical categories |
|---|---|
| **CBD & Hemp** (396) | CBD Flower · Extracts & Oils · Edibles · Cosmetics · Creams & Topicals |
| **Papers & Rolling** (598) | Rolling Papers · Filters & Tips · Blunts & Wraps · Cones & Tubes · Rolling Trays · Rolling & Filling Machines · Cigarette Tubes · Rolling Accessories |
| **Smoking Gear** (1,364) | Bongs · Pipes · Grinders · Bong & Pipe Accessories · Lighters · Ashtrays · Scales · Presses · Snuff Accessories · Storage & Stash · Dab & Concentrate Gear |
| **Vape** (1,888) | E-Liquids · Coils & Pods · Vape Devices · Prefilled & Disposables · Vaporizers · Nicotine Shots · Vape Accessories |
| **Tobacco & Shisha** (379) | Tobacco · Shisha Tobacco · Shishas & Hookahs · Shisha Bowls · Shisha Coal · Shisha Hoses |
| **Cafe & Food** (47) | Food & Snacks · Cafe |
| **Lifestyle & Gifts** (300) | Decor · Incense & Smudge · Apparel & Textiles · Gifts & Gadgets · Entertainment & Games · Knives & Tools · Packaging & Bags |
| **Grow & Lab** (41) | Drug Testing · Grow Supplies |
| **Unsorted / System** (157) | Accessories (general) · Unsorted · Other |

The full 61→canonical mapping (every raw string, its count, its target, and a `verify` note
where the German slug is ambiguous) is the `mapping` array in the JSON.

## 4. THE BUSINESS DECISIONS — these are FELIX's calls, not the executor's

These are the only judgement calls; everything else is mechanical. Surface them in the review
sheet as the questions Felix answers:

1. **"Marijuana" (203 items)** — legally CBD/hemp flower in CH. Display name: **"CBD Flower"**
   (recommended), "Hemp Flower", or keep "Marijuana"? His shop, his shelf sign.
2. **"Oel Dabbing" (157)** — the one real split risk: is it CBD **oils/extracts** (a product) or
   **dab rigs/gear** (headshop)? Likely both → may need splitting into two categories.
3. **Group count** — 9 groups. Felix may want fewer (e.g. fold Grow & Lab into Lifestyle, or
   Tobacco into Shisha). Let him merge on the sheet.
4. **"Zubehoer" (74 generic accessories)** — the biggest junk bucket. Accept "Accessories
   (general)" for now, or is it worth re-splitting by product during the migration?
5. **Stash Safes ("Verstecktresore", 31)** — folded into Storage & Stash, or a fun standalone
   retail category worth its own shelf?
6. **Tobacco vs Shisha grouping** — kept together as "Tobacco & Shisha". Split if he prefers.

## 5. WHY THIS ALSO FIXES A SEARCH BUG

Category "Feuerzeuge" does nothing for an English user typing "lighter" — the synonym layer
shipped for product NAMES (BL-101) but categories never got one. Same disease, second seal.
The canonical tree + label map closes it.

---

## 6. EXECUTOR TASK LIST (BL-CAT) — ordered, STOP at the gate

**All of this is pre-sign-off and safe: read-only against prod, build artifacts locally, NO
prod writes, NO deploy.** Owner: 🐯.

- **✅ BL-CAT.1 — DONE 2026-07-16.** All 14 `verify` rows spot-checked against live `banco_prod`
  (read-only). **4 real mis-mappings caught + corrected in the JSON:** Oel Dabbing (157) CBD-oils→
  **dab gear** (Smoking Gear); Raw Produkte (9) papers→**cones**; Vape Co (17) accessories→**prefilled**
  (CBD vape pens); Treats (7) CBD-edibles→**system** (giveaway TREAT-* items). 10 others confirmed;
  every row annotated `verified:`. Group counts updated (CBD 396→232, Smoking Gear 1364→1521, System 157→164).
- **✅ BL-CAT.2 — DONE 2026-07-16 — `docs/testing/banco/BANCO-CATEGORY-TAXONOMY-REVIEW.html`.** The Felix
  review sheet: 9 groups × 49 categories, each with live item count + 3 real product names, the 4 corrections
  called out, and 7 tickable decisions (§4 + a bonus Books&Media rename). 5,175/5,170 mapped, 0 unmapped
  categories. Builder: `scripts/blcat_build_review.py` (reads the JSON + live samples). **← ready for Angel to walk Felix.**
- **BL-CAT.1 (orig) — Verify the ambiguous mappings.** For every `verify: true` row in the JSON, pull
  ~5 real product names from `banco_prod` (read-only, in-container: `docker exec
  helix-platform-banco …`) and confirm the bucket. Correct the JSON where the sample disagrees.
  Especially "Oel Dabbing" (split?), "Marijuana", "Tabak", "Zubehoer". Reuse the audit scripts
  in this session's scratchpad (`lang_audit.py` / `lang_audit2.py`) as the pattern.
- **BL-CAT.2 — Build the Felix review sheet** (Angel's favourite method: a self-contained HTML
  test-script, per `method-html-test-script`). Show the 9 groups, each canonical category with
  its item count + 3 sample real product names, and the 6 decisions from §4 as explicit
  checkbox/choice questions. Put it in `docs/testing/banco/`. This is what Angel walks Felix
  through. **← the real deliverable.**
- **✅ BL-CAT.3 — DONE 2026-07-16 — `scripts/blcat_migrate.py` (dry-run default, `--commit` guarded/disabled).**
  Ran read-only against prod: **5,175 products · 4,984 would move · 0 coverage gaps · 61 raw → 49 canonical**;
  product_class distribution asserted unchanged (migration only rewrites `products.category`). Report:
  `docs/testing/reports/prod/blcat3-migration-dryrun-2026-07-16.txt`. The `--commit` path is intentionally
  disabled pre-sign-off.
- **✅ BL-CAT.4 — DONE 2026-07-16 — `docs/BANCO-CATEGORY-FUNNEL-PLAN.md`.** Code-funnel plan with real
  file:line targets: categories table + seed; `POS_CATEGORY_LABELS` en-block + 49-label parity
  (`pos-i18n.js:6693`); the 4 writer paths (vision prompt `vision.py:270`, adopt `pos_router.py:1110`,
  quick-add→Unsorted, enrichment map); `ensure_description` source_lang honesty (`product_translations.py:116`);
  category search-synonym layer. Ordered post-sign-off, gated, class/age/VAT invariant asserted.
- **BL-CAT.3 (orig) — Scaffold the migration as DRY-RUN ONLY.** A Python script (per rule 11) that
  reads the JSON and would: (a) create a `categories` table (Group→Category, per
  `banco-category-management-plan`) and seed it from the canonical list; (b) remap every
  product's free-text `category` via the synonym map; (c) emit a **before→after diff report**
  (how many products move, any raw string that matches nothing). **Run it `--dry-run` against a
  prod COPY or sandbox only. Do NOT `--commit` anything.** Age/VAT class untouched — assert it.
- **BL-CAT.4 — Write the code-funnel plan** (plan, don't ship): add an `en` block +
  full coverage to `POS_CATEGORY_LABELS`; force the four writer paths onto the canonical
  vocabulary — the vision/snap-fill prompt (`src/services/vision.py`, kill `Flower`/`Cosmetics`
  drift + specify output language), the adopt path (`pos_router.py` ~999), quick-add, and the
  enrichment map; make `ensure_description` stop minting an authoritative `en` skin from
  unverified text (flag `needs_review`) and stamp `source_lang` honestly.

### 🚦 SIGN-OFF GATE — HARD STOP

Everything above produces artifacts and plans. **Nothing goes to prod, nothing deploys, no
migration commits, until Angel + Felix approve the tree via the BL-CAT.2 sheet.** After
sign-off, the migration ships through the normal gated ladder (`make deploy ENV=…`,
backup-gated, re-probed) — that is a *separate* session, started deliberately.

Report progress by updating this file's checkboxes and the worklist line. When BL-CAT.2 is
ready, tell Angel "the Felix taxonomy sheet is ready" and stop.
