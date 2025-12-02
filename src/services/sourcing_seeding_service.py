"""
Sourcing System Seeding Service
Seeds suppliers and sourcing requests for UAT testing.

Two data sets:
1. EASY SET - Clean, simple data for happy path testing
2. CHUCK NORRIS SET - Edge cases, unicode, stress testing
"""
import logging
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.models import SupplierModel, SourcingRequestModel, SourcingNoteModel

logger = logging.getLogger(__name__)


# =============================================================================
# EASY SET - Happy Flow Test Data
# =============================================================================

EASY_SUPPLIERS = [
    {
        "code": "420",
        "name": "BR Break Shop",
        "country": "CH",
        "lead_time_days_min": 2,
        "lead_time_days_max": 5,
        "quality_rating": "A",
        "categories": "pipes,accessories,rolling",
        "swiss_certified": True,
        "contacts": {"name": "Hans", "email": "hans@breakshop.ch"},
        "notes": "Reliable for bulk orders"
    },
    {
        "code": "WR",
        "name": "Wellauer AG",
        "country": "CH",
        "lead_time_days_min": 1,
        "lead_time_days_max": 3,
        "quality_rating": "A",
        "categories": "general,tobacco,papers",
        "swiss_certified": True,
        "contacts": {"name": "Maria", "phone": "+41 44 123 4567"},
        "notes": "Premium Swiss distributor"
    },
    {
        "code": "ND",
        "name": "Near Dark GmbH",
        "country": "DE",
        "lead_time_days_min": 3,
        "lead_time_days_max": 7,
        "quality_rating": "B",
        "categories": "vapes,electronics,batteries",
        "swiss_certified": False,
        "contacts": {"name": "Klaus", "email": "klaus@neardark.de"},
        "notes": "Good prices, EU shipping"
    },
    {
        "code": "Hem",
        "name": "Hemag Nova",
        "country": "CH",
        "lead_time_days_min": 2,
        "lead_time_days_max": 4,
        "quality_rating": "A",
        "categories": "cbd,hemp,extracts,oils",
        "swiss_certified": True,
        "contacts": {"name": "Sophie", "email": "sophie@hemagnova.ch"},
        "notes": "Specialist for CBD/hemp products"
    },
]

EASY_REQUESTS = [
    {
        "request_code": "SR-2024-001",
        "product_name": "Volcano Maintenance Set",
        "requested_by": "Pam",
        "assigned_to": "Felix",
        "status": "investigating",
        "priority": "normal",
        "expected_price": Decimal("15.00"),
        "notes": [
            {"author": "Pam", "content": "Customer asked for this 3 times", "source": "research"},
            {"author": "Felix", "content": "Checking with 420 and WR", "source": "research"},
        ]
    },
    {
        "request_code": "SR-2024-002",
        "product_name": "Metal Pipe Kurz",
        "requested_by": "Ralph",
        "assigned_to": "Felix",
        "status": "sourced",
        "supplier_code": "420",
        "priority": "normal",
        "expected_price": Decimal("8.50"),
        "min_order_qty": 10,
        "notes": [
            {"author": "Felix", "content": "Found at Break Shop, good price", "source": "call"},
        ]
    },
    {
        "request_code": "SR-2024-003",
        "product_name": "CBD Oil 20% Premium",
        "requested_by": "Pam",
        "assigned_to": "Felix",
        "status": "sourced",
        "supplier_code": "Hem",
        "priority": "high",
        "expected_price": Decimal("89.00"),
        "min_order_qty": 5,
        "notes": [
            {"author": "Felix", "content": "Hemag Nova has best quality", "source": "research"},
            {"author": "Felix", "content": "Swiss certified, lab tested", "source": "research"},
        ]
    },
    {
        "request_code": "SR-2024-004",
        "product_name": "Rolling Papers King Size",
        "requested_by": "Leandra",
        "assigned_to": None,
        "status": "new",
        "priority": "low",
        "notes": []
    },
]


