# File: src/services/isotto_catalog_seeding_service.py
"""
ISOTTO Sport Catalog Seeding Service - Suppliers, products, stock, and team order demo.
Runs on application startup. Populates the merch catalog with real supplier data.

Since 1968. Famous Guy knows his suppliers.

"ASD Trapani Calcio: 20 players, 20 names, 20 numbers, 7 different sizes.
On paper = mistakes every time. In the system = perfect every time."
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.models.isotto_supplier_model import IsottoSupplierModel
from src.db.models.isotto_catalog_model import (
    IsottoCatalogProductModel, IsottoMerchCategory, IsottoPrintMethod,
)
from src.db.models.isotto_catalog_stock_model import IsottoCatalogStockModel
from src.db.models.isotto_order_line_item_model import IsottoOrderLineItemModel, LineItemStatus
from src.db.models.isotto_order_model import IsottoOrderModel, ProductType, OrderStatus
from src.db.models.isotto_customer_model import IsottoCustomerModel

logger = logging.getLogger(__name__)


async def seed_isotto_catalog_data(db: AsyncSession) -> None:
    """
    Seed catalog data for ISOTTO Sport merch: suppliers, products, stock, team order.
    Idempotent -- checks if supplier data exists before seeding.
    """
    logger.info("Checking if ISOTTO Sport catalog data needs to be seeded...")

    # Check if suppliers already exist
    result = await db.execute(select(IsottoSupplierModel).limit(1))
    if result.scalar_one_or_none():
        logger.info("ISOTTO Sport catalog data already seeded. Skipping.")
        return

    logger.info("Seeding ISOTTO Sport catalog data...")

    # ================================================================
    # SUPPLIERS
    # ================================================================
    roly = IsottoSupplierModel(
        name="ROLY",
        code="ROLY",
        contact_person=None,
        phone=None,
        email=None,
        website="www.rfroly.com",
        default_lead_time_days=7,
        min_order_amount=Decimal("50.00"),
        is_preferred=True,
        is_active=True,
        notes="Spanish garment manufacturer. Preferred supplier for ISOTTO Sport. "
              "Wide range: t-shirts, polos, hoodies, jackets, caps, bags, mugs, aprons.",
    )

    fotl = IsottoSupplierModel(
        name="Fruit of the Loom",
        code="FOTL",
        contact_person=None,
        phone=None,
        email=None,
        website="www.fruitoftheloom.eu",
        default_lead_time_days=14,
        min_order_amount=Decimal("100.00"),
        is_preferred=False,
        is_active=True,
        notes="American basics. Reliable quality, competitive pricing on high-volume staples.",
    )

    db.add_all([roly, fotl])
    await db.flush()  # Get IDs assigned

    # ================================================================
    # CATALOG PRODUCTS (10 items)
    # ================================================================

    # 1. ROLY Bahrain T-Shirt (code 6502)
    bahrain_tshirt = IsottoCatalogProductModel(
        supplier_id=roly.id,
        supplier_product_code="6502",
        name="ROLY Bahrain T-Shirt",
        description="Lightweight technical t-shirt. Breathable fabric, ideal for sports and casual wear. "
                    "Best seller for team orders and events.",
        category=IsottoMerchCategory.TSHIRT,
        available_colors=["white", "black", "navy", "red", "grey"],
        available_sizes=["XS", "S", "M", "L", "XL", "XXL", "3XL"],
        supplier_unit_price=Decimal("3.50"),
        retail_base_price=Decimal("12.00"),
        personalization_markup=Decimal("5.00"),
        print_areas=["front", "back"],
        recommended_print_methods=["screen_print", "dtg"],
        has_sample_in_store=True,
        is_active=True,
        tags="tshirt,sport,team,event,bahrain,roly,bestseller",
    )

    # 2. ROLY Bahrain Polo (code 6632)
    bahrain_polo = IsottoCatalogProductModel(
        supplier_id=roly.id,
        supplier_product_code="6632",
        name="ROLY Bahrain Polo",
        description="Classic polo shirt with collar. Professional look for hospitality, "
                    "corporate events, and team uniforms.",
        category=IsottoMerchCategory.POLO,
        available_colors=["white", "black", "navy"],
        available_sizes=["S", "M", "L", "XL", "XXL"],
        supplier_unit_price=Decimal("7.00"),
        retail_base_price=Decimal("18.00"),
        personalization_markup=Decimal("6.00"),
        print_areas=["front", "left_sleeve"],
        recommended_print_methods=["embroidery", "screen_print"],
        has_sample_in_store=True,
        is_active=True,
        tags="polo,corporate,hospitality,team,roly,bahrain",
    )

    # 3. ROLY Montblanc Hoodie (code 1171)
    montblanc_hoodie = IsottoCatalogProductModel(
        supplier_id=roly.id,
        supplier_product_code="1171",
        name="ROLY Montblanc Hoodie",
        description="Heavy-weight hoodie with kangaroo pocket. Perfect for winter team gear, "
                    "casual merch, and outdoor events.",
        category=IsottoMerchCategory.HOODIE,
        available_colors=["black", "navy", "grey"],
        available_sizes=["S", "M", "L", "XL", "XXL"],
        supplier_unit_price=Decimal("12.00"),
        retail_base_price=Decimal("28.00"),
        personalization_markup=Decimal("7.00"),
        print_areas=["front", "back"],
        recommended_print_methods=["screen_print", "dtg"],
        has_sample_in_store=False,
        is_active=True,
        tags="hoodie,winter,casual,team,roly,montblanc",
    )

    # 4. ROLY Windbreaker Jacket (code 5060)
    windbreaker = IsottoCatalogProductModel(
        supplier_id=roly.id,
        supplier_product_code="5060",
        name="ROLY Windbreaker Jacket",
        description="Lightweight windbreaker with zip front. Water-resistant, "
                    "ideal for outdoor sports teams and branded corporate wear.",
        category=IsottoMerchCategory.JACKET,
        available_colors=["navy", "black"],
        available_sizes=["S", "M", "L", "XL", "XXL"],
        supplier_unit_price=Decimal("15.00"),
        retail_base_price=Decimal("32.00"),
        personalization_markup=Decimal("8.00"),
        print_areas=["front", "back"],
        recommended_print_methods=["embroidery", "vinyl"],
        has_sample_in_store=False,
        is_active=True,
        tags="jacket,windbreaker,outdoor,sport,team,roly",
    )

    # 5. ROLY Cotton Cap (code 7031)
    cotton_cap = IsottoCatalogProductModel(
        supplier_id=roly.id,
        supplier_product_code="7031",
        name="ROLY Cotton Cap",
        description="Classic 6-panel cotton cap with adjustable strap. "
                    "Events, promo, team headwear.",
        category=IsottoMerchCategory.CAP,
        available_colors=["white", "black", "navy", "red"],
        available_sizes=["ONE_SIZE"],
        supplier_unit_price=Decimal("2.50"),
        retail_base_price=Decimal("8.00"),
        personalization_markup=Decimal("4.00"),
        print_areas=["front"],
        recommended_print_methods=["embroidery"],
        has_sample_in_store=True,
        is_active=True,
        tags="cap,hat,promo,event,team,roly,cotton",
    )

    # 6. FOTL Valueweight T-Shirt (code 61036)
    fotl_tshirt = IsottoCatalogProductModel(
        supplier_id=fotl.id,
        supplier_product_code="61036",
        name="FOTL Valueweight T-Shirt",
        description="The classic Fruit of the Loom Valueweight tee. Budget-friendly, "
                    "high-volume staple for events and promo runs.",
        category=IsottoMerchCategory.TSHIRT,
        available_colors=["white", "black", "navy", "red", "royal_blue", "dark_green"],
        available_sizes=["S", "M", "L", "XL", "XXL", "3XL"],
        supplier_unit_price=Decimal("2.00"),
        retail_base_price=Decimal("8.00"),
        personalization_markup=Decimal("4.00"),
        print_areas=["front", "back"],
        recommended_print_methods=["screen_print", "dtg"],
        has_sample_in_store=True,
        is_active=True,
        tags="tshirt,budget,volume,event,promo,fotl,valueweight",
    )

    # 7. FOTL Premium Polo (code 63218)
    fotl_polo = IsottoCatalogProductModel(
        supplier_id=fotl.id,
        supplier_product_code="63218",
        name="FOTL Premium Polo",
        description="Premium polo shirt from Fruit of the Loom. "
                    "Heavier fabric, reinforced collar, corporate quality.",
        category=IsottoMerchCategory.POLO,
        available_colors=["white", "black", "navy"],
        available_sizes=["S", "M", "L", "XL", "XXL"],
        supplier_unit_price=Decimal("6.00"),
        retail_base_price=Decimal("16.00"),
        personalization_markup=Decimal("6.00"),
        print_areas=["front", "left_sleeve"],
        recommended_print_methods=["embroidery"],
        has_sample_in_store=False,
        is_active=True,
        tags="polo,premium,corporate,fotl",
    )

    # 8. ROLY Tote Bag (code 7501)
    tote_bag = IsottoCatalogProductModel(
        supplier_id=roly.id,
        supplier_product_code="7501",
        name="ROLY Tote Bag",
        description="Cotton tote bag. Eco-friendly promo item, event giveaway, "
                    "or branded shopping bag.",
        category=IsottoMerchCategory.BAG,
        available_colors=["white", "black", "navy"],
        available_sizes=["ONE_SIZE"],
        supplier_unit_price=Decimal("1.50"),
        retail_base_price=Decimal("5.00"),
        personalization_markup=Decimal("3.00"),
        print_areas=["front", "back"],
        recommended_print_methods=["screen_print", "sublimation"],
        has_sample_in_store=False,
        is_active=True,
        tags="bag,tote,eco,promo,event,roly",
    )

    # 9. ROLY Ceramic Mug (code 8501)
    ceramic_mug = IsottoCatalogProductModel(
        supplier_id=roly.id,
        supplier_product_code="8501",
        name="ROLY Ceramic Mug",
        description="Standard 330ml ceramic mug. Sublimation-ready white surface. "
                    "Great for personalized gifts and corporate branded mugs.",
        category=IsottoMerchCategory.MUG,
        available_colors=["white"],
        available_sizes=["ONE_SIZE"],
        supplier_unit_price=Decimal("2.00"),
        retail_base_price=Decimal("7.00"),
        personalization_markup=Decimal("4.00"),
        print_areas=["front"],
        recommended_print_methods=["sublimation", "transfer"],
        has_sample_in_store=False,
        is_active=True,
        tags="mug,ceramic,gift,corporate,sublimation,roly",
    )

    # 10. ROLY Chef Apron (code 9126)
    chef_apron = IsottoCatalogProductModel(
        supplier_id=roly.id,
        supplier_product_code="9126",
        name="ROLY Chef Apron",
        description="Full-length chef apron with front pocket. "
                    "Restaurants, pizzerias, cooking events. Embroidery or screen print.",
        category=IsottoMerchCategory.APRON,
        available_colors=["white", "black"],
        available_sizes=["ONE_SIZE"],
        supplier_unit_price=Decimal("5.00"),
        retail_base_price=Decimal("14.00"),
        personalization_markup=Decimal("5.00"),
        print_areas=["front"],
        recommended_print_methods=["embroidery", "screen_print"],
        has_sample_in_store=False,
        is_active=True,
        tags="apron,chef,restaurant,kitchen,hospitality,roly",
    )

    all_products = [
        bahrain_tshirt, bahrain_polo, montblanc_hoodie, windbreaker, cotton_cap,
        fotl_tshirt, fotl_polo, tote_bag, ceramic_mug, chef_apron,
    ]
    db.add_all(all_products)
    await db.flush()  # Get product IDs assigned

    # ================================================================
    # STOCK ENTRIES (popular combos for top sellers)
    # ================================================================

    stock_entries = []

    # Product 1: ROLY Bahrain T-Shirt stock
    for color, size, qty in [
        ("white", "L", 10),
        ("white", "M", 8),
        ("white", "XL", 5),
        ("black", "L", 6),
        ("black", "M", 4),
        ("navy", "L", 3),
    ]:
        stock_entries.append(IsottoCatalogStockModel(
            product_id=bahrain_tshirt.id,
            color=color,
            size=size,
            quantity_on_hand=qty,
            quantity_reserved=0,
        ))

    # Product 6: FOTL Valueweight T-Shirt stock
    for color, size, qty in [
        ("white", "L", 15),
        ("white", "M", 12),
        ("white", "XL", 8),
        ("black", "L", 10),
        ("black", "M", 8),
    ]:
        stock_entries.append(IsottoCatalogStockModel(
            product_id=fotl_tshirt.id,
            color=color,
            size=size,
            quantity_on_hand=qty,
            quantity_reserved=0,
        ))

    db.add_all(stock_entries)
    await db.flush()

    # ================================================================
    # TEAM ORDER: ASD Trapani Calcio (10-player demo)
    # ================================================================

    # Find the existing Angelo Kenel customer
    result = await db.execute(
        select(IsottoCustomerModel).where(IsottoCustomerModel.name == "Angelo Kenel")
    )
    angel = result.scalar_one_or_none()

    if not angel:
        logger.warning("Customer 'Angelo Kenel' not found. Skipping team order seeding.")
        await db.commit()
        logger.info("ISOTTO Sport catalog seeding completed (without team order).")
        return

    # Create the team order
    team_order = IsottoOrderModel(
        order_number="ORD-20260224-0001",
        title="ASD Trapani Calcio Team Kit",
        description="Full team kit for ASD Trapani Calcio. 10 personalized ROLY Bahrain T-Shirts "
                    "with player names and numbers. White shirts, navy text, Impact font.",
        customer_id=angel.id,
        product_type=ProductType.TSHIRT,
        status=OrderStatus.APPROVED,
        quantity=10,
        unit_price=Decimal("17.00"),
        total_price=Decimal("170.00"),
        is_team_order=True,
        team_name="ASD Trapani Calcio",
        assigned_to="Famous",
        proof_approved=True,
        proof_approved_at=datetime(2026, 2, 24, 9, 0, tzinfo=timezone.utc),
        quoted_at=datetime(2026, 2, 23, 14, 0, tzinfo=timezone.utc),
        approved_at=datetime(2026, 2, 24, 9, 30, tzinfo=timezone.utc),
        customer_notes="10 players. White shirts, navy personalization. Impact font, name + number on back.",
        production_notes="Use ROLY Bahrain 6502 white. All personalization on back. Navy text.",
    )

    db.add(team_order)
    await db.flush()  # Get order ID assigned

    # Create 10 line items (one per player)
    roster = [
        ("ROSSI", "10", "L", 1),
        ("BIANCHI", "7", "M", 2),
        ("FERRARA", "1", "XL", 3),
        ("MARINO", "9", "L", 4),
        ("COSTA", "3", "S", 5),
        ("RICCI", "5", "M", 6),
        ("BRUNO", "11", "XXL", 7),
        ("MORETTI", "8", "L", 8),
        ("ROMANO", "2", "M", 9),
        ("GALLI", "4", "L", 10),
    ]

    line_items = []
    for name_text, number_text, size, sort_order in roster:
        line_items.append(IsottoOrderLineItemModel(
            order_id=team_order.id,
            catalog_product_id=bahrain_tshirt.id,
            sort_order=sort_order,
            color="white",
            size=size,
            name_text=name_text,
            number_text=number_text,
            font_name="Impact",
            text_color="navy",
            artwork_placement="back",
            unit_price=Decimal("17.00"),
            status=LineItemStatus.PENDING,
        ))

    db.add_all(line_items)
    await db.commit()

    logger.info("ISOTTO Sport catalog seeding completed!")
    logger.info("  - 2 suppliers (ROLY [preferred], Fruit of the Loom)")
    logger.info("  - 10 catalog products:")
    logger.info("    - ROLY Bahrain T-Shirt (6502) [sample in store]")
    logger.info("    - ROLY Bahrain Polo (6632) [sample in store]")
    logger.info("    - ROLY Montblanc Hoodie (1171)")
    logger.info("    - ROLY Windbreaker Jacket (5060)")
    logger.info("    - ROLY Cotton Cap (7031) [sample in store]")
    logger.info("    - FOTL Valueweight T-Shirt (61036) [sample in store]")
    logger.info("    - FOTL Premium Polo (63218)")
    logger.info("    - ROLY Tote Bag (7501)")
    logger.info("    - ROLY Ceramic Mug (8501)")
    logger.info("    - ROLY Chef Apron (9126)")
    logger.info("  - 11 stock entries (6 for ROLY Bahrain, 5 for FOTL Valueweight)")
    logger.info("  - 1 team order: ASD Trapani Calcio (10 line items, APPROVED)")
