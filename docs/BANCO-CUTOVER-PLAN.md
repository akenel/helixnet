# Banco — Felix / Artemis Cutover Plan (v1 — the runbook)

**Goal:** move Artemis Lucerne (Felix, 25 years, the flagship) onto Banco for the **till**,
without breaking his day. If it works for Felix, Banco is the reference customer for every
Swiss head-shop. *"Nothing can screw up — Felix can throw every edge case at me right there
and we can't miss."*

**What this is:** the step-by-step delivery runbook for go-live — sequenced, with an **owner**
on every step and a **go/no-go gate** before each irreversible move. This is the *exact scope*
of the **CHF 1,500 go-live package** in `docs/business/pricing/ARTEMIS-FELIX-PROPOSAL.html` —
the plan and the invoice describe the same job. Pairs with `BANCO-REALM-MODEL.md`
(realm=shop, promote-to-prod = go-live) and `BANCO-CLOSEOUT-TIMESHEET-AND-GOLIVE.md`
(go-live lands on a **sturdy Monday**, closeout = the heartbeat).

> **The two things that unblock everything:** (1) Felix signs the proposal, (2) Felix answers
> the **intake sheet** (`docs/business/FELIX-INTAKE.md`). Until those, this runbook can't start.

---

## 0. The shape in one screen

```
  SIGN + INTAKE        BUILD            LOAD           REHEARSE        PARALLEL         GO-LIVE         HYPERCARE
  (the agreement)   (staging)       (catalogue)     (edge cases)     (~3 days)      (sturdy Mon)      (week 1)
  ───────────────  ────────────   ─────────────   ─────────────   ─────────────   ─────────────   ─────────────
  proposal signed   shop realm     Mozy export     Felix throws     old till +     count floats     daily check-in
  intake answered   VAT/identity   loaded + price   his weird       Banco side by   first sale       fix-within-day
  hardware listed   cashiers       spot-check       cases; fix on    side; reconcile  hard switch     edge → sweep row
  ⟶ GATE A          payment methods sell-to-seed    the spot         nightly match   ⟶ GATE C        ⟶ GATE D
                    ⟶ GATE B        plan for tail    ⟶ edge-sweep                     (irreversible)  (sign-off)
                                                      green
```

Each gate is a **go/no-go**: if it's red, you do not advance. The only irreversible step is
**Gate C (hard switch)** — everything before it is reversible, and there's a rollback rehearsed.

---

## Intake snapshot — DRY RUN (Angel from memory, 2026-06-25 · confirm ✔ with Felix)

> Angel filled the intake as a dry run from what he knows. The **real data** below de-risks most of
> the build; the four ⚠ items are the only things that truly need Felix before go-live.

**The big reframe:** Artemis has run **all on paper since 1999** — *there is no legacy POS to migrate
from.* This is a **greenfield cutover**: no export, no integration, no old till to reconcile. The
"parallel run" is simply *keep the paper tally going 3 days while also ringing on Banco.* Easiest
possible switch.

**The killer feature (his words):** *"don't know what really sold — reporting."* 25+ years with no
item-level sales data. Banco's one-line pitch **and** payback story = **"you'll finally know what
actually sold, by item, every day."** Not VAT, not inventory — *reporting.* Lead the demo with it.

| Topic | Captured (dry run) | Status |
|---|---|---|
| Identity | Artemis GmbH, Murbacherstrasse 37, 6003 Luzern · 041 220 22 22 · contact@artemisluzern.ch · "Since 1999" | ✔ build it (kill the Zurich placeholder) |
| MWST no. | "na" | ⚠ **BLOCKER** — legally required on the receipt |
| Today's till | **All paper.** 6 numbers → 1 line/day into Banana, manual. | ✔ greenfield; Banco's Z-report = those 6 numbers |
| Pain | "don't know what really sold / reporting" | ✔ the headline feature |
| Cashiers | 3 | ✔ 3 logins, per-cashier drawer |
| Counter device | **"nothing"** | ⚠ **BLOCKER** — no device to run Banco on |
| Cash receipts | card terminal prints card receipts; cash = none today | ⚠ decide: thermal printer vs receipt-optional |
| Scanner | none → **phone camera** | ✔ our camera scan (BL-87/90) |
| Cash drawer | "just a bag" | ✔ software drawer works; physical optional |
| Labels | no thermal; office printer in back room | ✔ A4 sticker sheets, post-cutover |
| Catalogue | **Mozy export published daily online — just download.** 7–8k products. | ✔ load it; need the download link |
| Weight goods | none — all pre-packaged | ✔ simplifies pricing (no by-weight) |
| No-barcode | "lots" | ✔ sell-to-seed + Snap & fill |
| Members | seed as they pay | ✔ start fresh |
| VAT | head-shop goods standard-rated | ✔ **8.1% flat** for now; 2.6% only for the future café |
| Go-live date | "when ready" — none yet | set after rehearsal (not a blocker to start) |

