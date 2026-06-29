# SESSION-STATE — 2026-06-29 (Atomic-checkout + offline-decision day) · HANDOFF

*Single resume point after a compaction. Detail lives in memory files + the docs linked below.*

## 🟢 WHERE WE ARE — all 3 Banco envs uniform on `main @ c54d5cf` / build `b1394`, clean
- `scripts/ops/env-parity.py --local` → VERDICT: Banco trio in the SAME picture (sandbox/staging/prod all `c54d5cf`). local = origin/main = `c54d5cf`. Working tree clean.
- Prod = `banco.lapiazza.app` · staging = `staging-banco.lapiazza.app` · sandbox = `sandbox-banco.lapiazza.app`.
- POS realms: sandbox `kc-sandbox` · staging `borrowhood-staging` · prod `borrowhood`. Login felix/helix_pass.

## ✅ SHIPPED TO PROD TODAY (the arc, in order)
1. **Ticket Timing tracker** — "🩹 Healed in 2h 37m" SLA pill on resolved tickets (`src/services/ticket_timing.py`, 7 unit tests). Human-proven on a real prod ticket.
2. **Build stamp B** confirmed (`bNNNN` = git commit count + sha + dd/mm HH:MM) — from the prior session, now riding every deploy via `deploy-banco.py`.
3. **P2.1 — atomic, idempotent `POST /pos/sales`** (THE keystone): whole cart + payment in ONE call, idempotent on a `client_uuid`. Till switched to it. Migration-first (`client_uuid` col + unique index via `database._ADDITIVE_COLUMNS` per-env rail + alembic `009`), per-env `information_schema` proof on all 3. Parity test proves atomic == legacy money. Human-green **TEST-P21 11/11** (signed PDF in `docs/testing/banco/Test-Scripts/`). Legacy 3-step endpoints kept as a safety net.
4. **Offline = honest banner + block (NOT offline sales)** — built P2.2 outbox, tested it (TEST-P22), **Angel killed offline-mode** (tiny use case, huge fiscal cost). Shipped instead: big "⚠ no internet — sales paused, use mobile data/hotspot" top banner + honest checkout messages, cart kept safe. Outbox branch DELETED. Closes **BL-027**.
5. **Graceful checkout on a server blip** (deploy-safety): a restart/5xx/dropped-conn mid-checkout no longer dumps a raw error — tells a BLIP (keep cart+key, "tap again, can't ring twice", idempotent-safe) from a 4xx REJECTION (show real reason). `base.html` API attaches `err.status`; `scan.js` clearCart drops `pos_sale_uuid` so a committed-but-blipped sale can't shadow the next (real money-edge closed).

All gated sandbox→staging→prod, backup-gated (verified-restore), re-probed (prove-don't-assume). No migration on 3–5.

## 📐 DESIGNED, NOT BUILT (banked)
- **BL-009 change-control + THE ROLLOUT** (`docs/BANCO-CHANGE-CONTROL.md`): 10–20s deploys → courtesy NOTICE not a window. Felix picks now-with-~2min-countdown / schedule-tonight / next-interval-grid (severity 1–10 recommends). Banner+countdown to all online (shows incoming build/SHA). Lifecycle 🔔 scheduled→rolling→done("you're on bXXXX", reporter ticket CLOSES = last mile of Hypercare loop)→stale-session nudge. Principles: owner sets time, attended>unattended for non-critical, migration-flagged+windowed, Felix-simple-not-SAP, scales to multitenant forced-patch.

## 🔑 RESUME — code word "ON DECK" → open `docs/BANCO-WORKLIST.md`, execute the top item.

## ☑️ DO TASKS (after compaction, in priority order)
1. **Close BL-027** (Angel is reporter → close it on `my-tickets` with: "by design, no offline sales; shipped a clear warning instead"). Or ask Tigs to mark it fixed so it pops up to confirm. *(2-min loose end.)*
2. **GO-LIVE BLOCKERS still standing** (the real gates to Felix running his shop — from the worklist):
   - **P1 — Fiscal Treuhänder sign-off** 🧍 *long-lead, start the clock.* Cover note is READY to send: `docs/business/banco-fiscal/COVER-NOTE-treuhaender.md` + the 2 sample PDFs. Just needs Angel to send it. (This ALSO unblocks any future offline-receipt question.)
   - **P3 — Hardware dry-run** at the shop (thermal printer + scanner on real metal) 👥
   - **P4 — Prod identity cleanup + SMTP** 👥
3. **BL-009 change-control** — when ready to build: start P1 (Cockpit "needs your call" lane + approve + auto-checklist), THEN the ROLLOUT scheduling/notify layer. Not urgent; it's the maturity layer for when Felix is live + busy.
4. **Backlog bits:** per-ticket deploy-stamp ("live in prod 15:10" timing) · always-allow-reporter-comment · vision-key on all envs · `deploy-banco.py rollback` verb · "1B" svc-hypercare acct + rotate felix's prod demo password (`helix_pass`).

## 🧠 MEMORY FILES (durable, load each session)
- `banco-deploy-rails-and-prove-discipline` (deploy toolkit + prove-don't-assume + today's ships + BL-009 rollout)
- `banco-offline-and-pwa-plan` (OFFLINE SALES DROPPED decision + P0/P1/P2.1 status)
- `banco-hypercare-v2-shipped` · `banco-day-one-wishlist` · `banco-go-live readiness` (worklist)
