---
kb_id: HelixPOS_KB-004
title: CBD Compliance - Swiss Cannabis Law & Retail Requirements
domain: headshop-retail
language: en
contributor: Felix (Artemis Headshop, Bern, Switzerland - 25 years)
category: compliance
status: approved
version: 1.0.0
created: 2025-11-28
last_updated: 2025-11-28
applies_to: [helix-pos, artemis-headshop, swiss-retail]
vat_critical: true
compliance_level: critical
related_products: [CBD-OIL-10ML, CBD-FLOWER-5G, CBD-PREROLL-1G, CBD-GUMMIES-100MG]
points: 10
---

# HelixPOS_KB-004: CBD Compliance - Swiss Cannabis Law & Retail Requirements

**Everything You Need to Know to Sell CBD Legally in Switzerland**

---

## 🎯 Purpose

This KB is **MANDATORY READING** for all staff selling CBD products. It covers:
- Swiss cannabis law (what's legal, what's not)
- THC limits and lab certification requirements
- Age verification and ID checking
- Record keeping and audit trail
- What to do if police/customs inspect
- Penalties for non-compliance

**Non-compliance = Shop closure, fines up to CHF 50,000, criminal charges**

---

## ⚖️ Swiss Cannabis Law (2025)

### The 1% Rule

**Legal:** CBD products with **<1% THC** (delta-9-tetrahydrocannabinol)
**Illegal:** Products with **≥1% THC**

```
┌─────────────────────────────────────────────────────────────┐
│                    SWISS THC THRESHOLD                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   0%  ──────────────── 0.99% ──── 1.0% ───────────────→ THC │
│   │                      │          │                        │
│   │      ✅ LEGAL        │    ❌ ILLEGAL                     │
│   │   (CBD products)     │    (Cannabis/Marijuana)           │
│   │                      │          │                        │
│   │   - Sell freely      │    - Criminal offense             │
│   │   - Age 18+          │    - Fines + imprisonment         │
│   │   - Lab cert needed  │    - Shop closure                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Legal Authority
- **Federal Act:** Narcotics Act (BetmG/LStup)
- **Enforcement:** Federal Office of Public Health (BAG/OFSP)
- **Local:** Cantonal police, customs (Zoll)

### What This Means for Retail
1. **Every CBD product** must have lab certificate proving THC <1%
2. **Age 18+** required for ALL CBD sales (tobacco law applies)
3. **No medical claims** unless product is Swissmedic-approved
4. **Clear labeling** required (THC content, CBD content, batch number)

---

## 📋 Product Requirements

### Lab Certification (MANDATORY)

Every CBD product in your inventory MUST have:

| Document | What It Shows | Retention |
|----------|---------------|-----------|
| **Lab Certificate** | THC <1%, CBD content, terpene profile | 5 years |
| **Batch Number** | Links to specific production run | On product label |
| **Import Permit** | BAG approval (if imported) | 5 years |
| **Supplier Invoice** | Chain of custody | 10 years |

### Acceptable Lab Certificates
- Swiss labs (preferred): Labor Spiez, Bern Cantonal Lab
- EU labs (accepted): Must be ISO 17025 accredited
- Must be **dated within 12 months** (older = request new test)

### What to Check on Lab Certificate
```
✅ Product name matches what you're selling
✅ Batch number matches product label
✅ THC result: <1.0% (NOT "below detection limit" - need actual number)
✅ Date: Within 12 months
✅ Lab accreditation number visible
```

### Red Flags (DO NOT SELL)
- ❌ No lab certificate available
- ❌ Certificate from unknown/non-accredited lab
- ❌ Batch number doesn't match
- ❌ THC listed as "N/A" or "not tested"
- ❌ Certificate older than 12 months

---

## 🔞 Age Verification

### Legal Requirement
- **Age:** 18+ (Swiss tobacco law applies to CBD)
- **Verification:** EVERY sale, EVERY customer
- **No exceptions:** Even if customer is obviously 60+ years old

### Acceptable ID Documents
| Document | Valid | Notes |
|----------|-------|-------|
| Swiss ID card | ✅ | Most common |
| Swiss passport | ✅ | |
| Swiss driver's license | ✅ | Check expiry |
| EU/EEA ID card | ✅ | 27 EU countries + Norway, Iceland, Liechtenstein |
| Foreign passport | ✅ | Check expiry, verify DOB |
| Residence permit (B/C/L) | ✅ | With photo |
| Student ID | ❌ | NOT valid (no DOB) |
| Credit card | ❌ | NOT valid |

### How to Calculate Age
```
Today: 2025-11-28
Customer DOB: 2007-11-29

