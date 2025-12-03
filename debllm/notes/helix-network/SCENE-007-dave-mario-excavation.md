# SCENE 007: Dave & Mario — Excavation & Landscaping

## THE BUSINESS

```
DAVE — "The Face"
├─ Handles ALL customers
├─ Customers LOVE Dave
├─ Estimates, scheduling, follow-up
├─ The relationship guy
└─ "2-3 front yards, 1-2 big pools"

MARIO — "The Muscle"
├─ Digs. That's it. Digs.
├─ Runs the excavator
├─ Manages the crew (3-5 men)
├─ Equipment maintenance
└─ "You point, I dig"

THE CREW (3-5 max):
├─ Laborers
├─ Equipment operators
├─ Seasonal / per-job
└─ Paid by job or day
```

---

## WHAT THEY NEED (NOT A POS)

```
JOB MANAGEMENT:
├─ Quote → Approved → Scheduled → In Progress → Done → Invoiced
├─ Photos of site (before/after)
├─ Notes per job
└─ Customer history

EQUIPMENT TRACKING:
├─ Excavator (where is it?)
├─ Bobcat
├─ Trailer
├─ Tools (shovels, rakes, etc.)
└─ Maintenance schedule

CREW SCHEDULING:
├─ Who's on which job?
├─ Availability calendar
├─ Day rate tracking
└─ Contact info

CUSTOMER MANAGEMENT:
├─ Dave's relationships
├─ Property addresses
├─ Job history per customer
├─ Payment history
└─ "BBQ and pool customers"

SIMPLE INVOICING:
├─ Quote (estimate)
├─ Job completion
├─ Invoice generation
├─ Payment tracking
└─ No payment processing (checks/cash)
```

---

## THE SCENES

### Scene A: New Lead Comes In

```
DAVE's phone rings.

CUSTOMER: "Hey Dave, Mike referred me.
           I need my backyard dug out for a pool."

DAVE: *opens app on phone*
      *taps "New Job"*

      Customer: Johnson
      Property: 45 Oak Street
      Type: Pool excavation
      Referred by: Mike
      Notes: "Backyard, needs site visit"

      *saves*

DAVE: "I can come by Thursday for a look.
       Morning or afternoon?"

CUSTOMER: "Morning works."

DAVE: *schedules site visit*

      "See you Thursday 9am, Mr. Johnson."
```

### Scene B: Site Visit & Quote

```
Thursday 9am. Dave at Johnson property.

DAVE: *opens job on phone*
      *takes photos of backyard*
      *measures area*
      *notes obstacles: old shed, tree stump*

      Estimate:
      ├─ Excavation: 2 days
      ├─ Crew: Mario + 2
      ├─ Equipment: Excavator, Bobcat
      ├─ Disposal: 3 truckloads
      └─ Total: CHF 8,500

      *sends quote to customer via app*

CUSTOMER: *reviews on email*
          "Looks good. When can you start?"

DAVE: *checks Mario's schedule*
      "Next Tuesday work?"

CUSTOMER: "Done."

DAVE: *marks job APPROVED*
      *schedules for Tuesday*
      *assigns Mario + 2 crew*
      *reserves equipment*
```

### Scene C: Job Day

```
Tuesday 7am. Mario gets notification.

MARIO's phone:
┌─────────────────────────────┐
│ JOB TODAY                   │
│ Johnson - Pool Excavation   │
│ 45 Oak Street               │
│ Equipment: Excavator, Bobcat│
│ Crew: Mario, Luis, Pedro    │
│ Est. 2 days                 │
└─────────────────────────────┘

MARIO: *checks equipment status*
       Excavator: At yard ✓
       Bobcat: At Miller job (yesterday)

       *calls Luis*
       "Pick up Bobcat from Miller,
        meet me at Oak Street."

*On site*

MARIO: *starts job*
       *logs hours*
       *takes progress photos*
       *notes: "Hit old pipe, had to reroute"*
```

### Scene D: Job Complete & Invoice

```
Wednesday 4pm. Job done.

MARIO: *marks job COMPLETE*
       *uploads final photos*
       *logs: 2 days, as estimated*

DAVE: *gets notification*
      *reviews photos*
      *calls customer*

      "All done, Mr. Johnson! Take a look
       and let me know if you're happy."

CUSTOMER: "Looks great!"

DAVE: *generates invoice*
      *sends via email*

      Invoice #2024-047
      Johnson Pool Excavation
      ────────────────────
      Excavation (2 days)    7,500
      Disposal (3 loads)     1,000
      ────────────────────
      Total:                 8,500 CHF

      Payment: 30 days
      Method: Bank transfer

CUSTOMER: *pays next week*

DAVE: *marks PAID*
      *job archived*
```

---

## THE DATA MODEL (Simple)

```
CUSTOMERS:
├─ id
├─ name
├─ phone, email
├─ addresses[] (can have multiple properties)
├─ referred_by
├─ notes
└─ jobs[] (history)

JOBS:
├─ id
├─ customer_id
├─ property_address
├─ type (excavation, landscaping, pool, fence, deck, etc.)
├─ status (lead, quoted, approved, scheduled, in_progress, complete, invoiced, paid)
├─ quote_amount
├─ actual_amount
├─ scheduled_date
├─ crew_assigned[]
├─ equipment_needed[]
├─ photos[]
├─ notes
└─ invoice_id

EQUIPMENT:
├─ id
├─ name (Excavator CAT 320, Bobcat S650, etc.)
├─ type (excavator, loader, trailer, tool)
├─ status (available, on_job, maintenance)
├─ current_location (yard, job_id, shop)
├─ maintenance_due
└─ notes

CREW:
├─ id
├─ name
├─ phone
├─ role (operator, laborer)
├─ day_rate
├─ availability
└─ assigned_jobs[]

INVOICES:
├─ id
├─ job_id
├─ customer_id
├─ amount
├─ status (sent, paid, overdue)
├─ due_date
├─ paid_date
└─ payment_method
```

---

## WHAT THEY DON'T NEED

```
❌ POS system (no retail)
❌ Inventory management (equipment, not products)
❌ Customer loyalty/points (B2B relationships)
❌ Multiple registers (it's Dave's phone)
❌ Real-time sync (jobs are days, not seconds)
❌ Complex auth (Dave + Mario, that's it)
```

---

## THE MINIMAL STACK FOR DAVE & MARIO

```yaml
services:
  postgres:
    # Their data

  traefik:
    # HTTPS access

  excavation-api:
    # FastAPI with:
    # - /jobs endpoints
    # - /customers endpoints
    # - /equipment endpoints
    # - /crew endpoints
    # - /invoices endpoints

# TOTAL RAM: ~1GB
# COST: €5-10/month
# RUNS ON: Dave's laptop as server, or cheap VPS
```

---

## WHY THIS WORKS FOR THEM

```
DAVE:
├─ Sees all jobs on phone
├─ Creates quotes in 2 minutes
├─ Customer history at fingertips
├─ "Johnson? Yeah, did his neighbor's pool last year"
└─ THE RELATIONSHIP STAYS WITH DAVE

MARIO:
├─ Knows what's scheduled
├─ Knows where equipment is
├─ Logs hours and progress
├─ Takes photos for records
└─ THE DIGGING STAYS WITH MARIO

BOTH:
├─ No paperwork
├─ No lost quotes
├─ No "where's the excavator?"
├─ No "did we invoice Johnson?"
└─ JUST WORK
```

---

*Dave handles the customers.
Mario handles the ground.
The system handles the paperwork.
Water finds its level.*

---

**BUILD IT?**
