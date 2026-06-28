#!/usr/bin/env python3
"""Seed a realistic ~70-item catalog into a Banco env (for testing pagination / catalog
browse, where the default 12-item seed is too small to scroll).

Creates products across categories with the CORRECT product_class (so VAT, age-gate and
the promo-restricted discount block behave realistically). Idempotent-ish: SKUs are stable
(SEED-001…), so re-running 409s on dupes rather than duplicating.

Usage:
    python3 scripts/seed_sandbox_catalog.py <BASE_URL> <TOKEN>
      BASE_URL : e.g. https://sandbox-banco.lapiazza.app
      TOKEN    : a manager/cashier POS access token (any POS role can capture products)

NOTE: the sandbox resets nightly (the daily smoke), so re-run after a reset to get the
data back. Not for prod (prod grows its catalog by real sales — sell-to-seed).
"""
import json
import sys
import urllib.request as u

BASE = sys.argv[1].rstrip("/") + "/api/v1/pos" if len(sys.argv) > 1 else None
TOK = sys.argv[2] if len(sys.argv) > 2 else None
if not BASE or not TOK:
    sys.exit("usage: seed_sandbox_catalog.py <BASE_URL> <TOKEN>")

# (category, product_class, [(name, price), ...])
GROUPS = [
    ("CBD & Hemp", "cbd_open", [("CBD Oil 5% 10ml", 24.90), ("CBD Oil 10% 10ml", 39.90), ("CBD Oil 15% 10ml", 54.90), ("CBD Oil 20% 10ml", 69.90), ("CBD Massage Oil 100ml", 29.90), ("Hemp Seed Oil 250ml", 14.90), ("CBD Sleep Drops 30ml", 44.90)]),
    ("Creams & Topicals", "cbd_open", [("CBD Balm 50ml", 27.50), ("Hemp Body Lotion 200ml", 19.90), ("CBD Muscle Gel 100ml", 32.00), ("Hemp Hand Cream 75ml", 12.90), ("CBD Lip Balm", 6.90)]),
    ("Papers & Filters", "standard", [("OCB Slim White", 1.20), ("OCB Premium Black Slim", 1.50), ("RAW Classic King Size", 1.90), ("Smoking Blue King Size", 1.60), ("RAW Tips Perforated", 1.10), ("OCB Filter Tips Slim", 2.20), ("Purize Active Filters 50", 6.90), ("RAW Pre-Rolled Cones 6", 3.50), ("Juicy Jay Strawberry", 2.40)]),
    ("Grinders", "standard", [("4-part Grinder 50mm Black", 18.00), ("4-part Grinder 63mm Silver", 24.00), ("2-part Wood Grinder", 9.90), ("Aluminium Grinder Rainbow", 21.00)]),
    ("Lighters", "standard", [("Clipper Classic", 2.50), ("Clipper Pattern", 3.00), ("BIC Maxi", 2.80), ("Storm Jet Lighter", 7.90), ("Soft Flame Pipe Lighter", 12.90)]),
    ("Pipes & Bongs", "standard", [("Glass Spoon Pipe 10cm", 14.90), ("Silicone Pipe", 9.90), ("Acrylic Bong 30cm", 24.90), ("Glass Bong 40cm", 59.00), ("Bubbler Glass", 34.00)]),
    ("Vaporizers", "standard", [("Dry Herb Vape Mini", 69.00), ("510 Battery 350mAh", 14.90), ("Vape Cartridge Empty", 4.90)]),
    ("Tobacco & Cigarettes", "tobacco_nicotine", [("Cigarettes Pack Classic", 9.00), ("Rolling Tobacco 30g", 12.50), ("Pipe Tobacco 50g", 16.90), ("Snus Original", 6.50), ("Nicotine Pouches Mint", 5.90)]),
    ("Café", "cafe_food", [("Espresso", 3.50), ("Cappuccino", 4.50), ("Latte Macchiato", 5.00), ("Fresh Orange Juice", 5.00), ("Croissant", 3.00), ("Blueberry Muffin", 3.80), ("Club Sandwich", 8.50), ("Iced Tea 0.5L", 4.00), ("Hot Chocolate", 4.80), ("Brownie", 4.20)]),
    ("Bar", "alcohol", [("Lager Beer 0.5L", 4.50), ("IPA Craft 0.33L", 6.00), ("Red Wine Glass", 7.50), ("White Wine Glass", 7.50), ("Prosecco Glass", 8.00), ("Aperol Spritz", 11.00)]),
    ("Accessories", "standard", [("Rolling Tray Metal", 9.90), ("Storage Jar 100ml", 7.50), ("Hemp Wick 3m", 3.90), ("Ashtray Glass", 6.90), ("Cleaning Brush Set", 4.50), ("Odour-Proof Bag", 8.90), ("Scale 0.01g", 24.90)]),
]


def post(path, body):
    r = u.Request(BASE + path, data=json.dumps(body).encode(), method="POST",
                  headers={"Authorization": "Bearer " + TOK, "Content-Type": "application/json"})
    try:
        with u.urlopen(r, timeout=20) as resp:
            return resp.status
    except u.HTTPError as e:
        return e.code


def main():
    ok = fail = n = 0
    for cat, cls, items in GROUPS:
        for name, price in items:
            n += 1
            st = post("/products", {"sku": f"SEED-{n:03d}", "name": name, "price": price,
                                    "category": cat, "product_class": cls, "stock_quantity": 50})
            if st in (200, 201):
                ok += 1
            else:
                fail += 1
    print(f"created: {ok}  failed/dupe: {fail}  (attempted {n})")


if __name__ == "__main__":
    main()
