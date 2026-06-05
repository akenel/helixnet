# HelixNet — Repo Map

*One platform, many tenant apps. The whole thing on one page.*
*Last mapped: 2026-06-05 (deep scan by Tigs).*

---

## What this is, in one breath

**HelixNet is a self-hosted application platform.** One FastAPI app + Postgres + Keycloak +
Docker serves many small businesses as separate tenants — each with its own login realm, its
own data, its own web UI. Built solo, ~1 year (started July 2025).

**When someone's eyes glaze over, lead with ONE of these — not the whole universe:**
- *"I built the till system running a real shop."* (Artemis POS)
- *"I built a marketplace that's live with 34 real users."* (La Piazza / BorrowHood)
- *"I built a service-management app for a camper repair shop in Sicily."* (Camper & Tour)

Then, if they lean in, show them the rest below.

**Legend:** 🟢 LIVE (wired + seeded) · 🟡 DORMANT (models ready, no router) · 🟠 HALF-WIRED
(router exists, not registered) · 🗄️ attic.

---

## 🟢 Live applications (13)

| App | What it is | Reach | Tenant realm |
|---|---|---|---|
| **La Piazza / BorrowHood** | The marketplace — list/rent/find. **Live prod, 34 users.** | `lapiazza.app` (separate `borrowhood` app/image) | `borrowhood` |
| **Artemis POS** | Felix's retail till — products, sales, line items, shifts, 5-role RBAC | `/pos` · `/api/v1/pos` | `artemis`, `pos` |
| **Camper & Tour** | Sebastino's camper service shop — vehicles, jobs, bays, quotes, invoices, appointments (12 models) | `/api/v1/camper` | `camper` |
| **Isotto Print Shop** | Famous Guy's print shop (Trapani, since 1968) — orders, customers, invoices | `/print-shop` · `/api/v1/print-shop` | `isotto` |
| **Isotto Catalog** | Print products, stock, suppliers, purchase orders, artwork | `/api/v1/print-shop/catalog` | `isotto` |
| **HR / Payroll (BLQ)** | Employees, time entries, approvals, payroll runs, payslips | `/api/v1/hr` | (platform) |
| **CRACK Loyalty + KB** | Customer tiers + gamified knowledge-base credits | `/api/v1/customers` · `/api/v1/kb` | (platform) |
| **Sourcing** | Supplier requests / bestellungen | (embedded) | (platform) |
| **QA Dashboard** | Anne's test checklist — bugs, severity, activity | `/api/v1/testing` | (platform) |
| **Unified Backlog** | Cross-app board (dev/bug/ops) | `/api/v1/backlog` | (platform) |
| **LPCX — Compute Exchange** ⭐ | Decentralised compute marketplace — jobs, RabbitMQ queue, fair-share, credit ledger, provider nodes | `/api/v1/compute` · `/compute` | (platform) |
| **La Bottega** ⭐ | The workshop — recipe menu (CV→bio, CV-generate, cover-letter), enrich-safely profiles | `/api/v1/compute/bottega` · `/compute/bottega` | (platform) |
| **Core** | Auth, users, teams, jobs/tasks/artifacts, health, admin role mgmt | `/auth` `/api/v1/users` `/api/v1/jobs` `/admin` `/health` | (platform) |

⭐ = built this week (June 2026).

---

## 🟡 Dormant — schema ready, just needs a router + seed (6)

| App | What it'd be | Models built |
|---|---|---|
| **Farm & Batch Trace ("THE SPINE")** | End-to-end track-and-trace: farm → batch → lab test → lifecycle → trace events | 5 |
| **Equipment Supply Chain** | Procurement, suppliers, POs, shipments, customs, maintenance, buy/lease/rent | 7 |
| **Inventory Management** | Stock flow (in/out/adjust/transfer), reorder, stock status | 1 |
| **Promo & Discounts** | Comps, samples, waste tracking (tax/audit) | 1 |
| **Headshop & Cafe** | CBD/coffee/accessories — categories, strengths, pricing | 1 |
| **Helix Studio** | Content/episode pipeline (idea → recording → published) | 1 |

