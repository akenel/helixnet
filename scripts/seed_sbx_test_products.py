"""seed_sbx_test_products.py — a varied ~40-product TEST catalog for SANDBOX play.

Purpose (Angel 2026-07-08): a hand-picked spread of realistic head-shop products so we can
exercise the mobile views + workflows (badges, 18+ gate, descriptions, adopt/cleanup) and test
the BL-18 description-scrape cron. Every name is run through the REAL classifier, so this set
ALSO regression-tests the P0 fix + badges on a diverse catalog. ~half the descriptions are left
BLANK on purpose (the cron's job is to fill them).

SANDBOX ONLY. Idempotent: wipes prior SBXTEST-* rows, re-seeds. SKU prefix SBXTEST- = easy cleanup.

Run inside the sandbox container (scripts/ not mounted — docker cp first):
    docker cp scripts/seed_sbx_test_products.py helix-platform-sandbox:/app/scripts/
    docker exec -w /app -e PYTHONPATH=/app helix-platform-sandbox python /app/scripts/seed_sbx_test_products.py
"""
import asyncio
from decimal import Decimal

from sqlalchemy import delete, select, func

from src.db.database import get_db_session_context
from src.db.models.product_model import ProductModel
from src.services.catalog_taxonomy import classify

# (name, price, description|None)  — None/"" = blank on purpose (cron fills it)
ITEMS = [
    # --- Tobacco / cigars / cigarillos / pouches (must be 18+) ---
    ("Marlboro Gold 10x20cig", 90.00, None),
    ("Parisienne Jaune Box 8x25cig", 88.00, None),
    ("American Spirit Tabak Dose 75g", 42.00, "Loose rolling tobacco, additive-free Virginia blend."),
    ("Swisher Sweets Classic Cigarillos 2er", 4.50, None),           # P0 leak type
    ("Backwoods Honey Berry 5er", 13.00, "Natural leaf-wrapped cigars, honey-berry aroma."),
    ("Al Fakher Blueberry Shisha Tabak 50g", 12.00, None),
    ("Elf Nicotine Pouches Polar Mint 20mg/g", 6.50, None),         # P0 leak type
    # --- Nicotine vapes (18+) ---
    ("Elfbar 600 Blueberry 20mg", 9.00, "600-puff disposable, 20mg nic salt, blueberry."),
    ("Lost Mary BM6000 Cherry Ice 20mg", 22.00, None),
    ("Vozol Gear 7000 Watermelon 20mg", 24.00, "7000-puff rechargeable disposable, 20mg."),
    # --- CBD 18+ (flower/hash/vape) ---
    ("CBDeluxe White Widow Indoor 10g", 65.00, "Indoor CBD flower, <1% THC, hand-trimmed."),
    ("Starbuds OG Kush CBD 3g", 25.00, None),
    ("Harmony CBD E-Liquid 100mg Mango 10ml", 19.90, "CBD vape liquid, 100mg, mango."),
    # --- CBD open (oils/seeds/cosmetics — NOT 18+) ---
    ("CBD Öl 10% Full Spectrum 10ml", 59.00, "Full-spectrum CBD oil, 10%, MCT carrier."),
    ("Kannabia CBD Autoflower Samen 5 Stk", 35.00, None),
    ("Hemp Sana CBD Salbe 50ml", 24.00, "CBD topical balm for skin, 50ml."),
    # --- Papers & filters (open) ---
    ("OCB Premium Slim Papers + Tips", 2.20, None),
    ("RAW Classic King Size Slim", 1.80, "Unbleached, unrefined rolling papers, king size slim."),
    ("Gizeh Filter Tips 6mm 100er", 1.50, None),
    ("Purize Xtra Slim Aktivkohlefilter 50er", 8.50, None),
    # --- Vape hardware (open — no nicotine) ---
    ("Innokin Endura T18 Vaping System", 34.00, "Complete starter vaping kit, refillable."),
    ("GeekVape Aegis Legend 5 Kit", 69.00, None),
    ("Elfbar ELFA Refillable Pod 1.1Ohm 2pcs", 6.00, "Empty refillable replacement pods, no liquid."),
    # --- Lighters / grinders (standard) ---
    ("Clipper Feuerzeug Metall Micro Blue", 12.00, None),
    ("Bic Maxi Feuerzeug Sortiert", 2.50, "Classic maxi lighter, assorted colours."),
    ("Grinder Alu 4-teilig 50mm", 15.00, None),
    # --- Pipes / bongs (standard) ---
    ("Glasbong Beaker Clear 30cm", 45.00, "Borosilicate beaker bong, 30cm, incl. bowl."),
    ("Holzpfeife klein Natur", 9.00, None),
    ("Chillum Glas bunt 10cm", 6.50, None),
    # --- Accessories (standard) ---
    ("Gizeh Rolling Tray Metall Medium", 8.00, None),
    ("Feinwaage Digital 100g/0.01g", 24.00, "Precision pocket scale, 100g x 0.01g."),
    ("Stashbox Metall klein", 11.00, None),
    ("Kavatza Tabaktasche Small", 29.00, "Rolling pouch/organizer — accessory, holds papers + tin."),  # must NOT be 18+
    # --- Standard / other ---
    ("Remedy Kombucha Ginger Lemon 250ml", 3.50, None),
    ("Nag Champa Räucherstäbchen 15g", 2.50, "Classic incense sticks, sandalwood-champa."),
    ("Amethyst Armband Perlen", 14.00, None),
    # --- Edge cases (verify the gate does the RIGHT thing) ---
    ("Elf Bar No Nic 0mg Strawberry Disposable", 8.00, None),        # 0mg → must stay OPEN
    ("Absinth Löffel Antik Messing", 16.00, "Antique-style absinthe spoon — accessory."),  # NOT alcohol
    ("Real Leaf Tabakersatz Kräutermischung 30g", 12.00, None),      # herbal substitute → OPEN
    ("Natural Rebel Permanent Marker Schwarz", 4.00, "Permanent marker, black."),          # P0 over-gate type → standard
]


async def main() -> None:
    async with get_db_session_context() as db:
        await db.execute(delete(ProductModel).where(ProductModel.sku.like("SBXTEST-%")))
        rows = []
        for i, (name, price, desc) in enumerate(ITEMS, start=1):
            cat, cls, age = classify(name)
            rows.append(ProductModel(
                sku=f"SBXTEST-{i:03d}",
                barcode=None,
                name=name,
                description=(desc or None),
                price=Decimal(str(price)),
                cost=None,
                stock_quantity=0,
                category=cat,
                product_class=cls,
                is_age_restricted=bool(age),
                is_active=True,
                supplier_name="Artemis (test)",
            ))
        db.add_all(rows)
        await db.commit()

    print(f"\n=== SEEDED {len(ITEMS)} SBXTEST- products ===")
    print(f"{'CLASS':<18}{'18+':<5}{'DESC':<6}NAME")
    for i, (name, price, desc) in enumerate(ITEMS, start=1):
        cat, cls, age = classify(name)
        print(f"{cls:<18}{'YES' if age else '-':<5}{'yes' if desc else 'BLANK':<6}{name}")
    blanks = sum(1 for _, _, d in ITEMS if not d)
    ages = sum(1 for n, _, _ in ITEMS if classify(n)[2])
    print(f"\n{ages}/{len(ITEMS)} age-restricted · {blanks}/{len(ITEMS)} blank descriptions (cron test bed)")


if __name__ == "__main__":
    asyncio.run(main())
