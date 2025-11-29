# KB-033: Employee Value Tracking - Beyond Time

**Created**: 2024-11-30 (Bench outside the demo hall)
**Author**: Angel + Felix brainstorm
**Status**: DESIGN - New feature concept

---

## Felix's Current System (The Colored Books)

```
📗 GREEN BOOK: Daily sales log
📘 BLUE BOOK: Employee hours
📕 RED BOOK: Products, notes, personal info
```

**Works. BLQ. But almost too basic.**

---

## The Problem with Pure Time Tracking

> "Employees are my biggest expense and I have ZERO performance KPIs."

Traditional time tracking answers: "How long were you here?"
But not: "What value did you create?"

---

## Felix's Insight

> "Maybe the employee with the most or best KBs... or the most helpful KB of the month... it might encourage them to create quality KBs and start thinking SYSTEMS, METHODS... ways of working."

**Shift from**: Track time → Track value
**Shift from**: Hours worked → Knowledge created

---

## Simple Time Entry (Still Needed)

### Requirements
1. Employee enters start time and end time
2. No calculations required from employee
3. System validates entries

### Validation Rules

```
┌─────────────────────────────────────────────────────────────┐
│  SANITY CHECKS                                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚠️ Pam entered 19:00 end time (meant 9pm/21:00)           │
│     → "Did you mean 21:00? 19 hours seems too long."        │
│                                                             │
│  ⚠️ Max normal shift: 9 hours                               │
│     → Warn if exceeded (allow override for events)          │
│                                                             │
│  ⚠️ Shop hours: Thursday 11am-8pm                           │
│     → "Start time 08:00 is before shop opens at 11:00"      │
│                                                             │
│  ⚠️ Future dates                                            │
│     → Can't log time for tomorrow                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Shop Hours Reference

| Day | Hours | Notes |
|-----|-------|-------|
| Monday | 11:00-19:00 | |
| Tuesday | 11:00-19:00 | |
| Wednesday | 11:00-19:00 | |
| Thursday | 11:00-20:00 | Late night |
| Friday | 11:00-19:00 | |
| Saturday | 10:00-17:00 | Early start |
| Sunday | Closed | |

---

## The Value Tracking Layer (The New Idea)

### What We Can Measure

```
TIME (Blue Book)              VALUE (New!)
──────────────                ─────────────
Hours worked                  KBs created
Days present                  KBs referenced by others
Overtime events               Sales during shift
                              Problems solved
                              Training others
```

### KB Contribution Tracking

| Metric | What It Means |
|--------|---------------|
| KBs Authored | Employee created new knowledge |
| KBs Updated | Employee improved existing knowledge |
| KB Views | How often their KBs are read |
| KB References | Others citing their KB in solutions |
| KB of the Month | Community-voted best contribution |

---

## Gamification: KB Leaderboard

```
═══════════════════════════════════════════════════════════════
           ARTEMIS KNOWLEDGE CHAMPIONS - November 2024
═══════════════════════════════════════════════════════════════

🥇 Pam
   └── 3 KBs authored (KB-004, KB-010, KB-020)
   └── 47 KB views this month
   └── ⭐ KB of the Month: Age Verification Workflow

🥈 Felix
   └── 5 KBs authored (KB-001, KB-002, KB-021, KB-022, KB-023)
   └── 89 KB views this month
   └── Most Referenced: Headshop 101

🥉 Ralph
   └── 1 KB authored (KB-019 draft)
   └── 12 KB views this month
   └── Rising Star: First contribution!

   Leandra
   └── 0 KBs yet (new hire, learning)
   └── 23 KBs read this month
   └── 🎯 Challenge: Write your first KB!

═══════════════════════════════════════════════════════════════
```

---

## The Shift + Value Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  PAM - Saturday Nov 30, 2024                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⏰ TIME                                                    │
│  ├── Shift: 10:00 - 17:00 (7h, 30m break = 6h 30m)         │
│  └── Status: ✅ Normal (within shop hours)                  │
│                                                             │
│  💰 SALES                                                   │
│  ├── Transactions: 8                                        │
│  ├── Total: CHF 423.50                                      │
│  └── Avg: CHF 52.94/sale                                    │
│                                                             │
│  📚 KNOWLEDGE                                               │
│  ├── KBs referenced today: 2                                │
│  │   └── KB-004 (CBD Compliance) - helped customer         │
│  │   └── KB-002 (Volcano) - answered tech question         │
│  ├── KB contribution: None today                            │
│  └── Streak: 3 days since last KB update                   │
│                                                             │
│  🎯 SUGGESTION                                              │
│  └── "You answered a Volcano question - add it to KB-002?" │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema (Simple)

```sql
-- Shifts table (time tracking)
CREATE TABLE shifts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    shift_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME,
    break_minutes INT DEFAULT 30,
    hours_worked DECIMAL(4,2),  -- calculated
    is_overtime BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Prevent duplicate shifts per day
    UNIQUE(user_id, shift_date)
);

-- KB contributions tracking
CREATE TABLE kb_contributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    kb_file VARCHAR(255) NOT NULL,  -- e.g., "KB-004"
    action VARCHAR(50) NOT NULL,    -- 'created', 'updated', 'referenced'
    created_at TIMESTAMP DEFAULT NOW()
);

-- KB views tracking
CREATE TABLE kb_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kb_file VARCHAR(255) NOT NULL,
    viewed_by UUID REFERENCES users(id),
    viewed_at TIMESTAMP DEFAULT NOW()
);
```

---

## The Philosophical Shift

### Old Way (Track Time)
- Clock in, clock out
- Calculate hours
- Pay for presence

### New Way (Track Value)
- Clock in, clock out (still needed)
- But ALSO track: What did you learn? What did you teach?
- Pay for presence + reward for contribution

---

## Felix's Rules (Common Sense Validation)

1. **No shift > 9 hours** without override (events excepted)
2. **Can't start before shop opens** (warn, allow override)
3. **Can't end after shop closes + 1 hour** (cleaning time)
4. **5-minute rounding** (the "420 rule" - always round up)
5. **Break auto-deducted** for shifts > 6 hours

---

## What This Encourages

| Behavior | How System Encourages It |
|----------|-------------------------|
| Accurate time entry | Validation catches mistakes |
| Knowledge sharing | KB leaderboard recognition |
| Helping colleagues | "Referenced by" tracking |
| Continuous learning | KB reading stats |
| Systems thinking | Visible "ways of working" |

---

## Key Insight

> "Employees are my biggest expense."

True. But also:

> "Employee KNOWLEDGE is my biggest asset."

Time tracking: Necessary for payroll.
Value tracking: Necessary for growth.

**Do both.**

---

*Felix and Angel look at each other.*

**Felix**: "This is more than a time clock."

**Angel**: "It's a knowledge flywheel. The more they document, the more everyone learns. The more everyone learns, the better they serve customers. The better they serve, the more they have to document."

**Felix**: "And I can see who's contributing."

**Angel**: "Not just hours. VALUE."
