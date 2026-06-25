<!-- The map of everything in the HelixNet monorepo, so we stop losing track and stop reinventing
wheels. First generated 2026-06-20 from src/routes, src/db/models, src/templates, src/schemas, docs.
Refreshed 2026-06-25: Banco drawn as a CLUSTER (one ERP), HR marked system-of-record with My Day as
its POS view, one-screen tree added. Clickable version: HELIXNET-ESTATE-MAP.html. -->

# HelixNet Estate Map

*One engine (HelixNet), many apps under the **La Piazza** roof. ~19 app surfaces, ~72 domain models,
~710 markdown files — a year of work. This is the living inventory: what's built, what's sketched, the
**Banco ERP cluster**, and the naming/subdomain convention that keeps it from getting messy.*

> **The rule, up front:** we do NOT split repos. This is a **modular monolith** — one FastAPI app, one
> DB, one Keycloak. A "module" = `routes/<x>_router.py` + `templates/<x>/` + `db/models/<x>_*.py` +
> `services/<x>_seeding.py`. Products get a **subdomain**; internal modules get a **path**; the engine
> never gets a customer name. Separation is by **convention**, not by repository.

---

## 0. The sitemap at a glance (the one screen)

```
lapiazza.app  ── the FAMILY ROOF (the town square) ─────────────────────────────────────
│
├─ PRODUCTS  (a brand a customer uses → gets a subdomain)
│   ├─ 🛒 BANCO        banco.lapiazza.app     = the head-shop ERP  ← a CLUSTER, not one app:
│   │      └── POS (till) · HR (people) · Customer (loyalty) · KB (knowledge)
│   ├─ 🏛️ BOTTEGA      bottega.lapiazza.app   = the workshop  ← Cleo concierge · recipes · compute
│   └─ 🪪 LA PIAZZA     lapiazza.app           = the marketplace  ← ⚠ SEPARATE REPO (BorrowHood)
│
├─ CLIENT / PARTNER apps  (own subdomain when they run it live)
│   ├─ 🚐 Camper & Tour   "the garage" (Sebastino)  — the most-built surface here (4,044 lines)
│   └─ 🖨️ ISOTTO Sport     "the print shop"  — catalog · suppliers · POs · label/print pipeline
│
├─ INTERNAL modules  (staff/dev → a PATH, no subdomain)
│   ├─ 👔 HR  /hr        ← SYSTEM OF RECORD for people (employees · time · payroll)
│   ├─ 🐞 Backlog /backlog  · 🧪 QA /qa  · 👑 Admin  · 📚 KB  · 🎮 Customer (shared)
│   └─ auth · users · jobs · tasks · health        = engine plumbing
│
├─ ⚙️ THE ENGINE  (never customer-named)  = src/llm (model-as-data) · src/compute (recipe = BOM)
│                                            · Keycloak (multi-realm) · 72-model DB · print pipeline · RabbitMQ
│
└─ 💤 CONCEPTS  (models/schemas only — designed, not wired)
       farm → batch → lab_test → traceable_item → trace_event  (seed-to-sale traceability)
       headshop_cafe · helix_studio · (experiments: pets · bookstore)
```

---

## 1. The scale
- **~19 routers** (app surfaces / APIs) · **~72 domain models** · **~710 .md files** · 16k+ lines of router code.
- It is NOT a pile of toys — several apps are deeply built (Camper alone is 4,000+ router lines).
- **Two repos only:** this monolith (`helixnet`, everything below) **+** the marketplace (`BorrowHood`,
  a different stack behind `lapiazza.app`). Nothing else is its own repo — and shouldn't be.

## 2. The BANCO cluster — one ERP, four modules (the head-shop product)
Banco isn't a single app; it's an **assembly** of modules under `banco.lapiazza.app`. This is the cluster
the head-shop ERP is built from:

| Module | Router lines | Role in Banco | Surface |
|---|---|---|---|
| **POS** | 1,906 | The till — sell, scan, drawer, Z-report, born-once catalog | `/pos/*` (Pam's screens) |
| **HR** | 976 | **System of record for PEOPLE** — employees, time entries, payroll, payslips | `/hr/*` API + (new) staff screens |
| **Customer** | 633 | CRACK loyalty / member records / QR | `/pos/customer-*` |
| **KB** | 628 | Knowledge base / contributions | `/kb/*` |

**The POS ↔ HR seam (locked 2026-06-25):** HR **owns** the people; POS **consumes** them.
- **`My Day`** (`templates/pos/my_day.html`, route `/pos/my-day`) = the **till-side view** of HR — the
  employee's living day + daily close-out. It lives in `templates/pos/` *on purpose* (it's the consumer
  view), reading the HR API (`/api/v1/hr/*`).
- The **HR module** owns the master record: new-hire onboarding (AHV/DOB/address, once), the employee
  card, calendar/rota, approvals, payroll. When built, those screens get their own **`templates/hr/`**.
- POS **never creates** an employee — Felix will **pick cashiers from the HR list** in Banco Settings.
- See `docs/BANCO-CLOSEOUT-TIMESHEET-AND-GOLIVE.md` for the full closeout/timesheet/auto-tally design.

## 3. Other BUILT apps (router + templates + models — real, usable)
| App | Size (router lines) | What it is | Tier |
|---|---|---|---|
| **Camper** | 4,044 | Camper & Tour service/QA/jobs app ("the garage") | client app |
| **Bottega** | 2,093 | The workshop: recipes-as-procedure, Cleo concierge, compute | **product** |
| **ISOTTO** (+catalog) | 1,386 + 949 | Print shop: catalog, suppliers, POs, label/print pipeline | partner app |
| **QA** | 626 | QA dashboard (bugs/tests) | internal tooling |
| **Compute** | 617 | LPCX compute exchange | **product/infra** |
| **Backlog** | 454 | Unified backlog + feedback intake (the 💬 button) | internal tooling |
| **Admin** | 425 | Admin surface / role management | internal |

