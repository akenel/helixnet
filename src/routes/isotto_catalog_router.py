# File: src/routes/isotto_catalog_router.py
"""
ISOTTO Sport Catalog Router -- Suppliers, Products, Stock.
The merch catalog for custom printing.

Prefix: /api/v1/print-shop/catalog

"Famous Guy knows his suppliers."
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
from collections import defaultdict
from uuid import UUID
from typing import Optional
from pathlib import Path

from src.db.database import get_db_session
from src.db.models.isotto_supplier_model import IsottoSupplierModel
from src.db.models.isotto_catalog_model import IsottoCatalogProductModel, IsottoMerchCategory
from src.db.models.isotto_catalog_stock_model import IsottoCatalogStockModel
from src.db.models.isotto_purchase_order_model import IsottoPurchaseOrderModel, IsottoPOStatus
from src.db.models.isotto_artwork_model import IsottoArtworkModel
from src.db.models.isotto_order_model import IsottoOrderModel
from src.db.models.isotto_order_line_item_model import IsottoOrderLineItemModel, LineItemStatus
from src.schemas.isotto_schema import (
    IsottoSupplierCreate, IsottoSupplierUpdate, IsottoSupplierRead,
    IsottoCatalogProductCreate, IsottoCatalogProductUpdate, IsottoCatalogProductRead,
    IsottoStockRead, IsottoStockBulkUpdate, IsottoStockReceive,
    IsottoPurchaseOrderCreate, IsottoPurchaseOrderUpdate, IsottoPurchaseOrderRead,
    IsottoPOStatusUpdate, IsottoPOGenerateResult,
    IsottoArtworkCreate, IsottoArtworkUpdate, IsottoArtworkRead,
)
from src.core.keycloak_auth import require_roles

logger = logging.getLogger(__name__)

# API Router
router = APIRouter(prefix="/api/v1/print-shop/catalog", tags=["ISOTTO Sport - Catalog"])

# HTML Router (catalog + supplier pages)
html_router = APIRouter(tags=["ISOTTO Sport - Catalog UI"])

# Jinja2 templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


# ================================================================
# AUTH HELPERS
# ================================================================

def require_any_isotto_role():
    return require_roles([
        "isotto-counter", "isotto-designer", "isotto-operator",
        "isotto-manager", "isotto-admin",
    ])


def require_isotto_manager_or_admin():
    return require_roles(["isotto-manager", "isotto-admin"])


# ================================================================
# SUPPLIER ENDPOINTS
# ================================================================

@router.post("/suppliers", response_model=IsottoSupplierRead, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier: IsottoSupplierCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_isotto_manager_or_admin()),
):
    """Create a new supplier (manager/admin only)"""
    # Check for duplicate code
    existing = await db.execute(
        select(IsottoSupplierModel).where(IsottoSupplierModel.code == supplier.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Supplier code '{supplier.code}' already exists")

    new_supplier = IsottoSupplierModel(**supplier.model_dump())
    db.add(new_supplier)
    await db.commit()
    await db.refresh(new_supplier)

    logger.info(f"ISOTTO supplier created: {new_supplier.name} ({new_supplier.code}) by {current_user['username']}")
    return new_supplier


@router.get("/suppliers", response_model=list[IsottoSupplierRead])
async def list_suppliers(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """List all suppliers"""
    query = select(IsottoSupplierModel)
    if active_only:
        query = query.where(IsottoSupplierModel.is_active == True)
    query = query.order_by(IsottoSupplierModel.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/suppliers/{supplier_id}", response_model=IsottoSupplierRead)
async def get_supplier(
    supplier_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """Get a single supplier"""
    result = await db.execute(
        select(IsottoSupplierModel).where(IsottoSupplierModel.id == supplier_id)
    )
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.put("/suppliers/{supplier_id}", response_model=IsottoSupplierRead)
async def update_supplier(
    supplier_id: UUID,
    supplier_update: IsottoSupplierUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_isotto_manager_or_admin()),
):
    """Update supplier (manager/admin only)"""
    result = await db.execute(
        select(IsottoSupplierModel).where(IsottoSupplierModel.id == supplier_id)
    )
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    update_data = supplier_update.model_dump(exclude_unset=True)

    # Check code uniqueness if changing
    if "code" in update_data and update_data["code"] != supplier.code:
        existing = await db.execute(
            select(IsottoSupplierModel).where(IsottoSupplierModel.code == update_data["code"])
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Supplier code '{update_data['code']}' already exists")

    for field, value in update_data.items():
        setattr(supplier, field, value)

    supplier.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(supplier)

    logger.info(f"ISOTTO supplier updated: {supplier.name} by {current_user['username']}")
    return supplier


@router.delete("/suppliers/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(
    supplier_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_isotto_manager_or_admin()),
):
    """Deactivate supplier (soft delete)"""
    result = await db.execute(
        select(IsottoSupplierModel).where(IsottoSupplierModel.id == supplier_id)
    )
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    supplier.is_active = False
    supplier.updated_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info(f"ISOTTO supplier deactivated: {supplier.name} by {current_user['username']}")


# ================================================================
# CATALOG PRODUCT ENDPOINTS
# ================================================================

@router.post("/products", response_model=IsottoCatalogProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: IsottoCatalogProductCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_isotto_manager_or_admin()),
):
    """Create a new catalog product (manager/admin only)"""
    # Verify supplier exists
    supplier_result = await db.execute(
        select(IsottoSupplierModel).where(IsottoSupplierModel.id == product.supplier_id)
    )
    if not supplier_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Supplier not found")

    new_product = IsottoCatalogProductModel(**product.model_dump())
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    logger.info(f"ISOTTO catalog product created: {new_product.name} by {current_user['username']}")
    return new_product


@router.get("/products", response_model=list[IsottoCatalogProductRead])
async def list_products(
    category: Optional[str] = None,
    supplier_id: Optional[UUID] = None,
    search: Optional[str] = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """List catalog products with filters"""
    query = select(IsottoCatalogProductModel)

    if active_only:
        query = query.where(IsottoCatalogProductModel.is_active == True)

    if category:
        try:
            cat = IsottoMerchCategory(category)
            query = query.where(IsottoCatalogProductModel.category == cat)
        except ValueError:
            pass

    if supplier_id:
        query = query.where(IsottoCatalogProductModel.supplier_id == supplier_id)

    if search:
        query = query.where(
            IsottoCatalogProductModel.name.ilike(f"%{search}%") |
            IsottoCatalogProductModel.tags.ilike(f"%{search}%") |
            IsottoCatalogProductModel.supplier_product_code.ilike(f"%{search}%")
        )

    query = query.order_by(IsottoCatalogProductModel.name).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/products/{product_id}", response_model=IsottoCatalogProductRead)
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """Get a single catalog product"""
    result = await db.execute(
        select(IsottoCatalogProductModel).where(IsottoCatalogProductModel.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/products/{product_id}", response_model=IsottoCatalogProductRead)
async def update_product(
    product_id: UUID,
    product_update: IsottoCatalogProductUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_isotto_manager_or_admin()),
):
    """Update catalog product (manager/admin only)"""
    result = await db.execute(
        select(IsottoCatalogProductModel).where(IsottoCatalogProductModel.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    product.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(product)

    logger.info(f"ISOTTO catalog product updated: {product.name} by {current_user['username']}")
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_isotto_manager_or_admin()),
):
    """Deactivate product (soft delete)"""
    result = await db.execute(
        select(IsottoCatalogProductModel).where(IsottoCatalogProductModel.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_active = False
    product.updated_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info(f"ISOTTO catalog product deactivated: {product.name} by {current_user['username']}")


# ================================================================
# STOCK ENDPOINTS
# ================================================================

@router.get("/products/{product_id}/stock", response_model=list[IsottoStockRead])
async def get_product_stock(
    product_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """Get stock levels for a product (all color/size combos)"""
    # Verify product exists
    product_result = await db.execute(
        select(IsottoCatalogProductModel).where(IsottoCatalogProductModel.id == product_id)
    )
    if not product_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Product not found")

    result = await db.execute(
        select(IsottoCatalogStockModel)
        .where(IsottoCatalogStockModel.product_id == product_id)
        .order_by(IsottoCatalogStockModel.color, IsottoCatalogStockModel.size)
    )
    return result.scalars().all()


@router.put("/products/{product_id}/stock", response_model=list[IsottoStockRead])
async def bulk_update_stock(
    product_id: UUID,
    stock_update: IsottoStockBulkUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_isotto_manager_or_admin()),
):
    """Bulk update stock levels for a product (upsert color/size combos)"""
    # Verify product exists
    product_result = await db.execute(
        select(IsottoCatalogProductModel).where(IsottoCatalogProductModel.id == product_id)
    )
    if not product_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Product not found")

    for entry in stock_update.entries:
        # Check if entry exists
        existing = await db.execute(
            select(IsottoCatalogStockModel).where(
                IsottoCatalogStockModel.product_id == product_id,
                IsottoCatalogStockModel.color == entry.color,
                IsottoCatalogStockModel.size == entry.size,
            )
        )
        stock = existing.scalar_one_or_none()

        if stock:
            stock.quantity_on_hand = entry.quantity_on_hand
            stock.quantity_reserved = entry.quantity_reserved
            stock.updated_at = datetime.now(timezone.utc)
        else:
            stock = IsottoCatalogStockModel(
                product_id=product_id,
                color=entry.color,
                size=entry.size,
                quantity_on_hand=entry.quantity_on_hand,
                quantity_reserved=entry.quantity_reserved,
            )
            db.add(stock)

    await db.commit()

    # Return updated stock
    result = await db.execute(
        select(IsottoCatalogStockModel)
        .where(IsottoCatalogStockModel.product_id == product_id)
        .order_by(IsottoCatalogStockModel.color, IsottoCatalogStockModel.size)
    )
    return result.scalars().all()


@router.post("/products/{product_id}/stock/receive", response_model=IsottoStockRead)
async def receive_stock(
    product_id: UUID,
    receive: IsottoStockReceive,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """Receive stock delivery (increment quantity_on_hand)"""
    # Verify product exists
    product_result = await db.execute(
        select(IsottoCatalogProductModel).where(IsottoCatalogProductModel.id == product_id)
    )
    if not product_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Product not found")

    # Find or create stock entry
    existing = await db.execute(
        select(IsottoCatalogStockModel).where(
            IsottoCatalogStockModel.product_id == product_id,
            IsottoCatalogStockModel.color == receive.color,
            IsottoCatalogStockModel.size == receive.size,
        )
    )
    stock = existing.scalar_one_or_none()

    if stock:
        stock.quantity_on_hand += receive.quantity
        stock.updated_at = datetime.now(timezone.utc)
    else:
        stock = IsottoCatalogStockModel(
            product_id=product_id,
            color=receive.color,
            size=receive.size,
            quantity_on_hand=receive.quantity,
        )
        db.add(stock)

    await db.commit()
    await db.refresh(stock)

    logger.info(f"ISOTTO stock received: +{receive.quantity} {receive.color}/{receive.size} for product {product_id} by {current_user['username']}")
    return stock


# ================================================================
# PURCHASE ORDER ENDPOINTS
# ================================================================

async def _generate_po_number(db: AsyncSession) -> str:
    """Generate next PO number: IPO-YYYYMMDD-NNNN"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"IPO-{today}-"

    result = await db.execute(
        select(func.count(IsottoPurchaseOrderModel.id))
        .where(IsottoPurchaseOrderModel.po_number.like(f"{prefix}%"))
    )
    count = result.scalar() or 0
    return f"{prefix}{(count + 1):04d}"


