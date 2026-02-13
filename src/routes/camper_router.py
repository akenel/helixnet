# File: src/routes/camper_router.py
"""
Camper & Tour Service Management API Router.
Handles vehicles, customers, service jobs, and dashboard for Sebastino's shop.

Prefix: /api/v1/camper

"Casa e dove parcheggi." - Home is where you park it.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, date, timezone
from decimal import Decimal
from uuid import UUID
from typing import Optional
from pathlib import Path

from src.db.database import get_db_session
from src.db.models.camper_vehicle_model import CamperVehicleModel, VehicleStatus
from src.db.models.camper_customer_model import CamperCustomerModel
from src.db.models.camper_service_job_model import CamperServiceJobModel, JobStatus
from src.schemas.camper_schema import (
    VehicleCreate, VehicleUpdate, VehicleRead, VehicleStatusUpdate,
    CamperCustomerCreate, CamperCustomerUpdate, CamperCustomerRead,
    ServiceJobCreate, ServiceJobUpdate, ServiceJobRead, ServiceJobStatusUpdate,
    DashboardSummary,
)
from src.core.keycloak_auth import require_roles

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
    """Update job details (mechanic/manager/admin)"""
    result = await db.execute(
        select(CamperServiceJobModel).where(CamperServiceJobModel.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Service job not found")

    update_data = job_update.model_dump(exclude_unset=True)
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

    return DashboardSummary(
        vehicles_in_shop=vehicles_in_shop,
        jobs_in_progress=jobs_in_progress,
        jobs_waiting_parts=jobs_waiting_parts,
        jobs_completed_today=jobs_completed_today,
        pending_quotes=pending_quotes,
        total_jobs=total_jobs,
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
