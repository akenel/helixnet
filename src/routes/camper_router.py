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
from sqlalchemy import select, func, and_, DateTime as SADateTime
from sqlalchemy.orm import selectinload
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
from uuid import UUID
from typing import Optional
from pathlib import Path
import io

from src.db.database import get_db_session
from src.db.models.camper_vehicle_model import CamperVehicleModel, VehicleStatus
from src.db.models.camper_customer_model import CamperCustomerModel
from src.db.models.camper_bay_model import CamperBayModel
from src.db.models.camper_service_job_model import CamperServiceJobModel, JobStatus
from src.db.models.camper_work_log_model import CamperWorkLogModel, LogType
from src.db.models.camper_quotation_model import CamperQuotationModel, QuotationStatus
from src.db.models.camper_purchase_order_model import CamperPurchaseOrderModel, CamperPOStatus
from src.db.models.camper_invoice_model import CamperInvoiceModel, PaymentStatus
from src.db.models.camper_document_model import CamperDocumentModel
from src.db.models.camper_shared_resource_model import CamperSharedResourceModel, ResourceType
from src.db.models.camper_resource_booking_model import CamperResourceBookingModel, BookingStatus
from src.db.models.camper_appointment_model import CamperAppointmentModel, AppointmentType, AppointmentPriority, AppointmentStatus
from src.db.models.camper_supplier_model import CamperSupplierModel
from src.schemas.camper_schema import (
    VehicleCreate, VehicleUpdate, VehicleRead, VehicleStatusUpdate,
    CamperCustomerCreate, CamperCustomerUpdate, CamperCustomerRead,
    BayCreate, BayUpdate, BayResponse,
    ServiceJobCreate, ServiceJobUpdate, ServiceJobRead, ServiceJobStatusUpdate,
    WorkLogCreate, WorkLogResponse, WaitStart, WaitEnd,
    QuotationCreate, QuotationUpdate, QuotationRead,
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderRead, POStatusUpdate,
    InvoiceCreate, InvoiceRead, InvoicePayment,
    DocumentRead, CalendarEvent,
    InspectionResult, DepositPayment,
    BayTimelineEntry, BayTimelineResponse,
    DashboardSummary,
    SharedResourceCreate, SharedResourceUpdate, SharedResourceResponse,
    ResourceBookingCreate, ResourceBookingStatusUpdate, ResourceBookingResponse,
    AppointmentCreate, AppointmentUpdate, AppointmentRead, AppointmentStatusUpdate,
    VehicleCheckIn, VehicleCheckOut,
    ServiceHistoryEntry, ServiceHistoryResponse, WarrantySet,
    ServiceReminder, RemindersResponse,
    TechnicianHours, TechnicianSummaryResponse,
    CamperSupplierCreate, CamperSupplierUpdate, CamperSupplierRead,
    CustomerVehicleSummary, CustomerVehicleListResponse, JobCostSummary,
    JobStatusCount, JobStatusCountsResponse,
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


async def _enrich_job_response(job: CamperServiceJobModel, db: AsyncSession) -> ServiceJobRead:
    """Build ServiceJobRead with computed fields (bay_name, total_logged_hours)"""
    bay_name = None
    if job.bay_id:
        bay_result = await db.execute(
            select(CamperBayModel.name).where(CamperBayModel.id == job.bay_id)
        )
        bay_name = bay_result.scalar_one_or_none()

    total_hours_result = await db.execute(
        select(func.coalesce(func.sum(CamperWorkLogModel.hours), 0)).where(
            and_(
                CamperWorkLogModel.job_id == job.id,
                CamperWorkLogModel.log_type == LogType.WORK,
            )
        )
    )
    total_logged_hours = float(total_hours_result.scalar() or 0)

    # Build from ORM attributes + computed fields
    data = {c.key: getattr(job, c.key) for c in job.__table__.columns}
    data["bay_name"] = bay_name
    data["total_logged_hours"] = total_logged_hours
    return ServiceJobRead.model_validate(data)


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


@router.get("/vehicles/{vehicle_id}/service-history", response_model=ServiceHistoryResponse)
async def get_vehicle_service_history(
    vehicle_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Full service history for a vehicle -- 'brakes done at 200,000km last year'"""
    vehicle_result = await db.execute(
        select(CamperVehicleModel).where(CamperVehicleModel.id == vehicle_id)
    )
    vehicle = vehicle_result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    jobs_result = await db.execute(
        select(CamperServiceJobModel)
        .where(CamperServiceJobModel.vehicle_id == vehicle_id)
        .order_by(CamperServiceJobModel.created_at.desc())
    )
    jobs = jobs_result.scalars().all()

    total_spend = sum(j.actual_total for j in jobs)
    entries = []
    for j in jobs:
        # Get customer name
        cust_result = await db.execute(
            select(CamperCustomerModel.name).where(CamperCustomerModel.id == j.customer_id)
        )
        cust_name = cust_result.scalar_one_or_none() or "Unknown"

        entries.append(ServiceHistoryEntry(
            job_id=j.id,
            job_number=j.job_number,
            title=j.title,
            job_type=j.job_type,
            status=j.status,
            assigned_to=j.assigned_to,
            scheduled_date=j.scheduled_date,
            started_at=j.started_at,
            completed_at=j.completed_at,
            mileage_in=j.mileage_in,
            mileage_out=j.mileage_out,
            actual_total=j.actual_total,
            currency=j.currency,
            warranty_months=j.warranty_months,
            warranty_expires_at=j.warranty_expires_at,
            work_performed=j.work_performed,
            parts_used=j.parts_used,
            vehicle_plate=vehicle.registration_plate,
            customer_name=cust_name,
        ))

    return ServiceHistoryResponse(
        entity_type="vehicle",
        entity_id=vehicle_id,
        entity_name=vehicle.registration_plate,
        total_jobs=len(entries),
        total_spend=total_spend,
        jobs=entries,
    )


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


@router.get("/customers/{customer_id}/service-history", response_model=ServiceHistoryResponse)
async def get_customer_service_history(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Full service history for a customer -- all their visits, all vehicles"""
    customer_result = await db.execute(
        select(CamperCustomerModel).where(CamperCustomerModel.id == customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    jobs_result = await db.execute(
        select(CamperServiceJobModel)
        .where(CamperServiceJobModel.customer_id == customer_id)
        .order_by(CamperServiceJobModel.created_at.desc())
    )
    jobs = jobs_result.scalars().all()

    total_spend = sum(j.actual_total for j in jobs)
    entries = []
    for j in jobs:
        # Get vehicle plate
        v_result = await db.execute(
            select(CamperVehicleModel.registration_plate)
            .where(CamperVehicleModel.id == j.vehicle_id)
        )
        plate = v_result.scalar_one_or_none() or "Unknown"

        entries.append(ServiceHistoryEntry(
            job_id=j.id,
            job_number=j.job_number,
            title=j.title,
            job_type=j.job_type,
            status=j.status,
            assigned_to=j.assigned_to,
            scheduled_date=j.scheduled_date,
            started_at=j.started_at,
            completed_at=j.completed_at,
            mileage_in=j.mileage_in,
            mileage_out=j.mileage_out,
            actual_total=j.actual_total,
            currency=j.currency,
            warranty_months=j.warranty_months,
            warranty_expires_at=j.warranty_expires_at,
            work_performed=j.work_performed,
            parts_used=j.parts_used,
            vehicle_plate=plate,
            customer_name=customer.name,
        ))

    return ServiceHistoryResponse(
        entity_type="customer",
        entity_id=customer_id,
        entity_name=customer.name,
        total_jobs=len(entries),
        total_spend=total_spend,
        jobs=entries,
    )


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
    return await _enrich_job_response(new_job, db)


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
    jobs = result.scalars().all()
    return [await _enrich_job_response(j, db) for j in jobs]


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
    return await _enrich_job_response(job, db)


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
        # Strip timezone info for comparison (DB may store naive, client sends aware)
        db_ts = job.updated_at.replace(tzinfo=None) if job.updated_at.tzinfo else job.updated_at
        exp_ts = expected.replace(tzinfo=None) if expected.tzinfo else expected
        if db_ts != exp_ts:
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
    return await _enrich_job_response(job, db)


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
    return await _enrich_job_response(job, db)


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
    return await _enrich_job_response(job, db)


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
    return await _enrich_job_response(job, db)


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
    return await _enrich_job_response(job, db)


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

    return await _enrich_job_response(job, db)


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
    return await _enrich_job_response(job, db)


# ================================================================
# CHECK-IN / CHECK-OUT WORKFLOW
# ================================================================

@router.post("/jobs/{job_id}/check-in", response_model=ServiceJobRead)
async def check_in_vehicle(
    job_id: UUID,
    check_in: VehicleCheckIn,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Record vehicle check-in: mileage, pre-existing damage, set vehicle status."""
    result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.checked_in_at is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Vehicle already checked in at {job.checked_in_at.isoformat()}"
        )

    now = datetime.now(timezone.utc)
    job.checked_in_at = now
    job.checked_in_by = current_user["username"]

    if check_in.mileage_in is not None:
        job.mileage_in = check_in.mileage_in
    if check_in.condition_notes_in is not None:
        job.condition_notes_in = check_in.condition_notes_in

    # Set vehicle status to CHECKED_IN
    vehicle_result = await db.execute(
        select(CamperVehicleModel).where(CamperVehicleModel.id == job.vehicle_id)
    )
    vehicle = vehicle_result.scalar_one_or_none()
    if vehicle:
        vehicle.status = VehicleStatus.CHECKED_IN

    job.updated_at = now
    await db.commit()
    await db.refresh(job)

    logger.info(
        f"Job {job.job_number} CHECK-IN by {current_user['username']}"
        f" | mileage={job.mileage_in} km"
    )
    return await _enrich_job_response(job, db)


@router.post("/jobs/{job_id}/check-out", response_model=ServiceJobRead)
async def check_out_vehicle(
    job_id: UUID,
    check_out: VehicleCheckOut,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Record vehicle check-out: mileage out, condition notes, set picked_up_at."""
    result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.checked_in_at is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot check out -- vehicle was never checked in"
        )

    if job.picked_up_at is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Vehicle already checked out at {job.picked_up_at.isoformat()}"
        )

    now = datetime.now(timezone.utc)

    if check_out.mileage_out is not None:
        # Validate mileage_out >= mileage_in (if mileage_in was recorded)
        if job.mileage_in is not None and check_out.mileage_out < job.mileage_in:
            raise HTTPException(
                status_code=422,
                detail=f"Mileage out ({check_out.mileage_out}) cannot be less than mileage in ({job.mileage_in})"
            )
        job.mileage_out = check_out.mileage_out

    if check_out.condition_notes_out is not None:
        job.condition_notes_out = check_out.condition_notes_out

    job.picked_up_at = now

    # Set vehicle status to PICKED_UP
    vehicle_result = await db.execute(
        select(CamperVehicleModel).where(CamperVehicleModel.id == job.vehicle_id)
    )
    vehicle = vehicle_result.scalar_one_or_none()
    if vehicle:
        vehicle.status = VehicleStatus.PICKED_UP

    job.updated_at = now
    await db.commit()
    await db.refresh(job)

    logger.info(
        f"Job {job.job_number} CHECK-OUT by {current_user['username']}"
        f" | mileage_in={job.mileage_in} -> mileage_out={job.mileage_out}"
    )
    return await _enrich_job_response(job, db)


# ================================================================
# WARRANTY TRACKING
# ================================================================

@router.post("/jobs/{job_id}/set-warranty", response_model=ServiceJobRead)
async def set_warranty(
    job_id: UUID,
    warranty: WarrantySet,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_manager_or_admin()),
):
    """Set warranty terms on a completed job. Auto-calculates expiry date."""
    result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status not in (JobStatus.COMPLETED, JobStatus.INVOICED):
        raise HTTPException(
            status_code=400,
            detail=f"Can only set warranty on COMPLETED or INVOICED jobs. Current: {job.status.value}"
        )

    job.warranty_months = warranty.warranty_months
    if warranty.warranty_terms is not None:
        job.warranty_terms = warranty.warranty_terms

    # Auto-calculate expiry: completed_at + warranty_months (or today if no completed_at)
    from dateutil.relativedelta import relativedelta
    base_date = job.completed_at.date() if job.completed_at else date.today()
    job.warranty_expires_at = base_date + relativedelta(months=warranty.warranty_months)

    job.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(job)

    logger.info(
        f"Job {job.job_number} WARRANTY set: {warranty.warranty_months} months, "
        f"expires {job.warranty_expires_at} by {current_user['username']}"
    )
    return await _enrich_job_response(job, db)


# ================================================================
# SERVICE REMINDERS
# ================================================================

@router.get("/reminders", response_model=RemindersResponse)
async def get_service_reminders(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Get all pending follow-ups and upcoming service reminders for Nino's morning view."""
    today = date.today()
    in_7_days = today + timedelta(days=7)
    in_30_days = today + timedelta(days=30)

    # Jobs with follow_up_required=True and next_service_date set
    result = await db.execute(
        select(CamperServiceJobModel)
        .where(
            and_(
                CamperServiceJobModel.follow_up_required == True,
                CamperServiceJobModel.next_service_date.isnot(None),
            )
        )
        .order_by(CamperServiceJobModel.next_service_date)
    )
    jobs = result.scalars().all()

    overdue = []
    upcoming_7 = []
    upcoming_30 = []

    for job in jobs:
        # Get customer + vehicle info
        cust_result = await db.execute(
            select(CamperCustomerModel).where(CamperCustomerModel.id == job.customer_id)
        )
        customer = cust_result.scalar_one_or_none()
        v_result = await db.execute(
            select(CamperVehicleModel.registration_plate)
            .where(CamperVehicleModel.id == job.vehicle_id)
        )
        plate = v_result.scalar_one_or_none() or "Unknown"

        days_until = (job.next_service_date - today).days
        reminder = ServiceReminder(
            job_id=job.id,
            job_number=job.job_number,
            title=job.title,
            customer_id=job.customer_id,
            customer_name=customer.name if customer else "Unknown",
            customer_phone=customer.phone if customer else None,
            vehicle_id=job.vehicle_id,
            vehicle_plate=plate,
            next_service_date=job.next_service_date,
            follow_up_notes=job.follow_up_notes,
            warranty_expires_at=job.warranty_expires_at,
            days_until_due=days_until,
            is_overdue=days_until < 0,
        )

        if days_until < 0:
            overdue.append(reminder)
        elif job.next_service_date <= in_7_days:
            upcoming_7.append(reminder)
        elif job.next_service_date <= in_30_days:
            upcoming_30.append(reminder)

    total = len(overdue) + len(upcoming_7) + len(upcoming_30)
    return RemindersResponse(
        overdue=overdue,
        upcoming_7_days=upcoming_7,
        upcoming_30_days=upcoming_30,
        total=total,
    )


# ================================================================
# TECHNICIAN SUMMARY
# ================================================================

@router.get("/jobs/{job_id}/technician-summary", response_model=TechnicianSummaryResponse)
async def get_technician_summary(
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Per-technician hour breakdown from work logs -- who did what."""
    job_result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get all WORK-type logs for this job
    logs_result = await db.execute(
        select(CamperWorkLogModel)
        .where(
            and_(
                CamperWorkLogModel.job_id == job_id,
                CamperWorkLogModel.log_type == LogType.WORK,
            )
        )
        .order_by(CamperWorkLogModel.logged_at)
    )
    logs = logs_result.scalars().all()

    # Group by technician
    tech_map: dict[str, dict] = {}
    for log in logs:
        tech = log.logged_by
        if tech not in tech_map:
            tech_map[tech] = {"hours": 0.0, "count": 0, "latest": None}
        tech_map[tech]["hours"] += log.hours or 0
        tech_map[tech]["count"] += 1
        tech_map[tech]["latest"] = log.logged_at

    technicians = [
        TechnicianHours(
            technician=tech,
            total_hours=round(data["hours"], 2),
            log_count=data["count"],
            latest_entry=data["latest"],
        )
        for tech, data in sorted(tech_map.items(), key=lambda x: x[1]["hours"], reverse=True)
    ]

    return TechnicianSummaryResponse(
        job_id=job.id,
        job_number=job.job_number,
        total_hours=round(sum(t.total_hours for t in technicians), 2),
        technicians=technicians,
    )


# ================================================================
# CUSTOMER VEHICLE LIST
# ================================================================

@router.get("/customers/{customer_id}/vehicles", response_model=CustomerVehicleListResponse)
async def list_customer_vehicles(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """All vehicles linked to a customer through their jobs -- 'What does Marco drive?'"""
    customer_result = await db.execute(
        select(CamperCustomerModel).where(CamperCustomerModel.id == customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Get distinct vehicle IDs from this customer's jobs
    jobs_result = await db.execute(
        select(
            CamperServiceJobModel.vehicle_id,
            func.count(CamperServiceJobModel.id).label("job_count"),
            func.max(CamperServiceJobModel.created_at).label("last_service"),
        ).where(
            CamperServiceJobModel.customer_id == customer_id
        ).group_by(CamperServiceJobModel.vehicle_id)
    )
    vehicle_rows = jobs_result.all()

    vehicles = []
    for row in vehicle_rows:
        v_result = await db.execute(
            select(CamperVehicleModel).where(CamperVehicleModel.id == row.vehicle_id)
        )
        vehicle = v_result.scalar_one_or_none()
        if vehicle:
            vehicles.append(CustomerVehicleSummary(
                vehicle_id=vehicle.id,
                registration_plate=vehicle.registration_plate,
                make=vehicle.make,
                model=vehicle.model,
                vehicle_type=vehicle.vehicle_type.value if vehicle.vehicle_type else None,
                status=vehicle.status.value if vehicle.status else None,
                total_jobs=row.job_count,
                last_service=row.last_service,
            ))

    return CustomerVehicleListResponse(
        customer_id=customer.id,
        customer_name=customer.name,
        total_vehicles=len(vehicles),
        vehicles=vehicles,
    )


# ================================================================
# JOB COST SUMMARY
# ================================================================

@router.get("/jobs/{job_id}/cost-summary", response_model=JobCostSummary)
async def get_job_cost_summary(
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Financial breakdown: labor + parts + totals. What's this job costing us?"""
    job_result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Service job not found")

    labor_rate = Decimal("35.00")
    estimated_labor = labor_rate * Decimal(str(job.estimated_hours or 0))
    actual_labor = labor_rate * Decimal(str(job.actual_hours or 0))

    # Sum all PO totals for parts cost
    parts_result = await db.execute(
        select(func.sum(CamperPurchaseOrderModel.total)).where(
            and_(
                CamperPurchaseOrderModel.job_id == job_id,
                ~CamperPurchaseOrderModel.status.in_([CamperPOStatus.CANCELLED]),
            )
        )
    )
    parts_cost = parts_result.scalar() or Decimal("0.00")

    # Quotation total (if any)
    quote_result = await db.execute(
        select(CamperQuotationModel.total).where(
            CamperQuotationModel.job_id == job_id
        ).order_by(CamperQuotationModel.created_at.desc()).limit(1)
    )
    quotation_total = quote_result.scalar()

    # Invoice total (if any)
    invoice_result = await db.execute(
        select(CamperInvoiceModel.total).where(
            CamperInvoiceModel.job_id == job_id
        ).order_by(CamperInvoiceModel.created_at.desc()).limit(1)
    )
    invoice_total = invoice_result.scalar()

    return JobCostSummary(
        job_id=job.id,
        job_number=job.job_number,
        estimated_hours=job.estimated_hours or 0,
        actual_hours=job.actual_hours or 0,
        labor_rate_per_hour=labor_rate,
        estimated_labor_cost=estimated_labor,
        actual_labor_cost=actual_labor,
        parts_cost=parts_cost,
        estimated_total=estimated_labor + Decimal(str(job.estimated_parts_cost or 0)),
        actual_total=actual_labor + parts_cost,
        quotation_total=quotation_total,
        invoice_total=invoice_total,
        deposit_paid=job.deposit_paid or Decimal("0.00"),
    )


# ================================================================
# VEHICLE CURRENT JOB
# ================================================================

@router.get("/vehicles/{vehicle_id}/current-job", response_model=ServiceJobRead)
async def get_vehicle_current_job(
    vehicle_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """What's happening with this van right now? Returns the active job, or 404."""
    # Verify vehicle exists
    v_result = await db.execute(
        select(CamperVehicleModel).where(CamperVehicleModel.id == vehicle_id)
    )
    if not v_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Active = not cancelled, not invoiced, not completed (or completed but not invoiced)
    active_statuses = [
        JobStatus.QUOTED, JobStatus.APPROVED, JobStatus.IN_PROGRESS,
        JobStatus.WAITING_PARTS, JobStatus.INSPECTION,
    ]
    result = await db.execute(
        select(CamperServiceJobModel).where(
            and_(
                CamperServiceJobModel.vehicle_id == vehicle_id,
                CamperServiceJobModel.status.in_(active_statuses),
            )
        ).order_by(CamperServiceJobModel.created_at.desc()).limit(1)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="No active job for this vehicle")

    return await _enrich_job_response(job, db)


# ================================================================
# JOB STATUS COUNTS (Quick Status Board)
# ================================================================

@router.get("/stats/jobs-by-status", response_model=JobStatusCountsResponse)
async def get_jobs_by_status(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Job count per status -- the quick status board widget."""
    result = await db.execute(
        select(
            CamperServiceJobModel.status,
            func.count(CamperServiceJobModel.id),
        ).group_by(CamperServiceJobModel.status)
    )
    rows = result.all()

    by_status = [
        JobStatusCount(status=row[0].value, count=row[1])
        for row in rows
    ]
    total = sum(item.count for item in by_status)

    return JobStatusCountsResponse(total=total, by_status=by_status)


# ================================================================
# SUPPLIER DIRECTORY
# ================================================================

@router.post("/suppliers", response_model=CamperSupplierRead, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier: CamperSupplierCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_manager_or_admin()),
):
    """Add supplier to directory (manager/admin only)"""
    new_supplier = CamperSupplierModel(**supplier.model_dump())
    db.add(new_supplier)
    await db.commit()
    await db.refresh(new_supplier)
    logger.info(f"Supplier created: {new_supplier.name} by {current_user['username']}")
    return new_supplier


@router.get("/suppliers", response_model=list[CamperSupplierRead])
async def list_suppliers(
    specialty: Optional[str] = None,
    preferred_only: bool = False,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """List suppliers with optional filters"""
    query = select(CamperSupplierModel).where(CamperSupplierModel.is_active == True)
    if specialty:
        query = query.where(CamperSupplierModel.specialty.ilike(f"%{specialty}%"))
    if preferred_only:
        query = query.where(CamperSupplierModel.is_preferred == True)
    query = query.order_by(CamperSupplierModel.is_preferred.desc(), CamperSupplierModel.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/suppliers/{supplier_id}", response_model=CamperSupplierRead)
async def get_supplier(
    supplier_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Get supplier by ID"""
    result = await db.execute(
        select(CamperSupplierModel).where(CamperSupplierModel.id == supplier_id)
    )
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.put("/suppliers/{supplier_id}", response_model=CamperSupplierRead)
async def update_supplier(
    supplier_id: UUID,
    supplier_update: CamperSupplierUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_manager_or_admin()),
):
    """Update supplier info (manager/admin only)"""
    result = await db.execute(
        select(CamperSupplierModel).where(CamperSupplierModel.id == supplier_id)
    )
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    update_data = supplier_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)

    supplier.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(supplier)
    logger.info(f"Supplier updated: {supplier.name} by {current_user['username']}")
    return supplier


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

    if deposit.amount <= 0:
        raise HTTPException(status_code=422, detail="L'importo del deposito deve essere positivo")

    new_total = (job.deposit_paid or Decimal("0")) + deposit.amount
    if job.deposit_required and job.deposit_required > 0 and new_total > job.deposit_required:
        remaining = job.deposit_required - (job.deposit_paid or Decimal("0"))
        raise HTTPException(
            status_code=422,
            detail=f"Deposito eccessivo: richiesto {job.deposit_required:.2f} EUR, "
                   f"già versato {job.deposit_paid:.2f} EUR, "
                   f"massimo accettabile {remaining:.2f} EUR"
        )

    job.deposit_paid = new_total
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

    return await _enrich_job_response(job, db)


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

    # Cap deposit_applied to total (never go negative)
    deposit_applied = min(invoice.deposit_applied, total)
    amount_due = total - deposit_applied

    # Determine payment status based on deposit
    if amount_due <= Decimal("0"):
        payment_status = PaymentStatus.PAID
    elif deposit_applied > Decimal("0"):
        payment_status = PaymentStatus.DEPOSIT_PAID
    else:
        payment_status = PaymentStatus.PENDING

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
        deposit_applied=deposit_applied,
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
# BAY MANAGEMENT ENDPOINTS (manager+ only)
# ================================================================

@router.get("/bays", response_model=list[BayResponse])
async def list_bays(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """List all service bays, ordered by display_order"""
    result = await db.execute(
        select(CamperBayModel).order_by(CamperBayModel.display_order, CamperBayModel.name)
    )
    bays = result.scalars().all()

    responses = []
    for bay in bays:
        # Count active jobs in this bay
        job_count_result = await db.execute(
            select(func.count()).where(
                and_(
                    CamperServiceJobModel.bay_id == bay.id,
                    CamperServiceJobModel.status.in_([
                        JobStatus.APPROVED, JobStatus.IN_PROGRESS,
                        JobStatus.WAITING_PARTS, JobStatus.INSPECTION,
                    ])
                )
            )
        )
        current_jobs = job_count_result.scalar() or 0

        responses.append(BayResponse(
            id=bay.id,
            name=bay.name,
            bay_type=bay.bay_type,
            description=bay.description,
            is_active=bay.is_active,
            display_order=bay.display_order,
            current_jobs=current_jobs,
            created_at=bay.created_at,
            updated_at=bay.updated_at,
        ))

    return responses


@router.post("/bays", response_model=BayResponse, status_code=status.HTTP_201_CREATED)
async def create_bay(
    bay_data: BayCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_manager_or_admin()),
):
    """Create a new service bay"""
    bay = CamperBayModel(
        name=bay_data.name,
        bay_type=bay_data.bay_type,
        description=bay_data.description,
        display_order=bay_data.display_order,
    )
    db.add(bay)
    await db.commit()
    await db.refresh(bay)

    logger.info(f"Bay created: '{bay.name}' by {current_user['username']}")

    return BayResponse(
        id=bay.id,
        name=bay.name,
        bay_type=bay.bay_type,
        description=bay.description,
        is_active=bay.is_active,
        display_order=bay.display_order,
        current_jobs=0,
        created_at=bay.created_at,
        updated_at=bay.updated_at,
    )


@router.patch("/bays/{bay_id}", response_model=BayResponse)
async def update_bay(
    bay_id: UUID,
    bay_data: BayUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_manager_or_admin()),
):
    """Update a service bay"""
    result = await db.execute(
        select(CamperBayModel).where(CamperBayModel.id == bay_id)
    )
    bay = result.scalar_one_or_none()
    if not bay:
        raise HTTPException(status_code=404, detail="Bay non trovato")

    update_data = bay_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bay, field, value)

    await db.commit()
    await db.refresh(bay)

    # Count active jobs
    job_count_result = await db.execute(
        select(func.count()).where(
            and_(
                CamperServiceJobModel.bay_id == bay.id,
                CamperServiceJobModel.status.in_([
                    JobStatus.APPROVED, JobStatus.IN_PROGRESS,
                    JobStatus.WAITING_PARTS, JobStatus.INSPECTION,
                ])
            )
        )
    )
    current_jobs = job_count_result.scalar() or 0

    logger.info(f"Bay updated: '{bay.name}' by {current_user['username']}")

    return BayResponse(
        id=bay.id,
        name=bay.name,
        bay_type=bay.bay_type,
        description=bay.description,
        is_active=bay.is_active,
        display_order=bay.display_order,
        current_jobs=current_jobs,
        created_at=bay.created_at,
        updated_at=bay.updated_at,
    )


@router.delete("/bays/{bay_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_bay(
    bay_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_manager_or_admin()),
):
    """Deactivate a service bay (soft delete -- jobs may reference it)"""
    result = await db.execute(
        select(CamperBayModel).where(CamperBayModel.id == bay_id)
    )
    bay = result.scalar_one_or_none()
    if not bay:
        raise HTTPException(status_code=404, detail="Bay non trovato")

    bay.is_active = False
    await db.commit()

    logger.info(f"Bay deactivated: '{bay.name}' by {current_user['username']}")


# ================================================================
# WORK LOG ENDPOINTS (mechanic+ only)
# ================================================================

@router.post("/jobs/{job_id}/work-log", response_model=WorkLogResponse, status_code=status.HTTP_201_CREATED)
async def log_work(
    job_id: UUID,
    log_data: WorkLogCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_mechanic_or_above()),
):
    """Log a work session on a job. Hours + what was done."""
    # Verify job exists
    job_result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Lavoro non trovato")

    if log_data.hours is None or log_data.hours <= 0:
        raise HTTPException(status_code=400, detail="Le ore sono obbligatorie per le registrazioni di lavoro")

    # Validate bay_id if provided
    if log_data.bay_id:
        bay_result = await db.execute(
            select(CamperBayModel).where(CamperBayModel.id == log_data.bay_id)
        )
        if not bay_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Bay non trovato")

    work_log = CamperWorkLogModel(
        job_id=job_id,
        bay_id=log_data.bay_id,
        log_type=LogType.WORK,
        hours=log_data.hours,
        notes=log_data.notes,
        logged_by=current_user["username"],
    )
    db.add(work_log)
    await db.flush()  # Ensure work_log is in DB before SUM query

    # Auto-update actual_hours on the job (sum of all WORK logs incl. new one)
    total_hours_result = await db.execute(
        select(func.sum(CamperWorkLogModel.hours)).where(
            and_(
                CamperWorkLogModel.job_id == job_id,
                CamperWorkLogModel.log_type == LogType.WORK,
            )
        )
    )
    job.actual_hours = total_hours_result.scalar() or 0

    await db.commit()
    await db.refresh(work_log)

    logger.info(f"Work logged: {log_data.hours}h on {job.job_number} by {current_user['username']}")

    return WorkLogResponse(
        id=work_log.id,
        job_id=work_log.job_id,
        bay_id=work_log.bay_id,
        log_type=work_log.log_type,
        hours=work_log.hours,
        notes=work_log.notes,
        wait_reason=work_log.wait_reason,
        logged_by=work_log.logged_by,
        logged_at=work_log.logged_at,
        created_at=work_log.created_at,
    )


