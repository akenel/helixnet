# File: src/routes/isotto_router.py
"""
ISOTTO Sport Print Shop API Router.
Handles customers, print orders, and dashboard for Famous Guy's shop.

Prefix: /api/v1/print-shop

Since 1968. Via Buscaino, Trapani.
"The postcard is the handshake. The coffee is the close."
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
from src.db.models.isotto_customer_model import IsottoCustomerModel
from src.db.models.isotto_order_model import IsottoOrderModel, OrderStatus, ProductType
from src.schemas.isotto_schema import (
    IsottoCustomerCreate, IsottoCustomerUpdate, IsottoCustomerRead,
    PrintOrderCreate, PrintOrderUpdate, PrintOrderRead, PrintOrderStatusUpdate,
    IsottoDashboardSummary,
)
from src.core.keycloak_auth import require_roles

logger = logging.getLogger(__name__)

# API Router (JSON endpoints)
router = APIRouter(prefix="/api/v1/print-shop", tags=["ISOTTO Sport - Print Shop"])

# HTML Router (Web UI pages for Famous Guy's team)
html_router = APIRouter(tags=["ISOTTO Sport - Print Shop UI"])

# Setup Jinja2 templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


# ================================================================
# AUTH HELPERS (ISOTTO-specific role shortcuts)
# ================================================================

def require_any_isotto_role():
    """Any authenticated print shop staff"""
    return require_roles([
        "isotto-counter",
        "isotto-designer",
        "isotto-operator",
        "isotto-manager",
        "isotto-admin",
    ])


def require_isotto_operator_or_above():
    """Operator, designer, manager, or admin"""
    return require_roles([
        "isotto-operator",
        "isotto-designer",
        "isotto-manager",
        "isotto-admin",
    ])


def require_isotto_manager_or_admin():
    """Manager or admin only"""
    return require_roles([
        "isotto-manager",
        "isotto-admin",
    ])


# ================================================================
# CUSTOMER ENDPOINTS
# ================================================================

@router.post("/customers", response_model=IsottoCustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer: IsottoCustomerCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """Create customer profile (any print shop role)"""
    new_customer = IsottoCustomerModel(
        **customer.model_dump(),
        first_order_date=date.today(),
        last_order_date=date.today(),
        order_count=0,
    )
    db.add(new_customer)
    await db.commit()
    await db.refresh(new_customer)

    logger.info(f"ISOTTO customer created: {new_customer.name} by {current_user['username']}")
    return new_customer


@router.get("/customers", response_model=list[IsottoCustomerRead])
async def list_customers(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """List/search customers (any print shop role)"""
    query = select(IsottoCustomerModel)

    if search:
        query = query.where(
            IsottoCustomerModel.name.ilike(f"%{search}%") |
            IsottoCustomerModel.company_name.ilike(f"%{search}%") |
            IsottoCustomerModel.phone.ilike(f"%{search}%") |
            IsottoCustomerModel.email.ilike(f"%{search}%")
        )

    query = query.order_by(IsottoCustomerModel.last_order_date.desc().nullslast()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/customers/{customer_id}", response_model=IsottoCustomerRead)
async def get_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """Get customer with order history"""
    result = await db.execute(
        select(IsottoCustomerModel).where(IsottoCustomerModel.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.put("/customers/{customer_id}", response_model=IsottoCustomerRead)
async def update_customer(
    customer_id: UUID,
    customer_update: IsottoCustomerUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """Update customer info (any print shop role)"""
    result = await db.execute(
        select(IsottoCustomerModel).where(IsottoCustomerModel.id == customer_id)
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

    logger.info(f"ISOTTO customer updated: {customer.name} by {current_user['username']}")
    return customer


# ================================================================
# ORDER ENDPOINTS
# ================================================================

@router.post("/orders", response_model=PrintOrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    order: PrintOrderCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """Create new print order (starts as QUOTED)"""
    # Verify customer exists
    customer_result = await db.execute(
        select(IsottoCustomerModel).where(IsottoCustomerModel.id == order.customer_id)
    )
    if not customer_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Customer not found")

    # Generate order number
    today = date.today().strftime("%Y%m%d")
    count_result = await db.execute(
        select(func.count()).where(
            IsottoOrderModel.order_number.like(f"ORD-{today}-%")
        )
    )
    count = count_result.scalar() or 0
    order_number = f"ORD-{today}-{count + 1:04d}"

    order_data = order.model_dump()
    order_data["order_number"] = order_number
    order_data["status"] = OrderStatus.QUOTED
    order_data["quoted_at"] = datetime.now(timezone.utc)
    new_order = IsottoOrderModel(**order_data)
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    logger.info(f"ISOTTO order created: {order_number} by {current_user['username']}")
    return new_order


@router.get("/orders", response_model=list[PrintOrderRead])
async def list_orders(
    status_filter: Optional[str] = None,
    product_type: Optional[str] = None,
    customer_id: Optional[UUID] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """List orders with filters (any print shop role)"""
    query = select(IsottoOrderModel)

    if status_filter:
        try:
            os = OrderStatus(status_filter)
            query = query.where(IsottoOrderModel.status == os)
        except ValueError:
            pass

    if product_type:
        try:
            pt = ProductType(product_type)
            query = query.where(IsottoOrderModel.product_type == pt)
        except ValueError:
            pass

    if customer_id:
        query = query.where(IsottoOrderModel.customer_id == customer_id)

    if search:
        query = query.where(
            IsottoOrderModel.order_number.ilike(f"%{search}%") |
            IsottoOrderModel.title.ilike(f"%{search}%")
        )

    query = query.order_by(IsottoOrderModel.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/orders/{order_id}", response_model=PrintOrderRead)
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """Get full order details"""
    result = await db.execute(
        select(IsottoOrderModel).where(IsottoOrderModel.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Print order not found")
    return order


@router.put("/orders/{order_id}", response_model=PrintOrderRead)
async def update_order(
    order_id: UUID,
    order_update: PrintOrderUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_isotto_operator_or_above()),
):
    """Update order details (operator/designer/manager/admin)"""
    result = await db.execute(
        select(IsottoOrderModel).where(IsottoOrderModel.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Print order not found")

    update_data = order_update.model_dump(exclude_unset=True)

    # Handle proof approval timestamp
    if "proof_approved" in update_data and update_data["proof_approved"] and not order.proof_approved:
        order.proof_approved_at = datetime.now(timezone.utc)

    for field, value in update_data.items():
        setattr(order, field, value)

    order.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(order)

    logger.info(f"ISOTTO order updated: {order.order_number} by {current_user['username']}")
    return order


@router.patch("/orders/{order_id}/status", response_model=PrintOrderRead)
async def update_order_status(
    order_id: UUID,
    status_update: PrintOrderStatusUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_isotto_operator_or_above()),
):
    """Advance order status (operator/designer/manager/admin)"""
    result = await db.execute(
        select(IsottoOrderModel).where(IsottoOrderModel.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Print order not found")

    old_status = order.status
    order.status = status_update.status
    order.updated_at = datetime.now(timezone.utc)

    # Auto-set timestamps based on status transitions
    if status_update.status == OrderStatus.APPROVED and not order.approved_at:
        order.approved_at = datetime.now(timezone.utc)
    elif status_update.status == OrderStatus.IN_PRODUCTION and not order.production_started_at:
        order.production_started_at = datetime.now(timezone.utc)
    elif status_update.status in (OrderStatus.READY, OrderStatus.QUALITY_CHECK) and not order.completed_at:
        order.completed_at = datetime.now(timezone.utc)
    elif status_update.status == OrderStatus.PICKED_UP and not order.picked_up_at:
        order.picked_up_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(order)

    logger.info(f"ISOTTO order {order.order_number}: {old_status.value} -> {status_update.status.value} by {current_user['username']}")
    return order


@router.post("/orders/{order_id}/approve", response_model=PrintOrderRead)
async def approve_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """Customer approves quote -> status becomes APPROVED"""
    result = await db.execute(
        select(IsottoOrderModel).where(IsottoOrderModel.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Print order not found")

    if order.status != OrderStatus.QUOTED:
        raise HTTPException(
            status_code=400,
            detail=f"Can only approve orders in QUOTED status. Current: {order.status.value}"
        )

    order.status = OrderStatus.APPROVED
    order.approved_at = datetime.now(timezone.utc)
    order.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(order)

    logger.info(f"ISOTTO order {order.order_number} APPROVED by {current_user['username']}")
    return order


@router.post("/orders/{order_id}/complete", response_model=PrintOrderRead)
async def complete_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_isotto_operator_or_above()),
):
    """Mark order production complete -> READY for pickup"""
    result = await db.execute(
        select(IsottoOrderModel).where(IsottoOrderModel.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Print order not found")

    if order.status not in (OrderStatus.IN_PRODUCTION, OrderStatus.QUALITY_CHECK, OrderStatus.APPROVED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot complete order in {order.status.value} status"
        )

    order.status = OrderStatus.READY
    order.completed_at = datetime.now(timezone.utc)
    order.updated_at = datetime.now(timezone.utc)

    # Update customer stats
    customer_result = await db.execute(
        select(IsottoCustomerModel).where(IsottoCustomerModel.id == order.customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    if customer:
        customer.last_order_date = date.today()
        customer.order_count = (customer.order_count or 0) + 1
        customer.total_spend = (customer.total_spend or Decimal("0.00")) + order.total_price

    await db.commit()
    await db.refresh(order)

    logger.info(f"ISOTTO order {order.order_number} COMPLETED by {current_user['username']}: {order.total_price} EUR")
    return order


# ================================================================
# DASHBOARD
# ================================================================

@router.get("/dashboard", response_model=IsottoDashboardSummary)
async def get_dashboard(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """One-screen overview for Famous Guy"""
    # Orders in production
    in_production_result = await db.execute(
        select(func.count()).where(IsottoOrderModel.status == OrderStatus.IN_PRODUCTION)
    )
    orders_in_production = in_production_result.scalar() or 0

    # Pending approval (quoted)
    pending_result = await db.execute(
        select(func.count()).where(IsottoOrderModel.status == OrderStatus.QUOTED)
    )
    orders_pending_approval = pending_result.scalar() or 0

    # Ready for pickup
    ready_result = await db.execute(
        select(func.count()).where(IsottoOrderModel.status == OrderStatus.READY)
    )
    orders_ready = ready_result.scalar() or 0

    # Quality check
    qc_result = await db.execute(
        select(func.count()).where(IsottoOrderModel.status == OrderStatus.QUALITY_CHECK)
    )
    orders_in_quality_check = qc_result.scalar() or 0

    # Completed today
    today_start = datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)
    today_end = datetime.combine(date.today(), datetime.max.time(), tzinfo=timezone.utc)
    completed_today_result = await db.execute(
        select(func.count()).where(
            and_(
                IsottoOrderModel.completed_at >= today_start,
                IsottoOrderModel.completed_at <= today_end,
            )
        )
    )
    orders_completed_today = completed_today_result.scalar() or 0

    # Total orders all-time
    total_result = await db.execute(select(func.count()).select_from(IsottoOrderModel))
    total_orders = total_result.scalar() or 0

    return IsottoDashboardSummary(
        orders_in_production=orders_in_production,
        orders_pending_approval=orders_pending_approval,
        orders_ready=orders_ready,
        orders_completed_today=orders_completed_today,
        orders_in_quality_check=orders_in_quality_check,
        total_orders=total_orders,
    )


# ================================================================
# HTML WEB UI ROUTES (Famous Guy's Team Interface)
# ================================================================

@html_router.get("/print-shop", response_class=HTMLResponse, name="isotto_login")
async def isotto_login(request: Request):
    """ISOTTO Sport login page - entry point"""
    return templates.TemplateResponse("isotto/login.html", {"request": request})


@html_router.get("/print-shop/callback")
async def isotto_oauth_callback(request: Request, code: str = None, error: str = None):
    """
    OAuth2 Callback - Server-side token exchange.
    Same pattern as Camper: browser -> Keycloak -> code -> server exchanges -> redirect with token.
    """
    import httpx
    from fastapi.responses import RedirectResponse

    if error:
        logger.error(f"ISOTTO OAuth callback error: {error}")
        return RedirectResponse(url="/print-shop?error=" + error)

    if not code:
        logger.warning("ISOTTO OAuth callback without code")
        return RedirectResponse(url="/print-shop?error=no_code")

    # Keycloak config -- internal Docker URL for server-to-server
    keycloak_internal_url = "http://keycloak:8080"
    realm = "kc-isotto-print-realm-dev"
    client_id = "isotto_print_web"

    # Reconstruct redirect_uri from forwarded headers (must match browser's original)
    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host", "helix.local")
    redirect_uri = f"{forwarded_proto}://{forwarded_host}/print-shop/callback"

    logger.info(f"ISOTTO token exchange redirect_uri: {redirect_uri}")

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
                logger.error(f"ISOTTO token exchange failed: {response.status_code} - {response.text}")
                return RedirectResponse(url="/print-shop?error=token_exchange_failed")

            tokens = response.json()
            access_token = tokens.get("access_token")

            if not access_token:
                logger.error("ISOTTO: No access_token in response")
                return RedirectResponse(url="/print-shop?error=no_token")

            logger.info("ISOTTO OAuth callback successful, redirecting to dashboard")
            return RedirectResponse(url=f"/print-shop/dashboard#token={access_token}")

    except Exception as e:
        logger.error(f"ISOTTO token exchange exception: {e}")
        return RedirectResponse(url="/print-shop?error=token_exchange_error")


@html_router.get("/print-shop/dashboard", response_class=HTMLResponse, name="isotto_dashboard")
async def isotto_dashboard_page(request: Request):
    """Dashboard - Morning overview for Famous Guy"""
    return templates.TemplateResponse("isotto/dashboard.html", {"request": request})


@html_router.get("/print-shop/orders", response_class=HTMLResponse, name="isotto_orders")
async def isotto_orders_page(request: Request):
    """Order board - filterable list of all print orders"""
    return templates.TemplateResponse("isotto/orders.html", {"request": request})


@html_router.get("/print-shop/orders/new", response_class=HTMLResponse, name="isotto_order_new")
async def isotto_order_new_page(request: Request):
    """New order - create a quotation"""
    return templates.TemplateResponse("isotto/order_detail.html", {"request": request})


@html_router.get("/print-shop/orders/{order_id}", response_class=HTMLResponse, name="isotto_order_detail")
async def isotto_order_detail_page(request: Request, order_id: str):
    """Order detail - view, edit, advance status"""
    return templates.TemplateResponse("isotto/order_detail.html", {"request": request})


@html_router.get("/print-shop/customers", response_class=HTMLResponse, name="isotto_customers")
async def isotto_customers_page(request: Request):
    """Customer lookup - search and manage profiles"""
    return templates.TemplateResponse("isotto/customers.html", {"request": request})
