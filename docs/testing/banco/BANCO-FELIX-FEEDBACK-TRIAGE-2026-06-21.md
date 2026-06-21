# Banco — Felix live-feedback triage (2026-06-21)

**Source:** 3 feedbacks filed from `banco.lapiazza.app` on an Android phone (viewport 411×695,
Europe/Zurich), 14:23–14:25 today — real-world use of the new **transactions / shift report**
screen. Backlog items **BL-83, BL-84, BL-85**. (The 14 items at 09:10 are test-suite fixtures —
ignore.)

All three live on **one screen** (`/pos/transactions` → `src/templates/pos/transactions.html`)
plus the global status bar (`src/templates/pos/base.html`). One tight fix pass.

---

## BL-84 (🔴 HIGH) — payment totals collapse to "cash"

**Felix:** "shows total transactions but it all shows as cash — should say debit card, TWINT,
cash, and maybe bank transfer."

**Root cause (confirmed in code):**
- `transactions.html` summary shows only **2 buckets**: *Cash Sales* + *Card/Mobile Sales*
  (lines 66–72, JS reducer 211–216 buckets `cash` vs `['card','mobile']`).
- The per-row payment pill only colours `cash / card / mobile` (lines 121–126), but the real
  `PaymentMethod` enum is **`CASH / DEBIT / TWINT`** (+visa/crypto/other) — so TWINT/debit rows
  render with the grey "none" style.
- **The backend already has the full split:** `DailySummary` returns
  `cash_total / visa_total / debit_total / twint_total / crypto_total / other_total`
  (`pos_schema.py:198`). The UI just isn't using it.

**Fix:** point the summary cards at the real `/reports/daily-summary` buckets (Cash · Debit ·
TWINT · Visa · Other), and fix the row pill colour map to the real enum values.
**Open product Q for Angel/Felix:** "bank transfer / IBAN" is **not** a current payment method —
add `BANK_TRANSFER` to the enum, or leave out? (Don't auto-add — flag it.)
**Effort:** S (frontend) + tiny if we add a payment method (additive enum + migration).

## BL-83 (🟡 MED) — line detail: duplicate header, no cashier name, weak time

**Felix:** "transaction is bold which is great but underneath it's the same info = wasted space;
should show the cashier's name; no timestamp, just the date — want the time for stats/sorting."

**Root cause (confirmed in code):**
- **Duplicate line:** row col 1 shows `receipt_number || transaction_number` **bold** (line 108)
  then `transaction_number` **underneath** (line 109) — identical whenever `receipt_number` is
  null (the demo case). Exactly what Felix saw.
- **"Just says Cashier":** template reads `txn.cashier_name || 'Cashier'` (line 116) but
  `list_transactions` returns raw `TransactionRead` (`pos_router.py:881`) which has **no
  cashier_name** (only `cashier_id`, a Keycloak sub) → always falls back to the literal "Cashier".
- **Time:** the row does render `formatTime` (line 113) — verify on mobile it isn't clipped; the
  real gap is cashier name + the duplicate, and making time first-class.

**Fix:** (a) drop/repurpose the duplicate second line; (b) **return a cashier name** — cleanest is
an additive `cashier_username` column on `transactions`, stamped at checkout from the token (same
pattern the shift log already uses via `CashShiftModel.username`), surfaced in `TransactionRead`;
(c) confirm time shows on mobile.
**Effort:** M — the cashier-name piece is a small backend add (additive column + checkout stamp +
schema), the rest is frontend.

## BL-85 (🟡 MED) — status bar cramped in mobile portrait

**Felix:** "in portrait the status line is crunched, can't reach the health-check icon far right;
landscape is fine."

**Root cause:** `.helix-status-bar` (`base.html:130`) is a single fixed-footer flex row
(pulse · text · time · version · sha … + right section with the health link) — at 411px portrait
it overflows and the far-right health link falls off-screen / unreachable.

**Fix:** make the bar responsive — `flex-wrap`, drop dividers on narrow widths, and/or keep the
health link pinned/reachable (e.g. collapse the middle on `max-width` portrait). CSS-only.
**Effort:** S.

---

## Build order & gate

1. **BL-84** — ✅ **BUILT + on staging (`3f19dfc`), awaiting Angel PASS.** Added `BANK_TRANSFER`
   to the enum; replaced the 2-bucket summary with a real per-method breakdown; row pills + filter
   fixed; Banana CSV gains the bucket. Tests: `tests/pos/test_pos_bank_transfer.py` (3) + reports
   sum-invariant updated — green. **Root cause confirmed on live staging data:** the day held
   *visa CHF 24,852 + twint CHF 915 + cash CHF 3,837*, but the old UI only summed `cash` and
   `card`/`mobile` — and the real data is `visa`/`twint`, so ~CHF 25k rendered as **zero**. That's
   the "it all shows as cash." Now every bucket shows.
2. **BL-83** (cashier name = small additive backend, rest frontend) — NEXT.
3. **BL-85** (CSS-only responsive) — after.

**One pass, same two files** (`transactions.html` + `base.html`) plus a small `pos_router` /
`transaction_model` add for the cashier name. Then the standard gate:
**staging → `make test-pos` + Playwright E2E → Angel PASS on staging → re-deploy the Banco prod
container** (reset `/opt/helix-banco-tree` to new `origin/main`, recreate `helix-platform-banco`).

**Do NOT touch** the divergent Bottega `helix-platform` tree (#140).