# =============================================================================
# CHUCK NORRIS SET - Edge Cases & Stress Testing
# =============================================================================

CHUCK_NORRIS_SUPPLIERS = [
    {
        "code": "CN1",
        "name": "Chuck's Roundhouse Supplies Ltd.",
        "country": "US",
        "lead_time_days_min": 14,
        "lead_time_days_max": 30,
        "quality_rating": "A",
        "categories": "everything,anything,impossible",
        "swiss_certified": False,
        "contacts": {"name": "Chuck", "note": "He calls you"},
        "notes": "When Chuck ships, the package delivers itself"
    },
    {
        "code": "LONG123",
        "name": "Extremely Long Supplier Name That Tests Database Field Limits And UI Wrapping",
        "country": "JP",
        "lead_time_days_min": 1,
        "lead_time_days_max": 999,
        "quality_rating": "C",
        "categories": "a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z",
        "swiss_certified": False,
        "notes": "Testing long text fields"
    },
    {
        "code": "UNI",
        "name": "Edelweiss AG",
        "country": "CH",
        "lead_time_days_min": 1,
        "lead_time_days_max": 2,
        "quality_rating": "A",
        "categories": "premium,swiss,quality",
        "swiss_certified": True,
        "contacts": {"name": "Hans-Peter", "email": "hp@edelweiss.ch"},
        "notes": "Testing standard chars"
    },
    {
        "code": "ZERO",
        "name": "Zero Lead Time Express",
        "country": "CH",
        "lead_time_days_min": 0,
        "lead_time_days_max": 0,
        "quality_rating": "A",
        "categories": "instant",
        "swiss_certified": True,
        "notes": "Same-day delivery test case"
    },
]

CHUCK_NORRIS_REQUESTS = [
    {
        "request_code": "SR-CN-001",
        "product_name": "Chuck Norris Action Figure (Roundhouse Kick Edition)",
        "product_description": "When you open the box, it's already assembled. And it assembled you.",
        "requested_by": "Chuck",
        "assigned_to": "Felix",
        "status": "investigating",
        "priority": "urgent",
        "expected_price": Decimal("999999.99"),
        "notes": [
            {"author": "Felix", "content": "How do I source something that sources itself?", "source": "research"},
            {"author": "Chuck", "content": "I don't get sourced. I source.", "source": "call"},
        ]
    },
    {
        "request_code": "SR-CN-002",
        "product_name": "A" * 200,  # 200 character product name
        "requested_by": "Test",
        "status": "new",
        "priority": "low",
        "notes": []
    },
    {
        "request_code": "SR-CN-003",
        "product_name": "Item with 0.00 Price",
        "requested_by": "Pam",
        "assigned_to": "Felix",
        "status": "sourced",
        "supplier_code": "ZERO",
        "expected_price": Decimal("0.00"),
        "min_order_qty": 0,
        "notes": [
            {"author": "Felix", "content": "Free sample program", "source": "email"},
        ]
    },
    {
        "request_code": "SR-CN-004",
        "product_name": "Not Available Until 2030",
        "requested_by": "Ralph",
        "status": "not_available",
        "not_available_until": date(2030, 1, 1),
        "priority": "normal",
        "notes": [
            {"author": "Felix", "content": "Discontinued, recheck in 2030", "source": "research"},
        ]
    },
    {
        "request_code": "SR-CN-005",
        "product_name": "Coconut Extract Natural 100ml",
        "product_description": "Andy's order - natural only, no synthetic. See KB-004, KB-587 section 4.",
        "requested_by": "Andy",
        "assigned_to": "Felix",
        "status": "sourced",
        "supplier_code": "Hem",
        "priority": "high",
        "expected_price": Decimal("24.00"),
        "min_order_qty": 1,
        "notes": [
            {"author": "Andy", "content": "Need 100ml ASAP for next week", "source": "research"},
            {"author": "Felix", "content": "Hemag Nova has Swiss certified natural extract", "source": "call"},
            {"author": "Felix", "content": "3 day ETA, A-tier quality", "source": "research", "kb_reference": "KB-004"},
        ]
    },
]


