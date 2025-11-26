# File: src/services/pos_seeding_service.py
"""
POS Seeding Service - Populates demo products for Felix's Artemis store.
Runs on application startup to ensure demo data is available.
"""
import logging
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.models import ProductModel

logger = logging.getLogger(__name__)


async def seed_artemis_products(db: AsyncSession) -> None:
    """
    Seed initial products for Felix's Artemis Kräuter & Düfte store.
    Based on typical CBD shop inventory in Luzern, Switzerland.
    """
    logger.info("🌱 Checking if POS products need to be seeded...")

    # Check if products already exist
    result = await db.execute(select(ProductModel).limit(1))
    existing_product = result.scalar_one_or_none()

    if existing_product:
        logger.info("✅ POS products already seeded. Skipping.")
        return

    logger.info("🌱 Seeding demo products for Artemis store...")

    demo_products = [
        # ======= CBD PRODUCTS (Age-Restricted, Premium) =======
        {
            "sku": "CBD-OIL-10ML",
            "barcode": "7610000123456",
            "name": "CBD Oil 10% - 10ml",
            "description": "Premium full-spectrum CBD oil, Swiss quality, 10% concentration",
            "price": Decimal("49.90"),
            "cost": Decimal("25.00"),
            "stock_quantity": 50,
            "stock_alert_threshold": 10,
            "category": "CBD Oils",
            "tags": "cbd, oil, premium, swiss, full-spectrum",
            "is_active": True,
            "is_age_restricted": True,
            "vending_compatible": False,  # Oils not suitable for vending
            "vending_slot": None,
        },
        {
            "sku": "CBD-OIL-20ML",
            "barcode": "7610000123457",
            "name": "CBD Oil 20% - 10ml",
            "description": "High-potency CBD oil, 20% concentration for experienced users",
            "price": Decimal("89.90"),
            "cost": Decimal("45.00"),
            "stock_quantity": 30,
            "stock_alert_threshold": 5,
            "category": "CBD Oils",
            "tags": "cbd, oil, premium, high-potency",
            "is_active": True,
            "is_age_restricted": True,
            "vending_compatible": False,
            "vending_slot": None,
        },
        {
            "sku": "CBD-FLOWER-5G",
            "barcode": "7610000123458",
            "name": "CBD Flower 'Alpine Dream' - 5g",
            "description": "Organic Swiss CBD flower, <1% THC, aromatic and relaxing",
            "price": Decimal("35.00"),
            "cost": Decimal("18.00"),
            "stock_quantity": 100,
            "stock_alert_threshold": 20,
            "category": "CBD Flowers",
            "tags": "cbd, flower, organic, swiss, alpine",
            "is_active": True,
            "is_age_restricted": True,
            "vending_compatible": True,  # Can be sold in vending machine
            "vending_slot": 1,
        },
        {
            "sku": "CBD-PREROLL-1G",
            "barcode": "7610000123459",
            "name": "CBD Pre-Roll 1g (Pack of 3)",
            "description": "Ready-to-smoke CBD pre-rolls, convenient 3-pack",
            "price": Decimal("15.00"),
            "cost": Decimal("7.50"),
            "stock_quantity": 150,
            "stock_alert_threshold": 30,
            "category": "CBD Pre-Rolls",
            "tags": "cbd, pre-roll, ready-to-smoke, convenience",
            "is_active": True,
            "is_age_restricted": True,
            "vending_compatible": True,
            "vending_slot": 2,
        },

        # ======= SMOKING ACCESSORIES (Not Age-Restricted) =======
        {
            "sku": "PAPER-OCB-SLIM",
            "barcode": "7610000123460",
            "name": "OCB Slim Rolling Papers",
            "description": "Premium slim rolling papers, 32 leaves per pack",
            "price": Decimal("1.50"),
            "cost": Decimal("0.60"),
            "stock_quantity": 500,
            "stock_alert_threshold": 100,
            "category": "Smoking Accessories",
            "tags": "papers, rolling, ocb, slim",
            "is_active": True,
            "is_age_restricted": False,
            "vending_compatible": True,
            "vending_slot": 3,
        },
        {
            "sku": "GRINDER-METAL-4P",
            "barcode": "7610000123461",
            "name": "4-Piece Metal Grinder",
            "description": "Durable aluminum herb grinder with pollen catcher",
            "price": Decimal("12.90"),
            "cost": Decimal("6.00"),
            "stock_quantity": 75,
            "stock_alert_threshold": 15,
            "category": "Smoking Accessories",
            "tags": "grinder, metal, 4-piece, aluminum",
            "is_active": True,
            "is_age_restricted": False,
            "vending_compatible": True,
            "vending_slot": 4,
        },
        {
            "sku": "LIGHTER-CLIPPER",
            "barcode": "7610000123462",
            "name": "Clipper Lighter (Assorted Colors)",
            "description": "Refillable Clipper lighter, random color selection",
            "price": Decimal("2.50"),
            "cost": Decimal("1.00"),
            "stock_quantity": 200,
            "stock_alert_threshold": 50,
            "category": "Smoking Accessories",
            "tags": "lighter, clipper, refillable",
            "is_active": True,
            "is_age_restricted": False,
            "vending_compatible": True,
            "vending_slot": 5,
        },
        {
            "sku": "TIPS-RAW-PERFORATED",
            "barcode": "7610000123463",
            "name": "RAW Perforated Filter Tips",
            "description": "Natural unrefined filter tips, 50 per pack",
            "price": Decimal("1.20"),
            "cost": Decimal("0.50"),
            "stock_quantity": 300,
            "stock_alert_threshold": 60,
            "category": "Smoking Accessories",
            "tags": "tips, filters, raw, perforated",
            "is_active": True,
            "is_age_restricted": False,
            "vending_compatible": True,
            "vending_slot": 6,
        },

        # ======= VAPORIZERS & PREMIUM ITEMS =======
        {
            "sku": "VAPE-DAVINCI-IQ2",
            "barcode": "7610000123464",
            "name": "DaVinci IQ2 Vaporizer",
            "description": "Premium dry herb vaporizer with precise temperature control",
            "price": Decimal("299.00"),
            "cost": Decimal("200.00"),
            "stock_quantity": 5,
            "stock_alert_threshold": 2,
            "category": "Vaporizers",
            "tags": "vaporizer, davinci, premium, dry-herb",
            "is_active": True,
            "is_age_restricted": True,
            "vending_compatible": False,  # Too expensive for vending
            "vending_slot": None,
        },
        {
            "sku": "VAPE-PUFFCO",
            "barcode": "7610000123465",
            "name": "Puffco Peak Pro",
            "description": "Smart rig for concentrate enthusiasts, app-enabled",
            "price": Decimal("449.00"),
            "cost": Decimal("320.00"),
            "stock_quantity": 3,
            "stock_alert_threshold": 1,
            "category": "Vaporizers",
            "tags": "vaporizer, puffco, concentrate, smart",
            "is_active": True,
            "is_age_restricted": True,
            "vending_compatible": False,
            "vending_slot": None,
        },

        # ======= WELLNESS & LIFESTYLE =======
        {
            "sku": "TEA-CBD-RELAX",
            "barcode": "7610000123466",
            "name": "CBD Relaxation Tea - 20 Bags",
            "description": "Herbal tea blend with CBD, chamomile, and lavender",
            "price": Decimal("8.90"),
            "cost": Decimal("4.50"),
            "stock_quantity": 80,
            "stock_alert_threshold": 20,
            "category": "Wellness",
            "tags": "tea, cbd, relaxation, herbal",
            "is_active": True,
            "is_age_restricted": False,
            "vending_compatible": True,
            "vending_slot": 7,
        },
        {
            "sku": "BALM-CBD-MUSCLE",
            "barcode": "7610000123467",
            "name": "CBD Muscle Balm - 50ml",
            "description": "Topical CBD balm for sore muscles and joints",
            "price": Decimal("24.90"),
            "cost": Decimal("12.00"),
            "stock_quantity": 40,
            "stock_alert_threshold": 10,
            "category": "Wellness",
            "tags": "cbd, balm, topical, muscle, recovery",
            "is_active": True,
            "is_age_restricted": False,
            "vending_compatible": False,  # Topicals not in vending
            "vending_slot": None,
        },

        # ======= BESTSELLERS / HIGH TURNOVER =======
        {
            "sku": "COMBO-STARTER-KIT",
            "barcode": "7610000123468",
            "name": "Starter Kit (Papers + Tips + Lighter)",
            "description": "Perfect starter bundle for new customers",
            "price": Decimal("4.50"),
            "cost": Decimal("2.00"),
            "stock_quantity": 120,
            "stock_alert_threshold": 25,
            "category": "Bundles",
            "tags": "combo, starter, bundle, value",
            "is_active": True,
            "is_age_restricted": False,
            "vending_compatible": True,
            "vending_slot": 8,
        },
        {
            "sku": "CBD-GUMMIES-100MG",
            "barcode": "7610000123469",
            "name": "CBD Gummies - 10 pieces (100mg total)",
            "description": "Delicious fruit-flavored CBD gummies, 10mg per piece",
            "price": Decimal("14.90"),
            "cost": Decimal("7.00"),
            "stock_quantity": 90,
            "stock_alert_threshold": 20,
            "category": "CBD Edibles",
            "tags": "cbd, gummies, edibles, fruit, tasty",
            "is_active": True,
            "is_age_restricted": True,
            "vending_compatible": True,
            "vending_slot": 9,
        },

        # ======= SEASONAL / SPECIAL ITEMS =======
        {
            "sku": "XMAS-GIFT-BOX",
            "barcode": "7610000123470",
            "name": "Holiday Gift Box (CBD Sampler)",
            "description": "Curated CBD product sampler, perfect holiday gift",
            "price": Decimal("59.00"),
            "cost": Decimal("30.00"),
            "stock_quantity": 25,
            "stock_alert_threshold": 5,
            "category": "Gift Sets",
            "tags": "gift, holiday, christmas, sampler, cbd",
            "is_active": True,  # Set to False after holiday season
            "is_age_restricted": True,
            "vending_compatible": False,
            "vending_slot": None,
        },
        {
            "sku": "ASHTRAY-CERAMIC",
            "barcode": "7610000123471",
            "name": "Handmade Ceramic Ashtray",
            "description": "Artisan ceramic ashtray, Luzern local artist collaboration",
            "price": Decimal("18.00"),
            "cost": Decimal("9.00"),
            "stock_quantity": 15,
            "stock_alert_threshold": 3,
            "category": "Accessories",
            "tags": "ashtray, ceramic, handmade, local, art",
            "is_active": True,
            "is_age_restricted": False,
            "vending_compatible": False,
            "vending_slot": None,
        },

        # ======= TEST ITEMS (For demo purposes) =======
        {
            "sku": "TEST-OUT-OF-STOCK",
            "barcode": "7610000999998",
            "name": "Test Item (Out of Stock)",
            "description": "Demo product for testing stock alerts",
            "price": Decimal("1.00"),
            "cost": Decimal("0.50"),
            "stock_quantity": 0,  # Out of stock
            "stock_alert_threshold": 5,
            "category": "Test",
            "tags": "test, demo",
            "is_active": True,
            "is_age_restricted": False,
            "vending_compatible": False,
            "vending_slot": None,
        },
        {
            "sku": "TEST-INACTIVE",
            "barcode": "7610000999999",
            "name": "Test Item (Inactive)",
            "description": "Demo product for testing inactive state",
            "price": Decimal("1.00"),
            "cost": Decimal("0.50"),
            "stock_quantity": 100,
            "stock_alert_threshold": 10,
            "category": "Test",
            "tags": "test, demo, inactive",
            "is_active": False,  # Inactive - should not appear in sales
            "is_age_restricted": False,
            "vending_compatible": False,
            "vending_slot": None,
        },
    ]

    # Insert products
    for product_data in demo_products:
        product = ProductModel(**product_data)
        db.add(product)

    await db.commit()

    logger.info(f"✅ Seeded {len(demo_products)} demo products for Artemis store!")
    logger.info("   - 4 CBD products (oils, flowers, pre-rolls)")
    logger.info("   - 4 smoking accessories (papers, grinder, lighter, tips)")
    logger.info("   - 2 premium vaporizers (DaVinci, Puffco)")
    logger.info("   - 2 wellness items (tea, muscle balm)")
    logger.info("   - 2 bestsellers (starter kit, gummies)")
    logger.info("   - 2 seasonal/special items (gift box, ashtray)")
    logger.info("   - 2 test items (out-of-stock, inactive)")
    logger.info("   📦 Total: 18 products ready for Felix's demo!")
