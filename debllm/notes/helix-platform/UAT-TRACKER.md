# HelixNET UAT Tracker

**Version:** v2.6.0
**Demo Date:** Dec 6, 2024
**Last Nuke:** 2025-12-01 13:56 (Cycle #1 - Safe Nuke)

---

## Test Status Legend

- `[ ]` Not tested
- `[~]` Partial / Issues found
- `[x]` Passed
- `[!]` Blocked / Needs fix

---

## NUKE CYCLES

| Cycle | Date | Duration | Result | Notes |
|-------|------|----------|--------|-------|
| #1 | 2025-12-01 13:56 | ~2 min | PASS | Safe nuke, DB preserved, 20/20 containers, 7/7 endpoints |
| #2 | 2025-12-01 14:15 | ~2 min | PASS | Fix persisted, 20/20 containers, 7/7 endpoints, 4 customers OK |
| #3 | 2025-12-01 14:23 | ~2 min | PASS | E2E test suite: 23/23 tests passed |
| #4 | 2025-12-01 14:39 | ~10 min | PASS | **FULL NUKE** - rebuilt from zero, 23/23 E2E passed |

---

## AUTH / KEYCLOAK

| Test | Claude | Human | Status | Notes |
|------|--------|-------|--------|-------|
| Realm imports (artemis) | Required | Verify | [x] | Confirmed in health check |
| Realm imports (blowup) | Required | Verify | [x] | Confirmed in health check |
| Realm imports (420) | Required | Verify | [x] | fourtwenty realm active |
| Pam login (cashier) | Required | Test | [x] | Keycloak direct: OK, API auth: OK (BUG-001 fixed) |
| Felix login (admin) | Required | Test | [x] | Keycloak direct: OK |
| Ralph login (manager) | Required | Test | [x] | Keycloak direct: OK |
| Michael login (auditor) | Required | Test | [~] | Not in realm file |
| Leandra login | Required | Test | [x] | Keycloak direct: OK |
| Token refresh | Required | Test | [ ] | |
| Logout | Required | Test | [ ] | |
| Wrong password | Required | Test | [ ] | |

---

## POS / PRODUCTS

| Test | Claude | Human | Status | Notes |
|------|--------|-------|--------|-------|
| Product search loads | Required | Test | [x] | 7,447 products, endpoint 200 |
| Search by name | Required | Test | [ ] | |
| Search by barcode | Required | Test | [ ] | |
| Category filter | Required | Test | [ ] | |
| Product image displays | Required | Verify | [ ] | |
| Add to cart | Required | Test | [ ] | |
| Remove from cart | Required | Test | [ ] | |
| Quantity adjust | Required | Test | [ ] | |

---

## CHECKOUT

| Test | Claude | Human | Status | Notes |
|------|--------|-------|--------|-------|
| Cart totals correct | Required | Verify | [ ] | |
| VAT calculation (8.1%) | Required | Verify | [ ] | |
| Cash payment | Required | Test | [ ] | |
| Card payment | Required | Test | [ ] | |
| TWINT payment | Required | Test | [ ] | |
| Quick Round (10/20/50/100) | Required | Test | [ ] | |
| Pink Punch (product as change) | Required | Test | [ ] | |
| Change calculation | Required | Verify | [ ] | |
| Complete transaction | Required | Test | [ ] | |
| Receipt displays | Required | Verify | [ ] | |

---

## CASH COUNT

| Test | Claude | Human | Status | Notes |
|------|--------|-------|--------|-------|
| Page loads | Required | Verify | [ ] | |
| Denomination entry | Required | Test | [ ] | |
| Total calculates | Required | Verify | [ ] | |
| Variance shows | Required | Verify | [ ] | |
| Submit count | Required | Test | [ ] | |

---

## CUSTOMER / CRACK

| Test | Claude | Human | Status | Notes |
|------|--------|-------|--------|-------|
| Customer search | Required | Test | [x] | 4 customers returned (ChuckB, GreenQueen, Poppie, SmokeKing) |
| Search by handle | Required | Test | [x] | Works - search 'Chuck' returns ChuckB |
| Search by @instagram | Required | Test | [x] | Works - search '@' returns all with instagram |
| Create new customer | Required | Test | [ ] | Ready to test |
| Welcome credits awarded | Required | Verify | [ ] | Ready to verify |
| Profile displays | Required | Verify | [x] | tier, credits, visit_count, crack_level shown |
| Tier discount shows | Required | Verify | [x] | bronze=5%, silver=10%, gold=15%, platinum=20% |
| Apply to checkout | Required | Test | [ ] | Ready to test |

---

## KB APPROVALS

| Test | Claude | Human | Status | Notes |
|------|--------|-------|--------|-------|
| Pending KBs list | Required | Verify | [ ] | |
| Quality badges show | Required | Verify | [ ] | |
| Approve single KB | Required | Test | [ ] | |
| Batch approve | Required | Test | [ ] | |
| Credits awarded | Required | Verify | [ ] | |
| Reject with reason | Required | Test | [ ] | |
| Send for review | Required | Test | [ ] | |

---

## NETWORK / TELL ME

| Test | Claude | Human | Status | Notes |
|------|--------|-------|--------|-------|
| RabbitMQ running | Required | Verify | [ ] | |
| Queue exists | Required | Verify | [ ] | |
| Publish message | Future | - | [ ] | |
| Consume message | Future | - | [ ] | |

---

## EDGE CASES

| Test | Claude | Human | Status | Notes |
|------|--------|-------|--------|-------|
| Empty cart checkout | Required | Test | [ ] | Should block |
| Negative quantity | Required | Test | [ ] | Should block |
| Session timeout | Required | Test | [ ] | Redirect to login |
| Network disconnect | Optional | Test | [ ] | Graceful error |
| Double submit | Optional | Test | [ ] | Should prevent |

---

## BUGS FOUND

| ID | Description | Found By | Status | Fix |
|----|-------------|----------|--------|-----|
| BUG-001 | Realm mismatch: App uses master, users in artemis | Claude UAT | FIXED | Updated env/helix.env + src/core/keycloak_auth.py |

---

## HUMAN NOTES

(Add your observations here during testing)

```
Date:
Tester:
Notes:


```

---

## E2E TEST SUITE

**Script:** `scripts/uat/e2e-test.sh`
**Usage:** `./e2e-test.sh [--json] [--quick]`

| Category | Tests | Status |
|----------|-------|--------|
| Container Health | 6 | All Pass |
| Environment Config | 1 | Pass |
| API Endpoints (Public) | 2 | All Pass |
| Keycloak Auth | 5 | All Pass |
| Authenticated API (CRACK) | 3 | All Pass |
| Database Integrity | 3 | All Pass |
| Keycloak Realms | 3 | All Pass |
| **TOTAL** | **23** | **23 PASS** |

---

## NEXT ACTIONS

1. [x] Run Nuke Cycle #1 - PASSED
2. [x] Fix BUG-001 (realm mismatch) - FIXED
3. [x] Complete Auth tests - DONE (Pam, Felix, Ralph, Leandra)
4. [x] Run Nuke Cycle #2 - PASSED (fix persists)
5. [x] Create E2E test suite - 23 automated tests
6. [x] Run Nuke Cycle #3 - PASSED (E2E validated)
7. [x] Run FULL NUKE #4 - PASSED (rebuilt from zero)
8. [ ] Complete POS happy path
9. [ ] Demo dry run

---

*"Be water, my friend"* - BLQ
