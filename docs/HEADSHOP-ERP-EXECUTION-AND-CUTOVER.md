<!-- Companion to HEADSHOP-ERP-GRAND-PLAN.md. That doc is the VISION; this is the HOW:
the build order and the cutover playbook. Felix-first, YAGNI, reuse-don't-reinvent. 2026-06-20. -->

# Head Shop ERP — Execution & Cutover Plan

*Companion to [HEADSHOP-ERP-GRAND-PLAN.md](HEADSHOP-ERP-GRAND-PLAN.md). The grand plan is the vision;
this is the how — the build order and the migration playbook. Felix is the first and only customer
until he is the live reference. Nothing here is destructive; the Tamar webshop stays untouched and the
old paper method stays available as a fallback at every step.*

---

## 1. Where Felix is today (current state — the thing we're migrating FROM)

| Area | Today | Pain |
|---|---|---|
| **Daily sales** | Paper + pen → spreadsheet; manually types Cash/TWINT/Visa/Debit totals into the books | Re-typing, error-prone |
| **Product catalog** | ~10k items on the **Tamar Trade** webshop (artemisluzern.ch); JS-rendered, no export feed, no back-end integration | Catalog isn't usable as data anywhere else |
| **Inventory** | ~100–200k CHF of physical stock, **none of it logged**; scattered across shop, Leadtower (lab/grow), Seedle, boxes downstairs | "How much do you have?" → "no idea" |
| **HR / payroll** | A spreadsheet | The real ongoing pain |
| **Locations** | Head shop (moves March), Leadtower lab/grow, Seedle office + vending | Multi-site, nothing tracks where stock is |
| **Vending** | 2+ machines, ~1,000 CHF/machine/month, restocked by Felix by hand | Growing, no par/restock data |

## 2. Execution plan (build order — Felix-first, brick by brick)

### Phase 1 — a working till by Monday  *(nearly done)*
- ✅ **Stock deduction on checkout** — inventory decrements on every sale (committed).
- ✅ **Banana CSV export** — `/reports/daily-summary.csv`, one line per payment method (committed).
- ✅ **Printable daily Z-report** — clean print sheet on the closeout screen; Felix prints it, copies the
  ~5 totals into his book (committed). *This is what input #1 actually needed — not a chart of accounts.*
- ☐ **Create-product-on-the-fly** — wire the catalog form in `scan.html` for loose grow-shop items with no
  barcode (topsoil, a single grinder). Self-contained, next brick.
- ☐ **Unified feedback button** — port the La Piazza feedback widget (attachments + diagnostic snapshot)
  into helixnet as the *standard*, plus a 🎤 mic (Web Speech → text; later Whisper on a voice note). Its own
  focused build; it becomes the standard across POS + La Piazza and retires Bottega's.

> **YAGNI for Phase 1:** no multi-tenant, no BOM/production, no vending dashboard, no QR-bill, no Bexio API,
> no loyalty. One shop, one realm, one till.

### Phases 2–4
Per the grand plan: **P2** = genesis count at the March move + multi-location inventory + cycle-count
discipline. **P3** = light production/BOM + white-label/labeling + vending. **P4** = multi-tenant + the
steward crew. Each phase has an explicit YAGNI line in the grand plan — honour it.

**Reuse already confirmed in the repo (don't rebuild):** HR/payroll bones (`employee_model`,
`payroll_run_model`, `payslip_model`, `time_entry_model`, `hr_router`), suppliers/POs/inventory
(`supplier_model`, `purchase_order_model`, `inventory_model`), the recipe engine as a BOM
(`recipes.py`/`runner.py`), the print pipeline (`sop-to-pdf.js`, `postcard-to-pdf.js`), Keycloak
multi-realm, the backlog/feedback tooling.

---

## 3. The cutover plan (the centerpiece)

**Principle: ride the March move, never fight it.** Felix has to pick up every box to move the shop anyway —
so the move *is* the genesis inventory count. We turn his biggest headache into the system's foundation.

**Safety rails (true at every step):**
- The **Tamar webshop stays live and untouched** — it is not part of the cutover. The POS is the in-store
  till; web↔store inventory sync is a *future* feature, not a day-one dependency.
