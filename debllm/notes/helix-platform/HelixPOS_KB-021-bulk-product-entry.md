# HelixPOS KB-021: Bulk Product Entry for Color/Size Variants

## Document Information
- **KB ID:** KB-021
- **Title:** Efficient Bulk Product Entry Using Batch Methods
- **Category:** Product Management
- **Priority:** MEDIUM
- **Created:** 2025-11-28
- **Requested By:** Felix (Store Manager)
- **Developed By:** Ralph (Manager/Developer)
- **Status:** APPROVED

---

## Overview

This KB documents the efficient workflow for adding large numbers of product variants (size × color combinations) to the catalog. This is common when:

- Artisan brings new product line with multiple colors/sizes
- Seasonal collections with variant matrices
- Any product family with consistent pricing structure
- Bulk initial inventory setup

---

## When to Use Bulk Entry vs Manual Entry

| Scenario | Use Bulk Entry | Use Manual Entry |
|----------|---------------|------------------|
| 10+ similar products | ✅ | |
| Size × Color matrix | ✅ | |
| Consistent pricing by size | ✅ | |
| Single unique product | | ✅ |
| Products with different structures | | ✅ |
| Quick one-off addition | | ✅ |

---

## The Matrix Approach

### Step 1: Define Your Dimensions

Identify the product dimensions (typically 2-3):

**Dimension 1: Sizes**
```
MINI  - Mini Wallet    - CHF 22.00 (cost: CHF 9.00)
SM    - Small Pouch    - CHF 32.00 (cost: CHF 13.00)
MD    - Medium Pouch   - CHF 48.00 (cost: CHF 20.00)
LG    - Large Tote     - CHF 75.00 (cost: CHF 32.00)
```

**Dimension 2: Colors**
```
NAT - Natural       (#D4C4B0)
BUR - Burgundy      (#722F37)
GRN - Forest Green  (#228B22)
BLU - Ocean Blue    (#006994)
CHR - Charcoal      (#36454F)
ORG - Sunset Orange (#FD5E53)
```

### Step 2: Calculate Total Products

```
Total = Dimension1 × Dimension2 × ... × DimensionN
Example: 4 sizes × 6 colors = 24 products
```

### Step 3: Define SKU Pattern

```
Format: [BRAND]-[SIZE]-[COLOR]
Example: SYLVIE-MINI-NAT, SYLVIE-LG-BUR
```

### Step 4: Define Barcode Sequence

```
Swiss EAN-13 Format: 761000000[XXXX]
Starting number: Pick a sequence not in use
Example: 7610000002XX for this batch
```

---

## Implementation Methods

### Method A: API Batch Script (Recommended)

For managers with API access, use a simple script:

```python
sizes = [
    {"code": "MINI", "name": "Mini Wallet", "price": "22.00", "cost": "9.00"},
    {"code": "SM", "name": "Small Pouch", "price": "32.00", "cost": "13.00"},
    # ... more sizes
]

colors = [
    {"code": "NAT", "name": "Natural"},
    {"code": "BUR", "name": "Burgundy"},
    # ... more colors
]

barcode_counter = 201  # Starting sequence

for size in sizes:
    for color in colors:
        product = {
            "name": f"Sylvie {size['name']} - {color['name']}",
            "sku": f"SYLVIE-{size['code']}-{color['code']}",
            "barcode": f"76100000{barcode_counter:04d}",
            "price": size["price"],
            "cost": size["cost"],
            "stock_quantity": 2,
            "category": "Artisan - Sylvie Collection",
            # ... other fields
        }
        api_call("POST", "/api/v1/pos/products", product)
        barcode_counter += 1
```

**Performance:** ~25 products in < 1 minute

### Method B: CSV Import (Alternative)

Prepare a CSV with all products:

```csv
name,sku,barcode,price,cost,stock,category
"Sylvie Mini Wallet - Natural",SYLVIE-MINI-NAT,761000000201,22.00,9.00,2,"Artisan - Sylvie"
"Sylvie Mini Wallet - Burgundy",SYLVIE-MINI-BUR,761000000202,22.00,9.00,2,"Artisan - Sylvie"
...
```

