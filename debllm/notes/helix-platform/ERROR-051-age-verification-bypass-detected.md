---
error_id: ERROR-051
title: Age Verification Bypass - CBD Sale to Unverified Customer
service: helix-platform
error_domain: functional
severity: critical
resolution_group: business-functional
assignee: felix
first_seen: 2025-11-28
last_seen: 2025-11-28
occurrence_count: 1
in_kb: true
auto_fix: false
fix_command: null
requires_human: true
requires_business_decision: true
related_errors:
  - ERROR-052
  - ERROR-053
keywords: [age, verification, compliance, cbd, minor, legal, bypass, 18+]
patterns:
  - "age.*not verified"
  - "age_verified.*false.*cbd"
  - "restricted.*product.*unverified"
  - "compliance.*age.*bypass"
---

## 🔍 Symptoms
- Audit log shows age-restricted product sold without age verification flag
- Transaction record: `is_age_verified: false` with CBD product in cart
- Compliance report flags transaction as "potential violation"
- **Legal exposure:** Swiss law requires 18+ verification for CBD/tobacco products

## 🧠 Common Causes
1. **Staff bypassed verification** (40%) - Rushed transaction, clicked "skip"
2. **Software bug in checkout flow** (30%) - Age gate not enforced for certain products
3. **Product miscategorized** (20%) - CBD item marked as `is_age_restricted: false`
4. **Session state bug** (10%) - Previous customer's verification carried over

## 👥 Resolution Group
**Primary:** business-functional (Store manager reviews incident)
**Secondary:** tech-devops (if software bug)
**Decision Maker:** Felix (store owner - legal liability)
**Escalation Path:** If pattern detected (multiple incidents) → Legal counsel, insurance

## 🩺 Diagnosis Steps

### 1. Identify the transaction
```sql
-- Find transactions with age-restricted items but no verification
SELECT
    t.id,
    t.receipt_number,
    t.created_at,
    t.cashier_id,
    u.username as cashier_name,
    t.is_age_verified,
    p.name as product_name,
    p.is_age_restricted
FROM transactions t
JOIN transaction_line_items li ON t.id = li.transaction_id
JOIN products p ON li.product_id = p.id
JOIN users u ON t.cashier_id = u.id
WHERE p.is_age_restricted = true
  AND t.is_age_verified = false
ORDER BY t.created_at DESC;
```

### 2. Check if product is correctly flagged
```sql
-- Verify product age restriction setting
SELECT sku, name, is_age_restricted, category
FROM products
WHERE is_age_restricted = true
ORDER BY category;
```

### 3. Review cashier's recent transactions
```sql
-- Check if this cashier has pattern of bypassing
SELECT
    u.username,
    COUNT(*) as total_transactions,
    SUM(CASE WHEN is_age_verified = false AND EXISTS (
        SELECT 1 FROM transaction_line_items li
        JOIN products p ON li.product_id = p.id
        WHERE li.transaction_id = t.id AND p.is_age_restricted = true
    ) THEN 1 ELSE 0 END) as unverified_restricted_sales
FROM transactions t
JOIN users u ON t.cashier_id = u.id
WHERE t.created_at > NOW() - INTERVAL '30 days'
GROUP BY u.username
ORDER BY unverified_restricted_sales DESC;
```

### 4. Check if software enforces age gate
```bash
# Review age verification enforcement in code
grep -n "is_age_restricted\|age_verified" src/routes/pos_router.py
```

### 5. Review CCTV footage (if available)
```
Time: [transaction timestamp]
Location: POS terminal #1
Purpose: Verify if ID was checked but not recorded in system
```

## ✅ Resolution

### Immediate Actions (Within 1 Hour)

**Step 1: Document the Incident**
```markdown
Incident Report: Age Verification Bypass
Date: 2025-11-28
Time: [timestamp from transaction]
Transaction ID: [id]
Receipt: [receipt_number]
Cashier: [username]
Product: [CBD product name]
Customer Description: [if known]
Age Verified in System: NO
ID Checked (per CCTV/interview): [YES/NO/UNKNOWN]
```

**Step 2: Interview Cashier**
- Did you check the customer's ID?
- If yes, why wasn't it recorded in the system?
- If no, why was the verification skipped?
- Was the customer obviously over 18?

