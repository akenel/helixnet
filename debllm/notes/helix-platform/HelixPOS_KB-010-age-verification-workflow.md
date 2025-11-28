---
kb_id: HelixPOS_KB-010
title: Age Verification Workflow - HelixNet POS Screen Flow
domain: headshop-retail
language: en
contributor: Angel (HelixNet Developer)
category: operational
status: approved
version: 1.0.0
created: 2025-11-28
last_updated: 2025-11-28
applies_to: [helix-pos, artemis-headshop, swiss-retail]
vat_critical: false
compliance_level: critical
points: 3
---

# HelixPOS_KB-010: Age Verification Workflow

**Step-by-Step Guide: How Cashiers Verify Customer Age in HelixNet POS**

---

## 🎯 Purpose

This KB explains:
- When age verification is triggered
- What the cashier sees on screen
- How to properly verify an ID
- What happens if verification is skipped/bypassed
- Troubleshooting common issues

**Audience:** Cashiers (Pam, Ralph), new staff, trainers

---

## 🔄 Complete Workflow

### Overview Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                     AGE VERIFICATION FLOW                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   1. SCAN/ADD PRODUCT                                             │
│          │                                                        │
│          ▼                                                        │
│   ┌─────────────────┐                                            │
│   │ Is product      │ ── NO ──▶ Continue to cart                 │
│   │ age-restricted? │                                            │
│   └────────┬────────┘                                            │
│            │ YES                                                  │
│            ▼                                                      │
│   ┌─────────────────┐                                            │
│   │ Age already     │ ── YES ─▶ Continue to cart                 │
│   │ verified this   │          (flag set for session)            │
│   │ transaction?    │                                            │
│   └────────┬────────┘                                            │
│            │ NO                                                   │
│            ▼                                                      │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              AGE VERIFICATION MODAL                      │   │
│   │                                                          │   │
│   │  "This product requires age verification (18+)"          │   │
│   │                                                          │   │
│   │  [ ] I have verified the customer's ID                   │   │
│   │                                                          │   │
│   │  ID Type: [Swiss ID ▼]                                   │   │
│   │                                                          │   │
│   │     [CANCEL]              [VERIFY & ADD TO CART]         │   │
│   │                                                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│            │                                                      │
│            ├── [VERIFY] clicked ──▶ Product added, flag set      │
│            │                                                      │
│            └── [CANCEL] clicked ──▶ Product NOT added            │
│                                                                   │
│   2. CHECKOUT                                                     │
│          │                                                        │
│          ▼                                                        │
│   ┌─────────────────┐                                            │
│   │ Any restricted  │ ── NO ──▶ Normal checkout                  │
│   │ items in cart?  │                                            │
│   └────────┬────────┘                                            │
│            │ YES                                                  │
│            ▼                                                      │
│   ┌─────────────────┐                                            │
│   │ Age verification│ ── YES ─▶ Complete checkout                │
│   │ flag set?       │                                            │
│   └────────┬────────┘                                            │
│            │ NO (ERROR - should not happen)                       │
│            ▼                                                      │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  ⚠️ ERROR: Age verification required                     │   │
│   │                                                          │   │
│   │  Cannot checkout without verifying customer age.         │   │
│   │                                                          │   │
│   │     [GO BACK]              [VERIFY NOW]                  │   │
│   │                                                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📱 Screen-by-Screen Guide

### Screen 1: Scanning an Age-Restricted Product

