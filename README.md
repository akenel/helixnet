# HelixNet

**An auth-driven FastAPI platform hosting La Piazza, a peer-to-peer rental marketplace, plus a POS system, a self-hosted music player, and internal QA/backlog tooling.**

| Surface | Where | Status |
|---|---|---|
| La Piazza (production) | [lapiazza.app](https://lapiazza.app/) | Live |
| La Piazza (staging) | [staging.lapiazza.app](https://staging.lapiazza.app/) | Live |
| Local dev | `https://helix.local/` | Docker Compose |
| Repo | this one | Public |

Author: Angel Kenel. Collaborator: Tigs (Claude). Made in Sicily.

---

## What lives here

| App | What it is | Path | Status |
|---|---|---|---|
| **La Piazza** | Peer-to-peer rental marketplace, raffles, quotes, calendar, helpboard, AI draft, backlog feedback | `BorrowHood/` | Production |
| **HelixNet platform** | The shared kernel: FastAPI core, Keycloak OIDC, Caddy reverse proxy, Postgres, Redis, RabbitMQ, MinIO | `src/`, `compose/` | Production |
| **POS system** | 5-role RBAC point-of-sale (cashier, manager, developer, auditor, admin) | `src/` (pos routes) | Production-ready, not yet deployed standalone |
| **Camper & Tour** | Workshop management module (vehicles, bays, quotations, job activity trail) | `src/` (camper routes) | Production, behind realm |
| **Backlog / QA dashboard** | Unified bug + feedback intake with session-report capture, activity trail, priority/status workflow | `src/routes/backlog_router.py`, `BorrowHood/src/routers/backlog.py` | Live in both staging + prod |
| **Helix Media Player** | Self-hosted music (Swing Music) — the "Sunrise Chain" curated library | `compose/helix-media/` | Live, ~90 tracks |
| **DebLLM** | Self-healing log monitoring + KB-driven auto-remediation | `debllm/`, `src/debllm/` | Code preserved, infra dormant since Nov 2025 |

---

## Architecture

### Runtime components

| Service | Purpose | Local URL |
|---|---|---|
| Caddy | Reverse proxy + automatic HTTPS (Let's Encrypt on prod, self-signed on dev) | `:443` |
| FastAPI (helix-platform) | Core API, OIDC verification, Camper/POS/Backlog routes | `https://helix.local/` |
| FastAPI (BorrowHood / La Piazza) | Marketplace API + templates | `https://lapiazza.app/` (prod) |
| Keycloak | OIDC identity provider, multi-realm | `https://keycloak.helix.local/` |
| Postgres | Database for all services | internal |
| Redis | Cache + task broker | internal |
| RabbitMQ | Async messaging | internal |
| MinIO | S3-compatible object storage (uploads, attachments) | internal |
| MailHog | SMTP sink for dev/staging | `:8025` |
| LibreTranslate | Translation backend (optional) | internal |

All services run as Docker containers, orchestrated by `docker compose`.

### Stack choices

- **Caddy** for the reverse proxy (was Traefik; switched for simpler Let's Encrypt + path routing on Hetzner)
- **Keycloak** for OIDC, RS256 JWTs verified by FastAPI
- **SQLAlchemy 2.x** async + `asyncpg`
- **Pydantic v2** for everything
- **Alpine.js + Tailwind CDN** on templates (no SPA — server-rendered first, JS for interactivity)
- **Puppeteer** for PDF generation (postcards, SOPs)
- **Playwright** for E2E tests (scaffolded under `tests/`)

---

## Environments

Locked naming convention across all apps:

| Code | Long name | Where | When |
|---|---|---|---|
| `dev` | Development | Local Docker Compose (`helix.local`) | Daily work |
| `stg` | Staging | `staging.lapiazza.app` (Hetzner) | Pre-prod sign-off |
| `uat` | User Acceptance | `uat.<app>.app` (Hetzner, only when running deeper test rounds) | Optional |
| `prod` | Production | `lapiazza.app` (Hetzner) | Real users |

**Hetzner host:** single CX32 box (4 vCPU, 8 GB RAM, ~7 €/mo). Caddy fronts everything via path-based routing.

**Deploy SOP** (mandatory — `scripts/smoke-test.sh` is the gate):

```bash
git push                                                      # local
ssh root@HETZNER_IP "cd /opt/helixnet && git pull && \
  cd hetzner && docker compose -f docker-compose.uat.yml \
  up -d --build helix-platform"
ssh root@HETZNER_IP "cd /opt/helixnet && bash scripts/smoke-test.sh hetzner"
```

Never deploy to prod without explicit staging sign-off. No exceptions, even for "low-risk" changes.

---

## Quick start (local development)

### Prerequisites

- Docker + Docker Compose
- `mkcert` for local HTTPS (or accept self-signed warnings)
- 8 GB free RAM, ~20 GB disk

### First-time setup

```bash
git clone <repo-url> helixnet
cd helixnet
cp .env.example .env                      # then edit secrets
make up                                   # full stack build + start
make status                               # check all containers healthy
```

Add to `/etc/hosts`:

```
127.0.0.1 helix.local
127.0.0.1 keycloak.helix.local
127.0.0.1 lapiazza.helix.local
```

Browse to `https://helix.local/` and you should land on the La Piazza homepage.

### Test users

All test users across all realms use password `helix_pass`. Examples:

| Username | Realm | Role |
|---|---|---|
| `helix_user` | master | Keycloak admin |
| `pam` | helix-pos | Cashier |
| `ralph` | helix-pos | Manager |
| `felix` | helix-pos | Admin |
| `alice` | borrowhood | Test buyer |
| `nino`, `angel`, `sebastino` | camper-service | Camper personas |

Full persona list: `scripts/seed-staging-personas.sh`.

---

## POS system — RBAC details

Five roles, JWT-enforced at every endpoint.

| Role | Discount limit | Can manage products | Can view reports |
|---|---|---|---|
| `pos-cashier` | 10% max | No | No |
| `pos-manager` | unlimited | Yes | Yes |
| `pos-developer` | n/a | Yes (test only) | No |
| `pos-auditor` | n/a | No | Yes (read-only) |
| `pos-admin` | n/a | Yes | Yes |

API endpoints (all under `/api/v1/pos/`): `products` (GET/POST/PUT/DELETE), `transactions` (POST), `checkout` (POST), `reports/daily-summary` (GET).

Realm config: `helix-pos-realm-dev.json`, auto-imported on startup.

---

## La Piazza — module overview

Implemented and live:

- **Listings** — create, edit, search (with `pg_trgm` similarity), publish/unpublish, raffle conversion
- **Calendar** — per-listing availability with blackout dates (recurring weekdays + date ranges)
- **Quotation requests** — buyer → seller flow, integrated into messages inbox
- **Raffles** — entries, draws, cancel/refund
- **Helpboard** — AI-assisted ticket drafting, escalation
- **Messages inbox** — threaded, with quotation requests surfaced inline
- **Backlog feedback** — public submission with session-report + screenshot capture
- **QA dashboard** — bug + test tracker (same auth as backlog)

Tested personas (`scripts/seed-staging-personas.sh`): Alice (buyer), Bob (seller), Carol (admin), Eve, Gia, Gemma, plus 11 imported demo users. All use `helix_pass`.

---

## Helix Media Player — the Sunrise Chain

> "No ads. No algorithm. No monthly ransom. Just music."

Self-hosted Swing Music instance with a curated library organized by timezone — songs follow the sunrise around the planet.

```
PACIFIC DAWN    AUSTRALIA    JAPAN-KOREA    SOUTHEAST ASIA
INDIA-PAKISTAN  MIDDLE EAST  AFRICA EAST    AFRICA WEST
EUROPE EAST     EUROPE WEST  AMERICAS EAST  AMERICAS WEST
                          |
                  SOUL FOUNDATION
```

Each track ships with synced lyrics (`.lrc`), a `MANIFEST.md` for provenance, and a `WISDOM.md` of between-song quotes. Tracks pulled via `yt-dlp` and curated by hand.

```bash
cd compose/helix-media
docker compose -f media-stack.yml up -d
# Visit http://localhost:1970
```

Library: `compose/helix-media/music/sunrise-chain/`

---

## Project structure

```
helixnet/
  BorrowHood/                  La Piazza application (FastAPI + templates)
    src/                       Models, routers, services, templates
    tests/                     Pytest suite
  compose/
    helix-media/               Music player stack
    keycloak/                  Realm JSON + bootstrap
  debllm/                      Self-healing monitor (dormant)
  docs/
    business/                  Postcards, SOPs, business plans
    design/                    Architecture design docs (LP CLI drafts, etc.)
    runbooks/                  Operator runbooks (secret rotation, etc.)
    testing/                   QA + UAT documentation
  hetzner/                     Production compose + env files (.env gitignored)
  scripts/
    smoke-test.sh              25-check post-deploy gate
    preflight.sh               28-point environment inspector
    rotate-secrets.sh          Interactive secret rotation
    seed-staging-personas.sh   Persona seeding
    sop-to-pdf.js              Puppeteer-driven PDF generation
  src/                         HelixNet kernel: FastAPI app, Keycloak,
                               POS, Camper, Backlog routes
  stories/                     The Great Escape narrative
  tests/                       Playwright E2E suite
  UFA_r2p/                     Print-ready PDFs (postcards, labels)
  videos/                      Video production assets (MP4s gitignored)
  CLAUDE.md                    Persistent context for the AI co-pilot
  Makefile                     `make up`, `make status`, `make logs`
```

---

## Authentication walk-through

The FastAPI app validates JWTs with Keycloak's RS256 public key.

### From Swagger UI

1. Open `https://helix.local/docs`
2. Click **Authorize**, choose **OAuth2 password flow**
3. Enter:
   ```
   username: helix_user
   password: helix_pass
   client_id: helix_client
   ```
4. Submit, then any `/api/v1/users/me` call should return 200.

### Direct token request

```bash
TOKEN=$(curl -sk -X POST \
  "https://keycloak.helix.local/realms/helix/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=helix_client" \
  -d "username=helix_user" \
  -d "password=helix_pass" \
  -d "grant_type=password" | jq -r '.access_token')

curl -sk "https://helix.local/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Operational state

| Area | State |
|---|---|
| Prod (`lapiazza.app`) | Live, healthy |
| Staging (`staging.lapiazza.app`) | Live |
| CI/CD | Partial — GitHub Actions on PR/push for BorrowHood tests; full CD pipeline still to wire |
| Operational housekeeping | Secret rotation in flight; tracked via `docs/runbooks/secret-rotation.md` |
| Monitoring | DebLLM code preserved, infrastructure dormant |
| E2E tests | Playwright scaffolded under `tests/`; scenario suites (O2C, P2P, mixed-role) on the roadmap |

---

## Documentation

| Topic | File |
|---|---|
| Persistent AI co-pilot context | `CLAUDE.md` |
| Deploy + smoke-test SOP | `scripts/smoke-test.sh` (script itself documents the checks) |
| Secret rotation runbook | `docs/runbooks/secret-rotation.md` |
| Resume points (session pickup notes) | `docs/runbooks/RESUME-*.md` |
| Architecture design docs | `docs/design/` |
| Hotel + business SOPs | `docs/business/consulting/HOTEL-SOP-MASTER.md` |
| Print-ready postcards + labels | `UFA_r2p/` |

---

## Warning

This is not a beginner project. Expect to troubleshoot certificate trust (`mkcert`), CORS, container networking, Caddy path routing, Keycloak realm configuration, Postgres ownership transfers, and the occasional 3am DB password drift. Proceed only if you have grit, coffee, and curiosity.

---

## Roadmap (live tasks)

- Wire CI staging-green gate into prod deploys
- Build Order-to-Cash, Procure-to-Pay, and mixed-role Playwright scenario suites
- Rename Hetzner UAT compose files to PROD
- Complete secret rotation (in flight)
- BorrowHood → La Piazza rebrand sweep (artifacts only; live app is already La Piazza)
- Demo path: `/demo` route with guided auto-login for first-time visitors
- Decide DebLLM revival vs. archive

Full task list lives in the repo's internal task tracker.

---

## License

TBD — for now: "All rights reserved. If you fork it, tell Angel why."

---

*"Be water, my friend." — Bruce Lee*
*"Casa è dove parcheggi." — Home is where you park it.*