@router.post("/purchase-orders", response_model=IsottoPurchaseOrderRead, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po: IsottoPurchaseOrderCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_isotto_manager_or_admin()),
):
    """Create a purchase order (manager/admin only)"""
    # Verify supplier
    supplier_result = await db.execute(
        select(IsottoSupplierModel).where(IsottoSupplierModel.id == po.supplier_id)
    )
    supplier = supplier_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    po_number = await _generate_po_number(db)

    # Calculate financials
    line_items_data = [item.model_dump() for item in po.line_items]
    for item in line_items_data:
        item["line_total"] = float(Decimal(str(item["quantity"])) * Decimal(str(item["unit_price"])))
        # Convert Decimal fields to float for JSONB
        item["unit_price"] = float(item["unit_price"])

    subtotal = Decimal(str(sum(item["line_total"] for item in line_items_data)))
    vat_rate = Decimal("22.00")
    vat_amount = (subtotal * vat_rate / Decimal("100")).quantize(Decimal("0.01"))
    total = subtotal + vat_amount

    related_ids = [str(oid) for oid in (po.related_order_ids or [])]

    new_po = IsottoPurchaseOrderModel(
        po_number=po_number,
        supplier_id=po.supplier_id,
        line_items=line_items_data,
        subtotal=subtotal,
        vat_rate=vat_rate,
        vat_amount=vat_amount,
        total=total,
        status=IsottoPOStatus.DRAFT,
        expected_delivery=po.expected_delivery,
        related_order_ids=related_ids,
        notes=po.notes,
        created_by=current_user["username"],
    )
    db.add(new_po)
    await db.commit()
    await db.refresh(new_po)

    logger.info(f"ISOTTO PO created: {po_number} for supplier {supplier.name} by {current_user['username']}")
    return new_po


