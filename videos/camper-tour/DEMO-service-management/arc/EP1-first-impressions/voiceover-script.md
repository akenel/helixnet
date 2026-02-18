# Camper & Tour -- EP1 "First Impressions"

## Overview
- **Target audience:** Nino, Sebastino, prospective camper service shops
- **Language:** English (base), Italian labels visible on-screen
- **Runtime:** ~3-4 minutes
- **Demo data:** 4 customers, 4 vehicles, 5 jobs (MAX seal story is REAL)

---

## Scene 1: Intro Card (5s)
*Static title card -- no voiceover during this shot.*

---

## Scene 2: Login & Dashboard (25s)
*Screen shows the Camper & Tour login page at /camper, then the dashboard with 4 stat cards and active jobs table*

- "This is Camper and Tour -- a service management system built for camper repair shops."
- "We're logging in as Nino, the shop manager, through Keycloak single sign-on."
- "Every morning, Nino opens one screen."
- "Four numbers: vehicles in the shop, active jobs, parts on order, pending quotes."
- "Below that -- every active job at a glance. Who's working on what, and the current status."
- "No paper shuffling. No asking around the shop."

---

## Scene 3: Vehicle Check-In (25s)
*Screen shows /camper/checkin, types "TI 123456", then tries a new plate*

- "A vehicle arrives. Type the plate -- TI 123456."
- "Instantly: make, model, year, owner, insurance, current status."
- "This is MAX -- a Fiat Ducato campervan, currently in for a major roof repair."
- "What about a vehicle you've never seen before?"
- "Type a new plate. Not found? Click to register."
- "One minute at the counter. First-time visitor becomes a tracked customer."

---

## Scene 4: Job Board (20s)
*Screen shows /camper/jobs with all jobs listed, filters and search visible*

- "The job board. Every job in the shop."
- "Filter by status -- show only what's in progress."
- "Search by name -- find MAX instantly."
- "Color-coded badges: gray for quoted, amber for in progress, red for waiting on parts, green for done."
- "Nino sees at a glance: who needs what, right now."

---

## Scene 5: Job Detail -- MAX Roof Seal (35s)
*Screen shows /camper/jobs/{id} for the MAX seal inspection -- the MONEY SHOT*

- "Let's open the big one. MAX -- full roof seal inspection."
- "The deposit section: how much was required, how much has been paid."
- "The quote shows estimated hours and parts cost."
- "The work section -- sixteen hours in, panels stripped, damage documented."
- "Parts on order, PO number tracked."
- "Mechanic notes, customer notes, the full story in one place."
- "Follow-up scheduled for six months after repair. Nothing gets forgotten."
- "This is a real job. This damage was real. The system tracked every step."

---

## Scene 6: Customer Intelligence (20s)
*Screen shows /camper/customers, search for "Angelo"*

- "Customer lookup. Search by name."
- "Angelo Kenel -- eight visits, twenty-four hundred euros total spend."
- "Expand to see vehicles owned and full service history."
- "Every customer, every vehicle, every euro -- tracked from day one."

---

## Scene 7: Outro Card (5s)
*Static recap card -- no voiceover during this shot.*

---

## Key Messages
- Replace paper folders and Word documents with searchable, trackable digital records
- Plate number search gives instant vehicle history -- no digging through files
- Job lifecycle from quote to invoice, fully visible on one screen
- Dashboard gives the morning overview without asking around the shop
- Customer spend and visit history builds business intelligence over time
- The MAX roof seal story is real -- the system tracked a real repair from day one

## Demo Credentials (Keycloak)
| User | Password | Role | Access |
|------|----------|------|--------|
| nino | helix_pass | camper-manager | Full shop management |
| simona | helix_pass | camper-counter | Check-in + customers |
| maximo | helix_pass | camper-mechanic | Jobs + work logging |
| sebastino | helix_pass | camper-admin | Everything + settings |

## Recording Instructions
Record each scene as a separate Telegram voice message. One scene = one clip. Pause between sentences for natural pacing. Speak slowly -- the voiceover will be time-stretched to fit the video if needed, but it is easier to slow down a fast recording than to speed up a slow one.

Scene timing guide:
| Scene | Duration | Clips |
|-------|----------|-------|
| 1 - Intro Card | 5s | No recording |
| 2 - Login & Dashboard | 25s | 6 lines |
| 3 - Vehicle Check-In | 25s | 6 lines |
| 4 - Job Board | 20s | 5 lines |
| 5 - Job Detail (MAX) | 35s | 8 lines |
| 6 - Customer Intelligence | 20s | 4 lines |
| 7 - Outro Card | 5s | No recording |
| **Total** | **~2:15 voice** | **29 lines, 5 clips** |
