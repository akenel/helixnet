# BL-87 — Camera Barcode Scanning for Banco POS (Android + iOS)

**Status:** READY — blocked on BL-86 (reaper) landing / working tree clearing.
**Type:** Frontend (one possible backend decision, see §Seam 2).
**Branch policy:** Work on `main` (trunk-based WoW). Its own commits, its own BL, so it
boards the release train independently of the reaper.
**Verification:** Real-device only — AC1–AC6 on Angel's Fairphone (Android Chrome) over
HTTPS on staging. iOS written to same path, verified later.

---

## Goal
Live-camera barcode scanning on the Banco POS sale screen. Tap scan control → camera
opens → reads a 1D retail barcode (EAN-13 / UPC-A / EAN-8 / Code128) → writes the number
into the existing barcode flow → fires the existing lookup. Manual keyboard entry stays as
fallback. One code path for Android Chrome (must-have) + iOS Safari (verify later).

Full original spec: Angel's WhatsApp 2026-06-21 18:37 (camera scan + lazy capture +
v1.1 photo-capture appendix). This doc is the verified, build-ready version.

---

## ✅ VERIFIED SEAMS (read before building — these correct the spec's assumptions)

### Seam 1 — the barcode input + lookup trigger (CONFIRMED)
- **File:** `src/templates/pos/scan.html` (NOT `transactions.html` — the spec guessed wrong).
- **The screen is an Alpine component** `scanData()` (defined at `scan.html:374`).
- **Barcode input:** `scan.html:60-66` — `<input x-model="barcodeInput" @keyup.enter="searchByBarcode()">`.
  No `id`; it's bound via Alpine `x-model`, not a DOM selector.
- **Lookup trigger:** the Alpine method **`searchByBarcode()`** (`scan.html:445`). It reads
  `this.barcodeInput`, calls `GET /api/v1/pos/products/barcode/{barcode}`, and on success
  `addToCart(product)` + clears the field; on 404 it switches `searchMode = 'catalog'`.

**➜ Integration rule:** wire the scanner INSIDE the `scanData()` Alpine component. On decode,
set `this.barcodeInput = <decoded>` then call `this.searchByBarcode()`. Do **not** write to a
raw DOM input + dispatch a synthetic Enter — Alpine owns the state, that path is flaky. Add
the overlay state (`scanOpen`, `startScan()`, `stopScan()`, `onDecode()`) as new properties
on `scanData()`. This is the clean seam and means **zero** change to the existing lookup.

### Seam 2 — "not on file" / tier-3 add + LAZY CAPTURE (⚠ SPEC ASSUMPTION WAS WRONG)
The spec said the one backend-adjacent change "genuinely needed" is adding a barcode
pass-through to the tier-3 add flow. **Reality is different — read this carefully:**

- The current not-on-file path = **Catalog mode** (`addCatalogItem()`, `scan.html:525-555`).
  It creates an **ephemeral cart line only**: `{ id: 'catalog-'+Date.now(), name: '[CATALOG] …',
  price, isCatalogItem: true }`. **No barcode field. No product is persisted.**
- At checkout (`checkout.html:460-468`) catalog lines are sent as **custom lines** with
  `product_id: null` (name + unit_price). They never become a row in the products table.
- **Therefore lazy capture is NOT supported today** — scanning an unknown item, adding it,
  and having it "known forever after" does **not** happen. The catalog line evaporates after
  the sale. The same item would be re-improvised every time. (This is exactly the failure the
  spec feared — confirmed.)
- **BUT** a real product-create endpoint already exists: **`POST /api/v1/pos/products`**
  (`pos_router.py:123`, `create_product`) and its schema **`ProductCreate` already accepts
  `barcode`** (`pos_schema.py:43`). So the backend can persist a product-with-barcode **with no
  backend change.**

**➜ So lazy capture is a FRONTEND wiring decision, not a backend pass-through:**
on "not on file," instead of (or alongside) the ephemeral catalog line, call
`POST /pos/products` with the scanned barcode + a name + price to mint a **real, persisted**
product, then add THAT to the cart. No backend code needed — but it's a **product decision
for Felix**, not a freebie: do we want every counter improvisation to mint a permanent catalog
product? Options to put to Angel/Felix:
  - **(a) Demo-minimal:** keep current behavior — unknown → catalog mode (ephemeral). Ships
    AC1–AC6 as literally written. Lazy capture deferred. ← smallest, true "afternoon."
  - **(b) Real lazy capture:** unknown → a small "name + price" prompt → `POST /pos/products`
    with the scanned barcode → persisted → added to cart → known on every future scan.
  - **Before wiring (b):** verify the role guard on `POST /pos/products` (cashier vs
    manager/admin) — a cashier may not be authorized to create products.

---