## 🟠 Half-wired — router written, just not registered in `main.py` (3)

| App | Reach (once registered) | Note |
|---|---|---|
| **Pet Wash (Michel)** | `/api/v1/pets` | Appointments, species/size, service types — wire into `main.py` |
| **Bookstore (Stans)** | `/api/v1/books` | ISBN, genres, formats, stock |
| **Tasks (Celery monitor)** | `/tasks` | Background-job result tracking |

## 🗄️ Attic
- **`Cat` model** — "Cats only. Peter's way." A joke stub. Move to `attic/` or delete.

---

## 🧰 Infrastructure (Docker stacks)

- **core** (`compose/helix-core`): Traefik · Postgres 17 · Keycloak 24 · Redis · RabbitMQ · MinIO · MailHog · Vault · Adminer · Prometheus · Grafana · n8n · Portainer · Dozzle · autoheal · filebrowser
- **main** (`compose/helix-main`): helix-platform (the app) · Celery worker · beat · flower · **lpcx-consumer** (aio-pika)
- **llm** (`compose/helix-llm`): Ollama · OpenWebUI · (Qdrant, disabled)
- **media** (`compose/helix-media`): **Swing Music** player (Sunrise Chain) · **Jellyfin** (video)
- **pod** (`compose/helix-pod`): helix-teller
- **prod/UAT** (`hetzner/`): Caddy + core set + helix-platform + lpcx-consumer + telegram-tigs + LibreTranslate + borrowhood (+ borrowhood_staging overlay) on one CX32 (€7.59/mo)

## 🔐 Keycloak realms (8 tenants)

`borrowhood` (34 users) · `camper` (10) · `pos` (9) · `helix-dev` (6) · `isotto` (5) ·
`fourtwenty` — 420 wholesale (4) · `artemis` — Luzern headshop (4) · `blowup` — Littau cafe (2)

## 🛠️ Notable tools (`scripts/`, `src/tools/`)

- **Ops:** `helix-boot.sh` · `helix.sh` (CLI) · `smoke-test.sh` · `rotate-secrets.sh` · `helix-backup/restore.sh` + DR runbook · `helix-chaos.sh`
- **Load/test:** `lpcx_loadtest.py` · `lpcx_durability_demo.py` · `helix-load-test.py`
- **Video:** `camper-demo-record.js` · `isotto-demo-record.js` · `kc-record-ep*.js` (8-ep series) · `video-stitch.js`
- **Content:** `postcard-to-pdf.js` · `sop-to-pdf.js` · `lp_tweet.py`
- **Data:** `ingest_to_qdrant.py` · `fourtwenty-sync.py` · `kc-migrations/`

## 🎬 Content & media (the soul)

- **The Great Escape** — the manuscript: 8 chapters, ~1,822 lines (`stories/the-great-escape/`)
- **Sunrise Chain** — self-hosted music: **241 tracks across 13 regions** + 40 playlists
- **Video** — 6 projects, ~617 files: SAP-Bridge, Keycloak series, Locandina, Crowhouse, bug-fixes, helixnet-vs-corp
- **Postcards** — 8 illustrated Sicily cards, print-ready (UFA)
- **Business** — SOPs, revenue ideas, marketing/Twitter kit

---

## How to wake a dormant app (the pattern — every live app follows it)

1. `src/db/models/<app>_model.py` — models (✅ already exists for the dormant 6)
2. `src/routes/<app>_router.py` — `router` + `html_router`, `require_roles(...)` auth
3. `src/services/<app>_seeding_service.py` — idempotent seed data
4. Register in `src/main.py` — `include_router(...)` + the seed call in lifespan
5. (If a new tenant) add a Keycloak realm JSON in `compose/helix-core/keycloak/realms/`
6. `make up` / restart → `create_all` builds the tables → smoke test

That consistency — same 6 steps for all 13 live apps — is the disciplined spine under the
sprawl. The mess is in the folders, not the architecture.

---

*"We host the square, not the model." · Built solo, July 2025 → June 2026.*
