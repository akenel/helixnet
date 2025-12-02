# HelixNet HR Module — KISS Edition
## One Employee. Swiss Legal. CSV-Ready.
### Design Doc v0.1 | December 2025

---

## Philosophy

```
BLQ RULE: If it works for 1, it works for 50.
Start with 1 employee. Get it right. Scale later.
```

---

## The Use Case

**One Full-Time Employee:**
- 40 hours/week
- 40 weeks/year (+ holidays)
- CHF 25-35/hour (example)
- 50% health covered after 3-month probation
- 1 remote day option (80% rate)
- KB contributions = bonus pool

---

## Swiss Payroll Essentials

### What the Law Requires

| Deduction | Rate | Employer Pays | Employee Pays |
|-----------|------|---------------|---------------|
| AHV/IV/EO | 10.6% | 5.3% | 5.3% |
| ALV (unemployment) | 2.2% | 1.1% | 1.1% |
| ALV2 (>148k) | 1.0% | 0.5% | 0.5% |
| BVG/LPP (pension) | ~7-18% | 50% | 50% |
| UVG (accident) | ~0.5-3% | 100% (NBU optional) | 0% |
| KTG (sick daily) | ~1-2% | Usually 50% | Usually 50% |
| FAK (family comp) | ~1-3% | 100% | 0% |

### Simplified Model (Start Here)

For MVP, use flat percentages:

```python
SWISS_DEDUCTIONS = {
    "ahv_iv_eo": 0.053,      # Employee share
    "alv": 0.011,            # Employee share
    "bvg": 0.07,             # Employee share (age-dependent, simplified)
    "uvg_nbu": 0.0,          # Often employer pays 100%
    "ktg": 0.005,            # Employee share if split
}

EMPLOYER_CONTRIBUTIONS = {
    "ahv_iv_eo": 0.053,
    "alv": 0.011,
    "bvg": 0.07,
    "uvg_bu": 0.015,         # Employer pays
    "uvg_nbu": 0.01,         # If employer covers
    "fak": 0.02,             # Family compensation
}
```

---

## Data Model

### Employee Table

```python
class EmployeeModel(Base):
    __tablename__ = "employees"

    id: UUID
    user_id: UUID  # Link to UserModel (Keycloak)

    # Personal
    first_name: str
    last_name: str
    date_of_birth: date
    nationality: str
    ahv_number: str  # 756.XXXX.XXXX.XX

    # Contact
    email: str
    phone: str
    address: str
    postal_code: str
    city: str

    # Banking
    iban: str
    bank_name: str

    # Employment
    start_date: date
    end_date: Optional[date]
    probation_end: date  # start_date + 3 months
    contract_type: str  # "fulltime", "parttime", "hourly"
    hours_per_week: Decimal  # 40.0
    hourly_rate: Decimal  # CHF 30.00

    # Benefits
    health_insurance_contribution: Decimal  # 50% after probation
    remote_days_per_week: int  # 1
    remote_rate_multiplier: Decimal  # 0.8

    # Status
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

### TimeEntry Table

```python
class TimeEntryModel(Base):
    __tablename__ = "time_entries"

    id: UUID
    employee_id: UUID

    # The entry
    date: date
    hours: Decimal
    entry_type: str  # "regular", "remote", "holiday", "sick", "unpaid"

    # Approval workflow
    status: str  # "draft", "submitted", "approved", "rejected"
    submitted_at: Optional[datetime]
    approved_by: Optional[UUID]  # Manager user_id
    approved_at: Optional[datetime]

    # Notes
    description: Optional[str]
    kb_contribution_id: Optional[UUID]  # Link to KB if bonus-eligible

    created_at: datetime
    updated_at: datetime
```

### PayrollRun Table

```python
class PayrollRunModel(Base):
    __tablename__ = "payroll_runs"

    id: UUID

    # Period
    year: int
    month: int  # 1-12

    # Status
    status: str  # "draft", "calculating", "pending_approval", "approved", "paid", "closed"

    # Workflow
    created_by: UUID
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    paid_at: Optional[datetime]
    closed_at: Optional[datetime]

    # Output files (MinIO paths)
    csv_export_path: Optional[str]
    pdf_slips_path: Optional[str]

    created_at: datetime
    updated_at: datetime
