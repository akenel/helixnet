# Banco — Felix Day-One Wishlist (predicted asks + quick specs)

*2026-06-27. "If I were Felix, what would I want on day one?" A predict-ahead list of features Felix and Pam will likely ask for once the shop is live — sorted by value vs. risk. Most of Bucket 1 is **read-only windows onto data we already capture** (transactions already store `customer_id` + line items; the customer record already holds `lifetime_spend`, tier, credits). That makes them low-risk: new GET endpoints + templates, no new money-handling.*

*Pairs with: [BANCO-GO-LIVE-READINESS.md](BANCO-GO-LIVE-READINESS.md) · [BANCO-INVENTORY-ROADMAP.md](BANCO-INVENTORY-ROADMAP.md) · [BANCO-CLOSEOUT-TIMESHEET-AND-GOLIVE.md](BANCO-CLOSEOUT-TIMESHEET-AND-GOLIVE.md)*

---

## THE ONE-LINE VERDICT

**The reporting Felix will ask for first is almost all *drill-down*, and the data is already in the tables — we just never built the window.** Build Bucket 1 (read-only product + customer drill-downs + a richer dashboard) in the sandbox now; it's cosmetic-grade risk. Write returns/refunds (#4) as its own spec and do **not** rush it — it touches money, VAT, and the Z-report.

---

## WHAT ALREADY EXISTS (so we don't rebuild it)

Verified in the codebase before writing this:
- **Daily summary** (`/api/v1/pos/reports/daily-summary`) — totals, VAT split 8.1/2.6, payment breakdown, per-cashier totals, top-3 sellers, avg basket, items sold, busiest hour. `?mine=true` scopes to one cashier.
- **Transaction history** (`/api/v1/pos/transactions`) — date range, status, payment-method, **cashier filter**, **customer filter**, reprint, click → receipt detail.
- **Shift detail** (`/api/v1/pos/shift/{id}/transactions`) — itemized per-shift log with line items.
- **Customer model** — handle/real_name, QR, loyalty tier + discount %, `lifetime_spend`, credits balances, CRACK level. QR scan at till works.
- **Closeout / Z-report** — printable, Banana CSV export, cash count + variance.
- **Dashboard / Shop Pulse** — today's sales, txns, VAT, members, catalog count, open drawers.

**The gap is not data capture. It's that the drill-downs dead-end** — you see a Customer column but can't click it; you see top-3 sellers but not the full product list or "who bought it."

---

## BUCKET 1 — QUICK WINS (read-only, low risk, build now)

### 1. Product Sales report  ⭐ highest-asked
**Felix's question:** *"What actually sold today / this week — and who bought it?"*
Today he gets only top-3 by quantity. No full list, no date range, no per-item drill.

- **New endpoint:** `GET /api/v1/pos/reports/product-sales?date_from=&date_to=`
  - Returns per product: `{product_id, name, category, qty_sold, revenue, vat_collected, txn_count}` sorted by revenue desc.
  - Aggregates `LineItemModel` joined to completed transactions in the window. Excludes giveaways from revenue (count separately).
- **New endpoint (drill):** `GET /api/v1/pos/reports/product-sales/{product_id}?date_from=&date_to=`
  - Returns the list of transactions that included this product: `{txn_number, time, cashier_name, customer_name, qty, line_total}`.
- **Screen:** `/pos/reports/products` — date-range picker (reuse the Today/7d/30d/month presets from transactions.html), sortable table (qty / revenue / name / category), click a row → drill panel listing the sales + who bought it. Category subtotals at top.
- **Risk:** Low. Read-only aggregate over existing rows. Manager-only (reuse the role guard already on multi-day reports).

### 1b. "Print / Export this view"  ⭐ (Felix idea, 2026-06-27)
**Felix's use case (his words):** filter the day to one customer → see he bought the same stuff five times, paid cash then TWINT then debit → *print that list* → "what's going on here?" This is **less a sales report than a know-your-customer / loss-prevention tool** — and the same buttons serve "print today's takings for the folder."