@router.get("/purchase-orders", response_model=list[IsottoPurchaseOrderRead])
async def list_purchase_orders(
    status_filter: Optional[str] = None,
    supplier_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """List purchase orders with optional filters"""
    query = select(IsottoPurchaseOrderModel)

    if status_filter:
        try:
            po_status = IsottoPOStatus(status_filter)
            query = query.where(IsottoPurchaseOrderModel.status == po_status)
        except ValueError:
            pass

    if supplier_id:
        query = query.where(IsottoPurchaseOrderModel.supplier_id == supplier_id)

    query = query.order_by(IsottoPurchaseOrderModel.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/purchase-orders/{po_id}", response_model=IsottoPurchaseOrderRead)
async def get_purchase_order(
    po_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """Get a single purchase order"""
    result = await db.execute(
        select(IsottoPurchaseOrderModel).where(IsottoPurchaseOrderModel.id == po_id)
    )
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po


@router.put("/purchase-orders/{po_id}", response_model=IsottoPurchaseOrderRead)
async def update_purchase_order(
    po_id: UUID,
    po_update: IsottoPurchaseOrderUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_isotto_manager_or_admin()),
):
    """Update a purchase order (manager/admin only)"""
    result = await db.execute(
        select(IsottoPurchaseOrderModel).where(IsottoPurchaseOrderModel.id == po_id)
    )
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    update_data = po_update.model_dump(exclude_unset=True)

    # Recalculate financials if line items changed
    if "line_items" in update_data and update_data["line_items"] is not None:
        line_items_data = [item.model_dump() for item in po_update.line_items]
        for item in line_items_data:
            item["line_total"] = float(Decimal(str(item["quantity"])) * Decimal(str(item["unit_price"])))
            item["unit_price"] = float(item["unit_price"])
        update_data["line_items"] = line_items_data
        subtotal = Decimal(str(sum(item["line_total"] for item in line_items_data)))
        po.subtotal = subtotal
        po.vat_amount = (subtotal * po.vat_rate / Decimal("100")).quantize(Decimal("0.01"))
        po.total = po.subtotal + po.vat_amount

    for field, value in update_data.items():
        setattr(po, field, value)

    po.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(po)

    logger.info(f"ISOTTO PO updated: {po.po_number} by {current_user['username']}")
    return po


@router.patch("/purchase-orders/{po_id}/status", response_model=IsottoPurchaseOrderRead)
async def update_po_status(
    po_id: UUID,
    status_update: IsottoPOStatusUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_isotto_manager_or_admin()),
):
    """Update PO status. When RECEIVED, automatically updates stock and line items."""
    result = await db.execute(
        select(IsottoPurchaseOrderModel).where(IsottoPurchaseOrderModel.id == po_id)
    )
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    old_status = po.status
    po.status = status_update.status
    po.updated_at = datetime.now(timezone.utc)

    if status_update.status == IsottoPOStatus.RECEIVED:
        po.actual_delivery = date.today()
        # Auto-update stock levels from PO line items
        for item in (po.line_items or []):
            product_code = item.get("product_code", "")
            color = item.get("color", "")
            size = item.get("size", "")
            qty = item.get("quantity", 0)

            if not color or not size or qty <= 0:
                continue

            # Find the catalog product by supplier code
            prod_result = await db.execute(
                select(IsottoCatalogProductModel).where(
                    and_(
                        IsottoCatalogProductModel.supplier_id == po.supplier_id,
                        IsottoCatalogProductModel.supplier_product_code == product_code,
                    )
                )
            )
            catalog_product = prod_result.scalar_one_or_none()
            if not catalog_product:
                continue

            # Upsert stock entry
            stock_result = await db.execute(
                select(IsottoCatalogStockModel).where(
                    and_(
                        IsottoCatalogStockModel.product_id == catalog_product.id,
                        IsottoCatalogStockModel.color == color,
                        IsottoCatalogStockModel.size == size,
                    )
                )
            )
            stock = stock_result.scalar_one_or_none()
            if stock:
                stock.quantity_on_hand += qty
                stock.updated_at = datetime.now(timezone.utc)
            else:
                db.add(IsottoCatalogStockModel(
                    product_id=catalog_product.id,
                    color=color,
                    size=size,
                    quantity_on_hand=qty,
                ))

            # Advance related line items: STOCK_ORDERED -> STOCK_RECEIVED
            for order_id_str in (po.related_order_ids or []):
                items_result = await db.execute(
                    select(IsottoOrderLineItemModel).where(
                        and_(
                            IsottoOrderLineItemModel.order_id == order_id_str,
                            IsottoOrderLineItemModel.catalog_product_id == catalog_product.id,
                            IsottoOrderLineItemModel.color == color,
                            IsottoOrderLineItemModel.size == size,
                            IsottoOrderLineItemModel.status == LineItemStatus.STOCK_ORDERED,
                        )
                    )
                )
                for line_item in items_result.scalars().all():
                    line_item.status = LineItemStatus.STOCK_RECEIVED
                    line_item.updated_at = datetime.now(timezone.utc)

        logger.info(f"ISOTTO PO {po.po_number} RECEIVED - stock updated, line items advanced")

    await db.commit()
    await db.refresh(po)

    logger.info(f"ISOTTO PO {po.po_number}: {old_status} -> {status_update.status} by {current_user['username']}")
    return po


@router.post("/purchase-orders/generate-from-order/{order_id}", response_model=IsottoPOGenerateResult)
async def generate_po_from_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_isotto_manager_or_admin()),
):
    """
    Auto-generate purchase orders from an order's line items.
    Groups items by supplier, compares to stock, generates 1 PO per supplier.
    """
    # Load order and line items
    order_result = await db.execute(
        select(IsottoOrderModel).where(IsottoOrderModel.id == order_id)
    )
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items_result = await db.execute(
        select(IsottoOrderLineItemModel)
        .where(IsottoOrderLineItemModel.order_id == order_id)
        .options(selectinload(IsottoOrderLineItemModel.catalog_product))
    )
    line_items = items_result.scalars().all()
    if not line_items:
        raise HTTPException(status_code=400, detail="Order has no line items")

    # Group by catalog product + color + size, then by supplier
    # Structure: {supplier_id: {(product_id, color, size): count}}
    supplier_needs = defaultdict(lambda: defaultdict(int))

    for item in line_items:
        if not item.catalog_product_id or not item.color or not item.size:
            continue
        product = item.catalog_product
        if not product:
            continue
        key = (product.id, product.supplier_id, product.supplier_product_code or "",
               product.name, item.color, item.size, float(product.supplier_unit_price))
        supplier_needs[product.supplier_id][key] += 1

    if not supplier_needs:
        return IsottoPOGenerateResult(purchase_orders_created=0, po_numbers=[], details=[])

    created_pos = []
    details = []

    for supplier_id, items_needed in supplier_needs.items():
        # Get supplier info
        supplier_result = await db.execute(
            select(IsottoSupplierModel).where(IsottoSupplierModel.id == supplier_id)
        )
        supplier = supplier_result.scalar_one_or_none()
        if not supplier:
            continue

        po_line_items = []
        for key, needed in items_needed.items():
            product_id, _, product_code, product_name, color, size, unit_price = key

            # Check current stock
            stock_result = await db.execute(
                select(IsottoCatalogStockModel).where(
                    and_(
                        IsottoCatalogStockModel.product_id == product_id,
                        IsottoCatalogStockModel.color == color,
                        IsottoCatalogStockModel.size == size,
                    )
                )
            )
            stock = stock_result.scalar_one_or_none()
            available = (stock.quantity_on_hand - stock.quantity_reserved) if stock else 0
            to_order = max(0, needed - available)

            if to_order > 0:
                line_total = float(Decimal(str(to_order)) * Decimal(str(unit_price)))
                po_line_items.append({
                    "product_code": product_code,
                    "product_name": product_name,
                    "color": color,
                    "size": size,
                    "quantity": to_order,
                    "unit_price": unit_price,
                    "line_total": line_total,
                })

        if not po_line_items:
            details.append({"supplier": supplier.name, "items": 0, "note": "All stock available"})
            continue

        # Create PO
        po_number = await _generate_po_number(db)
        subtotal = Decimal(str(sum(item["line_total"] for item in po_line_items)))
        vat_amount = (subtotal * Decimal("22") / Decimal("100")).quantize(Decimal("0.01"))

        new_po = IsottoPurchaseOrderModel(
            po_number=po_number,
            supplier_id=supplier_id,
            line_items=po_line_items,
            subtotal=subtotal,
            vat_rate=Decimal("22.00"),
            vat_amount=vat_amount,
            total=subtotal + vat_amount,
            status=IsottoPOStatus.DRAFT,
            expected_delivery=date.today() + timedelta(days=supplier.default_lead_time_days),
            related_order_ids=[str(order_id)],
            notes=f"Auto-generated from order {order.order_number}",
            created_by=current_user["username"],
        )
        db.add(new_po)
        await db.flush()

        # Mark line items as STOCK_ORDERED
        for item in line_items:
            if not item.catalog_product_id:
                continue
            product = item.catalog_product
            if product and product.supplier_id == supplier_id and item.status == LineItemStatus.PENDING:
                item.status = LineItemStatus.STOCK_ORDERED
                item.updated_at = datetime.now(timezone.utc)

        created_pos.append(po_number)
        details.append({
            "supplier": supplier.name,
            "po_number": po_number,
            "items": len(po_line_items),
            "total": float(subtotal + vat_amount),
        })

    await db.commit()

    logger.info(f"ISOTTO PO auto-generated from order {order.order_number}: {len(created_pos)} PO(s) by {current_user['username']}")
    return IsottoPOGenerateResult(
        purchase_orders_created=len(created_pos),
        po_numbers=created_pos,
        details=details,
    )


