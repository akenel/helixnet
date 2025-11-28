---
kb_id: HelixPOS_KB-001
title: Felix's Headshop 101 - Master Domain Knowledge
domain: headshop-retail
language: en
contributor: Felix (Artemis Headshop, Bern, Switzerland - 25 years)
category: foundation
status: approved
version: 1.0.0
created: 2025-11-27
last_updated: 2025-11-27
applies_to: [helix-pos, artemis-headshop]
vat_critical: true
compliance_level: high
---

# HelixPOS_KB-001: Felix's Headshop 101

**Master Domain Knowledge for Cannabis Retail (Legal Markets)**

---

## 🎯 Purpose

This KB is the **foundation** for all HelixNet headshop implementations. It captures 25 years of Artemis Headshop (Bern, Switzerland) operational knowledge, with focus on:
- VAT compliance (Swiss Federal Tax Administration standards)
- Legal cannabis/CBD retail (THC <1% Swiss law)
- Customer types and sales techniques
- Product categories and inventory management
- Age verification and compliance
- Seasonal patterns and supplier relationships

**Target Audience:** New headshop owners, HelixNet implementers, sales staff training

---

## 💰 VAT: The Foundation (Lessons from €20M Mistakes)

### Swiss VAT Rates (2025)
| Category | Rate | Products | Example |
|----------|------|----------|---------|
| **Standard** | 8.1% | Most headshop products | Bongs, grinders, papers, lighters |
| **Reduced** | 2.5% | Food, books, medicine | CBD oils (medicinal), health products |
| **Exempt** | 0% | Exports, specific services | Tax-Free tourist sales (with forms) |

### Critical VAT Rules

**1. Discount Calculation (AFTER discount, not before):**
```
WRONG (Accenture-style):
  Item: CHF 100.00
  VAT (8.1%): CHF 8.10
  Discount (10%): CHF -10.00
  Total: CHF 98.10  ❌ ILLEGAL

CORRECT (HelixNet):
  Item: CHF 100.00
  Discount (10%): CHF -10.00
  Subtotal: CHF 90.00
  VAT (8.1%): CHF 7.29
  Total: CHF 97.29  ✅ LEGAL
```

