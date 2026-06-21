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
2. **BL-83** — ✅ **BUILT + on staging (`2bd019d`), awaiting Angel PASS.** `list_transactions`
   resolves `cashier_id` (== `users.id`) to a display name in one batched lookup; `TransactionRead`
   gains `cashier_name`; the report shows it (drops the misleading "Cashier" literal) and no longer
   repeats the txn number under the receipt# on open carts. Verified live: 129 rows show Felix (116) /
   Pam (13). Test: `tests/pos/test_pos_cashier_name.py`. (Time-of-day already renders on this view —
   Felix's "no timestamp" note was about the shift-close log, not the transactions report.)
3. **BL-85** (CSS-only responsive status bar) — NEXT.

**One pass, same two files** (`transactions.html` + `base.html`) plus a small `pos_router` /
`transaction_model` add for the cashier name. Then the standard gate:
**staging → `make test-pos` + Playwright E2E → Angel PASS on staging → re-deploy the Banco prod
container** (reset `/opt/helix-banco-tree` to new `origin/main`, recreate `helix-platform-banco`).

**Do NOT touch** the divergent Bottega `helix-platform` tree (#140).

---

## BL-86 (teed up) — End-of-day reaper for stale empty carts

**Origin:** Angel spotted it in Felix's own data — a pile of `OPEN` / CHF 0.00 (and a few
CHF 10.00) transactions cluttering the report. **Real, not just a test artifact:** in the
live shop a cashier opens a sale and the customer walks, or Felix opens a cart in the back
and never closes it. They accumulate as dangling `OPEN` rows.

**What it is:** a small scheduled job that retires abandoned carts so the report stays clean.

**Proposed rule (needs Angel's nod on the thresholds):**
- Target: transactions with `status = OPEN`, **no line items** (or `total = 0`), older than
  **N hours** (default 12 — i.e. anything still open from earlier in the day).
- Action: set `status = CANCELLED` (auditable) rather than hard-delete — keep the trail,
  don't lose the number. (Open question for Angel: cancel vs delete.)
- Cadence: **end-of-day** (e.g. 23:30 shop-local) + optionally hourly during the day.
- Safety: never touch a cart that has items or a non-zero total; never touch `COMPLETED`/
  `REFUNDED`; log how many it reaped (no silent sweeps).

**Where:** a reaper function in `pos_router`/a service + a schedule. Check how other jobs are
scheduled in this repo before adding a new mechanism (don't invent a second scheduler).

**Decisions (Angel, 2026-06-21):** CANCEL (not delete) · **12h** threshold · **zero-value only**.

✅ **SHIPPED to prod (`3c29154`, 2026-06-21).** Includes hide-cancelled (default
transactions view excludes CANCELLED; reachable via the "Cancelled" status filter).
- `reap_stale_open_carts(db, older_than_hours=12)`: cancels carts that are `OPEN` AND
  `total==0` AND have **no line items** AND `created_at < now-12h`. Sets `CANCELLED` +
  `updated_at`, keeps the number. Idempotent; never touches carts with items or any value.
- `POST /api/v1/pos/maintenance/reap-empty-carts` (manager/admin) — manual/on-demand.
- **Hourly background loop** in the app lifespan (Celery Beat isn't deployed here; single
  uvicorn worker → runs once per container, idempotent on the shared DB; a bad tick logs and
  continues, never crashes the app).
- Test `tests/pos/test_pos_reaper.py` (3): old empty cart cancelled, cart-with-items spared,
  fresh cart spared. **Live staging proof:** cancelled 11 real 06-20 carts (>12h), spared
  today's (<12h) and the non-zero CHF 10 ones.

**Note:** today's CHF 0.00 OPEN carts get reaped automatically ~12h after they were opened
(by tomorrow morning). The CHF 10.00 OPEN carts are non-zero → deliberately NOT reaped (zero-
value-only). A "hide CANCELLED from the default list" tweak is an easy follow-up if you want
the rows gone from view entirely, not just marked dead.
