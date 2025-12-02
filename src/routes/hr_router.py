# File: src/routes/hr_router.py
"""
HR & Payroll API Router - BLQ Module

"Be water, my friend" - Bruce Lee
"KICKIS: Keep It Clean, Keep It Simple" - BLQ Philosophy

Endpoints for:
- Time entry CRUD
- Approval workflow
- Employee management (basic)
"""
import logging
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from uuid import UUID
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from src.db.database import get_db_session
from src.db.models import (
    EmployeeModel,
    TimeEntryModel,
    EntryType,
    EntryStatus,
    UserModel,
)
from src.schemas.hr_schema import (
    TimeEntryCreate,
    TimeEntryUpdate,
    TimeEntryRead,
    TimeEntrySubmit,
    TimeEntryApproval,
    EmployeeTimesheet,
)
from src.core.keycloak_auth import require_any_pos_role, require_manager_or_admin, verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/hr", tags=["HR - Time & Payroll"])


# ================================================================
# HELPER: Get employee from token
# ================================================================

async def get_employee_from_token(
    db: AsyncSession,
    token_payload: dict
) -> Optional[EmployeeModel]:
    """
    Find employee record linked to the authenticated user.
    Uses Keycloak 'sub' (user UUID) to match employee.user_id.
    """
    user_id = token_payload.get("sub")
    if not user_id:
        return None

    result = await db.execute(
        select(EmployeeModel).where(EmployeeModel.user_id == UUID(user_id))
    )
    return result.scalar_one_or_none()


# ================================================================
# TIME ENTRIES - My Entries (Employee View)
# ================================================================

