# BL-128 — Variant findability: make SIZE / price / photo POP in till search results

**Status:** #1 SHIPPED PROD (size badge); #2 SHIPPED PROD (size-token boost, 2026-07-16). Field-authored from a full day scanning at Felix's Littau shop (2026-07-16).
**Type:** Frontend (result-card rendering) + a tiny size-extract helper; no schema, no backend change for #1.
**Branch policy:** `main` (trunk-based). Own commit, own BL. Ship through the gate ladder sandbox→staging→prod.
**Verification:** Angel at the till — search a strain that has multiple sizes (e.g. "Lemon Haze") and confirm the
**2g vs 5g vs 10g is distinguishable at a GLANCE**, not by reading five near-identical German names.

---

## The pain (real, 2026-07-16 — Angel, full day at the shop)

Scanning "either works or it doesn't." When the barcode misses, searching for the item is HARD — the catalogue
throws back a **wall of near-identical items that look/sound like it but aren't right**. The killer: **same exact
product, wrong SIZE** — you find "Lemon Haze **10g**" but need the **2g** pack; identical name, can't pin the right
variant. Searches upside-down for ~5 min, gives up, falls back to photo + a guessed title + read the EAN + no
description + guess the price + move on. **~20–30% of scans.**

**Honest split:**
- Genuinely-NEW item → the manual/born-once fallback is BY DESIGN and fine/fast. Not the problem.
- Item EXISTS but is unfindable → operator creates a **DUPLICATE** (the real cost: dupes + fragmented sales +
  wasted 5 min). Variant confusion is the #1 driver.

## Root of the "they all look the same"

The size (2g) is buried inside a long German name, so five "Lemon Haze" rows render identical in the results list.
The operator has to *read* each name carefully to find the size. The true disambiguator — the pack barcode (2g ≠ 10g
EAN) — heals via capture-on-first-sale ([[banco-barcode-matching-doctrine]]), but the FIRST encounter per variant is
the pain, and a text search has to make the variant obvious.

## #1 — THIS BUILD: make the distinguishing detail POP

Across the **till search surfaces** — the scan-miss "find it in the catalog" bind-search (`scan.html`
`lazyLinkResults`/`refResults`), the snap-find picker (`product_matches`), and catalog manage-products results:
- **Extract the SIZE/pack from the product name** (client-side helper: `2g` · `10g` · `5ml` · `100 Stk` · `3er` …)
  and render it as a **bold badge** on each result card.
- Make the **price prominent** (bigger/bolder) and the **photo** clear — the three glance-cues (size, price, picture)
  do the disambiguation, so 2g vs 10g is one look, not a reading exercise.
- Highlight the size token in the name too (or lead the card with it) so identical names visually diverge.

**Acceptance (AC1):** searching a multi-size strain shows each result with its size as a prominent badge; the
operator can pick the 2g from the 10g without reading the full German name. No schema change; a pure-name parse.

## Follow-ons (separate BLs / not this build)

- **#2 — size-token search boost:** typing "lemon haze 2g" ranks the 2g variant to the TOP (backend
  `search_products_fast` ORDER BY — boost when a size token in the query matches the name's size).
- **#3 — name-dedup guard on MANUAL create:** `create_product` 409s only on barcode/SKU, never NAME — a give-up
  manual create slips a dupe past. Fire find-first on the text/manual create path too ("there's already a Lemon
  Haze 2g — is this it?").
- **#4 — variant grouping:** product → [2g, 5g, 10g] as one card with a size picker. Bigger; later.

## Notes / links

- Field data + the honest split live in memory `banco-product-matching-integrity-bl100` (2026-07-16 entry).
- The real manager at Felix's shop is **Rafi** (not "Ralph"). KC test user `ralph` is separate/generic.
- Reality check `banco-felix-reality-check`: real operator pain, normal priority — findability is the till's
  highest-friction moment and the top dupe-driver.
