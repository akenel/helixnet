# File: src/routes/pos_router.py
"""
POS (Point of Sale) API Router for Felix's Artemis Store.
Handles products, transactions, scanning, and checkout.

Sprint 4: Added HTML interface routes for Pam's POS system.
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID
from typing import Optional
from pathlib import Path

from src.db.database import get_db_session
from src.db.models import (
    ProductModel,
    TransactionModel,
    LineItemModel,
    UserModel,
    StoreSettingsModel,
    CustomerModel,
    ShiftSessionModel,
    SessionStatus,
    TransactionStatus,
    PaymentMethod,
    BacklogItemModel,
    BacklogItemType,
    BacklogPriority,
    CashShiftModel,
    CashShiftStatus,
    CashMovementModel,
    CashMovementKind,
    CustomerModel,
    CreditTransactionModel,
    CreditTransactionType,
)
from src.core.constants import HelixApplication
from src.services.cash_shift_service import (
    expected_cash, close_result, denoms_total, money,
)
from pydantic import BaseModel
from src.schemas.pos_schema import (
    ProductCreate,
    ProductUpdate,
    ProductRead,
    TransactionCreate,
    TransactionRead,
    TransactionWithItems,
    LineItemCreate,
    LineItemRead,
    BarcodeScanRequest,
    BarcodeScanResponse,
    CheckoutRequest,
    RefundRequest,
    DailySummary,
    StoreSettingsRead,
    StoreSettingsUpdate,
)
from src.schemas.customer_schema import CustomerQRScanResponse
# Real Keycloak authentication with RBAC
from src.core.keycloak_auth import (
    require_roles,
    require_any_pos_role,
    require_admin,
    require_manager_or_admin,
)
from src.core.config import get_settings
# REFERENCE ONLY: Mock auth kept for comparison
# from src.core.mock_auth import get_mock_user as get_current_user

logger = logging.getLogger(__name__)

# API Router (JSON endpoints)
router = APIRouter(prefix="/api/v1/pos", tags=["POS"])

# HTML Router (Web UI pages for Pam)
html_router = APIRouter(tags=["🖥️ POS Web UI"])

# Setup Jinja2 templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))
# Real build stamp in the POS status bar (version + the SHA actually deployed).
from src.build_info import get_version, get_git_sha  # noqa: E402
templates.env.globals["app_version"] = get_version()
templates.env.globals["git_sha"] = get_git_sha()


# ================================================================
# POS CONFIGURATION ENDPOINT
# ================================================================

@router.get("/config")
async def get_pos_config():
    """
    Get POS configuration including VAT rate, currency, locale.
    This is public (no auth required) so the UI can load it on init.

    VAT rates are updated annually:
    - 2024: 7.7%
    - 2025: 8.1%
    """
    settings = get_settings()
    return {
        "vat_rate": settings.POS_VAT_RATE,
        "vat_year": settings.POS_VAT_YEAR,
        "currency": settings.POS_CURRENCY,
        "locale": settings.POS_LOCALE,
        "vat_decimal": settings.POS_VAT_RATE / 100,  # 0.081 for calculations
    }


# ================================================================
# PRODUCT ENDPOINTS
# ================================================================

@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["👔️ pos-manager", "🛠️ pos-developer", "👑️ pos-admin"])),
):
    """Create a new product in the catalog (manager/developer/admin only)"""

    new_product = ProductModel(**product.model_dump())
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    logger.info(f"Product created: {new_product.sku} by user {current_user['username']}")
    return new_product


@router.get("/products", response_model=list[ProductRead])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """List all products in catalog (any POS role)"""
    query = select(ProductModel)

    if active_only:
        query = query.where(ProductModel.is_active == True)

    if category:
        query = query.where(ProductModel.category == category)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    products = result.scalars().all()

    return products


@router.get("/products/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Get product by ID (any POS role)"""
    result = await db.execute(select(ProductModel).where(ProductModel.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.get("/products/barcode/{barcode}", response_model=ProductRead)
async def get_product_by_barcode(
    barcode: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Get product by barcode (for scanning)"""
    result = await db.execute(select(ProductModel).where(ProductModel.barcode == barcode))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail=f"Product with barcode '{barcode}' not found")

    if not product.is_active:
        raise HTTPException(status_code=400, detail="Product is inactive")

    return product


@router.put("/products/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: UUID,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """Update product details (manager/admin only)"""

    result = await db.execute(select(ProductModel).where(ProductModel.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update only provided fields
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    product.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(product)

    logger.info(f"Product updated: {product.sku} by user {current_user['username']}")
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """Soft delete product (set inactive - manager/admin only)"""

    result = await db.execute(select(ProductModel).where(ProductModel.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_active = False
    product.updated_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info(f"Product deactivated: {product.sku} by user {current_user['username']}")


# ================================================================
# FAST SEARCH ENDPOINTS (PostgreSQL Full-Text + Trigram)
# ================================================================

@router.get("/search")
async def search_products_fast(
    q: str = "",
    category: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Fast paginated product search (trigram fuzzy + ILIKE + exact sku/barcode),
    backed by the GIN trigram index. Built for a big (thousands) catalog.

    Returns an envelope: {items, total, skip, limit}. `total` is the HONEST count
    of all matches (window count), so the UI can paginate / show "Found N".
    No auth required for search (public catalog).
    """
    from sqlalchemy import text

    if not q and not category:
        return {"items": [], "total": 0, "skip": skip, "limit": limit}

    # One query: ranked page + total matches via count(*) OVER().
    query = text("""
        SELECT id, sku, barcode, name, category, price, stock_quantity, image_url,
               similarity(name, :q) AS relevance,
               count(*) OVER() AS total_count
        FROM products
        WHERE is_active = true
          AND (
            :q = '' OR name ILIKE '%' || :q || '%' OR sku ILIKE '%' || :q || '%'
            OR barcode ILIKE '%' || :q || '%' OR similarity(name, :q) > 0.1
          )
          AND (CAST(:category AS TEXT) IS NULL OR category ILIKE '%' || CAST(:category AS TEXT) || '%')
        ORDER BY
          CASE WHEN name ILIKE :q || '%' THEN 0 ELSE 1 END,
          similarity(name, :q) DESC, name
        LIMIT :limit OFFSET :skip
    """)
    rows = (await db.execute(query, {
        "q": q or "", "category": category, "limit": limit, "skip": skip,
    })).fetchall()

    total = int(rows[0].total_count) if rows else 0
    items = [
        {
            "id": str(row.id), "sku": row.sku, "barcode": row.barcode, "name": row.name,
            "category": row.category, "price": float(row.price) if row.price else 0,
            "stock_quantity": row.stock_quantity or 0, "image_url": row.image_url,
            "relevance": float(row.relevance) if row.relevance else 0,
        }
        for row in rows
    ]
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/search/categories")
async def get_product_categories(
    db: AsyncSession = Depends(get_db_session),
):
    """Get all product categories with counts."""
    from sqlalchemy import text

    query = text("""
        SELECT category as name, product_count as count, avg_price
        FROM product_categories
        WHERE category IS NOT NULL AND category != ''
        ORDER BY product_count DESC
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    return [
        {
            "name": row.name,
            "count": row.count,
            "avg_price": float(row.avg_price) if row.avg_price else 0
        }
        for row in rows
    ]


@router.post("/assist/vouch")
async def vouch_for_customer(
    customer_handle: str,
    voucher_handle: str,
    amount: float,
    item_description: str,
    fallback_contact: str = "pam",
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Forgot My Card — Trust network deferred payment.

    BLQ Scene: Coolie forgot his card.
    Sylvie: "I'll take care of it. You met Pam already.
             We're all connected here."

    Creates a vouch record:
    - Who vouched (Sylvie)
    - For whom (Coolie)
    - Amount (the torch lighter)
    - Fallback contact (Pam has details)

    Payment settled later through the network.
    """
    from datetime import datetime, timezone

    vouch_record = {
        "vouch_id": f"VOUCH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "customer": customer_handle,
        "vouched_by": voucher_handle,
        "amount_chf": amount,
        "item": item_description,
        "fallback_contact": fallback_contact,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "network_message": f"{voucher_handle} vouches for {customer_handle}. "
                          f"Fallback: ask {fallback_contact} for contact details.",
        "trust_chain": [voucher_handle, fallback_contact, "felix"]
    }

    logger.info(f"VOUCH: {voucher_handle} vouches for {customer_handle} - CHF {amount}")

    return {
        "success": True,
        "vouch": vouch_record,
        "message": f"I'll take care of it. You met {fallback_contact} already. We're all connected.",
        "contact_script": f"If you have issues, call me on Telegram or ask {fallback_contact} — she has all my details."
    }


@router.get("/assist/decide")
async def assist_decision(
    product_a: str,
    product_b: str,
    customer_context: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Seal the Deal — Help customer decide between two options.

    BLQ Scene: Coolie can't decide blue or black torch.
    Sylvie steps in: "The blue. It matches your bag."

    Staff uses this when customer is stuck.
    Returns: recommendation + reason + upsell.
    """
    # Simple decision helper - in real life could use AI
    recommendations = {
        "blue": "Stands out, matches most bags, popular choice",
        "black": "Classic, professional, never goes out of style",
        "gold": "Premium feel, gift-worthy, collector's item",
        "silver": "Sleek, modern, easy to spot in a drawer",
    }

    # Pick one (simple logic - could be smarter)
    choice = product_a.lower()
    reason = recommendations.get(choice, "Quality choice, can't go wrong")

    if customer_context and "bag" in customer_context.lower():
        reason = f"Matches the bag. {reason}"

    return {
        "recommendation": product_a,
        "reason": reason,
        "closer_script": f"The {product_a}. {reason}. I'll take care of it.",
        "upsell": "Need a case for that?",
        "seal_it": True
    }


@router.get("/search/picture")
async def search_from_picture(
    description: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Product lookup from picture/description.

    BLQ Scene: Joey shows Ralph a picture on his phone.
    "Ever seen these before?" - Jack Herer papers.

    Ralph types what he sees: "jack herer rolling papers gold"
    System searches products + returns suggestions.

    No image AI needed - just good description search.
    YAGNI: Phone works. Type what you see.
    """
    from sqlalchemy import text

    if not description or len(description) < 2:
        return {
            "success": False,
            "message": "Describe what you see in the picture",
            "products": [],
            "suggestions": []
        }

    # Search products by description
    query = text("""
        SELECT id, sku, barcode, name, category, price, stock_quantity, image_url, relevance
        FROM search_products(:search_term, NULL, 20)
    """)

    result = await db.execute(query, {"search_term": description})
    rows = result.fetchall()

    products = [
        {
            "id": str(row.id),
            "sku": row.sku,
            "name": row.name,
            "category": row.category,
            "price": float(row.price) if row.price else 0,
            "in_stock": (row.stock_quantity or 0) > 0,
            "relevance": float(row.relevance) if row.relevance else 0
        }
        for row in rows
    ]

    # Build helpful response
    if products:
        top = products[0]
        return {
            "success": True,
            "message": f"Found {len(products)} matches. Best: {top['name']}",
            "products": products,
            "suggestions": [
                "Check stock in back room",
                "Ask if customer wants to order",
                "Note for Felix: sourcing request"
            ] if not top['in_stock'] else [
                f"In stock! {top['name']}",
                "Show customer the product",
                "Add to transaction"
            ]
        }

    return {
        "success": False,
        "message": "No matches found. Try different words from the picture.",
        "products": [],
        "suggestions": [
            "Create sourcing request for Felix",
            "Take photo for KB",
            "Ask customer for more details",
            "Check supplier catalogs"
        ]
    }


@router.get("/search/stats")
async def get_product_stats(
    db: AsyncSession = Depends(get_db_session),
):
    """Get product catalog statistics."""
    from sqlalchemy import text

    query = text("SELECT * FROM product_stats")
    result = await db.execute(query)
    row = result.fetchone()

    if row:
        return {
            "total": row.total_products,
            "categories": row.categories,
            "with_barcode": row.with_barcode,
            "in_stock": row.in_stock,
            "avg_price": float(row.avg_price) if row.avg_price else 0
        }

    return {"total": 0, "categories": 0, "with_barcode": 0, "in_stock": 0, "avg_price": 0}


# ================================================================
# CUSTOMER QR SCAN (BLQ: Rapid Checkout)
# ================================================================

@router.get("/customer/scan", response_model=CustomerQRScanResponse)
async def scan_customer_qr(
    code: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Rapid customer lookup via QR code scan.

    BLQ Scene: Coolie shows QR on phone → Pam scans → Instant recognition

    The code format is: HLX-XXXXXXXX (8 hex chars after prefix)

    Returns customer info for checkout:
    - Handle, tier, discount
    - Credits balance
    - VIP status

    No auth required - scan is public (code is the secret).
    """
    if not code:
        return CustomerQRScanResponse(
            success=False,
            message="No QR code provided"
        )

    # Look up by QR code
    result = await db.execute(
        select(CustomerModel).where(CustomerModel.qr_code == code)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        return CustomerQRScanResponse(
            success=False,
            message=f"Customer not found for code: {code}"
        )

    if not customer.is_active:
        return CustomerQRScanResponse(
            success=False,
            message="Customer account is inactive"
        )

    logger.info(f"QR scan: Customer '{customer.handle}' recognized via {code}")

    return CustomerQRScanResponse(
        success=True,
        message=f"Welcome back, {customer.handle}!",
        customer_id=customer.id,
        handle=customer.handle,
        qr_code=customer.qr_code,
        loyalty_tier=customer.loyalty_tier.value,
        tier_discount_percent=customer.tier_discount_percent,
        credits_balance=customer.credits_balance,
        crack_level=customer.crack_level.value,
        is_vip=customer.is_vip,
    )


@router.post("/customer/{customer_id}/generate-qr")
async def generate_customer_qr(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["👔️ pos-manager", "👑️ pos-admin"])),
):
    """
    Generate a new QR code for a customer (manager/admin only).

    Returns the new QR code value that should be encoded in a QR image.
    """
    result = await db.execute(
        select(CustomerModel).where(CustomerModel.id == customer_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Generate new QR code
    new_code = customer.generate_qr_code()
    await db.commit()

    logger.info(f"QR code generated for '{customer.handle}': {new_code}")

    return {
        "customer_id": str(customer.id),
        "handle": customer.handle,
        "qr_code": new_code,
        "message": f"QR code generated: {new_code}"
    }


# ================================================================
# SHIFT SESSION WIZARD (BLQ: Pam forgot logout, Ralph needs POS)
# ================================================================

@router.post("/shift/start")
async def start_shift_session(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Start a new POS shift session.

    BLQ Scene: Ralph arrives, logs in, starts his shift.

    Creates a session record for:
    - Tracking who's on the register
    - Cash drawer accountability
    - Shift handoff chain
    """
    user_id = current_user.get('sub', current_user.get('preferred_username', 'unknown'))
    username = current_user.get('preferred_username', current_user.get('name', 'Unknown'))

    # Check for existing active session for this user
    existing = await db.execute(
        select(ShiftSessionModel).where(
            ShiftSessionModel.user_id == user_id,
            ShiftSessionModel.status == SessionStatus.ACTIVE
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"User {username} already has an active session. End it first."
        )

    # Create new session
    session = ShiftSessionModel(
        user_id=user_id,
        username=username,
        store_number=1,  # Default store
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500],
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    logger.info(f"Shift started: {username} at store {session.store_number}")

    return {
        "session_id": str(session.id),
        "username": session.username,
        "store_number": session.store_number,
        "started_at": session.started_at.isoformat(),
        "message": f"Shift started for {username}"
    }


@router.post("/shift/end")
async def end_shift_session(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    End current user's shift session (normal logout).
    """
    user_id = current_user.get('sub', current_user.get('preferred_username', 'unknown'))
    username = current_user.get('preferred_username', 'Unknown')

    result = await db.execute(
        select(ShiftSessionModel).where(
            ShiftSessionModel.user_id == user_id,
            ShiftSessionModel.status == SessionStatus.ACTIVE
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="No active session found")

    session.end_session(ended_by=user_id, reason="Normal logout")
    await db.commit()

    logger.info(f"Shift ended: {username}")

    return {
        "session_id": str(session.id),
        "username": session.username,
        "ended_at": session.ended_at.isoformat(),
        "transaction_count": session.transaction_count,
        "message": f"Shift ended for {username}"
    }


@router.get("/shift/active")
async def get_active_sessions(
    store_number: int = 1,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Get all active sessions at a store.

    BLQ Scene: Ralph arrives, sees Pam is still logged in.
    """
    result = await db.execute(
        select(ShiftSessionModel).where(
            ShiftSessionModel.store_number == store_number,
            ShiftSessionModel.status == SessionStatus.ACTIVE
        ).order_by(ShiftSessionModel.started_at.desc())
    )
    sessions = result.scalars().all()

    return {
        "store_number": store_number,
        "active_sessions": [
            {
                "session_id": str(s.id),
                "username": s.username,
                "started_at": s.started_at.isoformat(),
                "last_activity": s.last_activity.isoformat(),
                "transaction_count": s.transaction_count,
                "drawer_opened": s.drawer_opened,
            }
            for s in sessions
        ],
        "count": len(sessions)
    }


@router.post("/shift/force-end/{session_id}")
async def force_end_session(
    session_id: UUID,
    reason: str = "Manager override",
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """
    Force end another user's session (manager/admin only).

    BLQ Scene: Felix on the road, gets call from Ralph.
    Felix force-ends Pam's session so Ralph can start his shift.
    """
    manager_id = current_user.get('sub', current_user.get('preferred_username', 'unknown'))
    manager_name = current_user.get('preferred_username', 'Manager')

    result = await db.execute(
        select(ShiftSessionModel).where(ShiftSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Session is not active")

    session.force_end(manager_id=manager_id, reason=reason)
    await db.commit()

    logger.warning(f"Session FORCE ENDED: {session.username} by {manager_name} - {reason}")

    return {
        "session_id": str(session.id),
        "username": session.username,
        "ended_by": manager_name,
        "reason": reason,
        "message": f"Session force-ended for {session.username}"
    }


@router.post("/shift/handoff/{session_id}")
async def handoff_shift(
    session_id: UUID,
    next_user: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """
    Handoff shift to next user (manager/admin only).

    BLQ Scene: Shift change - Pam → Ralph with manager approval.
    Creates audit trail of who handed off to whom.
    """
    manager_id = current_user.get('sub', current_user.get('preferred_username', 'unknown'))
    manager_name = current_user.get('preferred_username', 'Manager')

    result = await db.execute(
        select(ShiftSessionModel).where(ShiftSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Session is not active")

    old_user = session.username
    session.handoff_to(next_user=next_user, manager_id=manager_id)
    await db.commit()

    logger.info(f"Shift HANDOFF: {old_user} → {next_user} (approved by {manager_name})")

    return {
        "session_id": str(session.id),
        "from_user": old_user,
        "to_user": next_user,
        "approved_by": manager_name,
        "message": f"Shift handed off from {old_user} to {next_user}"
    }


@router.get("/shift/my-session")
async def get_my_session(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Get current user's active session (if any).

    Used by UI to show session status in header.
    """
    user_id = current_user.get('sub', current_user.get('preferred_username', 'unknown'))

    result = await db.execute(
        select(ShiftSessionModel).where(
            ShiftSessionModel.user_id == user_id,
            ShiftSessionModel.status == SessionStatus.ACTIVE
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        return {"active": False, "message": "No active session"}

    # Update activity
    session.update_activity()
    await db.commit()

    return {
        "active": True,
        "session_id": str(session.id),
        "username": session.username,
        "store_number": session.store_number,
        "started_at": session.started_at.isoformat(),
        "transaction_count": session.transaction_count,
        "drawer_opened": session.drawer_opened,
    }


# ================================================================
# TRANSACTION ENDPOINTS (Cart/Checkout)
# ================================================================

@router.get("/transactions", response_model=list[TransactionRead])
async def list_transactions(
    date: Optional[str] = None,
    status_filter: Optional[str] = None,
    payment_method: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """List transactions with optional filters. Managers see all, cashiers see their own."""
    query = select(TransactionModel)

    # Date filter
    if date:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    else:
        target_date = datetime.now(timezone.utc).date()

    start_of_day = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
    end_of_day = datetime.combine(target_date, datetime.max.time(), tzinfo=timezone.utc)
    query = query.where(TransactionModel.created_at >= start_of_day)
    query = query.where(TransactionModel.created_at <= end_of_day)

    # Status filter
    if status_filter:
        try:
            ts = TransactionStatus(status_filter.upper())
            query = query.where(TransactionModel.status == ts)
        except ValueError:
            pass
    else:
        # BL-86: hide reaped/cancelled empty carts from the default view so the report
        # stays clean. They're not deleted -- still reachable via status_filter=cancelled.
        query = query.where(TransactionModel.status != TransactionStatus.CANCELLED)

    # Payment method filter
    if payment_method:
        try:
            pm = PaymentMethod(payment_method.upper())
            query = query.where(TransactionModel.payment_method == pm)
        except ValueError:
            pass

    # Cashiers only see their own transactions; managers/admins see all
    user_roles = current_user.get("user_roles", [])
    is_manager = any("pos-manager" in r or "pos-admin" in r or "pos-auditor" in r for r in user_roles)
    if not is_manager:
        query = query.where(TransactionModel.cashier_id == current_user.get("sub"))

    query = query.order_by(TransactionModel.created_at.desc())
    result = await db.execute(query)
    txns = result.scalars().all()

    # BL-83 (Felix): show WHO rang each sale. cashier_id is the Keycloak sub, which
    # matches users.id -- resolve it to a display name (first name, else username) so
    # the report says "Pam"/"Felix", not a generic "Cashier". One batched lookup.
    cashier_ids = {t.cashier_id for t in txns if t.cashier_id}
    names: dict = {}
    if cashier_ids:
        urows = await db.execute(
            select(UserModel.id, UserModel.first_name, UserModel.username)
            .where(UserModel.id.in_(cashier_ids))
        )
        names = {uid: (first or uname) for uid, first, uname in urows.all()}
    for t in txns:
        t.cashier_name = names.get(t.cashier_id)
    return txns


@router.post("/transactions", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: TransactionCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["💰️ pos-cashier", "👔️ pos-manager", "👑️ pos-admin"])),
):
    """Create new transaction (open cart) - cashier/manager/admin only"""
    # Generate transaction number (simple sequential for demo)
    today = date.today().strftime("%Y%m%d")
    # TODO: Make this atomic with proper sequence
    count_result = await db.execute(
        select(func.count()).where(TransactionModel.transaction_number.like(f"TXN-{today}-%"))
    )
    count = count_result.scalar() or 0
    transaction_number = f"TXN-{today}-{count + 1:04d}"

    new_transaction = TransactionModel(
        transaction_number=transaction_number,
        cashier_id=current_user.get('sub', current_user.get('preferred_username', 'unknown')),
        status=TransactionStatus.OPEN,
        notes=transaction.notes,
        subtotal=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total=Decimal("0.00"),
    )

    db.add(new_transaction)
    await db.commit()
    await db.refresh(new_transaction)

    logger.info(f"Transaction created: {transaction_number} by cashier {current_user['username']}")
    return new_transaction


@router.get("/transactions/{transaction_id}")
async def get_transaction(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Get transaction details with line items"""
    result = await db.execute(
        select(TransactionModel).where(TransactionModel.id == transaction_id)
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Load line items separately
    line_items_result = await db.execute(
        select(LineItemModel).where(LineItemModel.transaction_id == transaction_id)
    )
    line_items = line_items_result.scalars().all()

    # Resolve product names so the receipt shows "CBD Oil 20%", not a generic "Product"
    # (one batched lookup, no N+1).
    product_names: dict = {}
    product_ids = {item.product_id for item in line_items if item.product_id is not None}
    if product_ids:
        prod_rows = await db.execute(
            select(ProductModel).where(ProductModel.id.in_(product_ids))
        )
        product_names = {p.id: p.name for p in prod_rows.scalars().all()}

    # Manually construct response to avoid async issues
    return {
        "id": str(transaction.id),
        "transaction_number": transaction.transaction_number,
        "cashier_id": str(transaction.cashier_id),
        "customer_id": str(transaction.customer_id) if transaction.customer_id else None,
        "status": transaction.status.value,
        "payment_method": transaction.payment_method.value if transaction.payment_method else None,
        "subtotal": str(transaction.subtotal),
        "discount_amount": str(transaction.discount_amount),
        "tax_amount": str(transaction.tax_amount),
        "total": str(transaction.total),
        "amount_tendered": str(transaction.amount_tendered) if transaction.amount_tendered else None,
        "change_given": str(transaction.change_given) if transaction.change_given else None,
        "receipt_number": transaction.receipt_number,
        "receipt_pdf_url": transaction.receipt_pdf_url,
        "notes": transaction.notes,
        "created_at": transaction.created_at.isoformat(),
        "updated_at": transaction.updated_at.isoformat(),
        "completed_at": transaction.completed_at.isoformat() if transaction.completed_at else None,
        "line_items": [
            {
                "id": str(item.id),
                "transaction_id": str(item.transaction_id),
                "product_id": str(item.product_id) if item.product_id else None,
                # Real product -> catalog name; custom line -> the name kept in notes.
                "product_name": product_names.get(item.product_id) or (item.notes if item.product_id is None else None),
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "discount_percent": str(item.discount_percent),
                "discount_amount": str(item.discount_amount),
                "line_total": str(item.line_total),
                "notes": item.notes,
                "is_giveaway": bool(item.is_giveaway),
                "created_at": item.created_at.isoformat()
            }
            for item in line_items
        ]
    }


# ================================================================
# 🧹 BL-86: empty-cart reaper (end-of-day cleanup)
# ================================================================
async def reap_stale_open_carts(db: AsyncSession, older_than_hours: int = 12) -> dict:
    """Cancel abandoned empty carts so the report stays clean.

    A real shop leaves dangling OPEN carts behind: a cashier opens a sale and the
    customer walks, or someone mis-taps. We retire only the *truly empty* ones --
    OPEN, zero value, AND no line items -- once they're older than `older_than_hours`.
    We set status=CANCELLED (auditable, the number survives), never delete, and never
    touch a cart that has items or any value. Idempotent: a cart cancelled once won't
    match again. Returns the count + the transaction numbers reaped.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
    has_items = (
        select(LineItemModel.id)
        .where(LineItemModel.transaction_id == TransactionModel.id)
        .exists()
    )
    rows = (await db.execute(
        select(TransactionModel).where(
            TransactionModel.status == TransactionStatus.OPEN,
            TransactionModel.total == 0,
            TransactionModel.created_at < cutoff,
            ~has_items,
        )
    )).scalars().all()

    reaped = []
    now = datetime.now(timezone.utc)
    for t in rows:
        t.status = TransactionStatus.CANCELLED
        t.updated_at = now
        reaped.append(t.transaction_number)
    if rows:
        await db.commit()
    return {
        "cancelled": len(reaped),
        "older_than_hours": older_than_hours,
        "transaction_numbers": reaped,
    }


@router.post("/maintenance/reap-empty-carts")
async def reap_empty_carts(
    older_than_hours: int = 12,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["👔️ pos-manager", "👑️ pos-admin"])),
):
    """Manually run the empty-cart reaper (it also runs hourly in the background).
    Manager/admin only. `older_than_hours` defaults to 12 -- anything still empty and
    open from earlier in the day gets cancelled."""
    result = await reap_stale_open_carts(db, older_than_hours=older_than_hours)
    logger.info(
        f"🧹 Empty-cart reaper (manual by {current_user.get('username')}): {result['cancelled']} cancelled"
    )
    return result


def _inclusive_vat(gross: Decimal) -> Decimal:
    """The VAT *contained within* a gross (VAT-inclusive) amount. Swiss retail prices include
    VAT, so for a gross G at rate r%, the contained VAT = G * r / (100 + r), rounded to cents.
    e.g. CHF 89.90 at 8.1% -> 6.74 VAT, leaving 83.16 net."""
    rate = Decimal(str(get_settings().POS_VAT_RATE))
    return (gross * rate / (Decimal("100") + rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@router.post("/transactions/{transaction_id}/items", response_model=LineItemRead)
async def add_item_to_transaction(
    transaction_id: UUID,
    item: LineItemCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["💰️ pos-cashier", "👔️ pos-manager", "👑️ pos-admin"])),
):
    """Add item to transaction cart (cashier/manager/admin only)"""
    # Verify transaction exists and is open
    trans_result = await db.execute(
        select(TransactionModel).where(TransactionModel.id == transaction_id)
    )
    transaction = trans_result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction.status != TransactionStatus.OPEN:
        raise HTTPException(status_code=400, detail="Transaction is not open")

    if item.product_id is not None:
        # Catalog product: price from the catalog (client unit_price ignored -> no
        # tampering), stock checked + later deducted at checkout.
        prod_result = await db.execute(
            select(ProductModel).where(ProductModel.id == item.product_id)
        )
        product = prod_result.scalar_one_or_none()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if not product.is_active:
            raise HTTPException(status_code=400, detail="Product is inactive")
        if product.stock_quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock. Available: {product.stock_quantity}")

        # A giveaway is a real product handed over free: zero revenue, but stock still
        # leaves (deducted at checkout) so it's tracked for COGS/tax.
        unit_price = Decimal("0.00") if item.is_giveaway else product.price
        line_notes = ("🎁 Treat — on the house" if item.is_giveaway else item.notes)
    else:
        # Custom line (manual catalog entry / product-as-change treat): no catalog
        # product, so the till supplies the price + name. No stock to check or deduct.
        if item.unit_price is None:
            raise HTTPException(status_code=422, detail="Custom line item requires unit_price")
        unit_price = item.unit_price
        # Keep the name for the receipt -- stored in notes (the only free-text column).
        line_notes = item.name or item.notes

    # Line is stored GROSS (qty x unit_price). The cart-wide % discount is applied ONCE
    # at the transaction level below. (Per-line discounting + the running subtotal being
    # re-rounded on each item's commit drifted a cent vs the till's single-rounded total
    # on multi-item discounts.)
    line_gross = unit_price * item.quantity
    line_total = line_gross

    new_line_item = LineItemModel(
        transaction_id=transaction_id,
        product_id=item.product_id,
        quantity=item.quantity,
        unit_price=unit_price,
        discount_percent=item.discount_percent,
        discount_amount=Decimal("0.00"),
        line_total=line_total,
        notes=line_notes,
        is_giveaway=item.is_giveaway,
    )

    db.add(new_line_item)

    # Transaction totals (inclusive VAT: subtotal & total are the GROSS the customer pays).
    # total = round(subtotal * (1 - pct/100)) -- the EXACT formula the till displays, so the
    # charged total always equals what the cashier/customer saw. discount = the reconciling gap.
    transaction.subtotal += line_gross
    keep = (Decimal("100") - item.discount_percent) / Decimal("100")
    transaction.total = (transaction.subtotal * keep).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    transaction.discount_amount = transaction.subtotal - transaction.total
    transaction.tax_amount = _inclusive_vat(transaction.total)
    transaction.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(new_line_item)

    item_label = product.sku if item.product_id is not None else (item.name or "custom")
    logger.info(f"Item added to transaction {transaction.transaction_number}: {item_label} x{item.quantity}")
    return new_line_item


@router.post("/transactions/{transaction_id}/scan", response_model=BarcodeScanResponse)
async def scan_barcode(
    transaction_id: UUID,
    scan: BarcodeScanRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["💰️ pos-cashier", "👔️ pos-manager", "👑️ pos-admin"])),
):
    """Scan barcode and add to transaction (cashier/manager/admin only)"""
    # Find product by barcode
    prod_result = await db.execute(
        select(ProductModel).where(ProductModel.barcode == scan.barcode)
    )
    product = prod_result.scalar_one_or_none()

    if not product:
        return BarcodeScanResponse(
            success=False,
            message=f"Product with barcode '{scan.barcode}' not found"
        )

    if not product.is_active:
        return BarcodeScanResponse(
            success=False,
            message="Product is inactive",
            product=ProductRead.model_validate(product)
        )

    # Add to transaction
    line_item_data = LineItemCreate(
        product_id=product.id,
        quantity=scan.quantity
    )

    try:
        line_item = await add_item_to_transaction(transaction_id, line_item_data, db, current_user)
        return BarcodeScanResponse(
            success=True,
            message=f"Added {scan.quantity}x {product.name}",
            product=ProductRead.model_validate(product),
            line_item=LineItemRead.model_validate(line_item)
        )
    except HTTPException as e:
        return BarcodeScanResponse(
            success=False,
            message=str(e.detail),
            product=ProductRead.model_validate(product)
        )


@router.post("/transactions/{transaction_id}/checkout", response_model=TransactionRead)
async def checkout_transaction(
    transaction_id: UUID,
    checkout: CheckoutRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["💰️ pos-cashier", "👔️ pos-manager", "👑️ pos-admin"])),
):
    """Process checkout and complete transaction (cashier/manager/admin only)"""
    trans_result = await db.execute(
        select(TransactionModel).where(TransactionModel.id == transaction_id)
    )
    transaction = trans_result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction.status != TransactionStatus.OPEN:
        raise HTTPException(status_code=400, detail="Transaction already processed")

    # --- CRM: attach the loyalty member + apply their tier discount (before the cash
    # check, so the member pays the discounted total). The total already reflects any
    # manual cart discount; the tier discount stacks on top of it. ---
    customer = None
    if checkout.customer_id is not None:
        customer = await db.get(CustomerModel, checkout.customer_id)
        if customer is None:
            raise HTTPException(status_code=404, detail="Customer (loyalty member) not found")
        transaction.customer_id = customer.id
        tier_pct = int(customer.tier_discount_percent or 0)
        if tier_pct > 0:
            before = Decimal(str(transaction.total))
            tier_disc = (before * Decimal(tier_pct) / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP)
            transaction.total = before - tier_disc
            transaction.discount_amount = Decimal(str(transaction.discount_amount or 0)) + tier_disc

    # Validate cash payment
    if checkout.payment_method == PaymentMethod.CASH:
        if not checkout.amount_tendered:
            raise HTTPException(status_code=400, detail="Cash payment requires amount_tendered")
        if checkout.amount_tendered < transaction.total:
            raise HTTPException(status_code=400, detail="Insufficient payment amount")
        transaction.change_given = checkout.amount_tendered - transaction.total

    transaction.payment_method = checkout.payment_method
    transaction.amount_tendered = checkout.amount_tendered
    transaction.status = TransactionStatus.COMPLETED
    transaction.completed_at = datetime.now(timezone.utc)
    transaction.updated_at = datetime.now(timezone.utc)

    # Keep VAT consistent with the final gross total (inclusive VAT) so the receipt and the
    # daily Z-report always show the right contained VAT.
    transaction.tax_amount = _inclusive_vat(transaction.total)

    # Generate receipt number
    transaction.receipt_number = f"REC-{transaction.transaction_number}"

    # TODO: Generate PDF receipt and store in MinIO

    # Deduct stock for each line item so inventory is real (floor at 0 -- a mis-count never
    # drives stock negative; Felix sees the zero and reconciles).
    li_result = await db.execute(
        select(LineItemModel).where(LineItemModel.transaction_id == transaction.id)
    )
    for li in li_result.scalars().all():
        if li.product_id is None:
            continue  # custom line (manual/change) -- no catalog stock to deduct
        product = await db.get(ProductModel, li.product_id)
        if product is not None:
            product.stock_quantity = max(0, product.stock_quantity - li.quantity)

    # --- CRM: the member earns points + their record updates (1 credit per CHF paid,
    # floored). Updates lifetime spend, history, average basket, then re-tiers. ---
    if customer is not None:
        paid = Decimal(str(transaction.total))
        earned = int(paid)  # 1 credit per CHF, rounded down
        now = transaction.completed_at or datetime.now(timezone.utc)
        customer.lifetime_spend = Decimal(str(customer.lifetime_spend or 0)) + paid
        customer.purchase_count = (customer.purchase_count or 0) + 1
        if customer.first_purchase is None:
            customer.first_purchase = now
        customer.last_purchase = now
        customer.last_visit = now
        customer.average_basket = (customer.lifetime_spend / customer.purchase_count).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP)
        if earned > 0:
            customer.credits_balance = (customer.credits_balance or 0) + earned
            customer.credits_earned_total = (customer.credits_earned_total or 0) + earned
            db.add(CreditTransactionModel(
                customer_id=customer.id,
                transaction_type=CreditTransactionType.PURCHASE,
                credits=earned,
                balance_after=customer.credits_balance,
                reference_id=transaction.id,
                reference_type="order",
                description=f"Purchase {transaction.transaction_number}: +{earned} credits",
            ))
        customer.recalculate_tier()

    await db.commit()
    await db.refresh(transaction)

    logger.info(f"Transaction completed: {transaction.transaction_number} - Total: {transaction.total} CHF"
                + (f" - member {customer.handle} +{int(Decimal(str(transaction.total)))}cr" if customer else ""))
    return transaction


@router.post("/transactions/{transaction_id}/refund", response_model=TransactionRead)
async def refund_transaction(
    transaction_id: UUID,
    refund: RefundRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["👔️ pos-manager", "👑️ pos-admin"])),
):
    """
    Process a refund for a completed transaction.

    Only managers and admins can process refunds.
    Customer always gets cash back (even if they paid with card).
    This is common in Swiss retail - simpler for accounting.

    Args:
        transaction_id: UUID of completed transaction to refund
        refund: RefundRequest with reason and optional partial amount

    Returns:
        Updated transaction with REFUNDED status
    """
    # Get transaction
    trans_result = await db.execute(
        select(TransactionModel).where(TransactionModel.id == transaction_id)
    )
    transaction = trans_result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction.status != TransactionStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Can only refund completed transactions. Current status: {transaction.status.value}"
        )

    # Calculate refund amount
    refund_amount = refund.partial_amount if refund.partial_amount else transaction.total

    if refund_amount > transaction.total:
        raise HTTPException(
            status_code=400,
            detail=f"Refund amount ({refund_amount}) cannot exceed transaction total ({transaction.total})"
        )

    # Update transaction
    transaction.status = TransactionStatus.REFUNDED
    transaction.updated_at = datetime.now(timezone.utc)

    # Add refund note with cashier info
    cashier_name = current_user.get('preferred_username', 'Unknown')
    refund_note = f"REFUNDED: CHF {refund_amount} cash back | Reason: {refund.reason} | Processed by: {cashier_name} | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"

    if transaction.notes:
        transaction.notes = f"{transaction.notes}\n{refund_note}"
    else:
        transaction.notes = refund_note

    # Full refund -> the goods come back on the shelf (mirror the checkout deduction so
    # inventory stays honest). Partial refunds are money-only: we can't know which items
    # were returned, so stock is left untouched and Felix reconciles by hand if needed.
    if not refund.partial_amount:
        li_result = await db.execute(
            select(LineItemModel).where(LineItemModel.transaction_id == transaction.id)
        )
        for li in li_result.scalars().all():
            if li.product_id is None:
                continue  # custom line (manual/change) -- no catalog stock to restore
            product = await db.get(ProductModel, li.product_id)
            if product is not None:
                product.stock_quantity = (product.stock_quantity or 0) + li.quantity

    await db.commit()
    await db.refresh(transaction)

    logger.info(f"Refund processed: {transaction.transaction_number} - CHF {refund_amount} by {cashier_name}")
    return transaction


# ================================================================
# REPORTING ENDPOINTS
# ================================================================

@router.get("/reports/daily-summary", response_model=DailySummary)
async def get_daily_summary(
    report_date: Optional[str] = None,
    mine: bool = False,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Get daily sales summary - accessible by any POS role (cashiers need it for closeout).

    mine=true filters to the CALLER's own sales (so a cashier's dashboard shows their
    own takings, not the whole store). Default false = store-wide (for managers/Felix)."""
    # Default to today
    if not report_date:
        target_date = date.today()
    else:
        target_date = datetime.strptime(report_date, "%Y-%m-%d").date()

    # Query completed transactions for the day
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())

    conditions = [
        TransactionModel.status == TransactionStatus.COMPLETED,
        TransactionModel.completed_at >= start_of_day,
        TransactionModel.completed_at <= end_of_day,
    ]
    if mine:
        conditions.append(TransactionModel.cashier_id == _uid(current_user))

    result = await db.execute(select(TransactionModel).where(and_(*conditions)))
    transactions = result.scalars().all()

    # Calculate totals
    total_sales = sum(t.total for t in transactions)
    vat_total = sum(t.tax_amount for t in transactions)
    cash_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.CASH)
    visa_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.VISA)
    debit_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.DEBIT)
    twint_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.TWINT)
    bank_transfer_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.BANK_TRANSFER)
    crypto_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.CRYPTO)
    other_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.OTHER)

    # Promotional treats given free today: count + their cost (COGS, for Felix's tax).
    giveaway_count = 0
    giveaway_cost = Decimal("0.00")
    tx_ids = [t.id for t in transactions]
    if tx_ids:
        gv = await db.execute(
            select(LineItemModel.quantity, ProductModel.cost)
            .join(ProductModel, ProductModel.id == LineItemModel.product_id, isouter=True)
            .where(and_(LineItemModel.transaction_id.in_(tx_ids), LineItemModel.is_giveaway == True))
        )
        for qty, cost in gv.all():
            q = int(qty or 0)
            giveaway_count += q
            giveaway_cost += Decimal(str(cost or 0)) * q

    return DailySummary(
        date=target_date.isoformat(),
        total_transactions=len(transactions),
        total_sales=Decimal(str(total_sales)),
        vat_total=Decimal(str(vat_total)),
        cash_total=Decimal(str(cash_total)),
        visa_total=Decimal(str(visa_total)),
        debit_total=Decimal(str(debit_total)),
        twint_total=Decimal(str(twint_total)),
        bank_transfer_total=Decimal(str(bank_transfer_total)),
        crypto_total=Decimal(str(crypto_total)),
        other_total=Decimal(str(other_total)),
        giveaway_count=giveaway_count,
        giveaway_cost=giveaway_cost,
    )


@router.get("/reports/daily-summary.csv")
async def get_daily_summary_csv(
    report_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Daily sales as a Banana Accounting 'Income & Expenses' CSV -- one quoted line per payment
    method that took money. Felix imports it straight into Banana instead of re-typing totals by
    hand. Account + VatCode are intentionally left blank: Felix maps them to his chart of accounts
    in Banana's import dialog (we pre-fill his real codes once he hands them over)."""
    import csv as _csv
    import io as _io

    summary = await get_daily_summary(report_date=report_date, db=db, current_user=current_user)
    by_method = [
        ("Cash", summary.cash_total),
        ("TWINT", summary.twint_total),
        ("Visa", summary.visa_total),
        ("Debit", summary.debit_total),
        ("Bank transfer", summary.bank_transfer_total),
        ("Crypto", summary.crypto_total),
        ("Other", summary.other_total),
    ]
    buf = _io.StringIO()
    writer = _csv.writer(buf, quoting=_csv.QUOTE_ALL)
    writer.writerow(["Date", "Description", "Income", "Expenses", "Account", "VatCode"])
    for label, amount in by_method:
        if amount and amount > 0:
            writer.writerow([summary.date, f"POS daily sales - {label}", f"{amount:.2f}", "", "", ""])
    # Promotional treats given free -- the cost is an expense (COGS) for tax.
    if summary.giveaway_cost and summary.giveaway_cost > 0:
        writer.writerow([summary.date,
                         f"POS giveaways (treats) x{summary.giveaway_count} - cost",
                         "", f"{summary.giveaway_cost:.2f}", "", ""])

    filename = f"banana-{summary.date}.csv"
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ================================================================
# STORE SETTINGS ENDPOINTS
# ================================================================

@router.get("/settings/{store_number}", response_model=StoreSettingsRead)
async def get_store_settings(
    store_number: int = 1,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Get store settings for a specific store number (any POS role).

    Used by frontend to:
    - Get current VAT rate
    - Display company info
    - Load discount limits
    - Show customer loyalty tiers
    """
    result = await db.execute(
        select(StoreSettingsModel).where(StoreSettingsModel.store_number == store_number)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(status_code=404, detail=f"Store #{store_number} not found")

    return settings


@router.put("/settings/{store_number}", response_model=StoreSettingsRead)
async def update_store_settings(
    store_number: int,
    settings_update: StoreSettingsUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_admin()),
):
    """
    Update store settings (admin only).

    Felix can update:
    - VAT rate (changes yearly in Switzerland)
    - Company information
    - Receipt header/footer
    - Discount limits
    - Customer loyalty tiers
    """
    result = await db.execute(
        select(StoreSettingsModel).where(StoreSettingsModel.store_number == store_number)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(status_code=404, detail=f"Store #{store_number} not found")

    # Update only provided fields
    update_data = settings_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    settings.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(settings)

    logger.info(f"Store #{store_number} settings updated by {current_user['username']}")
    return settings


# ================================================================
# SYSTEM PULSE -> the live shop card behind the 📊 in the status bar
# ================================================================
# Replaces a dead /health/dashboard link. One auth'd call returns a snapshot a
# cashier/manager actually cares about: today's takings, members, low stock, open
# drawers, catalog size -- plus the real build stamp + a DB heartbeat.

@router.get("/system/pulse")
async def system_pulse(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Live shop snapshot for the status-bar card. Best-effort: any sub-stat that
    errors degrades to None rather than failing the whole card."""
    db_ok = True
    today = None
    try:
        today = await get_daily_summary(db=db, current_user=current_user)
    except Exception:
        db_ok = False

    async def _count(stmt) -> Optional[int]:
        try:
            return int((await db.execute(stmt)).scalar() or 0)
        except Exception:
            return None

    members = await _count(select(func.count()).select_from(CustomerModel))
    catalog = await _count(
        select(func.count()).select_from(ProductModel).where(ProductModel.is_active == True))
    low_stock = await _count(
        select(func.count()).select_from(ProductModel).where(and_(
            ProductModel.is_active == True,
            ProductModel.stock_quantity <= ProductModel.stock_alert_threshold)))
    open_drawers = await _count(
        select(func.count()).select_from(CashShiftModel).where(
            CashShiftModel.status == CashShiftStatus.OPEN))

    settings = get_settings()
    return {
        "ok": True,
        "db": "ok" if db_ok else "fail",
        "shop": getattr(settings, "STORE_NAME", None) or "Artemis Store",
        "today": {
            "sales": float(today.total_sales) if today else None,
            "transactions": today.total_transactions if today else None,
            "vat": float(today.vat_total) if today else None,
            "giveaways": today.giveaway_count if today else None,
        },
        "members": members,
        "low_stock": low_stock,
        "catalog": catalog,
        "open_drawers": open_drawers,
        "build": {
            "version": get_version(),
            "sha": get_git_sha(),
            "env": getattr(settings, "HX_ENVIRONMENT", "") or "",
        },
    }


# ================================================================
# IN-APP FEEDBACK -> Backlog board (the seatback card, built into the till)
# ================================================================
# A cashier reports a bug/idea from inside the POS; it lands as a real item on
# the SAME backlog board (/backlog) the La Piazza 💬 button feeds. The POS token
# (kc-pos-realm-dev) can't call the bottega feedback endpoint (different realm),
# so this is the POS-native twin -- same BacklogItemModel, tagged for Banco/POS.

class POSFeedback(BaseModel):
    kind: str = "other"      # bug | idea | other
    severity: str = "annoying"  # blocking | annoying | cosmetic  -> backlog priority
    title: str
    body: str = ""
    screenshot: Optional[str] = None       # base64 data-URL (image/*) of the screen
    attachments: Optional[list] = None     # user-attached files [{name,type,data}] -- images & PDFs
    meta: Optional[dict] = None            # auto-collected browser/screen/path context
    diagnostics: Optional[list] = None     # console/network breadcrumbs from the page


# Cap an attached screenshot so a runaway data-URL can't bloat the shared DB
# (~2.2 MB image after base64). Bigger than that -> drop the image, keep the report.
_MAX_SHOT_CHARS = 3_000_000
# User-attached files (device picker / mobile camera). PDFs + images only, each
# capped, and a small ceiling on count + total so a report can't bloat the DB.
_ATTACH_PREFIXES = ("data:image/", "data:application/pdf")
_MAX_ATTACH_CHARS = 6_000_000     # ~4.4 MB per file after base64 (PDFs run bigger)
_MAX_ATTACH_COUNT = 5             # at most this many files per report
_MAX_ATTACH_TOTAL = 18_000_000    # ~13 MB total across all files


def _clean_attachments(raw: list | None) -> list:
    """Keep only well-formed image/PDF data-URLs, within the per-file/count/total
    caps. Malformed or oversized entries are silently dropped -- the report still
    files. Returns a list of {name, type, data} dicts."""
    if not isinstance(raw, list) or not raw:
        return []
    out, total = [], 0
    for a in raw:
        if not isinstance(a, dict):
            continue
        data = a.get("data")
        if not (isinstance(data, str) and data.startswith(_ATTACH_PREFIXES)):
            continue
        if len(data) > _MAX_ATTACH_CHARS or total + len(data) > _MAX_ATTACH_TOTAL:
            continue
        total += len(data)
        name = str(a.get("name") or "attachment")[:200]
        mime = data.split(";", 1)[0][5:] or "application/octet-stream"  # strip "data:"
        out.append({"name": name, "type": mime, "data": data})
        if len(out) >= _MAX_ATTACH_COUNT:
            break
    return out
# One-tap severity -> backlog priority (so the board sorts itself; default MEDIUM).
_SEVERITY_PRIORITY = {
    "blocking": BacklogPriority.HIGH,
    "annoying": BacklogPriority.MEDIUM,
    "cosmetic": BacklogPriority.LOW,
}
_MAX_DIAG = 25  # cap how many breadcrumbs we fold in (the buffer is small anyway)
# Only these context keys are folded into the description (whitelist -- no surprises).
_META_LABELS = [
    ("path", "Screen"), ("referrer", "Came from"), ("app", "POS build"),
    ("user", "User"), ("userAgent", "Browser"), ("platform", "Platform"),
    ("viewport", "Viewport"), ("screen", "Screen size"), ("dpr", "Pixel ratio"),
    ("language", "Locale"), ("tz", "Timezone"), ("online", "Online"),
    ("when", "Client time"),
]


def _format_meta(meta: dict | None) -> str:
    """Render the auto-collected context as a readable block for the board."""
    if not isinstance(meta, dict):
        return ""
    lines = []
    for key, label in _META_LABELS:
        val = meta.get(key)
        if val is None or val == "":
            continue
        lines.append(f"{label}: {str(val)[:300]}")
    return ("\n\n🖥️ Context (auto-collected)\n" + "\n".join(lines)) if lines else ""


def _format_diagnostics(diag: list | None) -> str:
    """Render the console/network breadcrumbs -- the half of a bug a screenshot
    can't show. Each entry is {t: error|warn|net, m: message, ts: epoch_ms}."""
    if not isinstance(diag, list) or not diag:
        return ""
    icons = {"error": "❌", "warn": "⚠️", "net": "🌐"}
    lines = []
    for e in diag[-_MAX_DIAG:]:
        if not isinstance(e, dict):
            continue
        t = str(e.get("t", "")).lower()
        msg = str(e.get("m", "")).replace("\n", " ").strip()[:300]
        if not msg:
            continue
        lines.append(f"{icons.get(t, '•')} [{t or '?'}] {msg}")
    return ("\n\n🔎 Console & network (last events)\n" + "\n".join(lines)) if lines else ""


@router.post("/feedback")
async def pos_feedback(
    f: POSFeedback,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """File a bug/idea from the till onto the shared Backlog board (/backlog).

    Optionally carries an auto-captured screenshot + browser/screen context so a
    report arrives with its own forensics."""
    title = (f.title or "").strip()
    if len(title) < 3:
        raise HTTPException(status_code=400, detail="Give it a short title (3+ characters)")
    user = current_user.get("username") or current_user.get("preferred_username", "unknown")
    kind = (f.kind or "other").lower()
    if kind not in ("bug", "idea", "other"):
        kind = "other"
    item_type = BacklogItemType.BUG_FIX if kind == "bug" else BacklogItemType.BUSINESS_OPS
    severity = (f.severity or "annoying").lower()
    if severity not in _SEVERITY_PRIORITY:
        severity = "annoying"
    priority = _SEVERITY_PRIORITY[severity]

    # next BL number -- same shared sequence as backlog_router / bottega feedback
    next_number = (await db.execute(
        select(func.coalesce(func.max(BacklogItemModel.item_number), 0)))).scalar() + 1

    body = (f.body or "").strip()
    desc = (f"{body}\n\n— filed from Banco POS by {user}" if body
            else f"Filed from Banco POS by {user}")
    desc += _format_meta(f.meta)
    desc += _format_diagnostics(f.diagnostics)

    # Validate + bound the screenshot: must be an image data-URL, under the size cap.
    shot = f.screenshot
    has_shot = False
    if shot and isinstance(shot, str) and shot.startswith("data:image/") and len(shot) <= _MAX_SHOT_CHARS:
        has_shot = True
    elif shot:
        shot = None  # malformed or oversized -> drop the image, still file the report

    # User-attached files (device picker / mobile camera) -- images and PDFs.
    attachments = _clean_attachments(f.attachments)
    if attachments:
        names = ", ".join(a["name"] for a in attachments)
        desc += f"\n\n📎 Attachments ({len(attachments)})\n{names}"

    item = BacklogItemModel(
        item_number=next_number, title=title[:200], description=desc,
        item_type=item_type, application=HelixApplication.HELIXNET,
        priority=priority, created_by=user,
        tags=f"banco,feedback,pos,{kind},{severity}",
        screenshot_data=shot if has_shot else None,
        attachments=json.dumps(attachments) if attachments else None)
    db.add(item)
    await db.commit()
    logger.info(f"BL-{next_number:03d} filed from Banco POS by {user}: {title} "
                f"(severity={severity}, screenshot={has_shot}, attachments={len(attachments)})")
    return {"ok": True, "item_number": next_number, "ref": f"BL-{next_number:03d}",
            "screenshot": has_shot, "attachments": len(attachments),
            "severity": severity, "priority": priority.value}


# ================================================================
# CASH SHIFT -- per-cashier drawer accountability (the lockbox loop)
# ================================================================
# Open with a counted float -> ring sales (tied to cashier_id) -> record any
# non-sale cash (paid-in/out) -> close by counting the drawer. The system shows
# expected vs counted, flags variance beyond the tolerance, and the open/close
# timestamps double as shift hours. Each cashier owns their own drawer.

def _uid(current_user: dict) -> str:
    return current_user.get("sub", current_user.get("preferred_username", "unknown"))


def _uname(current_user: dict) -> str:
    return current_user.get("preferred_username", current_user.get("username", "Unknown"))


async def _open_shift_for(db: AsyncSession, user_id: str) -> Optional[CashShiftModel]:
    return (await db.execute(select(CashShiftModel).where(
        CashShiftModel.user_id == user_id,
        CashShiftModel.status == CashShiftStatus.OPEN,
    ))).scalar_one_or_none()


async def _shift_sales(db: AsyncSession, user_id: str, start: datetime, end: datetime) -> dict:
    """Sum THIS cashier's takings in the shift window. Only CASH touches the drawer;
    card/twint/debit are reported but never counted. Refunds reduce the expected cash."""
    rows = (await db.execute(select(TransactionModel).where(
        TransactionModel.cashier_id == user_id,
        TransactionModel.completed_at >= start,
        TransactionModel.completed_at <= end,
    ))).scalars().all()
    cash_sales = card_sales = cash_refunds = Decimal("0")
    count = 0
    for t in rows:
        total = Decimal(str(t.total or 0))
        if t.status == TransactionStatus.COMPLETED:
            count += 1
            if t.payment_method == PaymentMethod.CASH:
                cash_sales += total
            else:
                card_sales += total
        elif t.status == TransactionStatus.REFUNDED and t.payment_method == PaymentMethod.CASH:
            cash_refunds += total
    return {"cash_sales": money(cash_sales), "card_sales": money(card_sales),
            "cash_refunds": money(cash_refunds), "count": count}


class OpenShiftReq(BaseModel):
    opening_float: Optional[str] = None     # explicit total, OR
    opening_denoms: Optional[dict] = None   # a {face: count} grid (preferred)
    register_id: Optional[str] = None


class PaidReq(BaseModel):
    kind: str           # paid_in | paid_out
    amount: str
    reason: str = ""


class CloseShiftReq(BaseModel):
    counted_cash: Optional[str] = None      # explicit total, OR
    closing_denoms: Optional[dict] = None   # a {face: count} grid
    note: str = ""


@router.post("/shift/open")
async def open_cash_shift(
    req: OpenShiftReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Start your drawer: count the float in. One open shift per cashier."""
    user_id, username = _uid(current_user), _uname(current_user)
    if await _open_shift_for(db, user_id):
        raise HTTPException(status_code=400,
            detail="You already have an open cash shift. Close it first.")
    opening = denoms_total(req.opening_denoms) if req.opening_denoms else money(req.opening_float or 0)
    shift = CashShiftModel(
        user_id=user_id, username=username, store_number=1,
        register_id=req.register_id, opening_float=opening,
        opening_denoms=json.dumps(req.opening_denoms) if req.opening_denoms else None)
    db.add(shift)
    await db.commit()
    await db.refresh(shift)
    logger.info(f"Cash shift OPEN: {username} float={opening}")
    return {"ok": True, "shift_id": str(shift.id), "opening_float": str(opening),
            "opened_at": shift.opened_at.isoformat()}


@router.post("/shift/paid")
async def shift_paid_in_out(
    req: PaidReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Record non-sale cash moving in/out of the drawer (with a reason) so the
    drawer can still balance at close."""
    user_id, username = _uid(current_user), _uname(current_user)
    shift = await _open_shift_for(db, user_id)
    if not shift:
        raise HTTPException(status_code=404, detail="No open cash shift to adjust.")
    kind = (req.kind or "").lower()
    if kind not in ("paid_in", "paid_out"):
        raise HTTPException(status_code=400, detail="kind must be paid_in or paid_out")
    amount = money(req.amount or 0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero.")
    reason = (req.reason or "").strip()
    if len(reason) < 2:
        raise HTTPException(status_code=400, detail="Give a short reason for the cash movement.")
    mv = CashMovementModel(
        shift_id=shift.id,
        kind=CashMovementKind.PAID_IN if kind == "paid_in" else CashMovementKind.PAID_OUT,
        amount=amount, reason=reason[:300], actor=username)
    db.add(mv)
    if kind == "paid_in":
        shift.paid_in_total = money(Decimal(str(shift.paid_in_total or 0)) + amount)
    else:
        shift.paid_out_total = money(Decimal(str(shift.paid_out_total or 0)) + amount)
    await db.commit()
    logger.info(f"Cash {kind}: {username} {amount} ({reason})")
    return {"ok": True, "paid_in_total": str(shift.paid_in_total),
            "paid_out_total": str(shift.paid_out_total)}


@router.get("/shift/current")
async def current_cash_shift(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """The caller's open drawer with the live expected-cash-so-far (or open:false)."""
    user_id = _uid(current_user)
    shift = await _open_shift_for(db, user_id)
    if not shift:
        return {"open": False}
    now = datetime.now(timezone.utc)
    s = await _shift_sales(db, user_id, shift.opened_at, now)
    exp = expected_cash(shift.opening_float, s["cash_sales"],
                        shift.paid_in_total, shift.paid_out_total, s["cash_refunds"])
    return {
        "open": True, "shift_id": str(shift.id),
        "opened_at": shift.opened_at.isoformat(),
        "opening_float": str(money(shift.opening_float)),
        "cash_sales": str(s["cash_sales"]), "card_sales": str(s["card_sales"]),
        "cash_refunds": str(s["cash_refunds"]),
        "paid_in_total": str(money(shift.paid_in_total)),
        "paid_out_total": str(money(shift.paid_out_total)),
        "expected_cash": str(exp), "transaction_count": s["count"],
        "tolerance": str(money(shift.tolerance)),
    }


@router.post("/shift/close")
async def close_cash_shift(
    req: CloseShiftReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Count the drawer out. Computes expected vs counted; a variance beyond the
    tolerance needs a note. Open->close timestamps are the shift hours."""
    user_id, username = _uid(current_user), _uname(current_user)
    shift = await _open_shift_for(db, user_id)
    if not shift:
        raise HTTPException(status_code=404, detail="No open cash shift to close.")
    now = datetime.now(timezone.utc)
    s = await _shift_sales(db, user_id, shift.opened_at, now)
    counted = denoms_total(req.closing_denoms) if req.closing_denoms else money(req.counted_cash or 0)
    exp = expected_cash(shift.opening_float, s["cash_sales"],
                        shift.paid_in_total, shift.paid_out_total, s["cash_refunds"])
    res = close_result(exp, counted, Decimal(str(shift.tolerance)))
    note = (req.note or "").strip()
    if not res["within_tolerance"] and not note:
        raise HTTPException(status_code=400,
            detail=f"Off by CHF {res['variance']}. Add a note to close the shift.")

    shift.cash_sales = s["cash_sales"]; shift.card_sales = s["card_sales"]
    shift.cash_refunds = s["cash_refunds"]; shift.transaction_count = s["count"]
    shift.counted_cash = counted
    shift.closing_denoms = json.dumps(req.closing_denoms) if req.closing_denoms else None
    shift.expected_cash = res["expected"]; shift.variance = res["variance"]
    shift.within_tolerance = res["within_tolerance"]
    shift.variance_note = note or None
    shift.status = CashShiftStatus.CLOSED; shift.closed_at = now
    await db.commit()

    hours = (now - shift.opened_at).total_seconds() / 3600.0
    logger.info(f"Cash shift CLOSE: {username} expected={res['expected']} counted={counted} "
                f"variance={res['variance']} within={res['within_tolerance']}")
    return _shift_report(shift, hours)


def _shift_report(shift: CashShiftModel, hours: float | None = None) -> dict:
    """The one-page per-cashier shift report payload (used by close + /shift/last)."""
    if hours is None and shift.closed_at:
        hours = (shift.closed_at - shift.opened_at).total_seconds() / 3600.0
    return {
        "ok": True, "shift_id": str(shift.id),
        "username": shift.username,
        "opening_float": str(money(shift.opening_float)),
        "cash_sales": str(money(shift.cash_sales or 0)),
        "card_sales": str(money(shift.card_sales or 0)),
        "cash_refunds": str(money(shift.cash_refunds or 0)),
        "paid_in_total": str(money(shift.paid_in_total)),
        "paid_out_total": str(money(shift.paid_out_total)),
        "expected_cash": str(money(shift.expected_cash or 0)),
        "counted_cash": str(money(shift.counted_cash or 0)),
        "variance": str(money(shift.variance or 0)),
        "within_tolerance": bool(shift.within_tolerance),
        "short": (Decimal(str(shift.variance or 0)) < 0),
        "tolerance": str(money(shift.tolerance)),
        "variance_note": shift.variance_note,
        "transaction_count": shift.transaction_count,
        "opened_at": shift.opened_at.isoformat(),
        "closed_at": shift.closed_at.isoformat() if shift.closed_at else None,
        "hours": round(hours, 2) if hours is not None else None,
    }


@router.get("/shift/last")
async def last_cash_shift(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """The caller's most recent CLOSED shift -- so the report screen survives a reload."""
    shift = (await db.execute(select(CashShiftModel).where(
        CashShiftModel.user_id == _uid(current_user),
        CashShiftModel.status == CashShiftStatus.CLOSED,
    ).order_by(CashShiftModel.closed_at.desc()).limit(1))).scalar_one_or_none()
    if not shift:
        return {"ok": False}
    return _shift_report(shift)


@router.get("/shift/{shift_id}/transactions")
async def shift_transactions(
    shift_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """The itemized daily log for one shift -- every transaction the cashier rang in
    the shift window, with its line items. This is what Pam hands Felix: 'I sold
    exactly these N transactions, here is every item.' Owner sees their own; a
    manager/admin can review anyone's."""
    shift = (await db.execute(select(CashShiftModel).where(
        CashShiftModel.id == shift_id))).scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    roles = (current_user.get("user_roles")
             or current_user.get("realm_access", {}).get("roles", []) or [])
    is_mgr = any(("manager" in r or "admin" in r or "developer" in r) for r in roles)
    if shift.user_id != _uid(current_user) and not is_mgr:
        raise HTTPException(status_code=403, detail="Not your shift.")

    end = shift.closed_at or datetime.now(timezone.utc)
    txs = (await db.execute(select(TransactionModel).where(
        TransactionModel.cashier_id == shift.user_id,
        TransactionModel.completed_at >= shift.opened_at,
        TransactionModel.completed_at <= end,
        TransactionModel.status.in_([TransactionStatus.COMPLETED, TransactionStatus.REFUNDED]),
    ).order_by(TransactionModel.completed_at.asc()))).scalars().all()

    tx_ids = [t.id for t in txs]
    items_by_tx: dict = {}
    if tx_ids:
        lis = (await db.execute(select(LineItemModel).where(
            LineItemModel.transaction_id.in_(tx_ids)))).scalars().all()
        pids = {it.product_id for it in lis if it.product_id is not None}
        names: dict = {}
        if pids:
            names = {p.id: p.name for p in (await db.execute(
                select(ProductModel).where(ProductModel.id.in_(pids)))).scalars().all()}
        for it in lis:
            items_by_tx.setdefault(it.transaction_id, []).append({
                "name": names.get(it.product_id) or (it.notes if it.product_id is None else "Item"),
                "quantity": it.quantity,
                "unit_price": str(money(it.unit_price)),
                "line_total": str(money(it.line_total)),
                "is_giveaway": bool(it.is_giveaway),
            })

    out = []
    item_count = 0
    for t in txs:
        items = items_by_tx.get(t.id, [])
        item_count += sum(i["quantity"] for i in items if not i["is_giveaway"])
        out.append({
            "number": t.transaction_number,
            "time": t.completed_at.isoformat() if t.completed_at else None,
            "payment_method": t.payment_method.value if t.payment_method else None,
            "status": t.status.value,
            "total": str(money(t.total)),
            "items": items,
        })
    return {"shift_id": str(shift.id), "username": shift.username,
            "transaction_count": len(out), "item_count": item_count, "transactions": out}


# ================================================================
# HTML WEB UI ROUTES (Sprint 4 - Pam's Interface)
# ================================================================

@html_router.get("/pos", response_class=HTMLResponse, name="pos_login")
async def pos_login(request: Request):
    """
    POS Login Page - Entry point for POS system

    Uses Keycloak OAuth2 Authorization Code Flow:
    1. Redirects to Keycloak for authentication
    2. User enters credentials (pam/helix_pass, felix/helix_pass, etc.)
    3. Keycloak redirects back with authorization code
    4. Frontend exchanges code for JWT token
    5. Token stored in sessionStorage
    6. Redirects to dashboard

    No authentication required (this is the login page)
    """
    return templates.TemplateResponse("pos/login.html", {"request": request})


@html_router.get("/pos/callback")
async def pos_oauth_callback(request: Request, code: str = None, error: str = None):
    """
    OAuth2 Callback - Server-side token exchange (avoids CORS issues)

    Flow:
    1. Keycloak redirects here with ?code=...
    2. Server exchanges code for token (no CORS - server-to-server)
    3. Redirects to dashboard with token in URL fragment
    4. Frontend picks up token and stores it

    This solves the CORS issue where browser can't POST to Keycloak directly.
    """
    import httpx
    from fastapi.responses import RedirectResponse

    if error:
        logger.error(f"OAuth callback error: {error}")
        return RedirectResponse(url="/pos?error=" + error)

    if not code:
        logger.warning("OAuth callback without code")
        return RedirectResponse(url="/pos?error=no_code")

    # Keycloak config
    # IMPORTANT: Use internal Docker URL for server-to-server calls
    keycloak_internal_url = "http://keycloak:8080"
    realm = "kc-pos-realm-dev"
    client_id = "helix_pos_web"

    # Build redirect_uri - MUST match EXACTLY what browser sent to Keycloak
    # request.base_url gives internal URL, but browser used external https URL
    # So we need to reconstruct it from the request headers

    # Get the original host from X-Forwarded headers (set by Traefik)
    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host", "helix.local")

    # Build the exact redirect_uri that the browser sent to Keycloak
    redirect_uri = f"{forwarded_proto}://{forwarded_host}/pos/callback"

    logger.info(f"Token exchange redirect_uri: {redirect_uri}")

    # Use internal URL for the actual HTTP call (no DNS issues inside Docker)
    token_endpoint = f"{keycloak_internal_url}/realms/{realm}/protocol/openid-connect/token"

    try:
        # Server-to-server token exchange (no CORS issues)
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
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return RedirectResponse(url="/pos?error=token_exchange_failed")

            tokens = response.json()
            access_token = tokens.get("access_token")

            if not access_token:
                logger.error("No access_token in response")
                return RedirectResponse(url="/pos?error=no_token")

            # Redirect to dashboard with the tokens in the URL fragment (never sent to
            # the server). Include the refresh_token + expires_in so the till can refresh
            # silently and NEVER hard-logout the cashier mid-sale.
            refresh_token = tokens.get("refresh_token", "")
            expires_in = tokens.get("expires_in", 300)
            logger.info("OAuth callback successful, redirecting to dashboard")
            frag = f"#token={access_token}&refresh={refresh_token}&expires_in={expires_in}"
            return RedirectResponse(url=f"/pos/dashboard{frag}")

    except Exception as e:
        logger.error(f"Token exchange exception: {e}")
        return RedirectResponse(url="/pos?error=token_exchange_error")


@html_router.post("/pos/refresh")
async def pos_token_refresh(request: Request):
    """Silent token refresh -- server-to-server (no CORS, mirrors /pos/callback).

    The till POSTs its refresh_token here when the access token is near/at expiry.
    We exchange it with Keycloak for a fresh access (+ rotated refresh) token so the
    cashier is NEVER hard-logged-out mid-sale. No auth dependency: the access token
    is expired by definition -- the refresh_token IS the credential."""
    import httpx
    from fastapi.responses import JSONResponse

    body = await request.json()
    refresh_token = body.get("refresh_token")
    if not refresh_token:
        return JSONResponse(status_code=400, content={"detail": "missing refresh_token"})

    keycloak_internal_url = "http://keycloak:8080"
    realm = "kc-pos-realm-dev"
    client_id = "helix_pos_web"
    token_endpoint = f"{keycloak_internal_url}/realms/{realm}/protocol/openid-connect/token"

    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.post(
                token_endpoint,
                data={
                    "grant_type": "refresh_token",
                    "client_id": client_id,
                    "refresh_token": refresh_token,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if response.status_code != 200:
            logger.info(f"Token refresh rejected: {response.status_code}")
            return JSONResponse(status_code=401, content={"detail": "refresh_failed"})
        tokens = response.json()
        return JSONResponse(content={
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token", refresh_token),
            "expires_in": tokens.get("expires_in", 300),
        })
    except Exception as e:
        logger.error(f"Token refresh exception: {e}")
        return JSONResponse(status_code=500, content={"detail": "refresh_error"})


@html_router.get("/pos/dashboard", response_class=HTMLResponse, name="pos_dashboard")
async def pos_dashboard(request: Request):
    """
    POS Dashboard - Role-based landing page

    Shows different actions based on user's POS roles:
    - Cashiers (Pam): New Sale, Product Catalog, Close Shift
    - Managers (Ralph/Felix): + Sales Reports, All Transactions
    - Admins (Felix): + User Management, Settings

    Real-time stats (fetched via API):
    - Today's sales total
    - Transaction count
    - Current shift time

    Authentication: Client-side JWT validation (token in sessionStorage)
    """
    return templates.TemplateResponse("pos/dashboard.html", {"request": request})


@html_router.get("/pos/scan", response_class=HTMLResponse, name="pos_scan")
async def pos_scan(request: Request):
    """
    Product Scan & Cart Management - Primary sales interface

    Solves Pam's workflow problem:
    - 3000 products in catalog
    - Most items don't have barcodes
    - Can't remember all codes
    - Needs simple, foolproof workflow

    Three input modes:

    1. BARCODE MODE (default):
       - Auto-focus input field
       - Enter to scan and add
       - For items with barcodes

    2. SEARCH MODE:
       - Fuzzy search by name/description
       - Handles typos
       - For quick lookups

    3. CATALOG MODE (items WITHOUT barcodes):
       Category-based classification:
       - Growing Supplies: A (>CHF 250), B (CHF 21-50), C (<CHF 20)
       - Decorations: A (>CHF 250), B (CHF 21-50), C (<CHF 20)
       - Miscellaneous: A (>CHF 250), B (CHF 21-50), C (<CHF 20)

       Pam workflow:
       1. Customer asks "how much is this?"
       2. Item has no barcode
       3. Pam selects category (e.g., "Growing - B Items")
       4. Enters price (e.g., CHF 35.00)
       5. Optional description
       6. Item added to cart
       7. Felix reviews catalog items later and adds barcodes

    Features:
    - Live cart with quantity adjustment
    - Remove items
    - Discount validation (Cashiers max 10%, Managers unlimited)
    - Swiss VAT calculation (7.7%)
    - Real-time totals
    """
    return templates.TemplateResponse("pos/scan.html", {"request": request})


@html_router.get("/pos/catalog", response_class=HTMLResponse, name="pos_catalog")
async def pos_catalog(request: Request):
    """Catalog management dashboard (BL-88) — manager/admin CRUD over products.

    Surfaces the create / update / soft-delete that already exist in the API:
    search, edit price/stock/picture/reorder fields, discontinue + reactivate,
    create new. Roles are enforced by the API endpoints (manager/admin); this
    page just renders the screen.
    """
    return templates.TemplateResponse("pos/catalog.html", {"request": request})


@html_router.get("/pos/checkout", response_class=HTMLResponse, name="pos_checkout")
async def pos_checkout(request: Request):
    """
    Checkout & Payment - Final transaction confirmation

    Displays:
    - Order summary (all cart items)
    - Price breakdown:
      * Subtotal
      * Discount (if applied)
      * VAT (7.7%)
      * Total

    Payment method selection:
    - Cash (adds to cash drawer)
    - Card (terminal payment - Visa/Mastercard)
    - Mobile (TWINT/Apple Pay/etc)

    Dry-run preview shows what will happen:
    - Cash drawer: +CHF amount (or 0 for card/mobile)
    - Inventory: List of deductions
    - Receipt: Will print
    - Daily total: +CHF amount

    Actions:
    - Cancel: Return to scan
    - Edit Cart: Return to scan
    - Confirm & Complete: Process transaction

    API workflow:
    1. POST /api/v1/pos/transactions (create empty transaction)
    2. POST /api/v1/pos/transactions/{id}/items (add each item)
    3. POST /api/v1/pos/transactions/{id}/checkout (finalize with payment)
    """
    return templates.TemplateResponse("pos/checkout.html", {"request": request})


@html_router.get("/pos/closeout", response_class=HTMLResponse, name="pos_closeout")
async def pos_closeout(request: Request):
    """
    Close Shift / End of Day - Pam's shift closure

    Problem: Pam takes 90 minutes to close shift (paper-based)
    Solution: Automated calculations, visual guidance

    Auto-calculated shift summary:
    - Cashier name (from JWT token)
    - Shift time (start - current)
    - Total transactions
    - Total sales (CHF)
    - Cash sales breakdown
    - Card/Mobile sales breakdown

    Cash drawer count workflow:
    1. Enter notes amount (CHF)
    2. Enter coins amount (CHF)
    3. System calculates total
    4. Shows difference vs expected
    5. Visual feedback:
       - Green check: Perfect match
       - Yellow warning: Difference detected

    Adjustment options:
    - No adjustment: Close immediately
    - Add note: Explain discrepancy (e.g., "Customer returned item")
    - Request manager approval: Escalate to Felix/Ralph

    Goal: Reduce Pam's 90-minute close to <10 minutes

    API call:
    - GET /api/v1/pos/reports/daily-summary (fetch today's stats)
    """
    return templates.TemplateResponse("pos/closeout.html", {"request": request})


@html_router.get("/pos/shift", response_class=HTMLResponse, name="pos_shift")
async def pos_shift(request: Request):
    """My Drawer -- per-cashier cash shift: open with a counted float, paid-in/out,
    close by counting out (expected vs counted, variance, one-page report)."""
    return templates.TemplateResponse("pos/shift.html", {"request": request})


@html_router.get("/pos/cash-count", response_class=HTMLResponse, name="pos_cash_count")
async def pos_cash_count(request: Request):
    """
    Cash Drawer Count - End of Day Reconciliation

    Felix's daily ritual: Count the drawer, verify against POS totals.
    Features denomination-by-denomination counting (Swiss Francs).

    Swiss Franc Denominations:
    - Notes: 200, 100, 50, 20, 10 CHF
    - Coins: 5, 2, 1 CHF, 50/20/10/5 Rappen

    Workflow:
    1. Enter cashier name
    2. Count each denomination
    3. System calculates total
    4. Compare against expected (from POS)
    5. Route variance (bonus/slush/review)
    6. Submit and print summary

    Variance Rules:
    - Perfect (0): +1 bonus point for cashier
    - Small over (<0.50): Goes to cashier bonus pool
    - Small under (<0.50): Goes to slush fund
    - Large variance: Manager review required

    URL: https://helix.local/pos/cash-count
    """
    return templates.TemplateResponse("pos/cash_count.html", {"request": request})


@html_router.get("/pos/customer-lookup", response_class=HTMLResponse, name="pos_customer_lookup")
async def pos_customer_lookup(request: Request):
    """
    Customer Lookup - Find CRACK profiles for checkout recognition

    The "Larry/Poppie" problem solved:
    - Customer walks in, says "I'm Poppie"
    - Cashier searches by handle, Instagram, email, or phone
    - Profile loads with tier discount, credits, CRACK level
    - Apply to checkout for personalized pricing

    Features:
    - Search by handle, @instagram, email, phone
    - Profile card with loyalty tier (Bronze→Diamond)
    - CRACK level display (Seedling→Oracle)
    - Credits balance and redeemable vouchers
    - Favorites and suggestions
    - Birthday/tier alerts
    - Quick-add new customer form
    - Recent customers grid

    Workflow:
    1. Search "poppie" or "@poppie_420"
    2. See Larry's profile (Gold tier, 247 credits)
    3. Click "Use for Checkout"
    4. Redirect to scan with 15% discount applied

    URL: https://helix.local/pos/customer-lookup
    """
    return templates.TemplateResponse("pos/customer_lookup.html", {"request": request})


@html_router.get("/pos/kb-approvals", response_class=HTMLResponse, name="pos_kb_approvals")
async def pos_kb_approvals(request: Request):
    """
    KB Approvals - Owner's knowledge contribution review

    "Knowledge is the gold" - KB-001

    CRACKs write KBs (Knowledge Base articles) about:
    - Recipes (CBD tanning butter, coconut extract method)
    - Protocols (Purple Power Sleep Protocol)
    - Guides (Grinder Maintenance 101)
    - Lab reports (tested formulas)

    Owner Approval Workflow:
    1. CRACK submits KB
    2. Owner sends to other CRACKs for review
    3. CRACKs rate and recommend (or flag concerns)
    4. Owner sees review summary
    5. 1-click approve or batch "Select All"
    6. Credits awarded to author

    Credit Calculation:
    - Base: 100 credits
    - With images: +25
    - With video: +50
    - With BOM/Recipe: +75
    - With lab report: +100
    - Featured bonus: +250

    Features:
    - Pending/In Review/Approved tabs
    - Quality badges (images, video, BOM, lab)
    - JH chapter reference display
    - CRACK review summary
    - Batch select and approve
    - Preview modal with full content
    - Feature KB button (+250 bonus)

    URL: https://helix.local/pos/kb-approvals
    """
    return templates.TemplateResponse("pos/kb_approvals.html", {"request": request})


@html_router.get("/pos/receipt/{transaction_id}", response_class=HTMLResponse, name="pos_receipt")
async def pos_receipt(request: Request, transaction_id: UUID):
    """
    Receipt View & Print - Display completed transaction receipt

    A4-optimized printable receipt for customer.
    Auto-loads transaction data and store settings.

    Features:
    - Company header (logo, name, address, VAT number)
    - Transaction details (date, time, cashier, receipt#)
    - Line items table
    - Totals breakdown (subtotal, discount, VAT, total)
    - Payment method
    - PAID watermark
    - Print button (window.print())
    - Reprint anytime

    Used for:
    - Auto-display after checkout
    - Reprint from transaction history
    - Closeout review (Pam checks all receipts)
    - Customer requests copy

    Pam's workflow:
    1. Complete transaction → receipt auto-displays
    2. Click Print → browser print dialog
    3. Customer gets receipt
    4. Receipt saved in history for reprint

    Felix's workflow (at closeout):
    1. Review all receipts
    2. Spot errors (e.g., CHF 25 should be CHF 250)
    3. Call Pam for explanation
    4. Note for Banana journal entry
    """
    return templates.TemplateResponse("pos/receipt.html", {"request": request})


@html_router.get("/pos/products", response_class=HTMLResponse, name="pos_products")
async def pos_products(request: Request):
    """
    Product Catalog Browser - Browse all products

    Future features:
    - Category filters
    - Search bar
    - Sort by name/price/category
    - Quick add to cart

    For now: Redirects to scan page
    """
    return templates.TemplateResponse("pos/scan.html", {"request": request})


@html_router.get("/pos/search", response_class=HTMLResponse, name="pos_search")
async def pos_search(request: Request):
    """
    Fast Product Search - Instant search with 7,442+ products

    Features:
    - Fuzzy name search (trigram similarity)
    - Instant barcode lookup (<5ms)
    - Category filtering
    - Full-text search (German language)
    - Product images
    - Add to cart functionality

    Barcode Scanner Support:
    - Auto-detects fast sequential input
    - Instant product lookup on scan
    - Auto-adds to cart on exact match

    URL: https://helix-platform.local/pos/search
    """
    return templates.TemplateResponse("pos/search.html", {"request": request})


@html_router.get("/pos/reports", response_class=HTMLResponse, name="pos_reports")
async def pos_reports(request: Request):
    """
    Sales Reports - Manager/Admin analytics

    Future features:
    - Daily/Weekly/Monthly charts
    - Top products
    - Cashier performance
    - Payment method breakdown
    - Category analysis
    """
    return templates.TemplateResponse("pos/reports.html", {"request": request})


@html_router.get("/pos/transactions", response_class=HTMLResponse, name="pos_transactions")
async def pos_transactions(request: Request):
    """
    Transaction History - View all sales transactions

    Critical for Pam's closeout workflow:
    - Review all today's transactions
    - Click to view receipt
    - Reprint any receipt
    - Spot errors (e.g., CHF 25 should be CHF 250)

    Features:
    - Filter by date (default: today)
    - Filter by status (completed, open, voided)
    - Filter by payment method (cash, card, mobile)
    - Summary stats (count, total sales, cash vs card)
    - Click transaction to view receipt
    - Reprint button (opens in new tab)

    Manager features:
    - View all cashiers' transactions
    - Filter by cashier
    - Void transaction (with approval)

    Pam's workflow at closeout:
    1. Click "Transaction History" from dashboard
    2. Review all today's receipts
    3. Spot mistake: "That CHF 25 should be CHF 250!"
    4. Call Felix: "Hey boss, line 15 is wrong"
    5. Felix: "OK, note it for Banana adjustment"
    """
    return templates.TemplateResponse("pos/transactions.html", {"request": request})


@html_router.get("/pos/admin", response_class=HTMLResponse, name="pos_admin")
async def pos_admin(request: Request):
    """
    User Management - Admin role management

    Future features:
    - List all users
    - Assign/remove POS roles
    - View user activity
    - Enable/disable users

    For now: Placeholder
    """
    return templates.TemplateResponse("pos/dashboard.html", {"request": request})


@html_router.get("/pos/settings", response_class=HTMLResponse, name="pos_settings")
async def pos_settings(request: Request):
    """
    POS System Settings - Admin configuration

    Future features:
    - Tax rate settings
    - Receipt header/footer
    - Printer configuration
    - Discount limits
    - Category management

    For now: Placeholder
    """
    return templates.TemplateResponse("pos/dashboard.html", {"request": request})
