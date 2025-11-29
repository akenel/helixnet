# HelixPOS KB-022: Setting Up Promotional Campaigns

## Document Information
- **KB ID:** KB-022
- **Title:** Promotional Campaign Setup & Tracking
- **Category:** Marketing / Promotions
- **Priority:** MEDIUM
- **Created:** 2025-11-29 (Day 4)
- **Author:** Felix (Store Manager)
- **Status:** DRAFT - IN PROGRESS

---

## Overview

This KB documents how to set up and track promotional campaigns in HelixPOS. This includes:

- Free add-on promotions (e.g., first 100 get free personalization)
- Discount campaigns
- Bundle deals
- Limited-time offers
- Tracking promotion usage

---

## Current Promotion: Free Custom Tags (First 100)

### Campaign Details

| Field | Value |
|-------|-------|
| **Campaign Name** | Sylvie Launch - Free Personalization |
| **Start Date** | 2025-11-29 |
| **End Date** | Until 100 tags given OR 2025-12-31 |
| **Eligible Products** | Any Sylvie Collection item |
| **Free Item** | SYLVIE-CUSTOM-TAG (CHF 15 value) |
| **Limit** | First 100 qualifying purchases |
| **Tracking** | Manual counter + transaction notes |

### How It Works

1. Customer purchases any Sylvie product
2. Cashier offers free custom tag ("Would you like free personalization?")
3. If yes, add SYLVIE-CUSTOM-TAG to transaction
4. Apply 100% discount to the tag line item
5. Note initials for engraving
6. Increment promotion counter

### Implementation in HelixPOS

#### Option A: Price Override (Current Method)

```
Transaction Flow:
1. Scan Sylvie product (e.g., SYLVIE-MINI-NAT)
2. Add SYLVIE-CUSTOM-TAG
3. Apply line-item discount: 100% (manager override)
4. Add transaction note: "PROMO: Free tag #[XX] - Initials: [ABC]"
5. Complete checkout
```

**Pros:** Works now, no system changes
**Cons:** Requires manager override, manual tracking

#### Option B: Promotional SKU (Recommended Future)

Create a separate promotional product:

```
SKU: SYLVIE-CUSTOM-TAG-PROMO
Name: Sylvie Custom Tag - FREE PROMO
Price: CHF 0.00
Cost: CHF 5.00 (for margin tracking)
Stock: 100 (auto-limits promotion)
Tags: promo, sylvie, free-personalization
```

**Pros:** Self-limiting (stock=100), easy tracking, no override needed
**Cons:** Requires product creation, two SKUs for same item

---

## Tracking Promotion Usage

### Manual Tracking Sheet

```
┌─────────────────────────────────────────────────────────────┐
│  SYLVIE FREE TAG PROMOTION - TRACKING                       │
├─────────────────────────────────────────────────────────────┤
│  Start: Nov 29, 2025    Budget: 100 tags                    │
│  Target: Build loyalty, word-of-mouth                       │
├─────────────────────────────────────────────────────────────┤
│  #   Date       Transaction    Initials   Cashier           │
│  ─── ────────── ────────────── ────────── ────────          │
│  001 2025-11-29 TXN-xxx-0025   A.M.       Felix             │
│  002 2025-11-29 TXN-xxx-0026   S.R.       Felix             │
│  ...                                                        │
│  100 ????-??-?? TXN-xxx-????   ???        ???               │
├─────────────────────────────────────────────────────────────┤
│  STATUS: ___ / 100 used                                     │
└─────────────────────────────────────────────────────────────┘
```

### Database Query for Tracking

Once using PROMO SKU, track usage with:

```sql
SELECT COUNT(*) as promo_tags_given
FROM line_items li
JOIN products p ON li.product_id = p.id
WHERE p.sku = 'SYLVIE-CUSTOM-TAG-PROMO';
```

---

## Campaign ROI Analysis

### Cost-Benefit Calculation

```
INVESTMENT:
- 100 tags × CHF 5.00 cost = CHF 500.00

EXPECTED RETURN:
- Increased Sylvie sales (word-of-mouth)
- Customer loyalty (personalized = emotional connection)
- Social media potential ("Got my custom Artemis bag!")

BREAK-EVEN:
- Need ~7 additional Large Tote sales (7 × CHF 75 margin)
- OR ~15 additional Mini Wallet sales (15 × CHF 13 margin)

ROI TARGET:
- 20% increase in Sylvie sales over 30 days
- Current: ~CHF 180/day → Target: ~CHF 216/day
- Additional revenue over 30 days: CHF 1,080
- Net ROI: CHF 1,080 - CHF 500 = CHF 580 (116% return)
```

---

## Future Campaign Ideas

### 1. "Artemis Exclusive" Collection
- Co-branded tags: "Ecolution × Artemis"
- Only available at our store
- Premium positioning

### 2. Color of the Month
- Featured color gets 10% off
- Drives sales of slower-moving colors
- Creates urgency

### 3. Bundle Deals
- "The Sylvie Set": Mini + Small + Free Tag = CHF 49
- Saves CHF 5 + free personalization
- Moves inventory faster

### 4. Loyalty Punch Card
- Buy 5 Sylvie items, get 6th 20% off
- Encourages repeat purchases
- Builds collection mindset

---

## Staff Training Points

### What to Say

**Offer Script:**
> "This is part of Sylvie's handmade collection - each piece is unique.
> Right now, we're offering free personalization with any purchase.
> Would you like your initials engraved on a custom leather tag?"

**Handling "No Thanks":**
> "No problem! The offer is valid on your next visit too."

### Key Points
- Always mention the promotion AFTER they've decided to buy
- Personalization makes great gifts - mention if near holidays
- Initials only (3 letters max) - no full names
- Takes 24-48 hours for engraving (Sylvie does it)

---

## Promotion Checklist

Before launching any promotion:

- [ ] Define clear start/end dates
- [ ] Set quantity or budget limit
- [ ] Create tracking method (manual or system)
- [ ] Train all staff on offer script
- [ ] Update signage in store
- [ ] Calculate break-even point
- [ ] Set review date for ROI analysis

---

## Related KBs
- KB-015: Discount Authorization Levels
- KB-020: Quick-Sell Workflow
- KB-021: Bulk Product Entry

---

## Revision History
| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-11-29 | 0.1 | Felix | Initial draft during rainy morning |

---

*This KB was created by Felix on Day 4 while waiting for Pam's doctor appointment update. "HelixNet was designed for these edge cases."*
