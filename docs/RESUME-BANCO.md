# PASTE-IN — Resume Banco (head-shop ERP) · for the 11 AM session

**Tigs: read these four docs first, in this order, then the NEXT list below.**
- `docs/HEADSHOP-ERP-GRAND-PLAN.md` — the vision (Swiss-native vertical ERP; phased roadmap; market cherry-picks; the moat = domain SOPs + stewardship + founder fit).
- `docs/HEADSHOP-ERP-EXECUTION-AND-CUTOVER.md` — build order + cutover playbook (ride Felix's **March move as the genesis inventory count**; reversible by design; Tamar webshop untouched).
- `docs/HELIXNET-ESTATE-MAP.md` — full monorepo inventory + naming convention (products get subdomains, modules don't; the buried `farm/batch/lab_test/trace` seed-to-sale GOLD).
- `docs/BANCO-LAPIAZZA-RUNBOOK.md` — deploy the subdomain (Caddy block, KC redirect URIs, staging-first, landmines, rollback).

## What Banco IS (one paragraph)
**Banco** (with a **C** — "the counter," NOT "the bank"; same family as La Piazza/Bottega) is a **Swiss-native
vertical ERP for head shops** — POS + multi-location inventory + light grow/lab production + vending +
white-label. It runs **on the HelixNet engine** (HelixNet is never renamed; it's infra). **Felix's Artemis
shop is customer #1.** Business model: **free/open-source software + paid stewardship + the SOP/role library**
(Angel does the genesis count, trains the trainers; "the joy only survives while the stewardship holds").
URL: **`banco.lapiazza.app` → existing helix-platform → `/pos`** (NO `/pos`→`/banco` rename; identity without
the refactor). Don't fork/rebuild — **grow in place**.

## Shipped tonight (committed on local `main`, NOT pushed, NOT deployed)
- `1289877` — Banana CSV export (`/reports/daily-summary.csv`) + stock-deduction-on-checkout.
- `72157dc` — printable daily **Z-report** on the closeout screen + the execution/cutover plan.
- `90c8aaa` — **shop-setup wizard BRAIN** (`src/services/shop_setup_service.py`, pure + tested:
  Artemis → CHF/8.1/de, ready to go live; `EUROPEAN_DEFAULTS` per country; Cashier/Manager/Owner
  reference roles) + the estate map + the runbook.

## Phase-1 till status
✅ Banana CSV · ✅ stock deduction · ✅ print Z-report. ☐ create-product-on-the-fly (wire `scan.html` catalog
form) · ☐ **unified feedback button** (port La Piazza/BorrowHood's GOOD one with attachments + diagnostic
snapshot, add a 🎤 mic — it's the standard; Bottega's is the bad one).

## NEXT (prioritized, for 11 AM — all fresh-hands bricks)
1. **Finish the wizard** (brain is done):
   a. add `currency` + `default_language` columns to `store_settings` (a **migration** — do rested).
   b. `POST /api/v1/pos/setup` endpoint → calls `shop_setup_service.build_shop_preferences()` → seeds `store_settings`.
   c. the wizard **form page** (guided; country pre-fills currency/VAT/language).
   d. **realm provisioning** via `scripts/lp_create_realm.py` (fresh realm per shop).
2. **Deploy tonight's bricks**: `git push origin main`, then staging→prod per the runbook (NEVER `git pull` in /opt/helixnet).
3. **`banco.lapiazza.app`**: Angel adds the A record → run `BANCO-LAPIAZZA-RUNBOOK.md` (Caddy block + KC redirect URIs in the **artemis** realm, staging first).

## 3 Felix-inputs (Angel to get — not code)
1. Banana account codes — *or just use the print Z-report* (input #1 is effectively solved).
2. A **sample Tamar product export** of the ~10k items (de-risk the March cutover — get it early).
3. **SOPs** — Angel **proxies for Felix** for now; ask the real Felix only when stuck.

## Decisions locked (don't relitigate)
- Name **Banco** (C, not K) = the counter. `banco.lapiazza.app` subdomain, no path rename. HelixNet = the engine (never renamed).
- **Don't fork/rebuild** — grow in helixnet. Products get subdomains; internal modules (backlog/qa/hr/admin/kb) stay at paths.
- Reference role model: **Cashier / Manager / Owner**, one realm per shop, owner can span shops, manager signs off refunds/voids/big discounts.
- **Sandbox/30-day-trial = Phase 4** (the wizard + a "try free" button later — one engine, two stages). Do NOT build trial infra before shop #1 is live.
- Multi-tenant framework only at ~3 shops; multi-currency = per-shop currency (no FX); hostnames in config (never hardcode).

## Context (why this matters)
Tonight was a **recovery**: Angel went from "dead end, maybe pivot careers" → Banco. Head shops = where his
**passion** (loves them, ideal customer), **mastery** (40 yrs SAP/ERP/MRP + Abacus inventory/production
control), **friend** (Felix), and a **real market** converge. The finisher's curse is cured — inventory +
stewardship never "finish." **Felix:** 25-yr head-shop professor, Lucerne (oldest there, 2nd-oldest in CH),
Curaprox connections, multi-site (shop **moves in March** = genesis-count moment; Leadtower lab/grow; Seedle
office+vending ~1k CHF/machine/mo). ~10k products on **Tamar Trade** (artemisluzern.ch), no integration, all
manual; **100–200k of unlogged inventory**. Staff: Pam (cashier), Ralph (manager), Felix (owner), Lila off sick.

*Watch Angel's overwork — this was a marathon all-nighter. Endorse stopping when green.*
