# Banco — Phase 2 Roadmap: "The System Felix Moves Onto"

*Created 2026-06-21. Folds three research artifacts into one build plan:*
- *Market reality → `docs/BANCO-MARKET-BRIEF-2026-06-21.md`*
- *Customer reality → memory `banco-felix-shop-move.md`*
- *Cafe VAT spec → `docs/BANCO-CAFE-VAT-SPEC-2026-06-21.md`*

---

> **⏸️ CAFÉ PARKED 2026-06-21.** Angel's call: the café is a genuinely new business
> (food, second staff, licensing) tied to a *March 2027, still-unconfirmed* move, while the
> real near-term dollar (Felix live on prod with today's head shop) is unshipped. Discussed,
> not building. WS-1 increment 1 (the dormant `department` column) stays as cheap reversible
> insurance; WS-2→5 (cafe VAT engine, Z-report screen, catalog, cutover) are **on hold until
> the move firms up**. Don't build the café till before the café exists.

## THE FRAME

Phase 2 is **not** "add multi-location." It's **"make Banco the system Felix moves his whole business onto in March 2027."**

The market brief proved the strategy: Banco's TAM is thin and unsizable, legalization is a 2029-30 mirage, and the real moat is **Felix's SOPs + Swiss-correctness + stewardship.** The right play for a thin-TAM, deep-moat product is **go deeper on the one real customer, not wider on a market that isn't there.** Felix's forced move is the perfect vehicle: it turns one account into three revenue surfaces and hands us a hard deadline to build against.

**The North-Star milestone is not "deploy to prod." It's: Felix opens the new shop in March 2027 running entirely on Banco, and never looks back.**

---

## THE CUSTOMER REALITY (what we're building for)

Felix must vacate his current ~2.5m-wide shop (building renovated from **March 2027**). Best option (likely, not yet confirmed): move into the larger space next door (~15m wide) — physically a different building. That space becomes **three businesses under one roof:**

1. **Head shop** (front — the core)
2. **Cafe** (NEW: coffee, muffins, ~25 seats; needs a toilet built)
3. **Grow-supplies** (raised back room — fertilizers, lights; the computer/POS already lives there)

Operational facts that drive the build:
- **~2 staff** (Pam can't run 25 covers + coffee + head shop alone).
- **Likely 2 tills** (head shop + cafe), **same legal entity**, separate Z-reports. Department/cost-center split, NOT a separate company.
- The cafe is the **community anchor** — "the coffee is the close." It's the physical home of the CRACK member-card loyalty (see `banco-crm-strategy`).

---

## PHASE 2 WORKSTREAMS

### WS-1 — Multi-department model (one shop, many counters)
**Increment 1 BUILT + tested LOCAL 2026-06-21, parked on branch `feat/banco-multidept`**
(café on hold; NOT on main/staging/prod — kept off the prod train deliberately). `Department` enum
(head_shop | cafe | grow_supplies) in `src/core/constants.py`; `department` column on
`products` + `transactions` (default head_shop, additive migration in `database.py`);
`TransactionCreate` accepts it (default head_shop, bad value → 422); `daily-summary` returns
a `by_department` split that sums to total_sales. Test: `tests/pos/test_pos_departments.py`
(4/4 green vs local). Verified: full POS suite shows no regression (failures are a
pre-existing `find_product(limit=100)` flake on the 7.4k-product catalog — main fails the
same/more). NEXT increment: per-department Z-report screen + tag products to cafe.

The data model needs a first-class **department / cost-center** concept inside a single shop (realm):
- Departments: `HEAD_SHOP`, `CAFE`, `GROW_SUPPLIES` (extensible).
- Each till/session is tagged to a department → drives **separate Z-reports per department** while rolling up to one shop's books.
- Products carry a department + a VAT category (see WS-2).
- Reuses, does NOT duplicate, the per-cashier cash-shift drawer work already shipped (two staff → two drawers, already proven).

**Why now:** this is the structural change the move forces. Everything else hangs off it.

### WS-2 — Cafe VAT engine (dine-in vs takeaway) — *legally mandatory*
Per `BANCO-CAFE-VAT-SPEC`. **Felix's 25 seats exceed the FTA's 20-seat flat-rate cap, so per-line splitting is the law, not a feature.**
- Per-line **`consumption` flag** (`DINE_IN` | `TAKEAWAY`), **default `DINE_IN`** (undocumented = FTA presumes standard rate).
- **Category → rate resolver:**
  - `ALCOHOL` → 8.1% always · `TOBACCO` → 8.1% always (head-shop relevance!)
  - `FOOD` / `NONALC_DRINK` → 8.1% dine-in, 2.6% takeaway
  - `RETAIL_GOODS` (head shop + grow) → 8.1%
- Rates stay **configurable data** (8.5% standard is proposed/future).
- **Receipt** prints per-line article/group + price + **VAT rate** (coded with a legend, e.g. `A=8.1% B=2.6%`).
- **Z-report** separates **dine-in vs takeaway turnover** streams. (Do NOT build separate COGS accounts — that obligation was refuted; only turnover must split.)

### WS-3 — QR-bill multi-rate invoicing
- Emit Swico S1 billing-info tag `/32/` as `rate:net` pairs (`8.1:x;2.6:y`).
- Enforce the **reconciliation check**: Σ(net) + Σ(computed VAT) == QR total. Reject otherwise.

### WS-4 — Cafe catalog + the community bridge
- Cafe product catalog (drinks/food) with VAT categories pre-tagged.
- Member card works across **both** counters (one membership, head shop + cafe) → this is where loyalty actually lives. Hook into the CRM Phase-0 wire-up (customer-attached-to-sale).

### WS-5 — Genesis cutover kit (the March 2027 move)
The move = max pain = where Banco earns its keep:
- Genesis inventory recount tool (new building, new layout, new lines).
- New-shop setup wizard run (departments, tills, staff, VAT categories).
- Dress-rehearsal on staging with Felix before the physical move.

---

## SEQUENCING

| Order | Workstream | Rationale | Gate |
|-------|-----------|-----------|------|
| 1 | **WS-1 multi-department** | Structural; everything hangs off it | Staging green + Angel PASS |
| 2 | **WS-2 cafe VAT** | Legally mandatory; the moat demo | Treuhänder sign-off on method (see below) |
| 3 | **WS-3 QR-bill multi-rate** | Follows VAT engine | Reconciliation test passes |
| 4 | **WS-4 cafe catalog + member card** | Needs WS-1 + WS-2 | CRM Phase-0 wired |
| 5 | **WS-5 cutover kit** | Last; needs all above stable | Dress rehearsal w/ Felix |

**Deadline math:** March 2027 cutover. Work backward — WS-1/2/3 should be staging-stable and Angel-PASSED well before then so WS-4/5 and a real dress rehearsal have runway. This is a *months*, not *weeks*, programme — but it is the highest-value Banco work on the board because it's load-bearing for the one paying customer.

---

## DEPENDENCIES & HUMAN SIGN-OFFS (don't hardcode)

A **Swiss Treuhänder** must decide before WS-2 ships to prod:
1. **Accounting method** — effective (two-rate till) vs Saldosteuersatz (eligible ≤CHF 5.024m turnover & ≤CHF 108k VAT/yr); and which net-tax rate(s) for a combined head-shop + cafe (may need a two-activity split).
2. **Re-ring workflow** — when a takeaway line (2.6%) becomes dine-in (customer sits). Spec recommends: confirm dine-in/takeaway *before* finalizing each line.
3. **Audit substantiation** — any signage/packaging the FTA wants beyond receipt + till programming.

Confirmation still pending from Felix: that he actually takes the next-door space, that he commits to the cafe line, and the final seat count (the 20-vs-25 line matters — at ≤20 the flat-rate shortcut reopens).

---

## HOW THIS CONNECTS TO PRICING (from the market brief)

The cafe makes the **stewardship sell** concrete. Banco isn't "a till" — it's "the Swiss-correct system that runs your head shop + cafe + grow room through one membership, files your VAT right, and that we install and hold through your move." That justifies the top of the defensible band: **CHF 99–149/mo bundled.** Validate against what Felix pays today.

---

## THE ONE-LINE STRATEGY

**Don't chase the TAM that isn't there. Make the one shop you have impossible to leave — by being the only system that's correct for a Swiss head-shop-plus-cafe through the hardest moment of its life (the move).** Win Felix completely, capture it as the reference install, *then* decide whether the pattern travels.

*(Does the pattern travel to the EU? Researched — verdict: **NO, not as a VAT edge.** Germany flattened its eat-in/takeaway food differential to 7% from Jan 2026, Italy's was always small, and EU POS incumbents already do VAT-splitting (table-stakes, not a moat). The real EU barrier is per-country e-invoicing/fiscal-till localization (DE TSE, FR NF525, IT SdI, ES Veri*Factu, AT RKSV) = N localization projects. Switzerland is the genuine gap (non-EU). See `docs/BANCO-EU-VAT-EDGE-BRIEF-2026-06-21.md`. Bottom line: win CH completely; treat EU expansion as funded, country-by-country localization, never "one EU product.")*