## 4. PARTIAL / smaller apps (router exists, lighter)
`pets` (610) · `bookstore` (247) · `jobs` (208) · `users` (137) · `tasks` (108) · `auth` (86) · `health` (101).
Mostly engine plumbing or early prototypes — fine, just don't mistake them for verticals.

## 5. DESIGNED-but-not-built (models/schemas only — no router/UI yet)
**This is the hidden gold.** A whole farm-to-table / seed-to-sale concept is captured as data models +
schemas, just not wired into an app:
- **Track & trace / seed-to-sale:** `farm`, `batch`, `lab_test`, `traceable_item`, `trace_event`,
  `shipment`, `customs_clearance`, `sourcing_request` models; `e2e_track_trace_schema.py`.
- **Farm-to-locker / cafe:** `headshop_cafe` model; `farm_to_locker_schema.py`, `salad_bar_ecosystem_schema.py`,
  `worker_lunchbox_schema.py`, `supply_chain_roles_schema.py`, `equipment_supply_chain_schema.py`.
- **Studio:** `helix_studio` (model + schema + seeding).
> **Why it matters for Banco:** Swiss CBD compliance (THC%, lot, lab number = the compliance receipt) is
> a differentiator nobody has — and **the data model is already prototyped**
> (`farm → batch → lab_test → traceable_item → trace_event`). A wheel already cut, needs mounting.
> **The mount now exists:** the vision engine's `lab_report` domain (`src/services/vision`) reads a lab
> certificate's THC%/lot/lab№ — wiring that read into `lab_test`/`batch`/`trace_event` is the next brick
> (domain DEFINED, consumer not yet built).

## 6. The shared ENGINE (HelixNet platform — invisible to customers)
Auth (Keycloak multi-realm), `src/llm` (run_llm, model-as-data), **`src/services/vision`
(vision-as-data — read a photo into structured data; one brain, a registry of `VisionDomain`
tasks; model-agnostic, Gemini default)**, `src/compute` (recipes/runner = a BOM engine), the
~72-model DB layer, the print pipeline (`sop-to-pdf.js`, `postcard-to-pdf.js`), RabbitMQ
fair-share queue, the backlog/feedback tooling. **This is the trunk. It never gets a customer-facing name.**

## 7. Naming & subdomain convention (the decision that prevents mess)
**Not every app needs a subdomain. PRODUCTS do; modules and concepts don't.**

| Tier | Gets | Examples |
|---|---|---|
| **Product** (a brand a customer uses) | its own subdomain of `lapiazza.app` now; its own apex domain later | `lapiazza.app` (marketplace), `bottega.lapiazza.app` (workshop), `banco.lapiazza.app` (shop ERP) |
| **Tenant** (one customer's instance of a product) | a sub-level under the product | Felix = `artemis.banco…` (later); for now rides `banco.lapiazza.app` |
| **Internal module** (staff/admin/dev) | NO public subdomain — lives at a path | `/hr`, `/backlog`, `/qa`, `/admin`, `/kb` |
| **Client/partner app** | own subdomain only if that client runs it live | Camper, ISOTTO |
| **Concept** (models/schemas only) | nothing yet — wait until built | farm-to-locker, salad-bar, track-trace |

**Rule that keeps it safe:** hostnames live in config, never hardcoded — so adding a subdomain/A-record is
a DNS + config change, never a code rewrite. The engine (`HelixNet`) is never renamed.

## 8. Health check — is it messy? (refreshed 2026-06-25)
**The code seams are clean; watch three smells (none urgent):**
1. **Flat `db/models/` (72 files).** Camper/ISOTTO are prefixed (`camper_*`, `isotto_*`); POS/HR/Bottega
   aren't. A future tidy (prefix or subfolder), not a refactor.
2. **Experiments next to verticals** (`pets`, `bookstore`, farm-to-locker) make it *look* busier than it is.
   They're prototypes + the designed-not-built gold — label them, don't delete them.
3. **Keep THIS map current.** The "messy" feeling is usually the map drifting from `src/`, not the code.
   Regenerate after each cluster change.

**Verdict:** the modular monolith is the right shape for a solo dev. Refresh the map; don't split repos.

## 9. What this means for Banco (the reuse map)
Banco is **assembly, not invention.** Already in the repo:
- **Till:** POS (built) + Banana export, stock deduction, Z-report.
- **People:** HR — `employee`/`time_entry`/`payroll_run`/`payslip` (built) + My Day (the POS view, shipped).
- **Inventory/suppliers:** `inventory`, `supplier`, `purchase_order`, `store_settings` (models there, routers wiring).
- **Compliance/traceability:** `farm`/`batch`/`lab_test`/`trace_event` (designed — the Swiss CBD differentiator).
- **Production/BOM:** `recipes.py`/`runner.py` (a recipe IS a BOM).
- **Labeling/white-label:** ISOTTO catalog + the print pipeline.
- **AI-assist:** `src/llm` (text, model-as-data) + Cleo + **`src/services/vision` (photo→structured
  data, model-agnostic).** First consumer WIRED: POS `/products/ai-suggest` ("Snap & fill" on the
  catalog + scan screens — photo of an unmarked item → drafted name/category/price). Next consumers
  (same brain, just register a `VisionDomain`): ISOTTO catalog photos, La Piazza photo listings, and —
  the moat — **seed-to-sale lab reports** (the `lab_report` domain is already DEFINED, §5).
