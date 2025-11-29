# KB-028: The Hankster Lesson - Anti-Fraud Time Tracking

**Created**: 2024-11-30 (Smoke break at the press demo)
**Author**: Angel (from Mosey's story)
**Status**: CRITICAL INSIGHT

---

## The Hankster Story

Mosey's warehouse manager Hank:
- 8 years with the company
- Clocked 62 hours/week on timesheets
- Actually arrived 3 hours late every day
- Buddy Marcel swiped his card at 6am
- Hank showed up at 9am

**Cost to Mosey:**
- ~15,000 CHF/year in phantom wages
- Multiple years of fraud
- 4 months to fire (Swiss labor law)
- 8,000 CHF in legal fees

---

## The Core Problem

> "With 50-60 people, you can't watch everyone. You need a system where the clock-in is tied to something real - like actually BEING there and DOING something."

Traditional timesheet = Trust-based
Trust-based = Exploitable

---

## The HelixNet Solution: POS = Proof of Presence

```
Traditional Timesheet:         HelixNet Approach:
─────────────────────         ────────────────────
Card swipe at door            POS login = clock in
  ↓                             ↓
Trust employee is there       Must be AT the register
  ↓                             ↓
Clock out when leaving        POS logout = clock out
  ↓                             ↓
No verification               Every sale = proof of work
```

**Key insight**: You can't fake a sale. Every transaction has:
- Timestamp
- Cashier ID
- Products sold
- Payment received

If the transaction exists, the employee was there.

---

## How It Works

### Clock In = First POS Login
```
08:55 - Pam logs into POS terminal
        → Shift automatically starts
        → No separate time clock needed
```

### Proof of Work = Sales Activity
```
09:02 - Transaction #1247 - CHF 45.00
09:15 - Transaction #1248 - CHF 23.50
09:31 - Transaction #1249 - CHF 178.00
...
```

Each sale proves:
- Pam was at the register
- Pam was serving customers
- Pam was actually working

### Clock Out = Final POS Logout
```
17:32 - Pam logs out of POS
        → Shift ends
        → Hours calculated
```

---

## The "Hankster Detector"

Red flags the system can catch:

| Pattern | What It Means |
|---------|---------------|
| Logged in, 0 sales for 2+ hours | Suspicious inactivity |
| First sale 3 hours after login | Late arrival? |
| Last sale 2 hours before logout | Early departure? |
| Logged in on day off | Buddy system fraud |
| Multiple logins same time, different locations | Impossible - flag it |

---

## Gap Analysis Dashboard (for Felix/Mosey)

```
═══════════════════════════════════════════════════════════
DAILY ACTIVITY ANALYSIS - 2024-11-30
═══════════════════════════════════════════════════════════

Employee: Pam
Login:    08:55
Logout:   17:32
Duration: 8h 37m (break deducted: 8h 07m)

SALES TIMELINE:
───────────────────────────────────────────────────────────
08:55 ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 17:32
      ↑        ↑↑↑↑  ↑↑↑   ↑↑↑↑↑↑  ↑↑↑  ↑↑↑   ↑↑↑↑↑  ↑
      Login    Sales activity throughout day         Logout

GAPS > 45 min:
  12:15-12:45 (lunch break - expected ✓)

STATUS: ✅ Normal activity pattern
───────────────────────────────────────────────────────────

Employee: Ralph
Login:    09:00
Logout:   18:05
Duration: 9h 05m (break deducted: 8h 35m)

SALES TIMELINE:
───────────────────────────────────────────────────────────
09:00 ░░░░░░░░░░░░████████░░░░░░░░░░░░░░░░░░░░░░░░ 18:05
      ↑          ↑                                   ↑
      Login      First sale at 11:30!              Logout

GAPS > 45 min:
  09:00-11:30 (2.5 hours, no sales)

STATUS: ⚠️ Review - 2.5 hour gap after login
───────────────────────────────────────────────────────────
```

---

## Why This Works for Retail (But Not Warehouse)

### Retail (Felix's shop, Mosey's 5 stores)
- Employee must be AT the POS
- Every sale = proof of work
- Can't buddy-swipe a cash register
- Natural verification built in

### Warehouse (Mosey's wholesale)
- No POS terminal
- Work isn't transaction-based
- Need different solution (scanning? tasks?)
- NOT what HelixNet solves

---

## Felix's Take

> "That's why I like the vending machines."

Vending machines don't need timesheets. They just work 24/7.

For humans, tie their time to their output. In retail, output = sales.

---

## Mosey's Conclusion

> "So the sales system IS the time tracking system..."

Exactly. The POS is the witness. No trust required.

---

## Implementation Notes

1. **Login = Shift Start** (already have user auth)
2. **Logout = Shift End** (already have this)
3. **Track gaps** (time between transactions)
4. **Daily report** shows timeline + flags
5. **Export for payroll** stays simple (start, end, hours, sales)

The anti-fraud features are just visibility into data we already have.

---

*"A 50,000 franc lesson in why you should never trust a timesheet."* - Mosey
