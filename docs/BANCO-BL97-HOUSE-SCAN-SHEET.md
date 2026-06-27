# BL-97 — House Scan Sheet (the binder of no-barcode staples)

*Status: SPEC ONLY — back-pocket simple solution. NOT built.*
*Spec date: 2026-06-27. Owner of the artifact in the field: Felix (catalog manager).*

---

## The problem (in Angel's words)

Some products have no EAN / no printed barcode on them — loose grinders, certain
papers, bulk CBD, anything unmarked. When one of those lands at the counter, Pam
either hunts for it on screen or — worst case — re-creates it from scratch. That's
wasted time, every day, and it's how the catalog gets polluted with duplicates.

We do **not** want to label every loose product, and we do **not** want Felix
reprinting a whole catalog book every day (that fights "sell-to-seed" — the catalog
grows as you sell, so a printed-everything book is stale the moment it prints).

## The concept

A **House Scan Sheet**: a physical binder (or laminated flip-cards on a ring) that
lives at the register, holding **one card per no-barcode staple**. Each card shows:

- a **big photo** of the product
- the **name + category/class**
- a **scannable barcode** the cashier scans *right off the card*
- a **date stamp** for version control

Cashier's flow: unmarked item in hand → flip to the right category section → match
the photo → scan the card → it's in the cart. No typing, no re-creating.

When a product changes (new photo, renamed, price note), Felix prints a **fresh
card and sticks it over the old one**. Print-once-per-product, not reprint-the-book.

> Trade terms so we're speaking the industry's language, not coinage:
> a printed page of scannable items = a **"scan sheet" / "barcode booklet"**;
> a single card that lives next to the product instead of on it =
> a **"shelf-edge label" / "shelf talker."** This feature is both, in binder form.

This is the **paper backup**. The **primary** path stays on-screen (the BL-96
taxonomy pickers + product photos in `/pos/catalog`). The binder is for when paper
is faster or the tablet's busy — and as a tangible thing Felix can hand a new hire.

---

## The landmine: the scanner only reads retail barcodes now

BL-90 deliberately **dropped CODE_128 / CODE_39 / ITF** from the scanner, keeping
only retail formats (EAN-13 / EAN-8 / UPC) to kill misreads. So if a card prints a
plain Code-128 of our internal SKU, **the scanner won't read it.** That would quietly
break the whole feature.

### The fix (and it's the standard, correct one)

Print an **internally-generated EAN-13 using a restricted in-store prefix (20–29)**.
GS1 reserves prefixes `02` and `20–29` for exactly this — store-internal /
variable-measure items that never leave the shop. The existing scanner already reads
EAN-13, so **zero scanner changes, zero regression.**

Mechanism, reusing what BL-90 already built:

1. When Felix marks a product "put on the House Scan Sheet," generate a valid
   EAN-13 in the `20–29` range (12 digits + check digit).
2. Store it as an **alias barcode** on that product (the `product_barcodes` table
   from BL-90 already supports primary + alias lookup).
3. The card prints that EAN-13. Scanning the card hits the normal
   `searchByBarcode` path → product found → added to cart. Identical to scanning a
   real product.

So the card's barcode *is* a first-class barcode for that product, just one we
minted because the manufacturer didn't.

---

## Version control / "is this card current?" — the part you asked about

You floated "last printed" vs "last edited." Use **both**, because each answers a
different question:

| Field | Source | Answers |
|-------|--------|---------|
| `updated_at` (product) | already exists on the product record | "When did the product's data last change?" |
| `card_printed_at` (new, small) | set when Felix prints the card | "When did we last print a card for it?" |

**Rule: a card is stale when `updated_at > card_printed_at`.** That's the whole
version-control logic. It means:

