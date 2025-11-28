---
error_id: ERROR-050
title: VAT Calculated Before Discount (Accenture-Style Error)
service: helix-platform
error_domain: functional
severity: critical
resolution_group: business-functional
assignee: sales-team
first_seen: 2025-11-28
last_seen: 2025-11-28
occurrence_count: 1
in_kb: true
auto_fix: false
fix_command: null
requires_human: true
requires_business_decision: true
related_errors:
  - ERROR-051
  - ERROR-042
keywords: [vat, tax, discount, calculation, compliance, swiss, legal, accenture]
patterns:
  - "VAT.*before.*discount"
  - "discount.*after.*VAT"
  - "tax calculation.*incorrect"
  - "receipt.*VAT.*wrong"
---

## 🔍 Symptoms
- Customer receipt shows higher total than expected after discount
- Pam reports: "The math doesn't add up - customer paid more VAT than they should"
- Daily VAT report shows inflated tax amounts
- Banana export (accounting) shows discrepancy with actual cash collected
- **Federal Tax Administration audit risk** (Swiss VAT law violation)

## 🧠 Common Causes
1. **Code regression after update** (50%) - Developer changed calculation order
2. **Custom discount logic bypassed VAT recalc** (30%) - New feature broke existing flow
3. **Database trigger misconfigured** (15%) - Trigger calculates VAT on original price
4. **Third-party integration override** (5%) - External system sent pre-calculated VAT

## 👥 Resolution Group
**Primary:** business-functional (Sales team identifies scope of impact)
**Secondary:** tech-devops (implements code fix)
**Decision Maker:** Felix/Store Manager (approve refund strategy)
**Escalation Path:** If >100 transactions affected → Legal review (Swiss VAT compliance)

## 🩺 Diagnosis Steps

### 1. Verify calculation order in recent transaction
```sql
-- Check a specific receipt
SELECT
    receipt_number,
    subtotal_before_discount,
    discount_amount,
    subtotal_after_discount,
    vat_amount,
    total
FROM transactions
WHERE receipt_number = 'R-2025-001234'
ORDER BY created_at DESC
LIMIT 1;
```

### 2. Compare expected vs actual VAT
```python
# Manual verification
subtotal = 100.00
discount = 10.00  # 10%
vat_rate = 0.081  # 8.1%

# WRONG (Accenture-style)
wrong_vat = subtotal * vat_rate  # CHF 8.10
wrong_total = subtotal + wrong_vat - discount  # CHF 98.10

# CORRECT (Swiss law)
correct_subtotal = subtotal - discount  # CHF 90.00
correct_vat = correct_subtotal * vat_rate  # CHF 7.29
correct_total = correct_subtotal + correct_vat  # CHF 97.29

# Difference per transaction: CHF 0.81 (overcharged)
```

### 3. Check how many transactions affected
```sql
-- Find transactions with incorrect VAT pattern
-- (VAT amount too high relative to discount)
SELECT COUNT(*) as affected_count,
       SUM(vat_amount) as total_vat_collected,
       SUM(discount_amount) as total_discounts
FROM transactions
WHERE discount_amount > 0
  AND created_at > '2025-11-25 00:00:00'
  AND vat_amount > (subtotal_after_discount * 0.081 * 1.01);  -- 1% tolerance
```

### 4. Identify code change that introduced bug
```bash
# Check recent commits to checkout/VAT logic
git log --oneline --since="2025-11-20" -- src/routes/pos_router.py src/services/
```

### 5. Review current calculation code
```bash
grep -n "vat\|VAT\|discount" src/routes/pos_router.py | head -30
```

## ✅ Resolution

### Step 1: Immediate Hotfix (Stop the Bleeding)
**Priority:** Within 1 hour of detection

```python
# Fix in src/routes/pos_router.py - checkout endpoint
# WRONG:
vat_amount = subtotal * vat_rate
total = subtotal + vat_amount - discount_amount

# CORRECT:
discounted_subtotal = subtotal - discount_amount
vat_amount = discounted_subtotal * vat_rate
total = discounted_subtotal + vat_amount
```

### Step 2: Deploy Fix
```bash
# Rebuild and restart
docker restart helix-platform

# Verify fix with test transaction
curl -X POST https://helix.local/api/v1/pos/checkout \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"transaction_id": "TEST-001", "discount_percent": 10}'
```