## Library
`html5-qrcode` (wraps ZXing; 1D retail formats; manages camera lifecycle + rear-camera
selection; iOS Safari 11+ and Android Chrome in one path).
- **Vendor locally** — download `html5-qrcode.min.js`, serve from
  `src/static/vendor/html5-qrcode.min.js` (confirm 200 + correct MIME). **No runtime CDN.**
  (CLAUDE.md rule #9 — full library, self-hosted posture.)
- `formatsToSupport`: `EAN_13, EAN_8, UPC_A, UPC_E, CODE_128, CODE_39, ITF` only.
- Fallback if 1D decode is flaky in shop light: swap decoder for `@zxing/library` — same seam,
  drop-in, not a rewrite. Do NOT do pre-emptively.

---

## Hard preconditions (these cause fake "it's broken")
1. **HTTPS mandatory** — `getUserMedia` needs a secure context. Staging is
   `https://staging-banco.lapiazza.app` (✓ secure). Plain-IP / `http://` = camera silently
   fails. Confirm the phone is on the https host before blaming code. `localhost` ok for local.
2. **CSP** — if a CSP is set on the POS responses, ensure: `script-src 'self'`,
   `media-src 'self' blob:`, `img-src 'self' blob: data:`, `worker-src 'self' blob:`. If no CSP,
   skip. (TODO at build time: check whether Banco sets a CSP header — not yet verified.)
3. **Camera permission** requested at first use — handle denial gracefully (AC3).

---

## UX / behaviour
1. Scan control on the sale screen — reuse the existing 📊 Barcode button area or add a clear
   camera icon beside the manual input; keep BOTH visible.
2. Tap → modal/overlay with live rear (`environment`) camera + a visible scan box.
3. On decode: stop+release camera immediately (single-shot), close overlay, set
   `barcodeInput`, call `searchByBarcode()`, short beep and/or `navigator.vibrate(60)`.
4. Found → normal ring-up. Not-on-file → see Seam 2 (decision (a) or (b)).
5. Manual keyboard entry stays fully working (it already does — untouched).
6. Overlay ALWAYS releases the camera on close/cancel/decode (no stuck "camera in use", no
   battery drain).

## iOS specifics (same path, verify later)
- `<video playsinline>` (html5-qrcode sets it — ensure no global CSS breaks it).
- Camera start inside the user gesture (it is — overlay opens on tap).
- iOS 11+ Safari only; old in-app webviews may refuse → fall back to manual.

---

## OUT OF SCOPE (keep it an afternoon)
❌ inventory qty / stock decrement · ❌ AI photo-fill · ❌ external EAN name lookup ·
❌ backend/DB changes beyond serving the static JS (the `POST /pos/products` path already
exists) · ❌ changes to the existing lookup · ❌ torch/zoom/multi-scan for v1.

---

## Acceptance criteria (manual, real device)
- **AC1** (Android/Chrome, HTTPS): tap scan → rear camera → point at an EAN → number
  populates + lookup runs within ~2s.
- **AC2** known item rings up; unknown → "not on file" → tier-3/catalog add appears.
- **AC3** deny camera permission → graceful message, falls back to manual, no crash/blank.
- **AC4** close/cancel overlay → camera indicator light OFF (released).
- **AC5** manual keyboard entry works exactly as before.
- **AC6** scanning a second item after the first works (no locked camera, no double-fire).

**Android passing AC1–AC6 = the demo gate.** iOS verified later on a real iPhone.
Camera/getUserMedia cannot be unit-tested or pytested — device verification is expected, not
a failure.

---

## Implementation order
1. Vendor `html5-qrcode.min.js` → `src/static/vendor/`; confirm served (200 + MIME).
2. (Seams already located above — see §Verified Seams.)
3. Overlay markup + minimal CSS (full-screen camera, scan box, cancel button) in `scan.html`.
4. Scanner JS as new methods on `scanData()`: tap → start (environment cam, retail formats)
   → on decode → stop cam → set `barcodeInput` → `searchByBarcode()` → beep/vibrate → close.
5. Denial/error handling → manual fallback.
6. Verify HTTPS + CSP preconditions on the live banco host.
7. Decide (a) vs (b) for lazy capture with Angel/Felix.
8. Hand to Angel for AC1–AC6 on the Fairphone.

---

## Appendix — v1.1 (designed, NOT in this build)
Photo capture at product creation: one tap at the create moment attaches an image to the
freehand product, sale completes immediately — **no AI at the counter, nothing waits.**
Processing is async/off-counter: an enrichment queue later runs a vision model over
(photo + rough name) to draft name/description/category + EN/DE/FR/IT translations; Felix or
Leanna approve the batch. Capture belongs at create-time (fast, deferred); processing never
touches the sale path. Ship scan + lazy capture first; add photo capture only once proven.
