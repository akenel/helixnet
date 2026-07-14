# Banco Inventory Roadmap — "Sell-to-Seed"

*The lazy-inventory path for Felix's Artemis shop. Customer #1 steers the order.*
*Written 2026-06-21, grounded in the actual codebase (not aspirational).*

---

## The concept: sell-to-seed inventory

You do **not** load the shop's catalog on day one. You *start selling*. Every unknown
item is entered **once** at the counter (name + price + qty), saved as a real product,
and known forever after. The catalog builds itself from real sales. The two-week
inventory project disappears.

Why it fits Artemis specifically: the goods are ~100% **unmarked** (no manufacturer
barcode). A normal POS makes you barcode-and-load everything before you can sell. Banco
lets Felix skip straight to selling and accrete the catalog as money crosses the counter.

> Optional: preload a handful of fast movers via the Banana CSV importer. Not required.
> Day one with an empty catalog is a feature, not a gap.

---

## What ALREADY exists today (the credibility floor)

Most of what Felix will ask for is already in the product data model — just not all
surfaced in UI yet. This is why the demo is honest:

| Capability | State | Where |
|---|---|---|
| Create / read / update product | ✅ live | `POST/GET/PUT /api/v1/pos/products` |
| **Soft delete** (discontinue safely, keep history) | ✅ live | `DELETE /products/{id}` → `is_active=false` |
| Barcode scan + lazy capture at counter | ✅ **shipped to prod** | BL-87, `/pos/scan` |
| Cost, supplier name/SKU/price | ✅ on product | `product_model.py` |
| Reorder params: `stock_alert_threshold`, `min_stock`, `max_stock`, `lead_time_days` | ✅ on product | `product_model.py` |
| Low-stock query ("running low") | ✅ exists | `pos_router.py` |
| Catalog picture | ✅ field exists | `image_url` |
| Stock OUT (decrement on every sale) | ✅ live | sale path |
| Bulk preload | ✅ exists | Banana CSV import |
| `StockMovement`, `PurchaseOrder`, `Supplier`, `ReorderRequest`, `InventoryCount` models | ⚠ built, **not wired** to the Banco sale path | `inventory_model.py`, `purchase_order_model.py` |

**Honest framing for Felix:** the foundation is in. Receiving isn't from scratch — it's
*connecting existing parts*.

---

## The phases

### P0 — Scan + lazy capture ✅ SHIPPED (BL-87)
Live on `banco.lapiazza.app`. Camera scan, sell-to-seed, quantity, manager-only create,
graceful cashier fallback. Camera verified on Angel's Fairphone.

### P1 — Catalog CRUD dashboard 🔨 BUILDING NOW (BL-88)
The window onto the CRUD that already exists in the API. Manager/admin screen to:
- search/list products (active + discontinued)
- edit: name, price, **stock**, cost, category, barcode, picture (`image_url`), reorder thresholds
- discontinue (soft delete) + reactivate
- create new (same path as lazy capture, but deliberate)
This is what makes Felix feel he can *run* the catalog, not just accrete it.

### P2 — Receiving / goods-in + stock-movement ledger
The "box just came from the supplier" flow. Out is already logged; **in is the gap.**
A manager receiving screen: scan/confirm item → "I got N" → stock goes up → a
**stock-movement record** is written (in/out ledger). Once both directions are logged,
the reorder report falls out almost for free. Wire to the existing `StockMovement` model.

### P3 — Units of measure (box → unit)
Buy by the box, sell by the unit (rolling papers: box of 50, sold singly). Add
`units_per_pack` to the product so **receiving one box adds N selling units**
automatically. The schema concept already exists elsewhere in the code.

### P4 — Reorder report + purchase orders
Surface "what to reorder" from the low-stock + min/max/lead-time data that's already on
the product. Then optionally generate a PO to the supplier. Wire the existing
`PurchaseOrder` / `ReorderRequest` models.

### P5 — Languages (EN base, DE must)
English is the base language, full stop — Felix's stock is English-labeled (Gizeh ships
English-only). German next; FR/IT later. Design the language *structure* now so we don't
repaint, but don't block on translations — many items never need them.

### Deferred — AI enrichment / photo capture (v1.1)
Snap a photo at create-time (instant, counter-safe, no AI at the counter). Later, in calm
hours, an enrichment queue drafts name/description/category + EN/DE/FR/IT translations for
batch approval by Felix/Leanna. Feeds clean data into the "what sells most" report.

---

## The 5 design decisions (with recommendations)

1. **Unmarked items → label or picture-catalog?**
   *Recommend picture-catalog.* Their goods are ~100% unmarked; printing a barcode label
   per loose item is labor Felix will hate. Lazy-capture with no barcode (SKU auto-made) +
   a tap-to-find **picture catalog**. Reserve printed labels for rare high-value items.

