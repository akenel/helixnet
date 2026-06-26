# Banco Cafe VAT — Multi-Line Tax Build Plan + Season 2 Story Arc

*2026-06-26. The build plan for per-line dine-in/takeaway VAT (the Swiss moat no US POS can match),
structured so every build increment doubles as one Season 2 short. Spec it satisfies:
`docs/BANCO-CAFE-VAT-SPEC-2026-06-21.md`. Series bible: `videos/banco/SERIES-BIBLE.md`.*

> **The thesis (the Brendan pivot):** his video says tech keeps asking *"could we"* and never *"should we."*
> Season 2 is the answer in code: software that knows *this* shop's *this* canton's *this* law. The
> broken stone — "they didn't stop to think if they should" — becomes our cornerstone: we built the
> "should" (Swiss VAT law) directly into the till. The opposite of slop.

---

## CURRENT STATE (verified in code, 2026-06-26)

| Piece | Status | Where |
|-------|--------|-------|
| `product_class` on every product (drives VAT) | ✅ EXISTS | `product_model.py:109` |
| Catalog tagged by class (BL-96 taxonomy) | ✅ DONE | `catalog_taxonomy.py` |
| Single-rate inclusive VAT helper (8.1%) | ✅ EXISTS | `pos_router.py:1980 _inclusive_vat` |
| Per-line `consumption` flag (dine-in/takeaway) | ❌ MISSING | `line_item_model.py` |
| Per-line rate snapshot + resolver | ❌ MISSING | — |
| Two turnover streams in Z-report | ❌ MISSING | daily-summary |
| Receipt per-line rate + legend | ❌ MISSING | receipt render |
| QR-bill Swico S1 `/32/` multi-rate | ❌ MISSING | invoice gen |

**Translation:** the knowledge (which product is which class) is already in the data. We're adding the
*decision* (dine-in vs takeaway), the *math* (resolve + snapshot the rate per line), and the *proof*
(receipt + Z-report that print the split). A few focused days.

---

## THE BUILD — 5 increments, each a testable slice AND a short

### INC 1 — The Brain (`vat_resolver.py`) — pure function, no UI, no DB
The whole law as one deterministic function + a truth-table test suite straight from the spec §2.

```
resolve_vat_rate(product_class, consumption) -> Decimal
  ALCOHOL          -> 8.1   (always, Art. 25 MWSTG)
  TOBACCO/NICOTINE -> 8.1   (always — matters double for a head shop)
  CAFE_FOOD:
       DINE_IN     -> 8.1   (restaurant supply)
       TAKEAWAY    -> 2.6   (delivery of goods)
  everything else  -> 8.1   (retail goods / undocumented => FTA presumes standard)
```
- Rates come from config/data, NOT hardcoded (spec §1 — a rise to 8.5% is proposed).
- Default consumption = `DINE_IN` (spec §2: undocumented sale is *presumed* standard-rated; 2.6% must
  be the deliberate, recorded choice).
- **Deliverable:** `src/services/vat_resolver.py` + `tests/pos/test_vat_resolver.py` (the spec's truth
  table, ~12 cases, all green). Zero risk — pure logic. This is the cornerstone episode.