Use spreadsheet to generate the matrix:
1. Create size rows
2. Use CONCAT formulas for SKU/barcode
3. Export as CSV
4. Import via Admin Panel

---

## Barcode Label Generation

After bulk entry, generate labels for all new products:

```
┌────────────────────────────┐
│ 761000000201               │
│ |||||||||||||||||||||||    │
│ Sylvie Mini Wallet         │
│ Natural - CHF 22.00        │
└────────────────────────────┘
```

**Recommended Label Size:** 30mm × 20mm thermal peel-off

---

## Time Comparison

| Method | 24 Products | Time | Notes |
|--------|------------|------|-------|
| Manual Entry | 24 × 3 min | 72+ minutes | Error-prone |
| API Batch | 24 products | < 1 minute | Consistent |
| CSV Import | 24 products | 5-10 minutes | Requires prep |

**ROI:** Batch method is 70-100x faster than manual entry

---

## Best Practices

### DO:
- ✅ Plan your SKU pattern before starting
- ✅ Reserve a barcode sequence range
- ✅ Include cost prices for margin tracking
- ✅ Set appropriate stock alert thresholds
- ✅ Add consistent tags for filtering
- ✅ Test with 1-2 products first

### DON'T:
- ❌ Skip the cost price (breaks margin reports)
- ❌ Use inconsistent SKU naming
- ❌ Forget to generate barcode labels
- ❌ Leave stock quantities at 0

---

## Real-World Example: Sylvie Day 3 Launch

### Scenario
Sylvie brings new product line: 4 sizes × 6 colors = 24 products + 1 custom tag option = 25 products total.

### What Ralph Did
1. **10:15 AM** - Defined size/color matrix
2. **10:18 AM** - Created batch script
3. **10:20 AM** - Ran script (0.7 seconds!)
4. **10:25 AM** - Generated 25 barcode labels
5. **10:30 AM** - All products tagged and display ready

### Result
- 25 products in < 5 minutes (vs 72+ minutes manual)
- All barcodes sequential and scannable
- Cost prices enabled margin tracking
- Same-day sales: CHF 283.00 from new collection

---

## Troubleshooting

### Duplicate Barcode Error
- **Cause:** Barcode sequence overlaps with existing
- **Solution:** Query existing barcodes first, pick unused range

### Missing Products After Import
- **Cause:** Validation errors in some rows
- **Solution:** Check API response for each product, log failures

### Inconsistent Pricing
- **Cause:** Price defined per-product instead of per-size
- **Solution:** Use the matrix approach - price lives with size

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│  BULK ENTRY CHEAT SHEET                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. PLAN YOUR MATRIX                                        │
│     • List all sizes with prices/costs                      │
│     • List all colors/variants                              │
│     • Calculate total: Size × Color = Products              │
│                                                             │
│  2. DEFINE PATTERNS                                         │
│     • SKU: BRAND-SIZE-COLOR                                 │
│     • Barcode: 76100000XXXX (sequential)                    │
│                                                             │
│  3. RUN BATCH SCRIPT OR CSV IMPORT                          │
│                                                             │
│  4. GENERATE BARCODE LABELS                                 │
│                                                             │
│  5. TAG PRODUCTS AND UPDATE DISPLAY                         │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  REMEMBER: Plan once, execute fast. That's BLQ!             │
└─────────────────────────────────────────────────────────────┘
```

---

## Related KBs
- KB-020: Quick-Sell Workflow for New Products
- KB-001: Felix's Headshop 101
- KB-015: Discount Authorization Levels

---

## Revision History
| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-11-28 | 1.0 | Ralph | Initial creation based on Sylvie Day 3 |
| 2025-11-28 | 1.0 | Felix | Approved for production use |

---

*This KB was created after Ralph successfully cataloged 25 Sylvie products in under 5 minutes using the batch method on Day 3.*
