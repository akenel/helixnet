#!/usr/bin/env python3
"""Mama Cynthia — create her 7 handmade balms as a colour-variant product family.

The archetype EXCLUSIVE supplier: no EAN, on no website but her own (mama-cynthia.ch, inCMS),
German only. Live search can never find these — they're AUTHORED from her postcard. This is
the reverse of the FourTwenty/Artemis flow: the librarian finds what exists; here we create
what's exclusive. Data is straight off her order-card (front = the story, back = the prices);
images are her own round labels pulled from her site.

Idempotent upsert on sku (MC-*). Repeatable: get it right on sandbox, run the same script on
prod. Barcodes are internally MINTED EAN-13 (in-store 20-prefix) so Felix can still scan/print
them — her jars carry no manufacturer code.

Usage:
    python scripts/import/mama_cynthia.py --env sandbox [--dry-run]
    python scripts/import/mama_cynthia.py --env prod
"""
from __future__ import annotations

import argparse
import subprocess
import sys

HETZNER = "root@46.62.138.218"
DB_FOR = {"sandbox": "banco_sandbox", "staging": "banco_staging", "prod": "banco_prod"}
IMG_BASE = "https://www.mama-cynthia.ch/incms_files/filebrowser/cache"

# name / price / German subtitle+description / colour / label-image / scent-ingredients
CREAMS = [
    ("MC-LAVENDEL", "Lavendelsalbe", 30.0, "violett",
     "beruhigend & entspannend",
     "Für die tägliche Anwendung. Beruhigt und entspannt Körper & Geist. Auch als Gesichtspflege geeignet.",
     "Lavendel",
     "Etikette_Lavendelsalbe_violett_rund_979975349a44a29ac921921200691127.png"),
    ("MC-HANF-BLUMIG", "Hanfsalbe (blumig)", 35.0, "blau",
     "blumig duftend",
     "Für die tägliche Anwendung. Verbessert das Hautbild und verwöhnt mit seinem blumigen Duft.",
     "Hanf",
     "Etikette_Hanfsalbe_blau_rund_da272317cdadbb80d6579b45b5cc0ee8.png"),
    ("MC-KOPFBALSAM", "Kopfbalsam", 35.0, "hellblau",
     "mit Pfefferminze & Hanf",
     "Beruhigend und erfrischend bei Kopfschmerzen. Belebt den Geist.",
     "Pfefferminze, Hanf",
     "Etikette_Kopfbalsam_hellblau_rund_48b9a472a2f8f7368c00d0d5ddb06e0c.png"),
    ("MC-HANF-BERUHIGEND", "Hanfsalbe (beruhigend)", 35.0, "grün",
     "lindernd & beruhigend",
     "Für die tägliche Anwendung. Hilft bei trockener, juckender Haut, verbessert das Hautbild & hebt die Stimmung.",
     "Hanf",
     "Etikette_Hanfsalbe_gruen_rund_f4df3112d5219cb96e722cea763454ef.png"),
    ("MC-GELENK", "Gelenkbalsam", 35.0, "gelb",
     "mit Weihrauch & Hanf",
     "Wohltuend bei Gelenkschmerzen, entzündungshemmend und verbessert das Hautbild.",
     "Weihrauch, Hanf",
     "Etikette_Gelenkbalsam_gelb_rund_1f7cdde0e14516d97b2f203a6c35b8f9.png"),
    ("MC-RINGELBLUMEN", "Ringelblumensalbe", 30.0, "orange",
     "Alltags-Pflege",
     "Alltags-Pflege für trockene Haut oder bei kleinen Wunden und Schürfungen. Geeignet für Babys.",
     "Ringelblume",
     "Etikette_Ringelblumensalbe_orange_rund_9bac9e2e7cb32b36b2d019275e80a88f.png"),
    ("MC-WAERME", "Wärmebalsam", 30.0, "rot",
     "mit Thymian & Rosmarin",
     "Wärmt bei Erkältung, befreit die Nase und wirkt vitalisierend auf Körper und Seele.",
     "Thymian, Rosmarin",
     "Etikette_Waermebalsam_rot_rund_a4d427d1a7a828e9cc132f7ca6d92364.png"),
]