```

### PaySlip Table

```python
class PaySlipModel(Base):
    __tablename__ = "payslips"

    id: UUID
    payroll_run_id: UUID
    employee_id: UUID

    # Period
    year: int
    month: int

    # Hours
    regular_hours: Decimal
    remote_hours: Decimal
    holiday_hours: Decimal
    sick_hours: Decimal
    total_hours: Decimal

    # Gross
    gross_salary: Decimal

    # Deductions (employee share)
    ahv_iv_eo: Decimal
    alv: Decimal
    bvg: Decimal
    uvg_nbu: Decimal
    ktg: Decimal
    other_deductions: Decimal
    total_deductions: Decimal

    # Net
    net_salary: Decimal

    # Employer costs (for reporting)
    employer_ahv: Decimal
    employer_alv: Decimal
    employer_bvg: Decimal
    employer_uvg: Decimal
    employer_fak: Decimal
    total_employer_cost: Decimal

    # Bonus
    kb_bonus: Decimal  # From approved KB contributions

    # Status
    email_sent: bool
    email_sent_at: Optional[datetime]

    created_at: datetime
```

---

## Workflow

### Monthly Cycle

```
Week 1-4:  Employees log time (draft entries)
           ↓
Day 25:    Deadline to submit time entries
           ↓
Day 26-28: Manager reviews & approves entries
           ↓
Day 28:    Admin creates PayrollRun (status: draft)
           ↓
Day 28:    System calculates all payslips
           ↓
Day 29:    Manager approves PayrollRun
           ↓
Day 30:    Admin marks as "paid" (manual bank transfer)
           ↓
Day 30:    System emails PDF payslips to employees
           ↓
Day 30:    CSV exported to MinIO (archive)
           ↓
Month+1:   PayrollRun closed
```

### Approval Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   DRAFT     │ ──► │  SUBMITTED  │ ──► │  APPROVED   │
│  (Employee) │     │  (Employee) │     │  (Manager)  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  REJECTED   │
                    │  (Manager)  │
                    └─────────────┘
```

---

## API Endpoints

### Time Entries

```
POST   /api/v1/hr/time-entries              # Create entry
GET    /api/v1/hr/time-entries              # List my entries
PUT    /api/v1/hr/time-entries/{id}         # Update entry
POST   /api/v1/hr/time-entries/{id}/submit  # Submit for approval
DELETE /api/v1/hr/time-entries/{id}         # Delete draft

# Manager only
GET    /api/v1/hr/time-entries/pending      # Entries awaiting approval
POST   /api/v1/hr/time-entries/{id}/approve # Approve
POST   /api/v1/hr/time-entries/{id}/reject  # Reject with reason
```

### Payroll

```
# Admin only
POST   /api/v1/hr/payroll/runs              # Create new run
GET    /api/v1/hr/payroll/runs              # List runs
GET    /api/v1/hr/payroll/runs/{id}         # Get run details
POST   /api/v1/hr/payroll/runs/{id}/calculate  # Calculate all slips
POST   /api/v1/hr/payroll/runs/{id}/approve    # Approve run
POST   /api/v1/hr/payroll/runs/{id}/paid       # Mark as paid
POST   /api/v1/hr/payroll/runs/{id}/close      # Close month
GET    /api/v1/hr/payroll/runs/{id}/csv        # Download CSV
GET    /api/v1/hr/payroll/runs/{id}/slips      # List payslips

# Employee
GET    /api/v1/hr/payslips                  # My payslips
GET    /api/v1/hr/payslips/{id}/pdf         # Download PDF
```

### Year-End (Lohnausweis)

```
# Admin only
POST   /api/v1/hr/lohnausweis/{year}        # Generate for year
GET    /api/v1/hr/lohnausweis/{year}/{employee_id}  # Get PDF
POST   /api/v1/hr/lohnausweis/{year}/send   # Email all to employees
```

---

## Calculation Engine

### Monthly Payslip Calculation

```python
def calculate_payslip(employee: Employee, entries: List[TimeEntry], month: int, year: int) -> PaySlip:
    """Calculate one employee's monthly payslip."""

    # Sum hours by type
    regular_hours = sum(e.hours for e in entries if e.entry_type == "regular")
    remote_hours = sum(e.hours for e in entries if e.entry_type == "remote")
    holiday_hours = sum(e.hours for e in entries if e.entry_type == "holiday")
    sick_hours = sum(e.hours for e in entries if e.entry_type == "sick")

    # Calculate gross
    regular_pay = regular_hours * employee.hourly_rate
    remote_pay = remote_hours * employee.hourly_rate * employee.remote_rate_multiplier
    holiday_pay = holiday_hours * employee.hourly_rate
    sick_pay = sick_hours * employee.hourly_rate  # Simplified, real has limits

    gross_salary = regular_pay + remote_pay + holiday_pay + sick_pay

    # Calculate deductions (employee share)
    ahv = gross_salary * Decimal("0.053")
    alv = gross_salary * Decimal("0.011")
    bvg = gross_salary * Decimal("0.07")  # Simplified

    total_deductions = ahv + alv + bvg

    # Net
    net_salary = gross_salary - total_deductions

    # KB Bonus (if any approved KB contributions this month)
    kb_bonus = calculate_kb_bonus(employee, month, year)

    net_salary += kb_bonus

    return PaySlip(
        gross_salary=gross_salary,
        ahv_iv_eo=ahv,
        alv=alv,
        bvg=bvg,
        total_deductions=total_deductions,
        kb_bonus=kb_bonus,
        net_salary=net_salary,
        # ... other fields
    )
```

