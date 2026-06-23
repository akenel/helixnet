# BL-BUG — Cashier scans a NEW barcode → product sold but never saved (phantom)

**Found:** 2026-06-23, Angel, on Fairphone (mobile), sandbox-banco.lapiazza.app, logged in as **pam (cashier)**.
**Source:** `docs/testing/banco/fp ... bug video_2026-06-23_13-26-03.mp4`
**Severity:** HIGH — silently breaks the core "born once / scan once, known forever" promise for the
most common real case (a cashier scanning a brand-new barcoded item). Not a crash; a *silent data loss*.

---

## What happens (repro)
1. Log in as **pam (cashier)** on mobile.
2. New Sale → camera scan a **brand-new barcode** (`7649590831060`).
3. "Item not on file" → fill **name = HempSana**, **price = CHF 45**, take a **photo** → Save & add to cart.
4. Cart shows **`[NEW] HempSana`** (note the `[NEW]` prefix).
5. Checkout → 10% member discount → **TWINT** → receipt prints, **+60 points** to larry. Sale completes.
6. Back on New Sale, search **"He"** → **"No matches."**

**Confirmed in the DB:** `SELECT … FROM products WHERE name ILIKE '%hemp%' OR barcode='7649590831060'`
returns **0 rows**. HempSana was **never persisted**. (The search function is fine —
`search_products('He', …)` returns nothing because there is nothing to find.)

---

## Root cause — two born-once paths, gated differently
| Path | UI call (`scan.html`) | Endpoint | Gate | Cashier? |
|------|------------------------|----------|------|----------|
| No-barcode quick create | line 716 | `POST /products/quick` (`pos_router.py:155`) | `require_any_pos_role()` | ✅ allowed → **persists** |
| **Barcode** lazy-capture | **line 846** | **`POST /products`** (`pos_router.py:130`) | `require_roles(["👔️ pos-manager","🛠️ pos-developer","👑️ pos-admin"])` | ❌ **403 → phantom** |

A cashier scanning a new barcode hits the **manager-only** `POST /products` → **403**. `scan.html` catches it
(line 868-871) and **falls back to a one-off cart line** (`id: 'otf-' + Date.now()`, `name: '[NEW] ' + name`,
line 742 / 871) "so the sale never blocks." The sale completes against a **transient item that is never
written to `products`.**

So: the no-barcode path (Christina's cups) is cashier-safe and persists; its **barcode twin silently
doesn't.** *If one seal works, check the identical seal next to it.*

---

## Fix (for the forge terminal — this is the war-room write-up only)
1. **Route barcode born-once through the cashier-safe create.** Point `scan.html:846` at
   `POST /products/quick` (which already sets `is_active=true`, defaults category "On the fly", and allows
   `require_any_pos_role`) — adding the barcode to the payload — instead of the manager-only `POST /products`.
   *(Alternative: relax `POST /products` to `require_any_pos_role` for the minimal born-once create, but
   that muddies "full catalogue management is manager-only"; routing through `/products/quick` is cleaner.)*
2. **Make the fallback visible.** When the create genuinely can't persist, the one-off line must tell the
   cashier: a toast like *"Rung as a one-off — not added to the catalogue."* Right now it only `console.warn`s,
   so the cashier believes they created a product. Silent data loss is the real danger.
3. **Optional hardening:** the `[NEW]` one-off should be the *exception* (true offline/permission edge), not
   the default for any cashier scanning a barcode.

## Regression test to add
- As **cashier**: scan an unknown barcode → create → **assert the product row exists** in `products`
  (`is_active=true`, category "On the fly", barcode set) **and** that searching its name returns it.
- Guard both paths (with-barcode and no-barcode) so this can't drift apart again.

## Check-all-the-seals sweep (other POST /products callers)
- **`scan.html:846`** — the reported phantom. **FIXED** → now `POST /products/quick` (cashier-safe).
- **`catalog.html:417`** — full catalogue CRUD. **Correctly manager-only — leave as-is.**
- **`receiving.html:263`** — goods-in create. Hits the same manager-only `/products`, BUT it **fails
  loudly** (`showToast('Could not create the product','error')`, no one-off phantom) — so it's a UX
  block, not silent data loss. **For the forge (its active file):** if cashiers do receiving, route
  this to `/products/quick` too (carries `stock_quantity:0`, which `/products/quick` accepts).

## Note for the intro video
The "scan once, known forever" demo must be shown on a path that actually persists (no-barcode quick
create, or as a manager) until this lands — otherwise the very claim the video makes is the bug.