# ================================================================
# ARTWORK ENDPOINTS
# ================================================================

@router.post("/artworks", response_model=IsottoArtworkRead, status_code=status.HTTP_201_CREATED)
async def create_artwork(
    artwork: IsottoArtworkCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """Upload/register artwork metadata"""
    new_artwork = IsottoArtworkModel(**artwork.model_dump())
    db.add(new_artwork)
    await db.commit()
    await db.refresh(new_artwork)

    logger.info(f"ISOTTO artwork created: {new_artwork.title} by {current_user['username']}")
    return new_artwork


@router.get("/artworks", response_model=list[IsottoArtworkRead])
async def list_artworks(
    customer_id: Optional[UUID] = None,
    order_id: Optional[UUID] = None,
    reusable_only: bool = False,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """List artworks with optional filters"""
    query = select(IsottoArtworkModel)

    if customer_id:
        query = query.where(IsottoArtworkModel.customer_id == customer_id)
    if order_id:
        query = query.where(IsottoArtworkModel.order_id == order_id)
    if reusable_only:
        query = query.where(IsottoArtworkModel.is_reusable == True)

    query = query.order_by(IsottoArtworkModel.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/artworks/{artwork_id}", response_model=IsottoArtworkRead)
async def get_artwork(
    artwork_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """Get a single artwork"""
    result = await db.execute(
        select(IsottoArtworkModel).where(IsottoArtworkModel.id == artwork_id)
    )
    artwork = result.scalar_one_or_none()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    return artwork


@router.put("/artworks/{artwork_id}", response_model=IsottoArtworkRead)
async def update_artwork(
    artwork_id: UUID,
    artwork_update: IsottoArtworkUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_isotto_role()),
):
    """Update artwork metadata"""
    result = await db.execute(
        select(IsottoArtworkModel).where(IsottoArtworkModel.id == artwork_id)
    )
    artwork = result.scalar_one_or_none()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    update_data = artwork_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(artwork, field, value)

    artwork.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(artwork)

    logger.info(f"ISOTTO artwork updated: {artwork.title} by {current_user['username']}")
    return artwork


@router.delete("/artworks/{artwork_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artwork(
    artwork_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_isotto_manager_or_admin()),
):
    """Delete artwork (hard delete)"""
    result = await db.execute(
        select(IsottoArtworkModel).where(IsottoArtworkModel.id == artwork_id)
    )
    artwork = result.scalar_one_or_none()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    await db.delete(artwork)
    await db.commit()

    logger.info(f"ISOTTO artwork deleted: {artwork.title} by {current_user['username']}")


# ================================================================
# HTML WEB UI ROUTES
# ================================================================

@html_router.get("/print-shop/catalog", response_class=HTMLResponse, name="isotto_catalog")
async def isotto_catalog_page(request: Request):
    """Catalog page - browse and manage products"""
    return templates.TemplateResponse("isotto/catalog.html", {"request": request})


@html_router.get("/print-shop/suppliers", response_class=HTMLResponse, name="isotto_suppliers")
async def isotto_suppliers_page(request: Request):
    """Supplier directory - manage suppliers"""
    return templates.TemplateResponse("isotto/suppliers.html", {"request": request})


@html_router.get("/print-shop/purchase-orders", response_class=HTMLResponse, name="isotto_purchase_orders")
async def isotto_purchase_orders_page(request: Request):
    """Purchase orders - manage supplier orders"""
    return templates.TemplateResponse("isotto/purchase_orders.html", {"request": request})


@html_router.get("/print-shop/artworks", response_class=HTMLResponse, name="isotto_artworks")
async def isotto_artworks_page(request: Request):
    """Artwork gallery - manage design assets"""
    return templates.TemplateResponse("isotto/artworks.html", {"request": request})
