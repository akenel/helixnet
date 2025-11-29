# KB-026: Understanding Enterprise Scale - Mosey's Operation

**Created**: 2024-11-30 (Saturday morning smoke break with Mosey)
**Author**: Angel
**Status**: DISCOVERY - Understanding the gap

---

## The Smoke Break Conversation

**Angel**: "How's business, Mosey?"

**Mosey** *(blowing smoke)*: "I love the products but sometimes the people in this industry... they're not the hardest workers and need to be told."

---

## Mosey's Scale vs Felix's Scale

| Metric | Felix (Artemis) | Mosey (Network) |
|--------|-----------------|-----------------|
| Stores | 1 | 5 |
| Location | Luzern | Bern + surrounding |
| Employees | 5 | 50-60 |
| Monthly payroll | ~15,000 CHF? | **250,000 CHF** |
| Business model | Retail | **Retail + Wholesale** |
| Main headache | Sales tracking | **People management** |
| Peak season | Contractors? | Must hire contractors |
| Currency | CHF only | Multi-currency (DE) |

---

## Mosey's Actual Problems (Not POS!)

### 1. Wholesale/B2B Operations
> "I do a lot of buying and I have to chase my customers to pay the bill"

- Invoice tracking system
- Accounts receivable
- Supplier onboarding
- Payment collection

### 2. HR/People Management
> "Lazy people I can never fire"

- 50-60 employees mostly fulltime
- Swiss labor law makes firing difficult
- Staff motivation issues
- "Need to be told" what to do

### 3. Time Tracking at Scale
> "During peak season I have to hire contractors so time keeping is a pain"

- Seasonal contractor management
- Time tracking for 50-60 people
- 250k CHF monthly payroll accuracy is critical

### 4. Multi-Location Operations
- 5 stores in/around Bern
- Inventory across locations
- Staff scheduling across sites

---

## What Mosey Uses Today

| System | Purpose | Mosey's Opinion |
|--------|---------|-----------------|
| Magento | E-commerce, B2B | "It's ok for selling and buying" |
| ??? | Invoice tracking | Has one, chases payments |
| ??? | Payroll/Time | "Pain" - unclear if system or manual |
| ??? | Multi-currency | Handles CHF + EUR |

---

## Key Insight: Wrong Problem Space

```
┌─────────────────────────────────────────────────────────────┐
│                    MOSEY'S UNIVERSE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  WHOLESALE   │  │   HR/PAYROLL │  │   5x RETAIL  │      │
│  │   (Magento)  │  │   (250k/mo)  │  │    STORES    │      │
│  │              │  │              │  │              │      │
│  │  - Invoicing │  │  - 50-60 ppl │  │  - POS ???   │      │
│  │  - B2B sales │  │  - Time track│  │  - Sales     │      │
│  │  - Suppliers │  │  - Contracts │  │  - Inventory │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│        ▲                  ▲                  ▲              │
│        │                  │                  │              │
│   BIG PROBLEM        BIGGEST PROBLEM    Maybe HelixNet?    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**HelixNet could help with**: The 5 retail stores (POS, sales tracking)

**HelixNet cannot help with**:
- Wholesale/B2B (Magento already does this)
- HR/Payroll (needs enterprise HR system)
- Time tracking for 60 people (way beyond scope)
- Contractor management

---

## Felix's Reaction

> "Whose keeping track of time? I think we are running late now - let's go!"

Even Felix - with his 5-person operation - thinks about time constantly. For Mosey at 50-60 people, it's 10x more complex.

---

## Questions for Follow-up

1. What POS does Mosey use at his 5 retail stores today?
2. Is it connected to Magento?
3. How does he handle inventory across 5 locations?
4. Would he want a simpler retail POS that syncs with Magento?

---

## The Honest Truth

Mosey doesn't need HelixNet. He needs:
1. Better HR/time tracking system (SAP, Personio, etc.)
2. His Magento wholesale system (already has it)
3. Maybe a simpler retail POS for the stores (possible fit)

**Don't try to boil the ocean.** Understand the customer's real problems first.

---

*Running late for the show - 10:45 AM*
