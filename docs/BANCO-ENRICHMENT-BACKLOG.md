# Banco — Enrichment Backlog (post-initial-flow)

Good ideas surfaced while walking the initial flow. **None block a first sale** — the
on-the-fly flow already handles "not on file." These make the catalogue *richer*. Captured
here so they're banked, not lost, and so the initial flow can ship without waiting on them.

Guiding principle (Angel, 2026-06-22): **the NAME is the key, not the barcode.** A scanned
EAN may not match the website or may not exist; humans navigate by name + picture + brand.
The barcode is an internal handle we *capture*, not a lookup we depend on.

---

## 1. Pull-from-Artemis (product enrichment from the shop's own website)

**Why:** artemisluzern.ch already has ~6,318 products with real prices, pictures, German
descriptions, categories, brand, specs. Pulling that in solves "Pam guesses the price and
gives the store away" — the canonical price comes from the shop's own source.

**Feasibility (probed 2026-06-22):**
- ✅ **By-URL pull works.** Fetched the Granny's filter page → clean structured data
  (name, CHF 9.50, category breadcrumb, brand, specs, image path). Proven via WebFetch.
- ⚠️ **By-name search is JS/AJAX.** `/de/suche?q=…` 404s — the public search is a dynamic
  widget. Needs the underlying search API endpoint found + parsed (R&D).
- Note: the product page exposes **no EAN/barcode** — confirms the name-is-the-key principle.

**The flow (when built):** "not on file" → fork:
1. **🔎 Pull from Artemis** — find by name (human reads the package once) → preview card
   (price/picture/description, translated DE→EN via the BYO VLM) → save, **attaching the
   scanned EAN as the product's barcode** (reuse BL-90 alias system → scan-once-known-forever).
2. **🆕 One-off / brand-new** — the on-the-fly flow (already built). For items not yet on
   the website (genuinely new products) — she has it in hand with a barcode + a photo.
3. **🔗 Link to existing** — alias path (already built).

**Pieces:** (a) by-URL pull → real server endpoint (httpx + LLM extract/translate);
(b) by-name search → find Artemis's search API; (c) preview→save with EAN attach.

## 2. VLM photo-read (resolve the no-EAN-index problem)

**Why:** scanning the EAN can't find it on the website (no EAN index). So instead: Pam takes
a good photo → the **vision LLM (Ollama image model, BYO brain)** reads the packaging (name,
brand, text) → that feeds the Artemis name-search → best-guess hits. After ~3 misses → "give
up gracefully → add as a brand-new product" (the on-the-fly path). The good photo she took is
reused as the product image. Infra exists (the slip-reader VLM pattern: run_llm + images).

## 3. Park / hold a sale ("suspend transaction")

**Why (Angel):** if Pam doesn't know a price, she can't finish — she needs to text someone or
set it aside and serve the next customer. **We don't have this today.** Standard POS feature
("park sale"). Persist the open cart server-side with a label → a "held sales" list → resume.
Banco already has OPEN transactions; this is: save cart to an OPEN/HELD txn + a resume UI.

## 4. CRUD on every entity (Angel: "all the schemas should have a CRUD")

**Why:** products have the Catalogue CRUD (`/pos/catalog`), but customers, suppliers,
store settings, categories, etc. don't all have a manage screen. Vision: every data model
gets a consistent admin CRUD (list / create / edit / discontinue), manager-gated. Likely a
generic CRUD scaffold over the schemas rather than hand-building each. Big, deferred — noted
so it's not lost. ("Let's not get into that right now." — Angel, 2026-06-22.)

## 5. Velocity reporting (the reorder signal — zero-inventory's other half)

**Why:** Banco runs zero perpetual inventory — reorder guidance comes from **sales velocity**
(what's selling fast), not a stock count. The sales log already holds the data; this is the
report/dashboard that turns it into "reorder these." Not built / not demonstrated yet ("I
haven't caught this working" — Angel). The natural P4 after the initial flow ships. Pairs
with the on-the-fly + Artemis enrichment (a fast-moving on-the-fly item is a reorder candidate
*and* an "enhance me properly" candidate).

## 6. Product label printing (the seal that was never installed)

**Status (verified 2026-06-22):** does NOT exist. No label queue, no N-up PDF, no "print
label" button — searched routes/templates/services. The only trace is an *aspirational
comment* in `scan.html` genInternalBarcode() ("a manager prints the label from the
Catalogue") describing intent, not a feature. The on-the-fly flow correctly *mints* a valid
internal EAN-13; nothing prints it.

**Not Day-One-blocking:** find-by-name covers re-selling; a printed sticker only buys
"scan instead of type." Convenience, not requirement.

**When built (short):** "Print labels" → N-up PDF of {product name + barcode + QR} per item.
All parts already in hand — **segno** (QR/barcode), **Puppeteer** (PDF), N-up layout math
documented in CLAUDE.md (postcard 2/3/4-up GOLD). Likely a label queue (mark items "to
label") → generate the sheet → print on the shop's label/sticker printer (⟶ NEED hardware
spec from Felix). FIX-NOW (tiny): correct the misleading scan.html comment so the code stops
claiming a feature that isn't there.

---

**Recommendation:** ship the tested initial-flow core to prod first (cash drawer, on-the-fly,
search fix, photos — all green on staging). Then take #1–#5 as their own focused projects,
one at a time. Don't let enrichment block the working till from reaching Felix. Think big
picture continuously (this doc is where it lives); build one focused slice at a time.
