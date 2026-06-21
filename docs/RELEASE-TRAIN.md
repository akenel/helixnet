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

`🟢 IDLE` — no train running. (Last: Banco stood up on prod via clean container, 2026-06-21 ~13:36 — Tigs.)

## Boarding (awaiting the next prod train)

| Feature | Commits (main) | Staging | Prod |
|---|---|---|---|
| **BL-84** Real payment-method breakdown on the report + bank transfer (Felix live feedback) | `3f19dfc` | **green — on staging-banco @ 3f19dfc; daily-summary shows all buckets (visa 24.8k + twint 915 + cash 3.8k were hidden before); enum `BANK_TRANSFER` added to shared DB** | **STAGED — awaiting Angel visual PASS** |
| **BL-83** Name the cashier on the transactions report + drop duplicate # line (Felix live feedback) | `2bd019d` | **green — on staging-banco @ 2bd019d; 129 rows now show Felix (116) / Pam (13), no more generic "Cashier"** | **STAGED — awaiting Angel visual PASS** |
| **BL-85** Status bar fits mobile portrait — 📊 stays reachable (Felix live feedback) | `f2f58f2` | **green — on staging-banco @ f2f58f2; sm-hide + @media(≤480px) verified in served HTML** | **STAGED — awaiting Angel visual PASS** |

> **🚂 Train loaded @ `f2f58f2` (BL-84 + BL-83 + BL-85), awaiting Angel's GO.** All three
> verified on staging-banco; prod deploy held at the staging-before-prod gate until Angel
> signs off. On GO: reset `/opt/helix-banco-tree` → `origin/main`, restart `helix-platform-banco`,
> smoke 8098. Bottega `#140` tree untouched.
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

- **2026-06-21 — Banco stand-up on prod (first Banco-on-prod).** 9 features (feedback
  attachments, cash-shift drawers, status-bar stamp, Shop Pulse, /health/dashboard, CRM
  Phase 0, no-cache headers, member directory, release-gate suite) went live on
  `banco.lapiazza.app` via a NEW clean container at `8303204` — NOT by reconciling the
  divergent Bottega tree. Bottega untouched. Driver: Tigs (Angel: PATH 1).
