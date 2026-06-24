# BL-97 — Reference Catalog (product master) for Banco POS

**Status:** SPEC — ready to build. Follows BL-96 (scan-miss → search-first, shipped `cd18321`, staged).
**Type:** Backend (new table + importer + search source) + small frontend (second source in the
search-first modal).
**Branch policy:** Work on `main` (trunk-based WoW). Own commits, own BL → boards the release train
independently.
**Verification:** Importer = pytest + a real 420 CSV sample. Cherry-pick UX = Angel on the Fairphone
over HTTPS on staging-banco (AC1–AC6 below).

---

## Goal

Give Banco a **reference catalog** — a large, canonical, supplier-fed product master (the full 420 /
TMR dump, tens of thousands of items, with real **title + description + photo**) that the POS can
search but never sells from directly. On a scan-miss or a search, the cashier finds the item in the
reference and **cherry-picks** it: one tap copies the real data into the live catalog, binds the
scanned barcode, and the cashier just confirms the price. **Pam never invents data — she confirms it.**

This is the standard retail **PIM (Product Information Management) → POS** pattern (flagging
coined-vs-standard per CLAUDE.md: "reference catalog" / "product master" / "PIM" are the real terms;
"our private curated backup list" is Angel's phrasing for the same thing).

---

## Why (the problem it solves)

1. **Felix's catalog is pre-loaded rich, not empty.** ~6–7k items from 420 ≈ 80% of sales. The product
   almost always already exists; only its barcode is missing/wrong. BL-96 made scan-miss search-first
   so the cashier *binds* instead of *duplicates* — but it searches the **live** catalog, which today
   is bloated with the whole dump.
2. **"Don't make up data" (Angel's core fear).** When an item truly isn't on file, the create-new form
   invites Pam to re-type a name/description from memory. The reference layer removes that: the title,
   description, and photo come from 420's own record.
3. **It makes the live catalog honest.** Today "what's in my store" lists thousands he may not stock.
   Move the dump to a reference layer and the live catalog means **"what Felix actually sells"** — real
   zero-perpetual-inventory: the live list accretes from genuine cherry-picks + sales, not a bulk import.

| | **Reference catalog** (new, BL-97) | **Live catalog** (`products`, today) |
|---|---|---|
| Holds | Full 420/TMR dump — real title/description/photo | Only what Felix carries / has sold |
| Source | CSV dump from 420, re-imported periodically | Cherry-picks + real sales (lazy capture) |
| Sold from? | **Never** — lookup only | Yes |
| Maintained by | Angel, separately, on his schedule | The counter, automatically |
| Size | Tens of thousands | Lean (hundreds → low thousands) |

---

## Decisions (locked from the 2026-06-24 discussion)

1. **CSV dump, not live TMR scraping.** A periodic dump from Felix's own supplier is clean; live
   scraping the TMR website is fragile + a ToS risk. Reference DB fed by CSV is strictly better.
2. **Separate table, same Postgres** (`reference_products`) — not a separate database. One backup, one
   ops story, FK-free isolation. A separate DB is overkill now.
3. **Cherry-pick first, never sell from reference directly** — keeps the live list honest. But make it
   **one tap = pick + add to cart** so it's not slower at the counter.
4. **Leave the existing 6–7k in `products` for now.** Reference is added *alongside*. "Demote the unsold
   dump items to reference" is a clean later follow-up (BL-97b), not a blocker — so today's staged BL-96
   demo keeps working.
5. **Copy the image into our own storage on cherry-pick** — don't hotlink TMR/420 URLs forever.

---

## Verified seams (grounded in the code, 2026-06-24)

- **Live product model:** `src/db/models/product_model.py` (`ProductModel`, table `products`). Already
  has the fields cherry-pick needs to land into: `barcode, sku, name, description, price, cost,
  category, tags, image_url, supplier_sku, supplier_name, supplier_price`. **No live schema change for
  the target** — cherry-pick is just an INSERT into `products`.
- **Alias barcodes:** `ProductBarcodeModel` (table `product_barcodes`, BL-90). Cherry-pick attaches the
  scanned code via the existing `POST /api/v1/pos/products/{id}/barcodes` (`pos_router.py:285`).
- **Fast search:** `GET /api/v1/pos/search` → `search_products_fast` (`pos_router.py:668`) — trigram GIN
  + ILIKE, returns `{items, total, skip, limit}`, public. The new reference search mirrors this shape.
- **Cashier-safe create:** `POST /api/v1/pos/products/quick` (`pos_router.py:165`, `require_any_pos_role`)
  — the cherry-pick endpoint reuses this gate so a cashier can pick (not manager-only).
- **Search-first modal (BL-96):** `src/templates/pos/scan.html` — `scanData()` Alpine component;
  `searchExisting()` / `linkToExisting()` / `lazyLinkResults`. The reference becomes a **second source**
  in that same modal.
- **⚠️ Schema drift (read `[[schema-create-all-alembic-drift]]`):** `create_all` will auto-make
  `reference_products` on restart, but `alembic upgrade` is the source of truth and the chain has drifted.
  **Ship the table as a real alembic migration AND verify it exists on staging/prod** — don't rely on
  create_all. `helix_db` is shared prod+staging+banco-prod, so the table appears in all three; that's fine
  (additive, read-mostly).

---

## Schema

New table `reference_products` (migration + model `src/db/models/reference_product_model.py`):

| column | type | notes |
|---|---|---|
| `id` | uuid PK | |
| `supplier` | text, NOT NULL | e.g. `"420"`, `"TMR"` — part of the upsert key |
| `supplier_sku` | text | supplier's own article number |
| `barcode` | text, indexed | EAN/UPC if the dump has one |
| `title` | text, NOT NULL | canonical name |
| `description` | text | canonical description |
| `image_url` | text | source image (copied to our storage on cherry-pick) |
| `category` | text | |
| `suggested_price` | numeric(10,2) | optional RRP; cashier can override |
| `cost` | numeric(10,2) | supplier buy price if present |
| `raw` | jsonb | the original CSV row (audit / future fields) |
| `imported_at` | timestamptz | set per import run |

**Indexes:** GIN trigram on `title` (mirror the live search), btree on `barcode`, unique on
`(supplier, supplier_sku)` (the upsert key; fall back to `(supplier, barcode)` when no sku).

This table is **read-only at the counter** — only the importer writes to it.

---

## Importer (Python-first, per CLAUDE.md rule 11)

`scripts/import_reference_catalog.py` (Typer CLI):

- `import-reference-catalog FILE.csv --supplier 420 [--map mapping.yaml] [--dry-run]`
- **Idempotent upsert** on `(supplier, supplier_sku)` (or `(supplier, barcode)`): re-running a fresh dump
  updates changed rows, inserts new ones, leaves the rest. Never deletes silently — report adds/updates/
  unchanged counts (no-silent-cap rule).
- Column mapping via a small YAML (420's headers → our columns) so a new supplier = a new mapping file,
  not new code.
- Stash the original row in `raw` jsonb.
- Validates with Pydantic; bad rows are collected and reported, not dropped silently.
- Runs from the host venv against the DB, or inside the container — document both (the venv has no
  fastapi but asyncpg is enough for a direct import).

---

## API

1. `GET /api/v1/pos/reference/search?q=&barcode=&limit=` → `{items, total, ...}` — same envelope as
   `/search`, trigram over `reference_products.title` + exact `barcode`. Public (catalog lookup).
2. `POST /api/v1/pos/reference/{ref_id}/adopt` (`require_any_pos_role` — cashier-safe) — the cherry-pick:
   - Create a live `products` row copying `title→name, description, image_url, category, supplier*`,
     price = body price (or `suggested_price`), via the same path as `/products/quick`.
   - Copy the reference image into our storage (reuse the product-image pipeline); fall back to keeping
     `image_url` if the copy fails (never block the pick).
   - If a `barcode` is supplied (the scanned miss), attach it via the alias path.
   - Return the new product (so the modal can `addToCart` immediately).
   - Guard against double-adopt: if a live product already carries this `(supplier, supplier_sku)` or
     barcode, return that one instead of creating a duplicate.

---

## Frontend (small — extends BL-96)

In `scan.html` `scanData()`:
- After the live `searchExisting()` results, run a **reference** search and render its hits in a second
  group tagged **"From reference — add to your shop"** (visually distinct: a small badge + the supplier).
- Tapping a reference hit calls `adopt` (with the scanned barcode + a price prompt / accept-suggested),
  then `addToCart` — one motion. Live hits still bind via BL-90 as today.
- Create-new stays the last-resort fallback (now genuinely rare).

The "oh yeah — we found something similar in our reference" moment is the demo beat: the POS *knows* the
product even though this shop has never sold it.

---

## Acceptance criteria (Fairphone, staging-banco, HTTPS)

- **AC1** Import a real 420 CSV sample → `reference_products` populated; re-import same file → counts show
  0 new / N unchanged (idempotent), no duplicates.
- **AC2** Scan a barcode NOT in the live catalog but present in the reference → search-first modal shows it
  under "From reference" with its real photo + title.
- **AC3** Tap it → set/accept price → it's created in the live catalog with the real title/description,
  the scanned barcode bound, and added to the cart in one motion.
- **AC4** Scan the same barcode again → instant live hit (BL-90), no reference round-trip, no duplicate.
- **AC5** Adopt twice (e.g. two cashiers) → second adopt returns the existing live product, not a twin.
- **AC6** Reference search by typed keyword (no barcode) → relevant hits with photos; create-new still
  reachable as the collapsed fallback.

---

## Phasing

- **P1 (this BL):** schema + migration + importer + reference search API + `adopt` + modal second source.
  Demo: load reference on staging-banco, cherry-pick live.
- **BL-97b (follow-up):** demote the existing 6–7k dump from `products` → `reference_products` (tag the
  420-imported rows, move the unsold ones), so the live catalog becomes "what Felix actually sells".
- **BL-97c (later):** scheduled / one-click re-import when 420 sends a new dump; diff report.

## Out of scope

- Live TMR website scraping (rejected — see Decision 1).
- Perpetual inventory / stock counts (Banco stays zero-perpetual-inventory).
- The La Piazza / Artemis Premium listing bridge (separate track; reference is upstream of it).

---

*"Oh yeah — we found something similar in our reference catalog." — the cherry-pick moment.*
*Pairs with BL-96 (search-first) and BL-90 (alias barcodes). Heed `[[schema-create-all-alembic-drift]]`.*