- The **card prints the `updated_at` date** ("Updated: 2026-06-27"), not the print
  date — because the *content* date is what tells anyone glancing at it whether it
  matches the screen. (Print date alone can't tell you if the data moved on.)
- The **generator flags stale cards** — "3 cards need reprinting" — so Felix never
  has to eyeball the whole binder. He prints only what changed, sticks the new card
  over the old, done.

Optionally print a tiny **version counter** (`v3`) too — increments each reprint —
so two people can tell at a glance which card is newer if one falls out of the
binder. Cheap, nice-to-have, not required.

> Recommendation: show `Updated: <date>` + `v<n>` on the card; track
> `card_printed_at` invisibly for the stale-detector. Best of both, no clutter.

---

## Card layout (label-printer friendly)

Designed to print on a **large-format label printer** (Brother/Dymo-class) OR as a
4-up A4 sheet you cut — same content either way. Printer-agnostic.

```
┌────────────────────────────────────┐
│  [ BIG PRODUCT PHOTO ]             │  ← photo dominates, paper = big image
│                                    │
│  GIZEH Silver Rolling Papers       │  ← name (bold)
│  Papers · King Size                │  ← category · class
│                                    │
│  ███ ▌█ ▌▌ ███ ▌█ ███   2000001  │  ← EAN-13 (20–29 prefix), human-readable digits
│                                    │
│  Updated: 2026-06-27   v3   🔞     │  ← content date · version · age badge if 18+
└────────────────────────────────────┘
```

- **Age badge (🔞)** pulls from the BL-96 taxonomy `age_restricted` flag — so the
  binder itself reminds the cashier to check ID. Free compliance nudge.
- One **section per category** (CBD / Tobacco / Papers / Grinders & Bones / …),
  sorted, so the binder has tabs and you flip straight to the right block.

---

## Data model (almost all reused)

| Piece | New or existing |
|-------|-----------------|
| Product photo, name, category, class, `age_restricted`, `updated_at` | **exists** (product model + BL-96 taxonomy) |
| Alias barcode storage + lookup | **exists** (`product_barcodes`, BL-90) |
| `on_scan_sheet` boolean on product | **new** (one column — which products are in the binder) |
| `card_printed_at` timestamp on product | **new** (one column — stale detector) |
| `scan_sheet_version` int on product | **new, optional** (the `v3` counter) |
| EAN-13 internal generator (20–29 prefix + check digit) | **new** (small util, ~30 lines) |

Three columns + one util. Everything else is wiring.

---

## The generator (PDF)

Reuses the Puppeteer pipeline we already run for postcards/SOPs — same toolchain,
no new dependency.

- **Endpoint / manager action:** "Generate House Scan Sheet" in `/pos/catalog`
  (manager-only, like all catalog CRUD).
- **Input:** all products where `on_scan_sheet = true`, grouped by category.
- **Output options:**
  1. **Full binder PDF** — every card, sectioned by category, 4-up on A4 to cut, OR
     one-card-per-label for the label printer.
  2. **Stale-only PDF** — *just* the cards where `updated_at > card_printed_at`.
     This is the daily driver: print these few, stick over the old ones.
- On print, stamp `card_printed_at = now` and bump `scan_sheet_version` for the
  products included.

---

## Acceptance criteria

- **AC1** — Manager can toggle `on_scan_sheet` on a product from `/pos/catalog`.
- **AC2** — Toggling on generates (or reuses) an internal EAN-13 in the 20–29 range,
  stored as an alias barcode; scanning that code finds the product.
- **AC3** — "Generate House Scan Sheet" produces a category-sectioned PDF with photo,
  name, category/class, scannable EAN-13, human-readable digits, `Updated:` date,
  version, and 🔞 badge where `age_restricted`.
- **AC4** — A "stale only" generation includes exactly the products where
  `updated_at > card_printed_at`, and nothing else.
- **AC5** — Printing stamps `card_printed_at` and bumps the version for included items.
- **AC6 (Fairphone, Angel)** — A printed card scans correctly on the real scanner
  and adds the product to the cart, indistinguishable from a manufacturer barcode.
- **AC7** — No scanner regression: real EAN/UPC products still scan as before.

---

## Phasing

- **P0 — minimum back-pocket:** `on_scan_sheet` flag + EAN-13 generator + full-binder
  PDF. Felix can build the binder. (No stale-detector yet — he reprints what he knows
  changed.)
- **P1 — version control:** `card_printed_at` + stale-only PDF + the "N cards need
  reprinting" flag. This is the part that makes it low-effort to keep current.
- **P2 — polish:** `v<n>` counter on the card, label-printer one-up layout preset,
  category tab dividers.

Build P0 only when there's real demand (i.e. Felix says the on-screen pick isn't
enough). The on-screen visual pick (BL-96 pickers) is the primary path and may make
the binder unnecessary — so this stays specced-and-parked until the field asks for it.

---

## What to tell Felix (the one-paragraph pitch)

"For the stuff with no barcode, you don't label every product — you keep a little
binder at the till, one card per item with a big photo and a barcode we print for it.
Pam matches the picture, scans the card, done. When something changes, you print a
fresh card and stick it over the old one — the date on the card tells you which is
current, and the system tells you which cards have gone stale so you only reprint
those. Print-once, not a reprinted book."
