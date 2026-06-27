# Banco — Go-Live Readiness Plan

*Written 2026-06-27. The question: what stands between "the sandbox demo is gorgeous"
and "Felix runs his real shop on this next Monday without us scrambling"? Sized to
ONE small shop — not enterprise SRE, but the things that can sink a small business
or the relationship if we get them wrong.*

## 📌 Backlog queued (2026-06-27, Angel's call)
- **TODAY:** ① offsite copy of the banco_prod backups (currently box-only), ② push alerting
  (Telegram/email) on a non-zero daily smoke or backup, ③ clean prod identity (deterministic
  staff provisioning — no self-provision drift — + password-reset SMTP).
- **Fiscal robustness (found 2026-06-27 e2e):** harden the daily-summary turnover-split so the
  Z-report ALWAYS reconciles to total_sales, even on odd/legacy data. Per-sale VAT is exact and
  a CLEAN day reconciles to 0 (proven), but a transaction with `subtotal≤0` (e.g. giveaway-only,
  or pre-VAT legacy rows) makes split_vat unable to prorate → turnover can drift from total_sales
  on a messy mixed pile. Defensive fix: when `subtotal≤0` fall back to total (or reconcile the
  rounding/residual into the standard bucket) so the turnover-by-rate always ties out. Pre-existing
  (INC3 aggregation), NOT this batch; surfaced now because we display the split. Test-gate + ride.
- **AFTER Felix's live demo:** send the fiscal receipt + Z-report PDFs to his Treuhänder.
- Status note: UX+fiscal batch PASSED TEST-B01 (15/15) → rode to staging (green) → prod on Angel's go.

## What we've already nailed (don't re-litigate)
- The whole order-to-cash flow works and **reconciles** (VAT split, drawers, per-cashier,
  refunds) — proven by a full two-till day simulation + reconciliation harness.
- Cafe VAT (8.1 dine / 2.6 takeaway) is **legally correct per line** — the Swiss moat.
- UX is app-grade (pills, big inputs, cards, modals, mobile no-scroll, sortable/filterable
  history, VAT-safety selected states).
- Fuzz pass: **no server crashes**; the 2 gaps it found are fixed (empty-cart, qty cap).
- A daily smoke (`scripts/banco_sim/banco_daily_smoke.py`) we can run as a regression alarm.

## The gaps, ranked by CATASTROPHE risk (the honest part)

### 🔴 The three sinkers — non-negotiable before any prod go-live
1. **Data loss.** Is `banco_prod` backed up automatically, and have we ever *restored* a
   backup? If a day of Felix's sales vanishes, that's business-ending and trust-ending.
   → Automated nightly dump + an offsite copy + ONE tested restore drill. Also: remove any
   `sandbox-reset`-style footgun from anything that can touch prod.
2. **Fiscal compliance.** We verified the VAT *math*. We have NOT had a real receipt + Z-report
   reviewed by Felix's Treuhänder. Open questions: is receipt/invoice numbering **gapless and
   immutable**? Does the receipt show everything Swiss law wants (per-line rate, VAT %, shop
   VAT-ID once registered)? Is the Z-report the day's legal record? Data retention (CH = 10y).
   → Long lead time (external person). **Start this NOW** — print one real receipt + one Z-report
   PDF and get the Treuhänder's eyes on them.
3. **Can't take a sale.** If the internet blips mid-afternoon, can Felix still sell? Today: P1
   read-offline only; the P2 offline outbox is staged, not shipped. A real shop can't freeze.
   → Finish P2 (queue sales offline, sync on reconnect) OR document a clean cash-fallback so a
   blip never stops the till.

### 🟠 Operational — needed for a smooth first week
4. **Clean prod identity.** We literally hit the seed-vs-self-provision split-brain (two `pam`
   rows) in sandbox — that's the cashier-500 class of bug. Provision Felix's real staff
   *deterministically* in the prod realm (no drift), wire password-reset via prod SMTP, set
   session timeout + a quick re-auth/PIN for a shared tablet.
5. **Hardware dry-run at Felix's shop.** Camera scan is proven on a Fairphone; the **thermal
   receipt printer**, a USB scanner, and the cash-drawer kick are unproven on his actual gear.
   This needs a physical visit — schedule it; can't be crammed.
6. **Alerting / monitoring.** If checkout starts 500-ing at 2pm, someone must know immediately.
   → Wire the daily smoke to alert on non-zero; add uptime + a checkout-error alert to a channel
   Angel watches. (Health dashboard exists; this is the "tell me when it breaks" layer.)

### 🟡 Cutover & business — the launch itself
7. **Go-live runbook + rollback.** A written checklist (clean-Monday start via closeout, catalog
   pre-load of Felix's common items, who-does-what, how to roll back). The "day-one" mechanism
   is designed; turn it into a checklist.
8. **Staff training.** A 1-page SOP / laminated quick-cards for Pam + Felix (open drawer → sell →
   close). We have the SOP toolchain.
9. **The business wrap.** The invoice to Felix (setup + retainer), a light contract, and a
   data-processing note (his customers' data = CH DPA/GDPR). This is Angel's solo-founder move —
   "send Felix an invoice" — and it shouldn't trail the tech.

## What would be OVERKILL for one shop (say no, save the energy)
- Kubernetes / multi-region / autoscaling. One container is fine.
- Heavy load testing (a single shop's Saturday is small) — a light catalog-search check suffices.
- A full CI/CD pipeline to prod — the worktree-overlay deploy is fine for one operator; just add
  the smoke as a gate.

## The phased plan
- **P0 — this week (done / doing):** ✅ fix the 2 fuzz findings, ✅ save the daily smoke. →
  schedule the smoke; ride the UX+VAT batch to **staging** (not prod) and run the smoke there too.
- **P1 — the three sinkers:** backups+restore drill · fiscal sign-off (start immediately) ·
  offline P2 (or documented fallback).
- **P2 — operational:** clean prod identity + SMTP · hardware dry-run at Felix's · alerting.
- **P3 — cutover:** runbook+rollback · catalog pre-load · staff SOP · invoice/contract.

**Critical path (longest lead, start first): fiscal sign-off + hardware dry-run** — both need
external people/physical access and will cause the scramble if left to the last minute.

## Definition of "go-live ready"
Backups tested ✓ · Treuhänder signed off on receipt + Z-report ✓ · a sale survives a network
blip ✓ · real staff log in cleanly ✓ · prints on his printer ✓ · runbook + rollback written ✓ ·
daily smoke green + alerting on ✓ · invoice sent ✓.
