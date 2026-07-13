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

# One dict per balm. `en` = the juiced SOURCE description (English is the hub — every other
# language flows from it); `de` = her own authentic German (seeded as a 'source' translation so
# German customers get her real voice, not a back-translation). Both are GROUNDED in her card +
# her website (benefits + Zusammensetzung/ingredients + 30 ml + handmade in CH) — nothing invented.
CREAMS = [
    {"sku": "MC-LAVENDEL", "name": "Lavendelsalbe", "sub": "beruhigend & entspannend",
     "price": 30.0, "colour": "violett", "scent": "Lavendel",
     "ingredients": "Olivenöl, Kokosöl, Bienenwachs, Lavendel",
     "img": "Etikette_Lavendelsalbe_violett_rund_979975349a44a29ac921921200691127.png",
     "en": "A calming, grounding balm for everyday care. It gently soothes and relaxes body and "
           "mind, and is mild enough to use on the face. Handmade in Switzerland from olive oil, "
           "coconut oil, beeswax and true lavender. 30 ml — made with love by Mama Cynthia.",
     "de": "Eine beruhigende Salbe für die tägliche Pflege. Sie beruhigt und entspannt sanft "
           "Körper & Geist und ist mild genug für die Gesichtspflege. Von Hand in der Schweiz "
           "gemacht aus Olivenöl, Kokosöl, Bienenwachs und echtem Lavendel. 30 ml — mit viel Liebe."},
    {"sku": "MC-HANF-BLUMIG", "name": "Hanfsalbe (blumig)", "sub": "blumig duftend",
     "price": 35.0, "colour": "blau", "scent": "Hanf, Lavendel, Geranium, Jasmin, Rose",
     "ingredients": "Hanföl, Kokosöl, Bienenwachs, Hanfextrakt, Lavendel, Geranium, Jasmin, Rosmarin & Rosen",
     "img": "Etikette_Hanfsalbe_blau_rund_da272317cdadbb80d6579b45b5cc0ee8.png",
     "en": "A daily hemp balm that improves the skin and pampers with a soft, floral scent. Rich "
           "with hemp oil, coconut oil and beeswax, blended with hemp extract, lavender, geranium, "
           "jasmine, rosemary and rose. Handmade in Switzerland, 30 ml — made with love by Mama Cynthia.",
     "de": "Eine Hanfsalbe für jeden Tag, die das Hautbild verbessert und mit ihrem zarten, "
           "blumigen Duft verwöhnt. Reich an Hanföl, Kokosöl & Bienenwachs, verfeinert mit "
           "Hanfextrakt, Lavendel, Geranium, Jasmin, Rosmarin & Rosen. Handgemacht in der Schweiz, 30 ml."},
    {"sku": "MC-KOPFBALSAM", "name": "Kopfbalsam", "sub": "mit Pfefferminze & Hanf",
     "price": 35.0, "colour": "hellblau", "scent": "Pfefferminze, Hanf",
     "ingredients": "Hanföl, Kokosöl, Bienenwachs, Pfefferminze",
     "img": "Etikette_Kopfbalsam_hellblau_rund_48b9a472a2f8f7368c00d0d5ddb06e0c.png",
     "en": "A cooling head balm with peppermint and hemp — calming and refreshing when a headache "
           "sets in, and it wakes up a tired mind. Made from hemp oil, coconut oil, beeswax and "
           "real peppermint. Handmade in Switzerland, 30 ml — made with love by Mama Cynthia.",
     "de": "Ein kühlender Kopfbalsam mit Pfefferminze & Hanf — beruhigend und erfrischend bei "
           "Kopfschmerzen und belebend für den Geist. Aus Hanföl, Kokosöl, Bienenwachs und echter "
           "Pfefferminze. Handgemacht in der Schweiz, 30 ml."},
    {"sku": "MC-HANF-BERUHIGEND", "name": "Hanfsalbe (beruhigend)", "sub": "lindernd & beruhigend",
     "price": 35.0, "colour": "grün", "scent": "Hanf, Lavendel, Geranium",
     "ingredients": "Hanföl, Kokosöl, Bienenwachs, Hanfextrakt, Lavendel & Geranium",
     "img": "Etikette_Hanfsalbe_gruen_rund_f4df3112d5219cb96e722cea763454ef.png",
     "en": "A soothing, calming hemp balm for daily care — it relieves dry, itchy skin, improves "
           "the skin's look and gently lifts the mood. Made from hemp oil, coconut oil, beeswax, "
           "hemp extract, lavender and geranium. Handmade in Switzerland, 30 ml — made with love by Mama Cynthia.",
     "de": "Eine lindernde, beruhigende Hanfsalbe für die tägliche Pflege — sie hilft bei "
           "trockener, juckender Haut, verbessert das Hautbild und hebt sanft die Stimmung. Aus "
           "Hanföl, Kokosöl, Bienenwachs, Hanfextrakt, Lavendel & Geranium. Handgemacht in der Schweiz, 30 ml."},
    {"sku": "MC-GELENK", "name": "Gelenkbalsam", "sub": "mit Weihrauch & Hanf",
     "price": 35.0, "colour": "gelb", "scent": "Weihrauch, Hanf",
     "ingredients": "Hanföl, Kokosöl, Bienenwachs, Weihrauch, Hanfextrakt",
     "img": "Etikette_Gelenkbalsam_gelb_rund_1f7cdde0e14516d97b2f203a6c35b8f9.png",
     "en": "A comforting balm for aching joints, with frankincense and hemp. Soothing and "
           "anti-inflammatory, it eases joint pain while it improves the skin. Made from hemp oil, "
           "coconut oil, beeswax, frankincense and hemp extract. Handmade in Switzerland, 30 ml — made with love by Mama Cynthia.",
     "de": "Ein wohltuender Balsam für schmerzende Gelenke, mit Weihrauch & Hanf. Beruhigend und "
           "entzündungshemmend lindert er Gelenkschmerzen und verbessert dabei das Hautbild. Aus "
           "Hanföl, Kokosöl, Bienenwachs, Weihrauch & Hanfextrakt. Handgemacht in der Schweiz, 30 ml."},
    {"sku": "MC-RINGELBLUMEN", "name": "Ringelblumensalbe", "sub": "Alltags-Pflege",
     "price": 30.0, "colour": "orange", "scent": "Ringelblume, Hanf",
     "ingredients": "Hanföl, Kokosöl, Bienenwachs, Hanfextrakt, Lavendel & Geranium",
     "img": "Etikette_Ringelblumensalbe_orange_rund_9bac9e2e7cb32b36b2d019275e80a88f.png",
     "en": "A gentle everyday balm of calendula for dry skin and little cuts and grazes — mild "
           "enough for babies. Made from hemp oil, coconut oil, beeswax, hemp extract, lavender "
           "and geranium. Handmade in Switzerland, 30 ml — made with love by Mama Cynthia.",
     "de": "Eine sanfte Alltags-Salbe mit Ringelblume für trockene Haut, kleine Wunden und "
           "Schürfungen — mild genug für Babys. Aus Hanföl, Kokosöl, Bienenwachs, Hanfextrakt, "
           "Lavendel & Geranium. Handgemacht in der Schweiz, 30 ml."},
    {"sku": "MC-WAERME", "name": "Wärmebalsam", "sub": "mit Thymian & Rosmarin",
     "price": 30.0, "colour": "rot", "scent": "Thymian, Rosmarin",
     "ingredients": "Olivenöl, Kokosöl, Bienenwachs, Thymian & Rosmarin",
     "img": "Etikette_Waermebalsam_rot_rund_a4d427d1a7a828e9cc132f7ca6d92364.png",
     "en": "A warming balm with thyme and rosemary for cold days — it warms you through a cold, "
           "helps clear a stuffy nose and leaves body and soul feeling revived. Made from olive "
           "oil, coconut oil, beeswax, thyme and rosemary. Handmade in Switzerland, 30 ml — made with love by Mama Cynthia.",
     "de": "Ein wärmender Balsam mit Thymian & Rosmarin für kalte Tage — er wärmt bei Erkältung, "
           "befreit die Nase und wirkt vitalisierend auf Körper und Seele. Aus Olivenöl, Kokosöl, "
           "Bienenwachs, Thymian & Rosmarin. Handgemacht in der Schweiz, 30 ml."},
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
    import json
    stmts = []
    for i, c in enumerate(CREAMS):
        barcode = ean13("20" + str(700000 + i).rjust(10, "0")[:10])
        full = f"{c['name']} — {c['sub']}"                   # display name carries the flavour
        image_url = f"{IMG_BASE}/{c['img']}"
        attrs = json.dumps({"colour": c["colour"], "scent": c["scent"],
                            "ingredients": c["ingredients"], "size": "30 ml",
                            "family": "Mama Cynthia Salben"}, ensure_ascii=False)
        # THE PRODUCT — English is the SOURCE description (the hub every language flows from).
        stmts.append(
            "INSERT INTO products (id, sku, barcode, barcode_is_internal, name, description, "
            "price, cost, category, product_group, product_class, is_age_restricted, "
            "supplier_sku, supplier_name, supplier_price, image_url, attributes, "
            "source_system, source_url, source_lang, needs_translation, "
            "is_active, stock_quantity, vending_compatible, sync_override, created_at, updated_at) VALUES ("
            f"gen_random_uuid(), {q(c['sku'])}, {q(barcode)}, true, {q(full)}, {q(c['en'])}, "
            f"{c['price']}, NULL, {q(CATEGORY)}, {q(GROUP)}, 'standard', false, "
            f"{q(c['sku'])}, 'Mama Cynthia', {c['price']}, {q(image_url)}, {q(attrs)}::jsonb, "
            f"'mama-cynthia', 'https://www.mama-cynthia.ch', 'en', true, "
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
        # HER AUTHENTIC GERMAN — seeded as a 'source' translation so German customers read her
        # real voice, not a machine back-translation. FR/IT still flow from the English via BL-36.
        stmts.append(
            "INSERT INTO product_translations (id, product_id, lang, name, description, provenance, "
            "needs_review, created_at, updated_at) "
            f"SELECT gen_random_uuid(), p.id, 'de', NULL, {q(c['de'])}, 'source', false, now(), now() "
            f"FROM products p WHERE p.sku = {q(c['sku'])} "
            "ON CONFLICT ON CONSTRAINT uq_product_translations_product_lang DO UPDATE SET "
            "description=EXCLUDED.description, provenance='source', needs_review=false, updated_at=now();"
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