**2. Mixed VAT Rates (Common at Felix's):**
```
Cart:
  Bong (CHF 120.00, 8.1% VAT)
  CBD Oil (CHF 45.00, 2.5% VAT - medicinal)
  Rolling Papers (CHF 3.50, 8.1% VAT)

Calculation:
  Subtotal Standard (8.1%): CHF 123.50 → VAT CHF 10.00
  Subtotal Reduced (2.5%): CHF 45.00 → VAT CHF 1.13
  Total: CHF 179.63

Receipt MUST show:
  Subtotal: CHF 168.50
  VAT 8.1%: CHF 10.00
  VAT 2.5%: CHF 1.13
  Total: CHF 179.63
```

**3. Freebies (Dangerous!):**
- **Inventory:** Tracked as -1 stock (cost recorded)
- **VAT:** CHF 0.00 (but original cost + VAT logged)
- **Compliance:** If value > CHF 500/year per customer → gift tax
- **Felix's Rule:** Max 1 free item per CHF 200 purchase (lighter, paper)

**4. Tourist Tax-Free (Export VAT Refund):**
- Customer must be non-Swiss resident
- Purchase > CHF 300 (single transaction)
- Form: Swiss Customs Tax-Free form (stamped at border)
- HelixNet prints form automatically for eligible sales
- VAT refunded by Global Blue or similar (not Felix directly)

### Banana Integration (Swiss Accounting)
Every transaction exports to Banana with:
```
Date | Receipt# | Customer | Subtotal | VAT8.1 | VAT2.5 | Total | Payment
2025-11-27 | R-001 | Anonymous | 168.50 | 10.00 | 1.13 | 179.63 | Cash
```

**Audit Trail:** Every VAT calculation logged to penny, retrievable for 10 years (Swiss law)

---

## 🛒 Product Categories (Felix's Taxonomy)

### 1. Smoking Accessories (60% of sales)
| Subcategory | VAT | Examples | Margin |
|-------------|-----|----------|--------|
| Bongs/Water Pipes | 8.1% | Glass, acrylic, silicone | 40-60% |
| Grinders | 8.1% | Metal, wood, plastic | 50-70% |
| Rolling Papers | 8.1% | OCB, Raw, Smoking, Rizla | 30-40% |
| Lighters | 8.1% | Clipper, Zippo | 25-35% |
| Filters/Tips | 8.1% | Cardboard, glass | 40-50% |

### 2. CBD Products (25% of sales, GROWING)
| Subcategory | VAT | THC Limit | Compliance |
|-------------|-----|-----------|------------|
| CBD Flowers | 8.1% | <1% THC | Lab cert required |
| CBD Oils | 2.5% | <1% THC | Medicinal classification |
| CBD Edibles | 8.1% | <1% THC | Food safety cert |
| CBD Cosmetics | 8.1% | <1% THC | Swissmedic approval |

**Critical:** Every CBD product MUST have:
- Lab certificate (THC <1%, CBD content verified)
- Swiss import permit (if imported)
- Batch number (traceability)
- Expiry date (oils, edibles)

### 3. Vaporizers (10% of sales, HIGH margin)
| Brand | VAT | Price Range | Margin |
|-------|-----|-------------|--------|
| Storz & Bickel (Volcano, Mighty) | 8.1% | CHF 300-700 | 30-40% |
| Pax | 8.1% | CHF 200-350 | 35-45% |
| DynaVap | 8.1% | CHF 80-150 | 50-60% |

**Sales Technique:** Upsell cleaning kit (CHF 15-25, 60% margin)

### 4. Miscellaneous (5% of sales)
- Clothing (t-shirts, hats) - 8.1% VAT
- Books/Magazines - 2.5% VAT (reduced rate)
- Stickers/Decor - 8.1% VAT
- Scales (legal for tobacco use) - 8.1% VAT

---

## 👥 Customer Types (Felix's 25-Year Typology)

### 1. Locals (50% of revenue, RECURRING)
- **Profile:** Swiss residents, ages 25-55, weekly/monthly buyers
- **Behavior:** Brand loyal, price-sensitive on papers/grinders
- **Sales:** Build relationships, loyalty discounts (5-10%)
- **Language:** Swiss German (primary), German, French

### 2. Tourists (35% of revenue, SEASONAL)
- **Profile:** EU/US tourists, ages 21-40, one-time buyers
- **Behavior:** Curiosity purchases, legal cannabis novelty
- **Sales:** Explain Swiss THC limits (<1%), recommend CBD flowers
- **Language:** English, German, French, Italian
- **Peak:** Summer (June-August), Christmas markets

### 3. Medical/Therapeutic (10% of revenue, GROWING)
- **Profile:** Ages 40-70, chronic pain/anxiety, doctor-referred
- **Behavior:** CBD oils focus, seek advice
- **Sales:** Discretion, medical-grade products (lab certs)
- **Language:** All Swiss languages, explain certifications

### 4. Collectors (5% of revenue, HIGH value)
- **Profile:** Ages 30-60, glass art enthusiasts
- **Behavior:** High-end bongs (CHF 500-2000), infrequent
- **Sales:** Showcase craftsmanship, limited editions
- **Special:** Invoice for insurance purposes

---

## 🔒 Compliance & Legal (Switzerland, 2025)

### Age Verification (MANDATORY)
- **Legal Age:** 18+ (Switzerland)
- **ID Required:** ALL sales (even if customer looks 40+)
- **Acceptable IDs:** Swiss ID, passport, EU ID card, driving license
- **Tourist IDs:** Passport ONLY (verify age calculation)
- **HelixNet:** Age verify screen BEFORE product selection

### THC Limits (Cannabis Law)
- **Legal:** <1% THC (dry weight)
- **Illegal:** ≥1% THC → criminal offense (shop closure risk)
- **Testing:** Supplier must provide lab cert (updated quarterly)
- **Spot Checks:** Federal customs random tests (3-5x per year)

### Record Keeping (Audit Requirements)
- **Sales:** All transactions logged, 10 years retention
- **Inventory:** Stock movements (in/out) with supplier invoices
- **CBD Certs:** Lab certificates filed per batch
- **Employee:** Sales staff trained on age verification (cert on file)

### Prohibited Sales
- ❌ To minors (<18)
- ❌ THC ≥1% products
- ❌ Synthetic cannabinoids (Spice, K2)
- ❌ Drug paraphernalia with residue
- ❌ Nitrous oxide (laughing gas) - recent ban

---

## 📅 Seasonal Patterns (Felix's 25-Year Data)

### Q1 (Jan-Mar): Slow Period
- **Revenue:** 15-20% of annual
- **Focus:** Locals, loyalty programs
- **Inventory:** Reduce stock, clear old CBD (expiry)
- **Staffing:** 1-2 staff, Felix + part-timer

### Q2 (Apr-Jun): Spring Ramp-Up
- **Revenue:** 25-30% of annual
- **Focus:** Tourist season begins (Easter, Pentecost)
- **Inventory:** Stock CBD flowers (outdoor season harvest)
- **Staffing:** 2 staff + Felix

### Q3 (Jul-Sep): PEAK SEASON
- **Revenue:** 40-45% of annual
- **Focus:** Tourists (summer holidays)
- **Inventory:** Full stock, daily restocking (papers, lighters)
- **Staffing:** 3 staff + Felix (10-hour days)

### Q4 (Oct-Dec): Christmas + Tax Planning
- **Revenue:** 20-25% of annual
- **Focus:** Christmas gifts (vaporizers, high-end bongs)
- **Inventory:** Reduce before year-end (tax optimization)
- **Staffing:** 2-3 staff + Felix

---

## 🤝 Supplier Relationships (Felix's Network)

### Primary Suppliers (90% of stock)
| Supplier | Products | Payment Terms | Margin |
|----------|----------|---------------|--------|
| **Ehle Glass** (Germany) | High-end bongs | Net 30 | 45-55% |
| **Raw/Smoking** (Spain) | Papers, tips | Net 45 | 30-40% |
| **Kannaway** (Switzerland) | CBD oils | Net 15 | 40-50% |
| **Storz & Bickel** (Germany) | Vaporizers | Prepay | 30-35% |

### Supplier Best Practices
- **Contracts:** Annual agreements (volume discounts)
- **Returns:** Defective only (no refunds on CBD after opening)
- **Minimum Orders:** CHF 500-1000 (free shipping threshold)
- **Payment:** Bank transfer (VAT invoices required)

---

## 💡 Sales Techniques (Felix's Secrets)

### Upselling Combos
1. **Bong Buyer:**
   - ✅ Grinder (CHF 15-30) - "You'll need this"
   - ✅ Cleaning solution (CHF 10) - "Keeps it working"
   - ✅ Lighter (CHF 2-5) - "Free with purchase over CHF 100"

2. **CBD Flower Buyer:**
   - ✅ Papers (CHF 3-5) - "Recommended for CBD"
   - ✅ Vaporizer (CHF 80-300) - "Healthier option"

3. **First-Time Tourist:**
   - ✅ Explain Swiss law (<1% THC)
   - ✅ CBD flower sample (small bag, CHF 10-15)
   - ✅ Papers + lighter (CHF 5 total)

### Handling Discounts (VAT-Safe)
- **Loyalty:** 5% off for CHF 1000+ annual spend
- **Bulk:** 10% off for CHF 300+ single purchase
- **Freebies:** Lighter or paper pack (value <CHF 5)
- **NEVER:** Percentage off per item (VAT calculation nightmare)

### Freebies Policy (Avoid VAT Traps)
- Max CHF 5 per transaction
- Max CHF 500 per customer per year
- Logged as "PROMO" line item (CHF 0.00, cost tracked)
- Annual review: If customer > CHF 500 freebies → flag for gift tax

---

## 🏪 Store Layout (Felix's Proven Design)

### Artemis Headshop (25 Years, Same Location)
```
┌─────────────────────────────────────┐
│  ENTRANCE (Age Verify Here)         │
│  ↓                                   │
│  ┌──────────┐  ┌──────────┐         │
│  │ CBD      │  │ Papers   │         │
│  │ Flowers  │  │ Grinders │         │
│  │ (Glass   │  │ Lighters │         │
│  │ Display) │  │ (Wall)   │         │
│  └──────────┘  └──────────┘         │
│                                      │
│  ┌───────────────────────┐          │
│  │ Bongs (Glass Cases)   │          │
│  │ High-End Display      │          │
│  └───────────────────────┘          │
│                                      │
│  ┌──────────┐  COUNTER (HelixNet)   │
│  │ Vapes    │  ├─ POS Terminal      │
│  │ (Locked  │  ├─ Cash Drawer       │
│  │ Cabinet) │  ├─ Receipt Printer   │
│  └──────────┘  └─ Age Verify Screen │
│                                      │
│  STORAGE/OFFICE (Back)               │
└─────────────────────────────────────┘
```

**Key Design Principles:**
1. **Age Verify FIRST** - Customer cannot browse before ID check
2. **CBD Visible** - Eye-level, professional (not "head shop" stigma)
3. **High-End Secured** - Bongs in glass cases (insurance requirement)
4. **Vapes Locked** - High-value items behind counter
5. **Counter Central** - Felix sees entire store (theft prevention)

---

## 🚨 Common Mistakes (DON'T DO THIS)

### 1. VAT Calculation Errors (Accenture-Level Fails)
❌ Applying VAT before discount
❌ Using single VAT rate for all products
❌ Rounding VAT per item (must round at total)
❌ Not logging freebies (audit red flag)

### 2. Compliance Failures
❌ Selling to minors (shop closure risk)
❌ CBD without lab certs (customs seizure)
❌ THC ≥1% products (criminal charges)
❌ No age verification policy (fine CHF 10,000+)

### 3. Inventory Management
❌ Overstocking CBD (6-month shelf life for flowers)
❌ Not rotating stock (FIFO for perishables)
❌ No supplier contracts (price volatility)
❌ Mixing personal/shop inventory (tax nightmare)

### 4. Customer Service
❌ Medical advice (liability - refer to doctor)
❌ Illegal product recommendations (undercover stings)
❌ Not explaining THC limits to tourists (reputation damage)

---

## 🎓 Training Requirements (New Staff)

### Day 1: Legal & Compliance
- Swiss cannabis law (THC <1%)
- Age verification (ID types, how to verify)
- Prohibited products (what NOT to sell)
- Emergency procedures (police, underage attempt)

### Week 1: Product Knowledge
- Product categories (what's what)
- VAT rates (which products, how to calculate)
- Common brands (Raw, OCB, Storz & Bickel)
- CBD basics (THC limits, lab certs)

### Month 1: Sales Techniques
- Customer types (locals vs tourists)
- Upselling (combos, cleaning kits)
- Discount policy (when, how much)
- HelixNet POS operation (age verify → checkout)

### Ongoing: HelixKB Updates
- New product KBs (how to sell, how to use)
- Regulatory changes (Swiss Federal updates)
- Seasonal promotions (Christmas, summer)

---

## 📊 KPIs (Felix's Dashboard)

### Daily Metrics
- **Revenue:** Target CHF 800-1200 (avg CHF 1000)
- **Transactions:** 15-30 per day
- **Average Ticket:** CHF 40-60
- **VAT Collected:** Track 8.1% and 2.5% separately

### Weekly Metrics
- **Top Products:** Papers, grinders, CBD flowers
- **Slow Movers:** Flag items <2 sales/week
- **Freebie Cost:** Max CHF 50/week
- **Supplier Orders:** 1-2 orders/week (restock)

### Monthly Metrics
- **Revenue Growth:** YoY comparison
- **Customer Retention:** Repeat buyers (loyalty program)
- **CBD vs Accessories:** Shift to CBD (higher margin)
- **Compliance Audits:** Zero violations

### Annual Metrics
- **Revenue:** Target CHF 350,000-450,000
- **Margin:** Average 45-50%
- **Customer Growth:** 5-10% new customers
- **KB Contributions:** 10+ per year (community growth)

---

## 🌍 Multi-Language Support (Swiss Market)

### Receipt Languages (Auto-Detect)
- **German:** Standard (Felix's default)
- **French:** Geneva, Lausanne customers
- **Italian:** Ticino, Italian tourists
- **English:** International tourists

### Product Descriptions (4 Languages)
Every product KB includes:
- DE: Produktbeschreibung
- FR: Description du produit
- IT: Descrizione del prodotto
- EN: Product description

**Example:** Storz & Bickel Volcano
- DE: "Premium Verdampfer für medizinisches Cannabis"
- FR: "Vaporisateur premium pour cannabis médical"
- IT: "Vaporizzatore premium per cannabis medico"
- EN: "Premium vaporizer for medical cannabis"

---

## 🔄 Felix's New Location (2025-2026)

### Opportunity
- Building renovation forces 1-year move
- Return after renovation (option, not guaranteed)
- Fresh start for HelixNet implementation

### HelixNet Advantages for New Location
1. **No Legacy POS:** Clean implementation
2. **Layout Design:** HelixNet-optimized from day 1
3. **Hardware:** Modern (tablet, cloud-ready)
4. **Training:** New staff trained on HelixNet only
5. **Compliance:** Built-in from transaction #1

### Requirements (When Location Found)
- **Space:** 40-60 sqm (same as current)
- **Location:** Central Bern (foot traffic)
- **Lease:** Min 3 years (stability)
- **Network:** Fiber internet (cloud POS backup)
- **Security:** Insurance-compliant (cameras, safes)

---

## 📖 Related KBs (To Be Created)

### Product-Specific
- KB-002: Storz & Bickel Volcano (how to sell, how to use)
- KB-003: Rolling Papers Comparison (OCB vs Raw vs Smoking)
- KB-004: CBD Compliance (Swiss law, lab certs)
- KB-005: Bong Cleaning (sales technique + customer education)

### Operational
- KB-010: Age Verification Workflow (HelixNet screen flow)
- KB-011: Tax-Free Tourist Sales (forms, process)
- KB-012: Supplier Ordering (Ehle, Raw, Kannaway)
- KB-013: Inventory Rotation (FIFO, expiry management)

### Business
- KB-020: Banana Integration (accounting export)
- KB-021: Loyalty Program (discount tiers)
- KB-022: Seasonal Promotions (Christmas, summer)
- KB-023: Insurance Requirements (high-value stock)

---

## 🏆 Success Criteria

This KB is successful when:
1. ✅ New headshop owner can read and understand Felix's 25-year model
2. ✅ HelixNet implementation includes VAT-correct from day 1
3. ✅ Staff trained on compliance (zero violations)
4. ✅ Community contributes 10+ product KBs (year 1)
5. ✅ Felix's new location launches with HelixNet (2025-2026)

---

## 📜 Changelog

- **2025-11-27 (v1.0.0):** Initial creation by angel, based on Felix's 25-year Artemis Headshop expertise. VAT-first approach inspired by Nespresso/Accenture failure (€20M penalty lesson).

---

## 👨‍💼 Contributor Credit

**Felix (Artemis Headshop, Bern)**
- 25 years operational experience
- Swiss cannabis retail expert
- VAT compliance (zero violations, 25 years)
- Founding HelixNet headshop vertical contributor

---

## 📧 KB Contribution Workflow

This KB is **approved** (foundation template). To contribute updates:
1. Email: `kb@helixnet.local`
2. Subject: `UPDATE HelixPOS_KB-001 - [Your Change]`
3. Attach: PDF with proposed changes
4. Response: ACCEPT/DECLINE within 48 hours
5. Credit: Silver badge for 5 approved updates

---

**End of HelixPOS_KB-001**