2. **Units of measure in v1?**
   *Recommend yes, minimal:* a `units_per_pack` so receiving a box converts to sellable
   units. Decide if "I received 50 singles" is good enough to start (defer conversion) or
   box→unit is needed at launch.

3. **Receiving flow shape.**
   Manager-only screen, scan/confirm against the packing slip, writes a stock-movement.
   This is the single most valuable P2 build — it closes the in/out loop.

4. **Language structure now, content later.**
   EN base; add a language layer to the model now (cheap); fill DE as needed; AI drafts
   the rest later. Don't hand-translate 500 items.

5. **Who can do what (roles).**
   Create/edit/discontinue/receive = manager (Ralph) + admin (Felix). Cashier (Pam) =
   sell + lazy-capture-as-one-off only, until promoted. Already role-gated — promotion is
   a Keycloak role assignment, no code. (Optional future: a narrow `pos-keeper` role that
   grants create without full manager powers — for Pam on probation.)

---

## Felix's likely barrage → your answers

| He'll ask… | Answer |
|---|---|
| "How do I fix a wrong price / typo?" | P1 dashboard — edit any field, live. (API already there.) |
| "How do I get rid of an item?" | Discontinue = soft delete, history kept. Reactivate anytime. |
| "What happens when a box arrives?" | P2 receiving — scan, confirm, stock up, logged. |
| "How do I know what to reorder?" | P4 report from low-stock + min/max already on the product. |
| "I buy boxes, sell singles." | P3 units-per-pack; one box → N units. |
| "Can it be in German?" | EN base now, DE next; structure designed now. |
| "Can Pam do this?" | Role-gated; promote her when ready, no code. |

**The judo move:** the second he starts the barrage, say *"All on the roadmap — you're
customer #1, you tell me the order."* Hand him this page. He stops interrogating and starts
steering. That's the close.

---

## BL-100 — Product-matching integrity (the scan-trap / discontinued-dupe class)

**Status:** 📋 SPEC — raised 2026-07-14 after a live prod incident. Data patched by hand; code
hardening not built.

### The incident (what actually happened)
Mobile register, prod. Angel scans a can of **Tycoon Gas 250ml** → *"discontinued."* Root cause
was NOT a bug — it was a **bad match at intake weeks earlier**. Two rows existed:
- `REF-FOURTWENTY … "Tycoon dupe"` — old catalog-reference row, **discontinued**, but it still
  held the **real EAN off the can** (`4035687900004`) + the case code (`42425700`). Had 2 sales.
- `TAM-5851 "Tycoon Gas 250ml"` — the **live €6.90 item**, but only carried a *synthetic*
  placeholder barcode minted from its SKU (`2000000058511`) — nothing that's on the physical can.

Every scan hit the dead dupe (primary-barcode lookup wins) → `400 Product is inactive`. The live
twin never got a look-in. **Fix was a hand-patch:** moved the real barcodes onto the live row,
kept the placeholder as an alias, stripped the dupe (kept its 2 sales for history). Prod sweep
found only 2 other discontinued-with-barcode rows and both were harmless synthetic scrap items.

> **Angel's read (the real lesson):** *"the setup of a new product and matching it properly is the
> hardest part — if done wrong, complete disaster and needs patching."* The cost of a bad match is
> paid **later, at the till, by the cashier** — the most expensive place to discover it. Leverage
> is at **intake**, not at patch time.

### The failure mode, generalised
A **barcode is stranded on the wrong row.** It happens whenever the same physical good exists as
more than one product row and the code lands on the row you *don't* sell:
- an active twin lacks the real EAN (synthetic/placeholder barcode instead), OR
- the code sits on a **discontinued** row (dead-ends the scan), OR
- two active rows split the codes (scan is non-deterministic to the operator).

Root cause is upstream: **duplicates created + weak match at product setup / receiving.**

### The fixes (in leverage order — prevention first)
1. **Prevent the dupe at intake (highest leverage).** Receiving / create-product must *find-first*
   hard: before minting a new row, match on **barcode → SKU → fuzzy name+supplier** and surface
   *"Looks like this already exists: [live row]. Add barcode to it / edit it / create new anyway?"*
   Most of this rail exists (BL-90 alias capture, find-first search) — tighten it so the **default
   path is attach-to-existing**, and creating a true duplicate is the deliberate, harder choice.
2. **Deactivation releases its barcodes.** When a product is discontinued, **detach its barcodes**
   (or offer *"move barcodes to the replacement?"*). A dead row must never keep a scan-live code.
   One-liner in the discontinue handler + a migration to clean existing rows.
3. **Scan-to-inactive is a redirect, not a dead end.** When a scan resolves to an inactive product,
   don't throw a bare *"inactive."* Look for an **active product with the same barcode-family /
   name+supplier** and offer *"discontinued — sell the active replacement [Tycoon Gas 250ml] instead?"*
   Turns the cashier's dead end into one tap.