**Step 3: Technical Investigation**
```bash
# Check if age gate can be bypassed
curl -X POST https://helix.local/api/v1/pos/checkout \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "transaction_id": "TEST-AGE",
    "items": [{"product_id": "CBD-OIL-10ML", "quantity": 1}],
    "age_verified": false
  }'

# Expected: 400 Bad Request - Age verification required
# Bug: 200 OK - Age gate bypassed
```

### Software Fix (If Bug Found)
```python
# src/routes/pos_router.py - checkout endpoint

@router.post("/checkout")
async def checkout(request: CheckoutRequest, ...):
    # MUST enforce age verification for restricted products
    cart_items = await get_cart_items(request.transaction_id)

    has_restricted = any(item.product.is_age_restricted for item in cart_items)

    if has_restricted and not request.age_verified:
        raise HTTPException(
            status_code=400,
            detail="Age verification required for restricted products. "
                   "Please verify customer is 18+ before completing sale."
        )

    # Continue with checkout...
```

### Staff Training (If Human Error)
```markdown
Remedial Training Required:
- [ ] Review Swiss age verification law (18+ for CBD, tobacco)
- [ ] Walk through HelixNet age verification workflow
- [ ] Sign updated compliance acknowledgment
- [ ] Shadow experienced cashier for 1 shift
- [ ] Manager spot-checks for 2 weeks
```

### Disciplinary Action (If Repeated)
| Offense | Action |
|---------|--------|
| 1st | Verbal warning + training |
| 2nd | Written warning |
| 3rd | Suspension (1 day) |
| 4th | Termination |

**Note:** If cashier sold to actual minor → Immediate suspension pending investigation

## 📝 Notes

### Swiss Legal Requirements (2025)
- **Age Limit:** 18+ for CBD products (cannabis-derived)
- **ID Check:** Required for ALL sales (even if customer appears older)
- **Acceptable IDs:** Swiss ID, passport, EU ID card, driver's license
- **Record Keeping:** Not legally required to log ID number, but must verify
- **Penalties:**
  - Fine: CHF 5,000-50,000 per violation
  - License Risk: Repeated violations → shop closure
  - Criminal: Knowingly selling to minors → criminal charges

### Why HelixNet Enforces Age Gate
1. **Legal compliance:** Swiss law requires verification
2. **Audit trail:** If inspected, we can prove process was followed
3. **Insurance:** Policy requires documented compliance procedures
4. **Staff protection:** Clear process = staff knows what to do

### Felix's Policy (Artemis Headshop)
> "ID every customer, every time, no exceptions."
> "If they look 60, check. If they complain, explain Swiss law."
> "One bypass = one warning. Two bypasses = fired."

### System Safeguards (Should Be In Place)
1. **Hard block:** Cannot checkout age-restricted items without verification flag
2. **Modal confirmation:** "I have verified this customer is 18+ years old"
3. **Audit log:** Every verification recorded with timestamp + cashier ID
4. **Manager alert:** Email if >3 unverified attempts in 1 hour (possible bypass attempt)

### False Positive Considerations
- System bug logged `false` but cashier did verify (data issue)
- Verification happened but network glitch lost the flag
- Product was incorrectly marked as age-restricted

In these cases:
- Fix the data issue
- Add audit note explaining discrepancy
- No disciplinary action if CCTV confirms verification

## 📜 History
- **2025-11-28 14:00** (compliance-bot): Flagged transaction in daily audit
- **2025-11-28 14:15** (ralph): Reviewed audit log, confirmed bypass
- **2025-11-28 14:30** (felix): Interviewed cashier (pam) - claims she checked ID
- **2025-11-28 14:45** (angel): Found software bug - age gate not enforced for combos
- **2025-11-28 15:00** (angel): Deployed hotfix
- **2025-11-28 15:30** (pam): Cleared of wrongdoing (software bug, ID was checked)
- **2025-11-28 16:00** (felix): Added combo products to age verification test suite

## 🔗 References
- Swiss cannabis law: https://www.bag.admin.ch/bag/en/home/gesund-leben/sucht-und-gesundheit/cannabis.html
- HelixPOS_KB-001: Felix's Headshop 101 (Compliance section)
- Age verification workflow: `docs/age-verification-flow.md`
- Incident report template: `docs/templates/incident-report.md`