@router.get("/jobs/{job_id}/work-log", response_model=list[WorkLogResponse])
async def get_work_logs(
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Get all work log entries for a job, chronological"""
    # Verify job exists
    job_result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lavoro non trovato")

    result = await db.execute(
        select(CamperWorkLogModel)
        .where(CamperWorkLogModel.job_id == job_id)
        .order_by(CamperWorkLogModel.logged_at)
    )
    logs = result.scalars().all()

    return [
        WorkLogResponse(
            id=log.id,
            job_id=log.job_id,
            bay_id=log.bay_id,
            log_type=log.log_type,
            hours=log.hours,
            notes=log.notes,
            wait_reason=log.wait_reason,
            logged_by=log.logged_by,
            logged_at=log.logged_at,
            created_at=log.created_at,
        )
        for log in logs
    ]


# ================================================================
# WAIT TRACKING ENDPOINTS (mechanic+ only)
# ================================================================

@router.post("/jobs/{job_id}/wait", response_model=WorkLogResponse, status_code=status.HTTP_201_CREATED)
async def start_wait(
    job_id: UUID,
    wait_data: WaitStart,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_mechanic_or_above()),
):
    """Mark a job as waiting. Creates WAIT_START log entry."""
    job_result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Lavoro non trovato")

    if job.current_wait_reason:
        raise HTTPException(status_code=400, detail="Il lavoro e gia in attesa")

    # Create WAIT_START log entry
    work_log = CamperWorkLogModel(
        job_id=job_id,
        bay_id=job.bay_id,
        log_type=LogType.WAIT_START,
        notes=wait_data.notes or f"In attesa: {wait_data.reason}",
        wait_reason=wait_data.reason,
        logged_by=current_user["username"],
    )
    db.add(work_log)

    # Set wait fields on job
    job.current_wait_reason = wait_data.reason
    job.current_wait_until = wait_data.estimated_resume

    await db.commit()
    await db.refresh(work_log)

    logger.info(f"Wait started on {job.job_number}: '{wait_data.reason}' by {current_user['username']}")

    return WorkLogResponse(
        id=work_log.id,
        job_id=work_log.job_id,
        bay_id=work_log.bay_id,
        log_type=work_log.log_type,
        hours=work_log.hours,
        notes=work_log.notes,
        wait_reason=work_log.wait_reason,
        logged_by=work_log.logged_by,
        logged_at=work_log.logged_at,
        created_at=work_log.created_at,
    )


@router.post("/jobs/{job_id}/resume", response_model=WorkLogResponse, status_code=status.HTTP_201_CREATED)
async def end_wait(
    job_id: UUID,
    resume_data: WaitEnd,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_mechanic_or_above()),
):
    """Resume work on a waiting job. Creates WAIT_END log entry."""
    job_result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Lavoro non trovato")

    if not job.current_wait_reason:
        raise HTTPException(status_code=400, detail="Il lavoro non e in attesa")

    # Create WAIT_END log entry
    work_log = CamperWorkLogModel(
        job_id=job_id,
        bay_id=job.bay_id,
        log_type=LogType.WAIT_END,
        notes=resume_data.notes,
        logged_by=current_user["username"],
    )
    db.add(work_log)

    # Clear wait fields on job
    job.current_wait_reason = None
    job.current_wait_until = None

    await db.commit()
    await db.refresh(work_log)

    logger.info(f"Wait ended on {job.job_number} by {current_user['username']}")

    return WorkLogResponse(
        id=work_log.id,
        job_id=work_log.job_id,
        bay_id=work_log.bay_id,
        log_type=work_log.log_type,
        hours=work_log.hours,
        notes=work_log.notes,
        wait_reason=work_log.wait_reason,
        logged_by=work_log.logged_by,
        logged_at=work_log.logged_at,
        created_at=work_log.created_at,
    )


# ================================================================
# BAY TIMELINE ENDPOINT
# ================================================================

@router.get("/bay-timeline", response_model=list[BayTimelineResponse])
async def get_bay_timeline(
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Bay timeline: all active bays with their job entries for the date range"""
    # Parse dates (default to current week)
    today = date.today()
    try:
        start_date = date.fromisoformat(start) if start else today - timedelta(days=today.weekday())
    except ValueError:
        start_date = today - timedelta(days=today.weekday())

    try:
        end_date = date.fromisoformat(end) if end else start_date + timedelta(days=6)
    except ValueError:
        end_date = start_date + timedelta(days=6)

    # Get all active bays
    bays_result = await db.execute(
        select(CamperBayModel)
        .where(CamperBayModel.is_active == True)
        .order_by(CamperBayModel.display_order, CamperBayModel.name)
    )
    bays = bays_result.scalars().all()

    # Status colors
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

    timeline = []
    for bay in bays:
        # Find jobs assigned to this bay that overlap with the date range
        # A job overlaps if: job.start_date <= end_date AND job.end_date >= start_date
        # Fall back to scheduled_date for single-day jobs
        jobs_result = await db.execute(
            select(CamperServiceJobModel).where(
                and_(
                    CamperServiceJobModel.bay_id == bay.id,
                    CamperServiceJobModel.status.notin_([JobStatus.CANCELLED, JobStatus.INVOICED]),
                    # Job has date range that overlaps with requested range
                    CamperServiceJobModel.start_date.isnot(None),
                    CamperServiceJobModel.start_date <= end_date,
                    CamperServiceJobModel.end_date >= start_date,
                )
            ).order_by(CamperServiceJobModel.start_date)
        )
        jobs = jobs_result.scalars().all()

        # Also get jobs with only scheduled_date (no start_date/end_date yet)
        scheduled_only_result = await db.execute(
            select(CamperServiceJobModel).where(
                and_(
                    CamperServiceJobModel.bay_id == bay.id,
                    CamperServiceJobModel.status.notin_([JobStatus.CANCELLED, JobStatus.INVOICED]),
                    CamperServiceJobModel.start_date.is_(None),
                    CamperServiceJobModel.scheduled_date.isnot(None),
                    CamperServiceJobModel.scheduled_date >= start_date,
                    CamperServiceJobModel.scheduled_date <= end_date,
                )
            ).order_by(CamperServiceJobModel.scheduled_date)
        )
        scheduled_jobs = scheduled_only_result.scalars().all()

        entries = []
        for job in list(jobs) + list(scheduled_jobs):
            # Eagerly load vehicle and customer for display
            await db.refresh(job, ["vehicle", "customer"])

            job_start = job.start_date or job.scheduled_date
            job_end = job.end_date or job.start_date or job.scheduled_date

            entries.append(BayTimelineEntry(
                job_id=str(job.id),
                job_number=job.job_number,
                vehicle_plate=job.vehicle.registration_plate if job.vehicle else "???",
                customer_name=job.customer.name if job.customer else "???",
                status=job.status.value,
                start_date=job_start.isoformat() if job_start else "",
                end_date=job_end.isoformat() if job_end else "",
                wait_reason=job.current_wait_reason,
                color=status_colors.get(job.status, "#9CA3AF"),
            ))

        timeline.append(BayTimelineResponse(
            bay_id=str(bay.id),
            bay_name=bay.name,
            bay_type=bay.bay_type.value,
            entries=entries,
        ))

    return timeline


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
    """Jobs as calendar events. Uses start_date/end_date for multi-day bars, falls back to scheduled_date."""
    try:
        range_start = date.fromisoformat(start) if start else None
    except ValueError:
        range_start = None
    try:
        range_end = date.fromisoformat(end) if end else None
    except ValueError:
        range_end = None

    # Eager-load customer + vehicle for calendar display
    load_opts = [
        selectinload(CamperServiceJobModel.customer),
        selectinload(CamperServiceJobModel.vehicle),
    ]

    # Get jobs with start_date/end_date (multi-day)
    multi_day_query = select(CamperServiceJobModel).options(*load_opts).where(
        CamperServiceJobModel.start_date.isnot(None)
    )
    if range_start:
        multi_day_query = multi_day_query.where(CamperServiceJobModel.end_date >= range_start)
    if range_end:
        multi_day_query = multi_day_query.where(CamperServiceJobModel.start_date <= range_end)

    # Get jobs with only scheduled_date (single-day, backwards compat)
    single_day_query = select(CamperServiceJobModel).options(*load_opts).where(
        and_(
            CamperServiceJobModel.start_date.is_(None),
            CamperServiceJobModel.scheduled_date.isnot(None),
        )
    )
    if range_start:
        single_day_query = single_day_query.where(CamperServiceJobModel.scheduled_date >= range_start)
    if range_end:
        single_day_query = single_day_query.where(CamperServiceJobModel.scheduled_date <= range_end)

    multi_result = await db.execute(multi_day_query)
    single_result = await db.execute(single_day_query)
    multi_jobs = multi_result.scalars().all()
    single_jobs = single_result.scalars().all()

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

    def _build_event(job, start_iso, end_iso=None):
        """Build a CalendarEvent with customer + vehicle info."""
        customer_name = job.customer.name if job.customer else ""
        customer_lang = job.customer.language.value if job.customer and job.customer.language else ""
        customer_phone = job.customer.phone if job.customer else ""
        vehicle_plate = job.vehicle.registration_plate if job.vehicle else ""

        # Title: "JOB-123: Title | Customer (LANG)"
        title_parts = [f"{job.job_number}: {job.title}"]
        if customer_name:
            customer_label = f"{customer_name} ({customer_lang})" if customer_lang else customer_name
            title_parts.append(customer_label)
        title = " | ".join(title_parts)

        return CalendarEvent(
            id=str(job.id),
            title=title,
            start=start_iso,
            end=end_iso,
            color=status_colors.get(job.status, "#9CA3AF"),
            url=f"/camper/jobs/{job.id}",
            extendedProps={
                "status": job.status.value,
                "assigned_to": job.assigned_to or "",
                "job_number": job.job_number,
                "waiting": bool(job.current_wait_reason),
                "wait_reason": job.current_wait_reason or "",
                "customer_name": customer_name,
                "customer_lang": customer_lang,
                "customer_phone": customer_phone,
                "vehicle_plate": vehicle_plate,
            }
        )

    # Multi-day jobs: use start_date and end_date+1 (FullCalendar end is exclusive)
    for job in multi_jobs:
        fc_end = (job.end_date + timedelta(days=1)).isoformat() if job.end_date else None
        events.append(_build_event(job, job.start_date.isoformat(), fc_end))

    # Single-day jobs (backwards compat): scheduled_date only
    for job in single_jobs:
        events.append(_build_event(job, job.scheduled_date.isoformat()))

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

    # Jobs currently waiting (have active wait reason)
    waiting_result = await db.execute(
        select(func.count()).where(
            CamperServiceJobModel.current_wait_reason.isnot(None)
        )
    )
    jobs_waiting = waiting_result.scalar() or 0

    # Bay utilization: % of active bays that have at least one active job
    active_bays_result = await db.execute(
        select(func.count()).where(CamperBayModel.is_active == True)
    )
    active_bays = active_bays_result.scalar() or 0

    if active_bays > 0:
        occupied_bays_result = await db.execute(
            select(func.count(func.distinct(CamperServiceJobModel.bay_id))).where(
                and_(
                    CamperServiceJobModel.bay_id.isnot(None),
                    CamperServiceJobModel.status.in_([
                        JobStatus.APPROVED, JobStatus.IN_PROGRESS,
                        JobStatus.WAITING_PARTS, JobStatus.INSPECTION,
                    ])
                )
            )
        )
        occupied_bays = occupied_bays_result.scalar() or 0
        bay_utilization = round((occupied_bays / active_bays) * 100, 1)
    else:
        bay_utilization = 0

    # Average days per completed job (start_date to completed_at)
    avg_days_result = await db.execute(
        select(func.avg(
            func.extract('epoch', CamperServiceJobModel.completed_at) -
            func.extract('epoch', func.cast(CamperServiceJobModel.start_date, SADateTime(timezone=True)))
        )).where(
            and_(
                CamperServiceJobModel.status.in_([JobStatus.COMPLETED, JobStatus.INVOICED]),
                CamperServiceJobModel.start_date.isnot(None),
                CamperServiceJobModel.completed_at.isnot(None),
            )
        )
    )
    avg_seconds = avg_days_result.scalar()
    average_days_per_job = round(avg_seconds / 86400, 1) if avg_seconds else 0

    return DashboardSummary(
        vehicles_in_shop=vehicles_in_shop,
        jobs_in_progress=jobs_in_progress,
        jobs_waiting_parts=jobs_waiting_parts,
        jobs_waiting=jobs_waiting,
        jobs_completed_today=jobs_completed_today,
        pending_quotes=pending_quotes,
        total_jobs=total_jobs,
        pending_deposits=pending_deposits,
        total_revenue_month=total_revenue_month,
        overdue_invoices=overdue_invoices,
        jobs_in_inspection=jobs_in_inspection,
        bay_utilization=bay_utilization,
        average_days_per_job=average_days_per_job,
    )


# ================================================================
# SHARED RESOURCE ENDPOINTS (Hoist, Diagnostic Scanner, etc.)
# ================================================================

@router.get("/shared-resources", response_model=list[SharedResourceResponse])
async def list_shared_resources(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """List all shared resources (any camper role)"""
    result = await db.execute(
        select(CamperSharedResourceModel).order_by(CamperSharedResourceModel.name)
    )
    return result.scalars().all()


@router.post("/shared-resources", response_model=SharedResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_shared_resource(
    resource: SharedResourceCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_manager_or_admin()),
):
    """Create a new shared resource (manager/admin only)"""
    try:
        resource_type = ResourceType(resource.resource_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid resource type: {resource.resource_type}")

    new_resource = CamperSharedResourceModel(
        name=resource.name,
        resource_type=resource_type,
        description=resource.description,
    )
    db.add(new_resource)
    await db.commit()
    await db.refresh(new_resource)

    logger.info(f"Shared resource created: {new_resource.name} by {current_user['username']}")
    return new_resource


@router.patch("/shared-resources/{resource_id}", response_model=SharedResourceResponse)
async def update_shared_resource(
    resource_id: UUID,
    resource_update: SharedResourceUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_manager_or_admin()),
):
    """Update a shared resource (manager/admin only)"""
    result = await db.execute(
        select(CamperSharedResourceModel).where(CamperSharedResourceModel.id == resource_id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Shared resource not found")

    update_data = resource_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(resource, field, value)

    resource.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(resource)

    logger.info(f"Shared resource updated: {resource.name} by {current_user['username']}")
    return resource


# ================================================================
# RESOURCE BOOKING ENDPOINTS (Hoist Scheduling)
# ================================================================

async def _enrich_booking_response(booking: CamperResourceBookingModel, db: AsyncSession) -> ResourceBookingResponse:
    """Build ResourceBookingResponse with enriched fields from relationships."""
    # Get resource name
    resource_result = await db.execute(
        select(CamperSharedResourceModel.name).where(CamperSharedResourceModel.id == booking.resource_id)
    )
    resource_name = resource_result.scalar_one_or_none() or "Unknown"

    # Get job number and vehicle plate
    job_result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == booking.job_id)
    )
    job = job_result.scalar_one_or_none()
    job_number = job.job_number if job else "Unknown"

    vehicle_plate = "Unknown"
    if job:
        vehicle_result = await db.execute(
            select(CamperVehicleModel.registration_plate).where(CamperVehicleModel.id == job.vehicle_id)
        )
        plate = vehicle_result.scalar_one_or_none()
        if plate:
            vehicle_plate = plate

    return ResourceBookingResponse(
        id=booking.id,
        resource_id=booking.resource_id,
        resource_name=resource_name,
        job_id=booking.job_id,
        job_number=job_number,
        vehicle_plate=vehicle_plate,
        start_date=booking.start_date,
        end_date=booking.end_date,
        status=booking.status.value,
        notes=booking.notes,
        booked_by=booking.booked_by,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
    )


@router.post("/resource-bookings", response_model=ResourceBookingResponse, status_code=status.HTTP_201_CREATED)
async def create_resource_booking(
    booking: ResourceBookingCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_mechanic_or_above()),
):
    """Book a shared resource for a service job (mechanic+ only). Rejects overlapping bookings."""
    # Validate resource exists
    resource_result = await db.execute(
        select(CamperSharedResourceModel).where(CamperSharedResourceModel.id == booking.resource_id)
    )
    resource = resource_result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Shared resource not found")
    if not resource.is_active:
        raise HTTPException(status_code=400, detail="Resource is deactivated")

    # Validate job exists
    job_result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == booking.job_id)
    )
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Service job not found")

    # Validate dates
    if booking.end_date < booking.start_date:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")

    # OVERLAP DETECTION: find any ACTIVE booking for the same resource
    # that overlaps the requested date range
    overlap_result = await db.execute(
        select(CamperResourceBookingModel).where(
            and_(
                CamperResourceBookingModel.resource_id == booking.resource_id,
                CamperResourceBookingModel.status.in_([BookingStatus.SCHEDULED, BookingStatus.IN_USE]),
                CamperResourceBookingModel.start_date <= booking.end_date,
                CamperResourceBookingModel.end_date >= booking.start_date,
            )
        )
    )
    if overlap_result.scalars().first():
        raise HTTPException(
            status_code=409,
            detail="Resource already booked for this period"
        )

    new_booking = CamperResourceBookingModel(
        resource_id=booking.resource_id,
        job_id=booking.job_id,
        start_date=booking.start_date,
        end_date=booking.end_date,
        notes=booking.notes,
        booked_by=current_user['username'],
        status=BookingStatus.SCHEDULED,
    )
    db.add(new_booking)
    await db.commit()
    await db.refresh(new_booking)

    logger.info(
        f"Resource booking created: {resource.name} for {booking.start_date} -> {booking.end_date} "
        f"by {current_user['username']}"
    )
    return await _enrich_booking_response(new_booking, db)