**What You See:**
```
┌──────────────────────────────────────────────────────────────┐
│  HELIX POS - ARTEMIS HEADSHOP                    👤 Pam     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Current Transaction: TXN-20251128-0042                      │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  🔍 Scan barcode or search product...                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  CART                                                        │
│  ──────────────────────────────────────────────────────────  │
│  │ OCB Slim Rolling Papers     │  1 x CHF 1.50  │  CHF 1.50 │
│  │ Clipper Lighter             │  1 x CHF 2.50  │  CHF 2.50 │
│  ──────────────────────────────────────────────────────────  │
│                                                              │
│  Subtotal: CHF 4.00                                          │
│  VAT (8.1%): CHF 0.32                                        │
│  ──────────────────────────                                  │
│  TOTAL: CHF 4.32                                             │
│                                                              │
│  [ CHECKOUT ]                                                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Action:** Cashier scans barcode `7610000123456` (CBD Oil 10%)

---

### Screen 2: Age Verification Modal (Triggered)

**What You See:**
```
┌──────────────────────────────────────────────────────────────┐
│  HELIX POS - ARTEMIS HEADSHOP                    👤 Pam     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                                                        │ │
│  │  🔞 AGE VERIFICATION REQUIRED                          │ │
│  │  ─────────────────────────────────────────────────────│ │
│  │                                                        │ │
│  │  Product: CBD Oil 10% - 10ml                           │ │
│  │  Price: CHF 49.90                                      │ │
│  │                                                        │ │
│  │  This product is age-restricted.                       │ │
│  │  Swiss law requires customers to be 18+ years old.     │ │
│  │                                                        │ │
│  │  ┌─────────────────────────────────────────────────┐  │ │
│  │  │ ☑ I confirm I have checked the customer's ID    │  │ │
│  │  │   and verified they are 18 years or older.      │  │ │
│  │  └─────────────────────────────────────────────────┘  │ │
│  │                                                        │ │
│  │  ID Type Checked:                                      │ │
│  │  ┌──────────────────────────────────┐                 │ │
│  │  │ Swiss ID Card                  ▼ │                 │ │
│  │  └──────────────────────────────────┘                 │ │
│  │                                                        │ │
│  │  ┌─────────────┐    ┌──────────────────────────────┐  │ │
│  │  │   CANCEL    │    │    ✅ VERIFY & ADD TO CART   │  │ │
│  │  └─────────────┘    └──────────────────────────────┘  │ │
│  │                                                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**ID Type Dropdown Options:**
- Swiss ID Card
- Swiss Passport
- Swiss Driver's License
- EU/EEA ID Card
- Foreign Passport
- Residence Permit (B/C/L)

---

### Screen 3: After Verification (Product Added)

**What You See:**
```
┌──────────────────────────────────────────────────────────────┐
│  HELIX POS - ARTEMIS HEADSHOP                    👤 Pam     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Current Transaction: TXN-20251128-0042  ✅ Age Verified     │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  🔍 Scan barcode or search product...                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  CART                                                        │
│  ──────────────────────────────────────────────────────────  │
│  │ OCB Slim Rolling Papers     │  1 x CHF 1.50  │  CHF 1.50 │
│  │ Clipper Lighter             │  1 x CHF 2.50  │  CHF 2.50 │
│  │ 🔞 CBD Oil 10% - 10ml       │  1 x CHF 49.90 │ CHF 49.90 │
│  ──────────────────────────────────────────────────────────  │
│                                                              │
│  Subtotal: CHF 53.90                                         │
│  VAT (8.1%): CHF 3.57  |  VAT (2.5%): CHF 1.22              │
│  ──────────────────────────────                              │
│  TOTAL: CHF 58.69                                            │
│                                                              │
│  [ CHECKOUT ]                                                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Key Indicators:**
- `✅ Age Verified` badge shows at top
- `🔞` emoji marks age-restricted items in cart
- VAT correctly split (8.1% for papers/lighter, 2.5% for CBD oil)

---

### Screen 4: Checkout Confirmation

**What You See:**
```
┌──────────────────────────────────────────────────────────────┐
│  HELIX POS - CHECKOUT                            👤 Pam     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Transaction: TXN-20251128-0042                              │
│  ──────────────────────────────────────────────────────────  │
│                                                              │
│  Items: 3                                                    │
│  Subtotal: CHF 53.90                                         │
│  VAT (8.1%): CHF 3.57                                        │
│  VAT (2.5%): CHF 1.22                                        │
│  ──────────────────────────────                              │
│  TOTAL: CHF 58.69                                            │
│                                                              │
│  ──────────────────────────────────────────────────────────  │
│  COMPLIANCE                                                  │
│  ✅ Age verification completed (Swiss ID Card)              │
│  ✅ Cashier: Pam (pos-cashier)                              │
│  ✅ Timestamp: 2025-11-28 14:32:15 CET                      │
│  ──────────────────────────────────────────────────────────  │
│                                                              │
│  Payment Method:                                             │
│  [ CASH ]  [ VISA ]  [ TWINT ]  [ OTHER ]                   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              💳 COMPLETE CHECKOUT                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## ⚠️ Error Scenarios

### Error 1: Trying to Checkout Without Verification

**How It Happens:**
- Bug in system (should not occur normally)
- Session state lost (network issue)

