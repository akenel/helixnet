# Banco — The Daily Closeout, the Timesheet, and Go-Live

*Captured from Angel, 2026-06-25. The "what does day one actually look like in Felix's
real shop" brain dump — distinct from the Day-One **demo film** docs.*

This locks three things that all hang off **one idea**: the unit of Banco is **the day**,
and the day's anchor is the **closeout**. Get the closeout right and go-live, resilience,
accounting, and HR all fall out of it.

---

## 1. Go-Live: start clean, not big-bang

There is **no data migration**. Day one = preloaded items, **zero transactions**.

But it doesn't begin on a random Tuesday afternoon. Go-live happens on a **sturdy boundary**:
- A **Monday morning**, at open (~10:00), **start of a clean week**.
- Never mid-day, never mid-week. "Just doesn't make sense."

**Why this is the right model (and not a cop-out):** Banco doesn't need a migration because
the system's job isn't to inherit history — it's to **close out each day going forward**.
Felix already runs his shop as a sequence of independent daily closeouts. We're not replacing
his past; we're picking up the rhythm he already has, from a clean Monday.

> The closeout **is** the go-live mechanism. Each green closeout is one day fully live.

---

## 2. The Closeout — the heartbeat

Felix already does this by hand, every day, and has for 25 years:

> "That's the sales for today. Give me the cash. How many pieces went in." → **six numbers**
> → one line (or six) into **Banana** accounting. Plus expenses. Done.

Two layers stack on top of each other:

### 2a. The cashier closeout (Pam's one-pager) — **MOSTLY BUILT**
What Pam hands Felix at end of shift:
- **What she sold** — she writes down every item as she sells it; by close there are ~20
  items on one sheet. → *(built: the itemized Daily Sales Log on the drawer report.)*
- **The money, split by tender** — cash / Visa / debit / **Twint** readout totals, with the
  little slips stapled to the page. → *(built: cash counted in the drawer; card/Twint
  reported not counted.)*
- **The float reconciliation** — "I started with CHF 100 this morning, there's CHF 200 now."
  → *(built: counted float in, count out, expected-vs-counted, variance ±CHF 0.20.)*

This is the `cash_shift` work already on staging (see [[banco-cash-shift]]). The **money half
of the closeout is essentially done.** What's new below is the **person half**.

### 2b. Each day stands alone — the decoupling rule (the real prize)
> "If she shows up sick the next day and he doesn't show up, yesterday is **still closed out**.
> Nothing held up. The drawer is closed for the day."

Every day's closeout is **self-contained**. No open thread crosses midnight, no person's
absence blocks another person's books. Felix can write his **one Banana line per day**
regardless of who's in tomorrow. This is the resilience property to protect in every design
decision: **never let day N+1 depend on a human action from day N.**

---

## 3. The Timesheet — the person half of the closeout

When someone closes out, they **also close out *themselves*** for the day. Simple timesheet,
filled **at closeout**:

- **Start time** (e.g. 09:00) · **Finish time** (e.g. 18:00)
- **Lunch / break** deduction (e.g. ½ hour) → **hours worked computed for them**
- **Comments / notes** — optional ("how did it go")

Crucial nuance — **HR is tied to the POS but not the same as it:**
> "The people who close out are *usually* the cashiers — but not necessarily. Anybody could
> just be cleaning the plates. They still hand in a timesheet."

So the timesheet is a **general end-of-day act**, available to anyone on shift, **not**
strictly bolted to having rung sales. A dishwasher closes out a timesheet with no drawer.

**Everybody closes out their day — including Felix.** *(2026-06-25 follow-up)* — the rule is
flat: **"everybody has to do a checkup for the day."** One daily checkup per person, full stop.

### 3a. What Pam sees — her own day, not the store, not each sale *(follow-up)*
When Pam logs in, the screen is **hers**: her **hours / timesheet for today** front and
centre — not a feed of individual sales, not the store-wide numbers. At closeout it tells her
the three things she needs to hand over the day:
- **This much cash** to turn in,
- **This is your total sales**,
- **These are your hours** — start → the time you walk out.

(Matches the cash-shift "My Drawer" already built: a cashier sees only her own totals.)

