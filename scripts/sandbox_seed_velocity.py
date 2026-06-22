#!/usr/bin/env python3
"""
Banco sandbox — VELOCITY SEED.

Plants ~17 head-shop products + ~12 weeks of backdated sales with a deliberate **velocity
gradient** (fast movers, slow movers, high-value-low-volume, and a few dead-stock items) so
the Reports demo lights up on the otherwise-empty sandbox:
  - #2 Velocity / reorder     (the fast movers)
  - #3 Dead stock             (the 3 items that sold once ~75 days ago then went silent)
  - #4 By-units != by-revenue (cheap papers outsell a Puffco 90:1 by units, lose on money)
  - per-supplier shopping list (each product carries a supplier_name)

Emits SQL to **stdout** — apply with psql. **Idempotent + removable:** it deletes its own
prior seed first (marker: products sku `SEEDV-%`, transactions notes `SEEDV demo`), so
re-running re-seeds cleanly. Dates are relative to the DB clock (`now() - interval`), so the
window is always "the last ~12 weeks" whenever you run it.

RUN (sandbox, from anywhere with ssh to the box):
    python3 scripts/sandbox_seed_velocity.py | \
      ssh root@46.62.138.218 "docker exec -i postgres psql -U helix_user -d banco_sandbox"

UNDO (remove just the seed, back to empty):
    python3 scripts/sandbox_seed_velocity.py --undo | <same psql>

This is the OTHER mode to `make sandbox-reset` (which empties to zero for the Day-One
sell-to-seed demo). Reset = a brand-new shop. Seed = a shop with history, for reports.
"""
import random
import sys
import uuid
from decimal import Decimal, ROUND_HALF_UP

random.seed(42)            # deterministic — same seed every run
WINDOW = 84                # days of history
PAYMENTS = ["CASH", "CASH", "CASH", "TWINT", "VISA", "DEBIT"]   # weighted to cash

# name, price, cost, category, supplier, n_sales, dead
PRODUCTS = [
    ("CBD Oil 20% - 10ml",          "89.00", "45.00", "CBD",         "Mozy 420",   90, False),
    ("CBD Oil 10% - 10ml",          "49.00", "24.00", "CBD",         "Mozy 420",   70, False),
    ("4-Piece Metal Grinder",       "12.90",  "4.50", "Accessories", "FourTwenty", 85, False),
    ("RAW Rolling Papers King Size", "1.50",  "0.40", "Papers",      "FourTwenty", 95, False),
    ("RAW Filter Tips",              "1.20",  "0.30", "Papers",      "FourTwenty", 92, False),
    ("CBD Relaxation Tea - 20 Bags", "8.90",  "3.20", "CBD",         "Mozy 420",   60, False),
    ("Clipper Lighter",              "2.50",  "0.80", "Accessories", "FourTwenty", 80, False),
    ("CBD Flower 'Alpine Dream' 5g", "35.00","14.00", "CBD",         "Mozy 420",   38, False),
    ("Glass Pipe Handmade",         "24.00",  "9.00", "Glass",       "Local Glass",22, False),
    ("Hemp Wick 3m",                 "3.50",  "1.00", "Accessories", "FourTwenty", 30, False),
    ("Storage Jar 100ml",            "6.50",  "2.00", "Accessories", "FourTwenty", 26, False),
    ("Black Cup",                    "4.00",  "1.20", "On the fly",  "Local Glass",34, False),
    ("Puffco Peak Pro",            "449.00","280.00", "Vaporizers",  "Puffco",      9, False),
    ("Volcano Hybrid",             "599.00","380.00", "Vaporizers",  "Storz",       5, False),
    ("Novelty Ashtray 'Skull'",     "14.00",  "5.00", "Gifts",       "Local Glass", 1, True),
    ("Incense Sticks Sandalwood",    "3.00",  "0.90", "Gifts",       "FourTwenty",  2, True),
    ("Tie-Dye Bandana",              "9.00",  "3.00", "Apparel",     "FourTwenty",  2, True),
]


def sq(s: str) -> str:
    return s.replace("'", "''")


def vat(total: Decimal) -> Decimal:
    return (total * Decimal("8.1") / Decimal("108.1")).quantize(Decimal("0.01"), ROUND_HALF_UP)


def gen_barcode(i: int) -> str:
    # in-store EAN-ish (23-prefix is GS1's in-store range), deterministic + unique
    return ("23" + f"{4000000000 + i * 7919:011d}")[:13]


def emit(undo: bool) -> str:
    out = ["-- Banco sandbox velocity seed (generated; re-runnable) --", "BEGIN;"]
    # cleanup prior seed (marker-based) — this block is ALSO the --undo path
    out += [
        "DELETE FROM line_items WHERE transaction_id IN (SELECT id FROM transactions WHERE notes='SEEDV demo');",
        "DELETE FROM transactions WHERE notes='SEEDV demo';",
        "DELETE FROM products WHERE sku LIKE 'SEEDV-%';",
    ]
    if undo:
        return "\n".join(out + ["COMMIT;"])

    seq = 0
    for i, (name, price, cost, cat, supplier, n, dead) in enumerate(PRODUCTS):
        pid = uuid.uuid4()
        price_d = Decimal(price)
        out.append(
            "INSERT INTO products (id,sku,barcode,name,price,cost,stock_quantity,category,"
            "supplier_name,is_active,is_age_restricted,vending_compatible,sync_override,"
            "created_at,updated_at) VALUES "
            f"('{pid}','SEEDV-{i:03d}','{gen_barcode(i)}','{sq(name)}',{price},{cost},0,"
            f"'{sq(cat)}','{sq(supplier)}',true,false,false,false,"
            f"now()-interval '{WINDOW} days',now());"
        )
        for _ in range(n):
            seq += 1
            days_ago = random.randint(WINDOW - 12, WINDOW - 2) if dead else random.randint(0, WINDOW)
            hrs = random.randint(8, 20)
            qty = random.choices([1, 1, 1, 2, 3], [5, 5, 5, 2, 1])[0]
            line = (price_d * qty).quantize(Decimal("0.01"))
            tax = vat(line)
            tid, lid = uuid.uuid4(), uuid.uuid4()
            pay = random.choice(PAYMENTS)
            ts = f"now()-interval '{days_ago} days'-interval '{hrs} hours'"
            out.append(
                "INSERT INTO transactions (id,transaction_number,cashier_id,status,payment_method,"
                "subtotal,discount_amount,tax_amount,total,department,receipt_number,notes,"
                "created_at,updated_at,completed_at) VALUES "
                f"('{tid}','TXN-SEEDV-{seq:05d}',(SELECT id FROM users WHERE username='pam' LIMIT 1),"
                f"'COMPLETED','{pay}',{line},0,{tax},{line},'head_shop','SEEDV','SEEDV demo',"
                f"{ts},now(),{ts});"
            )
            out.append(
                "INSERT INTO line_items (id,transaction_id,product_id,quantity,unit_price,"
                "discount_percent,discount_amount,line_total,is_giveaway,created_at) VALUES "
                f"('{lid}','{tid}','{pid}',{qty},{price},0,0,{line},false,{ts});"
            )
    return "\n".join(out + ["COMMIT;"])


if __name__ == "__main__":
    print(emit(undo="--undo" in sys.argv))
