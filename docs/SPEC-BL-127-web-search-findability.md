# BL-127 — "Search the web" findability + honest-label gap (scan/snap miss must never dead-ends)

**Status:** ✅ BUILT + SHIPPED PROD 2026-07-16 (`42f7128`). Holding prod for Angel's staging
verify (AC-repro). Changes: catalog persistent "Not the right item?" row (🔎 Look it up on Google +
➕ Create from photo, no longer gated on results===0); snap-panel fallback offers Google AND Create;
scan-miss web-card "not this → Google" escape (passes barcode); honest copy — all `search_web` →
"Look it up on Google" (en/de/fr/it) + new keys catalog.not_right_item / create_from_photo. sw v128.
**Type:** Frontend (Alpine/HTML across catalog + scan + on-the-fly sale) + small copy/i18n; **optional**
backend re-wire (prefer tier-2 auto-fill over manual Google when a barcode is present).
**Branch policy:** Work on `main` (trunk-based WoW). Own commit(s), own BL → boards the release train
independently. Ship through the gate ladder sandbox→staging→prod.
**Verification:** Angel on staging-banco (Fairphone, HTTPS) with the ACTUAL trigger item — the special
bong-remote battery photo — reproduces the scenario in AC-repro below.

---

## The trigger (real, 2026-07-16)

Angel snapped a photo of a **special battery for a bong-remote setup** in the sandbox. Snap-find
identified it correctly ("it knows exactly what it is") — but there was **no obvious way to search the
web for it**, and the operator expected it to "search Google" and auto-fill. It didn't. Tracing the code
showed **nothing is broken** — but there's a real **findability + expectation gap** worth closing so a
special/rare item is never a dead-end at the till.

## What's actually wired today (evidence)

Two *different* "web" mechanisms exist, and the UI conflates them:

1. **Manual Google button — `webSearchProduct()`** at `src/templates/pos/base.html:997`:
   ```js
   window.open('https://www.google.com/search?q=' + encodeURIComponent(q), '_blank', 'noopener');
   ```
   It **opens Google in a new tab** for the human to read. It does NOT scrape or auto-fill (no free
   Google API). This is tier-1.

2. **Barcode auto-fill — `/products/web-lookup`** at `src/routes/pos_router.py:586` →
   `lookup_product(barcode, name)` in `src/services/web_product_lookup.py`. This is the real auto-fill
   (UPCitemdb trial → Open Products/Food Facts → images/brand/category). But it is **barcode-primary**:
   ```python
   if not barcode:
       out["note"] = "no_barcode"   # nothing to auto-resolve — hand back the Google link
       return out
   ```
   With only a photo/name it returns a Google URL and stops. And a **special bong-remote battery is
   almost certainly not in those consumer/food barcode DBs** even with a barcode → `not_found` → Google
   link again.

3. **Snap-find** (`/products/snap-find`, `src/routes/pos_router.py:600`) reads the item off the photo and
   runs `_find_catalog_matches`, returning `best_match_score`. Its own docstring: a low score means
   **"not found → search or create."** The AI draft "rides along as the fallback for a genuine new item."

### The three gaps

- **G1 — Button hides on weak matches.** In catalog "manage products," the 🔎 button only renders on the
  *zero-results empty state*: `src/templates/pos/catalog.html:181` (`x-show="results.length === 0"`).
  If snap-find/search returns even ONE weak near-match, the button disappears — so the operator "can't
  find where to search." This is the primary bug.
- **G2 — Dead-end in adjacent flows.** The on-the-fly **new-sale** miss and the **scan** miss surface a
  plain Google `<a>` link (`src/templates/pos/scan.html:655`, `src/templates/pos/receiving.html:310`) but
  there's no consistent, always-reachable "🔎 Search the web / ➕ Create from photo" affordance on a
  weak/near miss.
- **G3 — Dishonest label.** "Search the web" implies an in-app auto-search; it actually just opens Google.
  This is the exact expectation mismatch the operator hit.

## Goal

On any **miss or all-weak result** — in catalog manage-products, on the scan-miss, and in the on-the-fly
new-sale — the operator is **never dead-ended**. They always see, together:
- **🔎 Look it up on Google** (honest wording — it opens a tab), and
- **➕ Create from photo** (the snap-find AI draft, the "or create" branch), and
- when a **barcode is present**, an **auto-fill from barcode** action that calls the existing tier-2
  `/products/web-lookup` first, falling back to the Google open only on `no_barcode`/`not_found`.

**Pam never invents data — she confirms it.** For a special item with no retail barcode, "confirm" means:
read Google if she wants, then accept the AI photo draft. That path must be one tap away, always.

## Acceptance criteria

- **AC1 (G1):** In catalog manage-products, when a search returns results but the **best match is weak**
  (below the existing `best_match_score` "not found" threshold — reuse it, don't invent a new one), a
  persistent "**Not the right item?**" row offers 🔎 Look it up on Google **and** ➕ Create from photo.
  The button no longer requires `results.length === 0`.
- **AC2 (G2):** The same affordance is reachable, with identical wording, on the **scan-miss** and the
  **on-the-fly new-sale** miss. No surface dead-ends.
- **AC3 (G3):** The web-search control's copy makes clear it **opens Google** (manual look-up), visually
  distinct from any auto-fill action. Update `data-i18n` keys (`*.search_web`) + `src/static/pos/pos-i18n.js`
  entries (en/fr/nl/es) accordingly. Keep it short.
- **AC4 (optional/stretch):** When the miss carries a **barcode**, the primary action calls tier-2
  `/products/web-lookup` (auto-fill) and only falls back to the manual Google open on `no_barcode`/
  `not_found`. Surface the quota line already returned by `lookup_product`.
- **AC5 (G2/create branch):** A low-confidence **snap-find** result shows an explicit **➕ Create from
  photo** CTA pre-filled from the AI draft, so a special item (the battery) is a one-tap create, not a
  dead-end.
- **AC-repro:** On staging-banco, snap the special bong-remote battery photo → confirm the operator can,
  without leaving the flow, either look it up on Google OR create it from the photo draft. No dead-end,
  no "where do I search?" confusion.

## Out of scope

- Any real Google **scraping/API** (there isn't a free one — do NOT add a paid dependency here).
- Expanding the barcode DB coverage. Special/rare items simply won't be in UPCitemdb/OPF; the create-from-
  photo path is the answer for those, not more databases.

## Notes / links

- Aligns with the standing **web-search-fallback** idea (tier-1 zero-cost Google button, tier-2 in-app
  auto-lookup) and the **matching doctrine** (`banco-barcode-matching-doctrine` — BL-102 scan-miss →
  photo-first → capture barcode on first sale → hits forever). BL-127 is the *UI findability* slice of
  that doctrine.
- Reality check per `banco-felix-reality-check`: sandbox test, no real prod users — normal priority, not a
  prod-fire. It's a genuine UX dead-end worth fixing before the next live till session.
- Authored via a graphify code-graph trace + grep on 2026-07-16 (reverse-trace located
  `web_product_lookup.py` and the caller set fast).
