# Banco — Top 10 Reports (brainstorm)

The reporting layer. **Everything rides the sales log** — in zero perpetual inventory there
are no stock counts to trust, so reports are built from what actually *sold* (velocity), not
from a count. Each report below: what it answers · who reads it & how often · **data readiness**
(✅ have the data today · 🟡 partial · 🔨 needs new capture).

The engine exists: `get_daily_summary` (just enriched — totals, payment split, top-3, avg basket,
items sold, busiest hour, per-cashier). Most of the Top 10 are *angles on that engine over a date
range*, not new plumbing.

---

| # | Report | Answers | Who / cadence | Data |
|---|--------|---------|---------------|------|
| **1** | **Daily Z / end-of-day** | the day in one sheet → the ~6 numbers for Banana | cashier + Felix, **daily** | ✅ built (R2R hand-off) |
| **2** | **Velocity & reorder** ⭐ | *what's selling fast → what to re-buy.* Units/day per item; flag the movers. **This is zero-inventory's other half** — the report that justifies sell-to-seed. | Felix, **weekly** | ✅ from the sales log (need a date-range query + a velocity calc) |
| **3** | **Dead stock / slow movers** | the inverse: items with **no/low sales in N days** → clear, discount, or discontinue. (No stock count — "dead" = "hasn't sold".) | Felix, **monthly** | ✅ products + last-sold |
| **4** | **Bestsellers (ranged)** | top sellers over a week/month, by units **and** by revenue (different lists!) | Felix, **weekly** | ✅ (today's top-3 → ranged) |
| **5** | **Margin / profitability** | revenue − cost per product/category → *"am I pricing right / giving the store away?"* The answer to the price-guessing fear. | Felix, **monthly** | ✅ cost is captured (product + box-split) |
| **6** | **Sales by category / department** | head-shop vs **cafe** vs grow-supplies — where the money comes from (the 2027 multi-dept + the cafe VAT story) | Felix, **weekly** | 🟡 `by_department` exists (WS-1, local) — wire it through |
| **7** | **Cashier performance + hours** | sales per cashier **and hours worked** (clock-in/out = drawer open/close) → **sales per hour.** Doubles as the **timesheet.** | Felix, **weekly / payroll** | ✅ cash_shifts already hold user + opened_at/closed_at — *nearly free* |
| **8** | **Cash variance trend** | per cashier over time: expected vs counted. Who's consistently over/short → training or a problem. | Felix, **weekly** | ✅ cash_shifts store variance per close |
| **9** | **Member / loyalty value** | top members by spend, credits/points outstanding, member-vs-walk-in split, lapsed regulars. The **CRACK community**, quantified. | Felix, **monthly** | 🟡 customer + credits exist; wire the sale→member link |
| **10** | **VAT report (8.1 / 2.6 split)** | VAT collected per rate (dine-in vs takeaway) for the **Treuhänder** — compliance-grade. The Swiss moat no US POS does. | accountant, **monthly/quarterly** | 🟡 VAT captured; the dine-in/takeaway split is the cafe-phase build |

### Bonus round
- **Discount & giveaway leakage** — discounts given (by whom) + free treats (COGS). Generosity vs leakage. ✅ we capture giveaway count/cost + discount.
- **Sales heatmap (hour × weekday)** — when are we busy → **staffing.** Busiest-hour, scaled to a week. ✅ from completed_at timestamps.

---

## What I'd build first (the order)
1. **#2 Velocity & reorder** — the flagship; it's the report that *proves the whole zero-inventory
   thesis* and gives Felix something no spreadsheet does. ✅ data's there.
2. **#7 Cashier performance + hours** — nearly free (the cash-shift clock already records it) and
   it quietly delivers the **HR/timesheet** thread too. High value, low cost.
3. **#5 Margin** — answers the price-guessing fear directly; cost is already captured.

Then #3 (dead stock), #4 (ranged bestsellers), #6 (by-department), #8 (variance), #9 (members),
#10 (VAT split — rides the cafe phase).

**The shape:** one **Reports hub** with a **date-range picker**; each report is a tab/card that
re-queries the sales log for that window. The daily engine we just built generalises to "any
window" — so #1–#5 share most of the code. Build the hub + velocity first; the rest snap in.

---

## War-room notes (Tigs, 2026-06-22)

**Three reports to add to the Top 10:**
- **Catalogue health / enrichment gaps** — count of born-once items still missing a photo /
  a real category (still "On the fly") / a cost. This *runs the sell-to-seed → enrich loop*,
  and unlike velocity it's useful from **week 1**. ✅ all on the product row.
- **Refunds & voids** — refund rate + voids per cashier (shrinkage / anomaly signal). The
  bonus round covers discount/giveaway leakage but not this. ✅ refunds live in transactions.
- **Per-supplier shopping list** — velocity grouped **by supplier** = a draft reorder list
  ("the PO without building P2P"; the receiving-spec appendix called for exactly this). It's
  the *actionable output* of #2, not just a chart. ✅ `supplier_name` is on the product.

**Velocity & data-time — the nuance (and Angel's catch):**
- On a **fresh** sell-to-seed shop, velocity is empty for ~3–4 weeks (no history) — so don't
  put an empty velocity chart in front of Felix on Day One.
- BUT **staging/prod already hold weeks of real test sales** — so **velocity is runnable on
  the EXISTING data TODAY.** The "needs time" caveat is only for a brand-new shop.
- → **Build velocity (#2) first, now, against the existing sales log** — real numbers
  immediately. For the **sandbox** (empty by design), a small **backdated-sales seed** makes
  it demo-able without waiting.

**Sequence:** reports stay v2 / post-cutover for *Felix's* shop, but as a *capability* #2 can
be proven against today's data right away — it doubles as proof the thesis works on real
numbers.

### Proven — ran it on local data (2026-06-22, read-only)
6 months / **1,466 completed sales** locally. Velocity is **~10 lines of SQL on the sales log**:

```sql
SELECT p.name,
       SUM(li.quantity) AS units,
       SUM(li.quantity) FILTER (WHERE t.completed_at >= now() - interval '30 days') AS units_30d,
       ROUND(SUM(li.line_total), 2) AS revenue,
       MAX(t.completed_at)::date AS last_sold
FROM line_items li
JOIN transactions t ON t.id = li.transaction_id AND t.status = 'COMPLETED'
JOIN products p ON p.id = li.product_id
GROUP BY p.id, p.name
ORDER BY units DESC;            -- swap to ORDER BY revenue DESC for the by-money list
```

Real top movers it returned: **CBD Oil 20%** (181 units, CHF 16,255) · 4-Piece Grinder (165) ·
**Grinder Card** (160 units, only CHF 102) · … · **Puffco Peak Pro** (11 units, CHF 4,939).
That contrast **proves report #4** (by-units ≠ by-revenue — a CHF-102 card outsells a CHF-4,939
rig 15:1 by units). It also flagged the **Lollipop** (35 units, CHF 0 = giveaways).

**Endpoint:** `GET /reports/velocity?from=&to=&sort=units|revenue` — this query parameterised on
the window, behind `require_any_pos_role`. **Build ≈ an afternoon.**

**Note:** dead-stock (#3) returned **0** rows here only because this test data is uniformly
recent — it needs spread-out history (or a backdated seed) to populate. A real shop over time
fills it on its own.