---

## MinIO Storage Structure

```
helix-hr-bucket/
├── payroll/
│   ├── 2025/
│   │   ├── 01/
│   │   │   ├── payroll_run_2025_01.csv
│   │   │   ├── payslip_employee_uuid_2025_01.pdf
│   │   │   └── ...
│   │   ├── 02/
│   │   └── ...
│   └── lohnausweis/
│       ├── 2025/
│       │   ├── lohnausweis_employee_uuid_2025.pdf
│       │   └── ...
│       └── ...
└── time_entries/
    └── exports/
        └── time_entries_2025_01.csv
```

---

## CSV Export Format

### Monthly Payroll CSV

```csv
employee_id,name,ahv_number,month,year,regular_hours,remote_hours,holiday_hours,sick_hours,gross,ahv,alv,bvg,deductions,kb_bonus,net,iban
uuid1,"Max Muster",756.1234.5678.90,1,2025,160,8,0,0,5040.00,267.12,55.44,352.80,675.36,50.00,4414.64,CH93 0076 2011 6238 5295 7
```

### Lohnausweis Fields (Swiss Standard)

```
1.  Lohn (brutto)
2.  Gehaltsnebenleistungen
3.  Unregelmässige Leistungen
4.  Kapitalleistungen
5.  Beteiligungsrechte
6.  Verwaltungsratsentschädigungen
7.  Weitere Leistungen
8.  Bruttolohn Total
9.  AHV/IV/EO-Beiträge
10. ALV-Beiträge
11. NBU-Prämien
12. BVG ordentliche Beiträge
13. Nettolohn
```

---

## RBAC Roles

| Role | Can Do |
|------|--------|
| `hr-employee` | Log time, view own slips |
| `hr-manager` | Approve time entries |
| `hr-admin` | Run payroll, generate Lohnausweis |
| `hr-auditor` | View all, export CSV (read-only) |

Add to Keycloak realm:
```json
{
  "roles": ["hr-employee", "hr-manager", "hr-admin", "hr-auditor"]
}
```

---

## Implementation Estimate

### Phase 1: Core (2 weeks)

| Task | Days |
|------|------|
| Database models | 2 |
| Time entry CRUD | 2 |
| Approval workflow | 2 |
| Basic payslip calc | 2 |
| CSV export | 1 |
| MinIO integration | 1 |
| **Total** | **10 days** |

### Phase 2: Polish (1 week)

| Task | Days |
|------|------|
| PDF payslip generation | 2 |
| Email sending | 1 |
| Lohnausweis template | 2 |
| **Total** | **5 days** |

### Phase 3: Testing (1 week)

| Task | Days |
|------|------|
| Unit tests | 2 |
| Integration tests | 2 |
| UAT with 1 real employee | 1 |
| **Total** | **5 days** |

---

## Total Estimate

| Phase | Time | Cost (@CHF 150/hr) |
|-------|------|-------------------|
| Core | 2 weeks | CHF 12,000 |
| Polish | 1 week | CHF 6,000 |
| Testing | 1 week | CHF 6,000 |
| **TOTAL** | **4 weeks** | **CHF 24,000** |

---

## What You Get

After 4 weeks:

- ✅ Employees log time (web UI)
- ✅ Manager approves time entries
- ✅ Admin runs monthly payroll
- ✅ Automatic deduction calculations
- ✅ PDF payslips emailed to employees
- ✅ CSV exports to MinIO (auditable)
- ✅ Year-end Lohnausweis generation
- ✅ KB contribution → bonus tracking
- ✅ Remote day rate handling (80%)
- ✅ Probation period tracking (health insurance)

---

## What You DON'T Get (v1)

- ❌ Expense management
- ❌ Leave request workflow
- ❌ BVG age-based calculations (uses flat rate)
- ❌ Quellensteuer (withholding for foreigners)
- ❌ Multi-canton tax handling
- ❌ Direct bank payment integration
- ❌ Swissdec integration

*These are Phase 2 features.*

---

## Next Steps

1. **Confirm data model** — Does this match Felix's spreadsheet?
2. **Get sample Lohnausweis** — Use as PDF template
3. **Define KB bonus rules** — How much per approved KB?
4. **Set up MinIO bucket** — `helix-hr-bucket`
5. **Add Keycloak roles** — `hr-employee`, `hr-manager`, `hr-admin`

---

*KISS. One employee. Get it right. Scale later.*

*"If it works for 1, it works for 50."*