Customer turns 18 on: 2025-11-29
Today they are: 17 years old

RESULT: ❌ CANNOT SELL - Customer is underage by 1 day
```

### HelixNet Age Verification Flow
```
┌─────────────────────────────────────────────────────────────┐
│                   AGE VERIFICATION SCREEN                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Cart contains age-restricted items:                        │
│   • CBD Oil 10% - 10ml                                       │
│   • CBD Flower 'Alpine Dream' - 5g                           │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  I confirm I have verified the customer's ID and    │   │
│   │  they are 18 years of age or older.                 │   │
│   │                                                     │   │
│   │  ID Type: [Dropdown: Swiss ID / Passport / ...]     │   │
│   │                                                     │   │
│   │         [ VERIFY & CONTINUE ]                       │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                              │
│   [ CANCEL TRANSACTION ]                                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Record Keeping (Audit Requirements)

### What to Keep (Swiss Law)

| Record | Retention | Format |
|--------|-----------|--------|
| Sales transactions | 10 years | HelixNet database + backup |
| Lab certificates | 5 years | PDF (digital OK) |
| Supplier invoices | 10 years | PDF or paper |
| Import permits | 5 years | PDF or paper |
| Employee training records | Duration of employment | Signed certificates |
| Age verification log | 10 years | HelixNet database |

### HelixNet Automatic Logging
Every CBD sale records:
- Transaction ID, timestamp
- Products sold (SKU, batch number)
- Cashier ID
- Age verification flag (true/false)
- Payment method
- Customer type (anonymous/registered)

### Where Records Are Stored
```
Production:
  Database: PostgreSQL (helix-core)
  Backups: MinIO (daily) + off-site (weekly)
  Retention: 10 years (automatic archival after 2 years)

Documents:
  Lab certs: debllm/notes/compliance/lab-certs/
  Invoices: MinIO bucket (supplier-invoices)
```

---

## 🚨 Police/Customs Inspection

### What Happens During Inspection
1. Officers identify themselves (show badge)
2. Request to see: Products, lab certificates, sales records
3. May take samples for testing
4. May review recent transactions

### Your Rights
- ✅ Ask for identification (badge number)
- ✅ Request a witness present (call Felix)
- ✅ Take notes of what they inspect
- ❌ Cannot refuse inspection (obstruction = worse)
- ❌ Cannot destroy records during inspection

### What to Do

**Step 1: Stay Calm**
> "Good morning, how can I help you?"

**Step 2: Verify Identity**
> "May I see your identification please?"

**Step 3: Call Owner**
> "I'll cooperate fully. May I contact the store owner to be present?"

**Step 4: Provide Documents**
- Lab certificates (binder behind counter)
- Recent sales log (HelixNet export)
- Supplier invoices (office filing cabinet)

**Step 5: Document Everything**
- Officer names and badge numbers
- What they inspected
- What samples taken (if any)
- Any statements made

### If They Find a Problem
- DO NOT argue
- DO NOT admit fault
- SAY: "I understand. I'll need to consult with the owner and our legal advisor."
- DOCUMENT: What they claimed was wrong

### Felix's Emergency Number
```
Felix Mobile: [number on file in office]
Call immediately if:
- Police/customs arrive
- Product seized
- You're asked to make a statement
```

---

## 💰 VAT for CBD Products

### Which VAT Rate?

| Product Type | VAT Rate | Justification |
|--------------|----------|---------------|
| CBD Oils (medicinal) | 2.5% | Reduced rate (therapeutic) |
| CBD Flowers | 8.1% | Standard rate (tobacco substitute) |
| CBD Edibles | 8.1% | Standard rate (food product) |
| CBD Cosmetics | 8.1% | Standard rate (cosmetic) |

### Why CBD Oils Get 2.5%
- Classified as therapeutic/medicinal products
- Must be marketed for wellness, not recreation
- If marketed for "smoking" or "recreation" → 8.1%

