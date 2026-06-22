# BANCO — Master Roadmap (the whole cathedral)

*One page for the entire vision. Detail lives in the linked docs; this is the map.*
*Captured 2026-06-22. "Bake it all in and bank it." — Angel*

---

## 0. What Banco IS
A Swiss-native **vertical ERP for head-shops**, built on the HelixNet engine. The core is
**Order-to-Cash (the till)** done flawlessly; everything else either feeds it or hangs off it.

- **Customer #1:** Felix / **Artemis Lucerne** — 25-year flagship, the reference customer.
- **But it's not just for Felix — it's for the world, and free to use.** Shops can train
  themselves; the system *is* the SOP. Angel sells the **setup + stewardship**, not a licence cage.
- **Methodology (the moat):** **zero perpetual inventory** (a sale is never blocked by a count),
  **sell-to-seed** (the catalogue accretes from real sales), **the NAME is the key** (not the
  barcode — humans navigate by name + picture), and **velocity drives reorder** (not stock counts).

## 1. The product — modules
| Module | What | Status |
|---|---|---|
| **O2C — the till** | sell, discount, payment, receipt, cash drawer, close-out | ✅ **SHIPPED to prod** |
| **Cash & shifts** | open float → sell → close balanced; **the drawer = the time clock** (open=clock-in, close=clock-out — already captured in cash_shifts) | ✅ shipped |
| **Catalogue** | on-the-fly create ("inventing products"), photos + gallery, search, cost | ✅ shipped |
| **Settings / control centre** | tabbed: identity · address · contact & links · hours · tax · receipt & graphics · discounts (+ Labels, Staff to come) | ✅ shipped (growing) |
| **Members / the CRACKs** | loyalty + credits + community; *"any customer could be George Plenty or Bruce Lee walking in"* — everyone's somebody, VIPs recognised | 🟡 model exists, wire deeper → [[lp-cleopatra-reception-model]] |
| **Catalogue enrichment** | pull canonical data from sources instead of guessing prices | 🔨 backlog → `BANCO-ENRICHMENT-BACKLOG.md` |
| **Staff / HR / users** | onboard employee (name+role+photo, AHV later), payslips-or-feed-Banana, Keycloak login provisioning so Felix never opens the KC console | 🟡 models + KC service exist → `BANCO-STAFF-ADMIN-ROADMAP.md` |
| **Labels** | template library (size/layout/EAN vs QR/description space), per-article label type, N-up print — **labels are small postcards** (reuse the GOLD-template engine) | 🔨 backlog §6, ⟶ Felix's label stock |
| **Reporting** | velocity (reorder signal) + the **Top-10 reports** (TBD — §4) | 🟡 some exist, need many more |
| **Multi-department / Cafe** | Felix's 2027 move: head-shop + **cafe** (25 seats) + grow-supplies; the Swiss **dine-in 8.1% / takeaway 2.6% VAT split** moat no US POS can do | 🟡 increment 1 local → `BANCO-PHASE2-ROADMAP.md` |
| **Training** | in-app cashier wizard/coach-marks ("start here, scan, search needs 2 letters, no code→create+photo, never block the sale") + SOP/KB + demo videos | 🔨 net-new |

## 2. The AI layer (BYO brain)
- **Picture → identify → search → enrich.** Cashier snaps a photo → **vision LLM** reads the
  packaging (name/brand) → searches the source (Artemis/Tamar) → best-guess match → pull price +
  picture + description (translated DE→EN). 3 misses → "add as brand-new product."
- **Autonomous overnight enrichment.** The LLM runs a nightly job over thin/on-the-fly items —
  decipher photos, decide what they are, search, and **enrich the data on its own** so the
  catalogue self-improves while the shop sleeps.
- One place an LLM call happens (`src/llm/`); the model is data; default Turbo else local Ollama.

## 3. Data sources & integrations (don't reinvent — feed)
- **Mozy (the 420 wholesale guy):** product library of **~7,000 articles** across suppliers —
  the basis of the catalogue seed (P2P side; Felix purchases as he always has).
- **Artemis / Tamar website:** by-URL pull proven; by-name search = R&D (JS/AJAX) → enrichment source.
- **Banana (accounting / R2R):** Banco hands the daily Z-report = ~6 numbers. Never rebuilt.
- **HR / payroll:** feed hours (from the shift clock) to his existing process; reinvent only if asked.

## 4. Reporting — the Top-10 (TBD, to brainstorm)
Velocity is the headline (what's selling → what to reorder, zero-inventory's other half). Then
~10 reports Felix actually runs daily/weekly/monthly. **⟶ next working session: list the 10.**
(candidates: daily Z, velocity/reorder, by-department, by-cashier, cash variance trend, top
sellers, dead stock, member value, VAT split, margin.)

## 5. The business model / go-to-market (the real product is the *service*)
**Not a SaaS cage — a setup-and-stewardship package, per customer, on their own box.**
- Each customer gets **their own server**: their own **sandbox → staging → prod**, a cleaned
  clone of the repo (their own dev kit). Angel does all the wiring, apps, credentials.
- **The package deal:** "We set it up remotely on your server, hand you the credentials, you own
  it. Hands-off, or hands-on for a week or two — your call. I steward the first 3 weeks; week 4
  we go live, after all the testing, when everyone knows how to use it."
- **Self-training** via the in-app wizard + teaching material + demo videos. Angel does the
  high-touch first; the material scales it.
- Market reality (verified): niche, not venture TAM; price band CHF ~80–150/mo; **the moat is the
  domain fit + Angel's stewardship**, not the code → `BANCO-MARKET-BRIEF-2026-06-21.md`.

## 6. The cutover (how Felix actually goes live) → `BANCO-CUTOVER-PLAN.md`
Scope (O2C owns the till, feeds Banana) · data migration (Mozy catalogue) · short parallel run ·
training · go-live checklist · ⟶ NEED-FROM-FELIX (current POS, real VAT no., label printer, logo✅).

## 7. Status snapshot
- ✅ **Live on prod** (`banco.lapiazza.app`): the till, cash drawer + gate, on-the-fly seed-to-sell,
  search fix, photos + gallery, discount caps, real Artemis identity + Settings control centre.
- 🟢 **Regression net:** `scripts/edge-sweep.js` (34/34), per-feature test sheets, the Day-One run.
- 🔨 **Next bricks (pick one):** demo polish (Top-10) → Felix's details → cutover; OR a roadmap
  project (enrichment / staff+users / reporting / labels / cafe).

---

### The detail docs (this map points at them)
`BANCO-CUTOVER-PLAN.md` · `BANCO-DEMO-POLISH-TOP10.md` · `BANCO-STAFF-ADMIN-ROADMAP.md` ·
`BANCO-ENRICHMENT-BACKLOG.md` · `BANCO-PHASE2-ROADMAP.md` · `BANCO-MARKET-BRIEF-2026-06-21.md`

> **The discipline that makes the cathedral buildable:** dream the whole thing (this page), then
> lay **one tested brick at a time**, and never let the unbuilt rooms block the working front door.
