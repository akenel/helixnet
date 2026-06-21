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
