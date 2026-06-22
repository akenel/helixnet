# Banco — Staff & Admin Roadmap (the control centre)

Angel's vision (2026-06-22), captured + reality-checked against the code. **Good news: most
of it is closer than it feels** — the data models and even the Keycloak plumbing already exist.
The work is mostly *surfacing* what's there as UI, plus one real integration (logins).

Status key: ✅ exists · 🟡 partial/data-there-no-UI · 🔨 real build · ⟶ need.

---

## 1. Settings = a tabbed control centre  🟡
**Built today:** a real `/pos/settings` screen (admin-only) — store identity, address, contact,
Swiss VAT, receipt header/footer/logo, discount caps. Live on every receipt. *(Was a stub.)*
**Angel wants tabs:** Graphics/branding · Tax · Hours of operation · Address · Staff.
- Most fields already exist; **tabbing is reorganising one page.** 🟡
- **Hours of operation** — likely needs new fields on store_settings (additive). ⟶ build small.

## 2. Staff / user management  🟡 + 🔨 (the one real integration)
**The honest split — there are TWO things that look like "a user":**
1. **HR employee record** (name, photo, AHV/social-security no., payslip data) — model
   **`employee_model.py` already exists** (+ payroll/payslip). Needs a **form**. 🟡 easy-ish.
2. **A Keycloak login** (so they can actually sign in + carry the cashier/manager role) —
   **`keycloak_service.py` exists**, so the plumbing to call Keycloak's admin API is here. But
   creating a login + assigning a realm role from our UI (instead of the Keycloak console) is
   the **one genuinely delicate build** (security, provisioning). 🔨 real project.

**Angel's "5-second onboard":** type a name → assign **Cashier** → done; AHV/photo/rest later;
"once you do a payslip you need it all." → A quick **Add Employee** form (name + role + optional
photo) that (a) writes the HR record and (b) provisions the Keycloak login + role. (a) is easy;
(b) is the work. **Felix never opens Keycloak.** Photo reuses the image pipeline we built.
- The current "User Management" dashboard card → verify if real or another stub (`pos_router:3154`).

## 3. Time tracking = the cash drawer  ✅ (already captured!)
**This is the gem.** Angel: "opening the cash drawer logs their hour; closing it = clock out."
**It already does.** `cash_shift_model.py` records `user_id` + `username` + `opened_at` +
`closed_at` — the model comment literally says *"open_at/closed_at also give clean shift hours."*
The shift report already shows hours ("0.15 h"). So **the timesheet is already being recorded** —
open drawer = clock in, close = clock out. Work = **surface it** as a "staff hours" view
(aggregate cash_shifts by user × day). 🟡 small report, no new capture. No separate punch clock.

## 4. Payslips  🟡 → later
Models exist (`payroll_run`, `payslip`). Needs the full employee data (AHV etc.) + a run UI.
Per Angel's scope discipline: **maybe just feed Banana the hours/numbers, don't rebuild payroll.**
Decide at cutover whether Banco runs payslips or hands hours to his existing process.

## 5. Cashier training wizard / guide  🔨 (net-new, self-contained)
Angel wants an **interactive how-to** for a new cashier: *"Start here. Open your drawer. Scan
here. Search needs 2 letters, or pick a category. No code? Create it + take a picture — that's
all you do as a cashier, someone enhances it later. Never block the sale."* → a first-run guided
overlay / coach-marks, dismissible, re-openable from a "?" Help button. Doubles as the demo
narration script. Pairs with the SOP/KB (cutover §7).

---

## Recommended sequence (one brick at a time)
1. **Tabify Settings + add Hours of operation** — organises what's built, quick. (§1)
2. **Staff hours view** — surface the cash-shift clock-in/out we already capture. Nearly free. (§3)
3. **Add Employee form** (HR record: name + role + photo) — easy half. (§2a)
4. **Keycloak login provisioning** — the real integration; lets Felix make a working cashier
   without the Keycloak console. Do it deliberately, on its own. (§2b)
5. **Cashier training wizard** — net-new, also becomes the demo narration. (§5)
6. **Payslips / Banana hand-off** — decide reinvent-vs-feed at cutover. (§4)

**None of this blocks the till that's already shipped.** It's the admin/back-office layer that
makes Banco a *shop's system*, not just a checkout. Build it after the cutover core is signed off.
