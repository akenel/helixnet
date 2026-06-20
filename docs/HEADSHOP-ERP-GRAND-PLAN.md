<!-- Generated 2026-06-20 by the `headshop-erp-vision` workflow: 6 asset-mappers (repo) + 4 market-researchers (web) + 1 synthesis. Grounded in the actual codebase + a live market scan. This is the vision's home -- the grand plan lives as a DOCUMENT; the code grows in place in helixnet. -->

# Head Shop Software for the World — Unified Vision + Phased Plan

*Architect's synthesis. YAGNI-disciplined, Felix-first, reuse-don't-reinvent.*

## 1. POSITIONING

This is a **Swiss-native vertical ERP/MRP for head shops** — retail till + multi-location inventory + light grow/lab production + vending + white-label — that wins not on features (the US "big three" already have more) but on the three things none of them have: **(1) Felix's domain SOPs captured as procedure-as-code** (25 years of head-shop craft, encoded once and replayable by any new shop), **(2) human stewardship** (Angel does the genesis inventory count, trains the trainers, holds the cutover), and **(3) a founder with 40 years of exact-fit ERP/MRP + real inventory-and-production-control mastery** who can build the Banana/Bexio ledger leg, the BOM engine, and the multi-currency books *correctly the first time*. The US tools are built around two forces that don't exist here — Metrc track-and-trace and federal banking illegality — so their compliance core and payment cleverness are dead weight in Switzerland. The lane is wide open: a **boringly reliable, Swiss-correct (THC <1.0%, VAT 8.1/2.6/3.8, QR-bill, CHF+EUR), Banana/Bexio-connected** head-shop ERP whose moat is the captured brain and the steward who installs it. The joy only survives while the stewardship holds — so stewardship is a *product layer*, not a service afterthought.

## 2. ARCHITECTURE

