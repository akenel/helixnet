# Banco — HR / Payroll module: scope flag (decision needed)

There is a **complete, dark Swiss HR / Time & Payroll module** ("BLQ HR") in the codebase.
Before anyone wires the dashboard's **"User Management"** button to it, a deliberate call:
**is this part of Banco, or its own product?**

---

## What's there (back-end complete, ZERO front-end)
- **Models:** `EmployeeModel` (AHV number `756.XXXX.XXXX.XX`, Quellensteuer + tariff code,
  BVG pension, IBAN, canton, contract type, hourly rate, probation dates…),
  `TimeEntryModel`, `PaySlipModel`.
- **API `/api/v1/hr`** (registered, live): time entries (create/edit/submit/approve),
  `timesheet/week`, `payroll` run/calculate/approve/mark-paid, `payslips`.
- **`payroll_service`** — the Swiss deduction math.
- Seeded with demo employees + time entries at startup.
- **No UI at all.** The dashboard **"User Management" → `/pos/admin`** button is a stub that
  re-renders the dashboard.

## The tension
Banco's wedge is the head-shop **sales floor** — sell-to-seed, born-once, zero perpetual
inventory. HR/payroll is a **different buyer, different surface, different compliance
domain** (AHV / BVG / Quellensteuer / payslips). Bolting it onto the POS dashboard blurs
the product right when we're trying to make the Day-One story razor-sharp for Felix.

## Options
| | Option | Verdict |
|---|--------|---------|
| **A** | **Separate product.** "BLQ HR" rides the same engine but is its own app/surface (the payslip model literally says *"Built for Pam, Felix, and Mosey"*). Leave it dark in Banco; surface it elsewhere when it has its own customer + steward. | **RECOMMENDED** |
| **B** | **Thin "Staff" screen in Banco.** Wire only the lightest part — list employees, add/edit basics (name, AHV, role, hourly rate). Defer payroll. | Scope-creep risk |
| **C** | **Full HR in Banco.** Wire the whole payroll suite into the POS dashboard. | **Not recommended** — a second product hiding in a button |

## Recommendation — **A**
Leave it dark. Treat **BLQ HR as its own future product**, with its own demo and its own
steward, riding the shared engine (same design-factory thesis as the verticals). Do **not**
wire "User Management" to it for the Felix Day-One demo. Keep the head-shop story clean.

**Near-term action:** the "User Management" button should be **hidden** (or relabelled a
clear future-state stub) rather than left as a dead click. The **Settings page**
(`BANCO-SETTINGS-PAGE-SPEC.md`) is the *only* admin screen worth wiring now, and only for
the receipt-compliance reason.

## For the Day-One demo
Both admin buttons are admin-only; Felix demos as cashier/manager and never sees them —
so they don't block the demo. Just don't leave a dead "User Management" click in a video.
