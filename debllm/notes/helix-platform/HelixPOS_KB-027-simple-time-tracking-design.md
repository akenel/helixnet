# KB-027: Simple Time Tracking - The BLQ Approach

**Created**: 2024-11-30 (In the car, on the way to the show)
**Author**: Angel (back seat notes)
**Status**: DESIGN SKETCH

---

## The Insight (Felix in the car)

> "My system is simple but it's still a ton of numbers to add up for 5 employees... it still takes me a few hours to do the monthly payroll even with my spreadsheet."

> "If you get that HelixNet of yours to do time tracking you could save me time."

---

## What Felix Actually Needs

NOT a full HR system. Just:

```
┌─────────────────────────────────────────────────────────┐
│  SHIFT LOG - Simple as possible                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Employee: Pam                                          │
│  Date: 2024-11-30                                       │
│                                                         │
│  Clock In:  08:55                                       │
│  Clock Out: 17:32                                       │
│  Break:     30 min (lunch, in back room)                │
│                                                         │
│  Worked:    8h 07m                                      │
│  Sales:     CHF 423.50 (6 transactions)                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

That's it. No AHV numbers. No IBAN. No sick day calculations. Just:
- **Start time**
- **End time**
- **Break deduction**
- **Hours worked**
- **Sales during shift**

---

## Felix's Spreadsheet Still Does the Hard Work

```
HelixNet exports:           Felix's spreadsheet calculates:
─────────────────           ────────────────────────────────
Employee name               AHV contributions
Date                        IBAN payments
Hours worked                80% sick day adjustments
Total sales                 Tax withholdings
                            Lohnausweis generation
```

**HelixNet = Time clock + Sales**
**Spreadsheet = Payroll math**

---

## The 30-Minute Lunch Rule (Felix to Leandra)

> "We include 30 minute break for lunch but we don't close the shop at lunchtime so you still work and eat your sandwiches in the back, not here at the checkout. Same goes for croissants and coffees - please do that in the back room. If you hear the bell ring that means a customer just walked in so please swallow food first and then go immediately to the front."

**Implementation**:
- Auto-deduct 30 min for shifts > 6 hours
- Or manual "break start/end" buttons
- Keep it simple - default 30 min

---

## Data Model (Minimal)

```sql
CREATE TABLE shifts (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),

    -- Time tracking
    clock_in TIMESTAMP NOT NULL,
    clock_out TIMESTAMP,
    break_minutes INT DEFAULT 30,

    -- Calculated
    hours_worked DECIMAL(5,2),  -- e.g., 8.12 hours

    -- Link to sales
    transactions_count INT DEFAULT 0,
    sales_total DECIMAL(10,2) DEFAULT 0,

    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- active, completed, sick
    notes TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## UI: Clock In / Clock Out

```
┌─────────────────────────────────────────────┐
│  👋 Good morning, Pam!                      │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │                                     │    │
│  │       🕐 CLOCK IN                   │    │
│  │                                     │    │
│  │       Tap to start your shift       │    │
│  │                                     │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  Yesterday: 8h 15m | CHF 512.30            │
└─────────────────────────────────────────────┘
```

After clock in:
```
┌─────────────────────────────────────────────┐
│  🟢 Pam - ON SHIFT since 08:55              │
│                                             │
│  Current shift: 2h 34m                      │
│  Sales so far: CHF 145.00 (3 sales)         │
│                                             │
│  [🍽️ Take Break]  [🏁 Clock Out]            │
└─────────────────────────────────────────────┘
```

---

## Daily Closeout - The 1-Pager Felix Wants

```
═══════════════════════════════════════════════════════════
DAILY CLOSEOUT - Artemis Luzern - 2024-11-30 (Saturday)
═══════════════════════════════════════════════════════════

STAFF SUMMARY
─────────────────────────────────────────────────────────
Employee     In      Out     Break   Worked   Sales
─────────────────────────────────────────────────────────
Pam          08:55   17:32   30m     8h 07m   CHF 423.50
Ralph        09:00   18:05   30m     8h 35m   CHF 567.20
Leandra      10:00   16:30   30m     6h 00m   CHF 234.00
─────────────────────────────────────────────────────────
TOTAL                               22h 42m   CHF 1,224.70

CASH RECONCILIATION
─────────────────────────────────────────────────────────
Opening float:     CHF 200.00
Cash sales:        CHF 789.00
Card sales:        CHF 435.70
Expected drawer:   CHF 989.00
Actual count:      CHF 987.50
Variance:          CHF -1.50 ⚠️

═══════════════════════════════════════════════════════════
```

**This is what Felix copies into his spreadsheet.** One page per day.

---

## Export Format for Felix's Spreadsheet

Monthly CSV:
```csv
Date,Employee,Clock In,Clock Out,Break,Hours,Sales
2024-11-01,Pam,08:55,17:32,30,8.12,423.50
2024-11-01,Ralph,09:00,18:05,30,8.58,567.20
2024-11-02,Pam,09:00,17:00,30,7.50,356.00
...
```

Felix imports this into his master spreadsheet → payroll calculations done.

---

## What This Solves

| Problem | Solution |
|---------|----------|
| "Takes me hours to add up numbers" | Auto-calculated hours |
| "30 minute lunch break" | Auto-deducted |
| "Who sold what" | Linked to transactions |
| "Monthly payroll input" | CSV export |
| "Daily closeout" | 1-page summary |

## What This Does NOT Solve (Still Felix's Spreadsheet)

- AHV calculations
- Sick day 80% adjustments
- Tax withholdings
- IBAN payments
- Lohnausweis

---

## Mosey's Scale (50-60 people)

This simple system could work for Mosey's 5 retail stores, but:
- His wholesale B2B is different
- His contractor management needs more
- His 2 full-time payroll people do more than time tracking

**Verdict**: Good for Felix (5 people), maybe useful for Mosey's retail stores, not a replacement for his payroll team.

---

## Next Steps

1. [ ] Add `shifts` table to database
2. [ ] Clock in/out buttons on POS login screen
3. [ ] Link shifts to transactions (who sold during their shift)
4. [ ] Daily closeout report with time + sales
5. [ ] CSV export for Felix's spreadsheet

---

*Felix pulls into the show parking lot. 11:03 AM. Only 3 minutes late.*

> **Felix**: "See? We made it. No need to rush."
> **Mosey**: "You drive like my employees work - fast but sloppy."
> **Angel**: *(closes notebook)* "I think I've got an idea..."