### INC 2 — Per-line consumption + rate snapshot (migration + add-item wiring)
- Migration: add to `line_items` → `consumption` (varchar, nullable, default `dine_in`), `vat_rate`
  (Numeric 4,2), `vat_amount` (Numeric 10,2). Additive, safe (create_all + alembic — mind the schema
  drift note: run the migration, don't rely on create_all ALTERing).
- `add_item_to_transaction` (`pos_router.py:1988`) calls `resolve_vat_rate(product.product_class,
  consumption)`, snapshots `vat_rate` + computes `vat_amount` via the inclusive formula on the line.
- `LineItemCreate` schema gains optional `consumption` (default dine_in; bad value → 422).
- **Deliverable:** migration + wiring + tests. A coffee added twice (dine-in vs takeaway) stores two
  different rates. **Screenshot: the same SKU, two rates, same cart.**

### INC 3 — Transaction totals + the split rollup
- On finalize, sum per-line `vat_amount` → `transaction.tax_amount` (replaces the hardcoded 0.00 at
  `pos_router.py:1811`). Store/derive `turnover_dine_in` vs `turnover_takeaway`.
- **Deliverable:** transaction total reconciles; the two turnover streams are queryable. Tests assert
  sum(lines.vat) == tax_amount and the streams add to subtotal.

### INC 4 — The Proof: receipt legend + Z-report split (the payoff screenshots)
- Receipt prints per-line rate as a coded legend (`A=8.1%  B=2.6%`) — spec §3, legally required.
- Daily summary / Z-report splits **dine-in turnover vs takeaway turnover** — the "two separated
  turnover streams" the FTA mandates (spec §3.4).
- **Deliverable:** a printed receipt + a Z-report that a Treuhänder would nod at. **The hero shot.**

### INC 5 — QR-bill multi-rate emitter (Swico S1 `/32/`) — finale / when Felix invoices
- Optional billing-info field: `/32/8.1:553.39;2.6:400.19`, with the hard reconciliation check (net +
  computed VAT must equal the QR total). Spec §5.
- **Deliverable:** invoice generator emits valid `/32/`; reconciliation test. Ship when invoicing is live.

> **Treuhänder gates (do NOT hardcode — spec §6):** accounting method (effective vs Saldosteuersatz),
> the re-ring workflow (recommend: confirm dine-in/takeaway *before* finalize), audit substantiation.
> Build the till to be correct; let Felix's accountant sign the method.

---

## SEASON 2 — "The Coffee That Costs Two Prices"

*Syd Field three-act. Angel reads the teleprompter raw + in voice; Tigs builds the Ken Burns slideshow
+ title cards via Puppeteer and captures the REAL app screens as each increment lands. We film the
build — the screenshots are earned, never faked. That honesty IS the content (the anti-slop proof).*

| # | Title | Act | Backs onto | The shot |
|---|-------|-----|-----------|----------|
| **S2E1** | The Coffee That Costs Two Prices | I — Setup | (story only) | The hook: same coffee, two legal prices. No US register knows this exists. |
| **S2E2** | The Brain | II — Build | INC 1 | The ESTV law → the pure function → green tests. "Here's the law. Here's the code. Here's the proof." |
| **S2E3** | The Toggle | II — Build | INC 2 | Cashier taps dine-in/takeaway — the rate flips live. Same SKU, two rates, one cart. |
| **S2E4** | The Z-Report | II — Build | INC 3+4 | End of day. Two turnover streams print apart. The compliance payoff. |
| **S2E5** | The Receipt (The Handshake) | III — Resolution | INC 4 | The printed receipt, A/B legend. Tie back: THIS is "should we." Software that knows the local law. |
| *S2E6* | *The Town Square* (optional) | III — Coda | (green LP beat) | Product flies to La Piazza, decoupled. The counter talks to the square. Bridge to next season. |

**Arc logic:** Act 1 states the impossible-for-others problem. Act 2 is the honest build (the struggle
Syd Field wants on screen) — three episodes, each closing one wire and earning its screenshot. Act 3
is the printed proof + the thesis landing. E6 loops back to the one beat that's *already green* (LP
publish) so the season ends on something live and opens the door to Season 3 (the integration).

**Why this beats a polished fake:** Brendan's whole point is that one-clicked, unverified output is
negative value. We do the opposite on camera — show the law, show the code, show the failing-then-green
test, show the real receipt. The build being real is the differentiator. We don't claim "it all works"
until the screenshot proves it.

---

## NEXT
1. Build INC 1 (`vat_resolver.py` + truth-table tests) — longest-pole brain, zero risk, fully testable.
2. Draft the S2E1 teleprompter script (story-only, no code needed) so Angel can record while INC 1 builds.
3. Then INC 2 → film S2E3, and so on. Build and film march together.
