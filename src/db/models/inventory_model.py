# File: src/db/models/inventory_model.py
"""
HelixINVENTORY - Be Water, My Friend
"Damn capsules. I need a SYSTEM." - Andy, Day One, 11:10 AM

Stock flows in. Stock flows out.
Like a river. Never stagnant. Always moving.

When it runs low, it tells you.
When it's out, it screams.
When you reorder, it remembers.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, Enum as SQLEnum, Numeric, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


# ================================================================
# ENUMS - The Flow States
# ================================================================

class StockStatus(enum.Enum):
    """Stock level status"""
    OK = "ok"                       # All good
    LOW = "low"                     # Below threshold, reorder soon
    CRITICAL = "critical"           # Almost out, reorder NOW
    OUT = "out"                     # Zero. Emergency.
    OVERSTOCKED = "overstocked"     # Too much, slow down orders


class MovementType(enum.Enum):
    """Stock movement types"""
    IN_PURCHASE = "in_purchase"         # Bought from supplier
    IN_RETURN = "in_return"             # Customer return
    IN_ADJUSTMENT = "in_adjustment"     # Manual count adjustment up
    OUT_SALE = "out_sale"               # Sold to customer
    OUT_WASTE = "out_waste"             # Damaged, expired, Michel used whole bottle
    OUT_SAMPLE = "out_sample"           # Free sample, promo
    OUT_ADJUSTMENT = "out_adjustment"   # Manual count adjustment down
    TRANSFER = "transfer"               # Between locations


class ReorderStatus(enum.Enum):
    """Reorder request status"""
    SUGGESTED = "suggested"         # System suggests reorder
    APPROVED = "approved"           # Andy approved it
    ORDERED = "ordered"             # Order placed with supplier
    SHIPPED = "shipped"             # On the way
    RECEIVED = "received"           # In stock
    CANCELLED = "cancelled"         # Nevermind


class SupplierType(enum.Enum):
    """Supplier categories"""
    COFFEE = "coffee"               # Capsules, beans
    CBD = "cbd"                     # BLQ products
    FOOD = "food"                   # Cold cuts, baloney, croissants
    PET = "pet"                     # Shampoo, treats, kibbles
    ACCESSORIES = "accessories"     # Papers, grinders
    GENERAL = "general"             # Aldi runs, misc


class UnitType(enum.Enum):
    """Measurement units"""
    PIECE = "piece"                 # Individual items
    BOX = "box"                     # Box of items
    PACK = "pack"                   # Pack (papers, etc)
    BOTTLE = "bottle"               # Shampoo, oil
    BAG = "bag"                     # Coffee beans, kibbles
    KG = "kg"                       # By weight
    LITER = "liter"                 # Liquids
    CAPSULE = "capsule"             # THE CAPSULES


# ================================================================
# SUPPLIER MODEL - Where the stuff comes from
# ================================================================

class SupplierModel(Base):
    """
    Suppliers - the rivers that feed the shop.

    Aldi for emergencies.
    BLQ for the good stuff.
    Marco for vending.
    """
    __tablename__ = 'suppliers'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Identity
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True
    )
    code: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        comment="Short code: ALDI, BLQ, MARCO"
    )
    supplier_type: Mapped[SupplierType] = mapped_column(
        SQLEnum(SupplierType),
        default=SupplierType.GENERAL
    )

    # Contact
    contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Business
    payment_terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Net 30, COD, etc"
    )
    min_order_amount: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    lead_time_days: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment="Days from order to delivery"
    )

    # Flags
    is_emergency: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Can do same-day runs (like Aldi)"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Special instructions, quirks"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    products: Mapped[list["InventoryItemModel"]] = relationship(
        "InventoryItemModel",
        back_populates="primary_supplier"
    )

    def __repr__(self):
        return f"<SupplierModel(name='{self.name}', type='{self.supplier_type.value}')>"


# ================================================================
# INVENTORY ITEM MODEL - The Stock
# ================================================================

class InventoryItemModel(Base):
    """
    Every item in stock.

    Capsules. Shampoo bottles. Cold cuts.
    If it can run out, it's here.
    """
    __tablename__ = 'inventory_items'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Identity
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True
    )
    sku: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        index=True
    )
    barcode: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        index=True
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="capsules, shampoo, food, cbd, etc"
    )

    # Units
    unit_type: Mapped[UnitType] = mapped_column(
        SQLEnum(UnitType),
        default=UnitType.PIECE
    )
    units_per_pack: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment="If buying in packs, how many per pack"
    )

    # Current Stock
    quantity_on_hand: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Current stock level"
    )
    quantity_reserved: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Reserved for orders not yet fulfilled"
    )
    quantity_available: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="On hand minus reserved"
    )

    # Thresholds - The Alerts
    reorder_point: Mapped[int] = mapped_column(
        Integer,
        default=10,
        comment="When to start worrying"
    )
    critical_point: Mapped[int] = mapped_column(
        Integer,
        default=3,
        comment="When to panic"
    )
    max_stock: Mapped[int] = mapped_column(
        Integer,
        default=100,
        comment="Don't order more than this"
    )
    reorder_quantity: Mapped[int] = mapped_column(
        Integer,
        default=20,
        comment="How many to order when reordering"
    )

    # Status
    stock_status: Mapped[StockStatus] = mapped_column(
        SQLEnum(StockStatus),
        default=StockStatus.OK
    )

    # Pricing
    cost_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="What we pay"
    )
    sell_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="What customer pays"
    )

    # Supplier
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('suppliers.id', ondelete='SET NULL'),
        nullable=True
    )
    supplier_sku: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Supplier's product code"
    )

    # Location
    storage_location: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Shelf A, Basement, etc"
    )

    # Tracking
    last_counted: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    last_ordered: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    last_received: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Flags
    track_inventory: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Some items we don't track closely"
    )
    auto_reorder: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Automatically create reorder when low"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    primary_supplier: Mapped["SupplierModel"] = relationship(
        "SupplierModel",
        back_populates="products"
    )
    movements: Mapped[list["StockMovementModel"]] = relationship(
        "StockMovementModel",
        back_populates="item",
        cascade="all, delete-orphan"
    )

    def update_status(self):
        """Update stock status based on current quantity"""
        available = self.quantity_on_hand - self.quantity_reserved
        self.quantity_available = max(0, available)

        if self.quantity_on_hand <= 0:
            self.stock_status = StockStatus.OUT
        elif self.quantity_on_hand <= self.critical_point:
            self.stock_status = StockStatus.CRITICAL
        elif self.quantity_on_hand <= self.reorder_point:
            self.stock_status = StockStatus.LOW
        elif self.quantity_on_hand >= self.max_stock:
            self.stock_status = StockStatus.OVERSTOCKED
        else:
            self.stock_status = StockStatus.OK

    def __repr__(self):
        return f"<InventoryItemModel(name='{self.name}', qty={self.quantity_on_hand}, status='{self.stock_status.value}')>"


# ================================================================
# STOCK MOVEMENT MODEL - The Flow
# ================================================================

class StockMovementModel(Base):
    """
    Every movement of stock.

    In. Out. Like breathing.
    Michel uses whole bottle = OUT_WASTE.
    Aldi run = IN_PURCHASE.
    """
    __tablename__ = 'stock_movements'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # What moved
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inventory_items.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Movement details
    movement_type: Mapped[MovementType] = mapped_column(
        SQLEnum(MovementType),
        nullable=False,
        index=True
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Positive for IN, negative for OUT"
    )
    quantity_before: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Stock level before movement"
    )
    quantity_after: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Stock level after movement"
    )

    # Reference
    reference_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="order, restock, adjustment, etc"
    )
    reference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="ID of related order, restock, etc"
    )

    # Cost tracking
    unit_cost: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    total_cost: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )

    # Who did it
    performed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Andy, Michel, System"
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Michel used whole bottle for one cat"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True
    )

    # Relationships
    item: Mapped["InventoryItemModel"] = relationship(
        "InventoryItemModel",
        back_populates="movements"
    )

    def __repr__(self):
        return f"<StockMovementModel(item_id='{self.item_id}', type='{self.movement_type.value}', qty={self.quantity})>"


# ================================================================
# REORDER REQUEST MODEL - When the river runs low
# ================================================================

class ReorderRequestModel(Base):
    """
    Reorder requests - when stock needs refilling.

    System suggests. Andy approves. Supplier delivers.
    """
    __tablename__ = 'reorder_requests'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # What to reorder
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inventory_items.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('suppliers.id', ondelete='SET NULL'),
        nullable=True
    )

    # Quantities
    quantity_requested: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    quantity_received: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # Status
    status: Mapped[ReorderStatus] = mapped_column(
        SQLEnum(ReorderStatus),
        default=ReorderStatus.SUGGESTED,
        index=True
    )

    # Reason
    trigger_reason: Mapped[str] = mapped_column(
        String(100),
        default="low_stock",
        comment="low_stock, critical, manual, auto"
    )
    stock_at_trigger: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Stock level when reorder was triggered"
    )

    # Pricing
    estimated_cost: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    actual_cost: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Dates
    suggested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ordered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Who
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"<ReorderRequestModel(item_id='{self.item_id}', qty={self.quantity_requested}, status='{self.status.value}')>"


# ================================================================
# INVENTORY COUNT MODEL - Physical counts
# ================================================================

class InventoryCountModel(Base):
    """
    Physical inventory counts.

    Trust but verify. Count the capsules.
    """
    __tablename__ = 'inventory_counts'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Count details
    count_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    count_type: Mapped[str] = mapped_column(
        String(50),
        default="full",
        comment="full, spot, category"
    )
    category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="If counting specific category"
    )

    # Results
    items_counted: Mapped[int] = mapped_column(Integer, default=0)
    discrepancies_found: Mapped[int] = mapped_column(Integer, default=0)
    adjustments_made: Mapped[int] = mapped_column(Integer, default=0)

    # Who
    counted_by: Mapped[str] = mapped_column(String(100), nullable=False)
    verified_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default="in_progress",
        comment="in_progress, completed, cancelled"
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    def __repr__(self):
        return f"<InventoryCountModel(date='{self.count_date}', items={self.items_counted})>"


# ================================================================
# DEFAULT SUPPLIERS - The Starting Rivers
# ================================================================

DEFAULT_SUPPLIERS = [
    {
        "name": "Aldi Stans",
        "code": "ALDI",
        "supplier_type": SupplierType.GENERAL,
        "lead_time_days": 0,
        "is_emergency": True,
        "notes": "Around the corner. Emergency runs. Cold cuts, baloney, basics."
    },
    {
        "name": "BLQ Distribution",
        "code": "BLQ",
        "supplier_type": SupplierType.CBD,
        "lead_time_days": 2,
        "is_emergency": False,
        "notes": "CBD drops, oils. Blue and Pineapple flavors."
    },
    {
        "name": "Marco Vending",
        "code": "MARCO",
        "supplier_type": SupplierType.GENERAL,
        "lead_time_days": 1,
        "is_emergency": False,
        "notes": "Boris's guy. Vending machine products."
    },
    {
        "name": "Nespresso Business",
        "code": "NESPRESSO",
        "supplier_type": SupplierType.COFFEE,
        "lead_time_days": 3,
        "is_emergency": False,
        "notes": "CAPSULES. The system Andy needs."
    },
    {
        "name": "Pet Supplies Direct",
        "code": "PETDIRECT",
        "supplier_type": SupplierType.PET,
        "lead_time_days": 2,
        "is_emergency": False,
        "notes": "Shampoo, conditioner, kibbles. Michel uses whole bottles."
    },
]


# ================================================================
# DEFAULT INVENTORY ITEMS - Andy's Problem Children
# ================================================================

DEFAULT_INVENTORY_ITEMS = [
    {
        "name": "Nespresso Capsules - Ristretto",
        "sku": "CAPS-RIST-001",
        "category": "capsules",
        "unit_type": UnitType.CAPSULE,
        "units_per_pack": 50,
        "reorder_point": 100,
        "critical_point": 30,
        "max_stock": 500,
        "reorder_quantity": 200,
        "auto_reorder": True,
        "storage_location": "Basement",
    },
    {
        "name": "Nespresso Capsules - Lungo",
        "sku": "CAPS-LUNG-001",
        "category": "capsules",
        "unit_type": UnitType.CAPSULE,
        "units_per_pack": 50,
        "reorder_point": 100,
        "critical_point": 30,
        "max_stock": 500,
        "reorder_quantity": 200,
        "auto_reorder": True,
        "storage_location": "Basement",
    },
    {
        "name": "Pet Shampoo - Premium",
        "sku": "PET-SHAMP-001",
        "category": "pet_supplies",
        "unit_type": UnitType.BOTTLE,
        "reorder_point": 5,
        "critical_point": 2,
        "max_stock": 20,
        "reorder_quantity": 10,
        "auto_reorder": True,
        "notes": "Michel uses whole bottle per wash. Order frequently."
    },
    {
        "name": "Cold Cuts - Baloney",
        "sku": "FOOD-BALO-001",
        "category": "food",
        "unit_type": UnitType.KG,
        "reorder_point": 2,
        "critical_point": 1,
        "max_stock": 10,
        "reorder_quantity": 5,
        "auto_reorder": False,
        "notes": "Aldi run. Check freshness dates."
    },
    {
        "name": "BLQ CBD Drops - Blue",
        "sku": "CBD-BLUE-001",
        "category": "cbd",
        "unit_type": UnitType.BOTTLE,
        "reorder_point": 10,
        "critical_point": 3,
        "max_stock": 50,
        "reorder_quantity": 20,
        "auto_reorder": True,
    },
    {
        "name": "Kibbles Gift Bags",
        "sku": "PET-KIBB-001",
        "category": "pet_supplies",
        "unit_type": UnitType.BAG,
        "reorder_point": 20,
        "critical_point": 5,
        "max_stock": 100,
        "reorder_quantity": 50,
        "auto_reorder": True,
        "notes": "Gift for PUSS and friends"
    },
]


# ================================================================
# HELPER FUNCTIONS - The Flow Control
# ================================================================

def check_all_stock_levels(items: list[InventoryItemModel]) -> dict:
    """Check all items and return status summary"""
    summary = {
        "ok": 0,
        "low": 0,
        "critical": 0,
        "out": 0,
        "needs_reorder": []
    }

    for item in items:
        item.update_status()
        summary[item.stock_status.value] = summary.get(item.stock_status.value, 0) + 1

        if item.stock_status in [StockStatus.LOW, StockStatus.CRITICAL, StockStatus.OUT]:
            summary["needs_reorder"].append({
                "name": item.name,
                "current": item.quantity_on_hand,
                "reorder_point": item.reorder_point,
                "status": item.stock_status.value
            })

    return summary