CATEGORY = "Creams & Topicals"
GROUP = "Lifestyle"


def ean13(seed12: str) -> str:
    """EAN-13 check digit appended to a 12-digit body (in-store '20' prefix)."""
    body = (seed12 + "000000000000")[:12]
    s = sum((3 if i % 2 else 1) * int(d) for i, d in enumerate(body))
    return body + str((10 - s % 10) % 10)


def q(v) -> str:
    if v is None or v == "":
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"


def build_sql() -> str:
    stmts = []
    for i, (sku, name, price, colour, subtitle, desc, scent, img) in enumerate(CREAMS):
        barcode = ean13("20" + str(700000 + i).rjust(10, "0")[:10])
        full = f"{name} — {subtitle}"                       # display name carries the flavour
        image_url = f"{IMG_BASE}/{img}"
        # attributes (colour/scent) kept for the variant family + the postcard maker later
        attrs = ("{" + f'"colour":"{colour}","scent":"{scent}","family":"Mama Cynthia Salben"' + "}")
        stmts.append(
            "INSERT INTO products (id, sku, barcode, barcode_is_internal, name, description, "
            "price, cost, category, product_group, product_class, is_age_restricted, "
            "supplier_sku, supplier_name, supplier_price, image_url, attributes, "
            "source_system, source_url, source_lang, needs_translation, "
            "is_active, stock_quantity, vending_compatible, sync_override, created_at, updated_at) VALUES ("
            f"gen_random_uuid(), {q(sku)}, {q(barcode)}, true, {q(full)}, {q(desc)}, "
            f"{price}, NULL, {q(CATEGORY)}, {q(GROUP)}, 'standard', false, "
            f"{q(sku)}, 'Mama Cynthia', {price}, {q(image_url)}, {q(attrs)}::jsonb, "
            f"'mama-cynthia', 'https://www.mama-cynthia.ch', 'de', true, "
            "true, 0, false, false, now(), now()) "
            "ON CONFLICT (sku) DO UPDATE SET "
            "barcode=EXCLUDED.barcode, barcode_is_internal=EXCLUDED.barcode_is_internal, "
            "name=EXCLUDED.name, description=EXCLUDED.description, price=EXCLUDED.price, "
            "category=EXCLUDED.category, product_group=EXCLUDED.product_group, "
            "supplier_name=EXCLUDED.supplier_name, supplier_price=EXCLUDED.supplier_price, "
            "image_url=EXCLUDED.image_url, attributes=EXCLUDED.attributes, "
            "source_system=EXCLUDED.source_system, source_lang=EXCLUDED.source_lang, "
            "needs_translation=EXCLUDED.needs_translation, is_active=true, updated_at=now();"
        )
    return "\n".join(stmts) + "\n"


def psql(env: str, sql: str) -> str:
    db = DB_FOR[env]
    cmd = ["ssh", HETZNER, f"docker exec -i postgres psql -U helix_user -d {db}"]
    return subprocess.run(cmd, input=sql, text=True, capture_output=True).stdout


def main():
    ap = argparse.ArgumentParser(description="Create Mama Cynthia's 7 balms (variant family)")
    ap.add_argument("--env", choices=list(DB_FOR), required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    sql = build_sql()
    if args.dry_run:
        print(sql)
        print(f"-- {len(CREAMS)} creams for {DB_FOR[args.env]} (dry-run, not applied)")
        return

    out = psql(args.env, sql)
    ok = out.count("INSERT 0 1") + out.count("UPDATE 1")
    print(f"Applied to {DB_FOR[args.env]}: {ok} upserts across {len(CREAMS)} creams.")
    verify = psql(args.env,
                  "SELECT sku, name, price, category FROM products WHERE supplier_name='Mama Cynthia' ORDER BY sku;")
    print(verify.strip())


if __name__ == "__main__":
    main()