**The 4 things only Felix can clear (the real Gate-A list):**
1. ⚠ **MWST number** — the real VAT no. (or confirm registration). The receipt can't be legal without it.
2. ⚠ **A counter device** — he has nothing. Cheapest path: a tablet (camera-scans, runs Banco in Chrome).
   *We advise, he buys* — billable steward work, not a Banco cost.
3. ⚠ **Cash-sale receipts** — buy a small thermal receipt printer, or go receipt-optional/email? One small
   decision, maybe one cheap purchase.
4. **Mozy export access** — the download link/login so we can pull the 7–8k catalogue (prices current daily — excellent).

**What I can start now, no Felix needed:** stand up the shop on the sandbox with the real Luzern identity,
set VAT 8.1% flat, create 3 cashier logins, load the Mozy catalogue the moment we have the link. **Build
first → book the Monday once hardware + a sandbox rehearsal exist.**

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
hands the rest clean numbers. **Scope creep is the #1 risk to go-live** — every "can it also…"
goes on the roadmap, not into the cutover.

---

## 2. The runbook — phases, owners, gates

Days are **relative to Go-Live Monday (T-0)** and approximate — the real clock starts when
Gate A clears. Owner key: **A**=Angel (steward), **F**=Felix, **T**=Tigs (build/automation).

### Phase 0 — Agreement + intake · ⟶ **GATE A**
| # | Step | Owner |
|---|---|---|
| 0.1 | Send Felix the **proposal** + the **intake sheet** together | A |
| 0.2 | Felix signs (or "agreed") → **first invoice issued** (Phase-0 first franc) | F / A |
| 0.3 | Felix answers the intake (current till, Banana handoff, hardware, cashiers, members, label printer) | F |
| 0.4 | Pick the **Go-Live Monday** date on the calendar (a clean week, his choice) | A / F |

**GATE A — go when:** proposal signed · invoice sent · intake answered · date booked.
*No build work starts before Gate A.* (Demand-pull rule: we build the cutover because a paying customer booked it.)

### Phase 1 — Build the shop (staging) · ⟶ **GATE B**
| # | Step | Owner |
|---|---|---|
| 1.1 | Stand up Artemis as its own realm from the **reference template** (Cashier/Manager/Owner) — see `BANCO-REALM-MODEL.md` | T |
| 1.2 | **Real store identity** on receipts — his real Lucerne address (kill the Zurich placeholder), name, MWST no. | T / F |
| 1.3 | **VAT config** — 8.1% standard / 2.6% reduced where it applies; verify against his real product mix | T |
| 1.4 | **Cashier accounts** — one login per real person, correct role (cashier vs manager) | T / F |
| 1.5 | **Payment methods** — cash + the card/TWINT mix he actually takes | T / F |

**GATE B — go when:** Felix can log in on staging, sees his real shop name/address on a receipt, VAT looks right on a test sale.

### Phase 2 — Load the catalogue · (sell-to-seed for the tail)
| # | Step | Owner |
|---|---|---|
| 2.1 | Get a **clean current Mozy export** (~7,000 products) — **prices especially** (they go stale) | F / A |
| 2.2 | Load into Banco as the base catalogue; spot-check prices vs Mozy/Tamar | T |
| 2.3 | Decide the **long tail**: don't chase 100% — **sell-to-seed** fills gaps, photo/AI drafts the no-barcode goods (`Snap & fill`) | A |
| 2.4 | **Members/loyalty (CRACKs):** migrate if a list exists, else seed as customers transact | A / F |

> Catalogue completeness is **not** a go-live blocker. A shop that can ring up its top sellers
> and seed the rest at the counter is live. Perfect is the enemy of the sturdy Monday.

