# BLQ HR Module - Swiss Payroll & Time Tracking

> "Be water, my friend" - Bruce Lee
> "First Time Right" - Six Sigma
> "KICKIS: Keep It Clean, Keep It Simple" - BLQ Philosophy

## What Just Happened? (For Pam)

Hey Pam! We just built you a complete HR & payroll system. Here's what you can do now:

### Your New Superpowers

1. **Track Your Hours** - Enter your daily work hours (regular, remote, overtime, holidays)
2. **Submit for Approval** - Send your timesheet to Felix/Mosey for sign-off
3. **View Your Payslips** - See your monthly payslips with full Swiss breakdown
4. **Check Your Stats** - See monthly totals, balance, and status

### How It Works (Bruce Lee Simple)

```
You enter hours → Submit → Manager approves → Payroll runs → You get paid
     (draft)     (submitted)   (approved)     (calculated)    (paid)
```

---

## Quick Start Guide

### 1. Enter Your Time (Daily)

**Endpoint:** `POST /api/v1/hr/time-entries`

```json
{
  "entry_date": "2025-12-02",
  "entry_type": "regular",
  "hours": 8.5,
  "start_time": "08:00",
  "end_time": "17:30",
  "break_minutes": 60,
  "description": "Store shift + vending restock"
}
```

**Entry Types:**
| Type | Rate | When to Use |
|------|------|-------------|
| `regular` | 100% | Normal store/office work |
| `remote` | 80% | Working from home |
| `overtime` | 125% | Extra hours (approved) |
| `holiday` | 100% | Paid vacation (Ferien) |
| `sick` | 100% | Sick leave (Krankheit) |
| `public_holiday` | 100% | Feiertag (1. August, etc.) |
| `training` | 100% | KB contributions, courses |
| `unpaid` | 0% | Unpaid leave |

### 2. View Your Week

**Endpoint:** `GET /api/v1/hr/timesheet/week`

Shows your weekly entries with totals and balance against your contract hours.

### 3. Submit for Approval

**Endpoint:** `POST /api/v1/hr/time-entries/submit`

```json
{
  "entry_ids": ["uuid-1", "uuid-2", "uuid-3"]
}
```

Once submitted, you can't edit until:
- Manager approves (moves to `approved`)
- Manager rejects (moves back to `draft` with feedback)

### 4. View Your Payslips

**Endpoint:** `GET /api/v1/hr/payslips/my`

See all your payslips with:
- Hours breakdown
- Gross salary
- All deductions (AHV, ALV, BVG, etc.)
- Net salary
- PDF download link (when available)

---

## For Felix/Mosey (Managers)

### Approve Time Entries

1. **View Pending:** `GET /api/v1/hr/time-entries/pending`
2. **Approve/Reject:** `POST /api/v1/hr/time-entries/approve`

```json
{
  "entry_ids": ["uuid-1", "uuid-2"],
  "action": "approve"
}
```

Or reject with reason:
```json
{
  "entry_ids": ["uuid-3"],
  "action": "reject",
  "rejection_reason": "Missing project description"
}
```

### Run Monthly Payroll

```bash
# 1. Create payroll run
POST /api/v1/hr/payroll/run?year=2025&month=12

# 2. Calculate all payslips (processes approved time entries)
POST /api/v1/hr/payroll/{run_id}/calculate

# 3. Review the summary
GET /api/v1/hr/payroll/{run_id}

# 4. Approve (after review)
POST /api/v1/hr/payroll/{run_id}/approve

# 5. Mark as paid (after bank transfer)
POST /api/v1/hr/payroll/{run_id}/mark-paid
```

---

## Swiss Payroll Breakdown

### Employee Deductions
| Deduction | Rate | Notes |
|-----------|------|-------|
| AHV/IV/EO | 5.3% | Old age, disability, income replacement |
| ALV | 1.1% | Unemployment (up to CHF 148,200/year) |
| ALV2 | 0.5% | Solidarity (above CHF 148,200) |
| BVG | ~3.5% | Pension (employee half, age-dependent) |
| NBU | ~1.24% | Non-occupational accident (if applicable) |
| Quellensteuer | varies | Withholding tax (foreigners only) |

### Employer Contributions (Not on your payslip)
| Contribution | Rate |
|--------------|------|
| AHV/IV/EO | 5.3% |
| ALV | 1.1% |
| BVG | ~3.5% |
| UVG | ~1.5% |
| FAK | 1.2% |
| Admin | 0.2% |

