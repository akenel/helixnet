# Camper & Tour -- Testing Checklist

**Tester:** Anne
**Date:** February 17, 2026
**App:** Camper & Tour Service Management (HelixNet)
**Estimated time:** ~1 hour for first session

---

> **IMPORTANT -- URL CHANGE (Feb 17, 2026)**
>
> The app has moved to a new dedicated server. If you saved the old URL, please update your bookmark:
>
> ~~Old: `https://206.189.30.236:8081/camper`~~ -- no longer active
>
> **New: `https://46.62.138.218/camper`** -- use this one
>
> The new server is faster and runs 24/7 (no longer depends on Angel's laptop).

---

## ACCESS

**URL:** https://46.62.138.218/camper

**All passwords:** `helix_pass` (same for every account)

> **First time only:** Your browser will show a security warning ("Your connection is not private" or similar) because we use a self-signed certificate for testing. This is expected and safe:
> - **Chrome:** Click "Advanced" then "Proceed to 46.62.138.218 (unsafe)"
> - **Firefox:** Click "Advanced" then "Accept the Risk and Continue"
> - **Safari:** Click "Show Details" then "visit this website"
>
> After accepting, you should see the Camper & Tour login page with an orange gradient background.

---

## TEST ACCOUNTS

Pick one account per session. Start with **nino** (manager) for the best first impression.

| Username | Role | What you can do |
|----------|------|-----------------|
| **nino** | Manager | Everything -- vehicles, jobs, customers, appointments, invoices. **Start here.** |
| maximo | Mechanic | Log work, update jobs, view schedule |
| miguel | Counter | Check-in, customers, quotes |
| simona | Counter (trainee) | Same as miguel |
| camper-auditor | Auditor (read-only) | View everything, edit nothing |
| sebastino | Admin | Full access + admin features |

---

## PHASE 1: FIRST LOGIN (5 min)

- [ ] Open https://46.62.138.218/camper
- [ ] Click the orange "Accedi" button
- [ ] On the Keycloak login page, enter: **nino** / **helix_pass**
- [ ] Click "Sign In"
- [ ] You should land on the Dashboard with "Good morning, Nino!" (or afternoon/evening)
- [ ] Note: The dashboard shows stat cards: Vehicles, Jobs, Parts, Revenue

**Tip:** Add `?lang=en` to any URL for English labels. Example:
`https://46.62.138.218/camper/dashboard?lang=en`

---

## PHASE 2: EXPLORE THE DASHBOARD (5 min)

- [ ] Read all stat cards (Vehicles in Service, Active Jobs, Waiting for Parts, etc.)
- [ ] Click "View all" links on any stat card
- [ ] Try the quick-action icons (Check-In, New Quote, Calendar, Invoices)
- [ ] Notice the greeting changes based on time of day

---

## PHASE 3: VEHICLES (10 min)

- [ ] Navigate to Vehicles (via sidebar or dashboard)
- [ ] You should see 4 vehicles (Hymer Eriba, VW California, Fiat Ducato, Knaus)
- [ ] Click on a vehicle to see its details
- [ ] Note: plates, make/model, owner, service history
- [ ] Try the search/filter if available

---

## PHASE 4: CUSTOMERS (10 min)

- [ ] Navigate to Customers
- [ ] You should see 4 customers (Angel, Marco, Hans, Sophie)
- [ ] Click into a customer to see their details
- [ ] Try creating a NEW customer:
  - First name: Anne
  - Last name: Tester
  - Phone: 0041 79 123 4567
  - Email: anne@test.ch
- [ ] Search for the customer you just created

---

## PHASE 5: JOBS (15 min)

- [ ] Navigate to Jobs
- [ ] You should see 6 jobs (roof seal, brake service, winterization, etc.)
- [ ] Click into a job to see the full detail page
- [ ] Note: status badges, work log entries, cost summary
- [ ] Check the different job statuses (Open, In Progress, Waiting Parts, etc.)
- [ ] Try creating a new job:
  - Pick a vehicle
  - Pick a customer
  - Add a title like "Test Job -- Brake Inspection"
  - Add a description

---

## PHASE 6: APPOINTMENTS (10 min)

- [ ] Navigate to Appointments
- [ ] See today's board: Booked appointments (left) vs Walk-in Queue (right)
- [ ] Click "+ Quick Walk-in" -- fill in a name + description
- [ ] Watch it appear in the queue
- [ ] Try changing status: Arrived -> Start Service -> Completed

> Note: If the appointment board looks empty, it may be because seed data was generated on a different date. Try the other sections first.

---

## PHASE 7: BAY TIMELINE (5 min)

- [ ] Navigate to Bay Timeline (via sidebar)
- [ ] See the weekly grid: 5 bays x 7 days
- [ ] Hover over colored bars to see job details
- [ ] Click "Next Week" and "Today" buttons

---

## PHASE 8: QUOTATIONS + INVOICES (10 min)

- [ ] Navigate to Quotations
- [ ] View any existing quotations
- [ ] Navigate to Invoices
- [ ] View any existing invoices
- [ ] Check the PDF/print preview if available

---

## PHASE 9: ROLE TESTING (10 min)

This phase tests that different users see different things.

1. **Logout** (click your name in the top-right, then Logout)
2. **Login as maximo** / helix_pass (mechanic)
   - [ ] Can you see the dashboard?
   - [ ] Can you view jobs?
   - [ ] Try editing a job -- does it work?
   - [ ] Try accessing something a mechanic shouldn't do
3. **Logout and login as camper-auditor** / helix_pass
   - [ ] Can you VIEW everything?
   - [ ] Try to EDIT or CREATE something -- it should be blocked
   - [ ] Note any error messages

---

## BUG REPORTING

When you find something broken or confusing:

1. **Screenshot it** (or describe what you see)
2. **Note which user** you were logged in as
3. **Note what you clicked** and what you expected to happen
4. **Send to Angel on Telegram** (@BigKingFisher)

### What counts as a bug:
- Page shows an error or blank screen
- Button does nothing when clicked
- Data doesn't save after you submit a form
- Something looks wrong (overlapping text, broken layout)
- A feature is missing or incomplete

### What's NOT a bug (for now):
- Italian labels (use `?lang=en` for English)
- Slow loading on first page (server is in Helsinki, should be fast after that)
- Appointment board empty on certain dates (seed data limitation)

---

## KNOWN ISSUES

1. **Certificate warning:** The first time you visit the URL, your browser will warn about the security certificate. Accept it once -- see the ACCESS section above for instructions.
2. **Speed:** The app runs on a dedicated cloud server in Helsinki. Pages should load quickly (~100-300ms).
3. **Appointment seed data:** Walk-in and booked appointments are generated for specific dates. The board might be empty today -- create your own walk-ins to test.
4. **Session timeout:** If you get "Not authenticated" after ~30 minutes, just log out and back in.
5. **English mode:** Most labels are in Italian by default. Add `?lang=en` to the URL for English.

---

## AFTER TESTING

Send Angel a quick summary:
- What worked well?
- What was confusing?
- What broke?
- Any suggestions?

Thank you for being our first human tester!

---

*Updated: Feb 17, 2026 | HelixNet v1.0 | Camper & Tour Service Management | Server: Hetzner CX32 (Helsinki)*
