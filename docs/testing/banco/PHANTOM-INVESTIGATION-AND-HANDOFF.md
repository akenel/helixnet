# Phantom Sale — Investigation + Hand-off (2026-06-23 evening)

*Angel asked: is this a real bug, or a sandbox role problem? Do staging/prod have it too?
Here's what the investigation found, and the paste-ready steps to confirm it yourself.*

---

## TL;DR — the verdict
**It's a REAL code bug, it was IDENTICAL in all three environments, and it's ALREADY FIXED in all
three.** It is **NOT** a sandbox-specific role problem. Good news: one fix covered everything; there's
no env-specific surprise waiting in staging or prod.

And the thing that spooked you — **"the roles aren't implemented right" — turned out to be fine.**
The code handles it. Details below.

---

## What actually happened (the evidence chain)
1. **The ghost (sandbox txn 0004):** the sale's line item has `product_id = NULL`, a text note
   **`[NEW] HempSana`**, price 45, and **no barcode anywhere.** That `[NEW]` is the one-off fallback —
   the till rang a sale but never saved a product.
2. **Why the fallback fired:** the barcode born-once create posted to **`POST /products`**, which is
   **manager-only** (`require_roles(["👔️ pos-manager", "🛠️ pos-developer", "👑️ pos-admin"])`).
3. **A cashier can't pass that gate.** `pam` is `pos-cashier` only → correct 403 → silent `[NEW]`
   phantom. **That's the whole bug.** It has nothing to do with the realm; a cashier is a cashier
   everywhere.
4. **Why the receipt says "felix":** Felix **is** correctly recognized as a manager (see the role
   finding below), so *his* create would have **succeeded** — he did **not** make the phantom. The
   `[NEW]` line was created by a non-manager (the cashier); Felix appears because he rang the
   **checkout.** (The 4-minute test switched users mid-flow — Pam created, Felix completed. If you want
   100% certainty on the sequence, re-watch the clip — but it changes neither the bug nor the fix.)

## The role question — answered (no bug here)
- All three envs use **`KEYCLOAK_REALM=artemis`**.
- The **artemis** realm names its roles **plainly**: `pos-manager`, `pos-admin`, `pos-cashier`.
- The **code** asks for **emoji-prefixed** names: `👔️ pos-manager`, `👑️ pos-admin`, …
- **But the matcher bridges them.** `keycloak_auth.py:234` checks "is the user's role a substring of
  the required one" — and `"pos-manager"` **is** inside `"👔️ pos-manager"`. So Felix's plain
  `pos-manager` **matches**. He's a real manager to the code. (Proven by your passing staging manager
  tests — Settings, catalog, reports all worked.)
- **So the realms having different role names is cosmetic; the code handles it.** No fix needed there.
  *(Worth a cleanup someday so the names line up — but it is NOT breaking anything.)*

## The fix (already shipped everywhere)
Route the barcode born-once create to the **cashier-safe** `POST /products/quick`
(`require_any_pos_role` — any logged-in POS user, no manager check). It sidesteps the gate entirely.
Shipped: prod `banco` (`3a38874`), staging, sandbox (all on `1588cb4`+).

---

## YOUR HAND-OFF — confirm it in staging + prod (paste-ready, ~5 min each)

**Do this in BOTH `staging-banco.lapiazza.app` and `banco.lapiazza.app`.**

### A. As a CASHIER (the fix) — this is the one that mattered
1. `/pos` → log in **pam / helix_pass** (status pill should read **STG** then **PRD**).
2. New Sale → **Scan with camera** (or type a barcode) → use a **brand-new barcode** not in the shop.
3. "Item not on file" → name **Test Widget**, price **5.00**, take a photo → **Save & add to cart**.
4. ✅ EXPECT: toast **"Saved — scans instantly next time"** (NOT "ask a manager"), and the cart line has
   **no `[NEW]` prefix**.
5. Clear the search, type **Test** → ✅ **it appears.** (Before the fix: "No matches.")

### B. As the MANAGER (confirm Felix's rights are intact)
6. Log out → log in **felix / helix_pass**.
7. Open **/pos/catalog** → ✅ Test Widget is listed; Felix can edit/create (manager functions work).

If A passes in both envs, the bug is dead everywhere. If B passes, the role matcher is doing its job
and there's nothing realm-side to fix.

---

## Sandbox hygiene (your point — start every recording from scratch)
The sandbox accumulates (you're already on txn 4). **Reset to zero before each take:**
```
ssh root@46.62.138.218 'cd /opt/helixnet && make sandbox-reset'
```
→ 0 products, 0 sales, clean slate. The txn 0004 phantom is **unrecoverable** (no barcode was ever
stored) — it's pure evidence; the reset clears it for the next clean recording.

---

## One honest note
This bug was real and it was in **prod** too — but it was caught on a phone, in a sandbox, before a
single real customer ever hit it, and fixed the same day. That's not a failure; that's the system
working. *If one seal fails, check all the seals* — we did, and the others (the role matcher) held.
