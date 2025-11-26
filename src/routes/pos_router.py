# File: src/routes/pos_router.py
"""
POS (Point of Sale) API Router for Felix's Artemis Store.
Handles products, transactions, scanning, and checkout.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timezone, date
from decimal import Decimal
from uuid import UUID
from typing import Optional

from src.db.database import get_db_session
from src.db.models import (
    ProductModel,
    TransactionModel,
    LineItemModel,
    UserModel,
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
    DailySummary,
)
# Real Keycloak authentication with RBAC
from src.core.keycloak_auth import (
    require_roles,
    require_any_pos_role,
    require_admin,
    require_manager_or_admin,
)
# REFERENCE ONLY: Mock auth kept for comparison
# from src.core.mock_auth import get_mock_user as get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pos", tags=["POS"])


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
        cashier_id=current_user.id,
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
