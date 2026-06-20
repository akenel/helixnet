#!/usr/bin/env python3
"""
Banco POS — load a sample of the supplier catalog (fourtwenty.ch) into an env.

Reads the fourtwenty product feed, maps fields the same way fourtwenty-sync.py does
(sku FT-<sku>, 50% markup, category map, supplier photo), takes a random sample of
--count items that have an image, and INSERTs them idempotently (ON CONFLICT on sku;
barcode nulled to avoid unique collisions). Useful for populating a catalog to test
search/pagination/images without the full ~10k import.

Targets:
  local            -> the laptop's postgres container
  staging | prod   -> the SHARED Hetzner helix_db (staging and prod use the same DB)

Usage:
    python scripts/load_supplier_sample.py --env staging --count 300
    python scripts/load_supplier_sample.py --env local --count 500 --stock 25
    python scripts/load_supplier_sample.py --env prod --count 300 --dry-run   # write SQL only

NOTE: staging and prod share one DB -- loading to either populates the live Artemis till.
"""
import argparse
import csv
import io
import random
import subprocess
import sys
from decimal import Decimal, InvalidOperation

FEED = "/home/angel/repos/helixnet/debllm/feeds/fourtwenty/products_latest.csv"
HETZNER = "root@46.62.138.218"
DB = ["psql", "-U", "helix_user", "-d", "helix_db"]

# Same mapping as scripts/modules/tools/fourtwenty-sync.py (keep in sync).
MARKUP = Decimal("1.50")
HEADSHOP = {"Headshop", "Vape", "Vape Shop", "CBD", "Liquids Vape ", "Themen", "Punkteartikel"}
CATEGORY_MAP = {
    "Headshop": "Accessories", "Vape": "Vaporizers", "Vape Shop": "Vaporizers",
    "CBD": "CBD", "Liquids Vape ": "E-Liquids", "Themen": "Themed",
    "Punkteartikel": "Promotions", "Weekly Promotion": "Promotions", "Indoorgrowing": None,
}


def q(s):
    """SQL string literal (or NULL)."""
    if s is None or s == "":
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"


def dec(s):
    try:
        return Decimal(str(s).replace(",", ".")).quantize(Decimal("0.01"))
    except (InvalidOperation, AttributeError):
        return Decimal("0.00")


def read_feed():
    with open(FEED, encoding="utf-8") as f:
        text = f.read()
    delim = ";" if text.splitlines()[0].count(";") > text.splitlines()[0].count(",") else ","
    return list(csv.DictReader(io.StringIO(text), delimiter=delim))


def build_rows(count, stock):
    rows = read_feed()
    usable = []
    for p in rows:
        if p.get("categorygroup_1", "") not in HEADSHOP:
            continue
        cat = CATEGORY_MAP.get(p.get("categorygroup_1", ""))
        sku = (p.get("sku") or "").strip()
        name = (p.get("producttitle_de") or "").strip()
        img = (p.get("mainimageurl") or "").strip()
        if not (cat and sku and name and img):
            continue
        sp = dec(p.get("salespriceinclvat", "0"))
        usable.append({
            "sku": f"FT-{sku}", "name": name[:255], "price": (sp * MARKUP).quantize(Decimal("0.01")),
            "cost": sp, "category": cat, "supplier_sku": sku, "supplier_price": sp, "image_url": img[:500],
        })
    if not usable:
        sys.exit("No usable products in the feed.")
    sample = random.sample(usable, min(count, len(usable)))
    stmts = []
    for r in sample:
        stmts.append(
            "INSERT INTO products (id,sku,name,price,cost,category,supplier_sku,supplier_name,"
            "supplier_price,image_url,is_age_restricted,is_active,stock_quantity,vending_compatible,"
            "sync_override,created_at,updated_at) VALUES "
            f"(gen_random_uuid(),{q(r['sku'])},{q(r['name'])},{r['price']},{r['cost']},{q(r['category'])},"
            f"{q(r['supplier_sku'])},'FourTwenty',{r['supplier_price']},{q(r['image_url'])},false,true,"
            f"{int(stock)},false,false,now(),now()) ON CONFLICT (sku) DO NOTHING;"
        )
    return stmts


def psql_channel(env):
    """Return the argv that pipes SQL on stdin into the target env's psql."""
    if env == "local":
        return ["docker", "exec", "-i", "postgres", *DB]
    return ["ssh", HETZNER, "docker exec -i postgres " + " ".join(DB)]


def run(env, sql):
    return subprocess.run(psql_channel(env), input=sql, text=True,
                          capture_output=True).stdout.strip()


def count(env):
    out = run(env, "SELECT count(*) FROM products;")
    return out.splitlines()[-1].strip() if out else "?"


def main():
    ap = argparse.ArgumentParser(description="Load a supplier-catalog sample into an env")
    ap.add_argument("--env", choices=["local", "staging", "prod"], required=True)
    ap.add_argument("--count", type=int, default=300)
    ap.add_argument("--stock", type=int, default=10, help="placeholder on-hand per item (test data)")
    ap.add_argument("--dry-run", action="store_true", help="write SQL to /tmp, don't apply")
    args = ap.parse_args()

    if args.env in ("staging", "prod"):
        print("NOTE: staging and prod SHARE the Hetzner DB -- this populates the live Artemis till.")

    stmts = build_rows(args.count, args.stock)
    sql = "\n".join(stmts) + "\n"
    out_file = f"/tmp/supplier-sample-{args.env}-{args.count}.sql"
    with open(out_file, "w") as f:
        f.write(sql)
    print(f"Built {len(stmts)} INSERTs -> {out_file}")

    if args.dry_run:
        print("Dry run -- not applied.")
        return

    before = count(args.env)
    applied = run(args.env, sql)
    inserted = applied.count("INSERT 0 1")
    after = count(args.env)
    print(f"Applied to {args.env}: products {before} -> {after}  (new this run: {inserted})")


if __name__ == "__main__":
    main()
