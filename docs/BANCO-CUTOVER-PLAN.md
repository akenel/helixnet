# Banco — Felix / Artemis Cutover Plan (v0 — working draft)

**Goal:** move Artemis Lucerne (Felix, 25 years, the flagship) onto Banco for the **till**,
without breaking his day. If it works for Felix, Banco is the reference customer for every
Swiss head-shop. *"Nothing can screw up — Felix can throw every edge case at me right there
and we can't miss."*

**This is v0.** Sections marked **⟶ NEED FROM FELIX** are the unknowns to fill before go-live.

---

## 1. Scope — what Banco IS, what it hands off, what it never touches

Banco owns **Order-to-Cash (the till)**. Everything else stays as-is and Banco *feeds* it.

| Process | Owner | Banco's role |
|---|---|---|
| **O2C — the sale** (ring up, discount, payment, receipt, cash drawer, close-out) | **Banco** | **Replaces** the old till. The thing that must be perfect. |
| **R2R — accounting** (Banana) | Banana (stays) | Banco **feeds** it the daily Z-report = ~6 numbers. No reinvention. |
| **P2P — purchasing** (Mozy 420-wholesale, ordering stock) | Felix (stays) | Out of scope. Banco's catalogue is *seeded* from Mozy's library, not the buying. |
| **HR — timesheets/payroll** (his spreadsheets) | Spreadsheets (stay) | Out of scope. Maybe a light time-punch later; transfer numbers, don't rebuild. |
| **E-commerce** (Tamar online shop) | Tamar (stays) | A **data source** for enrichment (pictures/descriptions), not replaced. |

**The discipline:** Banco is the till + cash + catalogue + reports. It is NOT an ERP that
eats Banana, Mozy, the spreadsheets, or the webshop. It does one process flawlessly and
hands the rest clean numbers.

## 2. Current state ⟶ NEED FROM FELIX
- [ ] What POS / till does Artemis run **today**? (brand, what it does well, what annoys him)
- [ ] How does he get numbers into **Banana** today? (manual entry? export? which figures?)
- [ ] Hardware: till device(s)? receipt printer (model/connection)? barcode scanner? cash drawer?
- [ ] How many cashiers, and how cash-heavy vs card/TWINT is a typical day?
- [ ] Member/loyalty data (the CRACKs) — does it exist anywhere to migrate, or start fresh?
- [ ] **Label printer** — what does he stick on a product, on what printer? (thermal label
      printer + size, or A4 sticker sheets?) Decides the label-print layout (backlog §6).

## 3. Data migration — the catalogue is the big one
- **Products (~7,000):** sourced from **Mozy's wholesale library** (already the basis of the
  Banana import). Plan: load into Banco prod as the base catalogue, then **enrich on demand**
  (sell-to-seed for the long tail; Tamar/photo-pull for the rest). ⟶ confirm we have a clean
  current export from Mozy (prices especially — they go stale).
- **Opening cash floats:** counted on go-live morning (per cashier).
- **Members/loyalty:** migrate if it exists, else seed as customers transact.
- **Store settings:** VAT (8.1% / 2.6% split), store identity, receipt header — verify vs Felix's real values (the prod receipt currently shows a *Zurich* placeholder address — must be his real Lucerne details before go-live). ⟶ NEED FROM FELIX.

## 4. Cutover approach — recommended: **short parallel run, then hard switch**
1. **Load + dress-rehearse** on the sandbox (empty → real catalogue) — Felix throws edge cases.
2. **Parallel run, ~3 days:** Banco live alongside the old till on a quiet stretch. Cashiers
   ring real sales on Banco; the old till stays available as a safety net. Reconcile both at
   close each night — they must match.
3. **Hard switch:** old till retired; Banco is the shop. Old system kept read-only ~2 weeks.
4. **Hypercare:** daily check-in for the first week; me on call for fixes within the day.

## 5. Training (short — the system is the SOP)
- **Cashiers:** open your drawer + count float (start of day) → sell → the **🆕 New item** flow
  for no-barcode goods → close-out + count (end of day). The new must-do: **open the drawer
  before cash** (the gate enforces it).
- **Felix/manager:** catalogue manage (create/edit/discontinue, photos), reports, the **Z-report
  → Banana** six-number handoff, enhancing on-the-fly items.
- **The SOP/KB** (§7) is the written version they can re-read.

## 6. "Can't miss" — the hardening net
- **Edge-sweep regression suite** (`scripts/edge-sweep.js`, 33/33) — re-run after any change.
- **Live edge-case session with Felix:** he throws his real weird cases (returns, weird
  discounts, partial cash, a customer who changes their mind mid-sale, a power blip) and we
  fix on the spot. Each new case → a new row in the sweep. That's how we get to "can't miss."

## 7. SOP / Knowledge Base ⟶ TO WRITE
A written **Banco O2C standard operating procedure** + a small knowledge base: open day →
sell → handle the odd cases → close day → feed Banana. Felix's shop has 25 years of "how we
do it" in people's heads; this writes it down. (We have ISO-9001 SOP standards + a PDF
pipeline already — `scripts/sop-to-pdf.js`.) Likely the next artifact after this plan.

## 8. Go-live checklist (fill before the switch)
- [ ] Real store identity + VAT on receipts (not the Zurich placeholder)
- [ ] Catalogue loaded + spot-checked (prices sane vs Mozy/Tamar)
- [ ] Receipt printer + scanner + drawer working on Felix's hardware
- [ ] Each cashier can log in; roles correct (cashier vs manager)
- [ ] Edge-sweep green on the prod build; Felix's live edge-case session passed
- [ ] Z-report → Banana handoff agreed (which 6 numbers, how)
- [ ] Rollback rehearsed: `git -C /opt/helix-banco-tree checkout --force <prev> && docker restart helix-platform-banco`
- [ ] Day-One first-sale recorded (the story)

---

**Bottom line:** stop enriching for now. The till is shipped and green. The next real work is
**this plan** — fill the NEED-FROM-FELIX gaps, load the Mozy catalogue, dress-rehearse with
Felix throwing edge cases, parallel-run, switch. Enrichment (Artemis/Tamar pull, photo-search,
Pam-proposes-enhancement) rides *after* the cutover — it makes a working shop richer, it does
not block the switch.
