# BLQ Scene Backlog
## HelixNet UAT Scenarios - Prioritized

*Last Updated: 2025-12-03*

---

## Completed Scenes

### Episode 1: George Clooney / Bruce Lee Epic ✅
**Status:** COMPLETE | **Commit:** cf2794e (v3.2.0)

| Scene | Characters | Outcome |
|-------|------------|---------|
| 1.1 Zippo Flint JAM | George, Pam | Products: Zippo line, KB-040 |
| 1.2 Bruce Grinder Arrival | Pam, Felix | Products: Bruce Lee grinders, KB-041 |
| 1.3 Dayo Cheap Lighter | Dayo, Pam | Products: Mini flints, KB-042 |
| 1.4 Felix + Coolie Road Trip | Felix, George | Customer journey complete |
| 1.5 Ralph Takes Over | Ralph, Pam | Staff handoff tested |

**Gaps Filled:**
- [x] Product search with trigram
- [x] Zippo product line (8 SKUs)
- [x] Bruce Lee Grinders (3 SKUs)
- [x] Cleaning kits (A/B/C tiers)
- [x] Customer IBAN/VAT fields
- [x] Status bar footer

---

## In Progress

### Episode 2: Ralph's Afternoon 🔄
**Status:** STAGED | **Priority:** HIGH

| Scene | Characters | Gap to Fill | Complexity |
|-------|------------|-------------|------------|
| 2.1 CN Identity | Ralph, CN (Chuck Norris?) | Edge case customer handling | C2 |
| 2.2 Pam's Closeout Error | Ralph, Pam | Cash reconciliation, 40 rappen discrepancy | C1 |
| 2.3 Timesheet Approval | Ralph | Manager approval workflow | C1 |

---

## Backlog - Prioritized

### Priority 1: Core Operations

#### Episode 3: Boris Vending Service
**Characters:** Pam, Vera, Boris, Marco
**Location:** Boris Vending Site
**Time Pressure:** 4pm deadline, jammed slot

| Scene | Description | Gap to Fill | Complexity |
|-------|-------------|-------------|------------|
| 3.1 Meet Vera | Pam picks up Vera (LAB worker, Vaper CRACK) | New employee onboarding | C1 |
| 3.2 Travel to Boris | En route, Vera explains vape expertise | Knowledge transfer | C1 |
| 3.3 Vape Restock | Empty slots, customer complaints | Multi-location inventory | C2 |
| 3.4 Slot 4 Jam | Stick blocking mechanism | Vending maintenance SOP | C2 |
| 3.5 Marco Handoff | Escalate to Monday technician | Task escalation workflow | C1 |

**Products Needed:**
- CBD Vape inventory management
- Vending slot status tracking
- Multi-location dashboard