- The filters already exist on `/pos/transactions` (date, cashier, customer, payment). The gap is **export/print exactly what's currently on screen.**
- **Add to the filtered transactions screen, the product-sales drill (#1), and the customer detail (#2):** a **"Print this view"** button (reuse the `@media print` clean-chrome already built for receipts) and an **"Export CSV"** button (client-side, from the already-loaded rows → exports *exactly* what's shown).
- **Every export is self-describing:** a header stamp — shop name, the active filter ("Customer: Poppie · 2026-06-20 to 2026-06-27"), generated-at timestamp — and a filename like `banco-transactions-poppie-2026-06-27.csv`. On paper the story must read: each transaction's time + **payment method** + **items**, so "same items 5×, three payment types" is obvious at a glance.
- **Risk:** Low. Client-side print/CSV over data already fetched. No new endpoint required (server CSV optional later).

**Where exports live (the "Miro thing"):** do NOT build an in-app report archive for day one. The export *is* the archive — a self-describing PDF/CSV that Felix saves to his own Google Drive (`Banco reports / 2026-06 /`). His data, shareable by link, searchable, survives independent of Banco running, and adds zero bus-factor. An in-app "report history" list is real but **Bucket 3** — see below.

### 1c. Export formats — CSV now, PDF now, XLSX as the "full feature" (Felix idea, 2026-06-27)
Felix wants a proper export feature: "export to PDF, CSV, all that good stuff — XLS directly would be good." Honest take, because the three formats are NOT equal cost:

| Format | Effort | When it's the right choice | Build when |
|--------|--------|----------------------------|------------|
| **CSV** | Trivial, no deps, client-side | The lingua franca — opens directly in Excel / Numbers / Sheets. Re-import into Banana. | **Now** (every report) |
| **PDF** | Low — reuse existing `@media print` clean-chrome + browser "Save as PDF"; one-click branded PDF via the existing Puppeteer pipeline later | Human-readable, fixed layout. Print for the folder, hand across the counter, email to the Treuhänder. | **Now** (print button = PDF for free) |
| **XLSX** | Medium — needs a real library (**openpyxl**, the full industry-standard one, per rule #9) + a server endpoint + **container-image rebuild** (openpyxl isn't in the image today, same gotcha as Pillow) | Only beats CSV when you want *formatting*: a multi-sheet workbook (Summary · Transactions · Products), frozen header row, a bold totals row, number formatting. For a polished Treuhänder hand-off. | **Follow-up** (after CSV/PDF land) |

**Recommendation:** ship CSV + PDF on every report screen *now* — together they cover ~90% of "export this." Add **native XLSX via openpyxl** as the deliberate full-feature follow: a server endpoint `/reports/*.xlsx` that builds a formatted workbook, **plus a `requirements.txt` line + image rebuild** (flag this — don't claim XLSX works until the image actually carries openpyxl). Do *not* hand-roll a fake `.xls` (HTML-table-renamed) — that's the bundled-subset shortcut rule #9 warns against; Excel throws a security warning on it.

**Read mode:** the print-clean view *is* the read-only view — chrome stripped, just the data. A shareable read-only report *link* (no login, tokenised) is a Bucket-3 nice-to-have, not day one.

**Export security — VIEW and EXPORT are separable privileges (export is the higher bar):**
- **Viewing is ephemeral and supervised; exporting is exfiltration** — a portable copy that walks out the door (the departing-employee-emails-the-customer-list risk). So export can warrant a *tighter* gate than view. Felix's instinct, and it's right.
- **Client-side export inherits the view gate** (our product-sales CSV/Print re-serialize on-screen data → same manager gate as view). Fine for *sales* data, where leakage risk is low.
- **To make export tighter than view you need a server-side export endpoint** with its own (stricter) role check **+ an audit log** of who exported what, when. A client-side lock is soft — anyone who can see the JSON can copy it (screenshot/devtools). The audit log doubles as a trust/data-protection feature.
- Posture by data class:
  - **Sales / product reports** — cashier may even *view*; **manager** exports. ✅ built (manager-gated both).
  - **Customer list / PII** (`real_name`, lifetime spend) — view restricted; **export = owner/admin, server-side, logged.** Respects the model's handle/real-name split.
  - **HR / timesheet / payroll** — view self-scoped (Pam sees only her own); **export = owner/admin only, logged**; payroll stays dark. Tight gating here is *necessary*, not overkill.
- Rule of thumb: **the format is never the security boundary — the data's sensitivity is; and a copy that can leave the building is a higher privilege than a glance at the screen.**
- **BL (follow-up):** audited server-side export for PII/HR (own endpoint + owner/admin role + export-log table).

### 2. Customer detail view
**Felix's question:** *"Pull up Poppie — what does she buy, what's she worth?"*
The Customer column in transactions dead-ends; there's no customer detail screen.

- **New endpoint:** `GET /api/v1/pos/customers/{id}/summary`
  - Returns `{handle, real_name, tier, tier_discount_percent, lifetime_spend, credits_balance, crack_level, is_vip, first_seen, last_seen, visit_count, avg_basket, top_items:[{name, qty}]}`.
  - `top_items` = their most-bought products (line items joined on `customer_id`).
- **New endpoint:** reuse `GET /api/v1/pos/transactions?customer_id=` for the full purchase list (filter already exists — just need to accept an explicit id).
- **Screen:** `/pos/customers/{id}` — header card (name, tier badge, lifetime spend, credits), "usually buys" chips, purchase-history table (click → receipt). Link in from: transactions list Customer column, customer-lookup results.
- **Risk:** Low. Read-only. Respect the real_name/handle staff-visibility split already in the model.

### 3. Dashboard enrichment
**Felix's question:** *"Give me the pulse without opening a report."*

- Add cards to `/pos/dashboard` (manager view): **Week-to-date sales** (not just today), **Items sold today**, **Top customer today**, **Top product today**.
- Source: extend `/api/v1/pos/system/pulse` with `week.sales` + `today.top_customer` + `today.top_product`, or call daily-summary for a 7-day range.
- **Risk:** Cosmetic. ~20–30 min.

---

## BUCKET 2 — FUNCTIONAL GAPS (money-touching)

### 4. Returns / refunds  — ❌ NOT NEEDED (Felix confirmed 2026-06-27)
Originally flagged as a risky must-build. **Felix says returns essentially don't happen** and we should NOT build a refund module. Why, in his words:
- The product mix is **sub-CHF-50** — papers, lighters, trays, soil. Nobody returns a half-used pack of papers or a lighter they've handled.
- **Broken cheap item → exchange.** New lighter, toss the bad one, no paperwork. *Not a transaction event at all* — it never touches the till.
- **Zippo / special light → repair**, not return. "Leave it with me, pick it up tomorrow." A service, not a refund.
- **Rare serious case → just reverse the order.** That's a manager **void of one transaction**, not a VAT-refund flow with its own fiscal document.
- **So:** no `BANCO-RETURNS-SPEC.md`, no negative-turnover Z-report lines, no Treuhänder refund review.
- **And the rare "reverse the order" path already exists:** `POST /api/v1/pos/transactions/{id}/refund` — manager/admin only, full *or* partial, logs reason + who, and correctly adjusts day takings (full → drops the sale from totals; partial → keeps the net, so reversing CHF 5 of a CHF 50 sale doesn't erase all 50). **Build nothing for returns.** Felix's rare case is covered today.

### 5. Park / hold a sale
Customer steps away mid-ring; Pam serves the next; resumes later. Real cashier need.
- Persist the open cart (we have `OPEN` transaction status + cart in sessionStorage) → "Hold" button parks it, "Resume" reloads. Moderate effort, no money risk until checkout.

---

## BUCKET 3 — NICE-TO-HAVE (later)

- **Price-check mode** — scan to see price/stock without starting a sale (Pam at the shelf).
- **Category rollup** — revenue by category (falls out of #1's aggregate almost free).
- **Slow-mover / dead-stock alert** — "not sold in N days" (needs the product-sales aggregate from #1).
- **Loyalty/credits redemption UI** — the model tracks credits but nothing spends them yet. Pairs with [the community loop](business/BANCO-LAPIAZZA-COMMUNITY-LOOP.md).
- **Refund/void reason drill-down**, payment-method reconciliation vs. bank statement.

---

## FROM TEST-B02 (Product Sales report — Angel field notes, 2026-06-28, staging 11/11 PASS)

- **BL — Category subtotals as a chart + print.** The "By category" pills are correct but flat. Add a small **bar or pie chart** of revenue-by-category on the Product Sales report, and a **print/PDF button for that chart/section** too (not just the table). *(Angel note on check #3: "could have a simple bar chart or pie chart display and print report too button.")* Lightweight — the category aggregate already ships in the endpoint; a tiny inline SVG/canvas chart, no heavy lib.
- **BL — Buyer row → full transaction invoice.** In the "👥 Who bought it" panel, make each buyer row a **hyperlink to the actual full transaction/receipt** (the complete invoice for that sale), not just the line summary. *(Angel note on check #5: "a hyperlink from the txn to display the actual full transaction invoice would be nice.")* The receipt/transaction view already exists (`/pos/transactions` + receipt render) — wire `transaction_number` → that view. Read-only, manager-gated.

## LOGGED BL ITEMS (don't forget — Felix will want these)

- **BL — XLSX export (native Excel).** openpyxl (full lib, rule #9) + server endpoint `/reports/*.xlsx` building a formatted multi-sheet workbook (Summary · Transactions · Products, frozen header, bold totals) + **requirements.txt line + container-image rebuild**. Don't claim it works until openpyxl is actually in the image (Pillow gotcha). Build after CSV/PDF land. *(Felix asked 2026-06-27.)*
- **BL — "Export to Google Drive" (a sellable feature).** One-click push of a report PDF/CSV/XLSX straight into the shop's own Google Drive folder (`Banco reports / YYYY-MM /`). Turns the export into a self-filing archive *and* is a feature we can offer other shops. The Drive connection is the durable answer to "where do reports live" — his data, his Drive, shareable, zero bus-factor on us. Needs Google OAuth + Drive API scope per shop. *(Angel idea 2026-06-27 — "brilliant, we could offer that export feature.")*
- **BL — Audited server-side export for PII/HR.** Own endpoint + owner/admin role + an export-log table (who exported what, when). Lets export be tighter than view, and doubles as a data-protection trust feature. *(See Export security above.)*

## BUILD ORDER (recommended)

1. **#3 dashboard cards** (warm-up, 20 min, instant "wow" for Felix).
2. **#1 product-sales report + drill** (the big one — answers his most-likely first question).
3. **#2 customer detail view** (closes the dead-end click).
4. Stop. Write **#4 returns** as its own spec; don't build it in the same sprint.

All of 1–3 are read-only, manager-gated, sandbox-first, and reversible. Verify each headless (getComputedStyle / endpoint returns) before claiming done — per the styling-gotchas and the "never say fixed without verifying" rule.

---

*"The data's already in the table — we just never built the window."*
*"Build the read-only drill-downs fast; treat anything that touches money like a seal — inspect all of it first."*
