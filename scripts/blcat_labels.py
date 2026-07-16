#!/usr/bin/env python3
"""BL-CAT — inject de/fr/it/en labels into the canonical tree + emit the POS_CATEGORY_LABELS block.

Adds label_en/label_de/label_fr/label_it to every canonical_category and group in the draft JSON,
and (with --emit) prints the JS entries to splice into POS_CATEGORY_LABELS (pos-i18n.js) so the
new English canonical categories render in each language. Felix's shop is German → DE labels are
the priority (a migration to English labels without these would show his staff English shelves).
"""
import argparse
import json

# canonical_key -> (en, de, fr, it)
CAT = {
    "cbd-flower": ("CBD Flower", "CBD Blüten", "Fleurs CBD", "Fiori CBD"),
    "cbd-extracts": ("Extracts & Oils", "Extrakte & Öle", "Extraits & huiles", "Estratti & oli"),
    "cbd-edibles": ("Edibles", "Esswaren", "Comestibles", "Commestibili"),
    "cbd-cosmetics": ("Cosmetics", "Kosmetik", "Cosmétiques", "Cosmetici"),
    "cbd-topicals": ("Creams & Topicals", "Cremes & Salben", "Crèmes & baumes", "Creme & balsami"),
    "rolling-papers": ("Rolling Papers", "Drehpapier", "Feuilles à rouler", "Cartine"),
    "filters-tips": ("Filters & Tips", "Filter & Tips", "Filtres & embouts", "Filtri & tips"),
    "blunts-wraps": ("Blunts & Wraps", "Blunts & Wraps", "Blunts & wraps", "Blunt & wrap"),
    "cones-tubes": ("Cones & Tubes", "Cones & Hülsen", "Cônes & tubes", "Coni & tubi"),
    "rolling-trays": ("Rolling Trays", "Roll-Trays", "Plateaux à rouler", "Vassoi"),
    "rolling-machines": ("Rolling & Filling Machines", "Dreh- & Stopfmaschinen", "Rouleuses & tubeuses", "Rollatrici & riempitrici"),
    "cigarette-tubes": ("Cigarette Tubes", "Zigarettenhülsen", "Tubes à cigarette", "Tubetti"),
    "rolling-accessories": ("Rolling Accessories", "Dreh-Zubehör", "Accessoires à rouler", "Accessori per rollare"),
    "bongs": ("Bongs", "Bongs", "Bongs", "Bong"),
    "pipes": ("Pipes", "Pfeifen", "Pipes", "Pipe"),
    "grinders": ("Grinders", "Grinder", "Grinders", "Grinder"),
    "bong-pipe-parts": ("Bong & Pipe Accessories", "Bong- & Pfeifenzubehör", "Accessoires bong & pipe", "Accessori bong & pipa"),
    "lighters": ("Lighters", "Feuerzeuge", "Briquets", "Accendini"),
    "ashtrays": ("Ashtrays", "Aschenbecher", "Cendriers", "Posacenere"),
    "scales": ("Scales", "Waagen", "Balances", "Bilance"),
    "presses": ("Presses", "Pressen", "Presses", "Presse"),
    "snuff": ("Snuff Accessories", "Schnupf-Zubehör", "Accessoires à priser", "Accessori da fiuto"),
    "storage-stash": ("Storage & Stash", "Aufbewahrung", "Rangement & planque", "Conservazione"),
    "dab-concentrate": ("Dab & Concentrate Gear", "Dab- & Konzentrat-Zubehör", "Matériel dab & concentrés", "Attrezzi dab & concentrati"),
    "e-liquids": ("E-Liquids", "E-Liquids", "E-liquides", "E-liquid"),
    "coils-pods": ("Coils & Pods", "Coils & Pods", "Résistances & pods", "Coil & pod"),
    "vape-devices": ("Vape Devices", "Vape-Geräte", "Cigarettes électroniques", "Dispositivi vape"),
    "prefilled": ("Prefilled & Disposables", "Vorgefüllt & Einweg", "Préremplis & jetables", "Preriempiti & usa e getta"),
    "vaporizers": ("Vaporizers", "Vaporizer", "Vaporisateurs", "Vaporizzatori"),
    "nicotine-shots": ("Nicotine Shots", "Nikotin-Shots", "Boosters nicotine", "Shot di nicotina"),
    "vape-accessories": ("Vape Accessories", "Vape-Zubehör", "Accessoires vape", "Accessori vape"),
    "tobacco": ("Tobacco", "Tabak", "Tabac", "Tabacco"),
    "shisha-tobacco": ("Shisha Tobacco", "Shisha-Tabak", "Tabac à chicha", "Tabacco per shisha"),
    "shishas": ("Shishas & Hookahs", "Shishas", "Chichas", "Shisha"),
    "shisha-bowls": ("Shisha Bowls", "Shisha-Köpfe", "Foyers de chicha", "Fornelli shisha"),
    "shisha-coal": ("Shisha Coal", "Kohle", "Charbon", "Carbone"),
    "shisha-hoses": ("Shisha Hoses", "Schläuche", "Tuyaux", "Tubi"),
    "food-snacks": ("Food & Snacks", "Essen & Snacks", "Nourriture & snacks", "Cibo & snack"),
    "cafe": ("Cafe", "Café", "Café", "Caffè"),
    "decor": ("Decor", "Deko", "Déco", "Decorazioni"),
    "incense": ("Incense & Smudge", "Räucherwerk", "Encens", "Incensi"),
    "apparel": ("Apparel & Textiles", "Textilien", "Vêtements & textiles", "Abbigliamento & tessili"),
    "gifts-gadgets": ("Gifts & Gadgets", "Geschenke & Gadgets", "Cadeaux & gadgets", "Regali & gadget"),
    "entertainment": ("Entertainment & Games", "Unterhaltung & Spiele", "Divertissement & jeux", "Intrattenimento & giochi"),
    "knives-tools": ("Knives & Tools", "Messer & Werkzeuge", "Couteaux & outils", "Coltelli & utensili"),
    "packaging": ("Packaging & Bags", "Verpackung & Beutel", "Emballage & sachets", "Imballaggio & sacchetti"),
    "drug-testing": ("Drug Testing", "Drogentests", "Tests de dépistage", "Test antidroga"),
    "grow": ("Grow Supplies", "Grow-Bedarf", "Matériel de culture", "Materiale coltivazione"),
    "accessories": ("Accessories (general)", "Zubehör (allgemein)", "Accessoires (général)", "Accessori (generale)"),
    "unsorted": ("Unsorted", "Unsortiert", "Non trié", "Non ordinato"),
    "other": ("Other", "Diverses", "Autre", "Altro"),
}
GRP = {
    "cbd": ("CBD & Hemp", "CBD & Hanf", "CBD & chanvre", "CBD & canapa"),
    "papers": ("Papers & Rolling", "Papers & Drehen", "Feuilles & roulage", "Cartine & rollaggio"),
    "headshop": ("Smoking Gear", "Rauchzubehör", "Matériel de fumeur", "Attrezzi da fumo"),
    "vape": ("Vape", "Vape", "Vape", "Vape"),
    "shisha": ("Tobacco & Shisha", "Tabak & Shisha", "Tabac & chicha", "Tabacco & shisha"),
    "cafe": ("Cafe & Food", "Café & Essen", "Café & nourriture", "Caffè & cibo"),
    "lifestyle": ("Lifestyle & Gifts", "Lifestyle & Geschenke", "Lifestyle & cadeaux", "Lifestyle & regali"),
    "growlab": ("Grow & Lab", "Grow & Labor", "Culture & labo", "Coltivazione & lab"),
    "system": ("Unsorted / System", "Unsortiert / System", "Non trié / système", "Non ordinato / sistema"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", required=True)
    ap.add_argument("--emit", action="store_true", help="print POS_CATEGORY_LABELS JS entries")
    a = ap.parse_args()
    draft = json.load(open(a.draft, encoding="utf-8"))

    for c in draft["canonical_categories"]:
        en, de, fr, it = CAT[c["key"]]
        c["label_en"], c["label_de"], c["label_fr"], c["label_it"] = en, de, fr, it
    for g in draft["groups"]:
        en, de, fr, it = GRP[g["key"]]
        g["label_en"], g["label_de"], g["label_fr"], g["label_it"] = en, de, fr, it

    if a.emit:
        # Emit {lang: {EN_label: LANG_label}} for categories + groups.
        for lang, idx in (("de", 1), ("fr", 2), ("it", 3)):
            print(f"\n// --- {lang} ---")
            for src in (CAT, GRP):
                for k, tup in src.items():
                    print(f'    {json.dumps(tup[0], ensure_ascii=False)}: {json.dumps(tup[idx], ensure_ascii=False)},')
        return

    json.dump(draft, open(a.draft, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"labels injected into {a.draft} — {len(CAT)} categories, {len(GRP)} groups × en/de/fr/it")


if __name__ == "__main__":
    main()
