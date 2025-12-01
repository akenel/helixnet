# BLQ KB-002: Product Catalog & SKU System

**Owner:** Andy Warhol
**Created:** 2025-11-30
**ISO Reference:** Product Identification & Traceability

---

## SKU Naming Convention

### BLQ Premium Products
```
BLQ-[FLAVOR]-[SIZE]

Examples:
BLQ-PP-001    = Pink Punch, 10ml, variant 001
BLQ-PP-002    = Pink Punch, 2ml, variant 002
BLQ-OT-001    = Orange Tang, 10ml
BLQ-BB-001    = Blue Berry Banger, 10ml
BLQ-MG-001    = Mango Madness, 10ml
```

### Flavor Codes
| Code | Flavor | Color | Target | Status |
|------|--------|-------|--------|--------|
| PP | Pink Punch | Pink | Universal | ✅ Live |
| OT | Orange Tang | Orange | Universal | Dev |
| BB | Blue Berry Banger | Blue | Universal | Planned |
| MG | Mango Madness | Yellow | Universal | Planned |
| GG | Grape Galaxy | Purple | Universal | Planned |
| LM | Lemon Lightning | Yellow | Universal | Planned |

### Size Variants
| Suffix | Size | Use Case |
|--------|------|----------|
| -001 | 10ml | Standard retail |
| -002 | 2ml | Sample/trial |
| -003 | 30ml | Value size |
| -1L | 1 Liter | B2B/White label |

### White Label SKUs
```
BLQ-WL-[CBD%]-[SIZE]

Examples:
BLQ-WL-03-1L   = White Label, 3% CBD, 1 Liter
BLQ-WL-05-1L   = White Label, 5% CBD, 1 Liter
BLQ-WL-10-1L   = White Label, 10% CBD, 1 Liter
BLQ-WL-10-100  = White Label, 10% CBD, 100x 10ml bottles
BLQ-WL-30-1L   = White Label, 30% CBD, 1 Liter (premium)
```

---

## Barcode Assignment

### EAN-13 Range (Reserved for BLQ)
```
761 0000 0000 01 - Pink Punch 10ml
761 0000 0000 02 - Orange Tang 10ml
761 0000 0000 03 - Blue Berry Banger 10ml
...
761 0000 0001 xx - White Label products
761 0000 0002 xx - Future expansion
```

---

## Product Master Data

### CBD Pink Punch (BLQ-PP-001)

```yaml
sku: BLQ-PP-001
barcode: "7610000000001"
name: "CBD Pink Punch - BlowUp Littau Signature (10ml)"
category: "Custom Blends"

pricing:
  retail_price: 42.00
  cost: 12.00
  margin_percent: 71.4
  currency: CHF

specifications:
  cbd_percent: 10
  thc_percent: 0.0  # Legal limit <1%
  volume_ml: 10
  carrier_oil: "Peruvian Organic MCT"

packaging:
  bottle_type: "Amber glass dropper"
  box_required: true
  vending_compatible: false

compliance:
  age_restricted: false  # CBD, not THC
  requires_lab_cert: true
  shelf_life_months: 24
  storage: "Cool, dark place"

inventory:
  reorder_point: 20
  reorder_quantity: 50
  lead_time_days: 3  # Production time
```

---

## Product Templates

### New Flavor Checklist
When launching a new flavor (e.g., Orange Tang):

1. **Create SKU**
   - [ ] Assign flavor code (OT)
   - [ ] Create BLQ-OT-001 (10ml)
   - [ ] Create BLQ-OT-002 (2ml) if needed

2. **Assign Barcode**
   - [ ] Get next available EAN-13
   - [ ] Register in HelixNet

3. **Set Pricing**
   - [ ] Calculate cost (base + divine + carrier + packaging)
   - [ ] Set retail (target 60-70% margin)
   - [ ] Verify VAT handling (8.1%)

4. **Create in HelixNet**
   ```sql
   INSERT INTO products (
     id, sku, barcode, name, price, cost, category,
     is_active, stock_quantity, created_at, updated_at
   ) VALUES (
     gen_random_uuid(),
     'BLQ-OT-001',
     '7610000000002',
     'CBD Orange Tang - BlowUp Littau (10ml)',
     45.00, 14.00, 'Custom Blends',
     true, 0, NOW(), NOW()
   );
   ```

5. **Upload Image**
   - [ ] AI generate or photograph
   - [ ] Resize to 800x800
   - [ ] Upload to product record

6. **Test Sale**
   - [ ] Add to cart in POS
   - [ ] Complete test transaction
   - [ ] Verify receipt
   - [ ] Check inventory deduction

---

## Pricing Strategy

### Cost Breakdown (10ml bottle)
| Component | Cost (CHF) |
|-----------|------------|
| CBD Isolate/Distillate | 5.00 |
| Peruvian Carrier Oil | 2.00 |
| Divine 2ml Secret | 1.00 |
| Bottle + Dropper | 1.50 |
| Label + Box | 1.50 |
| Labor (5 min) | 1.00 |
| **Total Cost** | **12.00** |

### Retail Pricing Tiers
| Product Type | Cost | Retail | Margin |
|--------------|------|--------|--------|
| Standard 10ml | 12.00 | 42.00 | 71% |
| Premium 10ml | 14.00 | 49.00 | 71% |
| Mini 2ml | 4.00 | 15.00 | 73% |
| White Label 1L | 180.00 | 350.00 | 49% |

---

## Inventory Categories in HelixNet

```
Custom Blends        → BLQ Premium products
Lab - Raw Materials  → CBD isolate, carrier oils
Lab - Supplies       → Bottles, droppers, labels
Lab - CBD Blends     → Work in progress batches
```

---

## Future Products Pipeline

### 2025 Q4
- [x] BLQ-PP-001 Pink Punch 10ml

### 2026
- [ ] BLQ-PP-002 Pink Punch 2ml
- [ ] BLQ-OT-001 Orange Tang 10ml
- [ ] BLQ-OT-002 Orange Tang 2ml

### 2027
- [ ] BLQ-BB-001 Blue Berry Banger
- [ ] BLQ-MG-001 Mango Madness
- [ ] White Label program launch

### 2028+
- [ ] Full 6-8 flavor collection
- [ ] Cookie/edible line
- [ ] Vape cartridge line

---

## Related KBs

- BLQ_KB-001: Vision & Launch Epic
- BLQ_KB-003: Batch & Lot Tracking
- BLQ_KB-004: Daily Operations SOP
