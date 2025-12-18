
# 🧩 HelixNet — Auth-Driven FastAPI Microstack

**Status:** Forged Bronze Edition 🏆
**Author:** Angel
**Tagline:** “Because you don’t learn Keycloak in school.”

---

## ⚙️ Overview

HelixNet is a **production-grade FastAPI stack** featuring:

* 🔐 **Keycloak** for enterprise-level OpenID Connect authentication
* 🚀 **Traefik** reverse proxy with automatic HTTPS (Let’s Encrypt-ready)
* 🧠 **FastAPI** core application with JWT token verification
* 🧱 **Docker Compose** orchestration
* 📊 **Swagger UI** integrated with OAuth2 password flow
* 🐇 (Optional) Celery & Redis for async jobs
* 📈 (Optional) Grafana & Prometheus for metrics

This project demonstrates a *real-world secure microservice environment* that mirrors modern SaaS architecture.
CONCEPT: for 12 year old learning tool to spin-up an enterprise middleware platform and start developing secure web apps.

## ⚙️ Overview example: Point-of-Sale PoS System:
   Here's the architecture:
   - FastAPI backend - POS endpoints (scan, checkout, reports)
   - Keycloak - Staff logins with roles (cashier, manager)
   - Postgres - Products, transactions, daily totals
   - MinIO - Store receipts/invoices as PDFs
   - Simple HTML frontend - No React, just FastAPI templates + HTMX
   - Traefik - HTTPS for in-store tablet

  This is EXACTLY what HelixNet was built for.

---

## 🛒 Production POS System (Sprint 3: RBAC Complete)

**Status:** ✅ Production-Ready with Keycloak RBAC

HelixNet now includes a **fully functional Point-of-Sale (POS) system** with enterprise-grade authentication and role-based access control.

### 🔐 Features

* **Real Keycloak Authentication** - JWT token validation with RS256 signatures
* **5-Role RBAC System**:
  * 💰️ **pos-cashier** - Create transactions, scan products, process checkout (10% discount limit)
  * 👔️ **pos-manager** - Full POS access including product management, unlimited discounts, reports
  * 🛠️ **pos-developer** - Create products for testing, limited production access
  * 📊️ **pos-auditor** - Read-only access to all transactions, products, reports (compliance)
  * 👑️ **pos-admin** - Full system control over POS realm and configuration
* **Automated Realm Import** - Infrastructure as Code (no manual Keycloak setup)
* **Startup Health Checks** - Realm status matrix showing users/clients count
* **Pre-seeded Test Users** - 6 users ready for testing (Pam, Ralph, Michael, Felix, pos-developer, pos-auditor)
* **Multi-Environment Ready** - Identical configs for DEV/UAT/PROD

### 🚀 Quick Test

```bash
# 1. Login as Pam (Cashier)
curl -k -X POST "https://keycloak.helix.local/realms/kc-pos-realm-dev/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=helix_pos_web" \
  -d "username=pam" \
  -d "password=helix_pass" \
  -d "grant_type=password" | jq -r '.access_token'

# 2. Use token to access POS API
curl -k "https://helix-platform.local/api/v1/pos/products" \
  -H "Authorization: Bearer $TOKEN"
```

### 📚 Documentation

* **Full Setup Guide**: See `docs/KEYCLOAK_SETUP.md`
* **Realm Config**: `helix-pos-realm-dev.json` (auto-imported on startup)
* **Test Users**: All passwords are `helix_pass` (demo only)

### 🧪 Test Users & Roles

| Username | Password | Role | Can Create Products? | Can View Reports? |
|----------|----------|------|---------------------|-------------------|
| pam | helix_pass | 💰️ Cashier | ❌ No | ❌ No |
| ralph | helix_pass | 👔️ Manager | ✅ Yes | ✅ Yes |
| michael | helix_pass | 🛠️ Developer | ✅ Yes | ❌ No |
| felix | helix_pass | 👑️ Admin | ✅ Yes | ✅ Yes |
| pos-auditor | helix_pass | 📊️ Auditor | ❌ No | ✅ Yes (read-only) |

### 🔧 API Endpoints

* `GET /api/v1/pos/products` - List products (any POS role)
* `POST /api/v1/pos/products` - Create product (manager/developer/admin only)
* `PUT /api/v1/pos/products/{id}` - Update product (manager/admin only)
* `DELETE /api/v1/pos/products/{id}` - Delete product (manager/admin only)
* `POST /api/v1/pos/transactions` - Create transaction (cashier/manager/admin)
* `POST /api/v1/pos/checkout` - Process checkout (cashier/manager/admin)
* `GET /api/v1/pos/reports/daily-summary` - Daily sales report (manager/auditor/admin)

