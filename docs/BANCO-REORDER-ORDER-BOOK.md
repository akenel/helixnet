# Banco — Reorder / "Order Book" (design note, not built)

*2026-06-28. Captured live from Angel thinking out loud while we built catalog sort. The
question that kicked it off: **"how do you do reorder properly with zero-perpetual-inventory?"**
The answer is the "creative thing" he sensed — you don't run MRP off on-hand stock; you lean
on what you reliably know and let the human do the part only they can.*

*Pairs with [BANCO-INVENTORY-ROADMAP.md](BANCO-INVENTORY-ROADMAP.md) (P4 reorder). NOT BUILT — future.*

---

## Why classic reorder doesn't fit

MRP / reorder-point planning needs **perpetual inventory**: trusted on-hand + on-order + demand
→ compute what to buy. Banco deliberately has **zero-perpetual-inventory** — the on-hand count
is a lie for the ~100% unmarked goods, and the till **never blocks a sale on a stock number**.

**Why that's actually fine (Angel's key point):** the *physical item is the inventory check*.
You can only ring up what you're physically holding / can scan. If the shelf is empty, the
cashier simply can't sell it — reality is the gate, not a count. *"If you can't see it, you
shouldn't be selling it."* So a digital "0 in stock" is irrelevant: holding it = it exists;
empty shelf = nothing to ring. Blocking on a (wrong) count would only create false "can't sell"
errors on items that ARE there — worse than useless.

## How the shop actually reorders (observed reality)

They **walk the floor and eyeball it** — "running low on these, sold out of those" — and
**pencil a list**, then hand it to the supplier rep. No thresholds, no calc. The rep even
catches doubles: *"that's on the next order already, why are you ordering it again?"*

## The reframe: an Order Book fed by what we DO know

Don't calculate from on-hand. Build a shared **Order Book** (the digital pencil list) fed by
three reliable sources, with the human deciding:

1. **Sales velocity = rock solid.** The till records every sale, so we know exactly what sold
   and how fast ("20 of these in 2 weeks") — reliable even with zero-perpetual. The system can
   *suggest* fast-movers; it never *insists*.
2. **On-order STATE = the one new thing to track.** When an item goes on an order, mark it
   "on order (qty, eta)". That kills the double-order problem AND lets you tell a customer
   *"I can have that for you next week."* No on-hand math needed — just order state:
   **to-order → on-order → received**.
3. **The human eyeball = the on-hand judgment.** The person walking the floor supplies what
   the system can't know. The Order Book just *remembers* it.

## Two kinds of entry in the Order Book

- **Restock** — "we're low / sold out, get more" (eyeball + velocity hint).
- **Customer special-order** — *"Larry wanted the extra thing — don't forget to order it,"*
  "I can get that delivered tomorrow/next week." A request tied to a customer, ordered
  specially, and ideally **notify the customer when it arrives** (ties to the La Piazza
  loyalty/identity link).

## Shape (future build — keep it light, NOT MRP)

- A `reorder_items` / order-book table: item (catalog ref OR free-text for not-yet-stocked),
  qty wanted, reason (restock | customer-request), customer_id (optional), supplier, status
  (to-order | on-order | received), eta, note. Product already holds supplier_name,
  lead_time_days, min/max_stock (use as *hints*, never gates).
- **Add to Order Book** from: the catalog (a button on a product), a sale (customer asks for
  X we don't have → capture it), or free-typed.
- **Generate a supplier order** = group to-order items by supplier → a printable/exportable
  order form → marks them on-order.
- **Receive** = mark on-order items received (no stock-count reconciliation required;
  optional bump to the informational count).
- Sales-velocity **suggestions** = a side list "selling fast, not on order" — advisory only.

## Guardrails

- It's an **assistant to the pencil list**, not a planner. Suggest, don't decide.
- Never gate sales on any of this (zero-perpetual stays).
- Respect the promo-restricted classes if any pricing/promo ever attaches.
- Standard terms: this is "replenishment / purchasing", the customer part is "special orders /
  back-order". Ours stays deliberately lighter than ERP purchasing.

---

*"You can order that and have it delivered tomorrow or next week… don't forget the extra thing
Larry wanted." — Angel, 2026-06-28. The system's job is to remember + track order state; the
human walks the floor.*
