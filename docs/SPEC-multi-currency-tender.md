# SPEC — Multi-currency tender (accept foreign money at a set rate)

*Status: building 2026-07-18 · ties `banco-currency-conversion-plan`, `banco-go-italian-doctrine`,
`banco-competitive-swot-2026-07` (the cross-border empty-lane moat), `banco-money-cent-precision`.*

## The principle (get this right or nothing else matters)

Two different currencies, kept strictly separate:
1. **Home / books currency** — what prices, VAT, totals and the Z-report are IN. Lucerne = CHF. **Exactly one,
   always.** Never dual-price the catalog; never mix the books. (This is the `store_settings.currency` field.)
2. **Tender currency** — what the customer physically hands over (a tourist's EUR cash). Accepted at **the shop's
   own plan-rate**, but the sale is still **recorded in the home currency.**

So "multi-currency retail" = **price + account in one home currency, ACCEPT foreign tender at a set rate.** Exactly
how every Swiss tourist shop takes EUR.

## What already exists (reuse, don't reinvent)

- `src/services/currency.py` — flat plan-rate FX: `DEFAULT_FX` (`{base:CHF, rates:{EUR:0.96,USD:0.88,…}}`),
  `load_fx(json)`, `convert(amount, from_ccy, base) → {base_amount, rate, as_of}`. Rate = **base units per 1 foreign
  unit** (`base = foreign * rate`). Per-shop override on `store_settings.fx_rates` (JSON), else `DEFAULT_FX`.
- Today it only powers supplier-price DISPLAY. We wire it into Settings + checkout + the drawer.

## The till flow

1. Cart total is home currency: **TOTAL CHF 8.55**.
2. Cashier picks **"Pay in EUR"** → till shows **≈ EUR 8.91** (`base / rate`, the inverse of `convert`).
3. Customer pays EUR cash; cashier enters what was handed over.
4. **Change is given in the HOME currency (CHF)** — the drawer's home float. Simple + standard.
5. Sale is **recorded as CHF 8.55** (books untouched); the EUR amount + rate are stored as **tender detail** for
   the drawer. Cards self-handle (DCC on the customer's bank) → this is a **cash** feature.

Sandbox mirror: Roma (home EUR) accepts CHF at a set rate — the exact reverse, ideal test bed.

## Blocks

### ✅ Block 0 — rates editor + checkout courtesy (no data-model change, zero risk)
- `currency.py`: add `to_tender(base_amount, ccy, fx) → {tender_amount, rate, as_of}` (home → foreign; `base/rate`).
- Settings → Tax: an **"Accepted currencies & rates"** editor (ADMIN-only, beside the currency field) — edits
  `store_settings.fx_rates` (base = the home currency; rows of {currency, rate}). Same add/remove-row pattern as the
  VAT table. Server: `fx_rates` accepted in the update schema, validated + JSON-serialised, **admin-only** (stripped
  for managers, same seal as currency/discounts).
- `/pos/config`: return the shop's `fx` (accepted currencies + rates) so the client can convert.
- Checkout: a read-only **"≈ EUR 8.91 · USD 9.72"** courtesy line under the total. Pure display.

### Block 1 — record foreign CASH tender
- `transactions`: + `tender_currency VARCHAR(8)`, `tender_amount NUMERIC(12,2)`, `tender_rate NUMERIC(12,6)` (all
  nullable; NULL = paid in home currency, byte-identical to today). `total`/`subtotal`/`tax` stay HOME currency.
- Checkout: when the cashier chooses a foreign tender, they enter the **foreign amount tendered**; the server
  converts to home at the shop rate, computes **change in the home currency**, and stamps the tender detail. Cash
  drawer gate still applies (a foreign-cash sale is a cash sale).
- Receipt: show "Paid EUR 10.00 @ 0.96 → CHF 9.60, change CHF 1.05".

### Block 2 — drawer reconciliation for foreign cash
- `cash_shifts`: + `foreign_tender_json` (per-currency totals taken this shift) so close-out knows how much EUR/USD
  cash *should* be in the drawer, and `foreign_counted_json` (what the cashier counted per currency at close).
- Close-out: show a per-currency breakdown; the cashier counts foreign notes per currency; the system converts each
  to home at the plan rate and folds it into `counted_cash` so `expected vs counted` still balances in home currency.
- Honest MVP: home-currency change means the drawer accumulates foreign notes only from the tendered side; the
  reconciliation converts them back at the SAME plan rate, so it balances by construction (real-world FX drift on the
  physical notes is the shop's spread, surfaced as a small over/short — acceptable + visible).

## Rules that apply
Money at cent precision (quantize first) `banco-money-cent-precision`; never hardcode a currency (read
`_store_currency`); admin-only fiscal fields stripped server-side; schema ALTER is manual (`create_all` won't);
machine-green ≠ human-green (a real foreign-cash sale on sandbox). Sandbox-first; NOT prod without Angel's push.
