# SCENE 008: The Garage — Mechanics, Plates, and Serial Numbers

## THE OPPORTUNITY

```
OLD SCHOOL GARAGE:
├─ Pen and paper
├─ Customer calls: "Is my car ready?"
├─ "Let me check..." *shuffles papers*
├─ Lost tickets
├─ No history: "Have we worked on this car before?"
├─ Plates and VINs scribbled on napkins
└─ MONEY LEFT ON THE TABLE

THE LION:
├─ CRM for vehicles (not just people)
├─ Plate → Customer → Vehicle history
├─ Serial numbers tracked
├─ Job status: customer can check online
├─ "Your 2019 Tesla Model 3 was last here 6 months ago"
├─ Upsell: "Your brakes were at 40% then..."
└─ MONEY CAPTURED
```

---

## THE CHARACTERS

```
TONY — "The Front Desk"
├─ Answers phone
├─ Checks in vehicles
├─ Explains work to customers
├─ Handles payments
├─ "Your car? Let me pull it up... VW Golf, right?"
└─ THE FACE

MIKE — "The Wrench"
├─ Under the hood
├─ Headset on (hands dirty, can't touch screen)
├─ "Tony, tell 'em it's the alternator, 2 hours"
├─ Knows every car he's ever touched
└─ THE MUSCLE

SARAH — "The Parts"
├─ Orders parts
├─ Tracks inventory
├─ "We got the filter, but alternator is 2 days out"
├─ Knows every supplier
└─ THE SUPPLY CHAIN
```

---

## THE DATA MODEL

```
CUSTOMERS:
├─ id
├─ name
├─ phone, email
├─ vehicles[] (one customer, many cars)
└─ visit_history[]

VEHICLES (The real asset):
├─ id
├─ customer_id
├─ plate_number (searchable!)
├─ vin (vehicle identification number)
├─ make (Tesla, Ford, BMW, Honda)
├─ model (Model 3, F-150, 320i, Civic)
├─ year
├─ color
├─ mileage_last_visit
├─ notes ("Customer says rattling when turning")
└─ service_history[]

JOBS (Work orders):
├─ id
├─ vehicle_id
├─ customer_id
├─ status (checked_in, diagnosing, waiting_parts, in_progress, ready, picked_up)
├─ mechanic_assigned
├─ problem_description
├─ diagnosis
├─ work_performed
├─ parts_used[]
├─ labor_hours
├─ parts_cost
├─ labor_cost
├─ total
├─ estimated_ready
├─ actual_ready
└─ paid

PARTS:
├─ id
├─ name
├─ part_number
├─ supplier
├─ cost
├─ markup
├─ quantity_in_stock
└─ reorder_threshold

SERVICE_HISTORY (Per vehicle):
├─ id
├─ vehicle_id
├─ date
├─ mileage
├─ work_performed
├─ parts_replaced
├─ next_service_due
└─ notes
```

---

## THE SCENES

### Scene A: Customer Calls

```
*Phone rings*

TONY: "Mike's Garage, Tony speaking."

CUSTOMER: "Hey, my Tesla is making a weird noise."

TONY: *types plate number*
      "That's the white Model 3, right?
       We did your brakes last March.
       You're at about 45,000 miles now?"

CUSTOMER: "Yeah, that's right. How'd you know?"

TONY: "It's in the system. When can you bring it in?"

CUSTOMER: "Tomorrow morning?"

TONY: *creates job*
      Status: SCHEDULED
      Problem: "Weird noise, customer reports"
      Time: Tomorrow 8am

      "See you at 8. We'll take a look."
```

### Scene B: Check-In

```
*Tomorrow 8am. Customer arrives.*

TONY: *scans plate with phone camera*
      System auto-fills:
      ├─ Customer: John Smith
      ├─ Vehicle: 2019 Tesla Model 3 White
      ├─ VIN: 5YJ3E1EA5KF...
      ├─ Mileage last: 42,350
      └─ Last service: Brakes, March 2024

TONY: "Mileage today?"

CUSTOMER: "45,200"

TONY: *updates*
      *prints ticket*
      *hands keys to Mike*

      "Mike will take a look. I'll call you
       when we know what's up."
```

### Scene C: Diagnosis (Headset)

```
*Mike under the car, headset on*

MIKE: "Tony, you there?"

TONY: "Yeah, what you got?"

MIKE: "It's the wheel bearing, front left.
       Part's about 180, plus 2 hours labor.
       Total around 450."

TONY: *updates job*
      Diagnosis: Wheel bearing, front left
      Parts: Wheel bearing kit - $180
      Labor: 2 hours @ $120 = $240
      Total estimate: $450

      *calls customer*

      "Mr. Smith? It's the wheel bearing.
       We can have it done by 3pm, $450 total.
       Want us to go ahead?"

CUSTOMER: "Yeah, do it."

TONY: *marks APPROVED*
      *checks parts inventory*
      "Sarah, we got a front wheel bearing for Model 3?"

SARAH: "Got one. Pulling it now."

TONY: *assigns part to job*
      *status: IN_PROGRESS*
```

### Scene D: Ready & Pickup