**Total employer cost:** ~13-15% on top of your gross salary

---

## WoW Score System (First Time Right)

Inspired by Six Sigma's "First Time Right" metric:

| Score | Meaning | What Happens |
|-------|---------|--------------|
| 5/5 | Perfect week - all entries approved first time | +25 bonus credits |
| 4/5 | Minor corrections needed | +10 bonus credits |
| 3/5 | Some rejections | No bonus |
| 2/5 | Multiple issues | Coaching chat |
| 1/5 | Needs training | Training session |

**How to get 5/5:**
1. Enter hours daily (not weekly batch)
2. Add descriptions for non-standard entries
3. Use correct entry types
4. Submit by Friday EOD

---

## API Endpoints Summary

### Employee Self-Service
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/hr/me` | My HR profile |
| GET | `/api/v1/hr/time-entries/my` | My time entries |
| POST | `/api/v1/hr/time-entries` | Create entry |
| PUT | `/api/v1/hr/time-entries/{id}` | Update draft |
| DELETE | `/api/v1/hr/time-entries/{id}` | Delete draft |
| POST | `/api/v1/hr/time-entries/submit` | Submit for approval |
| GET | `/api/v1/hr/timesheet/week` | Weekly view |
| GET | `/api/v1/hr/stats/my-month` | Monthly stats |
| GET | `/api/v1/hr/payslips/my` | My payslips |
| GET | `/api/v1/hr/payslips/{id}` | Payslip detail |

### Manager/Admin Only
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/hr/time-entries/pending` | Pending approvals |
| POST | `/api/v1/hr/time-entries/approve` | Approve/reject |
| GET | `/api/v1/hr/payroll` | List payroll runs |
| POST | `/api/v1/hr/payroll/run` | Create payroll run |
| POST | `/api/v1/hr/payroll/{id}/calculate` | Calculate payslips |
| GET | `/api/v1/hr/payroll/{id}` | Payroll summary |
| POST | `/api/v1/hr/payroll/{id}/approve` | Approve payroll |
| POST | `/api/v1/hr/payroll/{id}/mark-paid` | Mark as paid |

---

## Testing Guide

### As Pam (pos-cashier role):

```bash
# 1. Login to get token
TOKEN=$(curl -s -X POST "https://keycloak.helix.local/realms/artemis/protocol/openid-connect/token" \
  -d "client_id=artemis_pos" \
  -d "username=pam" \
  -d "password=helix_pass" \
  -d "grant_type=password" | jq -r '.access_token')

# 2. Check your HR profile
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:9003/api/v1/hr/me

# 3. Create a time entry
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entry_date":"2025-12-02","entry_type":"regular","hours":8.5,"description":"Store shift"}' \
  http://localhost:9003/api/v1/hr/time-entries

# 4. View your entries
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:9003/api/v1/hr/time-entries/my
```

### As Felix (pos-manager role):

```bash
# Login as Felix
TOKEN=$(curl -s -X POST "https://keycloak.helix.local/realms/artemis/protocol/openid-connect/token" \
  -d "client_id=artemis_pos" \
  -d "username=felix" \
  -d "password=helix_pass" \
  -d "grant_type=password" | jq -r '.access_token')

# View pending approvals
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:9003/api/v1/hr/time-entries/pending

# Run December payroll
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "http://localhost:9003/api/v1/hr/payroll/run?year=2025&month=12"
```

---

## Chuck Norris Mode

When Chuck Norris (CN) drops into Artemis for spot buys:
- No TWINT needed - carries cash EUs only
- Gets CRACK loyalty credits anyway
- His time entries approve themselves

---

## Files Added

```
src/db/models/employee_model.py      # Employee data model
src/db/models/time_entry_model.py    # Time entry tracking
src/db/models/payroll_run_model.py   # Monthly payroll runs
src/db/models/payslip_model.py       # Individual payslips
src/schemas/hr_schema.py             # Pydantic schemas
src/routes/hr_router.py              # API endpoints
src/services/payroll_service.py      # Swiss calculation engine
migrations/versions/002_add_hr_module.py  # Database migration
```

---

## Version

**v3.1.0** - BLQ HR Module
Built with Bruce Lee precision for the Artemis team.

*"Empty your mind, be formless, shapeless - like water."*
