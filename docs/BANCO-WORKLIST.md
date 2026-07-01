# Banco Go-Live Worklist — THE ordered list

> 🔑 **Code word "ON DECK"** → you're reading the right file. State the top items and start executing the first actionable one. No re-planning, no re-asking.

*Open this, work top-down, finish one tier before opening the next. Don't fan out across five things. 2026-06-28.*

*Owners: 🧍 = Angel's hands needed (physical / decision / external call) · 🐯 = Tigs can do it · 👥 = both, together.*

*Detail lives in: [BANCO-GO-LIVE-READINESS.md](BANCO-GO-LIVE-READINESS.md) (analysis) · [BANCO-DAY-ONE-WISHLIST.md](BANCO-DAY-ONE-WISHLIST.md) (polish backlog).*

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
  - [ ] **Prod identity cleanup** — the pam split-brain in the prod realm. Still pending. *Effort: one focused session.*

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