@router.get("/time-entries/my")
async def get_my_time_entries(
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Get my time entries (for logged-in employee).
    Default: last 30 days.
    """
    employee = await get_employee_from_token(db, current_user)
    if not employee:
        raise HTTPException(
            status_code=404,
            detail="No employee record found for your user account"
        )

    # Default date range: last 30 days
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # Build query
    query = (
        select(TimeEntryModel)
        .where(TimeEntryModel.employee_id == employee.id)
        .where(TimeEntryModel.entry_date >= start_date)
        .where(TimeEntryModel.entry_date <= end_date)
    )

    if status_filter:
        try:
            status_enum = EntryStatus(status_filter)
            query = query.where(TimeEntryModel.status == status_enum)
        except ValueError:
            pass  # Ignore invalid status

    query = query.order_by(TimeEntryModel.entry_date.desc()).limit(limit)

    result = await db.execute(query)
    entries = result.scalars().all()

    return {
        "employee_id": str(employee.id),
        "employee_name": f"{employee.first_name} {employee.last_name}",
        "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "entries": [
            {
                "id": str(e.id),
                "entry_date": e.entry_date.isoformat(),
                "entry_type": e.entry_type.value,
                "hours": float(e.hours),
                "start_time": e.start_time,
                "end_time": e.end_time,
                "break_minutes": e.break_minutes,
                "status": e.status.value,
                "description": e.description,
                "submitted_at": e.submitted_at.isoformat() if e.submitted_at else None,
                "approved_at": e.approved_at.isoformat() if e.approved_at else None,
                "rejection_reason": e.rejection_reason,
            }
            for e in entries
        ],
        "total_entries": len(entries),
    }


@router.post("/time-entries", status_code=status.HTTP_201_CREATED)
async def create_time_entry(
    entry: TimeEntryCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Create a new time entry for myself.
    Entry starts in 'draft' status.
    """
    employee = await get_employee_from_token(db, current_user)
    if not employee:
        raise HTTPException(
            status_code=404,
            detail="No employee record found for your user account"
        )

    # Check for duplicate entry on same date with same type
    existing = await db.execute(
        select(TimeEntryModel).where(
            and_(
                TimeEntryModel.employee_id == employee.id,
                TimeEntryModel.entry_date == entry.entry_date,
                TimeEntryModel.entry_type == entry.entry_type
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Entry already exists for {entry.entry_date} with type {entry.entry_type.value}"
        )

    # Create entry
    new_entry = TimeEntryModel(
        employee_id=employee.id,
        entry_date=entry.entry_date,
        entry_type=entry.entry_type,
        hours=entry.hours,
        start_time=entry.start_time,
        end_time=entry.end_time,
        break_minutes=entry.break_minutes,
        description=entry.description,
        status=EntryStatus.DRAFT,
        kb_contribution_id=entry.kb_contribution_id,
    )

    db.add(new_entry)
    await db.commit()
    await db.refresh(new_entry)

    logger.info(f"Time entry created: {employee.first_name} {entry.entry_date} {entry.hours}h")

    return {
        "id": str(new_entry.id),
        "entry_date": new_entry.entry_date.isoformat(),
        "entry_type": new_entry.entry_type.value,
        "hours": float(new_entry.hours),
        "status": new_entry.status.value,
        "message": f"Entry created for {entry.entry_date}",
    }


@router.put("/time-entries/{entry_id}")
async def update_time_entry(
    entry_id: UUID,
    update: TimeEntryUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Update a draft time entry.
    Only draft entries can be modified.
    """
    employee = await get_employee_from_token(db, current_user)
    if not employee:
        raise HTTPException(status_code=404, detail="No employee record found")

    # Get entry
    result = await db.execute(
        select(TimeEntryModel).where(TimeEntryModel.id == entry_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    # Verify ownership
    if entry.employee_id != employee.id:
        raise HTTPException(status_code=403, detail="Cannot edit another employee's entry")

    # Only draft entries can be edited
    if entry.status != EntryStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot edit entry with status '{entry.status.value}'. Only draft entries can be modified."
        )

    # Apply updates
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)

    entry.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "id": str(entry.id),
        "entry_date": entry.entry_date.isoformat(),
        "status": entry.status.value,
        "message": "Entry updated successfully",
    }


@router.delete("/time-entries/{entry_id}")
async def delete_time_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Delete a draft time entry.
    Only draft entries can be deleted.
    """
    employee = await get_employee_from_token(db, current_user)
    if not employee:
        raise HTTPException(status_code=404, detail="No employee record found")

    result = await db.execute(
        select(TimeEntryModel).where(TimeEntryModel.id == entry_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    if entry.employee_id != employee.id:
        raise HTTPException(status_code=403, detail="Cannot delete another employee's entry")

    if entry.status != EntryStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete entry with status '{entry.status.value}'"
        )

    await db.delete(entry)
    await db.commit()

    return {"message": f"Entry for {entry.entry_date} deleted"}


@router.post("/time-entries/submit")
async def submit_time_entries(
    submission: TimeEntrySubmit,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Submit draft entries for manager approval.
    Changes status from 'draft' to 'submitted'.
    """
    employee = await get_employee_from_token(db, current_user)
    if not employee:
        raise HTTPException(status_code=404, detail="No employee record found")

    submitted_count = 0
    errors = []

    for entry_id in submission.entry_ids:
        result = await db.execute(
            select(TimeEntryModel).where(TimeEntryModel.id == entry_id)
        )
        entry = result.scalar_one_or_none()

        if not entry:
            errors.append(f"{entry_id}: not found")
            continue

        if entry.employee_id != employee.id:
            errors.append(f"{entry_id}: not your entry")
            continue

        if entry.status != EntryStatus.DRAFT:
            errors.append(f"{entry_id}: not in draft status")
            continue

        entry.status = EntryStatus.SUBMITTED
        entry.submitted_at = datetime.now(timezone.utc)
        submitted_count += 1

    await db.commit()

    logger.info(f"Submitted {submitted_count} entries for {employee.first_name}")

    return {
        "submitted": submitted_count,
        "errors": errors if errors else None,
        "message": f"{submitted_count} entries submitted for approval",
    }


# ================================================================
# TIME ENTRIES - Manager Approval View
# ================================================================

@router.get("/time-entries/pending")
async def get_pending_approvals(
    employee_id: Optional[UUID] = Query(None, description="Filter by employee"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """
    Get all submitted time entries waiting for approval.
    Manager/Admin only.
    """
    query = (
        select(TimeEntryModel, EmployeeModel)
        .join(EmployeeModel, TimeEntryModel.employee_id == EmployeeModel.id)
        .where(TimeEntryModel.status == EntryStatus.SUBMITTED)
    )

    if employee_id:
        query = query.where(TimeEntryModel.employee_id == employee_id)

    query = query.order_by(TimeEntryModel.entry_date.desc()).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    return {
        "pending_count": len(rows),
        "entries": [
            {
                "id": str(entry.id),
                "employee_id": str(entry.employee_id),
                "employee_name": f"{emp.first_name} {emp.last_name}",
                "employee_number": emp.employee_number,
                "entry_date": entry.entry_date.isoformat(),
                "entry_type": entry.entry_type.value,
                "hours": float(entry.hours),
                "start_time": entry.start_time,
                "end_time": entry.end_time,
                "description": entry.description,
                "submitted_at": entry.submitted_at.isoformat() if entry.submitted_at else None,
            }
            for entry, emp in rows
        ],
    }


@router.post("/time-entries/approve")
async def approve_time_entries(
    approval: TimeEntryApproval,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """
    Approve or reject submitted time entries.
    Manager/Admin only.
    """
    approver_id = UUID(current_user.get("sub"))
    approved_count = 0
    rejected_count = 0
    errors = []

    for entry_id in approval.entry_ids:
        result = await db.execute(
            select(TimeEntryModel).where(TimeEntryModel.id == entry_id)
        )
        entry = result.scalar_one_or_none()

        if not entry:
            errors.append(f"{entry_id}: not found")
            continue

        if entry.status != EntryStatus.SUBMITTED:
            errors.append(f"{entry_id}: not in submitted status")
            continue

        if approval.action == "approve":
            entry.status = EntryStatus.APPROVED
            entry.approved_by_id = approver_id
            entry.approved_at = datetime.now(timezone.utc)
            entry.rejection_reason = None
            approved_count += 1
        else:  # reject
            entry.status = EntryStatus.REJECTED
            entry.rejection_reason = approval.rejection_reason
            rejected_count += 1

    await db.commit()

    logger.info(f"Manager {current_user.get('username')}: approved={approved_count}, rejected={rejected_count}")

    return {
        "approved": approved_count,
        "rejected": rejected_count,
        "errors": errors if errors else None,
        "message": f"Processed {approved_count + rejected_count} entries",
    }


# ================================================================
# TIMESHEET SUMMARY
# ================================================================

@router.get("/timesheet/week")
async def get_weekly_timesheet(
    week_start: Optional[date] = Query(None, description="Monday of the week (defaults to current week)"),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Get weekly timesheet summary for the logged-in employee.
    Shows entries for the week with totals.
    """
    employee = await get_employee_from_token(db, current_user)
    if not employee:
        raise HTTPException(status_code=404, detail="No employee record found")

    # Calculate week boundaries
    if not week_start:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)  # Sunday

    # Get entries for the week
    result = await db.execute(
        select(TimeEntryModel)
        .where(TimeEntryModel.employee_id == employee.id)
        .where(TimeEntryModel.entry_date >= week_start)
        .where(TimeEntryModel.entry_date <= week_end)
        .order_by(TimeEntryModel.entry_date)
    )
    entries = result.scalars().all()

    # Calculate totals
    total_hours = sum(e.hours for e in entries if e.status != EntryStatus.REJECTED)
    pending_count = sum(1 for e in entries if e.status == EntryStatus.SUBMITTED)
    draft_count = sum(1 for e in entries if e.status == EntryStatus.DRAFT)

    # Target hours for the week (based on contract)
    target_hours = employee.hours_per_week

    return {
        "employee_id": str(employee.id),
        "employee_name": f"{employee.first_name} {employee.last_name}",
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "entries": [
            {
                "id": str(e.id),
                "day": e.entry_date.strftime("%A"),
                "entry_date": e.entry_date.isoformat(),
                "entry_type": e.entry_type.value,
                "hours": float(e.hours),
                "status": e.status.value,
                "description": e.description,
            }
            for e in entries
        ],
        "summary": {
            "total_hours": float(total_hours),
            "target_hours": float(target_hours),
            "balance": float(total_hours - target_hours),
            "entries_count": len(entries),
            "pending_approval": pending_count,
            "draft": draft_count,
        },
    }


# ================================================================
# EMPLOYEE - Basic Info
# ================================================================

@router.get("/me")
async def get_my_hr_profile(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Get my HR profile (employee record).
    """
    employee = await get_employee_from_token(db, current_user)
    if not employee:
        raise HTTPException(
            status_code=404,
            detail="No employee record linked to your account. Contact HR."
        )

    return {
        "id": str(employee.id),
        "employee_number": employee.employee_number,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "email": employee.email,
        "status": employee.status.value,
        "contract_type": employee.contract_type.value,
        "hours_per_week": float(employee.hours_per_week),
        "hourly_rate": float(employee.hourly_rate),
        "start_date": employee.start_date.isoformat(),
        "remote_days_per_week": employee.remote_days_per_week,
        "health_insurance_active": employee.health_insurance_active,
        "bvg_insured": employee.bvg_insured,
    }


# ================================================================
# STATS - Dashboard
# ================================================================

@router.get("/stats/my-month")
async def get_my_month_stats(
    year: int = Query(None, description="Year (defaults to current)"),
    month: int = Query(None, description="Month 1-12 (defaults to current)"),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Get my monthly time entry statistics.
    """
    employee = await get_employee_from_token(db, current_user)
    if not employee:
        raise HTTPException(status_code=404, detail="No employee record found")

    # Default to current month
    today = date.today()
    year = year or today.year
    month = month or today.month

    # Month boundaries
    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)

    # Get all entries for the month
    result = await db.execute(
        select(TimeEntryModel)
        .where(TimeEntryModel.employee_id == employee.id)
        .where(TimeEntryModel.entry_date >= month_start)
        .where(TimeEntryModel.entry_date <= month_end)
    )
    entries = result.scalars().all()

    # Calculate by status
    by_status = {s.value: [] for s in EntryStatus}
    for e in entries:
        by_status[e.status.value].append(e)

    # Calculate by type
    by_type = {}
    for e in entries:
        if e.status != EntryStatus.REJECTED:
            t = e.entry_type.value
            by_type[t] = by_type.get(t, Decimal("0")) + e.hours

    total_hours = sum(e.hours for e in entries if e.status not in [EntryStatus.REJECTED, EntryStatus.DRAFT])
    target_hours = employee.hours_per_week * Decimal("4.33")  # Standard Swiss month

    return {
        "employee_name": f"{employee.first_name} {employee.last_name}",
        "period": f"{year}-{month:02d}",
        "month_start": month_start.isoformat(),
        "month_end": month_end.isoformat(),
        "summary": {
            "total_hours": float(total_hours),
            "target_hours": float(target_hours),
            "balance": float(total_hours - target_hours),
            "entries_count": len(entries),
        },
        "by_status": {
            "draft": len(by_status["draft"]),
            "submitted": len(by_status["submitted"]),
            "approved": len(by_status["approved"]),
            "rejected": len(by_status["rejected"]),
            "paid": len(by_status["paid"]),
        },
        "by_type": {k: float(v) for k, v in by_type.items()},
    }


# ================================================================
# PAYROLL - Manager/Admin Only
# ================================================================

@router.post("/payroll/run")
async def create_payroll_run(
    year: int = Query(..., ge=2024, le=2100, description="Payroll year"),
    month: int = Query(..., ge=1, le=12, description="Payroll month"),
    notes: Optional[str] = Query(None, max_length=1000),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """
    Create a new payroll run for a specific month.
    Manager/Admin only.
    """
    from src.services.payroll_service import PayrollCalculator

    try:
        calculator = PayrollCalculator(db)
        creator_id = UUID(current_user.get("sub"))
        payroll_run = await calculator.create_payroll_run(year, month, creator_id, notes)

        return {
            "id": str(payroll_run.id),
            "period": payroll_run.period_name,
            "status": payroll_run.status.value,
            "message": f"Payroll run created for {payroll_run.period_name}",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payroll/{payroll_run_id}/calculate")
async def calculate_payroll(
    payroll_run_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """
    Calculate all payslips for a payroll run.
    Processes approved time entries into payslips.
    Manager/Admin only.
    """
    from src.services.payroll_service import PayrollCalculator

    try:
        calculator = PayrollCalculator(db)
        result = await calculator.calculate_all_payslips(payroll_run_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payroll/{payroll_run_id}/approve")
async def approve_payroll(
    payroll_run_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """
    Approve a calculated payroll run.
    Manager/Admin only.
    """
    from src.services.payroll_service import PayrollCalculator

    try:
        calculator = PayrollCalculator(db)
        approver_id = UUID(current_user.get("sub"))
        payroll_run = await calculator.approve_payroll_run(payroll_run_id, approver_id)

        return {
            "id": str(payroll_run.id),
            "period": payroll_run.period_name,
            "status": payroll_run.status.value,
            "approved_at": payroll_run.approved_at.isoformat(),
            "message": f"Payroll {payroll_run.period_name} approved",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payroll/{payroll_run_id}/mark-paid")
async def mark_payroll_paid(
    payroll_run_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """
    Mark payroll as paid (after bank transfer).
    Manager/Admin only.
    """
    from src.services.payroll_service import PayrollCalculator

    try:
        calculator = PayrollCalculator(db)
        payroll_run = await calculator.mark_payroll_paid(payroll_run_id)

        return {
            "id": str(payroll_run.id),
            "period": payroll_run.period_name,
            "status": payroll_run.status.value,
            "paid_at": payroll_run.paid_at.isoformat(),
            "message": f"Payroll {payroll_run.period_name} marked as paid",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payroll/{payroll_run_id}")
async def get_payroll_summary(
    payroll_run_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """
    Get detailed summary of a payroll run with all payslips.
    Manager/Admin only.
    """
    from src.services.payroll_service import PayrollCalculator

    try:
        calculator = PayrollCalculator(db)
        result = await calculator.get_payroll_summary(payroll_run_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payroll")
async def list_payroll_runs(
    year: Optional[int] = Query(None, description="Filter by year"),
    limit: int = Query(12, ge=1, le=50),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """
    List payroll runs.
    Manager/Admin only.
    """
    from src.db.models import PayrollRunModel

    query = select(PayrollRunModel)

    if year:
        query = query.where(PayrollRunModel.year == year)

    query = query.order_by(
        PayrollRunModel.year.desc(),
        PayrollRunModel.month.desc()
    ).limit(limit)

    result = await db.execute(query)
    runs = result.scalars().all()

    return {
        "count": len(runs),
        "payroll_runs": [
            {
                "id": str(r.id),
                "year": r.year,
                "month": r.month,
                "period": r.period_name,
                "status": r.status.value,
                "total_employees": r.total_employees,
                "total_gross": r.total_gross,
                "total_net": r.total_net,
                "created_at": r.created_at.isoformat(),
            }
            for r in runs
        ],
    }


# ================================================================
# PAYSLIPS - Individual Employee Payslips
# ================================================================

@router.get("/payslips/my")
async def get_my_payslips(
    year: Optional[int] = Query(None, description="Filter by year"),
    limit: int = Query(12, ge=1, le=24),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Get my payslips.
    Returns payslips for the logged-in employee.
    """
    from src.db.models import PaySlipModel

    employee = await get_employee_from_token(db, current_user)
    if not employee:
        raise HTTPException(status_code=404, detail="No employee record found")

    query = (
        select(PaySlipModel)
        .where(PaySlipModel.employee_id == employee.id)
    )

    if year:
        query = query.where(PaySlipModel.year == year)

    query = query.order_by(
        PaySlipModel.year.desc(),
        PaySlipModel.month.desc()
    ).limit(limit)

    result = await db.execute(query)
    payslips = result.scalars().all()

    return {
        "employee_name": f"{employee.first_name} {employee.last_name}",
        "count": len(payslips),
        "payslips": [
            {
                "id": str(p.id),
                "year": p.year,
                "month": p.month,
                "period": f"{p.year}-{p.month:02d}",
                "total_hours": float(p.total_hours),
                "gross_salary": float(p.gross_salary),
                "total_deductions": float(p.total_deductions),
                "net_salary": float(p.net_salary),
                "pdf_available": p.pdf_generated,
                "created_at": p.created_at.isoformat(),
            }
            for p in payslips
        ],
    }


@router.get("/payslips/{payslip_id}")
async def get_payslip_detail(
    payslip_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Get detailed payslip.
    Employees can only view their own payslips.
    Managers can view any payslip.
    """
    from src.db.models import PaySlipModel

    result = await db.execute(
        select(PaySlipModel).where(PaySlipModel.id == payslip_id)
    )
    payslip = result.scalar_one_or_none()

    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")

    # Check authorization
    employee = await get_employee_from_token(db, current_user)
    user_roles = current_user.get("user_roles", [])
    is_manager = any(r in user_roles for r in ["pos-manager", "pos-admin"])

    if not is_manager and (not employee or payslip.employee_id != employee.id):
        raise HTTPException(status_code=403, detail="Cannot view this payslip")

    return {
        "id": str(payslip.id),
        "employee_name": payslip.employee_name,
        "employee_number": payslip.employee_number,
        "ahv_number": payslip.ahv_number,
        "period": f"{payslip.year}-{payslip.month:02d}",
        "hourly_rate": float(payslip.hourly_rate),

        "hours": {
            "regular": float(payslip.regular_hours),
            "remote": float(payslip.remote_hours),
            "holiday": float(payslip.holiday_hours),
            "sick": float(payslip.sick_hours),
            "public_holiday": float(payslip.public_holiday_hours),
            "overtime": float(payslip.overtime_hours),
            "training": float(payslip.training_hours),
            "unpaid": float(payslip.unpaid_hours),
            "total": float(payslip.total_hours),
        },

        "gross": {
            "regular_pay": float(payslip.regular_pay),
            "remote_pay": float(payslip.remote_pay),
            "holiday_pay": float(payslip.holiday_pay),
            "sick_pay": float(payslip.sick_pay),
            "public_holiday_pay": float(payslip.public_holiday_pay),
            "overtime_pay": float(payslip.overtime_pay),
            "training_pay": float(payslip.training_pay),
            "gross_salary": float(payslip.gross_salary),
        },

        "deductions": {
            "ahv_iv_eo": float(payslip.ahv_iv_eo),
            "alv": float(payslip.alv),
            "alv2": float(payslip.alv2),
            "bvg": float(payslip.bvg),
            "uvg_nbu": float(payslip.uvg_nbu),
            "ktg": float(payslip.ktg),
            "quellensteuer": float(payslip.quellensteuer),
            "other": float(payslip.other_deductions),
            "total": float(payslip.total_deductions),
        },

        "additions": {
            "kb_bonus": float(payslip.kb_bonus),
            "expense_reimbursement": float(payslip.expense_reimbursement),
            "other": float(payslip.other_additions),
        },

        "net_salary": float(payslip.net_salary),

        "employer_costs": {
            "ahv": float(payslip.employer_ahv),
            "alv": float(payslip.employer_alv),
            "bvg": float(payslip.employer_bvg),
            "uvg": float(payslip.employer_uvg),
            "fak": float(payslip.employer_fak),
            "admin": float(payslip.employer_admin),
            "total": float(payslip.total_employer_cost),
        },

        "delivery": {
            "pdf_generated": payslip.pdf_generated,
            "pdf_path": payslip.pdf_path,
            "email_sent": payslip.email_sent,
            "email_sent_at": payslip.email_sent_at.isoformat() if payslip.email_sent_at else None,
        },

        "notes": payslip.notes,
        "created_at": payslip.created_at.isoformat(),
    }
