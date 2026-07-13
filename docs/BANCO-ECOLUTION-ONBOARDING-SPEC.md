# Ecolution Supplier Onboarding — Build Spec (SANDBOX)

*The real artisan-supplier onboard. Angel plays manager **Ralph** receiving a delivery from **Sylvie
(Ecolution)** and enters the goods himself, "like a new guy — here's a box, figure it out." Sandbox
ONLY. Manual-first. The postcards must turn out perfectly (the 2026-07-13 maker). Written 2026-07-13
as the resume anchor after a compaction.*

Store facts + the community-loop rationale live in memory **`banco-ecolution-sylvie-supplier`**
(Sylvie Thiel · Lucerne · 16 yrs Etsy · 4.9★/721 · wholesale offered). This doc = the BUILD.

---

## The scenario (test = demo = method — Angel's favorite loop)
1. A box arrives from **Sylvie / Ecolution** (simulated delivery — no PO).
2. **Ralph (manager)** opens **Receiving** and enters the new goods.
3. New product ⇒ **NO EAN** (brand-new; mint a human code).
4. **Source = Etsy** (`etsy.com/shop/Ecolution`) — name, description, photos come from the listing.
   Working method: **Angel copy-pastes the Etsy item info to Tigs → Tigs sets up the item → Angel drops in the pictures.**
5. Enter as **proper, clean items** so the **postcard renders perfectly** (hero pieces → card + QR → her IG / `ecolution-craft.ch` / La Piazza).

## Pilot item (Angel to confirm the exact one)
- **Wool/Merino felt glasses case / eyewear sleeve** — "displays fantastic, ~15 colours in one box."
  Likely the Etsy *"Deluxe Wool Glasses Case – Merino Felt Eyewear Sleeve"* (CHF 34.59) or the upcycled version.
- **Start with ONE colour (gray)** — maybe 1–2 SKUs to prove the flow, not the whole rainbow.
- Display-box context: ~**24 pieces / ~8 colours** per display (Angel to confirm). Sylvie won't ship 24 grays → it's an **assortment**.

## The supplier record to create
- **Ecolution / Sylvie Thiel** · contact = Sylvie · `etsy.com/shop/Ecolution` + `ecolution-craft.ch` + IG `ecolution.switzerland` · Lucerne studio · **wholesale offered** (get her list) · custom orders welcome.

---

## Open design questions — HIT THESE FRESH (this is why it's a "new build")
1. **Supplier create UI** — does Banco have a manual "add a supplier" seam (name / contact / website / address)?
   The live-search suppliers (Artemis / FourTwenty / Near Dark) are *adapters*; a **local maker** like Ecolution
   is a plain manual supplier. If the seam's missing, build it. (See [[banco-local-maker-onboarding]].)
2. **Etsy as a SOURCE-TYPE** — per the doctrine "the adapter differs per source-type, not per seller."
   Manual-first: paste an Etsy item URL → pull name/desc/photo/price. Could be copy-paste + Tigs-assist now,
   a tiny Etsy-URL fetch later. **Scope it, don't over-build.**
3. **Variants / colours** ⚠ the real modelling question — one product with colour variants, or N separate
   products? Does Banco model variants today? A display box = an **assortment** (e.g. 8 colours). Design how you
   RECEIVE and LIST an assortment so it doesn't become 15 near-dupe items or one messy blob.
4. **Receiving a brand-new (no-EAN) product** — the receiving flow needs an "add new product while receiving"
   path (mint code, set supplier cost, shelf price). Confirm it exists (RECEIVING-POC) or build the gap.
5. **Wholesale → margin** — store Sylvie's wholesale as `supplier_price`, Felix's shelf price on top (existing
   price-comparison rails: [[banco-supplier-price-comparison-spec]]).

## Guardrails
- **SANDBOX ONLY.** Manual-first. Sell-first (a curated pilot, not all 93 items). Postcards perfect.
- Reuse existing rails wherever possible (receiving, supplier model, photo→product/find-first, postcard maker) —
  build only the genuinely-missing seams (supplier-create, Etsy-source, variants).

## Resume ritual
**ON DECK → open this spec.** Angel = Ralph, simulated Sylvie delivery, enter as new items in **sandbox**,
render the postcard. Real-world parallel tomorrow (2026-07-14 AM): Felix demo in Littau + the new hire (starts Thu).