### 3b. The trust model — self-reported, her choice, camera is the *backstop* *(follow-up)*
The finish time is **self-entered and honest by choice**. She writes the time she's walking
out — she can even enter it slightly ahead ("I'm leaving in half an hour, I'll just put the
time I walk out the door"). **It's her call.**

This is **trust-first, not buddy-punch lockdown.** Came-in-at-8-but-really-9 can't be
perfectly verified — there's a real amount of trust. But the store has **video cameras
everywhere**, so it *can* be verified when it matters (the cameras have recorded robberies
and handed footage to the police). The camera is the **backstop, not the gate** — nobody
clocks in *through* a camera; the camera is there if a dispute ever needs settling.

> Design note: the dark `TimeEntryModel` header says *"Cameras verify. No buddy punching."*
> Angel's lived model is **softer** — trust the person, let them self-report, keep the camera
> as evidence-of-last-resort. Build the screen for **honesty + ease**, not for policing.
> (Felix once chased an armed robber down the street while watching from the back-room camera —
> local-hero stuff the cops weren't thrilled about. Point: cameras are for the real events,
> not for catching Pam ten minutes short.)

### Felix's rollup cadence (already how he works)
- He tracks 3–5 staff on a **spreadsheet** he's proud of: full name, **AHV number**,
  birth date, address — a card on every person.
- **Weekly or (more likely) end-of-month**, he walks the timesheets and computes:
  hours worked, **what days they showed up**, **vacation** earned, part-time vs **overtime**,
  each person's **%**. Then payroll nonsense.

---

### 3c. Anytime, not just at closeout — Pam's living day view *(2026-06-25 follow-up)*
The timesheet isn't a one-shot at the end. **Any time during the day** Pam can open her view
and see: what time she put in, when she started, her **shift time**, and **exactly what
transactions she's done so far** — by cash or by customer. So 3a's "she sees her own day, not
each sale" means **her day is the *frame*** (hours + timesheet front and centre); her **own**
transactions are there to drill into — never the store-wide feed, always just hers.

Her day view also **pulls in live context** (read-only): **previous-day sales**, shop stats,
**who's on duty** (the Friday calendar / rota), etc. A real cockpit for *her* shift.

**Shift time is pre-filled from shop config — and editable.** Banco derives her expected shift
from **day-of-week × operating hours** in the **Settings / Preferences dashboard**. If it's
wrong, **she can fix it** (it's a default, not a lock — consistent with 3b's trust model).

> ⚠ **Gap:** today `store_settings.opening_hours` is a single **free-text** string
> (`"Mon–Wed 11–19, Thu–Fri 11–20…"`) — great for the receipt/storefront, but **can't** be
> machine-read to derive a per-day shift or drive a coverage calendar. To deliver 3c/3d we need
> a **structured per-day-of-week schedule** (open/close per weekday) in settings, in addition
> to the human-readable string. Flagging before anyone assumes the field is ready.

### 3d. The coverage calendar / rota — planned vs actual *(2026-06-25 follow-up)*
A **shift-coverage board**, separate from the timesheet:
- **All operating hours must be covered by somebody.** Open/uncovered shifts show as gaps.
- **Self-serve sign-up:** a worker can **grab an open shift** — "I'll do that afternoon" — if
  it isn't covered. Felix doesn't have to assign every block.
- **Manager (Felix) can edit** the calendar at will.
- **Reality overrides the calendar.** *"If she's working, she's working — doesn't matter what
  the calendar says."* The rota is a **planning / coverage tool**, the timesheet is **what
  actually happened**. They are two different things and the **timesheet (actual) wins**. Never
  let the calendar gate or auto-fill hours-actually-worked.
- **Constraint = minimum rest between shifts.** Angel: ~8h separation between one shift's end
  and the next start (he also said "like 24 hours" — fuzzy). ⚠ **Verify against Swiss law:**
  Arbeitsgesetz Art. 15a mandates **11 consecutive hours daily rest** — use that as the real
  rule, not 8, and flag it as a lawyer/Treuhänder check before enforcing.

> **Planned-vs-actual is the rule to hold:** calendar = intent (coverage, self-signup, rest
> constraint); timesheet = truth (self-reported, camera-backstopped). Don't conflate them.

### 3e. THE KICKER — it's done for them automatically *(2026-06-25 follow-up)*
> "They don't even have to do anything — it's done for them automatically. It shows when they
> logged in, so we can tally it up for them from the day."

The timesheet's **default is zero-effort.** Banco already records every login/logout as a
presence session (`ShiftSessionModel`: `started_at` + `ended_at`, "every login creates a
session, every logout ends it"). So the day's hours can be **auto-tallied** from those
sessions — the employee confirms, doesn't type. "My Day" becomes: *"You logged in at 09:02,
leaving now? → 8.4 h"* — one tap. The manual start/finish form is the **override/exception**,
not the everyday path.

- **Granularity:** the login events allow fine reporting (per-login, last-hour) **if ever
  wanted** — but *"we're really a daily business,"* so **the day is the reporting unit.**
- **Worst case is only Day-1 of a brand-new employee** (the one-time setup below). After that,
  every day is automatic.

> Reframes the screen I'm building: pre-fill start + running hours from the session log; the
> employee just **confirms at close**. Same screen, smarter default.

### 3f. WHERE PEOPLE LIVE — HR is the system of record, POS just *picks* *(2026-06-25 follow-up)*
Angel reasoned the layering out loud and landed it cleanly:

- **New-employee onboarding happens in the HR module, ONCE** — the who's-who card
  (Leanna: AHV, DOB, address). *"We have an HR module and just pull the data in from there;
  we prepop calendar, people resources, expenses in the HR module — not [the POS]."*
  → **HR module = the system of record for people, calendar/rota, resources, expenses.**
  This **validates the original Option-A** (HR is its own product) — it's not just dark
  payroll, it's the people-master the POS reads from.
- **POS/Banco is a CONSUMER.** *"In the POS config/settings screen, Felix selects the cashiers
  from a list — from HR."* POS **never creates** employee master data; Felix just **maps which
  HR employees are cashiers** on this till.

**This is the *proper* identity link** — and it supersedes the username/email bridge I shipped
in `get_employee_from_token`. That bridge stays as the **interim** (so My Day works today on
the seeded cast), but the designed answer is **Felix's settings cashier-picker**: pick an HR
employee → store the `users.id ↔ employees` link → the token resolves the real way. One-time,
explicit, no guessing.

```
   HR MODULE  ──(system of record: people · calendar · expenses)──┐
   new hire Leanna → AHV/DOB/address entered ONCE                 │ pull
                                                                  ▼
   POS / BANCO  ── Settings ▸ "Cashiers" ▸ Felix picks from HR list ──→ login auto-tallies hours
                  (consumer; maps cashier ↔ HR employee, never creates one)
```

## 4. The AI End-of-Day Survey — the feature Felix will ask for "right away"

At closeout, an **optional** quick survey:
- Were sales good? · Weather? · Roughly how many people came in? · Busy or slow?
- Saw any regulars today?

**The killer move — Banco drafts it *for* them.** The day's sales data is already in the
system, so the AI **pre-fills the survey** ("you sold X, Y, Z; it was a busy afternoon;
takings up vs last Monday") and the cashier just confirms or tweaks. **Velocity-driven** —
the survey writes itself; the human signs off. Optional, never mandatory.

This turns a chore into a one-tap habit and gives Felix a **daily texture log** (mood,
footfall, weather, regulars) sitting next to the hard numbers — narrative + ledger, the
Banco signature.

---

## 5. The seal-inspection finding: **this is all already built, dark**

Per the rule — *if one seal fails, check all the seals* — before scoping this as new work,
checked the codebase. **The entire HR/timesheet back-end already exists and is wired to the
API; it just has no UI.** (See `BANCO-HR-MODULE-SCOPE-FLAG.md`.)

| Angel's words | Already in code |
|---|---|
| start time / finish time | `TimeEntryModel.start_time` / `end_time` (HH:MM) |
| half-hour for lunch | `break_minutes` + `effective_hours` (hours after break) |
| hours worked computed | `hours` / `effective_hours` (Numeric) |
| vacation / sick / overtime | `EntryType`: regular·holiday·sick·overtime·public_holiday·training |
| comments / notes | `TimeEntryModel.description` |
| Felix's weekly/monthly approve | status flow draft→submitted→**approved**→paid + `timesheet/week` API |
| card on every person (AHV/DOB/address) | `EmployeeModel` (AHV `756.…`, DOB, address, IBAN, canton, hourly rate) |
| the % / payroll | `payroll_service` (Swiss deduction math) + `PaySlipModel` |

**Gap = the three thin things, not the engine:**
1. A **timesheet-at-closeout screen** (anyone on shift; start/finish/lunch → hours; note).
2. The **link** cash-shift close → create that day's `TimeEntry` (and let a non-cashier
   close a bare timesheet with no drawer).
3. The **AI survey** auto-draft from the day's sales (genuinely new; small recipe on the
   existing `run_llm`).

---

## 6. Decision this forces (updates the HR scope flag)

`BANCO-HR-MODULE-SCOPE-FLAG.md` recommended **Option A: keep all HR dark, it's its own
product.** That call holds for **payroll** (AHV/BVG/Quellensteuer/payslips — different buyer,
different compliance). But Angel's brain dump says the **lightest sliver — timesheet capture
at closeout + the AI survey — is wanted day one** because it falls naturally out of the
drawer close Pam already does.

**Recommended refinement — "Option A, with the closeout sliver":**
- **In scope for Banco now:** timesheet-at-closeout (start/finish/lunch → hours + note) and
  the AI end-of-day survey. These ride the *existing* `TimeEntryModel` — capture only.
- **Stays dark / separate product:** payroll runs, payslips, Swiss deduction math, the
  vacation/overtime/% computation. Felix keeps doing the monthly rollup in his proud
  spreadsheet for now; Banco just **feeds him clean timesheet data** instead of paper.
- **Don't** wire the "User Management" → full payroll button for the demo (unchanged).

Net: Banco captures the day (sales **and** hours **and** texture) in one closeout; Felix's
spreadsheet stays his — we remove the **paper**, not his system. Earns the right to the full
HR product later.

---

## Build order — status as of 2026-06-25 (sandbox @ 9636975)
- ✅ **My Day** — mobile-first daily checkout (`templates/pos/my_day.html`, `/pos/my-day`).
- ✅ **Brick A — identity link.** Self-healing username-join bridge + **Settings ▸ 👥 Staff &
  Logins tab** (Felix links each staff card to a till login). Schema-free.
- ✅ **Brick B — add employees.** `GET/POST/PUT /api/v1/hr/employees`; the Staff tab's
  **➕ Add new employee** (who's-who card; auto BLQ-NNN; pay/IBAN later).
- ✅ **Brick C — auto-tally.** Login records presence (`/shift/start`), My Day **pre-fills
  start** from the first login (`GET /shift/today`) + "✓ tracked you in" banner; manual = override.
- ✅ **Brick D — create a real sign-in + password.** `POST /employees/{id}/provision-login`
  creates the Keycloak user (POS_REALM) + password + cashier role + real link. The Staff row's
  **🔑 Create sign-in**. Re-run = password reset. *This is what actually lets a new hire log in.*
- ✅ **AI end-of-day survey** (`src/services/day_survey.py` + `POST /pos/day-survey/draft`).
  My Day's "🌙 How did the day go?" → **✨ Draft it for me** reads the cashier's day (sales,
  top sellers, span, busiest hour) and drafts busy/steady/slow + footfall + a warm 1–2 line
  note. The human confirms/tweaks; it folds into the time entry's `description` (capture-only,
  no schema change). BYO-brain via `run_llm`; **resilient** — zero-sales / brain-down both
  degrade to an honest deterministic draft, never blocking closeout. *Sandbox-verified
  `ai:true` end-to-end.* 8 unit + 2 black-box tests.
- ✅ **Self-set password (email path)** — `POST /hr/employees/{id}/email-setup` fires
  Keycloak's `UPDATE_PASSWORD`+`VERIFY_EMAIL` email so a hire picks their own password from
  their inbox; Staff row **📧 Email them a setup link instead**. Graceful: no SMTP / no real
  email → plain message to use the password field (the counter-password path is unchanged).
  Gated on realm SMTP → `scripts/configure_kc_smtp.py` (Typer; set/show/test, run once).
- ⏳ **Cleanup brick (proposed) — plain-ASCII role names.** Move the emoji out of the role
  *identifier* into a display label (it's a latent foot-gun; see the emoji note). Do with
  explicit go + careful auth testing — never blind.
- **Later — HR module surface:** calendar/rota, weekly/monthly rollup, payroll (stays dark).

**Resilience acceptance test for all of it:** a cashier sick on day N+1 never blocks day N's
closeout, books, or anyone else's drawer.

---

*Pairs with [[banco-cash-shift]] (the money half, built), `BANCO-HR-MODULE-SCOPE-FLAG.md`
(the dark engine + the A/B/C call), and the Day-One **demo** docs (a different "day one":
the film, not Felix's real go-live).*