**Cross-cutting foundations (already proven):**
- **Multi-tenant:** Keycloak v24.0.4, RS256, multi-realm proven (POS + Camper + Bottega + BorrowHood live). Tenant model = **one realm per shop** (current proven pattern) for Phase 1–3; **shop_id custom claim + row-scoping** only when we cross ~3 tenants (Phase 4). Do not build the shop_id-on-every-model framework before then.
- **Multi-currency:** CHF base, store both the transacted amount *and* the CHF-equivalent-at-sale-time (Swiss VAT must reconcile in CHF). EUR is the only real second currency Felix needs.
- **Multi-language:** Jinja i18n already in the codebase (DE/FR/IT/EN). Document-level (QR-bill/invoice in the canton's language) is the Swiss-specific gap to close — later.

**Module map — REUSE vs BUILD:**

| Module | REUSE (our_assets) | BUILD |
|---|---|---|
| **POS / till** | `pos_router.py`, `pos_schema.py`, transaction/line_item/shift_session models, 12 POS templates, Banana CSV export (shipped) | PDF receipt (TODO line 1152), dynamic dashboard stats, age-gate + per-txn quantity register-rule (logged for audit) |
| **Inventory + multi-location** | `inventory_model.py`, `stock_movement`, `reorder_request`, `store_settings_model` (multi-store, per-store VAT), `supplier_model` | Wire models to routers/API (currently stub), batch/lot + expiry as first-class tracked dimension, cycle-count mobile flow, per-location stock views |
| **Light production / BOM + white-label/labeling** | `recipes.py` + `runner.py` (a recipe **IS** a BOM + routing), `isotto_purchase_order_model`, `equipment_acquisition_model` (buy/lease/outsource logic), Puppeteer PDF pipeline (`postcard-to-pdf.js`, `sop-to-pdf.js`) | `source_policy` field per product (make / buy-finished / outsourced-OPO), Outsourced Purchase Order document, draft/editable BOM at run-time with variance capture, barcode-image lib + label-sheet templates (none yet) |
| **Vending** | `headshop_cafe_model`, store_settings as location, recipe-as-output for pull-sheets | planogram table `slot→{product,price,capacity,par,restock_count}`, picklist generator `(par−current)`, consume a Nayax-class reader's sales feed (buy the rail, don't build it), remote-price-change action |
| **Suppliers / POs** | `supplier_model`, `purchase_order_model`, `isotto_*` + `camper_*` PO patterns, `customs_clearance_model` | Generalize PO router from stubs, OPO leg, landed-cost capture |
| **Reporting** | Banana CSV export (shipped, the proven pattern), activity-trail/audit pattern (Backlog/QA), `sop-to-pdf.js` | **The real gap.** Generic CSV builder (filter/columns/stream), daily Z-report→one summary journal entry, per-VAT-rate + per-lot granularity, Bexio API connector (nobody has connected a CBD POS to Bexio/Banana) |
| **SOP / KB** | `sop-to-pdf.js` (ISO-9001 headers/footers/page-X-of-Y), Backlog/QA boards, recipe engine | SOP-as-recipe library (Felix's brain), staff-tablet voice guide (TTS via existing voiceover recipe), batch/QC checklist templates |
| **AI-assist** | `llm/client.py` (`run_llm`, model-as-data), `concierge.py` (Cleopatra), `dispatcher.py`, `reception.py`, RabbitMQ fair-share queue | "The Steward" master (shop-manager persona) for staff/member Q&A, product-description recipe, member-intake recipe |

## 3. CHERRY-PICK TABLE

| Idea (source) | Module | Verdict |
|---|---|---|
| Daily Z-report → **ONE summary journal entry** (Lightspeed Acct) | Reporting | **Must-have** — already half-shipped via Banana CSV |
| **Invert tax authority**: chart-of-accounts + VAT codes defined in ledger, pulled into POS as mapping | Reporting/POS | **Must-have** — POS must never hardcode a Swiss rate |
| **Swiss QR-bill** as an output type (IBAN, amount, CHF/EUR) | Reporting/POS | **Must-have** (Phase 2–3) — mandatory since Oct 2022, every non-Swiss tool skips it |
| Batch/lot + expiry as first-class field, COA/THC% on the lot (Cova-light/Unleashed) | Inventory | **Must-have** — Swiss <1.0% THC; the lot's lab number IS the compliance receipt |
| Age-gate + quantity cap as a **logged register-rule** (Lightspeed CBD) | POS | **Must-have** — table-stakes, cheap to build |
| CHF base + EUR transaction, CHF-equiv stored at sale | POS | **Must-have** |
| `source_policy` per product (make/buy/outsource-OPO) + OPO document (Katana/Cin7) | Production | **Must-have** (Phase 3) — it's the white-label workflow Felix/Angel actually run |
| Draft/editable BOM with variance capture (Cin7) | Production | **Must-have** (Phase 3) — real grow/lab runs vary |
| Multi-location **included, not paywalled** (Unleashed) | Inventory | **Must-have** — Felix is multi-site day one (shop, Leadtower lab, Seedle vending) |
| Cycle-count / paperless stocktake on phone (Erply/Unleashed) | Inventory | **Must-have** (Phase 2) — the genesis count and ongoing discipline |
| Planogram = small table + auto picklist `(par−current)` (VendSoft/Parlevel) | Vending | **Must-have** (Phase 3) — 16–18 slots = one dict, Bottega's exact shape |
| Buy the cashless rail (Nayax-class reader), consume its feed | Vending | **Must-have** (Phase 3) — no PCI burden |
| Self-service kiosk / scan-to-shop on customer's own phone (Cova) | POS/Vending | **Later** — reuse Bottega storefront flow, not a new app; vending kiosk = same spine |
| Live compliance/exception feed (wrong VAT, missing lot, expired stock) (BLAZE) | Reporting | **Later** — generalize to an audit feed once data is flowing |
| Pre-arrival retail-ready labels at intake (BLAZE) | Labeling | **Later** (Phase 3) — maps to ISOTTO/UFA print pipeline |
| Loyalty tied to purchase-history segmentation (Springbig/Alpine IQ) | POS/CRM | **Later** — build native on user records, no 3rd-party bolt-on |
| Remote price change as one-tap action | Vending | **Later** |
| Auto-disassembly of returned kits into components (Unleashed) | Production | **Later** |
| Odoo Community self-host as the inventory primitives | (build-vs-buy) | **Skip** — validates that our differentiator is the Cleo/SOP/steward layer, not re-implementing BOMs; but we don't adopt Odoo |
| **Metrc/BioTrack seed-to-sale** compliance engine | — | **Skip** — US-only, builds the wrong machine |
| PIN-debit/ACH/Pay-by-Bank payment gymnastics | — | **Skip** — EU has normal rails (TWINT/SEPA/Visa) |
| EDI, dynamic fleet routing, enterprise warehouse/route logic | — | **Skip** — single shop, single machine; enterprise overhead |
| Cheap-subscription + monetize-payments + paywall-support model | (pricing) | **Skip (inverse pick)** — flat CHF/mo, accounting connector *included*, never paywall support; that's the trust play vs Dutchie lock-in |

## 4. PHASED ROADMAP

### Phase 1 — Felix's working till by Monday *(underway)*
- **Felix need:** Ring up sales at Artemis and not re-type totals into Banana by hand.
- **Reuse:** Full POS router/schema/templates, shift sessions, stock-deduction-on-checkout (shipped), Banana CSV export (shipped — `/reports/daily-summary.csv`, one quoted line per payment method).
- **Build (thin):** PDF receipt, real dashboard numbers, age-gate register-rule (logged).
- **YAGNI — do NOT build:** multi-tenant framework, BOM/production, vending, Bexio API, QR-bill, loyalty, kiosk. One shop, one realm, one till.

### Phase 2 — The genesis count (March move) + multi-location inventory + cycle-count discipline
- **Felix need:** When the shop physically moves in March, count every item once, correctly, and never lose the thread again. This is the **genesis-inventory moment** and Angel's stewardship hook.
- **Reuse:** `inventory_model`, `stock_movement`, `reorder_request`, `store_settings` (each site = a location: shop, Leadtower lab/grow, Seedle office+vending), supplier model, the Backlog/QA activity-trail pattern for the count's audit log.
- **Build:** Wire inventory models to routers (un-stub), **batch/lot + expiry as a tracked dimension** (COA/THC% on the lot), **mobile cycle-count flow** (Fairphone + barcode scan, below-threshold replenishment report), per-location stock views. Multi-location is included from day one — never paywalled.
- **YAGNI — do NOT build:** production BOMs, OPO, vending planogram, multi-tenant, demand forecasting beyond static min/max. Counting and seeing stock per site is enough.

### Phase 3 — Production / white-label + vending
- **Felix need:** Leadtower lab/grow runs (lot in → finished product out), white-label/private-label via partners (Curaprox connections, ISOTTO-style outsourcing), and the Seedle vending machine restocked from real par data.
- **Reuse:** `recipes.py`/`runner.py` as the BOM+routing engine, `equipment_acquisition` buy/lease/outsource logic, `isotto_purchase_order` pattern, Puppeteer print pipeline for labels, `headshop_cafe_model` for vending products.
- **Build:** `source_policy` field (make/buy/outsource-OPO) + OPO document, draft/editable BOM with variance capture, barcode-image lib + label-sheet templates, planogram table + picklist generator, consume a Nayax-class reader's sales feed, **Swiss QR-bill output type**, daily-Z→summary-journal for Bexio, batch/QC SOP checklists.
- **YAGNI — do NOT build:** EDI, fleet routing, kiosk app, loyalty segmentation engine, live exception feed, multi-tenant. One shop's production + one machine.

### Phase 4 — Multi-tenant + the world
- **Felix need:** Felix becomes the reference install; the captured SOPs + steward playbook let a *second* and *third* head shop onboard.
- **Reuse:** Everything above + the realm-creation CLI (`lp_create_realm.py`), Keycloak multi-realm fabric, the SOP-as-recipe library (Felix's brain, now portable).
- **Build:** shop_id custom claim + row-scoping (or per-shop realm provisioning at scale), tenant onboarding flow, the steward playbook as a product (genesis-count kit + trainer-training SOPs), document-level multi-language QR-bills/invoices per canton, the generic reporting/CSV builder + first analytics dashboard (burndown/cycle-time pattern from Today board).
- **YAGNI — do NOT build:** marketplace, app-store, white-label-the-whole-platform, data warehouse — until ≥3 paying tenants prove the demand.

## 5. DIFFERENTIATORS + HONEST RISKS

**Differentiators:**
- **Captured SOPs as procedure-as-code** — Felix's 25 years replayable by any shop. No competitor ships this.
- **Stewardship as a product layer** — the genesis count + train-the-trainers is the install, and the retention.
- **Swiss-correct from the metal up** — THC <1.0%, VAT 8.1/2.6/3.8, QR-bill, CHF+EUR, Banana/Bexio. Nobody has connected a CBD POS to a Swiss ledger.
- **Boring reliability as a feature** — the entire US category bleeds on its busiest day (Dutchie 4/20). Bake load/uptime into the gate.
- **Founder exact-fit** — 40 years SAP/ERP/MRP means the books, BOMs, and multi-currency are built right once, not iterated into correctness.

**Honest risks:**
- **Stewardship dependency (the core tension):** "The joy only survives while the stewardship holds." If Angel is the only steward, the model doesn't scale past a handful of shops without the steward playbook becoming real, teachable product. This is a Phase-4 existential question, not a Phase-1 one — but name it now.
- **Scope creep:** This input set spans POS + MRP + vending + white-label + multi-tenant + reporting. The discipline is brick-by-brick; every phase has an explicit YAGNI line for exactly this reason. The "best reports in the world" claim is currently **overselling** — CSV export beyond Banana doesn't exist yet. Earn the claim, don't assert it.
- **Single-customer start:** Everything is shaped to Felix. That's correct (Felix-first), but it means design decisions that feel general may be Felix-specific. Resist building the multi-tenant framework until a second shop is real.
- **The Tamara / cutover dependency:** Phase 2's genesis count and the existing ~10k-item catalog live in Tamara (current system). The whole migration hinges on getting a clean product export out of it and reconciling against the physical count during the March move. If that export is messy or Tamara fights us, the cutover slips. **De-risk early:** get a sample Tamara export *now*, before March.

## 6. THE FELIX-INPUTS WE STILL NEED

1. **Banana chart of accounts** — the real account codes + VAT-rate mappings (8.1% / 2.6% / 3.8% / 0%-exempt). The Banana CSV export already has placeholders (`pos_router.py` line ~1299: "we pre-fill his real codes once he hands them over"). Without this, the import dialog stays manual. **Highest-leverage single input.**
2. **A Tamara product export of the ~10k items** — SKU, barcode, category, price, current stock, supplier, and (critically) any THC%/lot data. This is the seed for the genesis count and the migration. **Get a sample now to de-risk the March cutover.**
3. **SOP interviews to capture Felix's brain** — recorded (Whisper-transcribed) walk-throughs of: opening/closing checklist, inventory count procedure, member-discount logic, grow/lab batch process, vending restock, compliance/age-gate handling. Each becomes a recipe. This is the moat; it's also the most perishable asset — capture it while Felix is available and motivated.

**Secondary (Phase 2+):** confirm the EUR use-cases (where does EUR actually change hands?), the Seedle vending machine's reader model (does it emit per-slot sales / DEX?), and whether Bexio (not just Banana) is in Felix's future — the connector target shifts the Phase-3/4 build.

---

Key grounded files: `/home/angel/repos/helixnet/src/routes/pos_router.py` (POS + shipped Banana CSV at `/reports/daily-summary.csv`, receipt TODO ~line 1152), `/home/angel/repos/helixnet/src/db/models/inventory_model.py` + `store_settings_model.py` (multi-location, models complete / routers stub), `/home/angel/repos/helixnet/src/compute/recipes.py` + `runner.py` (recipe = BOM+routing engine), `/home/angel/repos/helixnet/src/llm/client.py` + `compute/concierge.py` (Steward AI-assist), `/home/angel/repos/helixnet/scripts/sop-to-pdf.js` (SOP/KB + label PDF pipeline), `/home/angel/repos/helixnet/scripts/lp_create_realm.py` (Phase-4 tenant provisioning).
