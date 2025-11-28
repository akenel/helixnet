"""
Artemis Headshop Product Seeding Service
Realistic product catalog for Felix's shop (25-year veteran)
"""

from decimal import Decimal
from typing import List, Dict
from sqlalchemy.orm import Session

from src.db.models.product_model import Product
from src.db.database import get_db


# Swiss VAT Rates (2025)
VAT_STANDARD = Decimal("8.1")  # Most products
VAT_REDUCED = Decimal("2.5")   # Medical CBD oils
VAT_EXEMPT = Decimal("0.0")    # Exports (not used for Felix)


def get_artemis_product_seed_data() -> List[Dict]:
    """
    20 realistic headshop products based on Felix's 25-year expertise

    Categories:
    - Smoking Accessories (60% of sales)
    - CBD Products (25% of sales)
    - Vaporizers (10% of sales)
    - Miscellaneous (5% of sales)

    VAT-Compliant:
    - Standard 8.1% for most products
    - Reduced 2.5% for medical CBD oils
    - All prices are GROSS (incl. VAT) - Swiss consumer standard
    """

    return [
        # ========================================
        # SMOKING ACCESSORIES (60% of sales)
        # ========================================

        # Bongs/Water Pipes (high margin, flagship)
        {
            "sku": "BONG-EHLE-250",
            "name": "Ehle Glass Bong 250ml",
            "description_de": "Premium Glasbong, handgefertigt in Deutschland, 25cm Höhe",
            "description_en": "Premium glass bong, handcrafted in Germany, 25cm height",
            "category": "bongs",
            "subcategory": "glass",
            "brand": "Ehle Glass",
            "price_gross": Decimal("120.00"),  # Including VAT
            "vat_rate": VAT_STANDARD,
            "cost": Decimal("70.00"),  # Margin: ~42%
            "stock": 5,
            "min_stock": 2,
            "supplier": "Ehle Glass Germany",
            "age_restricted": True,
            "requires_id": True,
            "thc_limit": None,
            "active": True,
            "tags": ["premium", "glass", "german", "bestseller"]
        },
        {
            "sku": "BONG-ACRY-001",
            "name": "Acrylic Bong Rainbow 30cm",
            "description_de": "Robuste Acrylbong, ideal für Einsteiger, Regenbogenfarben",
            "description_en": "Durable acrylic bong, ideal for beginners, rainbow colors",
            "category": "bongs",
            "subcategory": "acrylic",
            "brand": "Generic",
            "price_gross": Decimal("25.00"),
            "vat_rate": VAT_STANDARD,
            "cost": Decimal("12.00"),  # Margin: ~52%
            "stock": 15,
            "min_stock": 10,
            "supplier": "China Wholesale",
            "age_restricted": True,
            "requires_id": True,
            "thc_limit": None,
            "active": True,
            "tags": ["budget", "beginner", "colorful"]
        },

        # Grinders (very high margin)
        {
            "sku": "GRIND-SPACE-4P",
            "name": "Space Case Grinder 4-Piece Titanium",
            "description_de": "4-teiliger Premium Grinder, Titanium-Beschichtung, Pollenfänger",
            "description_en": "4-piece premium grinder, titanium-coated, pollen catcher",
            "category": "grinders",
            "subcategory": "metal",
            "brand": "Space Case",
            "price_gross": Decimal("65.00"),
            "vat_rate": VAT_STANDARD,
            "cost": Decimal("28.00"),  # Margin: ~57%
            "stock": 20,
            "min_stock": 10,
            "supplier": "Space Case USA",
            "age_restricted": False,
            "requires_id": False,
            "thc_limit": None,
            "active": True,
            "tags": ["premium", "titanium", "pollen-catcher"]
        },
        {
            "sku": "GRIND-PLT-001",
            "name": "Plastic Grinder 2-Piece",
            "description_de": "Einfacher Plastik Grinder, 2-teilig, verschiedene Farben",
            "description_en": "Simple plastic grinder, 2-piece, various colors",
            "category": "grinders",
            "subcategory": "plastic",
            "brand": "Generic",
            "price_gross": Decimal("5.00"),
            "vat_rate": VAT_STANDARD,
            "cost": Decimal("1.50"),  # Margin: ~70%
            "stock": 50,
            "min_stock": 30,
            "supplier": "China Wholesale",
            "age_restricted": False,
            "requires_id": False,
            "thc_limit": None,
            "active": True,
            "tags": ["budget", "disposable", "stocking-stuffer"]
        },

        # Rolling Papers (volume sellers, lower margin)
        {
            "sku": "PAPER-OCB-SLIM",
            "name": "OCB Premium Slim Papers",
            "description_de": "Lange Blättchen, chlorfrei, 32 Blatt pro Heft",
            "description_en": "Long rolling papers, chlorine-free, 32 sheets per booklet",
            "category": "papers",
            "subcategory": "slim",
            "brand": "OCB",
            "price_gross": Decimal("1.50"),
            "vat_rate": VAT_STANDARD,
            "cost": Decimal("0.90"),  # Margin: ~40%
            "stock": 200,
            "min_stock": 100,
            "supplier": "OCB Spain",
            "age_restricted": False,
            "requires_id": False,
            "thc_limit": None,
            "active": True,
            "tags": ["bestseller", "slim", "chlorine-free"]
        },
        {
            "sku": "PAPER-RAW-KING",
            "name": "RAW King Size Organic Hemp Papers",
            "description_de": "King Size Bio-Hanf Blättchen, ungebleicht, 50 Stück",
            "description_en": "King size organic hemp papers, unbleached, 50 count",
            "category": "papers",
            "subcategory": "king-size",
            "brand": "RAW",
            "price_gross": Decimal("2.50"),
            "vat_rate": VAT_STANDARD,
            "cost": Decimal("1.50"),  # Margin: ~40%
            "stock": 150,
            "min_stock": 80,
            "supplier": "RAW Spain",
            "age_restricted": False,
            "requires_id": False,
            "thc_limit": None,
            "active": True,
            "tags": ["organic", "hemp", "king-size"]
        },

        # Lighters (impulse buy, upsell item)
        {
            "sku": "LIGHT-CLIP-001",
            "name": "Clipper Lighter (Refillable)",
            "description_de": "Nachfüllbares Feuerzeug, austauschbarer Feuerstein, Zufallsdesign",
            "description_en": "Refillable lighter, replaceable flint, random design",
            "category": "lighters",
            "subcategory": "clipper",
            "brand": "Clipper",
            "price_gross": Decimal("2.00"),
            "vat_rate": VAT_STANDARD,
            "cost": Decimal("1.20"),  # Margin: ~40%
            "stock": 100,
            "min_stock": 50,
            "supplier": "Clipper Spain",
            "age_restricted": False,
            "requires_id": False,
            "thc_limit": None,
            "active": True,
            "tags": ["refillable", "impulse-buy", "freebie-option"]
        },
        {
            "sku": "LIGHT-ZIPPO-001",
            "name": "Zippo Lighter Classic Chrome",
            "description_de": "Klassisches Zippo Benzinfeuerzeug, lebenslange Garantie",
            "description_en": "Classic Zippo lighter, lifetime warranty, chrome finish",
            "category": "lighters",
            "subcategory": "zippo",
            "brand": "Zippo",
            "price_gross": Decimal("35.00"),
            "vat_rate": VAT_STANDARD,
            "cost": Decimal("22.00"),  # Margin: ~37%
            "stock": 10,
            "min_stock": 5,
            "supplier": "Zippo USA",
            "age_restricted": False,
            "requires_id": False,
            "thc_limit": None,
            "active": True,
            "tags": ["premium", "lifetime-warranty", "collector"]
        },

        # Filters/Tips
        {
            "sku": "FILT-RAW-TIPS",
            "name": "RAW Pre-Rolled Tips (200 count)",
            "description_de": "Vorgefertigte Filter Tips, ungebleicht, 200 Stück",
            "description_en": "Pre-rolled filter tips, unbleached, 200 count",
            "category": "filters",
            "subcategory": "pre-rolled",
            "brand": "RAW",
            "price_gross": Decimal("4.50"),
            "vat_rate": VAT_STANDARD,
            "cost": Decimal("2.50"),  # Margin: ~44%
            "stock": 80,
            "min_stock": 40,
            "supplier": "RAW Spain",
            "age_restricted": False,
            "requires_id": False,
            "thc_limit": None,
            "active": True,
            "tags": ["pre-rolled", "unbleached", "convenient"]
        },

        # Cleaning Supplies (upsell with bongs)
        {
            "sku": "CLEAN-ISO-500",
            "name": "Isopropanol Cleaning Solution 500ml",
            "description_de": "Reinigungsalkohol 99%, ideal für Glasbongs und Pfeifen",
            "description_en": "Isopropyl alcohol 99%, ideal for glass bongs and pipes",
            "category": "accessories",
            "subcategory": "cleaning",
            "brand": "Generic",
            "price_gross": Decimal("12.00"),
            "vat_rate": VAT_STANDARD,
            "cost": Decimal("5.00"),  # Margin: ~58%
            "stock": 30,
            "min_stock": 15,
            "supplier": "Chemical Supplier CH",
            "age_restricted": False,
            "requires_id": False,
            "thc_limit": None,
            "active": True,
            "tags": ["cleaning", "upsell-with-bong", "maintenance"]
        },

        # ========================================
        # CBD PRODUCTS (25% of sales, GROWING)
        # ========================================

        # CBD Flowers (legal <1% THC)
        {
            "sku": "CBD-FLW-HAZE",
            "name": "CBD Flowers - Lemon Haze (5g)",
            "description_de": "CBD Blüten Lemon Haze, <1% THC, 12% CBD, Bio-Anbau Schweiz",
            "description_en": "CBD flowers Lemon Haze, <1% THC, 12% CBD, organic Swiss-grown",
            "category": "cbd",
            "subcategory": "flowers",
            "brand": "SwissCBD",
            "price_gross": Decimal("45.00"),
            "vat_rate": VAT_STANDARD,  # Flowers = standard VAT
            "cost": Decimal("25.00"),  # Margin: ~44%
            "stock": 20,
            "min_stock": 10,
            "supplier": "SwissCBD Farms",
            "age_restricted": True,
            "requires_id": True,
            "thc_limit": Decimal("0.8"),  # <1% THC (Swiss law)
            "cbd_content": Decimal("12.0"),
            "lab_cert_required": True,
            "batch_number": "HAZE-2025-Q4-001",
            "active": True,
            "tags": ["cbd", "swiss", "organic", "lab-tested"]
        },
        {
            "sku": "CBD-FLW-OG",
            "name": "CBD Flowers - OG Kush (5g)",
            "description_de": "CBD Blüten OG Kush, <1% THC, 15% CBD, Indoor-Anbau",
            "description_en": "CBD flowers OG Kush, <1% THC, 15% CBD, indoor-grown",
            "category": "cbd",
            "subcategory": "flowers",
            "brand": "SwissCBD",
            "price_gross": Decimal("50.00"),
            "vat_rate": VAT_STANDARD,
            "cost": Decimal("28.00"),  # Margin: ~44%
            "stock": 15,
            "min_stock": 8,
            "supplier": "SwissCBD Farms",
            "age_restricted": True,
            "requires_id": True,
            "thc_limit": Decimal("0.9"),
            "cbd_content": Decimal("15.0"),
            "lab_cert_required": True,
            "batch_number": "OG-2025-Q4-002",
            "active": True,
            "tags": ["cbd", "premium", "indoor", "high-cbd"]
        },

        # CBD Oils (medicinal = reduced VAT!)
        {
            "sku": "CBD-OIL-10",
            "name": "CBD Oil 10% Full Spectrum (10ml)",
            "description_de": "CBD Öl 10%, Vollspektrum, MCT-Trägeröl, <1% THC",
            "description_en": "CBD oil 10%, full spectrum, MCT carrier oil, <1% THC",
            "category": "cbd",
            "subcategory": "oils",
            "brand": "Kannaway",
            "price_gross": Decimal("60.00"),
            "vat_rate": VAT_REDUCED,  # MEDICINAL = 2.5% VAT
            "cost": Decimal("32.00"),  # Margin: ~47%
            "stock": 25,
            "min_stock": 12,
            "supplier": "Kannaway Switzerland",
            "age_restricted": True,
            "requires_id": True,
            "thc_limit": Decimal("0.5"),
            "cbd_content": Decimal("10.0"),
            "lab_cert_required": True,
            "batch_number": "OIL10-2025-Q4-003",
            "expiry_date": "2026-11-01",
            "active": True,
            "tags": ["cbd", "oil", "medicinal", "reduced-vat"]
        },
        {
            "sku": "CBD-OIL-20",
            "name": "CBD Oil 20% Full Spectrum (10ml)",
            "description_de": "CBD Öl 20%, Vollspektrum, MCT-Trägeröl, <1% THC, Premium",
            "description_en": "CBD oil 20%, full spectrum, MCT carrier oil, <1% THC, premium",
            "category": "cbd",
            "subcategory": "oils",
            "brand": "Kannaway",
            "price_gross": Decimal("100.00"),
            "vat_rate": VAT_REDUCED,  # MEDICINAL = 2.5% VAT
            "cost": Decimal("55.00"),  # Margin: ~45%
            "stock": 15,
            "min_stock": 8,
            "supplier": "Kannaway Switzerland",
            "age_restricted": True,
            "requires_id": True,
            "thc_limit": Decimal("0.6"),
            "cbd_content": Decimal("20.0"),
            "lab_cert_required": True,
            "batch_number": "OIL20-2025-Q4-004",
            "expiry_date": "2026-11-01",
            "active": True,
            "tags": ["cbd", "oil", "premium", "high-strength", "reduced-vat"]
        },

        # ========================================
        # VAPORIZERS (10% of sales, HIGH margin)
        # ========================================

        {
            "sku": "VAPE-VOLCANO",
            "name": "Storz & Bickel Volcano Classic",
            "description_de": "Premium Tisch-Vaporizer, medizinische Qualität, 3 Jahre Garantie",
            "description_en": "Premium desktop vaporizer, medical grade, 3-year warranty",
            "category": "vaporizers",
            "subcategory": "desktop",
            "brand": "Storz & Bickel",
            "price_gross": Decimal("700.00"),
            "vat_rate": VAT_STANDARD,
            "cost": Decimal("480.00"),  # Margin: ~31% (brand controlled)
            "stock": 2,
            "min_stock": 1,
            "supplier": "Storz & Bickel Germany",
            "age_restricted": False,
            "requires_id": False,
            "thc_limit": None,
            "warranty_years": 3,
            "active": True,
            "tags": ["premium", "medical-grade", "desktop", "flagship"]
        },
        {
            "sku": "VAPE-MIGHTY",
            "name": "Storz & Bickel Mighty+ Portable",
            "description_de": "Tragbarer Vaporizer, USB-C, Supercharge-Funktion, 2 Jahre Garantie",
            "description_en": "Portable vaporizer, USB-C, supercharge function, 2-year warranty",
            "category": "vaporizers",
            "subcategory": "portable",
            "brand": "Storz & Bickel",
            "price_gross": Decimal("350.00"),
            "vat_rate": VAT_STANDARD,
            "cost": Decimal("240.00"),  # Margin: ~31%
            "stock": 5,
            "min_stock": 2,
            "supplier": "Storz & Bickel Germany",
            "age_restricted": False,
            "requires_id": False,
            "thc_limit": None,
            "warranty_years": 2,
            "active": True,
            "tags": ["portable", "usb-c", "bestseller"]
        },
        {
            "sku": "VAPE-DYNAVAP",
            "name": "DynaVap M 2024 Edition",
            "description_de": "Mechanischer Vaporizer, keine Batterie, lebenslange Garantie",
            "description_en": "Mechanical vaporizer, battery-free, lifetime warranty",
            "category": "vaporizers",
            "subcategory": "mechanical",
            "brand": "DynaVap",
            "price_gross": Decimal("80.00"),
            "vat_rate": VAT_STANDARD,
            "cost": Decimal("45.00"),  # Margin: ~44%
            "stock": 12,
            "min_stock": 6,
            "supplier": "DynaVap USA",
            "age_restricted": False,
            "requires_id": False,
            "thc_limit": None,
            "warranty_years": None,  # Lifetime
            "active": True,
            "tags": ["budget", "mechanical", "lifetime-warranty"]
        },

        # ========================================
        # MISCELLANEOUS (5% of sales)
        # ========================================

        {
            "sku": "MERCH-SHIRT-420",
            "name": "420 T-Shirt Cotton Black (L)",
            "description_de": "Baumwoll T-Shirt, 420 Logo, schwarz, Größe L",
            "description_en": "Cotton t-shirt, 420 logo, black, size L",
            "category": "merchandise",
            "subcategory": "clothing",
            "brand": "Artemis",
            "price_gross": Decimal("25.00"),
            "vat_rate": VAT_STANDARD,
            "cost": Decimal("10.00"),  # Margin: ~60%
            "stock": 20,
            "min_stock": 10,
            "supplier": "Print Shop Bern",
            "age_restricted": False,
            "requires_id": False,
            "thc_limit": None,
            "active": True,
            "tags": ["merch", "clothing", "branding"]
        },
        {
            "sku": "BOOK-GROW-101",
            "name": "The Cannabis Grow Bible (German Edition)",
            "description_de": "Anbau-Handbuch für Hobbygrower, 400 Seiten, illustriert",
            "description_en": "Cultivation handbook for hobby growers, 400 pages, illustrated",
            "category": "books",
            "subcategory": "cultivation",
            "brand": "Green Candy Press",
            "price_gross": Decimal("30.00"),
            "vat_rate": VAT_REDUCED,  # BOOKS = 2.5% VAT
            "cost": Decimal("18.00"),  # Margin: ~40%
            "stock": 8,
            "min_stock": 3,
            "supplier": "Green Candy Press",
            "age_restricted": False,
            "requires_id": False,
            "thc_limit": None,
            "active": True,
            "tags": ["book", "education", "reduced-vat"]
        },
        {
            "sku": "SCALE-DIGI-001",
            "name": "Digital Pocket Scale 0.01g Precision",
            "description_de": "Digitale Taschenwaage, 0.01g Genauigkeit, 200g Maximalgewicht",
            "description_en": "Digital pocket scale, 0.01g precision, 200g max weight",
            "category": "accessories",
            "subcategory": "scales",
            "brand": "Generic",
            "price_gross": Decimal("15.00"),
            "vat_rate": VAT_STANDARD,
            "cost": Decimal("7.00"),  # Margin: ~53%
            "stock": 25,
            "min_stock": 12,
            "supplier": "China Wholesale",
            "age_restricted": False,
            "requires_id": False,
            "thc_limit": None,
            "active": True,
            "tags": ["scale", "precision", "legal-use-only"]
        },
    ]