All endpoints enforce RBAC via JWT token validation.

> ⚠️ **Warning:**
> This is not a beginner project. Expect to troubleshoot certificates MKCERT, CORS, and container networking via Traefik and Keycloak.
> Proceed only if you have **grit, coffee, and curiosity**.

---

## 🎵 Helix Media Player — THE SUNRISE CHAIN

**Status:** Live & Roaring 🐅

Because Spotify has ads. Because YouTube has algorithms. Because SoundCloud disappeared our account. So we built our own.

### Philosophy

> "No ads. No algorithm. No monthly ransom. Just music."
> — Electric Jungle

### What It Is

A self-hosted music player (Swing Music) with a curated collection organized by **timezone** — following the sunrise around the Earth.

```
🌅 THE SUNRISE CHAIN — 66 tracks across 13 regions

PACIFIC DAWN     → AUSTRALIA      → JAPAN-KOREA    → SOUTHEAST ASIA
INDIA-PAKISTAN   → MIDDLE EAST    → AFRICA EAST    → AFRICA WEST
EUROPE EAST      → EUROPE WEST    → AMERICAS EAST  → AMERICAS WEST
                      ↓
              SOUL FOUNDATION (the bedrock)
```

### Quick Start

```bash
cd compose/helix-media
docker compose -f media-stack.yml up -d

# Visit http://localhost:1970
# Or add to /etc/hosts: 127.0.0.1 music.helix.local
```

### Features

- **Self-hosted** — Your music, your server, your rules
- **Synced lyrics** (.lrc files for sing-along)
- **MANIFEST.md** — The story behind every track
- **WISDOM.md** — Philosopher quotes for between songs
- **yt-dlp integration** — Grab any track from YouTube

### The Legends Inside

Sam Cooke, Bob Dylan, Aretha Franklin, Pink Floyd, Queen, Led Zeppelin, The Beatles, Jimi Hendrix, Bob Marley, Nirvana, The Cult, Rolling Stones, AC/DC, and 50+ more icons from every corner of the globe.

> "Be water, my friend." — Bruce Lee

📁 **Location:** `compose/helix-media/`

---

## 🧰 Components

| Service              | Purpose                     | URL                                  |
| -------------------- | --------------------------- | ------------------------------------ |
| **Helix (FastAPI)**  | Core API                    | `https://helix-platform.local/docs`  |
| **Keycloak**         | Identity Provider (OIDC)    | `https://keycloak.helix.local`       |
| **Traefik**          | Reverse Proxy + HTTPS       | `https://traefik.helix.local`        |
| **Postgres**         | Database for Keycloak + App | Internal                             |
| **Redis (optional)** | Task broker for Celery      | Internal                             |

---

## 🔑 Authentication (Swagger)

Swagger UI supports **OAuth2 password flow** via Keycloak.

1. Click **Authorize** in Swagger.
2. Choose the scheme **OAuth2 (password)**.
3. Fill in:

   ```
   username: helix_user
   password: helix_pass
   client_id: helix_client
   client_secret: helix_pass
   ```

4. Hit **Authorize**, then test any `/api/v1/users/me` or `/protected` endpoint.

✅ If you see 200 OK, your JWT was validated successfully.

---

## 🧩 Directory Structure

```
helixnet/
├─ compose/
│  ├─ traefik/
│  ├─ keycloak/
│  └─ helix/
├─ keycloak/
│  └─ config/
│     └─ kc-realm-dev.json
├─ src/
│  └─ helix/
│     ├─ main.py
│     ├─ routes/
│     └─ auth/
├─ .env
├─ docker-compose.yml
└─ README.md
```

---

## 🪄 Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/helixnet.git
cd helixnet

# 2. Configure environment
cp .env.example .env

# 3. Start everything
./scripts/helix-boot.sh

