# Banco Go-Live Worklist — THE ordered list

*Open this, work top-down, finish one tier before opening the next. Don't fan out across five things. 2026-06-28.*

*Owners: 🧍 = Angel's hands needed (physical / decision / external call) · 🐯 = Tigs can do it · 👥 = both, together.*

*Detail lives in: [BANCO-GO-LIVE-READINESS.md](BANCO-GO-LIVE-READINESS.md) (analysis) · [BANCO-DAY-ONE-WISHLIST.md](BANCO-DAY-ONE-WISHLIST.md) (polish backlog).*

---

## 🔥 RIGHT NOW — tonight, 5 minutes, your hands
- [ ] **Test the Product Sales report** on staging (Fairphone): https://staging-banco.lapiazza.app/pos/reports/products (login *felix*). Tap a product → "who bought it", try Export CSV + Print. **If it's good → tell Tigs "ship it" → it's on prod in one clean step** (already committed `9dc9641`, no migration). 🧍

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
*(All specced in [BANCO-DAY-ONE-WISHLIST.md](BANCO-DAY-ONE-WISHLIST.md). Don't build ahead of need.)*
- Product Sales #2 customer-detail screen · #3 dashboard cards · XLSX export · **Export-to-Google-Drive (sellable feature)** · audited PII/HR export.

---

*The blockers (P1–P4) are the only things standing between Felix and a clean Monday open. Everything below them makes it sturdier; everything in Polish makes him love it. Top-down. One tier at a time.*