- The **old paper/spreadsheet method stays available** as a fallback until Felix says otherwise.
- Nothing destructive: we *add* a system alongside the current one and switch when it's proven.

### Step 1 — Master data: get the product catalog in *(do NOW, before March)*
1. **Get a clean product export from the Tamar admin** (Felix's login) — SKU, barcode, category, price,
   current stock, supplier, and any THC%/lot data. **This is the highest-value de-risking move — get a
   *sample* now** so we learn the data shape months before we depend on it.
   - *Fallback if no admin export exists:* scrape artemisluzern.ch with **Puppeteer** (we already run it) —
     the public site is JS-rendered, so a plain fetch won't do; a headless browser will.
2. **Build a one-time importer** → load into `ProductModel`. Map categories (Headshop / CBD / Grow / Papers /
   Vape / Shisha / Lifestyle), normalise barcodes, prices, set `vending_compatible` + slot where known.
3. **Reconcile/clean** — dedupe, fix categories, flag items with no barcode (the create-on-the-fly cases).
4. **Add supplier links** — Mozey + 420 first (standard), the other 5–10 suppliers after.

### Step 2 — Genesis inventory count (at the March move)
- As each box/shelf is packed to move, **count it once, correctly**, against the imported catalog. Set the
  real stock level **per location** (shop, Leadtower lab/grow, Seedle). This is the clean baseline Felix has
  never had in 25 years — the thing that makes every later report true.
- Use the **mobile cycle-count flow** (Phase 2 build): Fairphone + barcode scan, below-threshold report.
- **Angel does the genesis count and trains Ralph/Felix on the discipline** — this is the stewardship layer,
  not a one-off. "The joy only survives while the stewardship holds."

### Step 3 — Parallel run
- Run the POS **alongside** the paper method for a few days around the move. Compare daily totals. No
  pressure, fallback intact. Fix what the parallel run surfaces (this is what the feedback button is for).

### Step 4 — Go live
- Switch the till over **on a quiet day**. Keep the old method as fallback for ~1 week. Felix prints the
  daily Z-report and copies it into his book exactly as he does today — same habit, cleaner numbers.

### Step 5 — Stewardship handover
- Capture the SOPs (open/close, count procedure, restock, grow/lab batch, labeling) as recipes/KB — **Angel
  proxies for Felix** for now, asks the real Felix only when genuinely stuck. Train Ralph as the on-site
  steward. The SOP library + the trained steward = the moat and the thing that scales to shop #2.

### Cutover timeline (anchored to the March move)
| When | Milestone |
|---|---|
| **Now → Jan** | Phase 1 till live for daily sales (Banana sheet + stock). Get the **sample Tamar export**. Build the importer. |
| **Jan → Mar** | Catalog imported + reconciled. Mobile cycle-count flow built. SOPs captured. |
| **March (the move)** | **Genesis count** as the shop is packed/moved. Stock baselined per location. |
| **Post-move** | Parallel run → go live → old method retired once trust holds. |

### Rollback
At any point, **stop using the POS and go back to paper.** The webshop never changed, the books were always
maintained the old way in parallel, and no data was destroyed. The cutover is reversible by design.

---

## 4. The three Felix-inputs (right-sized)
1. **Daily totals** — *solved.* He needs a printed 5-line sheet, not a chart of accounts. Done (the Z-report
   print view). The Banana CSV is a bonus for later if he wants it.
2. **Tamar product export** — get a **sample now** from the Tamar admin to de-risk the March cutover; full
   export when we build the importer. Puppeteer scrape is the fallback.
3. **SOPs** — **Angel plays Felix**; capture the procedures now, confirm with the real Felix only when stuck.

## 5. Cutover risk register
| Risk | Mitigation |
|---|---|
| Tamar export is messy / unavailable | Get a **sample now**; Puppeteer scrape as fallback; reconcile against the physical count |
| Genesis count inaccurate | Count *at the move* (every item handled once); cycle-count discipline + spot checks after |
| Staff don't adopt / count drifts | Stock auto-deducts on sale (built); SOPs + train Ralph as steward; feedback button for live issues |
| March move slips or is chaotic | The till (Phase 1) is already useful without the count; the count can run during *any* reorganisation, not only the move |
| Single-steward dependency | Capture SOPs as recipes + train Ralph now, so the discipline isn't only in Angel's head |
