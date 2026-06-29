# SESSION-STATE — 2026-06-29 (BL-012 timezone ship + tickets-as-KB) · HANDOFF

*Single resume point after a compaction. Detail lives in memory files + the docs linked below.*

## 🟢 WHERE WE ARE — all 3 Banco envs uniform on `main @ 1030ecb` / build `b1397`, clean
- `python3 scripts/ops/env-parity.py` → Banco trio (sandbox/staging/prod) all on `1030ecb`, CLEAN. (bottega-* DRIFT is unrelated "context".)
- Prod = `banco.lapiazza.app` · staging = `staging-banco.lapiazza.app` · sandbox = `sandbox-banco.lapiazza.app`.
- POS realms: sandbox `kc-sandbox` · staging `borrowhood-staging` · prod `borrowhood`. Login felix/helix_pass.
- ⚠️ Two FOREIGN files uncommitted in the tree (NOT mine, another session): `docs/business/BANCO-WHY-NOT-THE-BIG-GUYS.md` (modified) + `docs/business/BANCO-INVENTION-DISCLOSURE.md` (untracked). Left untouched — don't sweep them into a commit.

## ✅ SHIPPED TO PROD THIS SESSION
1. **BL-012 — status bar shows ONE timezone (device-local), labeled** (`1030ecb` / `b1397`). Felix asked "CEST local or UTC for the SHA time?" — investigation FLIPPED the premise: the build stamp was NOT UTC, it rendered the *committer's* authored wall-clock (`%cI` hour/min) verbatim, unlabeled. Labeling it "UTC" would've been wrong half the time. Fix (Felix-simple = one zone, his): live clock + build stamp both render device-local, labeled once with the short tz name (CEST, auto-flips CET↔CEST). Build stamp carries offset-bearing ISO (`build_date_iso`, set on **BOTH** Jinja2Templates instances — main.py + pos_router.py) and is **re-based client-side** (a UTC device shows 16:45 UTC, a Rome device 18:45 CEST for the same build — converts, not just relabels). `sw.js` CACHE_NAME v23→**v24**. Code-only, no migration. Gated sandbox→staging→backup-gate(RESTORE VERIFIED 24/13/87)→prod, re-probed (prod first probe 502 = restart-race → re-probed → 200/SW-v24/healthy; prove-don't-assume earned its keep again).

## 🎫 THE HYPERCARE BOARD (prod cockpit — feedback tickets BL-009..BL-014)
*Drive the board over the API at `BASE=https://banco.lapiazza.app/api/v1/pos` (NOT `/pos/*` — that's HTML pages). Auth: `POST https://lapiazza.app/realms/borrowhood/protocol/openid-connect/token` client_id `helix_pos_web`, felix/helix_pass. felix has `pos-admin`. Endpoints: `GET /feedback/queue?limit=50`, `POST /feedback` (file), `POST /feedback/{n}/done` (mark fixed→notifies reporter), `POST /feedback/{n}/reject`.*
- **BL-014 · done** — "Offline operation — by design, NO offline sales" — the retroactive KB record (offline outbox built+tested+DROPPED; warning banner shipped; answer-if-it-comes-up = "use mobile data / hotspot"). In felix's 🔔 to confirm-close. *(This is the corrected "BL-027" — BL-027 was a PHANTOM number in old notes; it never existed on prod. Real feedback tickets are BL-009..014 only.)*
- **BL-013 · pending (triaged, conf 94%)** — "Remove redundant System OK text + dot-icon status." 🍎 RIPENING ON THE BOARD ON PURPOSE — Angel's call: build it when ripe, not yet. **Spec (already designed, ready to build):** drop "System OK" (the green dot already says OK); two states only — green-solid-silent = OK, **red-pulsing + word "NOK"** = not-OK (presence of a word = the alarm); `flex` + fixed `gap` to kill the whitespace jitter; **tap-and-hold the dot → 1s "NOK TEST" flash** (test the smoke alarm); optional: de-dup the now-doubled tz label (CEST shows on both clock + stamp). Lives in `src/templates/pos/base.html` status bar.
- **BL-012 · done** — timezone (shipped above). In felix's 🔔 to confirm-close.
- **BL-011 / 010 / 009 · archived** — older, already run.

## ☑️ DO TASKS (after compaction, in priority order)
1. **Angel's two bell taps** (his, ~30s): confirm-close **BL-012** + **BL-014** on `my-tickets`. (Not mine to do — reporter closes.)
2. **BL-013** — build it WHEN ANGEL SAYS RIPE (don't pre-empt). Then the loop: sandbox → his Fairphone check → staging → backup-gate → prod. Spec above. Code-only, no migration.
3. **GO-LIVE BLOCKERS still standing** (real gates to Felix running his shop):
   - **P1 — Fiscal Treuhänder sign-off** 🧍 *long-lead, start the clock.* Cover note READY: `docs/business/banco-fiscal/COVER-NOTE-treuhaender.md` + 2 sample PDFs. Needs Angel's Treuhänder name+email → I can prep a Gmail DRAFT (review-before-send).
   - **P3 — Hardware dry-run** (thermal printer + scanner on real metal) 👥
   - **P4 — Prod identity cleanup + SMTP** 👥
4. **BL-009 change-control + ROLLOUT** (`docs/BANCO-CHANGE-CONTROL.md`, designed not built) — the maturity layer for when Felix is live + busy. Build P1 first (Cockpit "needs your call" lane).
5. **Backlog bits:** "1B" svc-hypercare acct + rotate felix prod demo pw (`helix_pass`) · vision-key on all envs · `deploy-banco.py rollback` verb · per-ticket deploy-stamp ("live in prod 15:10") · tickets-as-KB query layer (see memory — NOT yet, ~100-200 closed tickets first).

## 💡 BIG INSIGHT THIS SESSION — tickets ARE the knowledge base
Closed tickets don't vanish, they FILE. The board splits **working memory (≤500 open, Felix-simple)** from **long-term memory (unbounded closed corpus)** — small desk, vast library. The corpus is causal (problem→decision→fix→why→build-SHA), so an LLM can mine it: ask-the-history (RAG), AI-generated roadmap from real demand, self-documenting onboarding for stewards, cross-shop pre-emptive answers (the multitenant moat), ISO-9001/audit trail for free. The antidote to the seal lesson (knowledge that doesn't retire). HONEST CATCH: a KB only stays an asset if it stays TRUE+FINDABLE — enforce "no close without a captured why" (ideally in the rails), recency-weight (closed ≠ eternal — see superseded ADRs), and retrieval is real eng (build at ~100-200 closed, NOT now at 14). See [[banco-tickets-as-knowledge-base]].

## 🔑 RESUME — code word "ON DECK" → open `docs/BANCO-WORKLIST.md`, execute the top item.

## 🧠 MEMORY FILES (durable, load each session)
- `banco-tickets-as-knowledge-base` (NEW — the KB insight + honest catches + when-to-build)
- `banco-deploy-rails-and-prove-discipline` (deploy toolkit + prove-don't-assume + BL-012 ship + board API how-to)
- `banco-offline-and-pwa-plan` (OFFLINE DROPPED decision = BL-014) · `banco-hypercare-v2-shipped` · `banco-day-one-wishlist`