### Phase 3 — Dress rehearsal (sandbox) · ⟶ edge-sweep green
| # | Step | Owner |
|---|---|---|
| 3.1 | Sit with Felix on the **sandbox**; he throws his real weird cases — returns, odd discounts, partial cash, customer changes mind mid-sale, power blip | A / F |
| 3.2 | Fix on the spot; **each new case → a new row in `scripts/edge-sweep.js`** | T |
| 3.3 | Run the full edge-sweep; must be **green** on the prod build | T |
| 3.4 | Train: cashier loop (open drawer+float → sell → 🆕 new item → close+count) and manager loop (catalogue, reports, Z-report→Banana) | A |

### Phase 4 — Parallel run (~3 days, the week *before* go-live)
| # | Step | Owner |
|---|---|---|
| 4.1 | On a quiet stretch, cashiers ring **real sales on Banco** while the **old till stays available** as the safety net | F |
| 4.2 | **Reconcile both at each close** — the numbers must match | A / F |
| 4.3 | Any mismatch → root-cause + fix before go-live; a clean reconcile is the green light for Gate C | A / T |

### Phase 5 — Go-Live Monday (T-0) · ⟶ **GATE C (irreversible)**
| # | Step | Owner |
|---|---|---|
| 5.1 | **Promote the realm to prod** (staging → prod is the shop going live, `BANCO-REALM-MODEL.md`) | T |
| 5.2 | Monday at open (~10:00): **count opening floats** per cashier | F |
| 5.3 | **First sale on Banco as the shop of record** — old till retired (kept read-only ~2 weeks) | F |
| 5.4 | Record the **Day-One first-sale** story (the reference moment) | A |

**GATE C — go when:** parallel run reconciled clean · edge-sweep green on prod · receipts show real identity ·
each cashier logs in · **rollback rehearsed**. This is the one-way door — do not cross it red.

**Rollback (rehearsed before T-0):**
```
git -C /opt/helix-banco-tree checkout --force <prev-sha> && docker restart helix-platform-banco
```
Old till stays physically available and read-only for ~2 weeks as the ultimate safety net.

### Phase 6 — Hypercare (week 1) · ⟶ **GATE D (sign-off → steward Care begins)**
| # | Step | Owner |
|---|---|---|
| 6.1 | **Daily check-in** the first week; fixes within the day | A |
| 6.2 | Each real-world edge → a sweep row (the net keeps tightening) | T |
| 6.3 | Confirm the **Z-report → Banana** six-number handoff works on real days | A / F |
| 6.4 | End of week-1: Felix signs off; **Steward Care + hosting begin** (the MRR) | A / F |

**GATE D — go when:** a full clean week of closeouts · Banana handoff proven · Felix says "this is my till now."

---

## 3. The "can't miss" net

- **Edge-sweep regression** (`scripts/edge-sweep.js`) — re-run after *any* change; green is the gate.
- **Live edge-case session** (Phase 3) — Felix's 25 years of weird cases become test rows.
- **Parallel run reconcile** (Phase 4) — two systems must agree before the hard switch.
- **Rehearsed rollback** + old till read-only — the switch is reversible until Felix is sure.
- **SOP/KB** (below) — the written version of "how we do it" so it doesn't live only in heads.

## 4. SOP / Knowledge Base ⟶ TO WRITE (the Phase-1 playbook seed)
A written **Banco O2C standard operating procedure** + small KB: open day → sell → handle the
odd cases → close day → feed Banana. We have ISO-9001 SOP standards + a PDF pipeline
(`scripts/sop-to-pdf.js`). **This SOP is also the first brick of the Steward Onboarding Kit** —
write it once for Felix, reuse it for customer #2 and steward #1. (Externalize-yourself rule.)

---

## 5. What's deliberately NOT in this cutover (rides *after*)
Enrichment (Tamar/photo pull, `Snap & fill` everywhere, Pam-proposes-enhancement), receiving/PO,
reorder, German UI, multi-department (the March-2027 café). All mapped, none block the switch.
A working till first; richer shop second.

---

**Bottom line:** the till is shipped and green. Go-live is now an **operations** job, not a build
job: sign + intake (Gate A) → build the shop → load the catalogue → rehearse with Felix throwing
edge cases → parallel-run → switch on a sturdy Monday → hypercare. Fill the intake, book the
Monday, and run the gates.