def seed_artemis_products(db: Session) -> int:
    """
    Seed database with Artemis headshop products

    Returns:
        int: Number of products created
    """
    products_data = get_artemis_product_seed_data()
    created_count = 0

    for data in products_data:
        # Check if product already exists
        existing = db.query(Product).filter(Product.sku == data['sku']).first()

        if not existing:
            # Calculate net price from gross
            gross = data['price_gross']
            vat_rate = data['vat_rate']
            net = gross / (1 + vat_rate / 100)
            vat_amount = gross - net

            # Create product
            product = Product(
                sku=data['sku'],
                name=data['name'],
                description=data.get('description_en', ''),  # Default to English
                category=data['category'],
                subcategory=data.get('subcategory'),
                brand=data.get('brand'),
                price_net=net,
                price_gross=gross,
                vat_rate=vat_rate,
                vat_amount=vat_amount,
                cost=data['cost'],
                stock=data['stock'],
                min_stock=data.get('min_stock', 0),
                supplier=data.get('supplier'),
                age_restricted=data.get('age_restricted', False),
                requires_id=data.get('requires_id', False),
                active=data['active'],
                # CBD-specific fields
                thc_limit=data.get('thc_limit'),
                cbd_content=data.get('cbd_content'),
                lab_cert_required=data.get('lab_cert_required', False),
                batch_number=data.get('batch_number'),
                expiry_date=data.get('expiry_date'),
                # Warranty/other
                warranty_years=data.get('warranty_years'),
                tags=data.get('tags', []),
            )

            db.add(product)
            created_count += 1

    db.commit()
    return created_count


