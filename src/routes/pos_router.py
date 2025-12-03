# File: src/routes/pos_router.py
"""
POS (Point of Sale) API Router for Felix's Artemis Store.
Handles products, transactions, scanning, and checkout.

Sprint 4: Added HTML interface routes for Pam's POS system.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timezone, date
from decimal import Decimal
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
    TransactionStatus,
    PaymentMethod,
)
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
    db: AsyncSession = Depends(get_db_session),
):
    """
    Fast product search using PostgreSQL full-text search and trigram similarity.

    - Instant barcode lookup (exact match, <5ms)
    - Fuzzy name search (trigram similarity)
    - Full-text search (German language)
    - Category filtering

    No auth required for search (public catalog).
    """
    from sqlalchemy import text

    if not q and not category:
        # Return empty if no search term
        return []

    # Use the PostgreSQL search_products function
    query = text("""
        SELECT id, sku, barcode, name, category, price, stock_quantity, image_url, relevance
        FROM search_products(:search_term, :category_filter, :limit_rows)
    """)

    result = await db.execute(query, {
        "search_term": q if q else None,
        "category_filter": category,
        "limit_rows": limit
    })

    rows = result.fetchall()

    return [
        {
            "id": str(row.id),
            "sku": row.sku,
            "barcode": row.barcode,
            "name": row.name,
            "category": row.category,
            "price": float(row.price) if row.price else 0,
            "stock_quantity": row.stock_quantity or 0,
            "image_url": row.image_url,
            "relevance": float(row.relevance) if row.relevance else 0
        }
        for row in rows
    ]


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
# TRANSACTION ENDPOINTS (Cart/Checkout)
# ================================================================

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
                "product_id": str(item.product_id),
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "discount_percent": str(item.discount_percent),
                "discount_amount": str(item.discount_amount),
                "line_total": str(item.line_total),
                "notes": item.notes,
                "created_at": item.created_at.isoformat()
            }
            for item in line_items
        ]
    }


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

    # Get product and check stock
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

    # Calculate line item totals
    unit_price = product.price
    discount_amount = (unit_price * item.quantity * item.discount_percent) / Decimal("100")
    line_total = (unit_price * item.quantity) - discount_amount

    new_line_item = LineItemModel(
        transaction_id=transaction_id,
        product_id=item.product_id,
        quantity=item.quantity,
        unit_price=unit_price,
        discount_percent=item.discount_percent,
        discount_amount=discount_amount,
        line_total=line_total,
        notes=item.notes,
    )

    db.add(new_line_item)

    # Update transaction totals
    transaction.subtotal += line_total
    transaction.total = transaction.subtotal - transaction.discount_amount + transaction.tax_amount
    transaction.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(new_line_item)

    logger.info(f"Item added to transaction {transaction.transaction_number}: {product.sku} x{item.quantity}")
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

    # Generate receipt number
    transaction.receipt_number = f"REC-{transaction.transaction_number}"

    # TODO: Generate PDF receipt and store in MinIO
    # TODO: Deduct stock from products

    await db.commit()
    await db.refresh(transaction)

    logger.info(f"Transaction completed: {transaction.transaction_number} - Total: {transaction.total} CHF")
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
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["👔️ pos-manager", "📊️ pos-auditor", "👑️ pos-admin"])),
):
    """Get daily sales summary for Banana export (manager/auditor/admin only)"""
    # Default to today
    if not report_date:
        target_date = date.today()
    else:
        target_date = datetime.strptime(report_date, "%Y-%m-%d").date()

    # Query completed transactions for the day
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())

    result = await db.execute(
        select(TransactionModel).where(
            and_(
                TransactionModel.status == TransactionStatus.COMPLETED,
                TransactionModel.completed_at >= start_of_day,
                TransactionModel.completed_at <= end_of_day
            )
        )
    )
    transactions = result.scalars().all()

    # Calculate totals
    total_sales = sum(t.total for t in transactions)
    cash_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.CASH)
    visa_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.VISA)
    debit_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.DEBIT)
    twint_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.TWINT)
    crypto_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.CRYPTO)
    other_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.OTHER)

    return DailySummary(
        date=target_date.isoformat(),
        total_transactions=len(transactions),
        total_sales=Decimal(str(total_sales)),
        cash_total=Decimal(str(cash_total)),
        visa_total=Decimal(str(visa_total)),
        debit_total=Decimal(str(debit_total)),
        twint_total=Decimal(str(twint_total)),
        crypto_total=Decimal(str(crypto_total)),
        other_total=Decimal(str(other_total)),
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

    For now: Placeholder
    """
    return templates.TemplateResponse("pos/dashboard.html", {"request": request})


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