### HelixNet Product Setup
Each CBD product must have correct VAT category:
```python
# In product setup
{
    "sku": "CBD-OIL-10ML",
    "name": "CBD Oil 10% - 10ml",
    "vat_category": "reduced",  # 2.5%
    "vat_rate": 0.025
}

{
    "sku": "CBD-FLOWER-5G",
    "name": "CBD Flower 'Alpine Dream' - 5g",
    "vat_category": "standard",  # 8.1%
    "vat_rate": 0.081
}
```

---

## ❌ What You CANNOT Sell

### Prohibited Products
| Product | Why | Penalty |
|---------|-----|---------|
| THC ≥1% cannabis | Narcotics law | Criminal charges |
| Synthetic cannabinoids (Spice, K2) | Banned substance | Criminal charges |
| Products without lab cert | Unverified THC content | Fines, shop closure |
| CBD to minors (<18) | Tobacco law | Fines CHF 5,000-50,000 |

### Prohibited Claims
You CANNOT say:
- ❌ "This cures anxiety/pain/insomnia" (medical claim)
- ❌ "This is medicine" (unless Swissmedic-approved)
- ❌ "Doctor recommended" (unless actually prescribed)

You CAN say:
- ✅ "Many customers use this for relaxation"
- ✅ "CBD is known for its calming properties"
- ✅ "This is a wellness product"

---

## 🏋️ Staff Training Requirements

### Initial Training (Before First Shift)
| Topic | Duration | Certification |
|-------|----------|---------------|
| Swiss cannabis law | 30 min | Signed acknowledgment |
| Age verification | 15 min | Signed acknowledgment |
| Lab certificate verification | 15 min | Signed acknowledgment |
| What to do if inspected | 15 min | Signed acknowledgment |

### Annual Refresher
- Review any law changes
- Test on ID verification
- Practice inspection scenario
- Re-sign compliance acknowledgment

### Training Records Location
```
File: debllm/notes/compliance/training/
Format: [date]-[employee]-compliance-training.pdf
Retention: Duration of employment + 2 years
```

---

## 📊 Compliance Checklist (Daily)

### Opening Checklist
- [ ] Lab certificate binder behind counter
- [ ] Age verification policy visible
- [ ] "18+" signage displayed
- [ ] HelixNet system operational

### Per-Sale Checklist (CBD Products)
- [ ] Customer ID checked
- [ ] Age calculated (18+)
- [ ] Age verification clicked in HelixNet
- [ ] Product batch number matches lab cert on file

### Closing Checklist
- [ ] No unverified CBD sales in log
- [ ] Lab cert binder secured
- [ ] Any issues noted for Felix

---

## 🔗 Related KBs

- **HelixPOS_KB-001:** Felix's Headshop 101 (VAT section)
- **HelixPOS_KB-002:** Storz & Bickel Volcano (vaporizer for CBD)
- **KB-010:** Age Verification Workflow (detailed screen flow)
- **ERROR-051:** Age Verification Bypass Detected

---

## 📚 Legal References

### Federal Laws
- Narcotics Act (BetmG/LStup): https://www.fedlex.admin.ch/eli/cc/1952/241_241_245/de
- Tobacco Products Act: https://www.fedlex.admin.ch/eli/cc/2021/609/de

### Regulatory Bodies
- Federal Office of Public Health (BAG): https://www.bag.admin.ch/
- Swiss Customs: https://www.ezv.admin.ch/
- Swissmedic: https://www.swissmedic.ch/

### Industry Resources
- Swiss Hemp Association (SIGA): Industry standards
- Cantonal lab testing services: Varies by canton

---

## 📧 KB Contribution

This KB was created by Felix (Artemis Headshop, Bern) based on 25 years of compliance experience and current Swiss law.

**To report outdated information or law changes:**
1. Email: `compliance@helixnet.local`
2. Subject: `URGENT: KB-004 Law Change - [Description]`
3. Include: Link to official source, effective date
4. Response: Within 24 hours (compliance-critical)

---

## 📜 Changelog

- **2025-11-28 (v1.0.0):** Initial creation by angel, reviewed by Felix. Based on Swiss Narcotics Act and current BAG guidance.

---

**⚠️ DISCLAIMER:** This KB is for educational purposes. Always consult current Swiss federal and cantonal law. Laws change - verify with BAG/OFSP for latest requirements.

---

**End of HelixPOS_KB-004**