### Step 3: Quantify Impact
```sql
-- Calculate total overcharged VAT
SELECT
    COUNT(*) as affected_transactions,
    SUM(vat_amount - (subtotal_after_discount * 0.081)) as vat_overcharge,
    MIN(created_at) as first_affected,
    MAX(created_at) as last_affected
FROM transactions
WHERE discount_amount > 0
  AND vat_amount > (subtotal_after_discount * 0.081 * 1.01);
```

### Step 4: Customer Remediation (Business Decision Required)
**Options:**

**Option A: Proactive Refund (Recommended)**
- Email all affected customers with apology
- Offer refund of VAT difference (CHF X.XX)
- Provide corrected receipt PDF

**Option B: Refund on Request**
- Wait for customer complaints
- Refund when requested
- Risk: Reputational damage if discovered by media/regulator

**Option C: Credit Note**
- Issue credit notes for future purchases
- No cash refund
- Risk: Customers may not return

**Felix's Recommendation:** Option A (Proactive Refund)
- Builds trust
- Avoids Federal Tax Administration scrutiny
- Cost: ~CHF 50-200 depending on transaction count

### Step 5: Regulatory Reporting (If Required)
```
If total VAT overcharge > CHF 1000 or > 50 transactions:
- File amended VAT return with Federal Tax Administration
- Document error, cause, and remediation
- Retain records for 10 years (Swiss law)
```

## 📝 Notes

### Why This is Critical (The Accenture Lesson)
- Accenture/Nespresso paid €20M+ penalty for similar VAT error
- Swiss Federal Tax Administration does random audits
- Incorrect VAT = tax fraud (even if unintentional)
- Customer trust: Swiss customers expect precision

### Felix's Golden Rule
> "VAT is calculated on what the customer ACTUALLY pays, not what the item costs."
> - Apply discount FIRST
> - Calculate VAT SECOND
> - Round at the TOTAL, not per item

### Prevention Measures
1. **Unit tests:** Add test case for discount + VAT calculation order
2. **Code review:** Any change to checkout requires 2 approvals
3. **Daily reconciliation:** Compare VAT collected vs expected (automated alert)
4. **Regression testing:** Run VAT calculation suite before every release

### Impact Assessment
- **Legal Risk:** HIGH (Swiss VAT compliance violation)
- **Financial Risk:** MEDIUM (refunds + potential fines)
- **Reputational Risk:** HIGH (customer trust, local press)
- **Technical Risk:** LOW (fix is straightforward)

### Mixed VAT Rates Complexity
Remember: Swiss VAT has multiple rates
- 8.1% (standard) - most headshop products
- 2.5% (reduced) - CBD oils (medicinal), books

Each rate must be calculated correctly AFTER discount:
```
Cart: Bong (CHF 100, 8.1%) + CBD Oil (CHF 50, 2.5%)
Discount: 10% on total (CHF 15)

WRONG: VAT then discount
  Bong VAT: CHF 8.10
  Oil VAT: CHF 1.25
  Discount: -CHF 15
  Total: CHF 144.35  ❌

CORRECT: Discount then VAT (proportional)
  Bong after discount: CHF 90 → VAT CHF 7.29
  Oil after discount: CHF 45 → VAT CHF 1.13
  Total: CHF 143.42  ✅

Difference: CHF 0.93 (overcharged)
```

## 📜 History
- **2025-11-28 10:00** (pam): Noticed receipt math "felt wrong" on discounted sale
- **2025-11-28 10:15** (ralph): Confirmed bug via database query (12 transactions affected)
- **2025-11-28 10:30** (angel): Identified code regression in commit abc123
- **2025-11-28 11:00** (angel): Deployed hotfix
- **2025-11-28 11:30** (felix): Approved proactive refund strategy (Option A)
- **2025-11-28 12:00** (sales-team): Sent refund emails to 12 affected customers

## 🔗 References
- Swiss VAT law: https://www.estv.admin.ch/estv/en/home/value-added-tax.html
- HelixPOS_KB-001: Felix's Headshop 101 (VAT section)
- Accenture/Nespresso case study: [internal wiki]
- Unit test suite: `src/tests/test_vat_calculation.py`
