# SESSION-STATE — 2026-06-28 (Hypercare day) · HANDOFF

*Single resume point after a compaction. Detail lives in memory files + the docs linked below.*

## 🟢🟢 PROD (2026-06-28): Hypercare LIVE on banco.lapiazza.app + prod tree CLEANED
- TEST-HC2 17/17 on staging → shipped to PROD. Verified backup of `banco_prod` first (`/opt/backups/banco/banco_prod-prehypercare-20260628-204141.sql.gz`, restore-tested→products=13→dropped).
- **"Fix everything" DONE**: the prod tree was an overlay-pile but PROVED to be `main` minus hypercare (zero orphaned overlays — the identity prod-fold CODE was already merged to main; only its KC realm config lives in Keycloak, untouched). Overlaid `main`→prod `src/` → `git diff origin/main` = **ZERO** → removed 5 `.bak` junk → aligned HEAD to `origin/main` (`cced8cc`, **0 changed files = pristine checkout**). `pos_notifications` auto-created in `banco_prod`. Brain smoke PASSED on prod (triaged, then test ticket deleted). Prod cron `* * * * *` cadence=**medium** (hourly, NOT war-room).
- **All 3 banco envs now on Hypercare** (sandbox+staging cadence=hypercare/1min, prod=medium/hourly). branch `feat/hypercare-triage` can be deleted; trunk = main.
- ⏳ Optional follow-up: align sandbox + staging tree HEADs to main too (they're still overlay-piles; non-prod, low stakes).

## 🟢 STAGING (2026-06-28): Hypercare MERGED to main (314cd5a) + deployed to banco-staging
- TEST-HC2 = **17/17 PASS** on sandbox → merged `feat/hypercare-triage`→`main` (FF) → surgical overlay onto `/opt/helix-banco-staging-tree` (foreign identity/HR overlays PRESERVED — verified my branch is a superset, 0 staging-only lines lost) → `helix-platform-banco-staging` restarted → `pos_notifications` table auto-created in `banco_staging`. Brain smoke PASSED on staging. Cron: `* * * * *` env=staging realm=borrowhood-staging cadence=hypercare.
- Staging URLs: app `staging-banco.lapiazza.app` (felix/pam · helix_pass · realm borrowhood-staging); test sheet `/static/TEST-hypercare-loop-v2.html`.
- **PROD (banco) UNTOUCHED** — next: Angel mobile-retest on staging → then prod (overlay onto `/opt/helix-banco-tree` + restart; backup banco_prod first).

## 🔑 RESUME
- Code word **"ON DECK"** → open `docs/BANCO-WORKLIST.md`, execute the top item.
- To continue the new build: say **"continue hypercare"** → pick up the **reporter bell** (next PoC-3 increment) on branch `feat/hypercare-triage`.
- Git: `main @ d64b50b` (prod trunk, all pushed) · `feat/hypercare-triage @ a68f3c4` (sandbox-only, pushed, **NOT merged** — secret weapon). Working tree clean.

## ✅ SHIPPED TO PROD today (banco.lapiazza.app, on `main`, signed off, byte-identical sbx/stg/prd)
- **Product Sales report** — who-bought-it cards, category drill + emoji, card→receipt, origin-gated ← Back, CSV/print, manager-gated.
- **Mobile responsive pass** — `@media(max-width:480px)` in `pos/base.html` (tablet untouched); iPhone SE clean. Audit tool: `scripts/testing/mobile-overflow-audit.js`.
- **EXACT cash cent-precision fix** + regression test (was false "Insufficient payment" on .17 totals).
- **Promo-restricted discount block** — no discounts on tobacco/alcohol (cashier+manager) + regression test.
- **Catalog** — infinite scroll + Sort (name/price/recent/stock) + tap-to-PREVIEW (read-only, Edit-inside).
- Feedback button → small corner 💬 icon. Sign-off sheet: `/static/TEST-product-sales.html` (TEST-B03, 14/15).

## 🛰️ HYPERCARE TRIAGE COCKPIT — built & proven, **SANDBOX-ONLY** (`feat/hypercare-triage`)
Spec: `docs/BANCO-HYPERCARE-TRIAGE-COCKPIT.md`. Memory: `banco-hypercare-triage-cockpit`.
- **PoC-1 brain** ✅ `src/services/feedback_triage.py` — vision lens (TRIAGE_VISION) + `run_llm` (gpt-oss:120b on Turbo via `BH_OLLAMA_KEY`) → clean ticket {title,description,type,severity,area,confidence,decipherable,questions}. Graceful fallback.
- **PoC-2 automation** ✅ `POST /api/v1/pos/feedback/triage` (in-app session, idempotent, writes dual-version to `BacklogActivity.comment`=full JSON, old/new_value=titles). **Cadence cron** `/opt/hypercare/triage_cron.py` (repo `scripts/ops/`), per-env knob `/opt/hypercare/<env>.cadence` (hypercare15/high30/medium60/low1440/off), crontab `*/5`, sandbox=hypercare. PROVEN end-to-end (seed→cron→clean).
- **PoC-3 cockpit** ✅ `/pos/hypercare` (`pos/hypercare.html` + `GET /feedback/queue`) — scorecard + queue showing RAW↔AI-CLEANED side by side + "Run AI triage now". Manager/admin gated.
- **PoC-3 reporter BELL** ✅ new `POSNotificationModel` (auto-created table) → emit on triage to `created_by` ("🛠️ We're on it — BL-X …"). `GET /pos/notifications` (own only + unread) + `POST /pos/notifications/read`. 🔔 in status bar (`base.html`) w/ unread badge + dropdown, opens→marks read, polls 45s. Guard uses `sessionStorage.pos_token` (NOT `window.token` — it's a top-level const, undefined on window). sw v13.
- **PoC-3 "my tickets" view** ✅ `/pos/my-tickets` (`my_tickets.html` + `GET /feedback/mine`) — no-jargon journey stepper (Received→Understood→Fixing→Done) + "how we understood it" + confirm-back `[✅ Yes that's it] / [✏️ Add more]` (`POST /feedback/mine/{n}/confirm|note`). Bell links here.
- **PoC-3 DONE-LOOP** ✅ cockpit "✅ Mark fixed" → `POST /feedback/{n}/done` (status=done, optional commit/SHA) → reporter "shipped" bell ("✅ Fixed — please take a look") → my-tickets "🎉 We think this is fixed!" `[✓ Looks good, close it]`(→archived `POST .../close`) / `[✗ Still not right]`(→in_progress `POST .../reopen` w/ note). PROVEN cradle-to-grave end-to-end (file→triage→bell→confirm→fix→confirm-fixed→close).

## ⏳ NEXT (PoC-3 leftovers, on the branch, sandbox)
1. **dedup** (don't make same ticket twice — AI checks open tickets before creating) · SLA scorecard (open→picked→assessed→shipped+SHA) + reporter **points**.
2. **Test samples ready**: `docs/BANCO-HYPERCARE-TEST-SAMPLES.md` (10 real ones to file as Pam/Felix). Vision key still pending (degrades gracefully).
3. **Vision key**: Angel runs the safe `read -rs` command → `BH_GOOGLE_API_KEY` into `/opt/helixnet/hetzner/uat.env` → recreate sandbox container → screenshots get read. (`scripts/rotate-secrets.sh` now lists it.)
4. **Market study** (Userback/Marker.io/BugHerd/Usersnap/Jam.dev do capture; gap = user-closes-own-loop + owned backend). Then merge decision (it's the secret weapon — Angel's go required).

## ⚠️ PATTERNS / GOTCHAS
- **Deploy** = `git -C /opt/helix-<env>-tree checkout origin/<ref> -- <files>` then `docker restart helix-platform-<env>`. Hypercare runner needs `docker cp` (scripts/ not mounted) — but the endpoint/cron is the real path.
- **Async-ORM in scripts**: deferred/large columns (e.g. `screenshot_data`) lazy-load → MissingGreenlet. SELECT COLUMNS, not the entity; the in-app endpoint is the clean home.
- **Secret weapon**: hypercare stays sandbox-only; DO NOT merge to main/prod without Angel's explicit go.
- Money = cent-quantize. Inventory = zero-perpetual (NO stock gates/alerts). Reorder = "Order Book" not MRP. Promo-restricted classes = no discounts.
- Parked (other terminal): identity-terminal collision — its 3 commits not landed; **prod fold verified safe** (felix=admin, pam=cashier).

## 📌 SELLING > POLISH (Angel's own plan)
Software is at the "good enough to run a real shop" bar. Capture polish in the backlog (the 💬 button); **the one move is to invoice Felix**. Hypercare = the leverage tool + a sellable steward capability.
