# BLQ KB-018: Network Error Incident - POS Checkout Failure

**Priority:** HIGH
**Reported by:** Pam (Artemis Cashier)
**Assigned to:** Ralph (Support)
**Date:** 2025-11-30
**Status:** OPEN - Awaiting Investigation

---

## Incident Summary

```
🚨 INCIDENT REPORT - ARTEMIS POS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Location:       Artemis Headshop, Littau
Reporter:       Pam (Cashier)
Time:           2025-11-30 (during Felix's absence)
Error:          "Network Error" during checkout
Attempts:       3 phone calls + 1 Telegram message
Felix status:   Airplane mode (at Raber Leder, Küssnacht)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Error Details

### Screenshot from Pam

```
💳 Checkout
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Order Summary:
├─ 1x Weed Leaf Grinder 4er Assort     CHF 32.50
├─ 1x SLX Grinder V2.5 Black 62mm      CHF 89.70
└─ 1x Elektro Grinder Stiftform Schwarz CHF 45.50

🏷️ Discount
💡 Cashiers: max 10% | Managers: max 25% | Admin: unlimited

Subtotal:           CHF 167.70
Discount (25%):    -CHF 41.93
VAT (7.7%):         CHF 9.68      ⚠️ SEE ISSUE #2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL:              CHF 135.46
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 Payment Method: [Selected]

⚠️ Dry Run Preview:
• Cash drawer: +CHF 135.46
• Inventory: -1 each item
• Receipt: Will print to POS printer
• Daily total: +CHF 135.46

❓ Does everything look correct?

>>> ERROR: "Complete transaction for CHF 135.46? Network Error" <<<

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Issues Identified

### Issue #1: Network Error on Checkout (PRIMARY)

```
NETWORK ERROR ANALYSIS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYMPTOM:
├─ Error occurs at final checkout confirmation
├─ "Complete transaction for CHF 135.46? Network Error"
├─ Transaction cannot complete
└─ Customer waiting

POSSIBLE CAUSES:
├─ [ ] API endpoint unreachable
├─ [ ] Database connection timeout
├─ [ ] Backend service down
├─ [ ] Network connectivity at Artemis
├─ [ ] Docker container issue
├─ [ ] SSL/TLS certificate problem
└─ [ ] Firewall blocking request

INVESTIGATION STEPS:
1. Check HelixNet container status: docker ps
2. Check container logs: docker logs helix-platform
3. Test API endpoint: curl http://localhost:8000/api/v1/pos/health
4. Check database connection
5. Review network configuration
6. Check Artemis local network/WiFi

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Issue #2: VAT Rate Incorrect (SECONDARY)

```
VAT RATE DISCREPANCY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DISPLAYED:      7.7% (2024 rate)
EXPECTED:       8.1% (2025 rate)
DIFFERENCE:     0.4%

CALCULATION ERROR:
├─ Subtotal after discount: CHF 125.77
├─ VAT @ 7.7%: CHF 9.68 (displayed)
├─ VAT @ 8.1%: CHF 10.19 (correct)
└─ Undercollected: CHF 0.51 per transaction

CAUSE:
├─ Config not reloaded after update?
├─ Browser cache showing old values?
├─ POSConfig.load() not called?
└─ Environment variable not propagated?

FILES TO CHECK:
├─ /home/angel/repos/helixnet/env/helix.env
├─ /home/angel/repos/helixnet/src/core/config.py
├─ /home/angel/repos/helixnet/src/routes/pos_router.py
└─ /home/angel/repos/helixnet/src/templates/pos/checkout.html

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Immediate Workaround

### For Pam (Until Fixed)

```
BACKUP PROCEDURE - PEN AND PAPER:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Use CARAN PEN (Swiss Made standard)
2. Record transaction manually:
   ├─ Date/Time
   ├─ Items sold
   ├─ Prices
   ├─ Discount applied
   ├─ Total collected
   └─ Payment method

3. Issue handwritten receipt if needed
4. Enter into POS later when fixed
5. Keep all paper records for reconciliation

"Always works unless completely empty,
 better than any pencil!" — Felix

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Communication Trail

```
INCIDENT COMMUNICATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TIME        FROM    TO      CHANNEL     STATUS
────────────────────────────────────────────────────────────────
~11:00      Pam     Felix   Phone       Missed (airplane mode)
~11:05      Pam     Felix   Phone       Missed (airplane mode)
~11:10      Pam     Felix   Phone       Missed (airplane mode)
~11:15      Pam     Felix   Telegram    "Please Call - POS issue"
                                        + Screenshot attached
~12:00      Felix   Ralph   Email       Forwarded for investigation
                                        (lunch handover)

ESCALATION PATH:
Pam → Felix → Ralph → [Claude/KB if stuck]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Ralph's Investigation Checklist

### Step 1: System Health Check
```bash
# Check Docker containers
docker ps

# Check helix-platform logs
docker logs helix-platform --tail 100

# Check API health
curl http://localhost:8000/api/v1/pos/health

# Check database connectivity
docker exec helix-platform python -c "from src.core.database import get_db; print('DB OK')"
```

### Step 2: VAT Configuration Check
```bash
# Check environment variable
grep POS_VAT /home/angel/repos/helixnet/env/helix.env

# Test config endpoint
curl http://localhost:8000/api/v1/pos/config

# Expected response:
# {
#   "vat_rate": 8.1,
#   "vat_year": 2025,
#   "currency": "CHF",
#   "locale": "de-CH",
#   "vat_decimal": 0.081
# }
```

### Step 3: Network Diagnostics
```bash
# Check if API is listening
netstat -tlnp | grep 8000

# Test from Artemis network (if remote)
ping artemis-pos.local
curl https://artemis-pos.local/api/v1/pos/health
```

### Step 4: Restart if Needed
```bash
# Restart containers
make down && make up

# Or just the platform
docker restart helix-platform
```

---

## Resolution Status

| Issue | Status | Assigned | ETA |
|-------|--------|----------|-----|
| Network Error | OPEN | Ralph | TBD |
| VAT Rate 7.7% | OPEN | Ralph | TBD |

---

## Felix's Notes

> "No worries, no stress. We still have the old PEN AND PAPER.
> Ralph will take care of it when he takes over at lunch.
> The HelixNet has the ultimate BLQ health check -
> that system cannot fail if wired properly."
>
> — Felix (from Raber Leder, Küssnacht)

---

## Related KBs

- BLQ_KB-016: Labeling Compliance & QR (HelixNet API discussion)
- HelixPOS Configuration: VAT rate settings
- Artemis SOP: Backup procedures

---

## Updates

| Date | Time | Update | By |
|------|------|--------|-----|
| 2025-11-30 | ~12:00 | Incident reported, forwarded to Ralph | Felix |
| | | | |

