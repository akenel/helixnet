# 🚂 Release Train — staging → prod promotion ledger

**Why this file exists:** multiple terminals/sessions work on `main` at once, and prod
(`/opt/helixnet`, serves bottega.lapiazza.app) is a divergent `#140` tree many features
behind. We need ONE shared, durable signal for "validated on staging, cleared for prod"
so sessions don't fall over each other or push half-baked work to a live box.

## How it works

1. **The signal = a row marked `APPROVED`.** When Angel signs a feature off on staging,
   flip its **Prod** cell to `APPROVED — Angel, YYYY-MM-DD`. It's in git, so every
   terminal sees it on `git pull`. `STAGED` = on staging, not yet signed off. `PENDING`
   = not on staging yet.
2. **Prod ships as a TRAIN, not per-feature.** One deploy event promotes ALL `APPROVED`
   rows together. (Often forced anyway: features entangle in shared files — e.g. the
   feedback handler won't even import in prod without the cash-shift + CRM code.)
3. **One driver at a time.** Before running a train, set the **Status** line below to
   `🚦 DEPLOYING — <who/session> — <time>`. Others wait until it's back to `🟢 IDLE`.
4. **A train also RECONCILES the prod tree.** Prod is behind by design; the train brings
   prod's Banco files up to the agreed `main` SHA, deploys, smoke-tests, then marks the
   shipped rows `SHIPPED — <sha> — YYYY-MM-DD`.

## Status

`🟢 IDLE` — no train running. (Last: BL-86 reaper + hide-cancelled shipped to banco.lapiazza.app @ `3c29154`, 2026-06-21 — Tigs, Angel GO.)

## Boarding (awaiting the next prod train)

| Feature | Commit(s) | Test status | Prod |
|---|---|---|---|
| BL-87 camera barcode scan + lazy capture (`/pos/scan`) | `275e0a9`, `755ea99` (+ spec `90ac996`) | Camera PASSED on Fairphone (Angel). Logic fixes after device test: lazy-capture **quantity** field + **sellable stock** (was stock 1 → oversell-blocked on 2nd sale; persistence itself worked). Stale `LZ-%` test items bumped to 9999 on staging. POS gate 99 pass (7 = pre-existing flake). | **STAGED — staging-banco.lapiazza.app @ 755ea99, 2026-06-21. Awaiting Angel re-test PASS.** |

> _(BL-84 / BL-83 / BL-85 — Felix's three live feedbacks — and BL-86 (reaper + hide-cancelled)
> all **SHIPPED 2026-06-21**, see history below.)_
| Banco feedback: file + camera attachments | `0013263` (backend) + `4aba2da` | green (7/7 attach+screenshot, dog-fooded: img + 2 PDFs) | **SHIPPED — banco.lapiazza.app @ 8303204, 2026-06-21** |
| Banco cash shift — per-cashier drawer (incr 1-3) | `2d9df70`,`94a9c75`,`cc7b886` | green, "per-cashier isolation proven" | **SHIPPED — banco.lapiazza.app @ 8303204, 2026-06-21** |
| Status bar: real version + git SHA stamp | `af62709` | green — shows `v3.3.0 (af62709)`, env `uat` | **SHIPPED — banco.lapiazza.app @ 8303204, 2026-06-21** |
| Shop Pulse card (live 📊: sales/members/stock/drawers) | `af62709` | green — `GET /pos/system/pulse` 200, real stats | **SHIPPED — banco.lapiazza.app @ 8303204, 2026-06-21** |
| `/health/dashboard` diagnostics page (health + system + browser/screen specs) | `04ae273` | green — HTTP 200, all cards render, env UAT | **SHIPPED — banco.lapiazza.app @ 8303204, 2026-06-21** |
| Banco CRM Phase 0 (FK fix + on-sale attach/earn/re-tier/enroll) | `a6ef751`,`0013263`,`94a4619`,`9057c1d`,`675c6de`,`825a96e` | green — Angel signed off on staging | **SHIPPED — banco.lapiazza.app @ 8303204, 2026-06-21** |
| No-cache headers on server-rendered HTML (kills the stale-page ghost) | `a381563` | green — staging sends `no-cache` on /pos pages (verified) | **SHIPPED — banco.lapiazza.app @ 8303204, 2026-06-21** |
| Member directory + multi-match picker ("several Larrys") | `d76b751` | green — diagnostics page + members list confirmed on staging | **SHIPPED — banco.lapiazza.app @ 8303204, 2026-06-21** |
| Release-gate story suite + refund returns goods to shelf | `b76a6ee` | green — 13 gate tests + full refund restores stock | **SHIPPED — banco.lapiazza.app @ 8303204, 2026-06-21** |

## ✅ Banco IS live on prod (as of 2026-06-21)

`banco.lapiazza.app` now serves the **clean `origin/main` (8303204)** POS from its OWN
container `helix-platform-banco` (worktree `/opt/helix-banco-tree`, port 127.0.0.1:8098,
compose `hetzner/docker-compose.banco-prod.yml`). Caddy `banco.lapiazza.app` → that
container. Cashier login (felix, kc-pos-realm-dev) + authed Shop Pulse verified live.

**The divergent Bottega `helix-platform` (#140) was LEFT UNTOUCHED** — `bottega.lapiazza.app`
still serves it; the 1,204-line uncommitted divergence is backed up at
`/root/banco-prod-divergence-20260621/`. #140 reconciliation remains a separate task.
Note: the **prod Caddyfile is itself divergent** (has banco/staging-banco blocks not in
git) — its banco block now points to `helix-platform-banco`; backup `/root/Caddyfile.bak-20260621-133619`.

## Shipped (history)

- **2026-06-21 — BL-86 empty-cart reaper + hide-cancelled (@ `3c29154`).** Cancels stale
  `OPEN` carts that are zero-value + empty + >12h old (CANCELLED, never deleted; hourly
  background loop + `POST /maintenance/reap-empty-carts` for mgr/admin). Cancelled carts are
  hidden from the default transactions view (still reachable via `status_filter=cancelled`).
  Staging proof: reaped 11 real 06-20 carts; prod redeploy found them already cancelled
  (idempotent on the shared DB). Driver: Tigs (Angel: GO).
- **2026-06-21 — Felix's 3 live feedbacks (one train, @ `21742df`).** BL-84 (real
  payment-method breakdown on the report + new `BANK_TRANSFER` type — fixed ~CHF 25k of
  visa/twint that rendered as zero), BL-83 (cashier names on the transactions report —
  129 rows show Felix/Pam, no more generic "Cashier"; dropped the duplicate # line), BL-85
  (status bar fits mobile portrait so the 📊 stays reachable). Staged + Angel-PASSED on
  staging-banco, then shipped together via the clean `helix-platform-banco` container
  (worktree reset to origin/main + restart). Smoke green on banco.lapiazza.app. Bottega
  `#140` untouched. Driver: Tigs (Angel: GO).
- **2026-06-21 — Banco stand-up on prod (first Banco-on-prod).** 9 features (feedback
  attachments, cash-shift drawers, status-bar stamp, Shop Pulse, /health/dashboard, CRM
  Phase 0, no-cache headers, member directory, release-gate suite) went live on
  `banco.lapiazza.app` via a NEW clean container at `8303204` — NOT by reconciling the
  divergent Bottega tree. Bottega untouched. Driver: Tigs (Angel: PATH 1).
