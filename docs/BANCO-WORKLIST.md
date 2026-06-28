# Banco Go-Live Worklist — THE ordered list

> 🔑 **Code word "ON DECK"** → you're reading the right file. State the top items and start executing the first actionable one. No re-planning, no re-asking.

*Open this, work top-down, finish one tier before opening the next. Don't fan out across five things. 2026-06-28.*

*Owners: 🧍 = Angel's hands needed (physical / decision / external call) · 🐯 = Tigs can do it · 👥 = both, together.*

*Detail lives in: [BANCO-GO-LIVE-READINESS.md](BANCO-GO-LIVE-READINESS.md) (analysis) · [BANCO-DAY-ONE-WISHLIST.md](BANCO-DAY-ONE-WISHLIST.md) (polish backlog).*

---

## ⚠️ FIRST THING TOMORROW — identity terminal collision recovery
Tonight's Product Sales deploy (`checkout --force origin/main` on the sandbox + banco-staging box trees) **reverted the identity terminal's uncommitted code patches** on those two envs (orphan `.bak`s prove it). PROD untouched + safe. The identity terminal still holds its **3 fix commits** — nothing lost. Fix:
- [ ] Identity terminal: **land the 3 commits onto `main` (`92aabaa`) + push.** (It was waiting for this terminal to finish on main — now done.)
- [ ] Then **redeploy sandbox + banco-staging from updated main** (restores the fixes, committed this time).
- [ ] **Don't** `make sandbox-deploy` / force-checkout sandbox|staging before that — it just re-reverts.
- [ ] Verify prod actually carries the fold (its tree source matches plain main — may be KC-realm config, not code).
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

- [ ] **P1 — Fiscal sign-off. START THIS FIRST.** Send the Treuhänder the receipt + Z-report samples (already generated in `docs/business/banco-fiscal/`) and get the thumbs-up on gapless/immutable numbering. 🧍
  *Why first: it's the only item that waits on a human outside our control. Everything else we can do in days — this we can't rush, so start the clock now.*
- [ ] **P2 — Offline outbox.** A dropped network must never kill a sale (queue → replay when back). 🐯 build · spec in `BANCO-OFFLINE-AND-PWA-PLAN.md`.
  *Why: highest in-shop risk. Effort: real, a few sessions.*
- [ ] **P3 — Hardware dry-run at the shop.** Thermal printer + barcode scanner on real metal — never tested live. 👥 (must be at Artemis). *Effort: half a day on-site.*
- [ ] **P4 — Prod identity cleanup + SMTP.** Clean prod realm (the pam split-brain) + wire shop email. 👥 — **NOT tonight** (your call). *Effort: one focused session.*

---

## 🛡️ HARDEN — right after the blockers, before relaxing
- [ ] **P5 — Offsite backup copy.** Local backups + restore-drill are done; an offsite copy is still TODO. 🐯
- [ ] **P6 — Push alerting.** Today the daily smoke writes pull-only status files; add a push so a failure reaches you. 🐯
- [ ] **P7 — Fiscal-robustness fix.** The subtotal≤0 Z-report drift on messy mixed data — defensive fix is queued. 🐯
- [ ] **P8 — Runbook + rollback + staff SOP + invoice/contract + DPA.** The paperwork that makes it a business, not a demo. 👥

---

## ✨ POLISH BACKLOG — after go-live, only on demand
*(Most specced in [BANCO-DAY-ONE-WISHLIST.md](BANCO-DAY-ONE-WISHLIST.md). Don't build ahead of need.)*
- **✅ DONE 2026-06-28:** Feedback button → small corner 💬 icon (`17fa4ba`) · **Promo-restricted discount block** — no discounts on tobacco/alcohol, cashier+manager (`2b8aefa`, Angel: Pam discounted cigs; was role-cap-only). Both LIVE all 3 envs + regression tests.
- **Cosmetics queue (2026-06-28, in progress):** **Pagination** on long lists (transactions, catalog, buyer drill) ← *next, all three*.
- **Discount UX follow-up:** in the till, grey-out/hide the discount field for promo-restricted items so the cashier sees it can't be discounted BEFORE trying (server already blocks; this is the hint).
- **Tiered / quantity-break pricing (Angel idea 2026-06-28):** "buy 5 → price A, buy 10 → price B" auto in cart. A price-rules layer (product → qty thresholds → unit price). MODERATE build; MUST respect the promo-restricted guard (a volume break is still a promotion → none on tobacco/alcohol) + VAT/receipt/reconciliation. Ad-hoc discounts cover today; build only when a real shop asks.
- **Category** chart on the report + the **hierarchy/CRUD + emoji picker** (specced in `BANCO-CATEGORY-MANAGEMENT-PLAN.md`; emoji seam already shipped).
- Mobile tail: catalog card overflow on sub-375 phones (prod data); `cdn.tailwindcss.com` prod warning → proper Tailwind build (rule #9).
- Product Sales #2 customer-detail screen · #3 dashboard cards · XLSX export · **Export-to-Google-Drive (sellable feature)** · audited PII/HR export.

---

*The blockers (P1–P4) are the only things standing between Felix and a clean Monday open. Everything below them makes it sturdier; everything in Polish makes him love it. Top-down. One tier at a time.*
