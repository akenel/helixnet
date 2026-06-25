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
from uuid import UUID, uuid4
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
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
from sqlalchemy.exc import IntegrityError
import httpx

from src.core.config import settings
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
    Find the employee record for the authenticated POS user — and SELF-HEAL the link.

    1. PRIMARY (the real link): sub → users.keycloak_id → users.id → employees.user_id.
    2. USERNAME LINK (Felix-owned, the "Settings ▸ Cashiers" mapping): the employee is linked
       to a `users` row whose `username` matches the token's `preferred_username`. When this
       matches but the primary missed, we **write `users.keycloak_id = sub`** so the primary
       path resolves on every future login (lazy self-heal — first login stitches the identity).
    3. LAST-RESORT heuristics (email / first name): only if no explicit link exists yet, so a
       brand-new seeded cast still resolves. Unambiguous single-row matches only; logged.

    No schema change: the link lives entirely in the existing `users` table (username + keycloak_id).
    """
    keycloak_sub = token_payload.get("sub")
    if not keycloak_sub:
        return None
    try:
        sub_uuid = UUID(keycloak_sub)
    except (ValueError, TypeError):
        sub_uuid = None

    # 1. PRIMARY: the proper users.keycloak_id → employees.user_id join.
    if sub_uuid is not None:
        result = await db.execute(
            select(EmployeeModel)
            .join(UserModel, EmployeeModel.user_id == UserModel.id)
            .where(UserModel.keycloak_id == sub_uuid)
        )
        employee = result.scalar_one_or_none()
        if employee:
            return employee

    email = (token_payload.get("email") or "").strip().lower()
    username = (token_payload.get("preferred_username") or "").strip().lower()

    # 2. USERNAME LINK: employee → users.username == token username. Self-heal keycloak_id.
    if username:
        result = await db.execute(
            select(EmployeeModel, UserModel)
            .join(UserModel, EmployeeModel.user_id == UserModel.id)
            .where(func.lower(UserModel.username) == username)
        )
        row = result.first()
        if row:
            employee, user = row
            if sub_uuid is not None and user.keycloak_id != sub_uuid:
                try:
                    user.keycloak_id = sub_uuid  # stitch the real identity, once
                    await db.commit()
                    logger.info("HR identity link self-healed: users.keycloak_id set for '%s' → %s %s",
                                username, employee.first_name, employee.last_name)
                except Exception:
                    await db.rollback()  # resolution still succeeds; heal next time
            return employee

    # 3. LAST-RESORT heuristics (only until Felix links them in Settings ▸ Cashiers).
    if email:
        result = await db.execute(
            select(EmployeeModel).where(func.lower(EmployeeModel.email) == email)
        )
        employee = result.scalar_one_or_none()
        if employee:
            logger.info("HR identity bridge (email): %s → %s %s",
                        email, employee.first_name, employee.last_name)
            return employee

    if username:
        result = await db.execute(
            select(EmployeeModel).where(func.lower(EmployeeModel.first_name) == username)
        )
        matches = result.scalars().all()
        if len(matches) == 1:
            logger.info("HR identity bridge (first-name): '%s' → %s %s",
                        username, matches[0].first_name, matches[0].last_name)
            return matches[0]
        if len(matches) > 1:
            logger.warning("HR identity bridge: username '%s' matched %d employees — "
                           "refusing to guess; link them in Settings ▸ Cashiers.",
                           username, len(matches))

    return None


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
                "entry_type": e.entry_type,
                "hours": float(e.hours),
                "start_time": e.start_time,
                "end_time": e.end_time,
                "break_minutes": e.break_minutes,
                "status": e.status,
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
            detail=f"Entry already exists for {entry.entry_date} with type {entry.entry_type}"
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
        status="draft",
        kb_contribution_id=entry.kb_contribution_id,
    )

    db.add(new_entry)
    await db.commit()
    await db.refresh(new_entry)

    logger.info(f"Time entry created: {employee.first_name} {entry.entry_date} {entry.hours}h")

    return {
        "id": str(new_entry.id),
        "entry_date": new_entry.entry_date.isoformat(),
        "entry_type": new_entry.entry_type,
        "hours": float(new_entry.hours),
        "status": new_entry.status,
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
    if entry.status != "draft":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot edit entry with status '{entry.status}'. Only draft entries can be modified."
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
        "status": entry.status,
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

    if entry.status != "draft":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete entry with status '{entry.status}'"
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

        if entry.status != "draft":
            errors.append(f"{entry_id}: not in draft status")
            continue

        entry.status = "submitted"
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
        .where(TimeEntryModel.status == "submitted")
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
                "entry_type": entry.entry_type,
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
    # Lookup local user ID from keycloak sub
    keycloak_sub = UUID(current_user.get("sub"))
    user_result = await db.execute(
        select(UserModel.id).where(UserModel.keycloak_id == keycloak_sub)
    )
    approver_id = user_result.scalar_one_or_none()

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

        if entry.status != "submitted":
            errors.append(f"{entry_id}: not in submitted status")
            continue

        if approval.action == "approve":
            entry.status = "approved"
            entry.approved_by_id = approver_id
            entry.approved_at = datetime.now(timezone.utc)
            entry.rejection_reason = None
            approved_count += 1
        else:  # reject
            entry.status = "rejected"
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
    total_hours = sum(e.hours for e in entries if e.status != "rejected")
    pending_count = sum(1 for e in entries if e.status == "submitted")
    draft_count = sum(1 for e in entries if e.status == "draft")

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
                "entry_type": e.entry_type,
                "hours": float(e.hours),
                "status": e.status,
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
        "status": employee.status,
        "contract_type": employee.contract_type,
        "hours_per_week": float(employee.hours_per_week),
        "hourly_rate": float(employee.hourly_rate),
        "start_date": employee.start_date.isoformat(),
        "remote_days_per_week": employee.remote_days_per_week,
        "health_insurance_active": employee.health_insurance_active,
        "bvg_insured": employee.bvg_insured,
    }


# ================================================================
# EMPLOYEES — roster + login link (Settings ▸ Cashiers)
# ================================================================

@router.get("/employees")
async def list_employees(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """The roster for Settings ▸ Cashiers — every employee + the POS login they're linked to.
    Manager/admin only."""
    result = await db.execute(
        select(EmployeeModel, UserModel)
        .outerjoin(UserModel, EmployeeModel.user_id == UserModel.id)
        .order_by(EmployeeModel.first_name)
    )
    rows = result.all()
    return {
        "employees": [
            {
                "id": str(e.id),
                "first_name": e.first_name,
                "last_name": e.last_name,
                "email": e.email,
                "employee_number": e.employee_number,
                "status": e.status,
                "contract_type": e.contract_type,
                "login_username": (u.username if u else None),
                "is_linked": u is not None,
            }
            for (e, u) in rows
        ],
        "total": len(rows),
    }


@router.post("/employees/{employee_id}/link")
async def link_employee_login(
    employee_id: UUID,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """Link an HR employee to a POS login username — the real identity link Felix controls.
    Finds the `users` row by username (creates a placeholder if absent) and points
    employee.user_id at it. The real Keycloak sub is stitched on that person's next login
    (self-heal in get_employee_from_token). Pass an empty username to UNLINK. Manager/admin only."""
    username = (payload.get("username") or "").strip().lower()
    employee = (await db.execute(
        select(EmployeeModel).where(EmployeeModel.id == employee_id)
    )).scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if not username:
        employee.user_id = None
        await db.commit()
        return {"id": str(employee.id), "login_username": None, "is_linked": False,
                "message": "Login unlinked."}

    user = (await db.execute(
        select(UserModel).where(func.lower(UserModel.username) == username)
    )).scalar_one_or_none()

    if user:
        # One login = one employee. Don't steal a username already linked elsewhere.
        other = (await db.execute(
            select(EmployeeModel).where(
                EmployeeModel.user_id == user.id, EmployeeModel.id != employee.id
            )
        )).scalar_one_or_none()
        if other:
            raise HTTPException(
                status_code=409,
                detail=f"'{username}' is already linked to {other.first_name} {other.last_name}."
            )
        employee.user_id = user.id
    else:
        # New login row. `users.email` is UNIQUE — derive it from the (unique) username,
        # NOT the employee's email, which already belongs to their existing user row
        # (re-linking to a new username would otherwise collide → 500).
        user = UserModel(
            keycloak_id=uuid4(),  # placeholder — self-healed on first login
            username=username,
            email=f"{username}@pos.local",
        )
        db.add(user)
        employee.user = user  # SQLAlchemy fills employee.user_id on flush

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Could not link '{username}' — that login name or email is already in use."
        )
    logger.info("Cashier link: employee %s %s → login '%s'",
                employee.first_name, employee.last_name, username)
    return {"id": str(employee.id), "login_username": username,
            "is_linked": True, "message": f"Linked to {username}."}


async def _kc_pos_admin(c: httpx.AsyncClient) -> dict:
    """Master-realm admin token + the POS-realm admin base URL."""
    r = await c.post(
        f"{settings.KEYCLOAK_SERVER_URL}/realms/master/protocol/openid-connect/token",
        data={"grant_type": "password", "client_id": "admin-cli",
              "username": settings.KEYCLOAK_ADMIN_USER,
              "password": settings.KEYCLOAK_ADMIN_PASSWORD.get_secret_value()},
    )
    r.raise_for_status()
    return {"h": {"Authorization": f"Bearer {r.json()['access_token']}"},
            "base": f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.POS_REALM}"}


@router.post("/employees/{employee_id}/provision-login")
async def provision_login(
    employee_id: UUID,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """Create (or update) a REAL Keycloak sign-in for an employee: set their password, give
    them the cashier role, and link it to their card. This is what actually lets a new hire
    log in. Re-running with a new password = a password reset. Manager/admin only."""
    username = (payload.get("username") or "").strip().lower()
    password = (payload.get("password") or "").strip()
    if not username:
        raise HTTPException(status_code=422, detail="Give the login a username (e.g. leanna).")
    if len(password) < 6:
        raise HTTPException(status_code=422, detail="Password must be at least 6 characters.")

    employee = (await db.execute(
        select(EmployeeModel).where(EmployeeModel.id == employee_id)
    )).scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    uid = None
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            kc = await _kc_pos_admin(c)
            h, base = kc["h"], kc["base"]

            existing = (await c.get(f"{base}/users", headers=h,
                                    params={"username": username, "exact": "true"})).json()
            if existing:
                uid = existing[0]["id"]
            else:
                cr = await c.post(f"{base}/users", headers=h, json={
                    "username": username,
                    "email": employee.email or f"{username}@pos.local",
                    "enabled": True, "emailVerified": True,
                    "firstName": (employee.first_name or username)[:60],
                    "lastName": (employee.last_name or "")[:60],
                    "requiredActions": [],
                    "credentials": [{"type": "password", "value": password, "temporary": False}],
                })
                cr.raise_for_status()
                uid = (await c.get(f"{base}/users", headers=h,
                                   params={"username": username, "exact": "true"})).json()[0]["id"]

            # (Re)set the password — covers both create and reset.
            await c.put(f"{base}/users/{uid}/reset-password", headers=h,
                        json={"type": "password", "value": password, "temporary": False})

            # Cashier role — match by substring (role names carry an emoji prefix).
            roles = (await c.get(f"{base}/roles", headers=h)).json()
            cashier = next((r for r in roles if "pos-cashier" in (r.get("name") or "")), None)
            if cashier:
                await c.post(f"{base}/users/{uid}/role-mappings/realm", headers=h, json=[cashier])
            else:
                logger.warning("provision-login: no pos-cashier role in %s", settings.POS_REALM)
    except httpx.HTTPError as e:
        logger.error("provision-login Keycloak error: %s", e)
        raise HTTPException(status_code=502, detail="Could not reach the login server. Try again.")

    # Link locally with the REAL Keycloak id (primary path resolves immediately).
    try:
        kc_uuid = UUID(uid)
    except (ValueError, TypeError):
        kc_uuid = uuid4()
    user = (await db.execute(
        select(UserModel).where(func.lower(UserModel.username) == username)
    )).scalar_one_or_none()
    if user:
        user.keycloak_id = kc_uuid
        employee.user_id = user.id
    else:
        user = UserModel(keycloak_id=kc_uuid, username=username, email=f"{username}@pos.local")
        db.add(user)
        employee.user = user
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409,
                            detail=f"'{username}' could not be linked — name or email already in use.")

    logger.info("Login provisioned: %s %s → '%s' (cashier)",
                employee.first_name, employee.last_name, username)
    return {"id": str(employee.id), "login_username": username, "is_linked": True,
            "message": f"Sign-in ready — {username} can log in now."}


def _employee_card(e: EmployeeModel, login_username: Optional[str] = None) -> dict:
    """Full employee card payload (the 'who's who')."""
    return {
        "id": str(e.id),
        "employee_number": e.employee_number,
        "first_name": e.first_name,
        "last_name": e.last_name,
        "date_of_birth": e.date_of_birth.isoformat() if e.date_of_birth else None,
        "nationality": e.nationality,
        "ahv_number": e.ahv_number,
        "email": e.email,
        "phone": e.phone,
        "street": e.street,
        "postal_code": e.postal_code,
        "city": e.city,
        "canton": e.canton,
        "iban": e.iban,
        "bank_name": e.bank_name,
        "contract_type": e.contract_type,
        "status": e.status,
        "start_date": e.start_date.isoformat() if e.start_date else None,
        "hours_per_week": float(e.hours_per_week),
        "hourly_rate": float(e.hourly_rate),
        "emergency_contact_name": e.emergency_contact_name,
        "emergency_contact_phone": e.emergency_contact_phone,
        "notes": e.notes,
        "login_username": login_username,
        "is_linked": login_username is not None,
    }


async def _next_employee_number(db: AsyncSession) -> str:
    """Auto-number new hires as BLQ-NNN (max existing + 1)."""
    result = await db.execute(select(EmployeeModel.employee_number))
    mx = 0
    for (num,) in result.all():
        if num and "-" in num:
            tail = num.rsplit("-", 1)[-1]
            if tail.isdigit():
                mx = max(mx, int(tail))
    return f"BLQ-{mx + 1:03d}"


@router.get("/employees/{employee_id}")
async def get_employee(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """Full employee card. Manager/admin only."""
    row = (await db.execute(
        select(EmployeeModel, UserModel)
        .outerjoin(UserModel, EmployeeModel.user_id == UserModel.id)
        .where(EmployeeModel.id == employee_id)
    )).first()
    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")
    e, u = row
    return _employee_card(e, u.username if u else None)


@router.post("/employees", status_code=status.HTTP_201_CREATED)
async def create_employee(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """Onboard a new employee — the one-time 'who's who' card (Leanna: name, AHV, DOB, address).
    Only the human essentials are required; employment/payroll fields default and are edited
    later. employee_number is auto-generated. Manager/admin only."""
    def req(k):
        v = (str(payload.get(k) or "")).strip()
        if not v:
            raise HTTPException(status_code=422, detail=f"'{k}' is required")
        return v

    first_name = req("first_name")
    last_name = req("last_name")
    ahv_number = req("ahv_number")
    email = req("email")
    street = req("street")
    postal_code = req("postal_code")
    city = req("city")

    # Dates
    try:
        dob = date.fromisoformat(req("date_of_birth"))
    except ValueError:
        raise HTTPException(status_code=422, detail="date_of_birth must be YYYY-MM-DD")
    start_raw = (str(payload.get("start_date") or "")).strip()
    try:
        start = date.fromisoformat(start_raw) if start_raw else date.today()
    except ValueError:
        raise HTTPException(status_code=422, detail="start_date must be YYYY-MM-DD")

    def dec(k, default):
        try:
            return Decimal(str(payload.get(k))) if payload.get(k) not in (None, "") else Decimal(default)
        except Exception:
            return Decimal(default)

    emp = EmployeeModel(
        first_name=first_name,
        last_name=last_name,
        date_of_birth=dob,
        nationality=(str(payload.get("nationality") or "CH")).strip() or "CH",
        ahv_number=ahv_number,
        email=email,
        phone=(str(payload.get("phone") or "")).strip() or None,
        street=street,
        postal_code=postal_code,
        city=city,
        canton=(str(payload.get("canton") or "LU")).strip().upper()[:2] or "LU",
        iban=(str(payload.get("iban") or "")).strip(),  # fill later
        bank_name=(str(payload.get("bank_name") or "")).strip() or None,
        employee_number=await _next_employee_number(db),
        contract_type=(str(payload.get("contract_type") or "fulltime")).strip(),
        status=(str(payload.get("status") or "probation")).strip(),
        start_date=start,
        hours_per_week=dec("hours_per_week", "40"),
        hourly_rate=dec("hourly_rate", "0"),
    )
    db.add(emp)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="That AHV number or employee already exists.")
    await db.refresh(emp)
    logger.info("Employee onboarded: %s %s (%s)", emp.first_name, emp.last_name, emp.employee_number)
    return _employee_card(emp)


@router.put("/employees/{employee_id}")
async def update_employee(
    employee_id: UUID,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """Edit an employee card. Manager/admin only."""
    emp = (await db.execute(
        select(EmployeeModel).where(EmployeeModel.id == employee_id)
    )).scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    text_fields = ["first_name", "last_name", "email", "phone", "street", "postal_code",
                   "city", "canton", "ahv_number", "iban", "bank_name", "contract_type",
                   "status", "nationality", "emergency_contact_name", "emergency_contact_phone", "notes"]
    for f in text_fields:
        if f in payload:
            v = payload.get(f)
            setattr(emp, f, (str(v).strip() or None) if v is not None else None)
    for f in ["date_of_birth", "start_date"]:
        if payload.get(f):
            try:
                setattr(emp, f, date.fromisoformat(str(payload[f])))
            except ValueError:
                raise HTTPException(status_code=422, detail=f"{f} must be YYYY-MM-DD")
    for f in ["hours_per_week", "hourly_rate"]:
        if payload.get(f) not in (None, ""):
            try:
                setattr(emp, f, Decimal(str(payload[f])))
            except Exception:
                raise HTTPException(status_code=422, detail=f"{f} must be a number")

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="That AHV number is already in use.")
    await db.refresh(emp)
    return _employee_card(emp)


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
        by_status[e.status].append(e)

    # Calculate by type
    by_type = {}
    for e in entries:
        if e.status != "rejected":
            t = e.entry_type
            by_type[t] = by_type.get(t, Decimal("0")) + e.hours

    total_hours = sum(e.hours for e in entries if e.status not in ["rejected", "draft"])
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

async def get_local_user_id(db: AsyncSession, keycloak_sub: str) -> Optional[UUID]:
    """Lookup local user ID from Keycloak sub."""
    result = await db.execute(
        select(UserModel.id).where(UserModel.keycloak_id == UUID(keycloak_sub))
    )
    return result.scalar_one_or_none()


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
        creator_id = await get_local_user_id(db, current_user.get("sub"))
        payroll_run = await calculator.create_payroll_run(year, month, creator_id, notes)

        return {
            "id": str(payroll_run.id),
            "period": payroll_run.period_name,
            "status": payroll_run.status,
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
        approver_id = await get_local_user_id(db, current_user.get("sub"))
        payroll_run = await calculator.approve_payroll_run(payroll_run_id, approver_id)

        return {
            "id": str(payroll_run.id),
            "period": payroll_run.period_name,
            "status": payroll_run.status,
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
            "status": payroll_run.status,
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
                "status": r.status,
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
