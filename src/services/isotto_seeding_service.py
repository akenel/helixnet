# File: src/services/isotto_seeding_service.py
"""
ISOTTO Sport Print Shop Seeding Service - Demo data for the pitch to Famous Guy.
Runs on application startup. Uses real client names from Angel's postcard pipeline.

Since 1968. Largo Franchi, 3 - Trapani.

"The postcard is the handshake. The coffee is the close."
"""
import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.models.isotto_customer_model import IsottoCustomerModel
from src.db.models.isotto_order_model import (
    IsottoOrderModel, ProductType, OrderStatus,
    ColorMode, DuplexMode, Lamination,
)

logger = logging.getLogger(__name__)


async def seed_isotto_data(db: AsyncSession) -> None:
    """
    Seed demo data for ISOTTO Sport print shop management.
    Idempotent -- checks if data exists before seeding.
    """
    logger.info("Checking if ISOTTO Sport data needs to be seeded...")

    # Check if customers already exist
    result = await db.execute(select(IsottoCustomerModel).limit(1))
    if result.scalar_one_or_none():
        logger.info("ISOTTO Sport data already seeded. Skipping.")
        return

    logger.info("Seeding ISOTTO Sport demo data...")

    # ================================================================
    # CUSTOMERS
    # ================================================================
    angel = IsottoCustomerModel(
        name="Angelo Kenel",
        company_name="UFA Foo Fighters",
        phone="+41 79 000 0000",
        email="angel@helixnet.ch",
        address="Baglio Xiare",
        city="Trapani",
        tax_id=None,
        first_order_date=date(2026, 1, 25),
        last_order_date=date(2026, 2, 13),
        order_count=4,
        total_spend=Decimal("85.00"),
        notes="Canadian-Swiss. Postcard and merch business. Building HelixNet platform. "
              "Multiple product lines: 4-UP postcards, tent cards, sticker labels.",
    )

    carmello = IsottoCustomerModel(
        name="Carmello Ferrante",
        company_name="Caffe Maltese",
        phone="+39 328 555 1234",
        email="info@caffemaltese.it",
        address="Centro Storico",
        city="Trapani",
        tax_id="FRRCML75B15L219K",
        first_order_date=date(2026, 2, 1),
        last_order_date=date(2026, 2, 10),
        order_count=1,
        total_spend=Decimal("35.00"),
        notes="CBD vending partner. Midnight fisherman at Baglio Xiare. Paulo's place.",
    )

    giovanni = IsottoCustomerModel(
        name="Giovanni Russo",
        company_name="Piccolo Bistratto",
        phone="+39 328 666 7890",
        email="info@piccolobistratto.it",
        city="Trapani",
        tax_id="RSSGVN80C20L219M",
        first_order_date=date(2026, 2, 8),
        last_order_date=date(2026, 2, 13),
        order_count=1,
        total_spend=Decimal("0.00"),
        notes="Jonathan the chef, Paolo (friend). Wants card set. In production.",
    )

    maria = IsottoCustomerModel(
        name="Maria Catalano",
        company_name="Hotel PuntaTipa",
        phone="+39 0923 111 222",
        email="info@puntatipa.it",
        address="38.029472, 12.528162",
        city="Trapani",
        tax_id="CTLMRA70D45L219F",
        first_order_date=None,
        last_order_date=None,
        order_count=0,
        total_spend=Decimal("0.00"),
        notes="Receptionist at PuntaTipa. Printer was broken. Reviewing Dualism postcard on screen.",
    )

    db.add_all([angel, carmello, giovanni, maria])
    await db.flush()  # Get IDs assigned

    # ================================================================
    # ORDERS
    # ================================================================

    # Order 1: Pizza Planet postcards (INVOICED -- done and paid)
    pizza_planet = IsottoOrderModel(
        order_number="ORD-20260203-0001",
        title="Pizza Planet 4-UP Postcards",
        description="4-UP portrait + landscape postcards for Pizza Planet, Bonagia. "
                    "Ciccio's forno a legna dal 2000. Google Maps QR code.",
        customer_id=angel.id,
        product_type=ProductType.POSTCARD,
        status=OrderStatus.INVOICED,
        quantity=200,
        unit_price=Decimal("0.25"),
        total_price=Decimal("50.00"),
        paper_weight_gsm=250,
        color_mode=ColorMode.CMYK,
        duplex=True,
        duplex_mode=DuplexMode.SHORT_EDGE,
        lamination=Lamination.NONE,
        size_description="A4 portrait + A4 landscape (4-UP, cut to 99x142.5mm / 142.5x99mm)",
        copies_per_sheet=4,
        cutting_instructions="1 horizontal + 1 vertical cut through center. Result: 4 cards with 3mm frame.",
        artwork_files="postcards-pizza-planet-A4-PORTRAIT.html, postcards-pizza-planet-A4-LANDSCAPE.html",
        proof_approved=True,
        proof_approved_at=datetime(2026, 2, 3, 10, 0, tzinfo=timezone.utc),
        assigned_to="Famous",
        quoted_at=datetime(2026, 2, 2, 14, 0, tzinfo=timezone.utc),
        approved_at=datetime(2026, 2, 3, 9, 0, tzinfo=timezone.utc),
        production_started_at=datetime(2026, 2, 3, 10, 30, tzinfo=timezone.utc),
        completed_at=datetime(2026, 2, 3, 15, 0, tzinfo=timezone.utc),
        picked_up_at=datetime(2026, 2, 3, 17, 0, tzinfo=timezone.utc),
        customer_notes="CRITICAL: Short edge flip for duplex. QR must scan to Google Maps PLACE, not coordinates.",
        production_notes="Clean run. 250gsm took the ink well. Cutter set to 148.5mm / 105mm for portrait sheets.",
    )

    # Order 2: Camper & Tour tent cards (INVOICED)
    camper_tent = IsottoOrderModel(
        order_number="ORD-20260126-0001",
        title="Camper & Tour A4 Tent Cards",
        description="A4 tent-fold postcards for Camper & Tour. Theme: Liberta (Freedom). "
                    "Bilingual Italian + English. Zero cuts -- just fold and tape.",
        customer_id=angel.id,
        product_type=ProductType.POSTCARD,
        status=OrderStatus.INVOICED,
        quantity=50,
        unit_price=Decimal("0.30"),
        total_price=Decimal("15.00"),
        paper_weight_gsm=250,
        color_mode=ColorMode.CMYK,
        duplex=False,
        lamination=Lamination.NONE,
        size_description="A4 portrait (210x297mm) -- single sided, fold into tent card",
        copies_per_sheet=1,
        cutting_instructions="No cutting. Full A4 sheet, fold at tick marks.",
        artwork_files="postcard-camperandtour-TENT-FINAL.html",
        proof_approved=True,
        proof_approved_at=datetime(2026, 1, 26, 11, 0, tzinfo=timezone.utc),
        assigned_to="Famous",
        quoted_at=datetime(2026, 1, 26, 9, 0, tzinfo=timezone.utc),
        approved_at=datetime(2026, 1, 26, 10, 0, tzinfo=timezone.utc),
        production_started_at=datetime(2026, 1, 26, 11, 30, tzinfo=timezone.utc),
        completed_at=datetime(2026, 1, 26, 14, 0, tzinfo=timezone.utc),
        picked_up_at=datetime(2026, 1, 26, 16, 0, tzinfo=timezone.utc),
        customer_notes="Approved by Nino at Camper & Tour. First LIVE UAT success!",
        production_notes="Clean print. Single-sided 250gsm.",
    )

    # Order 3: Caffe Maltese business cards (READY for pickup)
    caffe_cards = IsottoOrderModel(
        order_number="ORD-20260201-0001",
        title="Caffe Maltese Business Cards",
        description="Standard business cards for Caffe Maltese. CBD vending partner branding.",
        customer_id=carmello.id,
        product_type=ProductType.BUSINESS_CARD,
        status=OrderStatus.READY,
        quantity=500,
        unit_price=Decimal("0.07"),
        total_price=Decimal("35.00"),
        paper_weight_gsm=350,
        color_mode=ColorMode.CMYK,
        duplex=True,
        duplex_mode=DuplexMode.LONG_EDGE,
        lamination=Lamination.MATTE,
        size_description="85x55mm (standard business card)",
        copies_per_sheet=10,
        cutting_instructions="Standard business card cutter template. 85x55mm.",
        proof_approved=True,
        proof_approved_at=datetime(2026, 2, 5, 10, 0, tzinfo=timezone.utc),
        assigned_to="Marco Designer",
        quoted_at=datetime(2026, 2, 1, 10, 0, tzinfo=timezone.utc),
        approved_at=datetime(2026, 2, 3, 9, 0, tzinfo=timezone.utc),
        production_started_at=datetime(2026, 2, 5, 11, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 2, 10, 12, 0, tzinfo=timezone.utc),
        customer_notes="Matte lamination for premium feel. Logo must be sharp.",
        production_notes="350gsm + matte lamination. Good result. Cards ready in box at counter.",
    )

    # Order 4: Piccolo Bistratto menu cards (IN_PRODUCTION)
    piccolo_menu = IsottoOrderModel(
        order_number="ORD-20260208-0001",
        title="Piccolo Bistratto Menu Card Set",
        description="Menu cards for Piccolo Bistratto. Giovanni's place, Jonathan the chef.",
        customer_id=giovanni.id,
        product_type=ProductType.MENU,
        status=OrderStatus.IN_PRODUCTION,
        quantity=100,
        unit_price=Decimal("0.40"),
        total_price=Decimal("40.00"),
        paper_weight_gsm=300,
        color_mode=ColorMode.CMYK,
        duplex=True,
        duplex_mode=DuplexMode.SHORT_EDGE,
        lamination=Lamination.GLOSSY,
        size_description="A5 (148x210mm) -- folded menu",
        copies_per_sheet=2,
        cutting_instructions="Cut A4 in half (148.5mm from top). Result: 2 x A5 cards.",
        assigned_to="Luca Operator",
        estimated_completion=date(2026, 2, 15),
        quoted_at=datetime(2026, 2, 8, 10, 0, tzinfo=timezone.utc),
        approved_at=datetime(2026, 2, 10, 9, 0, tzinfo=timezone.utc),
        production_started_at=datetime(2026, 2, 12, 8, 0, tzinfo=timezone.utc),
        proof_approved=True,
        proof_approved_at=datetime(2026, 2, 10, 14, 0, tzinfo=timezone.utc),
        customer_notes="Jonathan wants glossy finish. Food photos must pop.",
        production_notes="In production. Glossy lamination after print run.",
    )

    # Order 5: PuntaTipa hotel postcards (QUOTED -- waiting approval)
    puntatipa_cards = IsottoOrderModel(
        order_number="ORD-20260213-0001",
        title="Hotel PuntaTipa Postcard Set",
        description="Dualism-themed postcards for Hotel PuntaTipa. "
                    "Blue|Cream|Red stripes. Coordinates + message lines.",
        customer_id=maria.id,
        product_type=ProductType.POSTCARD,
        status=OrderStatus.QUOTED,
        quantity=200,
        unit_price=Decimal("0.25"),
        total_price=Decimal("50.00"),
        paper_weight_gsm=250,
        color_mode=ColorMode.CMYK,
        duplex=True,
        duplex_mode=DuplexMode.SHORT_EDGE,
        lamination=Lamination.NONE,
        size_description="A4 portrait (4-UP, cut to 99x142.5mm)",
        copies_per_sheet=4,
        cutting_instructions="1 horizontal + 1 vertical cut through center.",
        assigned_to=None,
        estimated_completion=date(2026, 2, 20),
        quoted_at=datetime(2026, 2, 13, 9, 0, tzinfo=timezone.utc),
        customer_notes="Printer was broken when we visited. Maria reviewing design on screen.",
    )

    # Order 6: Color Clean postcards (IN_PRODUCTION)
    colorclean = IsottoOrderModel(
        order_number="ORD-20260210-0001",
        title="Color Clean 4-UP Postcards",
        description="4-UP postcards for Color Clean lavanderia. "
                    "Via Virgilio 105/107. They loved the tent card + review.",
        customer_id=angel.id,
        product_type=ProductType.POSTCARD,
        status=OrderStatus.IN_PRODUCTION,
        quantity=100,
        unit_price=Decimal("0.25"),
        total_price=Decimal("25.00"),
        paper_weight_gsm=250,
        color_mode=ColorMode.CMYK,
        duplex=True,
        duplex_mode=DuplexMode.SHORT_EDGE,
        lamination=Lamination.NONE,
        size_description="A4 landscape (4-UP, cut to 142.5x99mm)",
        copies_per_sheet=4,
        cutting_instructions="1 horizontal + 1 vertical cut through center.",
        artwork_files="postcards-colorclean-A4-LANDSCAPE.html",
        proof_approved=True,
        proof_approved_at=datetime(2026, 2, 11, 10, 0, tzinfo=timezone.utc),
        assigned_to="Famous",
        estimated_completion=date(2026, 2, 14),
        quoted_at=datetime(2026, 2, 10, 10, 0, tzinfo=timezone.utc),
        approved_at=datetime(2026, 2, 11, 9, 0, tzinfo=timezone.utc),
        production_started_at=datetime(2026, 2, 13, 8, 0, tzinfo=timezone.utc),
        customer_notes="They loved the tent card + review QR. Same style, 4-UP layout.",
        production_notes="Running alongside Pizza Planet batch. Same stock, same setup.",
    )

    # Order 7: UFA wax seal labels (QUOTED)
    wax_labels = IsottoOrderModel(
        order_number="ORD-20260213-0002",
        title="UFA Wax Seal Labels",
        description="Custom sticker labels for UFA experience box wax seals. "
                    "Round seal label + corner label on A4 sheet.",
        customer_id=angel.id,
        product_type=ProductType.LABEL,
        status=OrderStatus.QUOTED,
        quantity=500,
        unit_price=Decimal("0.03"),
        total_price=Decimal("15.00"),
        paper_weight_gsm=80,
        color_mode=ColorMode.CMYK,
        duplex=False,
        lamination=Lamination.NONE,
        size_description="A4 sticker sheet (multiple labels per sheet)",
        copies_per_sheet=20,
        cutting_instructions="Die-cut round seals (30mm diameter) + rectangular corners (40x15mm).",
        artwork_files="labels-seal-sheet.html",
        assigned_to=None,
        estimated_completion=date(2026, 2, 25),
        quoted_at=datetime(2026, 2, 13, 10, 0, tzinfo=timezone.utc),
        customer_notes="Need sticker stock, not regular paper. For wax seal application.",
    )

    db.add_all([pizza_planet, camper_tent, caffe_cards, piccolo_menu, puntatipa_cards, colorclean, wax_labels])
    await db.commit()

    logger.info("ISOTTO Sport seeding completed!")
    logger.info("  - 4 customers (Angelo/UFA, Carmello/Maltese, Giovanni/Bistratto, Maria/PuntaTipa)")
    logger.info("  - 7 print orders:")
    logger.info("    - Pizza Planet 4-UP postcards (INVOICED)")
    logger.info("    - Camper & Tour tent cards (INVOICED)")
    logger.info("    - Caffe Maltese business cards (READY)")
    logger.info("    - Piccolo Bistratto menu cards (IN_PRODUCTION)")
    logger.info("    - PuntaTipa hotel postcards (QUOTED)")
    logger.info("    - Color Clean 4-UP postcards (IN_PRODUCTION)")
    logger.info("    - UFA wax seal labels (QUOTED)")
