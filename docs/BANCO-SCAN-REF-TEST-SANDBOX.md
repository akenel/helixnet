# Banco — Scan-Miss → Reference Lookup — Sandbox Test Sheet

**Where:** https://sandbox-banco.lapiazza.app → **New Sale** → **📊 Barcode**
**Build:** b1533 `e7d0855` (feat/scan-ref-barcode-autolookup)
**Date prepared:** 2026-07-05
**What we're testing:** when you scan a barcode that isn't in the live catalog, the
exact supplier match (photo + price, one-tap adopt) now pops up **automatically** —
no typing. Before the fix, the box sat empty and told you to type a name.

You can **scan** the code with the camera OR just **type it** in the barcode box and
hit Enter — same path either way. Each code below is verified in the sandbox right now.

---

## TEST 1 — THE FIX: barcode-miss auto-finds the reference match  ⭐ the one that matters
**Type/scan:** `42238089`  (GIZEH Papers KingSize Slim)
**Expect:**
- "Not on file" modal opens.
- **Without you typing anything**, a purple **"From reference"** row appears:
  *GIZEH Papers KingSize Slim*, FourTwenty, photo, **CHF 3.00**.
- Tap it → price box pre-filled 3.00 → **Add to shop** → lands in the cart.

✅ PASS if the match appears on its own. ❌ FAIL if the box is empty until you type.

---

## TEST 2 — CONTROL: a code already in the live catalog adds instantly (no modal)
**Type/scan:** `2000000228457`  (Elements King Size — already a live product)
**Expect:** goes **straight into the cart**, green toast, no "Not on file" modal.
Proves normal scanning is untouched.

---

## TEST 3 — BINDING STICKS: adopt once, then it's known forever
1. Do TEST 1 (adopt `42238089`).
2. Clear the cart.
3. Scan/type `42238089` **again**.
**Expect:** this time it adds **instantly** like TEST 2 — no modal. The scanned
barcode is now bound to the real product. This is the "known on every future scan" promise.

---

## TEST 4 — TYPE-A-NAME still works (manual search unaffected)
**Type/scan** any miss (e.g. `42404910` GIZEH KingSize Slim Pink), then in the modal
**type** `gizeh` in the "What is it?" box.
**Expect:** a list of Gizeh matches (live + reference) to pick from. Proves the old
typed-search path still works alongside the new auto-lookup.

---

## TEST 5 — GENUINELY NEW: nothing anywhere → clean fallback to "add as new"
**Type/scan:** `9999999999999`  (not in live, not in reference)
**Expect:** modal opens, auto-search finds nothing, you see
*"No match in the catalog or reference. If it's genuinely new, add it below."*
→ tap **"Add it as a new item"** → name + price → Save & add to cart.
Proves the last-resort path is still there and never dead-ends.

---

## TEST 6 — YOUR REAL GIZEH BOX  📦 (the honest edge case — read this)
Scan the **actual barcode on your physical Gizeh papers.** Two possible outcomes:

- **It matches** → 🎉 the reference row pops up. Perfect.
- **It does NOT match** → this is **expected and not a bug.** The reference catalog
  holds **FourTwenty's** barcodes. If your Swiss retail box carries a different EAN
  than FourTwenty's record, it won't match by barcode. Fall back to **typing "gizeh"**
  (TEST 4) and adopt from there. When you adopt, TEST 3 kicks in — your box's real
  barcode gets bound, so it scans instantly forever after.

> This is the key thing to understand: a "no match" on a real box means the supplier
> dump doesn't have that exact EAN — not that the feature is broken. The name-search +
> adopt path is the safety net, and it teaches the system your barcode permanently.

---

## More real codes to play with (all verified in sandbox, all reference-only misses)
| Barcode | Product | Price |
|---|---|---|
| `42238089` | GIZEH Papers KingSize Slim | 3.00 |
| `42488583` | GIZEH Papers Unbleached King Size Slim + Tips | 3.00 |
| `42404910` | GIZEH Papers KingSize Slim Pink Edition | 3.00 |
| `4002604431002` | GIZEH Active Filter 6mm 34pcs | 11.10 |
| `4002604101004` | GIZEH Active Filter 8mm 10 Stk | 3.30 |
| `0016165005262` | Juicy Jays Blunt Wraps Tropical | 1.80 |

**Live-catalog control (instant add, no modal):** `2000000228457` Elements King Size.
**Nothing-anywhere (new-item fallback):** `9999999999999`.

---

## What to report back
For each test: ✅ / ❌ and anything that felt slow, confusing, or wrong.
Especially watch: does the reference row show **on its own** (TEST 1), and does a
photo load or fall back to the 📦 tile without breaking anything.