# 4. Visit
https://helix-platform.local/docs
```

---

## 🧠 Developer Tips

* To debug Traefik routes:

  ```bash
  docker logs traefik | grep helix
  ```

* To verify Keycloak realm import:

  ```bash
  docker exec -it keycloak /opt/keycloak/bin/kc.sh show-config
  ```

* If Swagger shows `NetworkError`, check:

  * DNS: `keycloak.helix.local` must resolve
  * HTTPS certificate trust
  * CORS headers in FastAPI and Keycloak client settings

---

## 🧱 Lessons Learned

* Keycloak JSON import path **must** be absolute (`/opt/keycloak/data/import/...`)
* Traefik will report *502 Bad Gateway* if the backend container name isn’t resolvable
* Swagger’s **password flow** is the simplest for human testing
* OAuth2 + FastAPI + Docker networking = patience required

---

## 🏁 Milestone: Forged Bronze

You’ve crossed the threshold of backend alchemy —
this is where microservices become art.

> “You can’t learn this from a tutorial.
> You learn it by bleeding YAML.” — Sherlock

---

# 🌌 HelixNet Distributed Platform: Task & Data Management

🌌 HelixNet Core API: Task & Data Management
 **technical and business layers**
---

## 🚀 **HelixNet (a.k.a. SecDevOps Edition) — Elevator Pitch**

HelixNet is an **AI-driven integration and transformation engine** designed to modernize legacy enterprise data flows — without forcing companies to rebuild everything on SAP BTP or other cloud platforms.

The system takes three core inputs:

1. **Context YAML** → describes the business or technical mapping rules
2. **Content files** → raw data (CSV, flat files, SAP IDocs, SFTP drops, etc.)
3. **Target JSON schema** → defines the desired output structure

Using these, HelixNet applies an **AI-assisted transformation and mapping engine** that analyzes the input data and produces the correctly structured output JSON, ready to be injected into SAP, BTP, or any downstream system.

This lets teams **automate the painful “mapping” work** that’s traditionally done manually with tools like SAP PI/PO, Seeburger, or custom ETL pipelines.
Instead of rewriting the whole integration layer, HelixNet helps organizations **bridge old and new systems safely and affordably**, while keeping the existing infrastructure intact.

---

### 💡 In one line

> “HelixNet is an AI-powered data mapping and transformation platform that turns messy legacy files into clean, structured JSON ready for SAP and modern systems — without a full migration.”

---

### 🧠 Tech Summary (for engineers)

* Context-aware Jinja2 templates (`.j2`) drive the transformation logic.
* YAML defines metadata, mapping hints, and processing pipelines.
* JSON defines the target output shape.
* AI (via local or external models) assists with schema inference and transformation mapping.
* Docker + Traefik + Keycloak + Vault provide secure, modular, multi-service orchestration.

---

## 🧭 Phase 1 — “The Demo VPS Era” (Right Now)

✅ **Goal:** Let potential users *see and feel* the product without setup friction.
**YES**, you can — and should — run this on a **VPS using Docker Compose**.

### Why it’s the perfect move

* **Docker Compose is enough** for 1–10 users testing the system.
* You can **control access** via Keycloak (each tester gets an account).
* You can **monitor** via Traefik logs, Portainer, and even basic shell scripts.
* You don’t need the operational complexity of K3D/K8s yet.
* Your “stack” already looks like a **production-ready demo environment** — just scaled down.

Think of this as your **HelixNet Demo Cloud** — stable, limited, but *representative*.

---

## 🚀 Phase 2 — “The Self-Serve Proof of Concept”

✅ **Goal:** Turn the VPS demo into a hands-off trial experience.

You’re already thinking correctly:

> “They log in, try it 10 times, I monitor, then upsell.”

This is **the SaaS funnel**:

1. **Discovery** — They find your landing page / repo
2. **Curiosity** — They see “Try the live demo”
3. **Engagement** — They upload some data, get a real transformation
4. **Value realization** — They see how your system makes sense of messy data
5. **Conversion** — You follow up (“Would you like to integrate your real data?”)

Even if only *one or two clients* do that, it validates your product and story.

---

## 🧩 Phase 3 — “K3D or Kubernetes Migration” (Later)

✅ **Goal:** When you’ve proven user traction or paying customers.

At that point:

* Move from **VPS Docker Compose** → **K3D or true Kubernetes** (for scalability + HA)
* Add **CI/CD pipeline** for automated deploys (GitHub Actions → VPS or cluster)
* Add **Monitoring & Observability stack** (Prometheus + Grafana + Loki)
* Migrate secrets into **Vault or AWS Secrets Manager**

But don’t rush this.
It’s *better to have 5 real users on Docker Compose* than 0 users on Kubernetes.

---

## 💡 Strategic Advice

### 🧠 You already have your “product-market fit story.”

> Enterprises stuck with SAP PI/PO or legacy EDI → need modern mapping → HelixNet automates it.

That’s gold.
This story will resonate with every integration architect or SAP consultant you show it to.
You’re not selling code; you’re selling **time, safety, and modernization**.

### 🪶 Keep it lightweight & open

Offer two paths:

* **SaaS (hosted by you)** — “Sign up, upload, test in minutes”
* **Self-hosted (Docker Compose)** — “Clone, .env, up — done.”

This dual model builds trust and accelerates adoption.

### 💬 Communication & Landing

You can use:

* **GitHub Pages** or **Readme.so** for a professional landing page
* A short **demo video** (your 90-sec pitch with a terminal run-through)
* A **live URL**: e.g. `https://demo.helixnet.io` or `https://try.helix.localhost.run`

