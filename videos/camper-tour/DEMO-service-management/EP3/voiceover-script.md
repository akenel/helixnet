# Camper & Tour -- EP3 "The Full Lifecycle"

## Overview
- **Target audience:** Nino, Sebastino, prospective camper service shops
- **Language:** English (base), Italian labels visible on-screen
- **Runtime:** ~3 minutes
- **Focus:** One job, start to finish. Three roles. RBAC in action.

---

## Scene 1: Intro Card (5s)
*Static title card -- no voiceover during this shot.*

---

## Scene 2: Simona -- Counter Check-In (30s)
*Login as Simona (camper-counter). Show /camper/checkin, type a plate, register new vehicle + customer.*

- "A camper pulls up to the shop. Simona is at the counter."
- "She logs in with her own account. She's a counter -- check-in and customers only."
- "She types the plate. New vehicle. One minute to register."
- "Vehicle and customer created. Simona's job is done."
- "Notice what's missing from her menu -- no Quotations, no Invoices, no Purchase Orders. Counter role. Clean screen."

---

## Scene 3: Simona -- Access Denied (15s)
*Show that Simona CANNOT access quotations or invoices. Navigate to /camper/quotations -- access denied.*

- "What if Simona tries to access quotations?"
- "Access denied. The system enforces it. No grey areas."
- "Every role sees exactly what they need. Nothing more."

---

## Scene 4: Nino -- Create Quotation (30s)
*Login as Nino (camper-manager). Show /camper/jobs, create new job, then /camper/quotations to create a quote with line items.*

- "Nino takes over. Manager role -- he sees everything Simona sees, plus financials."
- "He opens the new vehicle's check-in and creates a job."
- "Then he builds a quotation. Line items, labour hours, parts."
- "IVA twenty-two percent. Deposit twenty-five percent. Calculated automatically."
- "He sends the quote to the customer."

---

## Scene 5: Nino -- Approve Job (15s)
*Customer accepts. Nino clicks Approve. Job moves to APPROVED. Deposit recorded.*

- "The customer accepts. Nino approves the job."
- "Deposit recorded. Job status moves to Approved."
- "The mechanic can now see this job on their board."

---

## Scene 6: Maximo -- Mechanic Work Log (30s)
*Login as Maximo (camper-mechanic). Show /camper/jobs -- only sees jobs assigned to him. Open job, log work hours, add notes.*

- "Maximo is the mechanic. He logs in -- different screen."
- "He sees his assigned jobs. Not Nino's management views. Not Simona's counter."
- "He opens the job, logs his hours. Eight-thirty to twelve. Panel removal, seal inspection."
- "Mechanic notes: what he found, what he needs."
- "Notice: Maximo cannot approve jobs, cannot create invoices. Mechanic role. Hands on the vehicle, not the books."

---

## Scene 7: Maximo -- Submit for Inspection (10s)
*Maximo clicks Submit for Inspection. Job status moves to INSPECTION.*

- "Work complete. Maximo submits for inspection."
- "The job moves to Nino's inspection queue."

---

## Scene 8: Nino -- Inspection & Complete (20s)
*Login as Nino. Show the job in INSPECTION status. Pass inspection. Job moves to COMPLETED.*

- "Back to Nino. The job is waiting for inspection."
- "He reviews the work, checks the mechanic's notes."
- "Inspection passed. Job status: Completed."

---

## Scene 9: Nino -- Generate Invoice (20s)
*Nino generates invoice from completed job. Deposit deducted. Balance due shown.*

- "One click. Invoice generated from the completed job."
- "Deposit already deducted. Balance due calculated."
- "Customer gets the invoice. Payment tracked."

---

## Scene 10: Nino -- Vehicle Pickup (10s)
*Mark vehicle as picked up. Check-out with mileage. Job fully closed.*

- "Vehicle picked up. Check-out recorded."
- "From check-in to pickup -- every step tracked, every role enforced."

---

## Scene 11: Outro Card (5s)
*Static recap card -- no voiceover during this shot.*

---

## Key Messages
- Three roles, three different screens -- counter, manager, mechanic
- Each role sees exactly what they need, nothing more
- Access denied is a feature, not a bug -- it prevents mistakes
- Full job lifecycle: check-in, quote, approve, work, inspect, invoice, pickup
- 8 workflow steps, zero paper
- The system enforces the process -- humans focus on the work

## Demo Credentials (Keycloak)
| User | Password | Role | Access |
|------|----------|------|--------|
| simona | helix_pass | camper-counter | Check-in + customers only |
| nino | helix_pass | camper-manager | Full shop management + financials |
| maximo | helix_pass | camper-mechanic | Jobs + work logging only |
| sebastino | helix_pass | camper-admin | Everything + settings |

## Recording Instructions
Record each scene as a separate Telegram voice message. One scene = one clip.

Scene timing guide:
| Scene | Duration | Lines |
|-------|----------|-------|
| 1 - Intro Card | 5s | No recording |
| 2 - Simona Check-In | 30s | 5 lines |
| 3 - Simona Access Denied | 15s | 3 lines |
| 4 - Nino Create Quotation | 30s | 5 lines |
| 5 - Nino Approve Job | 15s | 3 lines |
| 6 - Maximo Work Log | 30s | 5 lines |
| 7 - Maximo Submit Inspection | 10s | 2 lines |
| 8 - Nino Inspection | 20s | 3 lines |
| 9 - Nino Invoice | 20s | 3 lines |
| 10 - Nino Vehicle Pickup | 10s | 2 lines |
| 11 - Outro Card | 5s | No recording |
| **Total** | **~3:10 voice** | **31 lines, 9 clips** |
