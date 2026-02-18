# Camper & Tour -- Service Management Demo

## Overview
- **Target audience:** Nino, Sebastino, and prospective camper service shops
- **Language:** English (base), Italian labels visible on-screen
- **Runtime:** ~4 minutes
- **Demo data:** 4 customers, 4 vehicles, 5 jobs (MAX seal story is real)

---

## Scene 1: Intro Card (5s)
*Static title card -- no voiceover during this shot.*

---

## Scene 2: Login (15s)
*Screen shows the Camper & Tour login page at /camper*

- "This is Camper and Tour -- a service management system built for camper repair shops."
- "We're logging in as Nino, the shop manager, through Keycloak single sign-on."

---

## Scene 3: Dashboard -- Morning Overview (25s)
*Screen shows the dashboard with 4 stat cards and active jobs table*

- "Every morning, Nino opens the dashboard."
- "Four numbers tell him everything: vehicles in the shop, active jobs, parts on order, and quotes waiting for approval."
- "Below that -- every active job, at a glance. Who's working on what, which vehicle, and the current status."
- "No paper shuffling. No asking around the shop. One screen."

---

## Scene 4: Vehicle Check-In -- Search by Plate (20s)
*Screen shows /camper/checkin, types "TI 123456" in the search box*

- "A vehicle arrives. Type the plate -- TI 123456."
- "Instantly: make, model, year, owner, insurance, current status."
- "This is MAX -- a Fiat Ducato campervan, currently in service for a major roof repair."
- "Full history, right from the plate number. No digging through folders."

---

## Scene 5: Vehicle Check-In -- New Vehicle (20s)
*Screen shows the "not found" state, then the registration form*

- "What about a vehicle you've never seen before?"
- "Type a new plate. Not found? Click to register."
- "Vehicle type, make, model, year -- plus customer details in one form."
- "One minute at the counter, and they're in the system. First-time visitor becomes a tracked customer."

---

## Scene 6: Job Board -- All Active Work (20s)
*Screen shows /camper/jobs with all jobs listed, filters visible*

- "The job board. Every job in the shop -- filterable by status, by mechanic, or free text search."
- "Color-coded status badges: gray for quoted, amber for in progress, red for waiting on parts, green for completed."
- "Nino can see at a glance: three jobs active, two quotes pending. Nobody has to ask what's going on."

---

## Scene 7: Job Detail -- MAX Roof Seal (30s)
*Screen shows /camper/jobs/{id} for the MAX seal inspection*

- "Let's open the big one. MAX -- full roof seal inspection."
- "The quote section shows estimated hours, parts cost, total."
- "The work section shows what's been done so far. Sixteen hours in, panels stripped, damage documented."
- "Parts on order -- PO number tracked."
- "Mechanic notes, customer notes, the full story in one place."
- "Follow-up scheduled for six months after repair. Nothing gets forgotten."

---

## Scene 8: Quote Approval + Status Workflow (20s)
*Screen shows Sophie's QUOTED gas inspection, then clicking Approve*

- "Sophie dropped off her Hymer for a gas system inspection. Status: Quoted."
- "Nino reviews the estimate. Clicks Approve. Status moves to Approved."
- "From here -- assign a mechanic, mark In Progress when work starts, mark Complete when it's done."
- "Quoted to Approved to In Progress to Completed to Invoiced. The full lifecycle, no paper trail."

---

## Scene 9: Customer Lookup (15s)
*Screen shows /camper/customers, search for "Angelo"*

- "Customer lookup. Search by name, phone, or email."
- "Angelo Kenel -- eight visits, twenty-four hundred euros total spend."
- "Expand to see vehicles owned and full service history."
- "Every customer touchpoint, every euro, tracked from day one."

---

## Scene 10: Outro Card (5s)
*Static recap card -- no voiceover during this shot.*

---

## Key Messages
- Replace Word documents and paper folders with searchable, trackable digital records
- Plate number search = instant vehicle history
- Job lifecycle from quote to invoice, fully visible
- Dashboard gives morning overview without asking around the shop
- Customer spend and visit history builds business intelligence
- Multi-language support (Italian, English, German, French) for tourist customers
- Role-based access: counter staff, mechanics, managers, admin

## Demo Credentials (Keycloak)
| User | Password | Role |
|------|----------|------|
| nino | helix_pass | camper-manager |
| simona | helix_pass | camper-counter |
| maximo | helix_pass | camper-mechanic |
| sebastino | helix_pass | camper-admin |
