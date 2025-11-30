# KB-038: FourTwenty Supplier Integration - Daily Product Feeds

**Created**: 2024-12-07
**Author**: Felix (with Angel's technical documentation)
**Status**: ACTIVE - Daily sync process

---

## The "Bus Factor" Philosophy

> "If I get hit by a bus, the business can continue and someone on the team can seamlessly and flawlessly replace me."

This KB exists so ANYONE can manage the FourTwenty supplier sync. No tribal knowledge.

---

## FourTwenty Overview

**Supplier**: FourTwenty.ch (Swiss vaping/headshop distributor)
**Model**: Dropship
**Update Frequency**: Daily CSV feeds
**VAT Rate**: 8.1% (Swiss standard)

---

## The Three Feeds

### 1. Product Feed (Master Catalog)

**URL**: `https://fourtwenty.ch/Dropship/Data/dropship_productfeed_v2.csv`

| Column | Description | Example |
|--------|-------------|---------|
| sku | Unique product ID | HE-EFESTLUC2 |
| gtin | Barcode (EAN/UPC) | 6958946200609 |
| producttitle_de | German product name | Efest Luc V2 Ladegerät |
| brandname | Manufacturer | Efest |
| categorygroup_1 | Main category | Vaping |
| categorygroup_2 | Sub-category | Accessories |
| categorygroup_3 | Sub-sub-category | Chargers |
| productcategory | Full path | Vaping > Accessories > Chargers |
| weight_g | Weight in grams | 250 |
| mainimageurl | Primary image URL | https://... |
| imageurl_1-4 | Additional images | https://... |
| salespriceinclvat | Price incl. 8.1% VAT | 36.00 |
| vatratepercentage | VAT rate | 8.1 |
| shipping_method | Delivery type | package / letter |

**Total columns**: 23

---

### 2. Stock Feed (Inventory Levels)

**URL**: `https://fourtwenty.ch/Dropship/Data/dropship_stockfeed_v1.csv`

| Column | Description | Example |
|--------|-------------|---------|
| sku | Product ID (links to product feed) | HE-EFESTLUC2 |
| ean | Barcode | 6958946200609 |
| qty | Current stock quantity | 45 |
| is_available | In stock? | TRUE / FALSE |

**Update frequency**: Real-time or near-real-time
**Note**: qty=0 usually means is_available=FALSE

---

### 3. Specification Feed (Product Details)

**URL**: `https://fourtwenty.ch/Dropship/Data/dropship_specificationfeed_v1.csv`

| Column | Description | Example |
|--------|-------------|---------|
| ProviderKey | Product SKU | HE-EFESTLUC2 |
| SpecificationKey | Attribute name (German) | Leistung |
| SpecificationValue | Attribute value | 200W |

**Format**: Vertical/EAV (Entity-Attribute-Value)
- One row per specification per product
- Multiple rows for same SKU with different specs

**Common specifications**:
- Physical: height, width, length, weight, diameter, color
- Technical: watts, ohms, mAh, temperature range, threading (510)
- Regulatory: age verification, minimum age (18+), CE/RoHS/FCC certs
- Liquids: nicotine mg/ml, PG/VG ratio, bottle size, flavor
- Safety: GHS symbols, warning labels, disposal instructions

---

## Daily Sync Process

```
┌─────────────────────────────────────────────────────────────────┐
│                    FOURTWENTY DAILY SYNC                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  06:00 - Download product_feed_v2.csv                          │
│        └── Parse 23 columns                                     │
│        └── Match SKUs to existing products                      │
│        └── Flag new products for review                         │
│                                                                 │
│  06:05 - Download stockfeed_v1.csv                             │
│        └── Update qty for all matched SKUs                      │
│        └── Set is_available flag                                │
│        └── Alert if key products go to qty=0                    │
│                                                                 │
│  06:10 - Download specificationfeed_v1.csv                     │
│        └── Update product specifications                        │
│        └── Check for regulatory changes (age, warnings)         │
│                                                                 │
│  06:15 - Generate sync report                                   │
│        └── New products added: X                                │
│        └── Prices changed: X                                    │
│        └── Stock alerts: X                                      │
│        └── Discontinued: X                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Mapping to HelixNet Products

| FourTwenty Field | HelixNet Field | Notes |
|------------------|----------------|-------|
| sku | supplier_sku | Keep original |
| gtin | barcode | Use for scanning |
| producttitle_de | name | German title |
| salespriceinclvat | cost_price | Our purchase price |
| - | retail_price | We set markup |
| qty | supplier_stock | Reference only |
| is_available | supplier_available | Reference only |

**Markup strategy**: Set in HelixNet based on category margins.

---

## Categories Mapping

| FourTwenty Category | HelixNet Category |
|---------------------|-------------------|
| Vaping > Hardware | Vaporizers |
| Vaping > Liquids | E-Liquids |
| Vaping > Accessories | Vaping Accessories |
| Growing > Nutrients | (Not carried) |
| Growing > Equipment | (Not carried) |

**Note**: FourTwenty has growing/cultivation products we don't carry at Artemis.

---

## Compliance Alerts

The specification feed includes regulatory fields. Watch for:

```
⚠️  MUST CHECK IN SPEC FEED:
├── Mindestalter (Minimum age) = 18+
├── Altersprüfung (Age verification) = Required
├── Warnhinweise (Warning labels) = Present
├── GHS-Symbole = Correct for product type
└── CE/RoHS = Certified
```

If any product lacks proper compliance data, DO NOT LIST until verified.

---

## Error Handling

| Error | Action |
|-------|--------|
| Feed download fails | Retry 3x, then alert |
| SKU not found in product feed | Skip, log warning |
| Price change > 20% | Flag for review |
| New category | Create mapping first |
| Missing GTIN | Use SKU as fallback barcode |

---

## Manual Override

Sometimes FourTwenty data needs correction:

```sql
-- Mark product as locally managed (ignore feed updates)
UPDATE products
SET sync_override = true,
    sync_notes = 'Local price/description maintained'
WHERE supplier_sku = 'HE-EFESTLUC2';
```

---

## The Network Vision

> "Chuck is doing this for his operation. The shop in Fribourg is working at it. The employees all have this mindset now."

**Who uses FourTwenty feeds**:
- Artemis (Felix) - Original implementation
- Chuck's Lab (Bern) - Adapting for B2B
- Fribourg Shop - Learning the process
- Future: Any shop joining HelixNet

**The succession plan**:
> "Someday I want to pass this onto my teenage sons when they get older. The boys are 16-18 now and will soon start college."

This documentation ensures they can take over seamlessly.

---

## Action Items

- [ ] Create automated daily sync script
- [ ] Build price change alert system
- [ ] Map all FourTwenty categories to HelixNet
- [ ] Document supplier contact process
- [ ] Create "New Product Review" workflow

---

## Key Insight

> "We are starting to prepare for ISO certification and clearly defining every process we do."

This KB IS the ISO 9001 documentation. Supplier management, data integrity, compliance checks - all documented.

When auditors ask "How do you manage supplier data?", we show them this KB.

---

*If Felix gets hit by a bus, Ralph reads this KB and keeps the sync running.*

*When Felix's sons take over, they read this KB and understand the supplier relationship.*

*That's the point.*
