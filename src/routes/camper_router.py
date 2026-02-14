# File: src/routes/camper_router.py
"""
Camper & Tour Service Management API Router.
Handles vehicles, customers, service jobs, quotations, purchase orders,
invoices, documents, calendar, and dashboard for Sebastino's shop.

Prefix: /api/v1/camper

"Casa e dove parcheggi." - Home is where you park it.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
from uuid import UUID
from typing import Optional
from pathlib import Path
import io

from src.db.database import get_db_session
from src.db.models.camper_vehicle_model import CamperVehicleModel, VehicleStatus
from src.db.models.camper_customer_model import CamperCustomerModel
from src.db.models.camper_service_job_model import CamperServiceJobModel, JobStatus
from src.db.models.camper_quotation_model import CamperQuotationModel, QuotationStatus
from src.db.models.camper_purchase_order_model import CamperPurchaseOrderModel, CamperPOStatus
from src.db.models.camper_invoice_model import CamperInvoiceModel, PaymentStatus
from src.db.models.camper_document_model import CamperDocumentModel
from src.schemas.camper_schema import (
    VehicleCreate, VehicleUpdate, VehicleRead, VehicleStatusUpdate,
    CamperCustomerCreate, CamperCustomerUpdate, CamperCustomerRead,
    ServiceJobCreate, ServiceJobUpdate, ServiceJobRead, ServiceJobStatusUpdate,
    QuotationCreate, QuotationUpdate, QuotationRead,
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderRead, POStatusUpdate,
    InvoiceCreate, InvoiceRead, InvoicePayment,
    DocumentRead, CalendarEvent,
    InspectionResult, DepositPayment,
    DashboardSummary,
)
from src.core.keycloak_auth import require_roles
from src.services.camper_email_service import (
    send_quotation_email, send_quotation_accepted_email,
    send_deposit_received_email, send_job_complete_email, send_invoice_email,
)
from src.services.camper_telegram_service import (
    notify_vehicle_ready, notify_deposit_received as telegram_notify_deposit,
)

logger = logging.getLogger(__name__)

# API Router (JSON endpoints)
router = APIRouter(prefix="/api/v1/camper", tags=["Camper & Tour"])

# HTML Router (Web UI pages for Nino's team)
html_router = APIRouter(tags=["Camper & Tour - Web UI"])

# Setup Jinja2 templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


# ================================================================
# AUTH HELPERS (Camper-specific role shortcuts)
# ================================================================

def require_any_camper_role():
    """Any authenticated camper staff"""
    return require_roles([
        "camper-counter",
        "camper-mechanic",
        "camper-manager",
        "camper-admin",
    ])


def require_camper_mechanic_or_above():
    """Mechanic, manager, or admin"""
    return require_roles([
        "camper-mechanic",
        "camper-manager",
        "camper-admin",
    ])


def require_camper_manager_or_admin():
    """Manager or admin only"""
    return require_roles([
        "camper-manager",
        "camper-admin",
    ])


# ================================================================
# VEHICLE ENDPOINTS
# ================================================================

@router.post("/vehicles", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle: VehicleCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Register a new vehicle (any camper role)"""
    # Check for duplicate plate
    existing = await db.execute(
        select(CamperVehicleModel).where(
            CamperVehicleModel.registration_plate == vehicle.registration_plate.upper()
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Vehicle with plate '{vehicle.registration_plate}' already registered"
        )

    vehicle_data = vehicle.model_dump()
    vehicle_data["registration_plate"] = vehicle_data["registration_plate"].upper()
    vehicle_data["status"] = VehicleStatus.CHECKED_IN
    new_vehicle = CamperVehicleModel(**vehicle_data)
    db.add(new_vehicle)
    await db.commit()
    await db.refresh(new_vehicle)

    logger.info(f"Vehicle registered: {new_vehicle.registration_plate} by {current_user['username']}")
    return new_vehicle


@router.get("/vehicles", response_model=list[VehicleRead])
async def list_vehicles(
    status_filter: Optional[str] = None,
    owner_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """List vehicles with optional filters (any camper role)"""
    query = select(CamperVehicleModel).where(CamperVehicleModel.is_active == True)

    if status_filter:
        try:
            vs = VehicleStatus(status_filter)
            query = query.where(CamperVehicleModel.status == vs)
        except ValueError:
            pass

    if owner_name:
        query = query.where(CamperVehicleModel.owner_name.ilike(f"%{owner_name}%"))

    query = query.order_by(CamperVehicleModel.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/vehicles/{vehicle_id}", response_model=VehicleRead)
async def get_vehicle(
    vehicle_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Get vehicle by ID (any camper role)"""
    result = await db.execute(
        select(CamperVehicleModel).where(CamperVehicleModel.id == vehicle_id)
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.get("/vehicles/plate/{plate}", response_model=VehicleRead)
async def get_vehicle_by_plate(
    plate: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Lookup vehicle by registration plate -- the fast path"""
    result = await db.execute(
        select(CamperVehicleModel).where(
            CamperVehicleModel.registration_plate == plate.upper()
        )
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail=f"No vehicle found with plate '{plate}'")
    return vehicle


@router.put("/vehicles/{vehicle_id}", response_model=VehicleRead)
async def update_vehicle(
    vehicle_id: UUID,
    vehicle_update: VehicleUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Update vehicle info (any camper role)"""
    result = await db.execute(
        select(CamperVehicleModel).where(CamperVehicleModel.id == vehicle_id)
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    update_data = vehicle_update.model_dump(exclude_unset=True)
    # Uppercase plate if provided
    if "registration_plate" in update_data and update_data["registration_plate"]:
        update_data["registration_plate"] = update_data["registration_plate"].upper()

    for field, value in update_data.items():
        setattr(vehicle, field, value)

    vehicle.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(vehicle)

    logger.info(f"Vehicle updated: {vehicle.registration_plate} by {current_user['username']}")
    return vehicle


@router.patch("/vehicles/{vehicle_id}/status", response_model=VehicleRead)
async def update_vehicle_status(
    vehicle_id: UUID,
    status_update: VehicleStatusUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Change vehicle status (check in / pick up)"""
    result = await db.execute(
        select(CamperVehicleModel).where(CamperVehicleModel.id == vehicle_id)
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    vehicle.status = status_update.status
    vehicle.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(vehicle)

    logger.info(f"Vehicle {vehicle.registration_plate} status -> {status_update.status.value} by {current_user['username']}")
    return vehicle


# ================================================================
# CUSTOMER ENDPOINTS
# ================================================================

@router.post("/customers", response_model=CamperCustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer: CamperCustomerCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Create customer profile (any camper role)"""
    new_customer = CamperCustomerModel(
        **customer.model_dump(),
        first_visit=date.today(),
        last_visit=date.today(),
        visit_count=1,
    )
    db.add(new_customer)
    await db.commit()
    await db.refresh(new_customer)

    logger.info(f"Customer created: {new_customer.name} by {current_user['username']}")
    return new_customer


@router.get("/customers", response_model=list[CamperCustomerRead])
async def list_customers(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """List/search customers (any camper role)"""
    query = select(CamperCustomerModel)

    if search:
        query = query.where(
            CamperCustomerModel.name.ilike(f"%{search}%") |
            CamperCustomerModel.phone.ilike(f"%{search}%") |
            CamperCustomerModel.email.ilike(f"%{search}%")
        )

    query = query.order_by(CamperCustomerModel.last_visit.desc().nullslast()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/customers/{customer_id}", response_model=CamperCustomerRead)
async def get_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Get customer with vehicles and job history"""
    result = await db.execute(
        select(CamperCustomerModel).where(CamperCustomerModel.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.put("/customers/{customer_id}", response_model=CamperCustomerRead)
async def update_customer(
    customer_id: UUID,
    customer_update: CamperCustomerUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Update customer info (any camper role)"""
    result = await db.execute(
        select(CamperCustomerModel).where(CamperCustomerModel.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = customer_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    customer.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(customer)

    logger.info(f"Customer updated: {customer.name} by {current_user['username']}")
    return customer


# ================================================================
# SERVICE JOB ENDPOINTS
# ================================================================

@router.post("/jobs", response_model=ServiceJobRead, status_code=status.HTTP_201_CREATED)
async def create_job(
    job: ServiceJobCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Create new service job (starts as QUOTED)"""
    # Verify vehicle exists
    vehicle_result = await db.execute(
        select(CamperVehicleModel).where(CamperVehicleModel.id == job.vehicle_id)
    )
    if not vehicle_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Verify customer exists
    customer_result = await db.execute(
        select(CamperCustomerModel).where(CamperCustomerModel.id == job.customer_id)
    )
    if not customer_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Customer not found")

    # Generate job number
    today = date.today().strftime("%Y%m%d")
    count_result = await db.execute(
        select(func.count()).where(
            CamperServiceJobModel.job_number.like(f"JOB-{today}-%")
        )
    )
    count = count_result.scalar() or 0
    job_number = f"JOB-{today}-{count + 1:04d}"

    job_data = job.model_dump()
    job_data["job_number"] = job_number
    job_data["status"] = JobStatus.QUOTED
    new_job = CamperServiceJobModel(**job_data)
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    logger.info(f"Service job created: {job_number} by {current_user['username']}")
    return new_job


@router.get("/jobs", response_model=list[ServiceJobRead])
async def list_jobs(
    status_filter: Optional[str] = None,
    mechanic: Optional[str] = None,
    vehicle_id: Optional[UUID] = None,
    customer_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """List jobs with filters (any camper role)"""
    query = select(CamperServiceJobModel)

    if status_filter:
        try:
            js = JobStatus(status_filter)
            query = query.where(CamperServiceJobModel.status == js)
        except ValueError:
            pass

    if mechanic:
        query = query.where(CamperServiceJobModel.assigned_to.ilike(f"%{mechanic}%"))

    if vehicle_id:
        query = query.where(CamperServiceJobModel.vehicle_id == vehicle_id)

    if customer_id:
        query = query.where(CamperServiceJobModel.customer_id == customer_id)

    query = query.order_by(CamperServiceJobModel.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/jobs/{job_id}", response_model=ServiceJobRead)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Get full job details"""
    result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Service job not found")
    return job


@router.put("/jobs/{job_id}", response_model=ServiceJobRead)
async def update_job(
    job_id: UUID,
    job_update: ServiceJobUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_mechanic_or_above()),
):
    """Update job details (mechanic/manager/admin). Supports optimistic locking via expected_updated_at."""
    result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Service job not found")

    update_data = job_update.model_dump(exclude_unset=True)

    # Optimistic locking: if client sends expected_updated_at, reject stale writes
    expected = update_data.pop("expected_updated_at", None)
    if expected is not None and job.updated_at is not None:
        # Compare with 1-second tolerance (DB vs Python datetime precision)
        if abs((job.updated_at - expected).total_seconds()) > 1:
            raise HTTPException(
                status_code=409,
                detail=f"Conflitto: il lavoro è stato modificato da un altro utente alle {job.updated_at.strftime('%H:%M:%S')}. Ricarica la pagina."
            )

    for field, value in update_data.items():
        setattr(job, field, value)

    job.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(job)

    logger.info(f"Job updated: {job.job_number} by {current_user['username']}")
    return job


@router.patch("/jobs/{job_id}/status", response_model=ServiceJobRead)
async def update_job_status(
    job_id: UUID,
    status_update: ServiceJobStatusUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_mechanic_or_above()),
):
    """Advance job status (mechanic/manager/admin)"""
    result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Service job not found")

    old_status = job.status
    job.status = status_update.status
    job.updated_at = datetime.now(timezone.utc)

    # Auto-set timestamps based on status transitions
    if status_update.status == JobStatus.IN_PROGRESS and not job.started_at:
        job.started_at = datetime.now(timezone.utc)
    elif status_update.status == JobStatus.COMPLETED and not job.completed_at:
        job.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(job)

    logger.info(f"Job {job.job_number}: {old_status.value} -> {status_update.status.value} by {current_user['username']}")
    return job


@router.post("/jobs/{job_id}/approve", response_model=ServiceJobRead)
async def approve_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Customer approves quote -> status becomes APPROVED"""
    result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Service job not found")

    if job.status != JobStatus.QUOTED:
        raise HTTPException(
            status_code=400,
            detail=f"Can only approve jobs in QUOTED status. Current: {job.status.value}"
        )

    job.status = JobStatus.APPROVED
    job.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(job)

    logger.info(f"Job {job.job_number} APPROVED by {current_user['username']}")
    return job


@router.post("/jobs/{job_id}/complete", response_model=ServiceJobRead)
async def complete_job(
    job_id: UUID,
    actual_hours: Optional[float] = None,
    actual_parts_cost: Optional[float] = None,
    work_performed: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_mechanic_or_above()),
):
    """Mechanic marks job done, logs final hours/parts"""
    result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Service job not found")

    if job.status not in (JobStatus.IN_PROGRESS, JobStatus.WAITING_PARTS, JobStatus.APPROVED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot complete job in {job.status.value} status"
        )

    job.status = JobStatus.COMPLETED
    job.completed_at = datetime.now(timezone.utc)
    job.updated_at = datetime.now(timezone.utc)

    if actual_hours is not None:
        job.actual_hours = actual_hours
    if actual_parts_cost is not None:
        job.actual_parts_cost = Decimal(str(actual_parts_cost))
    if work_performed:
        job.work_performed = work_performed

    # Calculate actual total (labor_rate * hours + parts)
    labor_rate = Decimal("35.00")  # EUR/hour -- Sicilian rate
    job.actual_labor_cost = Decimal(str(job.actual_hours)) * labor_rate
    job.actual_total = job.actual_labor_cost + job.actual_parts_cost

    await db.commit()
    await db.refresh(job)

    logger.info(f"Job {job.job_number} COMPLETED by {current_user['username']}: {job.actual_total} EUR")
    return job


# ================================================================
# INSPECTION WORKFLOW
# ================================================================

@router.post("/jobs/{job_id}/submit-inspection", response_model=ServiceJobRead)
async def submit_for_inspection(
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_mechanic_or_above()),
):
    """Mechanic submits job for manager inspection (IN_PROGRESS -> INSPECTION)"""
    result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Service job not found")

    if job.status != JobStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=400,
            detail=f"Can only submit for inspection from IN_PROGRESS. Current: {job.status.value}"
        )

    job.status = JobStatus.INSPECTION
    job.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(job)

    logger.info(f"Job {job.job_number} submitted for INSPECTION by {current_user['username']}")
    return job


@router.post("/jobs/{job_id}/pass-inspection", response_model=ServiceJobRead)
async def pass_inspection(
    job_id: UUID,
    result_data: InspectionResult,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_manager_or_admin()),
):
    """Manager passes inspection (INSPECTION -> COMPLETED)"""
    result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Service job not found")

    if job.status != JobStatus.INSPECTION:
        raise HTTPException(
            status_code=400,
            detail=f"Can only pass inspection from INSPECTION status. Current: {job.status.value}"
        )

    job.status = JobStatus.COMPLETED
    job.inspection_passed = True
    job.inspected_by = current_user['username']
    job.inspected_at = datetime.now(timezone.utc)
    job.completed_at = datetime.now(timezone.utc)
    job.updated_at = datetime.now(timezone.utc)
    if result_data.notes:
        job.inspection_notes = result_data.notes

    await db.commit()
    await db.refresh(job)

    logger.info(f"Job {job.job_number} PASSED inspection by {current_user['username']}")

    # Email + Telegram: vehicle ready for pickup
    try:
        customer_result = await db.execute(
            select(CamperCustomerModel).where(CamperCustomerModel.id == job.customer_id)
        )
        customer = customer_result.scalar_one_or_none()
        vehicle_result = await db.execute(
            select(CamperVehicleModel).where(CamperVehicleModel.id == job.vehicle_id)
        )
        vehicle = vehicle_result.scalar_one_or_none()
        if customer:
            plate = vehicle.registration_plate if vehicle else "N/A"
            if customer.email:
                send_job_complete_email(
                    to_email=customer.email,
                    customer_name=customer.name,
                    job_number=job.job_number,
                    vehicle_plate=plate,
                )
            if customer.telegram_chat_id:
                await notify_vehicle_ready(
                    chat_id=customer.telegram_chat_id,
                    customer_name=customer.name,
                    vehicle_plate=plate,
                )
    except Exception as e:
        logger.warning(f"Failed to send job complete notification: {e}")

    return job


@router.post("/jobs/{job_id}/fail-inspection", response_model=ServiceJobRead)
async def fail_inspection(
    job_id: UUID,
    result_data: InspectionResult,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_manager_or_admin()),
):
    """Manager fails inspection (INSPECTION -> IN_PROGRESS with notes)"""
    result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Service job not found")

    if job.status != JobStatus.INSPECTION:
        raise HTTPException(
            status_code=400,
            detail=f"Can only fail inspection from INSPECTION status. Current: {job.status.value}"
        )

    job.status = JobStatus.IN_PROGRESS
    job.inspection_passed = False
    job.inspected_by = current_user['username']
    job.inspected_at = datetime.now(timezone.utc)
    job.updated_at = datetime.now(timezone.utc)
    if result_data.notes:
        job.inspection_notes = result_data.notes

    await db.commit()
    await db.refresh(job)

    logger.info(f"Job {job.job_number} FAILED inspection by {current_user['username']}: {result_data.notes}")
    return job


# ================================================================
# DEPOSIT WORKFLOW
# ================================================================

@router.post("/jobs/{job_id}/record-deposit", response_model=ServiceJobRead)
async def record_deposit(
    job_id: UUID,
    deposit: DepositPayment,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Record deposit payment on a job"""
    result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Service job not found")

    job.deposit_paid = job.deposit_paid + deposit.amount
    job.deposit_paid_at = datetime.now(timezone.utc)
    job.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(job)

    logger.info(f"Job {job.job_number} deposit recorded: {deposit.amount} EUR ({deposit.payment_method}) by {current_user['username']}")

    # Email + Telegram notification for deposit
    try:
        customer_result = await db.execute(
            select(CamperCustomerModel).where(CamperCustomerModel.id == job.customer_id)
        )
        customer = customer_result.scalar_one_or_none()
        if customer:
            if customer.email:
                send_deposit_received_email(
                    to_email=customer.email,
                    customer_name=customer.name,
                    amount=f"{deposit.amount:.2f} EUR",
                    job_number=job.job_number,
                )
            if customer.telegram_chat_id:
                await telegram_notify_deposit(
                    chat_id=customer.telegram_chat_id,
                    customer_name=customer.name,
                    amount=f"{deposit.amount:.2f} EUR",
                )
    except Exception as e:
        logger.warning(f"Failed to send deposit notification: {e}")

    return job


# ================================================================
# QUOTATION ENDPOINTS
# ================================================================

def _calculate_quotation_totals(line_items: list, vat_rate: Decimal, deposit_percent: Decimal) -> dict:
    """Calculate subtotal, VAT, total, and deposit from line items"""
    subtotal = sum(Decimal(str(item.get("line_total", 0) if isinstance(item, dict) else item.line_total)) for item in line_items)
    vat_amount = (subtotal * vat_rate / Decimal("100")).quantize(Decimal("0.01"))
    total = subtotal + vat_amount
    deposit_amount = (total * deposit_percent / Decimal("100")).quantize(Decimal("0.01"))
    return {
        "subtotal": subtotal,
        "vat_amount": vat_amount,
        "total": total,
        "deposit_amount": deposit_amount,
    }


@router.post("/quotations", response_model=QuotationRead, status_code=status.HTTP_201_CREATED)
async def create_quotation(
    quotation: QuotationCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Create formal quotation for a job"""
    # Verify job exists
    job_result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == quotation.job_id)
    )
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Service job not found")

    # Generate quote number
    today = date.today().strftime("%Y%m%d")
    count_result = await db.execute(
        select(func.count()).where(
            CamperQuotationModel.quote_number.like(f"QUO-{today}-%")
        )
    )
    count = count_result.scalar() or 0
    quote_number = f"QUO-{today}-{count + 1:04d}"

    # Serialize line items and calculate totals
    line_items_data = [item.model_dump() for item in quotation.line_items]
    # Convert Decimal to float for JSONB
    for item in line_items_data:
        for key in ("unit_price", "line_total"):
            if key in item:
                item[key] = float(item[key])

    totals = _calculate_quotation_totals(quotation.line_items, quotation.vat_rate, quotation.deposit_percent)

    new_quotation = CamperQuotationModel(
        quote_number=quote_number,
        job_id=quotation.job_id,
        customer_id=quotation.customer_id,
        vehicle_id=quotation.vehicle_id,
        line_items=line_items_data,
        vat_rate=quotation.vat_rate,
        deposit_percent=quotation.deposit_percent,
        valid_until=quotation.valid_until,
        notes=quotation.notes,
        created_by=current_user['username'],
        **totals,
    )
    db.add(new_quotation)
    await db.commit()
    await db.refresh(new_quotation)

    logger.info(f"Quotation created: {quote_number} for {totals['total']} EUR by {current_user['username']}")
    return new_quotation


@router.get("/quotations", response_model=list[QuotationRead])
async def list_quotations(
    status_filter: Optional[str] = None,
    customer_id: Optional[UUID] = None,
    job_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """List quotations with filters"""
    query = select(CamperQuotationModel)

    if status_filter:
        try:
            qs = QuotationStatus(status_filter)
            query = query.where(CamperQuotationModel.status == qs)
        except ValueError:
            pass

    if customer_id:
        query = query.where(CamperQuotationModel.customer_id == customer_id)

    if job_id:
        query = query.where(CamperQuotationModel.job_id == job_id)

    query = query.order_by(CamperQuotationModel.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/quotations/{quotation_id}", response_model=QuotationRead)
async def get_quotation(
    quotation_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Get full quotation details"""
    result = await db.execute(
        select(CamperQuotationModel).where(CamperQuotationModel.id == quotation_id)
    )
    quotation = result.scalar_one_or_none()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return quotation


@router.put("/quotations/{quotation_id}", response_model=QuotationRead)
async def update_quotation(
    quotation_id: UUID,
    quotation_update: QuotationUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_manager_or_admin()),
):
    """Update quotation line items and recalculate totals"""
    result = await db.execute(
        select(CamperQuotationModel).where(CamperQuotationModel.id == quotation_id)
    )
    quotation = result.scalar_one_or_none()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    if quotation.status not in (QuotationStatus.DRAFT, QuotationStatus.SENT):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot update quotation in {quotation.status.value} status"
        )

    update_data = quotation_update.model_dump(exclude_unset=True)

    if "line_items" in update_data and update_data["line_items"] is not None:
        line_items_data = [item.model_dump() if hasattr(item, 'model_dump') else item for item in update_data["line_items"]]
        for item in line_items_data:
            for key in ("unit_price", "line_total"):
                if key in item:
                    item[key] = float(item[key])
        quotation.line_items = line_items_data

    if "vat_rate" in update_data and update_data["vat_rate"] is not None:
        quotation.vat_rate = update_data["vat_rate"]
    if "deposit_percent" in update_data and update_data["deposit_percent"] is not None:
        quotation.deposit_percent = update_data["deposit_percent"]
    if "valid_until" in update_data:
        quotation.valid_until = update_data["valid_until"]
    if "notes" in update_data:
        quotation.notes = update_data["notes"]

    # Recalculate totals
    totals = _calculate_quotation_totals(quotation.line_items, quotation.vat_rate, quotation.deposit_percent)
    quotation.subtotal = totals["subtotal"]
    quotation.vat_amount = totals["vat_amount"]
    quotation.total = totals["total"]
    quotation.deposit_amount = totals["deposit_amount"]
    quotation.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(quotation)

    logger.info(f"Quotation {quotation.quote_number} updated by {current_user['username']}")
    return quotation


@router.post("/quotations/{quotation_id}/send", response_model=QuotationRead)
async def send_quotation(
    quotation_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Mark quotation as SENT to customer"""
    result = await db.execute(
        select(CamperQuotationModel).where(CamperQuotationModel.id == quotation_id)
    )
    quotation = result.scalar_one_or_none()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    if quotation.status != QuotationStatus.DRAFT:
        raise HTTPException(status_code=400, detail=f"Can only send DRAFT quotations. Current: {quotation.status.value}")

    quotation.status = QuotationStatus.SENT
    quotation.sent_at = datetime.now(timezone.utc)
    quotation.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(quotation)

    logger.info(f"Quotation {quotation.quote_number} SENT by {current_user['username']}")

    # Email customer with quotation
    try:
        customer_result = await db.execute(
            select(CamperCustomerModel).where(CamperCustomerModel.id == quotation.customer_id)
        )
        customer = customer_result.scalar_one_or_none()
        if customer and customer.email:
            send_quotation_email(
                to_email=customer.email,
                customer_name=customer.name,
                quote_number=quotation.quote_number,
                total=f"{quotation.total:.2f} EUR",
                deposit=f"{quotation.deposit_amount:.2f} EUR",
            )
    except Exception as e:
        logger.warning(f"Failed to send quotation email: {e}")

    return quotation


@router.post("/quotations/{quotation_id}/accept", response_model=QuotationRead)
async def accept_quotation(
    quotation_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Accept quotation -> calculate deposit, update job to APPROVED"""
    result = await db.execute(
        select(CamperQuotationModel).where(CamperQuotationModel.id == quotation_id)
    )
    quotation = result.scalar_one_or_none()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    if quotation.status not in (QuotationStatus.DRAFT, QuotationStatus.SENT):
        raise HTTPException(
            status_code=400,
            detail=f"Can only accept DRAFT or SENT quotations. Current: {quotation.status.value}"
        )

    quotation.status = QuotationStatus.ACCEPTED
    quotation.accepted_at = datetime.now(timezone.utc)
    quotation.updated_at = datetime.now(timezone.utc)

    # Update job to APPROVED + set deposit required
    job_result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == quotation.job_id)
    )
    job = job_result.scalar_one_or_none()
    if job and job.status == JobStatus.QUOTED:
        job.status = JobStatus.APPROVED
        job.deposit_required = quotation.deposit_amount
        job.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(quotation)

    logger.info(f"Quotation {quotation.quote_number} ACCEPTED. Deposit required: {quotation.deposit_amount} EUR")

    # Email customer confirmation
    try:
        customer_result = await db.execute(
            select(CamperCustomerModel).where(CamperCustomerModel.id == quotation.customer_id)
        )
        customer = customer_result.scalar_one_or_none()
        if customer and customer.email:
            send_quotation_accepted_email(
                to_email=customer.email,
                customer_name=customer.name,
                quote_number=quotation.quote_number,
            )
    except Exception as e:
        logger.warning(f"Failed to send acceptance email: {e}")

    return quotation


@router.post("/quotations/{quotation_id}/reject", response_model=QuotationRead)
async def reject_quotation(
    quotation_id: UUID,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Reject quotation with optional reason"""
    result = await db.execute(
        select(CamperQuotationModel).where(CamperQuotationModel.id == quotation_id)
    )
    quotation = result.scalar_one_or_none()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    quotation.status = QuotationStatus.REJECTED
    quotation.rejected_at = datetime.now(timezone.utc)
    quotation.updated_at = datetime.now(timezone.utc)
    if reason:
        quotation.notes = (quotation.notes or "") + f"\nRejection reason: {reason}"

    await db.commit()
    await db.refresh(quotation)

    logger.info(f"Quotation {quotation.quote_number} REJECTED by {current_user['username']}")
    return quotation


# ================================================================
# PURCHASE ORDER ENDPOINTS
# ================================================================

@router.post("/purchase-orders", response_model=PurchaseOrderRead, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_manager_or_admin()),
):
    """Create purchase order for parts"""
    # Verify job exists
    job_result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == po.job_id)
    )
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Service job not found")

    # Generate PO number
    today = date.today().strftime("%Y%m%d")
    count_result = await db.execute(
        select(func.count()).where(
            CamperPurchaseOrderModel.po_number.like(f"PO-{today}-%")
        )
    )
    count = count_result.scalar() or 0
    po_number = f"PO-{today}-{count + 1:04d}"

    # Serialize line items
    line_items_data = [item.model_dump() for item in po.line_items]
    for item in line_items_data:
        for key in ("unit_price", "line_total"):
            if key in item:
                item[key] = float(item[key])

    subtotal = sum(Decimal(str(item.line_total)) for item in po.line_items)
    vat_amount = (subtotal * po.vat_rate / Decimal("100")).quantize(Decimal("0.01"))
    total = subtotal + vat_amount

    new_po = CamperPurchaseOrderModel(
        po_number=po_number,
        job_id=po.job_id,
        supplier_name=po.supplier_name,
        supplier_contact=po.supplier_contact,
        supplier_email=po.supplier_email,
        supplier_phone=po.supplier_phone,
        line_items=line_items_data,
        subtotal=subtotal,
        vat_rate=po.vat_rate,
        vat_amount=vat_amount,
        total=total,
        expected_delivery=po.expected_delivery,
        notes=po.notes,
        created_by=current_user['username'],
    )
    db.add(new_po)

    # Mark job as parts_on_order
    job_result2 = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == po.job_id)
    )
    job = job_result2.scalar_one_or_none()
    if job:
        job.parts_on_order = True
        job.parts_po_number = po_number

    await db.commit()
    await db.refresh(new_po)

    logger.info(f"PO created: {po_number} for {total} EUR by {current_user['username']}")
    return new_po


@router.get("/purchase-orders", response_model=list[PurchaseOrderRead])
async def list_purchase_orders(
    status_filter: Optional[str] = None,
    supplier: Optional[str] = None,
    job_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """List purchase orders with filters"""
    query = select(CamperPurchaseOrderModel)

    if status_filter:
        try:
            ps = CamperPOStatus(status_filter)
            query = query.where(CamperPurchaseOrderModel.status == ps)
        except ValueError:
            pass

    if supplier:
        query = query.where(CamperPurchaseOrderModel.supplier_name.ilike(f"%{supplier}%"))

    if job_id:
        query = query.where(CamperPurchaseOrderModel.job_id == job_id)

    query = query.order_by(CamperPurchaseOrderModel.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderRead)
async def get_purchase_order(
    po_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Get full PO details"""
    result = await db.execute(
        select(CamperPurchaseOrderModel).where(CamperPurchaseOrderModel.id == po_id)
    )
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po


@router.put("/purchase-orders/{po_id}", response_model=PurchaseOrderRead)
async def update_purchase_order(
    po_id: UUID,
    po_update: PurchaseOrderUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_manager_or_admin()),
):
    """Update purchase order"""
    result = await db.execute(
        select(CamperPurchaseOrderModel).where(CamperPurchaseOrderModel.id == po_id)
    )
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    update_data = po_update.model_dump(exclude_unset=True)

    if "line_items" in update_data and update_data["line_items"] is not None:
        line_items_data = [item.model_dump() if hasattr(item, 'model_dump') else item for item in update_data["line_items"]]
        for item in line_items_data:
            for key in ("unit_price", "line_total"):
                if key in item:
                    item[key] = float(item[key])
        po.line_items = line_items_data
        # Recalculate
        subtotal = sum(Decimal(str(item.get("line_total", 0))) for item in line_items_data)
        vat_rate = update_data.get("vat_rate", po.vat_rate)
        vat_amount = (subtotal * vat_rate / Decimal("100")).quantize(Decimal("0.01"))
        po.subtotal = subtotal
        po.vat_amount = vat_amount
        po.total = subtotal + vat_amount

    for field in ("supplier_name", "supplier_contact", "supplier_email", "supplier_phone",
                   "expected_delivery", "tracking_number", "notes", "vat_rate"):
        if field in update_data and update_data[field] is not None:
            setattr(po, field, update_data[field])

    po.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(po)

    logger.info(f"PO {po.po_number} updated by {current_user['username']}")
    return po


@router.patch("/purchase-orders/{po_id}/status", response_model=PurchaseOrderRead)
async def update_po_status(
    po_id: UUID,
    status_update: POStatusUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_manager_or_admin()),
):
    """Advance PO status. When RECEIVED, update job.parts_on_order = False"""
    result = await db.execute(
        select(CamperPurchaseOrderModel).where(CamperPurchaseOrderModel.id == po_id)
    )
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    old_status = po.status
    po.status = status_update.status
    po.updated_at = datetime.now(timezone.utc)

    if status_update.status == CamperPOStatus.RECEIVED:
        po.actual_delivery = date.today()
        # Only clear parts_on_order if ALL POs for this job are terminal (received/cancelled)
        terminal_statuses = (CamperPOStatus.RECEIVED, CamperPOStatus.CANCELLED)
        pending_pos = await db.execute(
            select(func.count()).where(
                CamperPurchaseOrderModel.job_id == po.job_id,
                CamperPurchaseOrderModel.id != po.id,
                ~CamperPurchaseOrderModel.status.in_(terminal_statuses),
            )
        )
        still_pending = pending_pos.scalar() or 0
        job_result = await db.execute(
            select(CamperServiceJobModel).where(CamperServiceJobModel.id == po.job_id)
        )
        job = job_result.scalar_one_or_none()
        if job:
            if still_pending == 0:
                job.parts_on_order = False
                logger.info(f"All POs for job {job.job_number} received -- parts_on_order cleared")
            else:
                logger.info(f"PO {po.po_number} received but {still_pending} other PO(s) still pending for job {job.job_number}")
            job.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(po)

    logger.info(f"PO {po.po_number}: {old_status.value} -> {status_update.status.value} by {current_user['username']}")
    return po


# ================================================================
# INVOICE ENDPOINTS
# ================================================================

@router.post("/invoices", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice: InvoiceCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_manager_or_admin()),
):
    """Generate invoice from completed job"""
    # Verify job exists
    job_result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == invoice.job_id)
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Service job not found")

    # Generate invoice number
    today = date.today().strftime("%Y%m%d")
    count_result = await db.execute(
        select(func.count()).where(
            CamperInvoiceModel.invoice_number.like(f"INV-{today}-%")
        )
    )
    count = count_result.scalar() or 0
    invoice_number = f"INV-{today}-{count + 1:04d}"

    # Serialize line items
    line_items_data = [item.model_dump() for item in invoice.line_items]
    for item in line_items_data:
        for key in ("unit_price", "line_total"):
            if key in item:
                item[key] = float(item[key])

    subtotal = sum(Decimal(str(item.line_total)) for item in invoice.line_items)
    vat_amount = (subtotal * invoice.vat_rate / Decimal("100")).quantize(Decimal("0.01"))
    total = subtotal + vat_amount
    amount_due = total - invoice.deposit_applied

    # Determine payment status based on deposit
    payment_status = PaymentStatus.PENDING
    if invoice.deposit_applied > Decimal("0"):
        payment_status = PaymentStatus.DEPOSIT_PAID

    new_invoice = CamperInvoiceModel(
        invoice_number=invoice_number,
        job_id=invoice.job_id,
        customer_id=invoice.customer_id,
        quotation_id=invoice.quotation_id,
        line_items=line_items_data,
        subtotal=subtotal,
        vat_rate=invoice.vat_rate,
        vat_amount=vat_amount,
        total=total,
        deposit_applied=invoice.deposit_applied,
        amount_due=amount_due,
        payment_status=payment_status,
        due_date=invoice.due_date,
        notes=invoice.notes,
        created_by=current_user['username'],
    )
    db.add(new_invoice)

    # Update job to INVOICED
    job.status = JobStatus.INVOICED
    job.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(new_invoice)

    logger.info(f"Invoice created: {invoice_number} total={total} due={amount_due} by {current_user['username']}")

    # Email customer with invoice
    try:
        customer_result = await db.execute(
            select(CamperCustomerModel).where(CamperCustomerModel.id == invoice.customer_id)
        )
        customer = customer_result.scalar_one_or_none()
        if customer and customer.email:
            send_invoice_email(
                to_email=customer.email,
                customer_name=customer.name,
                invoice_number=invoice_number,
                total=f"{total:.2f} EUR",
                amount_due=f"{amount_due:.2f} EUR",
            )
    except Exception as e:
        logger.warning(f"Failed to send invoice email: {e}")

    return new_invoice


@router.get("/invoices", response_model=list[InvoiceRead])
async def list_invoices(
    status_filter: Optional[str] = None,
    customer_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """List invoices with filters"""
    query = select(CamperInvoiceModel)

    if status_filter:
        try:
            ps = PaymentStatus(status_filter)
            query = query.where(CamperInvoiceModel.payment_status == ps)
        except ValueError:
            pass

    if customer_id:
        query = query.where(CamperInvoiceModel.customer_id == customer_id)

    query = query.order_by(CamperInvoiceModel.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/invoices/{invoice_id}", response_model=InvoiceRead)
async def get_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Get full invoice details"""
    result = await db.execute(
        select(CamperInvoiceModel).where(CamperInvoiceModel.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.post("/invoices/{invoice_id}/mark-paid", response_model=InvoiceRead)
async def mark_invoice_paid(
    invoice_id: UUID,
    payment: InvoicePayment,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_manager_or_admin()),
):
    """Record payment on invoice"""
    result = await db.execute(
        select(CamperInvoiceModel).where(CamperInvoiceModel.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice.payment_status = PaymentStatus.PAID
    invoice.payment_method = payment.payment_method
    invoice.paid_at = datetime.now(timezone.utc)
    invoice.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(invoice)

    logger.info(f"Invoice {invoice.invoice_number} PAID ({payment.payment_method}) by {current_user['username']}")
    return invoice


# ================================================================
# DOCUMENT ENDPOINTS
# ================================================================

@router.post("/documents/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    entity_type: str = Form(...),
    entity_id: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Upload file to MinIO and create tracking record"""
    from src.services.minio_service import minio_service

    # Build MinIO object key
    object_key = f"camper-documents/{entity_type}/{entity_id}/{file.filename}"

    # Upload to MinIO
    minio_key = await minio_service.upload_file_stream_async(file, object_key)
    if not minio_key:
        raise HTTPException(status_code=500, detail="File upload to MinIO failed")

    # Create DB record
    doc = CamperDocumentModel(
        entity_type=entity_type,
        entity_id=entity_id,
        file_name=file.filename,
        file_type=file.content_type or "application/octet-stream",
        file_size=file.size or 0,
        minio_object_key=minio_key,
        description=description,
        uploaded_by=current_user['username'],
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    logger.info(f"Document uploaded: {file.filename} for {entity_type}/{entity_id} by {current_user['username']}")
    return doc


@router.get("/documents", response_model=list[DocumentRead])
async def list_documents(
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """List documents for an entity"""
    query = select(CamperDocumentModel)

    if entity_type:
        query = query.where(CamperDocumentModel.entity_type == entity_type)
    if entity_id:
        query = query.where(CamperDocumentModel.entity_id == entity_id)

    query = query.order_by(CamperDocumentModel.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/documents/{doc_id}/download")
async def download_document(
    doc_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Stream file from MinIO"""
    from src.services.minio_service import minio_service

    result = await db.execute(
        select(CamperDocumentModel).where(CamperDocumentModel.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_data = minio_service.download_artifact(doc.minio_object_key)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found in storage")

    return StreamingResponse(
        io.BytesIO(file_data),
        media_type=doc.file_type,
        headers={"Content-Disposition": f'attachment; filename="{doc.file_name}"'}
    )


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_manager_or_admin()),
):
    """Remove document from MinIO and DB"""
    result = await db.execute(
        select(CamperDocumentModel).where(CamperDocumentModel.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await db.delete(doc)
    await db.commit()

    logger.info(f"Document deleted: {doc.file_name} by {current_user['username']}")


# ================================================================
# CALENDAR ENDPOINT
# ================================================================

@router.get("/calendar", response_model=list[CalendarEvent])
async def get_calendar(
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Jobs with scheduled_date in range as calendar events"""
    query = select(CamperServiceJobModel).where(
        CamperServiceJobModel.scheduled_date.isnot(None)
    )

    if start:
        try:
            start_date = date.fromisoformat(start)
            query = query.where(CamperServiceJobModel.scheduled_date >= start_date)
        except ValueError:
            pass

    if end:
        try:
            end_date = date.fromisoformat(end)
            query = query.where(CamperServiceJobModel.scheduled_date <= end_date)
        except ValueError:
            pass

    query = query.order_by(CamperServiceJobModel.scheduled_date)
    result = await db.execute(query)
    jobs = result.scalars().all()

    # Color-code by status
    status_colors = {
        JobStatus.QUOTED: "#9CA3AF",
        JobStatus.APPROVED: "#3B82F6",
        JobStatus.IN_PROGRESS: "#F59E0B",
        JobStatus.WAITING_PARTS: "#EF4444",
        JobStatus.INSPECTION: "#8B5CF6",
        JobStatus.COMPLETED: "#10B981",
        JobStatus.INVOICED: "#6366F1",
        JobStatus.CANCELLED: "#6B7280",
    }

    events = []
    for job in jobs:
        events.append(CalendarEvent(
            id=str(job.id),
            title=f"{job.job_number}: {job.title}",
            start=job.scheduled_date.isoformat(),
            color=status_colors.get(job.status, "#9CA3AF"),
            url=f"/camper/jobs/{job.id}",
            extendedProps={
                "status": job.status.value,
                "assigned_to": job.assigned_to or "",
                "job_number": job.job_number,
            }
        ))

    return events


# ================================================================
# DASHBOARD
# ================================================================

@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """One-screen overview for Nino"""
    # Vehicles in shop (checked_in or in_service or waiting_parts)
    in_shop_result = await db.execute(
        select(func.count()).where(
            CamperVehicleModel.status.in_([
                VehicleStatus.CHECKED_IN,
                VehicleStatus.IN_SERVICE,
                VehicleStatus.WAITING_PARTS,
                VehicleStatus.READY_FOR_PICKUP,
            ])
        )
    )
    vehicles_in_shop = in_shop_result.scalar() or 0

    # Jobs in progress
    in_progress_result = await db.execute(
        select(func.count()).where(CamperServiceJobModel.status == JobStatus.IN_PROGRESS)
    )
    jobs_in_progress = in_progress_result.scalar() or 0

    # Jobs waiting parts
    waiting_parts_result = await db.execute(
        select(func.count()).where(CamperServiceJobModel.status == JobStatus.WAITING_PARTS)
    )
    jobs_waiting_parts = waiting_parts_result.scalar() or 0

    # Completed today
    today_start = datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)
    today_end = datetime.combine(date.today(), datetime.max.time(), tzinfo=timezone.utc)
    completed_today_result = await db.execute(
        select(func.count()).where(
            and_(
                CamperServiceJobModel.status == JobStatus.COMPLETED,
                CamperServiceJobModel.completed_at >= today_start,
                CamperServiceJobModel.completed_at <= today_end,
            )
        )
    )
    jobs_completed_today = completed_today_result.scalar() or 0

    # Pending quotes
    pending_result = await db.execute(
        select(func.count()).where(CamperServiceJobModel.status == JobStatus.QUOTED)
    )
    pending_quotes = pending_result.scalar() or 0

    # Total jobs all-time
    total_result = await db.execute(select(func.count()).select_from(CamperServiceJobModel))
    total_jobs = total_result.scalar() or 0

    # Pending deposits (deposit_required > deposit_paid)
    deposits_result = await db.execute(
        select(func.sum(CamperServiceJobModel.deposit_required - CamperServiceJobModel.deposit_paid)).where(
            CamperServiceJobModel.deposit_required > CamperServiceJobModel.deposit_paid
        )
    )
    pending_deposits = deposits_result.scalar() or Decimal("0.00")

    # Total revenue this month (paid invoices)
    month_start = date.today().replace(day=1)
    revenue_result = await db.execute(
        select(func.sum(CamperInvoiceModel.total)).where(
            and_(
                CamperInvoiceModel.payment_status == PaymentStatus.PAID,
                CamperInvoiceModel.paid_at >= datetime.combine(month_start, datetime.min.time(), tzinfo=timezone.utc),
            )
        )
    )
    total_revenue_month = revenue_result.scalar() or Decimal("0.00")

    # Overdue invoices
    overdue_result = await db.execute(
        select(func.count()).where(
            and_(
                CamperInvoiceModel.payment_status.in_([PaymentStatus.PENDING, PaymentStatus.DEPOSIT_PAID, PaymentStatus.PARTIAL]),
                CamperInvoiceModel.due_date < date.today(),
            )
        )
    )
    overdue_invoices = overdue_result.scalar() or 0

    # Jobs in inspection
    inspection_result = await db.execute(
        select(func.count()).where(CamperServiceJobModel.status == JobStatus.INSPECTION)
    )
    jobs_in_inspection = inspection_result.scalar() or 0

    return DashboardSummary(
        vehicles_in_shop=vehicles_in_shop,
        jobs_in_progress=jobs_in_progress,
        jobs_waiting_parts=jobs_waiting_parts,
        jobs_completed_today=jobs_completed_today,
        pending_quotes=pending_quotes,
        total_jobs=total_jobs,
        pending_deposits=pending_deposits,
        total_revenue_month=total_revenue_month,
        overdue_invoices=overdue_invoices,
        jobs_in_inspection=jobs_in_inspection,
    )


# ================================================================
# HTML WEB UI ROUTES (Nino's Team Interface)
# ================================================================

@html_router.get("/camper", response_class=HTMLResponse, name="camper_login")
async def camper_login(request: Request):
    """Camper & Tour login page - entry point"""
    return templates.TemplateResponse("camper/login.html", {"request": request})


@html_router.get("/camper/callback")
async def camper_oauth_callback(request: Request, code: str = None, error: str = None):
    """
    OAuth2 Callback - Server-side token exchange.
    Same pattern as POS: browser -> Keycloak -> code -> server exchanges -> redirect with token.
    """
    import httpx
    from fastapi.responses import RedirectResponse

    if error:
        logger.error(f"Camper OAuth callback error: {error}")
        return RedirectResponse(url="/camper?error=" + error)

    if not code:
        logger.warning("Camper OAuth callback without code")
        return RedirectResponse(url="/camper?error=no_code")

    # Keycloak config -- internal Docker URL for server-to-server
    keycloak_internal_url = "http://keycloak:8080"
    realm = "kc-camper-service-realm-dev"
    client_id = "camper_service_web"

    # Reconstruct redirect_uri from forwarded headers (must match browser's original)
    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host", "helix.local")
    redirect_uri = f"{forwarded_proto}://{forwarded_host}/camper/callback"

    logger.info(f"Camper token exchange redirect_uri: {redirect_uri}")

    token_endpoint = f"{keycloak_internal_url}/realms/{realm}/protocol/openid-connect/token"

    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.post(
                token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "code": code,
                    "redirect_uri": redirect_uri
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code != 200:
                logger.error(f"Camper token exchange failed: {response.status_code} - {response.text}")
                return RedirectResponse(url="/camper?error=token_exchange_failed")

            tokens = response.json()
            access_token = tokens.get("access_token")

            if not access_token:
                logger.error("Camper: No access_token in response")
                return RedirectResponse(url="/camper?error=no_token")

            logger.info("Camper OAuth callback successful, redirecting to dashboard")
            return RedirectResponse(url=f"/camper/dashboard#token={access_token}")

    except Exception as e:
        logger.error(f"Camper token exchange exception: {e}")
        return RedirectResponse(url="/camper?error=token_exchange_error")


@html_router.get("/camper/dashboard", response_class=HTMLResponse, name="camper_dashboard")
async def camper_dashboard_page(request: Request):
    """Dashboard - Morning overview for Nino"""
    return templates.TemplateResponse("camper/dashboard.html", {"request": request})


@html_router.get("/camper/checkin", response_class=HTMLResponse, name="camper_checkin")
async def camper_checkin_page(request: Request):
    """Vehicle check-in - plate search + registration"""
    return templates.TemplateResponse("camper/checkin.html", {"request": request})


@html_router.get("/camper/jobs", response_class=HTMLResponse, name="camper_jobs")
async def camper_jobs_page(request: Request):
    """Job board - filterable list of all service jobs"""
    return templates.TemplateResponse("camper/jobs.html", {"request": request})


@html_router.get("/camper/jobs/new", response_class=HTMLResponse, name="camper_job_new")
async def camper_job_new_page(request: Request):
    """New job - create a quotation"""
    return templates.TemplateResponse("camper/job_detail.html", {"request": request})


@html_router.get("/camper/jobs/{job_id}", response_class=HTMLResponse, name="camper_job_detail")
async def camper_job_detail_page(request: Request, job_id: str):
    """Job detail - view, edit, advance status"""
    return templates.TemplateResponse("camper/job_detail.html", {"request": request})


@html_router.get("/camper/customers", response_class=HTMLResponse, name="camper_customers")
async def camper_customers_page(request: Request):
    """Customer lookup - search and manage profiles"""
    return templates.TemplateResponse("camper/customers.html", {"request": request})


@html_router.get("/camper/quotations", response_class=HTMLResponse, name="camper_quotations")
async def camper_quotations_page(request: Request):
    """Quotations list"""
    return templates.TemplateResponse("camper/quotations.html", {"request": request})


@html_router.get("/camper/quotations/{quotation_id}", response_class=HTMLResponse, name="camper_quotation_detail")
async def camper_quotation_detail_page(request: Request, quotation_id: str):
    """Quotation detail"""
    return templates.TemplateResponse("camper/quotation_detail.html", {"request": request})


@html_router.get("/camper/purchase-orders", response_class=HTMLResponse, name="camper_purchase_orders")
async def camper_purchase_orders_page(request: Request):
    """Purchase orders list"""
    return templates.TemplateResponse("camper/purchase_orders.html", {"request": request})


@html_router.get("/camper/invoices", response_class=HTMLResponse, name="camper_invoices")
async def camper_invoices_page(request: Request):
    """Invoices list"""
    return templates.TemplateResponse("camper/invoices.html", {"request": request})


@html_router.get("/camper/calendar", response_class=HTMLResponse, name="camper_calendar")
async def camper_calendar_page(request: Request):
    """Calendar view"""
    return templates.TemplateResponse("camper/calendar.html", {"request": request})