```
*2:30pm. Mike finishes.*

MIKE: "Tony, Model 3 is done."

TONY: *marks READY*
      *system auto-texts customer*

      📱 "Your 2019 Tesla Model 3 is ready
          for pickup. Total: $450"

*Customer arrives 4pm*

TONY: *pulls up job*
      "Wheel bearing replaced, test drove it,
       sounds good now. Here's what we did..."
      *shows service record on screen*

      "Total is $450. Cash or card?"

CUSTOMER: *pays*

TONY: *marks PAID*
      *marks PICKED_UP*
      *prints receipt with full service history*

      "Next service, I'd check those brakes.
       They were at 40% last time, probably
       due in another 10,000 miles."

CUSTOMER: "Thanks, Tony."
```

### Scene E: Proactive Follow-Up

```
*3 months later. System flags:*

┌─────────────────────────────────────┐
│ FOLLOW-UP DUE                       │
│ John Smith - Tesla Model 3          │
│ Brakes were at 40% (March)          │
│ Estimated due: ~55,000 miles        │
│ Current estimate: ~52,000 miles     │
│ ACTION: Call to schedule brake job  │
└─────────────────────────────────────┘

TONY: *calls*
      "Mr. Smith? Tony from Mike's Garage.
       Just wanted to check - how are those
       brakes feeling? We noted they were
       getting low last time..."

CUSTOMER: "Actually yeah, they've been squeaking."

TONY: "Want to bring it in this week?
       I can get you in Thursday."

*UPSELL COMPLETE. CUSTOMER HAPPY.*
```

---

## THE OLD SCHOOL vs THE LION

```
OLD SCHOOL (Pen & Paper):
├─ "Who's car is this?" *checks clipboard*
├─ "Have we seen this before?" *digs through files*
├─ "Is it ready?" "Let me check with Mike..."
├─ Lost tickets
├─ Forgotten follow-ups
├─ No upsell opportunities
└─ REACTIVE

THE LION (Helix Garage):
├─ Scan plate → instant customer + vehicle
├─ Full history in 2 seconds
├─ Real-time status updates
├─ Auto-text when ready
├─ Proactive service reminders
├─ "Your brakes were at 40%..."
└─ PROACTIVE = MORE REVENUE
```

---

## COMPLIANCE & TRACKING

```
WHAT REGULATORS WANT:
├─ VIN tracking (theft prevention)
├─ Parts sourcing (recall tracking)
├─ Disposal records (oil, fluids)
├─ Customer consent records
└─ Service history (warranty disputes)

WHAT HELIX TRACKS:
├─ Every VIN that enters
├─ Every part used (by serial if needed)
├─ Every service performed
├─ Full audit trail
└─ Export for inspectors

TESLA SPECIFIC:
├─ Software version tracking
├─ OTA update history
├─ Battery health records
├─ Supercharger usage (if shared)
└─ Warranty status integration
```

---

## STACK FOR GARAGE

```
MINIMAL (Mom & Pop shop):
├─ Postgres
├─ Traefik
├─ Garage API
├─ €10/month
└─ Tony's tablet + Mike's headset

FULL (Multi-bay shop):
├─ Add: Redis (real-time job board)
├─ Add: SMS integration (Twilio)
├─ Add: Parts API (AutoZone, NAPA)
├─ €50/month
└─ Wall-mounted job board display

CHAIN (Multiple locations):
├─ Add: Keycloak (multi-user auth)
├─ Add: Reporting dashboard
├─ Add: Inventory sync across locations
├─ €200/month
└─ Corporate can see all shops
```

---

## THE FILL STATION (Gas Station + Convenience)

```
SIMILAR PATTERN:
├─ POS for convenience store (we have this)
├─ Pump integration (API to pump controller)
├─ Loyalty (frequent fill discounts)
├─ Fleet accounts (business fuel cards)
└─ YAGNI: Start with store, add pumps later
```

---

## THE MOLESKIN TO DIGITAL FLOW

```
MARIO'S CURRENT:
├─ Moleskin notebook
├─ Pen
├─ iPhone (photos, calls)
├─ Customer convo → digest → capture essentials

THE BRIDGE:
├─ Voice memo → transcribe → structured data
├─ Photo of site → attached to job
├─ Moleskin sketch → photo → attached
└─ Don't replace the Moleskin. AUGMENT it.

YAGNI:
├─ Mario keeps his Moleskin (it works)
├─ After convo: 2 min to enter essentials
├─ Photo of Moleskin page = backup
└─ System handles the rest
```

---

## HOW FAR CAN WE GO?

```
TODAY:
├─ Retail POS (Artemis) ✓
├─ HR/Payroll ✓
├─ Sourcing ✓
├─ Customer loyalty ✓
├─ Knowledge base ✓

PROVEN POSSIBLE:
├─ Excavation (Dave & Mario scene)
├─ Leather workshop (Snake Skins scene)
├─ Garage/Mechanics (this scene)
├─ Fill stations

NEXT:
├─ Dental office (appointments + patient records)
├─ Law firm (cases + billing + docs)
├─ Restaurant (tables + orders + kitchen)
├─ Gym (members + classes + equipment)
├─ Property management (units + tenants + maintenance)

THE PATTERN IS THE SAME:
├─ Characters (who)
├─ Scenes (what happens)
├─ Data (what to track)
├─ Stack (minimal that works)
└─ YAGNI (add only when needed)
```

---

*Tony handles the front.
Mike handles the cars.
Sarah handles the parts.
The system handles the memory.*

*Be water. Flow like oil through an engine.* 🔧

---

**What gift are you getting for Mario's wife?**
