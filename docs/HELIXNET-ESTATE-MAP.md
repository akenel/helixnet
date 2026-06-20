<!-- The map of everything in the HelixNet monorepo, so we stop losing track and stop reinventing
wheels. Generated 2026-06-20 from src/routes, src/db/models, src/templates, src/schemas, docs. -->

# HelixNet Estate Map

*One engine (HelixNet), many apps. ~18 app surfaces, 71 domain models, ~710 markdown files — a year of
work. This is the inventory: what's built, what's sketched, and a naming/subdomain convention so each
real product gets a home without renaming the engine.*

## 1. The scale
- **18 routers** (app surfaces / APIs) · **71 domain models** · **~710 .md files** · 16k+ lines of router code.
- It is NOT a pile of toys — several apps are deeply built (Camper alone is 4,000+ router lines).

## 2. BUILT apps (router + templates + models — real, usable)
| App | Size (router lines) | What it is | Public? |
|---|---|---|---|
| **Camper** | 4,044 | Camper & Tour service/QA/jobs app (the most built thing here) | client app |
| **Bottega** | 2,093 | The workshop: recipes-as-procedure, Cleo concierge, compute | **product** |
| **POS** | 1,906 | The till → **Banco** (Felix's shop ERP starts here) | **product** |
| **ISOTTO** (+catalog) | 1,386 + 949 | Print shop: catalog, suppliers, POs, label/print pipeline | partner app |
| **HR** | 976 | Employees, payroll, payslips, time entries | internal module |
| **Customer** | 633 | Customer/loyalty records, QR | shared module |
| **KB** | 628 | Knowledge base | internal/shared |
| **QA** | 626 | QA dashboard (bugs/tests) | internal tooling |
| **Compute** | 617 | LPCX compute exchange | **product/infra** |
| **Backlog** | 454 | Unified backlog + feedback intake | internal tooling |
| **Admin** | 425 | Admin surface | internal |

## 3. PARTIAL / smaller apps (router exists, lighter)
`pets` (610) · `bookstore` (247) · `jobs` (208) · `users` (137) · `tasks` (108) · `auth` (86) · `health` (101).
Mostly modules or early prototypes.

## 4. DESIGNED-but-not-built (models/schemas only — no router/UI yet)
**This is the hidden gold.** A whole farm-to-table / seed-to-sale concept is captured as data models +
schemas, just not wired into an app:
- **Track & trace / seed-to-sale:** `farm`, `batch`, `lab_test`, `traceable_item`, `trace_event`,
  `shipment`, `customs_clearance`, `sourcing_request` models; `e2e_track_trace_schema.py`.
- **Farm-to-locker / cafe:** `headshop_cafe` model; `farm_to_locker_schema.py`, `salad_bar_ecosystem_schema.py`,
  `worker_lunchbox_schema.py`, `supply_chain_roles_schema.py`, `equipment_supply_chain_schema.py`.
- **Studio:** `helix_studio` (model + schema + seeding).
> **Why it matters for Banco:** the grand plan called Swiss CBD compliance (THC%, lot, lab number = the
> compliance receipt) a differentiator nobody has. **You already prototyped the data model for it** —
> `farm → batch → lab_test → traceable_item → trace_event`. That's seed-to-sale traceability, designed,
> waiting to be wired. Not a wheel to reinvent — a wheel already cut, needs mounting.

## 5. The shared ENGINE (HelixNet platform — invisible to customers)
Auth (Keycloak multi-realm), `src/llm` (run_llm, model-as-data), `src/compute` (recipes/runner = a BOM
engine), the 71-model DB layer, the print pipeline (`sop-to-pdf.js`, `postcard-to-pdf.js`), RabbitMQ
fair-share queue, the backlog/feedback tooling. **This is the trunk. It never gets a customer-facing name.**

## 6. Docs (~710 .md)
SOPs, the UFA/postcard business, La Piazza/Bottega plans, stories (the Great Escape), workout/coach notes,
video kits, REVENUE-IDEAS, and now the head-shop ERP grand-plan + cutover. A genuine knowledge base —
worth an index of its own later.

## 7. Naming & subdomain convention (the decision)
**Not every app needs a subdomain. PRODUCTS do; modules and concepts don't.**

| Tier | Gets | Examples |
|---|---|---|
| **Product** (a brand a customer uses) | its own subdomain of `lapiazza.app` now; its own apex domain later | `lapiazza.app` (marketplace), `bottega.lapiazza.app` (workshop), `banco.lapiazza.app` (shop ERP) |
| **Tenant** (one customer's instance of a product) | a sub-level under the product | Felix = `artemis.banco…` (later); for now rides `banco.lapiazza.app` |
| **Internal module** (staff/admin/dev) | NO public subdomain — lives at a path or under an admin host | `/backlog`, `/qa`, `/hr`, `/admin`, `/kb` |
| **Client/partner app** | own subdomain only if that client runs it live | Camper, ISOTTO |
| **Concept** (models/schemas only) | nothing yet — wait until built | farm-to-locker, salad-bar, track-trace |

**Rule that keeps it safe:** hostnames live in config, never hardcoded — so adding a subdomain/A-record is
a DNS + config change, never a code rewrite. The engine (`HelixNet`) is never renamed.

## 8. What this means for Banco (the reuse map)
Banco is **assembly, not invention.** Already in the repo:
- **Till:** POS (built) + today's bricks (Banana export, stock deduction, print Z-report).
- **Inventory/suppliers:** `inventory`, `supplier`, `purchase_order`, `store_settings` (models there, routers to wire).
- **Compliance/traceability:** `farm`/`batch`/`lab_test`/`trace_event` (designed — the Swiss CBD differentiator).
- **Production/BOM:** `recipes.py`/`runner.py` (a recipe IS a BOM).
- **HR/payroll:** `employee`/`payroll_run`/`payslip`/`time_entry` (built).
- **Labeling/white-label:** ISOTTO catalog + the print pipeline.
- **AI-assist:** `src/llm` + Cleo.
The grand plan's phased roadmap (HEADSHOP-ERP-GRAND-PLAN.md) maps each of these to a phase.
