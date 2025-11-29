# HelixPOS KB-020: How to Quickly Sell New Products On-The-Fly

## Document Information
- **KB ID:** KB-020
- **Title:** Quick-Sell Workflow for New Products Without Barcodes
- **Category:** POS Operations
- **Priority:** HIGH
- **Created:** 2025-11-28
- **Requested By:** Pam Beesly (Cashier)
- **Approved By:** Felix (Store Manager)
- **Status:** APPROVED

---

## Overview

This KB documents the workflow for selling artisan or handmade products that arrive without barcodes and need to be sold immediately. This is common when:

- Local artisans drop off handmade items
- New products arrive without labels
- Customers want to buy display items immediately
- Custom or one-off items need quick entry

---

## When to Use Quick-Sell vs Full Setup

| Scenario | Use Quick-Sell | Use Full Setup |
|----------|---------------|----------------|
| Customer waiting to buy NOW | ✅ | |
| Artisan just dropped off items | ✅ | |
| Need product in catalog permanently | | ✅ |
| Have time to enter all details | | ✅ |
| Regular inventory restock | | ✅ |
| One-time or custom item | ✅ | |

---

## Quick-Sell Workflow

### Step 1: Cashier Identifies Need
When a cashier (e.g., Pam) needs to sell a product without a barcode:

1. **DO NOT** try to create the product yourself (cashiers don't have permission)
2. **Call a manager** (Ralph or Felix) immediately
3. Provide these details to the manager:
   - Product name
   - Selling price
   - Brief description
   - Quantity to sell

### Step 2: Manager Creates TEMP Product
The manager creates a quick entry with minimal required fields:

```
Required Fields:
├── Name: "[Artisan] - [Product Name]"
├── SKU: "TEMP-[HHMMSS]-[###]" (auto-format)
├── Price: [Selling price]
├── Barcode: Auto-generated "TEMP-[HHMMSS]-[###]"
├── Category: "Artisan - [Artisan Name]"
├── Stock: [Quantity available]
└── Tags: Include "NEEDS-SETUP" tag
```

**Example:**
```
Name: Sylvie Handmade - Small Wool Pouch Natural
SKU: SYLVIE-TEMP-122903-001
Price: CHF 18.00
Barcode: TEMP-122903-001 (auto-generated)
Category: Artisan - Sylvie Handmade
Stock: 2
Tags: handmade, sylvie, wool, pouch, artisan, NEEDS-SETUP
```

### Step 3: Cashier Completes Sale
Once the manager confirms the product is created:

1. Search for the product by name or SKU
2. Add to transaction
3. Apply any applicable discounts
4. Complete checkout normally

### Step 4: System Auto-Notification
HelixNet automatically:

1. Detects products tagged `NEEDS-SETUP`
2. Sends email notification to store manager
3. Creates task for full catalog setup
4. Logs the quick-sell for audit trail

---

## Manager Follow-Up Tasks

After the immediate sale, the manager should:

### Update TEMP Products
1. Add proper cost price (for margin calculation)
2. Generate permanent barcode (Swiss EAN-13 format)
3. Update SKU to permanent format
4. Add full description
5. Set correct stock quantities
6. Remove `NEEDS-SETUP` tag

### Add Remaining Products
If the artisan brought multiple items:

1. Create full catalog entries for all products
2. Use consistent SKU naming: `[ARTISAN]-[TYPE]-[SIZE]-[COLOR]`
3. Generate barcodes for entire line
4. Print barcode labels

### Print Barcode Labels
1. Export product list to CSV
2. Use label printer software
3. Print peel-off labels (30mm x 20mm recommended)
4. Apply labels to all products

---

## Barcode Naming Convention

### Temporary Barcodes (Quick-Sell)
```
Format: TEMP-[HHMMSS]-[###]
Example: TEMP-122903-001
```

### Permanent Barcodes (Swiss EAN-13)
```
Format: 761000000[XXXX]
Example: 7610000000101
```

### SKU Naming Convention
```
Format: [ARTISAN]-[TYPE]-[SIZE]-[COLOR]
Examples:
- SYLVIE-WOOL-S-NAT (Small Wool, Natural)
- SYLVIE-LEATHER-BRN (Leather, Brown)
- SYLVIE-COMBO-M (Combo, Medium)
```

---

## Discount Guidelines for Quick-Sell Items

Cashiers can apply these standard discounts:

| Discount Type | Amount | When to Apply |
|--------------|--------|---------------|
| First-time customer | 10% | New customers |
| Cash payment | 5% | Cash transactions |
| Bundle deal | 10-15% | Multiple items |
| Staff discount | 15% | Employee purchases |

**Note:** Manager approval required for discounts > 15%

---

## Troubleshooting

### "Insufficient permissions" Error
- **Cause:** Cashiers cannot create products
- **Solution:** Ask a manager to create the product

### Duplicate Barcode Error
- **Cause:** Empty barcode conflicts with existing empty barcode
- **Solution:** Always use auto-generated TEMP barcodes

### Product Not Found After Creation
- **Cause:** Caching or sync delay
- **Solution:** Wait 5 seconds, then search again

---

## Real-World Example: Sylvie's Pouches

### Scenario
Sylvie (local artisan) drops off 10 handmade pouches. Customer wants to buy 3 immediately.

### What Happened
1. **Pam** identified need - customer waiting
2. **Pam** called Ralph for quick product entry
3. **Ralph** created 3 TEMP products in 2 minutes
4. **Pam** completed 3 sales with discounts
5. **System** sent email to Felix about NEEDS-SETUP products
6. **Ralph** later set up full catalog (all 10 products)
7. **Ralph** generated proper barcodes and printed labels
8. **Pam** applied labels to remaining inventory

### Result
- Customer happy (got products immediately)
- No lost sales
- Full catalog set up same day
- All products now have proper barcodes

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│  QUICK-SELL CHEAT SHEET                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Customer wants unlabeled product? CALL MANAGER          │
│                                                             │
│  2. Manager creates TEMP product:                           │
│     • Name, Price, Quantity                                 │
│     • Auto-barcode: TEMP-HHMMSS-###                        │
│     • Tag: NEEDS-SETUP                                      │
│                                                             │
│  3. Cashier completes sale normally                         │
│                                                             │
│  4. System notifies manager for follow-up                   │
│                                                             │
│  5. Manager updates with full details later                 │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  REMEMBER: Never lose a sale! Quick-sell now, update later  │
└─────────────────────────────────────────────────────────────┘
```

---

## Related KBs
- KB-001: Felix's Headshop 101
- KB-010: Age Verification Workflow
- KB-015: Discount Authorization Levels

---

## Revision History
| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-11-28 | 1.0 | Ralph | Initial creation based on Sylvie scenario |
| 2025-11-28 | 1.0 | Felix | Approved for production use |

---

*This KB was created in response to Pam's request after successfully handling Sylvie's handmade pouch launch on Day 2.*
