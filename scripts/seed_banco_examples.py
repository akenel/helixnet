"""seed_banco_examples.py — clean staging's operational data + seed 12 real example products
that span the BL-96 skeleton (every category + every class, incl. 18+ and café-VAT items).

DESTRUCTIVE: truncates products / transactions / customers (+ their dependents). KEEPS the
reference catalogue, store settings and Keycloak users. Meant for staging/sandbox, never prod.

Run:  docker exec -i helix-platform-banco-staging python scripts/seed_banco_examples.py
"""
import asyncio
from decimal import Decimal

from sqlalchemy import text

from src.db.database import get_db_session_context
from src.db.models.product_model import ProductModel
from src.services.catalog_taxonomy import class_is_age_restricted

# (name, category, class, barcode, price) — is_age_restricted is DERIVED from the class.
EXAMPLES = [
    ("RAW Classic King Size Slim Papers",   "Papers & Filters",     "standard",          "716165179924", 2.50),
    ("Clipper Lighter Classic Large",       "Lighters",             "standard",          "8412679110014", 3.00),
    ("Black Leaf 4-Part Grinder 50mm",      "Grinders",             "standard",          None,            24.90),
    ("HempSana CBD Cream 40ml",             "Creams & Topicals",    "cbd_hemp",          None,            39.00),
    ("CBD Blüten Gorilla Glue 5g",          "CBD & Hemp",           "cbd_hemp",          None,            45.00),
    ("CBD Gummibärchen 10er",               "Edibles",              "cbd_hemp",          None,            19.00),
    ("Pueblo Classic Tabak RYO 25g",        "Tobacco & Cigarettes", "tobacco_nicotine",  "7613311110014", 9.20),
    ("Swiss Smoke Shisha Tabak Mango 50g",  "Tobacco & Cigarettes", "tobacco_nicotine",  None,            12.90),
    ("Glass Beaker Ice Bong 30cm",          "Pipes & Bongs",        "standard",          None,            59.00),
    ("Storz & Bickel Mighty+ Vaporizer",    "Vaporizers",           "standard",          None,            379.00),
    ("Espresso",                            "Café",                 "cafe_food",         None,            4.50),
    ("Hausgemachter Schoko-Muffin",         "Café",                 "cafe_food",         None,            3.80),
]

# Operational tables to wipe (only the ones that exist; CASCADE clears their dependents).
_WIPE = [
    "products", "transactions", "line_items", "customers", "credit_transactions",
    "product_barcodes", "pos_stock_movements", "cash_shifts", "cash_movements",
]


async def main() -> None:
    async with get_db_session_context() as db:
        present = {r[0] for r in (await db.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))).all()}
        targets = [t for t in _WIPE if t in present]
        await db.execute(text(f"TRUNCATE TABLE {', '.join(targets)} RESTART IDENTITY CASCADE"))

        for i, (name, cat, cls, bc, price) in enumerate(EXAMPLES, start=1):
            db.add(ProductModel(
                sku=f"EX-{i:03d}",
                barcode=bc,
                name=name,
                category=cat,
                product_class=cls,
                is_age_restricted=class_is_age_restricted(cls),
                price=Decimal(str(price)),
                stock_quantity=0,
                is_active=True,
            ))
        await db.commit()

    print(f"WIPED: {', '.join(targets)}")
    print(f"SEEDED {len(EXAMPLES)} example products across the skeleton.")
    print("18+ ones:", ", ".join(n for n, c, cl, b, p in EXAMPLES if class_is_age_restricted(cl)))


if __name__ == "__main__":
    asyncio.run(main())
