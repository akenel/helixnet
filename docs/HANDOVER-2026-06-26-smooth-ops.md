# Handover — "smooth-ops" session, 2026-06-26 (Tigs → next side)

Read this first, then `docs/RELEASE-TRAIN.md` (state) + the memory index. Box = Hetzner
`46.62.138.218`. Everything below is **deployed as worktree file-overlays, NOT pushed** —
see the Durability Gap.

---

## 1. What shipped this session (4 threads)

**A. Postgres health investigation → "DEGRADED" explained.**
The POS health page showed DEGRADED. Cause was **Celery workers (none) graded as
critical**, NOT Postgres. Postgres is fine/tiny. Fixed grading (see B). Also found +
fixed Keycloak bloat: `event_entity` **835 MB → 17 MB** (VACUUM FULL; it was ~98% dead
pages from bot LOGIN/REGISTER errors). Set **30-day event expiration on all 13 realms**.
`helix_db` is now ~53 MB. Banco DBs are properly isolated (banco_prod/staging/sandbox).

**B. Universal System Info view + honest health grading** — `main` commit `f5feade`.
- Only CRITICAL deps (PostgreSQL, Keycloak) drive DEGRADED/503; Celery/Redis/RabbitMQ/
  MinIO/render-worker/LibreTranslate are reported but never flip overall health.
- New `GET /health/system` rich JSON (build, env, wiring, storage, uptime, dependency
  grid w/ latency) + short aliases `/system` + `/diagnostics`. Dashboard = env-colour
  theming, Wiring + Storage cards, real commit+date (2-line `build-sha.txt`), 15s refresh.
- **Live as overlay on all 4 active worktrees**; prod `/health/system` verified OK.

**C. Sandbox env mislabel fix** — `main` commit `4de60b9`.
`helix-platform-sandbox` was `HX_ENVIRONMENT=uat` (inherited from shared uat.env) → System
Info badged it UAT not SANDBOX. Added `HX_ENVIRONMENT: sandbox` override in
`hetzner/docker-compose.banco-sandbox.yml`; recreated the container. Other envs were
already correct (staging-banco=staging, banco=production).

**D. Banco POS → PWA + offline (the main build)** — branch `feat/banco-offline-pwa`.
Angel chose: **full never-down (P0→P2), phone-first, 5 nav tabs**. Done so far:
- `d70700a` **P0** — installable PWA shell: manifest + service worker (`/pos/sw.js`,
  scope `/pos`) + wolf icons; **vendored CDN deps locally** (Tailwind/Alpine/html2canvas
  in `src/static/vendor/` — offline + fixes dev-only-CDN). Inter font still CDN.
- `f06b782` **P0.5** — native app-shell: fixed frame (top bar / scrolling content /
  **bottom tab nav**: Scan·Cart·Catalog·Customers·My Day), safe-areas, killed web-isms,
  pre-auth hides chrome, live cart badge.
- `5fe991e` **SW self-update** — cache `v1→v2` + auto-reload on new SW (skips if cart has
  items) → fixes the "had to refresh / clunky" stale-cache problem Angel hit.

Plan doc: `docs/BANCO-OFFLINE-AND-PWA-PLAN.md`. **P1 (offline catalog) and P2 (sales
outbox) are NOT built.** P2 is gated on a Treuhänder nod (provisional-receipt approach).

---

## 2. Deploy state per environment (ALL overlays, not tracked SHAs)

| Env / host | System Info | PWA UI | Notes |
|---|---|---|---|
| **banco** `banco.lapiazza.app` (prod) | ✅ overlay on `3547efa` | ❌ | PWA gated off prod |
| **staging-banco** `staging-banco.lapiazza.app` | ✅ | ✅ P0+P0.5+SW-fix | Angel's test box |
| **sandbox-banco** `sandbox-banco.lapiazza.app` | ✅ | ✅ (added this session) | clean/empty demo box |
| **bottega** `helix-platform` (`/opt/helixnet`) | ❌ (reverted) | ❌ | **legacy pinned — do NOT deploy current main here** |

Active worktrees: `/opt/helix-{sandbox,staging,banco,banco-staging}-tree`. Deploy pattern
= `scp` file(s) into the tree + `docker restart <container>`. Verify via
`docker exec <c> python3 -c "import urllib.request; ...(/health/healthz or /pos/scan)"`.

---

## 3. ⚠️ Durability Gap (the #1 thing to resolve)

**Nothing is pushed. The box runs uncommitted file-overlays.** If any worktree is reset
to a clean checkout, the overlays are lost. The code IS committed locally (main + feat
branch) but `origin` doesn't have it, so the box can't `git pull` it.

To make durable: **push** `main` (System Info + ledger + sandbox-label) and the feat
branch, then advance the relevant worktrees to the pushed SHAs. NOTE advancing the
**banco-prod** worktree past `3547efa` would also carry the realm split + AI survey +
self-set-password (see §4) — so prod stays overlay-only until its own deliberate train.

---

## 4. ⚠️ Parallel work on main (another session)

`main` advanced with **identity/realm Phase-2** commits NOT from this session:
`690bb2d`, `3b7bba6`, `5f9b0c9` (build_unified_realm.py engine), `47b5755`, `c4c108b`,
`59f20b7`, plus earlier `f11b1c9`/`12fcf56`/realm-split `b9c9eca`+`a69ce61`. The
**kc-sandbox realm is LIVE on the box** per those commits. Don't clobber that lane. The
**Banco POS realm split Phase 2 → prod** is gated on Angel's explicit go + infra
(create `kc-pos-realm-prd` + Resend + seed Felix).

---

## 5. Immediate next steps

1. **Angel re-tests PWA on a CLEAN install** (he had a stale v1 install): delete the home-
   screen icon → clear site data for the box in the phone browser → reinstall from
   `https://staging-banco.lapiazza.app/pos` (or sandbox-banco). Future updates self-apply now.
2. He said staging mobile "generally looks good" but felt **clunky** (mostly the stale
   cache, now fixed). Get specifics on re-test → targeted polish.
3. **Known not-done:** page-to-page **flash on tab taps** (still full page loads — smooth
   in-app nav is a bigger lift). And **bottom-cutoff** check (content hidden behind nav).
4. **P1 — offline catalog** (IndexedDB read-cache: scan/search/price offline). Then
   **P2 — sales outbox** (atomic create-sale endpoint + client-UUID + sync) — Treuhänder gate.
5. **Push + durability** (§3) when Angel's ready.

---

## 6. Gotchas / rules learned

- **Never blanket-deploy current `main` to `/opt/helixnet`** (legacy bottega prod, no
  `__version__` → crash-loop). Revert tracked files one-at-a-time; `git checkout` aborts
  the whole command if ANY pathspec is untracked. (memory: deploy-skip-legacy-helixnet-tree)
- **Bump `CACHE_NAME` in `src/static/pos/sw.js`** on any shell/asset change, or installed
  PWAs serve stale.
- **SW scope:** `/pos/sw.js` served with header `Service-Worker-Allowed: /pos` to cover all POS pages.
- zsh **doesn't word-split unquoted vars** — use arrays in loops (bit me on scp loops).
- Keep memory current: `banco-offline-and-pwa-plan`, `deploy-skip-legacy-helixnet-tree` written this session.
