# BLQ KB-003: Batch & Lot Tracking System

**Owner:** Andy Warhol
**Created:** 2025-11-30
**ISO Reference:** ISO 9001:2015 - 8.5.2 Identification and Traceability

---

## Why Track Batches & Lots?

1. **Quality Control** - If issue found, recall specific batch only
2. **Supplier Traceability** - Link finished product to raw material source
3. **ISO Compliance** - Required for certification
4. **Customer Confidence** - Professional operation
5. **Legal Protection** - Prove compliance if questioned

---

## Numbering System

### LOT Number (Raw Materials)
```
LOT-[SUPPLIER]-[YYMMDD]-[SEQ]

Examples:
LOT-PERU-251130-001   = Peruvian oil, received Nov 30 2025, first shipment
LOT-420-251201-001    = 420 supplies, received Dec 1 2025, first shipment
LOT-CBD-251115-003    = CBD isolate, received Nov 15 2025, third shipment
```

### BATCH Number (Production)
```
BATCH-[PRODUCT]-[YYMMDD]-[SEQ]

Examples:
BATCH-PP-251130-001   = Pink Punch, produced Nov 30 2025, first batch
BATCH-OT-251215-001   = Orange Tang, produced Dec 15 2025, first batch
BATCH-WL10-251201-002 = White Label 10%, produced Dec 1 2025, second batch
```

---

## Traceability Chain

```
SUPPLIER → LOT → BATCH → BOTTLE → CUSTOMER

Example:
Peru Organics (Supplier)
    ↓
LOT-PERU-251130-001 (1 Liter organic oil received)
    ↓
BATCH-PP-251130-001 (50 bottles Pink Punch produced)
    ↓
BLQ-PP-001 Serial #0001-0050 (Individual bottles)
    ↓
Customer Order #12345 (Bottles #0023, #0024 sold)
```

---

## Batch Production Record

### Template: BATCH-PP-YYMMDD-XXX

```
═══════════════════════════════════════════════════════════════════
BATCH PRODUCTION RECORD
═══════════════════════════════════════════════════════════════════

Batch Number:     BATCH-PP-251130-001
Product:          BLQ-PP-001 - CBD Pink Punch 10ml
Production Date:  2025-11-30
Operator:         Andy Warhol
Quantity:         50 bottles

───────────────────────────────────────────────────────────────────
RAW MATERIALS USED
───────────────────────────────────────────────────────────────────
Material              LOT Number           Qty Used    Remaining
───────────────────────────────────────────────────────────────────
Peruvian MCT Oil      LOT-PERU-251130-001  400ml       600ml
CBD Isolate 99%       LOT-CBD-251115-003   50g         450g
Divine Secret 2ml     LOT-DIV-251101-001   100ml       400ml
Amber Bottles 10ml    LOT-420-251128-001   50 pcs      150 pcs
Dropper Caps          LOT-420-251128-001   50 pcs      150 pcs
Labels                LOT-PRT-251125-001   50 pcs      200 pcs
Boxes                 LOT-420-251128-002   50 pcs      100 pcs

───────────────────────────────────────────────────────────────────
PRODUCTION STEPS
───────────────────────────────────────────────────────────────────
Time      Step                              Initials  Verified
───────────────────────────────────────────────────────────────────
08:00     Workspace sanitized               AW        ✓
08:15     Raw materials weighed/measured    AW        ✓
08:30     Base formula mixed                AW        ✓
08:45     Divine 2ml added                  AW        ✓
09:00     Centrifuge 15 min @ 3000rpm       AW        ✓
09:15     pH tested (target 6.5-7.5)        AW        ✓ pH=7.1
09:30     Viscosity check                   AW        ✓ Pass
09:45     Filling started                   AW        ✓
10:30     Filling complete (50 bottles)     AW        ✓
10:45     Caps applied                      AW        ✓
11:00     Labels applied                    AW        ✓
11:15     Boxing complete                   AW        ✓
11:30     Final QC check (3 random)         AW        ✓ Pass

───────────────────────────────────────────────────────────────────
QUALITY CONTROL
───────────────────────────────────────────────────────────────────
Test                  Result      Spec        Pass/Fail
───────────────────────────────────────────────────────────────────
Visual inspection     Clear pink  Clear pink  ✓ Pass
pH level              7.1         6.5-7.5     ✓ Pass
Fill volume (avg)     10.2ml      10±0.5ml    ✓ Pass
Label alignment       Centered    Centered    ✓ Pass
Box seal              Secure      Secure      ✓ Pass

───────────────────────────────────────────────────────────────────
BATCH DISPOSITION
───────────────────────────────────────────────────────────────────
Total Produced:       50 bottles
QC Samples:           2 bottles (retained)
Available for Sale:   48 bottles
Batch Status:         ✓ RELEASED

───────────────────────────────────────────────────────────────────
SIGNATURES
───────────────────────────────────────────────────────────────────
Produced by:          Andy Warhol          Date: 2025-11-30
QC Approved by:       Andy Warhol          Date: 2025-11-30

═══════════════════════════════════════════════════════════════════
```

---

## HelixNet Integration

### Batch Tracking Table (Future)
```sql
CREATE TABLE production_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_number VARCHAR(50) UNIQUE NOT NULL,
    product_sku VARCHAR(50) REFERENCES products(sku),
    production_date DATE NOT NULL,
    quantity_produced INT NOT NULL,
    quantity_available INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, released, recalled
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    released_at TIMESTAMP
);

CREATE TABLE batch_materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID REFERENCES production_batches(id),
    lot_number VARCHAR(50) NOT NULL,
    material_name VARCHAR(100) NOT NULL,
    quantity_used DECIMAL(10,2) NOT NULL,
    unit VARCHAR(20) NOT NULL
);
```

### Link Sale to Batch
```sql
-- When selling, record which batch
UPDATE line_items
SET batch_number = 'BATCH-PP-251130-001'
WHERE product_sku = 'BLQ-PP-001';
```

---

## Supplier LOT Register

### Template: Monthly LOT Log

| Date | LOT Number | Supplier | Material | Qty | Unit | Exp Date | Status |
|------|------------|----------|----------|-----|------|----------|--------|
| 2025-11-30 | LOT-PERU-251130-001 | Peru Organics | MCT Oil | 1 | L | 2027-11 | Active |
| 2025-11-28 | LOT-420-251128-001 | FourTwenty | Bottles 10ml | 200 | pcs | N/A | Active |
| 2025-11-28 | LOT-420-251128-002 | FourTwenty | Boxes | 150 | pcs | N/A | Active |
| 2025-11-15 | LOT-CBD-251115-003 | CBD Supplier | Isolate 99% | 500 | g | 2026-11 | Active |

---

## Recall Procedure

If quality issue discovered:

1. **Identify Batch** - Which BATCH-XX-XXXXXX-XXX?
2. **Check Sales** - Which customers received this batch?
3. **Stop Sales** - Mark batch as RECALLED in HelixNet
4. **Contact Customers** - Email/call affected orders
5. **Investigate** - Which LOT caused the issue?
6. **Document** - Record everything for ISO audit
7. **Prevent** - Update process to prevent recurrence

---

## Daily Inventory Sync

```bash
# Daily backup includes batch tracking
# Run at 17:30 with closeout

# Future: Auto-sync batch quantities
# When sale made → reduce batch_available
# When production done → create new batch
```

---

## Related KBs

- BLQ_KB-001: Vision & Launch Epic
- BLQ_KB-002: Product Catalog & SKU System
- BLQ_KB-004: Daily Operations SOP