**What You See:**
```
┌────────────────────────────────────────────────────────────┐
│  ⚠️ CHECKOUT BLOCKED                                        │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Your cart contains age-restricted items:                   │
│  • CBD Oil 10% - 10ml                                       │
│  • CBD Flower 'Alpine Dream' - 5g                           │
│                                                             │
│  Age verification is required before checkout.              │
│                                                             │
│  ┌─────────────┐    ┌──────────────────────────────────┐   │
│  │  GO BACK    │    │      🔞 VERIFY AGE NOW           │   │
│  └─────────────┘    └──────────────────────────────────┘   │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

**Action:** Click "VERIFY AGE NOW" → Modal appears → Complete verification

---

### Error 2: Customer Refuses to Show ID

**Scenario:** Customer says "I don't have ID" or "I'm obviously over 18"

**What to Do:**
1. Politely explain: "Swiss law requires ID verification for all CBD sales."
2. Offer alternatives: "Do you have any form of ID? Passport, driver's license?"
3. If refused: Click "CANCEL" on verification modal
4. Product is NOT added to cart
5. Complete transaction with remaining (non-restricted) items

**Script:**
> "I understand, but I'm required by Swiss law to verify age for CBD products. Without ID, I cannot complete this part of your purchase. I can ring up your other items though."

---

### Error 3: Customer is Under 18

**Scenario:** You check ID and calculate customer is 17 years old

**What to Do:**
1. DO NOT click "Verify & Add to Cart"
2. Click "CANCEL"
3. Politely explain: "I'm sorry, this product requires customers to be 18+. You'll be able to purchase this next year."
4. Complete transaction with non-restricted items only

**Script:**
> "I apologize, but this product is only available to customers 18 and older. Is there anything else I can help you with today?"

**DO NOT:**
- ❌ Sell anyway and hope nobody notices
- ❌ Ask a colleague to verify instead
- ❌ Let customer "come back later" and skip verification

---

## 📊 Audit Trail (What Gets Logged)

### Successful Verification
```json
{
  "event": "age_verification_completed",
  "transaction_id": "TXN-20251128-0042",
  "timestamp": "2025-11-28T14:32:15+01:00",
  "cashier_id": "pam",
  "cashier_role": "pos-cashier",
  "id_type": "swiss_id_card",
  "products_verified": [
    {"sku": "CBD-OIL-10ML", "name": "CBD Oil 10% - 10ml"}
  ],
  "result": "verified"
}
```

### Cancelled Verification
```json
{
  "event": "age_verification_cancelled",
  "transaction_id": "TXN-20251128-0042",
  "timestamp": "2025-11-28T14:31:45+01:00",
  "cashier_id": "pam",
  "product_attempted": {"sku": "CBD-OIL-10ML"},
  "reason": "customer_refused_id"
}
```

### Compliance Report (Daily)
```
DAILY COMPLIANCE SUMMARY - 2025-11-28
=====================================
Total Transactions: 47
Transactions with Age-Restricted Items: 12
Age Verifications Completed: 12 (100%)
Age Verifications Cancelled: 3
  - Customer refused ID: 2
  - Customer underage: 1

Flagged for Review: 0
```

---

## ❓ FAQ

### Q: Can I verify once and add multiple CBD products?
**A:** Yes. Once verified for a transaction, all subsequent age-restricted products are added without re-verification. The flag is set per-transaction.

### Q: What if I accidentally verified for the wrong customer?
**A:** Cancel the transaction and start fresh. Each transaction has its own verification state. Report to manager if this happens.

### Q: The verification modal is stuck/not appearing - what do I do?
**A:** Refresh the POS page. If persistent, restart the browser. If still broken, contact Ralph (tech-devops) and process transaction manually with paper record.

### Q: Customer shows foreign ID I don't recognize - is it valid?
**A:** Foreign passports are valid. If unsure about other foreign IDs, ask for passport instead. When in doubt, don't verify.

### Q: Do I log the customer's ID number?
**A:** NO. Never record ID numbers, names, or take photos of IDs. You only confirm that you saw a valid ID and calculated age. Privacy law (GDPR/Swiss DSG) applies.

---

## 🔗 Related KBs

- **HelixPOS_KB-001:** Felix's Headshop 101 (compliance overview)
- **HelixPOS_KB-004:** CBD Compliance - Swiss Law
- **ERROR-051:** Age Verification Bypass Detected

---

## 📧 KB Contribution

**To suggest workflow improvements:**
1. Email: `kb@helixnet.local`
2. Subject: `UPDATE HelixPOS_KB-010 - [Your Suggestion]`
3. Include: Screenshot if UI-related

---

## 📜 Changelog

- **2025-11-28 (v1.0.0):** Initial creation by angel. Screen mockups based on HelixNet POS v2.1.0 design.

---

**End of HelixPOS_KB-010**
