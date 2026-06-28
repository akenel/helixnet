# SESSION-STATE — 2026-06-28 (Hypercare day) · HANDOFF

*Single resume point after a compaction. Detail lives in memory files + the docs linked below.*

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

## ⏳ NEXT (PoC-3 increments, on the branch, sandbox)
1. **Reporter BELL notifications** (in-app, by the name) ← do next.
2. Confirm-back loop ("is this what you meant?") · **dedup** (don't make same ticket twice) · SLA scorecard + reporter **points** · read-only user "my tickets / team" view + changelog (off the 📊 button, role-gated).
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