---

## 🧱 The Practical To-Do (Next 7 Days)

1. 🧹 Clean Docker Compose + `.env` (done! nearly)
2. 🧩 Deploy to VPS (Traefik + Keycloak + HelixNet Core)
3. 🧾 Add a minimal **README landing**: “What, Why, How to Try”
4. 🔐 Set up Keycloak realms for “Demo Users” (isolated)
5. 📈 Add a basic **audit logger** for user activity
6. 🎥 Record 90-sec demo video (“Upload CSV → Get JSON output”)
7. 🌐 Announce quietly on GitHub & LinkedIn (to gauge response)

---

### Current Setup Analysis

You're running a comprehensive AI development stack with:
* **AI/ML Services**: OpenWebUI + Ollama for local LLM inference
* **Core Platform**: Helix (FastAPI-based) with Celery for async tasks
* **Infrastructure**: Postgres, Redis, RabbitMQ, MinIO
* **Monitoring**: Prometheus, Grafana, Dozzle
* **Security**: Keycloak, Vault
* **Utilities**: MailHog, Adminer, Filebrowser
* **Reverse Proxy**: Traefik

### SWOT Analysis

**Strengths:**
✅ Full-stack development environment
✅ Containerized and reproducible (Docker)
✅ Built-in monitoring and logging
✅ Security-first approach (Keycloak, Vault)
✅ Local LLM capabilities
✅ Asynchronous task processing

**Weaknesses:**
⚠️ Resource-intensive for a laptop
⚠️ Complex setup with many moving parts
⚠️ Potential port conflicts (multiple services on 8080)
⚠️ Local-only by default

**Opportunities:**
🚀 Cloud deployment for production (DigitalOcean)
🚀 Scalable architecture
🚀 Potential for AI/ML application development
🚀 Could serve as a template for enterprise applications

**Threats:**
🔒 Security exposure if improperly configured
📈 Resource costs in production
🔄 Maintenance complexity

### Best Uses for This Setup

1. **AI Application Development:**
   * Build custom AI agents using Ollama models
   * Create chatbots with OpenWebUI
   * Develop RAG applications

2. **Microservices Platform:**
   * Prototype scalable applications
   * Test distributed systems patterns
   * Practice container orchestration

3. **DevOps Practice:**
   * CI/CD pipeline development
   * Infrastructure as Code (IaC) testing
   * Monitoring and logging implementation

### Production Deployment Strategy (VELIX on DigitalOcean)

**Recommended Architecture:**

```
[DigitalOcean Droplet]
├── Traefik (SSL Termination, Load Balancing)
├── Core Services:
│   ├── Helix (FastAPI) - scaled horizontally
│   ├── Postgres (Managed Database recommended)
│   ├── Redis (Managed Database recommended)
│   └── RabbitMQ
├── AI Services:
│   ├── Ollama (GPU-enabled instance recommended)
│   └── OpenWebUI
├── Monitoring:
│   ├── Prometheus
│   └── Grafana
└── Security:
    ├── Keycloak
    └── Vault
```

**Implementation Steps:**

1. **Infrastructure Setup:**

   ```bash
   # On DigitalOcean Droplet
   sudo apt update && sudo apt upgrade -y
   sudo apt install docker-compose -y
   git clone https://github.com/your-repo/velix.git
   cd velix
   ```

2. **Environment Configuration:**

   ```env
   # .env.prod
   DEPLOY_ENV=production
   DOMAIN=yourdomain.com
   TRAEFIK_EMAIL=admin@yourdomain.com
   ```

3. **Docker Compose Override:**

   ```yaml
   # docker-compose.prod.yml
   services:
     ollama:
       deploy:
         resources:
           reservations:
             devices:
               - driver: nvidia
                 count: 1
                 capabilities: [gpu]
   ```

4. **Deployment:**

   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

### Next Steps

1. **Optimize for Production:**
   * Set up proper backups for databases
   * Configure monitoring alerts
   * Implement CI/CD pipelines
   * Set up proper SSL certificates

2. **Security Hardening:**
   * Configure firewall rules
   * Set up VPN access
   * Regular security audits

3. **Scaling:**
   * Consider Kubernetes for orchestration
   * Database read replicas
   * Load balancing across multiple instances

This setup is extremely powerful for developing AI-powered applications.
A production version (VELIX) could be positioned as an enterprise AI platform or used as a foundation for custom AI solutions.
