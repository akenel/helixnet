# Camper & Tour -- EP2 "Quote to Invoice"

## Overview
- **Target audience:** Nino, Sebastino, prospective camper service shops
- **Language:** English (base), Italian labels visible on-screen
- **Runtime:** ~3-4 minutes
- **Focus:** The money flow -- from formal quotation to paid invoice

---

## Scene 1: Intro Card (5s)
*Static title card -- no voiceover during this shot.*

---

## Scene 2: Quotation List (20s)
*Screen shows /camper/quotations with all quotations listed by status*

- "In Episode One, we saw how vehicles come in and jobs get created."
- "Now we follow the money. It starts with a quotation."
- "Every quote gets a sequential number -- QUO-20260214-0001. No duplicates. No hand-written forms."
- "Status at a glance: draft, sent, accepted, rejected."

---

## Scene 3: Quotation Detail -- Line Items (30s)
*Screen shows /camper/quotations/{id} with line items, IVA calculation, deposit*

- "Let's open the MAX roof seal quotation."
- "Line items: each repair task with description, hours, and cost."
- "The system calculates IVA at twenty-two percent automatically."
- "Below that -- the deposit. Twenty-five percent of the total, calculated on acceptance."
- "Click Send -- the customer gets an email in Italian with the full breakdown."
- "When they accept, the deposit requirement is locked in. The job moves to Approved."

---

## Scene 4: Purchase Orders (25s)
*Screen shows /camper/purchase-orders with PO list and status tracking*

- "Parts on order. Every supplier gets a formal purchase order."
- "PO status tracks the full lifecycle: draft, sent, confirmed, shipped, received."
- "When parts arrive, mark received -- the job's 'waiting for parts' flag clears automatically."
- "No more calling the supplier to ask 'where are my parts?' -- the status is right here."

---

## Scene 5: Invoice Generation (25s)
*Screen shows /camper/invoices, then opens an invoice generated from a completed job*

- "Job complete. Time to get paid."
- "One click generates an invoice from the completed job."
- "The deposit is already deducted. The balance due is calculated automatically."
- "Payment tracking: pending, deposit paid, partial, paid, overdue."
- "Every euro from quote to cash -- tracked and auditable."

---

## Scene 6: Calendar View (20s)
*Screen shows /camper/calendar with jobs plotted across dates*

- "The calendar. Jobs scheduled across the week."
- "Nino sees capacity at a glance -- which days are full, which have room."
- "Click any job to jump straight to the detail."

---

## Scene 7: Bay Timeline (25s)
*Screen shows /camper/bay-timeline with CSS Grid resource view across 5 bays*

- "Five service bays. General, Electrical, Mechanical, Bodywork, Wash."
- "The bay timeline shows which vehicle is in which bay, across the week."
- "Overlap detection built in -- you can't double-book a bay."
- "This is how Nino plans tomorrow's work tonight."

---

## Scene 8: Appointments (20s)
*Screen shows /camper/appointments with booked and walk-in queue*

- "Appointments and walk-ins on the same screen."
- "Booked customers show first -- they reserved their spot."
- "Walk-ins join the queue below, sorted by arrival time."
- "Status moves through the lifecycle: scheduled, waiting, in service, completed."

---

## Scene 9: Outro Card (5s)
*Static recap card -- no voiceover during this shot.*

---

## Key Messages
- Formal quotations with sequential numbering eliminate hand-written forms
- IVA 22% and 25% deposit calculated automatically -- no math errors
- Purchase order tracking closes the "where are my parts?" loop
- Invoice generation from completed jobs -- deposit already deducted
- Calendar and bay timeline give capacity planning without a whiteboard
- Appointments separate booked from walk-in, keeping the queue fair

## Demo Credentials (Keycloak)
| User | Password | Role | Access |
|------|----------|------|--------|
| nino | helix_pass | camper-manager | Full shop management |
| simona | helix_pass | camper-counter | Check-in + customers |
| maximo | helix_pass | camper-mechanic | Jobs + work logging |
| sebastino | helix_pass | camper-admin | Everything + settings |

## Recording Instructions
Record each scene as a separate Telegram voice message. One scene = one clip. Pause between sentences for natural pacing.

Scene timing guide:
| Scene | Duration | Lines |
|-------|----------|-------|
| 1 - Intro Card | 5s | No recording |
| 2 - Quotation List | 20s | 4 lines |
| 3 - Quotation Detail | 30s | 6 lines |
| 4 - Purchase Orders | 25s | 4 lines |
| 5 - Invoice Generation | 25s | 5 lines |
| 6 - Calendar View | 20s | 3 lines |
| 7 - Bay Timeline | 25s | 4 lines |
| 8 - Appointments | 20s | 4 lines |
| 9 - Outro Card | 5s | No recording |
| **Total** | **~2:55 voice** | **30 lines, 7 clips** |