def print_product_summary():
    """Print summary of seeded products for demo"""
    products = get_artemis_product_seed_data()

    print("=" * 80)
    print("ARTEMIS HEADSHOP PRODUCT CATALOG")
    print("=" * 80)
    print(f"Total Products: {len(products)}")
    print()

    # Group by category
    by_category = {}
    for p in products:
        cat = p['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(p)

    # Print by category
    for cat, items in sorted(by_category.items()):
        print(f"\n{cat.upper()} ({len(items)} products)")
        print("-" * 80)

        total_value = sum(p['price_gross'] * p['stock'] for p in items)

        for p in items:
            vat_symbol = "⭐" if p['vat_rate'] == VAT_REDUCED else ""
            stock_value = p['price_gross'] * p['stock']

            print(f"  [{p['sku']}] {p['name']}")
            print(f"    Price: CHF {p['price_gross']} (VAT {p['vat_rate']}%) {vat_symbol}")
            print(f"    Stock: {p['stock']} units (CHF {stock_value:.2f} value)")
            print()

        print(f"  Category Total Value: CHF {total_value:.2f}")

    # Total inventory value
    total_inv_value = sum(p['price_gross'] * p['stock'] for p in products)
    print()
    print("=" * 80)
    print(f"TOTAL INVENTORY VALUE: CHF {total_inv_value:.2f}")
    print("=" * 80)


if __name__ == "__main__":
    # Print summary (for demo/testing)
    print_product_summary()

    # Uncomment to seed database
    # db = next(get_db())
    # count = seed_artemis_products(db)
    # print(f"\n✅ Seeded {count} products into database")