4. **Standing integrity sweep (the seal-check).** A cheap query, run on a schedule / surfaced in the
   hypercare cockpit: *discontinued rows that still hold a barcode* + *active rows whose only barcode
   is a synthetic `2…`/`LZ-`-derived placeholder while a sibling holds a real EAN.* Both are latent
   till-time traps. Report them before a cashier hits one. (Tonight's sweep was this query, by hand.)

**Priority:** (1) and (2) are the durable fixes — do them together (intake dedup + deactivation
detaches). (3) is a nice cashier-facing softener. (4) is a 20-minute report worth wiring into the
cockpit so we *find* traps instead of *scanning into* them. See the [[banco-terminal-collision]]-style
"prove don't assume" discipline: the data was green until someone actually scanned.

---

## BL-101 — Till search RECALL & RANKING (the "we don't sell that" false negative)

**Status:** 📋 SPEC — raised 2026-07-14, same session as BL-100. **Highest-value of the two** (a lost sale
leaves no error, so it's invisible). Not built.

### The incident
Angel, live till, looks for a **mini BIC lighter**. Searches for it → *appears not to be there.* He gives
up on the till, goes to the **Tamar supplier site**, finds the exact German title, comes back and searches
*that* — found. **A cashier who doesn't know Tamar's naming would conclude "we don't stock BIC lighters"** —
and we do. The lost sale throws no error; nobody ever learns it happened. That's what makes it worse than BL-100.

### The diagnosis — it's RANKING, not missing data
The item is well-formed: `TAM-9851 "Feuerzeug BIC mini"`, category `Feuerzeuge`, description *"BIC lighters
are characterized by…"*. Reproduced against the live `/pos/search` logic:

| query | what the cashier sees on screen one |
|---|---|
| `lighter` | `Lighter`, `LED Azlan UFO Light`, `LitLight`, `Northern Light` — **zero actual Feuerzeug lighters** |
| `bic lighter` | #1 is a product literally named `Lighter`; **"Feuerzeug BIC mini" isn't in the top 5** |
| `bick` / `mini bic` | ✅ surfaces "Feuerzeug BIC mini" #1 (trigram tolerates the typo) |

**Root cause:** `/pos/search` (`search_products_fast`, ~line 1785) matches `description ILIKE` — so the item is
*in the result set* — but **ORDERs by `similarity(name, :q)` ONLY**. The Artemis names are **German**
("Feuerzeug …"); the English is in the **description**. So an English query scores ~0 on the German name and
sinks below anything whose *name* coincidentally contains a token ("Light", "Lighter"). Description gets you
in the door but never to the top where a busy cashier looks. Multi-word queries (`bic lighter`) dilute the
name-trigram further.

**The kicker:** the **capture / photo search already solved this exact problem** (`search_reference_catalog`,
~line 409-423): it scores `GREATEST(similarity(name,:q), word_similarity(:q, name || ' ' || description))`
*specifically because* "the Artemis catalog NAME is German … the DESCRIPTION is the English text Artemis
publishes." **The till search just never got the same scoring.** Half the fix is porting one expression.

### The fixes (leverage order)
1. **Language-agnostic ranking (port the capture-search trick).** Change `/pos/search` ORDER BY to rank by
   `GREATEST(similarity(name,:q), word_similarity(:q, coalesce(name,'')||' '||coalesce(description,'')))`, not
   name-only. Cheap, no schema, no new data — floats German-named/English-described items to the top. Add the
   same term to the WHERE recall. **This alone fixes the BIC case.** Do it first.
2. **Word-token match, not whole-phrase ILIKE.** `description ILIKE '%bic lighter%'` needs the phrase
   contiguous; tokenise the query (AND of per-word `word_similarity`/ILIKE) so word order and multi-word
   queries stop failing.
3. **Brand + English-name enrichment (durable).** Add a `brand` field (BIC, Clipper, Storz & Bickel, RAW…)
   + a short English/common-name keyword blob per item, folded into search text. A brand is how people
   actually ask ("got any BICs?"). Fits the existing BL-98 enrichment queue — enrich, don't hand-edit 5,000 rows.
4. **Bilingual category synonyms (Feuerzeug ↔ lighter).** The category vocabulary is German. A small
   DE↔EN synonym map (Feuerzeuge=lighters, Mühle=grinder, Waage=scale…) expands the query so an English word
   reaches a German category. One curated table, ~30 rows covers the shop.

**Priority:** (1) is a one-expression change that fixes tonight's exact miss — ship it fast + a regression test
(assert "lighter"/"bic lighter" return "Feuerzeug BIC mini" in the top 5). (2)–(4) are the durable recall layer.
**The rule this incident teaches: a false-negative search is the most expensive failure in a shop because it is
SILENT — it looks like "we don't carry it," and only the operator's outside knowledge (go to Tamar) recovers it.**
