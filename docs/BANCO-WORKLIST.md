# Banco Go-Live Worklist — THE ordered list

> 🔑 **Code word "ON DECK"** → you're reading the right file. State the top items and start executing the first actionable one. No re-planning, no re-asking.

*Open this, work top-down, finish one tier before opening the next. Don't fan out across five things. 2026-06-28.*

*Owners: 🧍 = Angel's hands needed (physical / decision / external call) · 🐯 = Tigs can do it · 👥 = both, together.*

*Detail lives in: [BANCO-GO-LIVE-READINESS.md](BANCO-GO-LIVE-READINESS.md) (analysis) · [BANCO-DAY-ONE-WISHLIST.md](BANCO-DAY-ONE-WISHLIST.md) (polish backlog).*

---

## 🃏 ON DECK — 2026-07-03 (end of the backup-brain + Freehold session) ← START HERE

**TWO live threads — check with Angel which one he wants first.**

**① 🐺 FREEHOLD — the legacy starter kit (born today; what Angel reached for next).** Repo `/home/angel/repos/freehold` (git init'd, **NOT pushed**). *"Own your stack. Owe no one."* — a teachable, production-grade, own-it-outright app foundation harvested from helixnet: the anti-Vercel/lock-in answer, a gift to teach real craft, and a resilience hedge. **Done:** manifesto + spec + favicon + **✅ Phase 1 SKELETON (boot-proven 2026-07-03)** — `docker compose up -d` = postgres + keycloak(3 realms) + FastAPI + Caddy; app renders via Caddy `localhost:8080`, DB connected (PG 16.13), all 3 realms 200. Commit `7708788`. **✅ Phase 2 (the door, `8ab876b`) + ✅ Phase 3 (the rails, `950e92b`) DONE + proven.** Rails = stdlib Python `ops/`: deploy (stamp→backup-gates-prod→rebuild→health→prove served==stamped), backup (AES-256 encrypt + RESTORE DRILL), env-parity; app serves `/version`. VERIFIED: deploy b5·950e92b served==stamped, RESTORE VERIFIED, parity clean+matches HEAD. **✅ Phases 1-5 + enterprise-taste + manifesto DONE (browser-proven, 12 commits, latest `1de9b0a`).** Skeleton→door(OIDC+RBAC)→rails(deploy/backup-gate/parity)→loop(SQLAlchemy+Alembic feedback→QA)→base pages→**i18n EN+हिन्दी incl KC login**→**multi-currency ₹lakh/crore**→**manifesto** (/manifesto editorial 'New Evolution'). **CAPSTONE = La Piazza LISTINGS**, built ONE CLEAN SLICE AT A TIME (Angel: rebuild-all=overkill): a listing = post+photo(MinIO)+desc+category+profile+RBAC + BYO-brain 'write my description'; then events/raffles as further slices; BYOH compute-exchange = crown jewel last. **✅ GitHub PUSHED (github.com/akenel/freehold, MIT, 15 commits) + BASE ESSENTIALS DONE: HTTPS (Caddy internal CA, https://localhost:8443), test suite (make test 14 green), system pulse (/pulse diagnostics), PWA (installable+offline).** **✅ Profile slice (MinIO+Markdown+CRUD) + Swagger(/docs) + /sitemap + shared Banco-style nav/status bar (health dot·env·clock-w-seconds·build·SHA·lang·avatar·hamburger) DONE — 18 commits.** NEXT: bottom app bar (PWA) + more La Piazza slices (events/raffles). ⚠️ Freehold LOCAL-ONLY/unpushed — Angel making GitHub repo → then PUSH + wire footer GitHub icon. Detail: memory `freehold-starter-kit`. Frontend LOCKED = server-HTML + Tailwind + Alpine + `fetch()` (React is *rented*, Freehold is *owned*). Full detail: memory `freehold-starter-kit`.

**② 📮 Head-shop campaign — Rudestore card READY TO MAIL.** Stephan's handshake card (№4, DE) is locked; the landing (opaque token `/kaffee/VSWkHkZYVdst`) + 3-option CTA + Resend email-notify are **LIVE + proven on prod**. **🧍 Angel action:** print the 2-up A4, stamp, POST it → Stephan scans Monday → email pings. In parallel: the Felix re-open message (drafted) + the Discovery→Replicate→Reveal engine (field kits served at `/scope` + `/discovery`). Detail: memory `banco-headshop-vertical-mosey-gtm`.

**Also SHIPPED this session (Banco, all 3 envs, verified + backed up):** login-page dynamic build footer; status-bar trim (removed "System OK" text → dot only; clock → HH:MM, no seconds/tz; SHA off the bar, kept in tooltip; killed the stale "Sprint 4" line). **The backup-brain PARACHUTE is rigged + PROVEN** (memory `ai-backup-brain-plan`): `scripts/code-with-openrouter.sh` = Aider+OpenRouter/DeepSeek edits+commits hands-free (~$0.002/edit); Turbo direct; Groq spare; keys persisted in `uat.env`. ⚠️ OpenRouter key was rotated (old one had printed in-transcript — Angel revoked it).

---nco Go-Live Worklist — THE ordered list

> 🔑 **Code word "ON DECK"** → you're reading the right file. State the top items and start executing the first actionable one. No re-planning, no re-asking.

*Open this, work top-down, finish one tier before opening the next. Don't fan out across five things. 2026-06-28.*

*Owners: 🧍 = Angel's hands needed (physical / decision / external call) · 🐯 = Tigs can do it · 👥 = both, together.*

*Detail lives in: [BANCO-GO-LIVE-READINESS.md](BANCO-GO-LIVE-READINESS.md) (analysis) · [BANCO-DAY-ONE-WISHLIST.md](BANCO-DAY-ONE-WISHLIST.md) (polish backlog).*

---

## 🃏 ON DECK — HEAD-SHOP CAMPAIGN (2026-07-02 eve) ← START HERE

**CUSTOMER #1 (Rudestore, Luzern · Stephan Frei · Postino #11) — FULL PIPELINE LIVE + PROVEN on prod:**
scope-out → handshake card (№ 4, DE, his shopfront) → QR **opaque token** `/kaffee/VSWkHkZYVdst` (enumeration-proof) → personalized landing (**3-option CTA**: Ruf mich an / Komm vorbei / Zusammensitzen + comment; **Ecolution GmbH · Mattenweg 5 · 6375 Beckenried** identity; no video) → captured lead → **email notification via Resend → ecolution.gmbh@gmail.com**. Tested end-to-end with Angel's phone + inbox (real scan tracked + 2 notification emails received). Card PDF + **2-up A4** ready (`docs/business/postcards/headshop-campaign/out/rudestore-stephan{,-2up}.pdf`).

**🧍 Angel:** print (2-up A4 = keep one + mail one), stamp, POST → lands ~Mon 2026-07-07 → Stephan scans → email pings you.

**🐯 NEXT (top of deck):**
1. **`/app/data` persistent volume** — scan/lead log lives IN the container; `docker restart` (normal deploys) preserves it, but a RECREATE wipes it. Add a named volume before real leads flow. NOT urgent (restart-safe) but real.
2. **Systemic opaque tokens** — only Rudestore's ext_id is opaque; randomize token generation for ALL leads before card #2 (decouple Postino ext_id from the seed-dedupe key).
3. **FR/IT/EN native review** of card + landing before mailing a non-DE shop.
4. **Scale:** same first card to the next A-list (Hanfbob's / Zauber / Paff Paff) — sniper, one card, never a second.

**Prod:** all 3 banco envs on `main`; coffee landing + email LIVE (banco.lapiazza.app); `uat.env` has `COFFEE_SMTP_*` (Resend); encrypted backups via `banco_backup.sh`.

---nco Go-Live Worklist — THE ordered list

> 🔑 **Code word "ON DECK"** → you're reading the right file. State the top items and start executing the first actionable one. No re-planning, no re-asking.

*Open this, work top-down, finish one tier before opening the next. Don't fan out across five things. 2026-06-28.*

*Owners: 🧍 = Angel's hands needed (physical / decision / external call) · 🐯 = Tigs can do it · 👥 = both, together.*

*Detail lives in: [BANCO-GO-LIVE-READINESS.md](BANCO-GO-LIVE-READINESS.md) (analysis) · [BANCO-DAY-ONE-WISHLIST.md](BANCO-DAY-ONE-WISHLIST.md) (polish backlog).*

---

## 🃏 ON DECK — HEAD-SHOP CAMPAIGN (2026-07-02, ~2:30pm) ← START HERE

**IN FLIGHT:** Angel is out doing the **Rudestore (#11, Luzern) scope-out** — the secret-shopper dry-run (first-customer test, before Felix). Back ~4:20pm with a **shop photo + one line of scoop**.

**THE MACHINE (built + committed on main):** Handshake card (DE/FR/IT/EN, № serial, photos/logo, 2-up) + `render_card.py` · personalized multilingual landing (event/invite CTA, {{LANDING_INTRO}}) served by Banco `/kaffee/{token}` · tracking + web→CRM loop (scan/Ja → log + ecolution email + Telegram → Postino by ext_id) · **Postino CRM** (`crm/postino`, LOCAL `crm/start.sh` → :8900 / phone 192.168.178.24:8900) — **184 leads** (11 A), **journey checklist** (scope-out→close, time-of-day + quick-checks), **artifact store** (FS/MinIO), **scope survey** at `/scope` (offline, phone, GPS, 120% guard) · docs: `MASTER-LIST-RECIPE.md`, `LEAD-TO-CLOSE-PROCESS.md`, `scope-sheet.html`.

**🐯 WHEN ANGEL IS BACK (top of deck):**
1. **Finish the Rudestore dry-run** — paste his scope summary into Postino #11's scope note; take his **photo + scoop** → generate **Stephan's card** (DE, "war grad bei dir im Laden…", his photo, № serial) → he prints + mails → watch #11 walk the board.
2. **Tune the process end-to-end** — real feedback from the live run (smooth the scope→Postino handoff).
3. **CRM glow-up (ONE pass):** deploy ONE hosted Postino (phone-reachable) + simple login (one password, NOT a KC realm) + build/env footer + Banco look-and-feel + photo-attach. AFTER the KC-realm terminal is clear (one driver per shared surface).

**LOCKED DECISIONS:** postcard (not letter) = warm opener, letter later = the formal close · Postino = solo tool → ONE instance + simple auth (NOT 3-tier/KC — right-sized) · ONE driver per shared surface · Felix→Mosey run in parallel (highest-odds first customer).

**Full context (memory):** `banco-headshop-vertical-mosey-gtm` · `one-driver-orchestration-preference`.

---

## ✅ RESOLVED 2026-06-29 — identity terminal collision recovery
The 2026-06-28 collision (a `checkout --force` reverted the identity terminal's uncommitted patches on sandbox + banco-staging) is **fully recovered**:
- [x] Identity terminal's commits **landed on `main`** — `92aabaa` is in `main` history.
- [x] All 3 envs **redeployed from updated main** — sandbox/staging/prod parity-green at `aae0629`, build stamp `b1384` uniform.
- [x] **Zero orphan `.bak` files** remain anywhere in the tree (the collision fingerprint is gone); `origin/main` = local `main` = live prod.
- [ ] *Carry-forward into P4:* confirm prod's KC-realm config carries the fold (code is verified; realm config is the open piece — folded into the prod-identity blocker below).
*Full detail: memory `banco-terminal-collision-2026-06-28`.*

---

## ✅ SHIPPED + SIGNED OFF — 2026-06-28
- [x] **Product Sales report** — what sold, tap → who-bought-it (cards), category drill + emoji, card → receipt, origin-gated ← Back, CSV/print, manager-gated (pam 403). LIVE on prod, human-green.
- [x] **Mobile responsive pass** — POS was tablet-sized; added a ≤480px breakpoint (tablet untouched) + per-screen fixes. iPhone SE clean. Audit harness = `scripts/testing/mobile-overflow-audit.js`.
- [x] **EXACT cash-payment bug** — false "Insufficient payment" on `.17`-type totals (JSON number → imprecise Decimal). Fixed at cent precision + regression test. Angel verified the sale on prod.
- [x] **Refund policy = manager-only** (confirmed keep) — pam can't refund, felix can; enforced UI + server.
- **Sign-off:** TEST-B03 hypercare 14/15 PASS, "really good". All 3 envs byte-identical to main `0707093`. Fresh verified prod backup taken before deploy.

---

## 🚧 GO-LIVE BLOCKERS — must be done before Felix runs his shop (in this order)

- [x] **P1 — Fiscal sign-off. ✅ ASSUMED-APPROVED (SIMULATION).** 🧍 For the sim we assume the
  Treuhänder reviewed the samples and signed off clean — gapless/immutable numbering + per-rate VAT
  are approved, nothing done wrong. **This is a simulation stand-in, NOT a real sign-off.** The package
  is send-ready (`docs/business/banco-fiscal/`: receipt + Z-report PDFs + bilingual cover note).
  **⚠ At the REAL cutover, actually run the process:** fill `[Name]`/`[Angel]`, send to the real
  Treuhänder, get the written thumbs-up, THEN flip this to truly done. Until then it's green *for the
  simulation only.*
- **P2 — Network resilience.** *Re-scoped 2026-06-29 (see `BANCO-OFFLINE-AND-PWA-PLAN.md` decision banner).*
  - [x] **P2.1 — atomic, idempotent `POST /pos/sales`** (whole cart + payment in ONE call, idempotent on a client UUID; till switched). **SHIPPED prod `9cf8f9e`/`b1391`** — human-green TEST-P21 (11/11 Fairphone, signed PDF in `docs/testing/banco/Test-Scripts/`), per-env `client_uuid` proof, atomic==legacy parity test, backup-gated. Kept the better online checkout.
  - [x] **Offline = clear warning + block (NOT offline sales).** Built P2.2 outbox, tested it (TEST-P22), then **Angel killed offline-mode** (tiny use case, huge fiscal cost). Instead: big "⚠ no internet — sales paused, use mobile data/hotspot" banner + honest checkout block (cart kept safe). Outbox branch deleted.
  - ~~P2.2 outbox / P2.3 sync~~ **DROPPED** — don't re-open without a named customer demand.
- [ ] **P3 — Hardware dry-run at the shop.** Thermal printer + barcode scanner on real metal — never tested live. 👥 (must be at Artemis). *Effort: half a day on-site.*
- [~] **P4 — Prod identity cleanup + SMTP.** 👥
  - [x] **SMTP wired 2026-07-01** — all 3 banco KC realms had NO email. Hybrid: `kc-sandbox`→MailHog, `borrowhood-staging` + `borrowhood`→**Resend** (`lapiazza.app` verified, smtp.resend.com:587). `testSMTPConnection` = **HTTP 204 all three**; sandbox PROVEN via MailHog. Persists across restart (IGNORE_EXISTING import, `helix_db`). Set master admin `helix_user` email = angel's Gmail (enables KC test button). ⏳ Angel confirm the 2 Resend tests hit Gmail; optional real user-flow (forgot-password) proof. Detail: memory `banco-kc-smtp-resend`.
  - [x] **helix_pass quick-patch 2026-07-01** — GitGuardian flagged the shared demo password (`helix_pass`) in the PUBLIC repo. Assessed: no cloud keys leaked, Postgres not internet-exposed; the real door was KC logins. Rotated **8 real accounts** (felix/akenel/angel/pam/ralph on `borrowhood` + `borrowhood-staging`) off `helix_pass` to Angel's strong password via `scripts/ops/set-kc-passwords.py` (getpass, refuses helix_pass). Sandbox stays open by design. Detail: memory `banco-shared-password-cleanup`.
  - [x] **Clean Banco POS realms — 3-realm rebuild DONE + HUMAN-GREEN 2026-07-02.** Banco's till is off the 365-bot `borrowhood` swamp and on a dedicated clean realm per env. (The `helix-identity-architecture` 3-realm plan; detail in `docs/IDENTITY-CONSOLIDATION-PLAN.md`.)
    - [x] **`kc-sandbox`** — already built + live (sandbox Banco runs on it).
    - [x] **`kc-staging` — built, folded, cut over, HUMAN-GREEN.** Fresh realm (21 clients + tier/app roles + `shop:artemis`); folded felix(pos-admin)/pam(pos-cashier)/ralph(pos-manager) with `+tag` emails; Resend SMTP (working key pulled from `borrowhood-staging` DB); branded wolf email theme + display "La Piazza · Banco" + i18n(en,it) + "close this window" message; `POS_REALM`→kc-staging (LP left on borrowhood-staging). **Angel proved all 3: login + self-service forgot-password → reset → login, flawless.** `helix_pass` on staging (rehearsal, like sandbox).
    - [x] **`kc-production` — built, folded, cut over, HUMAN-GREEN.** Same recipe: backup-gated (`banco_prod` + `helix_db` dumps first), fresh realm, folded felix/pam/ralph with `+tag` emails + **NO `helix_pass`** (passwords set via the reset flow — clean prod), Resend SMTP (key from `borrowhood` DB, from=noreply@lapiazza.app), branded theme (logo→`banco.lapiazza.app`) + display + i18n + message. `POS_REALM: borrowhood→kc-production` in prod compose, recreated prod only (`--no-deps`), proven (realm/JWKS/`/pos/`/health; staging + KC untouched). **Angel proved felix/pam/ralph forgot-password→reset→login on banco.lapiazza.app — clean, "just works."**
    - [ ] **Retire `borrowhood` / `borrowhood-staging`** — separate, later, gated. POS is safely OFF them now (LP_REALM/marketplace still uses `borrowhood`, so audit + quarantine the 365 bots without breaking the Square). No rush, no risk to leave parked.
  - [ ] **Infra passwords still `helix_pass`** (network-gated, not urgent): Postgres `helix_user` DB pw + KC admin pw. Careful coordinated rotation (touches every container's DATABASE_URL + compose + the DB role); `scripts/rotate-secrets.sh` exists.
  - [ ] **Hygiene:** drop `|| 'helix_pass'` default in the e2e script + move DSN pw out of tracked compose; mark the GitGuardian incident resolved.

---

## 🛡️ HARDEN — right after the blockers, before relaxing
- [x] **P5 — Offsite backup copy. DONE 2026-07-01.** 🐯 The DB dumps used to live ONLY on the box (the one hole in the "disaster-proof" table — the Fishbowl checklist's step 6 "restore from backup" had nothing to restore from if the box died). Closed it: `scripts/ops/banco_offsite_pull.py` scp's the GPG-encrypted blobs box→laptop (sha256-verified bit-identical), **then `rclone copy` → Google Drive** `ecolution-gdrive:HelixNet-DB-Backups/banco` (MD5-verified, `rclone check` clean, 0 diffs / 13 files) — the SAME personal Drive as the kdbx + DR SOP, so the DR checklist stays ONE place. **Backups now in 3 places: box + laptop + Drive.** Wired `@hourly` on the laptop crontab. Safety: copy + age-delete, never `rclone sync` (laptop wipe can't nuke the cloud copy); cloud push non-fatal if offline. Also fixed IaC drift (repo `banco_backup.sh` was stale plaintext → now matches the live encrypted box script).
  - *Open follow-ups (small):* (a) 🧍 **backup KEY into the kdbx** — offsite ciphertext is unrecoverable without `/root/.banco-backup-key` (fp `4de994a0ef02fd82`); belongs in the KeePass kdbx that's already on Drive. (b) 📄 **DR SOP is `borrowhood`-only + stale** (last tested Apr 6) — doesn't cover `banco_prod` (the DB Felix's shop runs on) or its encrypted decrypt→restore path; needs a Banco section. (c) 🟡 **DigitalOcean later** (Angel's ask) — add DO Spaces as a 2nd remote for provider-diversity (survives a Google lockout); one line in `DEFAULT_REMOTES` + a token refresh. (d) side seal: `borrowhood` dumps are **plaintext** on the box (unencrypted PII) — Banco's are encrypted; worth aligning.
- [ ] **P6 — Push alerting.** Today the daily smoke writes pull-only status files; add a push so a failure reaches you. 🐯
- [ ] **P7 — Fiscal-robustness fix.** The subtotal≤0 Z-report drift on messy mixed data — defensive fix is queued. 🐯
- [ ] **P8 — Runbook + rollback + staff SOP + invoice/contract + DPA.** The paperwork that makes it a business, not a demo. 👥

---

## ✨ POLISH BACKLOG — after go-live, only on demand
*(Most specced in [BANCO-DAY-ONE-WISHLIST.md](BANCO-DAY-ONE-WISHLIST.md). Don't build ahead of need.)*
- **✅ DONE 2026-06-28:** Feedback button → small corner 💬 icon (`17fa4ba`) · **Promo-restricted discount block** — no discounts on tobacco/alcohol, cashier+manager (`2b8aefa`, Angel: Pam discounted cigs; was role-cap-only). Both LIVE all 3 envs + regression tests.
- **✅ SHIPPED 2026-06-29 — Catalog pass + Ticket Timing tracker (both LIVE all 3 envs, `e43843f` / `b1386`):**
  - **Catalog pass** (infinite scroll / Sort / tap-to-PREVIEW) — Angel-tested green; was ALREADY on prod (merged to main before the `aae0629` build-stamp deploy → rode along), confirmed by parity + ancestry. No separate promote needed.
  - **Ticket Timing tracker** — "🩹 Healed in 2h 37m" SLA pill on the Resolution card + story header (open tickets show "⏳ Open 3h"). Pure `src/services/ticket_timing.py` (7 unit tests), timeline + resolution endpoints return a `timing` block. Promoted sandbox→staging→prod, backup-gated (`banco_prod_20260629_1434`, verified-restore 24/13/87), re-probed (HTTP 200, code present, catalog no-regression).
  - *Catalog future (Angel ideas, NOT built):* ellipsis (⋯) per-item menu (preview/edit/delete/flag) · **mass-select / mass-edit** for hundreds–thousands of items · "**preview the listing**" (La Piazza listing look) inside the edit screen. Keep it "quick + simple"; build at need.
  - *No stock filter* on purpose — zero-perpetual ([[banco-zero-perpetual-and-order-book]]).
- **Cosmetics queue (2026-06-28, in progress):** Pagination on the **buyer drill + transactions** (catalog done above; transactions needs its summary moved server-side). ← *next*.
- **Discount UX follow-up:** in the till, grey-out/hide the discount field for promo-restricted items so the cashier sees it can't be discounted BEFORE trying (server already blocks; this is the hint).
- **Tiered / quantity-break pricing (Angel idea 2026-06-28):** "buy 5 → price A, buy 10 → price B" auto in cart. A price-rules layer (product → qty thresholds → unit price). MODERATE build; MUST respect the promo-restricted guard (a volume break is still a promotion → none on tobacco/alcohol) + VAT/receipt/reconciliation. Ad-hoc discounts cover today; build only when a real shop asks.
- **Category** chart on the report + the **hierarchy/CRUD + emoji picker** (specced in `BANCO-CATEGORY-MANAGEMENT-PLAN.md`; emoji seam already shipped).
- Mobile tail: catalog card overflow on sub-375 phones (prod data); `cdn.tailwindcss.com` prod warning → proper Tailwind build (rule #9).
- Product Sales #2 customer-detail screen · #3 dashboard cards · XLSX export · **Export-to-Google-Drive (sellable feature)** · audited PII/HR export.

---

*The blockers (P1–P4) are the only things standing between Felix and a clean Monday open. Everything below them makes it sturdier; everything in Polish makes him love it. Top-down. One tier at a time.*