**KBs to Create:**
- KB-043: Vending Machine Maintenance
- KB-044: CBD Vape Product Guide (Vera's expertise)

---

#### Episode 4: Black Friday Preparation
**Characters:** Felix, Pam, Ralph, Leandra, George (maybe)
**Location:** Artemis Shop
**Time Pressure:** Friday deadline

| Scene | Description | Gap to Fill | Complexity |
|-------|-------------|-------------|------------|
| 4.1 Inventory Check | What's low, what's hot | Stock alerts, reorder triggers | C2 |
| 4.2 Pricing Review | Black Friday specials | Promotional pricing system | C2 |
| 4.3 Staff Schedule | Who works Friday | Shift management | C1 |
| 4.4 Marketing Push | Social posts, customer alerts | Notification system | C2 |
| 4.5 George Confirmation | Will Coolie attend? | VIP customer tracking | C1 |

---

### Priority 2: Staff & HR

#### Episode 5: Leandra's First Week
**Characters:** Leandra (new), Pam (mentor), Felix (owner)
**Location:** Artemis Shop
**Time Pressure:** Learning curve

| Scene | Description | Gap to Fill | Complexity |
|-------|-------------|-------------|------------|
| 5.1 First Morning | Leandra arrives nervous | Onboarding checklist | C1 |
| 5.2 Shadow Pam | Learning the register | Training mode in POS | C2 |
| 5.3 First Solo Customer | Simple sale, needs help | Help system, KB links | C1 |
| 5.4 First Mistake | Wrong change given | Error handling, manager alert | C2 |
| 5.5 End of Day Review | Felix feedback | Performance tracking | C1 |

**KBs to Create:**
- KB-045: New Employee Onboarding
- KB-046: Common Cashier Mistakes (Leandra's learnings)

---

#### Episode 6: Payroll Week
**Characters:** Ralph, Felix, All Staff
**Location:** Back Office
**Time Pressure:** End of month

| Scene | Description | Gap to Fill | Complexity |
|-------|-------------|-------------|------------|
| 6.1 Timesheet Collection | Gather all staff hours | Timesheet submission flow | C1 |
| 6.2 Overtime Review | Pam worked late | Overtime rules, approval | C2 |
| 6.3 Deductions | AHV, taxes, etc. | Swiss payroll calculations | C3 |
| 6.4 Payslip Generation | Create monthly slips | Payslip PDF generation | C2 |
| 6.5 Felix Approval | Final sign-off | Owner approval workflow | C1 |

---

### Priority 3: Edge Cases

#### Episode 7: Chuck Norris Day
**Characters:** CN (Chuck Norris), Ralph, Felix
**Location:** Artemis Shop
**Time Pressure:** None (Chuck sets the pace)

| Scene | Description | Gap to Fill | Complexity |
|-------|-------------|-------------|------------|
| 7.1 The Legend Arrives | CN walks in | Celebrity customer handling | C2 |
| 7.2 Unusual Request | "I need a grinder that can handle anything" | Custom product search | C2 |
| 7.3 SylKen Wallet | Premium leather goods request | Supplier integration | C2 |
| 7.4 Texas Papers | Specific brand not in stock | Special order workflow | C2 |
| 7.5 The Roundhouse | Chuck tests the product | Quality guarantee | C1 |

**This episode tests:**
- Unknown customer handling
- Custom/special orders
- Premium product line
- Celebrity customer experience

---

#### Episode 8: The Return from Hell
**Characters:** Angry Customer, Pam, Felix
**Location:** Artemis Shop
**Time Pressure:** Customer threatening bad review

| Scene | Description | Gap to Fill | Complexity |
|-------|-------------|-------------|------------|
| 8.1 Storm In | Customer angry, product "broken" | Complaint handling | C2 |
| 8.2 Investigation | Was it user error or defect? | Return investigation flow | C2 |
| 8.3 No Receipt | Customer has no proof of purchase | Receipt lookup system | C2 |
| 8.4 Manager Override | Felix steps in | Escalation workflow | C1 |
| 8.5 Resolution | Refund, exchange, or deny? | Refund authority rules | C2 |

**KBs to Create:**
- KB-047: Handling Angry Customers
- KB-048: Return Investigation Checklist

---

### Priority 4: System & Integration

#### Episode 9: Supplier Sync Day
**Characters:** Ralph, Felix, Fourtwenty API
**Location:** Back Office
**Time Pressure:** Monthly sync deadline

| Scene | Description | Gap to Fill | Complexity |
|-------|-------------|-------------|------------|
| 9.1 Price Updates | Supplier changed prices | Bulk price update | C2 |
| 9.2 New Products | 50 new SKUs to import | Product import workflow | C2 |
| 9.3 Discontinued Items | Some products gone | Discontinue without delete | C2 |
| 9.4 Stock Sync | Reconcile supplier vs local | Inventory reconciliation | C3 |

---

#### Episode 10: System Down
**Characters:** All Staff, Customers
**Location:** All
**Time Pressure:** Business stopped

| Scene | Description | Gap to Fill | Complexity |
|-------|-------------|-------------|------------|
| 10.1 The Outage | System goes offline | Offline mode | C3 |
| 10.2 Paper Backup | Manual transactions | Paper receipt process | C1 |
| 10.3 Recovery | System comes back | Transaction sync | C3 |
| 10.4 Reconciliation | Match paper to digital | Post-outage reconciliation | C2 |

---

## Scene Estimation Guide

| Complexity | Time Estimate | Typical Gaps |
|------------|---------------|--------------|
| **C1** | 15-30 min | UI tweaks, simple CRUD, KB creation |
| **C2** | 30-60 min | New features, workflows, multiple roles |
| **C3** | 1-2 hours | Complex integrations, calculations, edge cases |

---

## Gap Tracker

### Known Gaps (Not Yet Built)

| Gap | Discovered In | Priority | Complexity |
|-----|---------------|----------|------------|
| Offline mode | Planning | LOW | C3 |
| Training mode for POS | Planning | MEDIUM | C2 |
| Multi-location dashboard | Episode 3 | HIGH | C2 |
| Vending slot monitoring | Episode 3 | HIGH | C2 |
| Promotional pricing | Episode 4 | MEDIUM | C2 |
| Shift scheduling | Episode 4 | MEDIUM | C2 |
| Custom order workflow | Episode 7 | LOW | C2 |
| Return investigation | Episode 8 | MEDIUM | C2 |

---

## Character Roster

### Active (Fully Developed)
- **Pam** - Cashier, front-of-house queen
- **Felix** - Owner, deal closer
- **Ralph** - Manager, detail-oriented
- **George "Coolie"** - VIP customer, collector

### Introduced (Need Development)
- **Dayo** - Local regular, upsell opportunity
- **CN (Chuck Norris?)** - Edge case tester
- **Vera** - LAB worker, vape expert
- **Boris** - Vending site manager
- **Marco** - Technician, Tessin

### Planned (Not Yet Used)
- **Leandra** - New employee
- **SylKen** - Custom engraver
- **Rosie** - Leather supplier
- **Mike** - Felix's brother
- **Angry Customer** - Return scenario
- **Gessler** - Street-level, price sensitive

---

## Session Planning

### Next Session Priority
1. **Episode 2: Ralph's Afternoon** (complete CN scene)
2. **Episode 3: Boris Vending** (multi-location test)
3. **Episode 5: Leandra Training** (onboarding flow)

### Estimated Scenes per Session
- Short session (1 hr): 2-3 C1 scenes
- Medium session (2 hr): 1-2 C2 scenes + 2 C1
- Long session (3+ hr): 1 C3 + multiple C1/C2 (like today)

---

## Changelog

- **2025-12-03:** Initial backlog created after George Clooney Epic
- Episode 1 complete, Episodes 2-10 planned

---

*"I fear not the man who has practiced 10,000 kicks once, but I fear the man who has practiced one kick 10,000 times."*
— Bruce Lee

*Build one scene at a time. Master it. Move on.*