@router.get("/resource-bookings", response_model=list[ResourceBookingResponse])
async def list_resource_bookings(
    resource_id: Optional[UUID] = None,
    start: Optional[date] = None,
    end: Optional[date] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """List resource bookings with optional filters (any camper role)"""
    query = select(CamperResourceBookingModel)

    if resource_id:
        query = query.where(CamperResourceBookingModel.resource_id == resource_id)
    if start:
        query = query.where(CamperResourceBookingModel.end_date >= start)
    if end:
        query = query.where(CamperResourceBookingModel.start_date <= end)
    if status_filter:
        try:
            bs = BookingStatus(status_filter)
            query = query.where(CamperResourceBookingModel.status == bs)
        except ValueError:
            pass

    query = query.order_by(CamperResourceBookingModel.start_date)
    result = await db.execute(query)
    bookings = result.scalars().all()
    return [await _enrich_booking_response(b, db) for b in bookings]


@router.patch("/resource-bookings/{booking_id}/status", response_model=ResourceBookingResponse)
async def update_booking_status(
    booking_id: UUID,
    status_update: ResourceBookingStatusUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_mechanic_or_above()),
):
    """Advance booking status: SCHEDULED -> IN_USE -> COMPLETED, or CANCELLED"""
    result = await db.execute(
        select(CamperResourceBookingModel).where(CamperResourceBookingModel.id == booking_id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Resource booking not found")

    try:
        new_status = BookingStatus(status_update.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status_update.status}")

    # Valid transitions
    valid_transitions = {
        BookingStatus.SCHEDULED: [BookingStatus.IN_USE, BookingStatus.CANCELLED],
        BookingStatus.IN_USE: [BookingStatus.COMPLETED, BookingStatus.CANCELLED],
    }
    allowed = valid_transitions.get(booking.status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {booking.status.value} to {new_status.value}"
        )

    booking.status = new_status
    booking.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(booking)

    logger.info(
        f"Booking {booking.id} status -> {new_status.value} by {current_user['username']}"
    )
    return await _enrich_booking_response(booking, db)


@router.delete("/resource-bookings/{booking_id}", response_model=ResourceBookingResponse)
async def cancel_resource_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_camper_mechanic_or_above()),
):
    """Cancel a resource booking (sets status=CANCELLED)"""
    result = await db.execute(
        select(CamperResourceBookingModel).where(CamperResourceBookingModel.id == booking_id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Resource booking not found")

    if booking.status in (BookingStatus.COMPLETED, BookingStatus.CANCELLED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel booking in {booking.status.value} status"
        )

    booking.status = BookingStatus.CANCELLED
    booking.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(booking)

    logger.info(f"Booking {booking.id} CANCELLED by {current_user['username']}")
    return await _enrich_booking_response(booking, db)


# ================================================================
# APPOINTMENT / WALK-IN QUEUE ENDPOINTS
# ================================================================

async def _enrich_appointment_response(appt: CamperAppointmentModel, db: AsyncSession) -> AppointmentRead:
    """Build AppointmentRead with enriched fields from relationships."""
    bay_name = None
    if appt.bay_id:
        bay_result = await db.execute(
            select(CamperBayModel.name).where(CamperBayModel.id == appt.bay_id)
        )
        bay_name = bay_result.scalar_one_or_none()

    job_number = None
    if appt.job_id:
        job_result = await db.execute(
            select(CamperServiceJobModel.job_number).where(CamperServiceJobModel.id == appt.job_id)
        )
        job_number = job_result.scalar_one_or_none()

    return AppointmentRead(
        id=appt.id,
        appointment_type=appt.appointment_type,
        priority=appt.priority,
        status=appt.status,
        customer_id=appt.customer_id,
        customer_name=appt.customer_name,
        customer_phone=appt.customer_phone,
        vehicle_id=appt.vehicle_id,
        vehicle_plate=appt.vehicle_plate,
        bay_id=appt.bay_id,
        bay_name=bay_name,
        job_id=appt.job_id,
        job_number=job_number,
        scheduled_date=appt.scheduled_date,
        scheduled_time=appt.scheduled_time.strftime("%H:%M") if appt.scheduled_time else None,
        arrival_time=appt.arrival_time,
        service_started_at=appt.service_started_at,
        service_completed_at=appt.service_completed_at,
        description=appt.description,
        estimated_duration_minutes=appt.estimated_duration_minutes,
        notes=appt.notes,
        created_by=appt.created_by,
        created_at=appt.created_at,
        updated_at=appt.updated_at,
    )


@router.post("/appointments", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appt: AppointmentCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """
    Create a booked appointment or walk-in queue entry.
    - BOOKED: requires scheduled_time, status starts as SCHEDULED
    - WALK_IN: arrival_time auto-set to NOW, status starts as WAITING
    """
    from datetime import time as time_type

    # Parse scheduled_time for booked appointments
    parsed_time = None
    if appt.appointment_type == AppointmentType.BOOKED:
        if not appt.scheduled_time:
            raise HTTPException(
                status_code=422,
                detail="Booked appointments require a scheduled_time (HH:MM)"
            )
        try:
            parts = appt.scheduled_time.split(":")
            parsed_time = time_type(int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            raise HTTPException(
                status_code=422,
                detail="Invalid time format. Use HH:MM (e.g., '09:30')"
            )

        # Check for double-booking: same date + overlapping time window
        # A time slot is "occupied" if another booked appointment overlaps
        existing = await db.execute(
            select(CamperAppointmentModel).where(
                and_(
                    CamperAppointmentModel.scheduled_date == appt.scheduled_date,
                    CamperAppointmentModel.scheduled_time == parsed_time,
                    CamperAppointmentModel.appointment_type == AppointmentType.BOOKED,
                    CamperAppointmentModel.status.notin_([
                        AppointmentStatus.CANCELLED,
                        AppointmentStatus.NO_SHOW,
                        AppointmentStatus.COMPLETED,
                    ]),
                )
            )
        )
        if existing.scalars().first():
            raise HTTPException(
                status_code=409,
                detail=f"Time slot {appt.scheduled_time} on {appt.scheduled_date} is already booked"
            )

    # Auto-uppercase plate if provided
    vehicle_plate = appt.vehicle_plate.upper() if appt.vehicle_plate else None

    new_appt = CamperAppointmentModel(
        appointment_type=appt.appointment_type,
        priority=appt.priority,
        status=AppointmentStatus.WAITING if appt.appointment_type == AppointmentType.WALK_IN else AppointmentStatus.SCHEDULED,
        customer_id=appt.customer_id,
        customer_name=appt.customer_name,
        customer_phone=appt.customer_phone,
        vehicle_id=appt.vehicle_id,
        vehicle_plate=vehicle_plate,
        scheduled_date=appt.scheduled_date,
        scheduled_time=parsed_time,
        arrival_time=datetime.now(timezone.utc) if appt.appointment_type == AppointmentType.WALK_IN else None,
        description=appt.description,
        estimated_duration_minutes=appt.estimated_duration_minutes,
        notes=appt.notes,
        created_by=current_user['username'],
    )
    db.add(new_appt)
    await db.commit()
    await db.refresh(new_appt)

    type_label = "Walk-in" if appt.appointment_type == AppointmentType.WALK_IN else "Appointment"
    logger.info(
        f"{type_label} created: {appt.customer_name} on {appt.scheduled_date} "
        f"by {current_user['username']}"
    )
    return await _enrich_appointment_response(new_appt, db)


@router.get("/appointments/today", response_model=list[AppointmentRead])
async def get_today_appointments(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """
    Today's appointment book + walk-in queue.
    Returns sorted: booked appointments by time first, then walk-ins by arrival time.
    This is what Nino sees at 8am.
    """
    today = date.today()
    result = await db.execute(
        select(CamperAppointmentModel)
        .where(CamperAppointmentModel.scheduled_date == today)
        .where(CamperAppointmentModel.status.notin_([
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW,
        ]))
        .order_by(
            # Booked first (BOOKED=0, WALK_IN=1 in sort order)
            CamperAppointmentModel.appointment_type,
            # Then by time (nulls last for walk-ins)
            CamperAppointmentModel.scheduled_time.asc().nullslast(),
            # Walk-ins by arrival time (first-come first-served)
            CamperAppointmentModel.arrival_time.asc().nullslast(),
        )
    )
    appointments = result.scalars().all()
    return [await _enrich_appointment_response(a, db) for a in appointments]


@router.get("/appointments", response_model=list[AppointmentRead])
async def list_appointments(
    scheduled_date: Optional[date] = None,
    status_filter: Optional[str] = None,
    appointment_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """List appointments with optional filters"""
    query = select(CamperAppointmentModel)

    if scheduled_date:
        query = query.where(CamperAppointmentModel.scheduled_date == scheduled_date)
    if status_filter:
        try:
            s = AppointmentStatus(status_filter)
            query = query.where(CamperAppointmentModel.status == s)
        except ValueError:
            pass
    if appointment_type:
        try:
            t = AppointmentType(appointment_type)
            query = query.where(CamperAppointmentModel.appointment_type == t)
        except ValueError:
            pass

    query = query.order_by(
        CamperAppointmentModel.scheduled_date.desc(),
        CamperAppointmentModel.scheduled_time.asc().nullslast(),
        CamperAppointmentModel.arrival_time.asc().nullslast(),
    )
    result = await db.execute(query)
    appointments = result.scalars().all()
    return [await _enrich_appointment_response(a, db) for a in appointments]


@router.get("/appointments/{appointment_id}", response_model=AppointmentRead)
async def get_appointment(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Get a single appointment by ID"""
    result = await db.execute(
        select(CamperAppointmentModel).where(CamperAppointmentModel.id == appointment_id)
    )
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return await _enrich_appointment_response(appt, db)


@router.put("/appointments/{appointment_id}", response_model=AppointmentRead)
async def update_appointment(
    appointment_id: UUID,
    update: AppointmentUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Update appointment details"""
    result = await db.execute(
        select(CamperAppointmentModel).where(CamperAppointmentModel.id == appointment_id)
    )
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    update_data = update.model_dump(exclude_unset=True)
    if "vehicle_plate" in update_data and update_data["vehicle_plate"]:
        update_data["vehicle_plate"] = update_data["vehicle_plate"].upper()
    if "scheduled_time" in update_data and update_data["scheduled_time"]:
        from datetime import time as time_type
        try:
            parts = update_data["scheduled_time"].split(":")
            update_data["scheduled_time"] = time_type(int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            raise HTTPException(status_code=422, detail="Invalid time format. Use HH:MM")

    for field, value in update_data.items():
        setattr(appt, field, value)

    appt.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(appt)

    logger.info(f"Appointment {appt.id} updated by {current_user['username']}")
    return await _enrich_appointment_response(appt, db)


@router.patch("/appointments/{appointment_id}/status", response_model=AppointmentRead)
async def update_appointment_status(
    appointment_id: UUID,
    status_update: AppointmentStatusUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """
    Advance appointment status.
    SCHEDULED -> WAITING (customer arrived)
    WAITING -> IN_SERVICE (work started, optionally assign bay)
    IN_SERVICE -> COMPLETED (done)
    Any active -> CANCELLED or NO_SHOW
    """
    result = await db.execute(
        select(CamperAppointmentModel).where(CamperAppointmentModel.id == appointment_id)
    )
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    new_status = status_update.status

    # Terminal states cannot be changed
    if appt.status in (AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot change status from {appt.status.value} (terminal state)"
        )

    # Valid forward transitions
    valid_transitions = {
        AppointmentStatus.SCHEDULED: [
            AppointmentStatus.WAITING, AppointmentStatus.IN_SERVICE,
            AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW,
        ],
        AppointmentStatus.WAITING: [
            AppointmentStatus.IN_SERVICE,
            AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW,
        ],
        AppointmentStatus.IN_SERVICE: [
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED,
        ],
    }
    allowed = valid_transitions.get(appt.status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {appt.status.value} to {new_status.value}"
        )

    # Auto-set timestamps based on status transitions
    if new_status == AppointmentStatus.WAITING and not appt.arrival_time:
        appt.arrival_time = datetime.now(timezone.utc)
    elif new_status == AppointmentStatus.IN_SERVICE:
        appt.service_started_at = datetime.now(timezone.utc)
        if status_update.bay_id:
            appt.bay_id = status_update.bay_id
    elif new_status == AppointmentStatus.COMPLETED:
        appt.service_completed_at = datetime.now(timezone.utc)

    appt.status = new_status
    appt.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(appt)

    logger.info(
        f"Appointment {appt.id} ({appt.customer_name}): -> {new_status.value} "
        f"by {current_user['username']}"
    )
    return await _enrich_appointment_response(appt, db)


@router.delete("/appointments/{appointment_id}", response_model=AppointmentRead)
async def cancel_appointment(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_camper_role()),
):
    """Cancel an appointment (sets status=CANCELLED)"""
    result = await db.execute(
        select(CamperAppointmentModel).where(CamperAppointmentModel.id == appointment_id)
    )
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appt.status in (AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel appointment in {appt.status.value} status"
        )

    appt.status = AppointmentStatus.CANCELLED
    appt.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(appt)

    logger.info(f"Appointment {appt.id} ({appt.customer_name}) CANCELLED by {current_user['username']}")
    return await _enrich_appointment_response(appt, db)


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


@html_router.get("/camper/appointments", response_class=HTMLResponse, name="camper_appointments")
async def camper_appointments_page(request: Request):
    """Appointment book + walk-in queue - Nino's daily command center"""
    return templates.TemplateResponse("camper/appointments.html", {"request": request})


@html_router.get("/camper/bay-timeline", response_class=HTMLResponse, name="camper_bay_timeline")
async def camper_bay_timeline_page(request: Request):
    """Bay timeline view - CSS Grid resource timeline"""
    return templates.TemplateResponse("camper/bay_timeline.html", {"request": request})