async def seed_easy_suppliers(db: AsyncSession) -> int:
    """Seed the easy/happy path supplier data."""
    count = 0
    for data in EASY_SUPPLIERS:
        existing = await db.execute(
            select(SupplierModel).where(SupplierModel.code == data["code"])
        )
        if existing.scalar_one_or_none():
            continue

        supplier = SupplierModel(**data)
        db.add(supplier)
        count += 1

    await db.commit()
    return count


async def seed_easy_requests(db: AsyncSession) -> int:
    """Seed the easy/happy path sourcing requests."""
    count = 0
    for data in EASY_REQUESTS:
        existing = await db.execute(
            select(SourcingRequestModel).where(
                SourcingRequestModel.request_code == data["request_code"]
            )
        )
        if existing.scalar_one_or_none():
            continue

        # Extract notes for separate creation
        notes_data = data.pop("notes", [])
        supplier_code = data.pop("supplier_code", None)

        # Resolve supplier ID if provided
        if supplier_code:
            supplier_result = await db.execute(
                select(SupplierModel).where(SupplierModel.code == supplier_code)
            )
            supplier = supplier_result.scalar_one_or_none()
            if supplier:
                data["supplier_id"] = supplier.id

        request = SourcingRequestModel(**data)
        db.add(request)
        await db.flush()  # Get the ID

        # Add notes
        for note_data in notes_data:
            note = SourcingNoteModel(
                request_id=request.id,
                **note_data
            )
            db.add(note)

        count += 1

    await db.commit()
    return count


async def seed_chuck_norris_suppliers(db: AsyncSession) -> int:
    """Seed the Chuck Norris edge case supplier data."""
    count = 0
    for data in CHUCK_NORRIS_SUPPLIERS:
        existing = await db.execute(
            select(SupplierModel).where(SupplierModel.code == data["code"])
        )
        if existing.scalar_one_or_none():
            continue

        supplier = SupplierModel(**data)
        db.add(supplier)
        count += 1

    await db.commit()
    return count


async def seed_chuck_norris_requests(db: AsyncSession) -> int:
    """Seed the Chuck Norris edge case sourcing requests."""
    count = 0
    for data in CHUCK_NORRIS_REQUESTS:
        existing = await db.execute(
            select(SourcingRequestModel).where(
                SourcingRequestModel.request_code == data["request_code"]
            )
        )
        if existing.scalar_one_or_none():
            continue

        # Extract notes for separate creation
        notes_data = data.pop("notes", [])
        supplier_code = data.pop("supplier_code", None)

        # Resolve supplier ID if provided
        if supplier_code:
            supplier_result = await db.execute(
                select(SupplierModel).where(SupplierModel.code == supplier_code)
            )
            supplier = supplier_result.scalar_one_or_none()
            if supplier:
                data["supplier_id"] = supplier.id

        request = SourcingRequestModel(**data)
        db.add(request)
        await db.flush()

        # Add notes
        for note_data in notes_data:
            note = SourcingNoteModel(
                request_id=request.id,
                **note_data
            )
            db.add(note)

        count += 1

    await db.commit()
    return count


async def seed_sourcing_system(db: AsyncSession) -> dict:
    """
    Full seeding for sourcing system.
    Seeds both EASY and CHUCK NORRIS data sets.
    """
    logger.info("Seeding Sourcing System data...")

    results = {
        "easy_suppliers": 0,
        "easy_requests": 0,
        "chuck_suppliers": 0,
        "chuck_requests": 0,
    }

    # Easy set first (happy path)
    results["easy_suppliers"] = await seed_easy_suppliers(db)
    results["easy_requests"] = await seed_easy_requests(db)

    # Chuck Norris set (edge cases)
    results["chuck_suppliers"] = await seed_chuck_norris_suppliers(db)
    results["chuck_requests"] = await seed_chuck_norris_requests(db)

    logger.info(f"Sourcing seeding complete: {results}")
    return results
