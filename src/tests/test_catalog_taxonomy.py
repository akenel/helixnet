"""Catalog enrichment classifier — the 18+ decision is made at IMPORT time.

The whole point (Felix's Artemis UAT, 2026-07-06): a product should come out of the
enrichment already knowing whether it's age-restricted — cigarettes and CBD flower = 18+,
papers and filters = open. The signal that makes this reliable is the SUPPLIER's own
category (stored in `raw`), not just the title: real cigarette packs are titled
"Marlboro Gold 10x20cig" with no "tabak"/"zigarette" token at all, so a title-only
classifier leaked them through as un-gated goods.

Pure function, no DB/network — fast regression guard on classify().
"""
from src.services.catalog_taxonomy import (
    classify, class_is_age_restricted, reconcile_age, resolve_class_on_create,
    canonicalize_category, CATEGORIES,
)


# ---- Alcohol: a real merchandising category (Angel: "no cat for alcohol??") ----

def test_alcohol_is_a_category_and_survives_the_funnel():
    assert "Alcohol" in CATEGORIES
    # the funnel must KEEP 'Alcohol' (its own group), not wipe it to Unsorted
    assert canonicalize_category("Alcohol") == ("Alcohol", "Bar & Alcohol")
    # common ways it's written / imported all funnel to Alcohol
    for s in ("Alkohol", "Beer", "Bier", "Wine", "Wein", "Spirits", "Spirituosen"):
        assert canonicalize_category(s)[0] == "Alcohol", s


def test_real_bottle_files_under_alcohol_and_flags_18plus():
    for t in ("Absolut Vodka 0.7L", "Feldschlösschen Bier", "Gin Bombay Sapphire", "Rum Havana Club"):
        cat, cls, age = classify(t)
        assert cat == "Alcohol" and cls == "alcohol" and age is True, t


def test_flavoured_papers_are_not_mislabelled_alcohol():
    # "Rum Flavour Papers" is rolling papers, NOT alcohol — its own product rule wins, class stays open
    cat, cls, age = classify("Juicy Jay Rum Flavour Papers")
    assert cat == "Papers & Filters" and cls == "standard" and age is False


def _ft(cg2, cg1="Headshop"):
    """A minimal FourTwenty-shaped raw row (only the columns classify() reads)."""
    return {"categorygroup_1": cg1, "categorygroup_2": cg2}


TABAK = "Tabak, Tabakersatz, Zigaretten und Stopfzub&ouml;hr"  # entity-encoded like the feed
DISPO = "Disposable Einweg E-Zigaretten"
SHISHA = "Shisha"
BLUETEN = "CBD Bl&uuml;ten / Trim - Tabakersatz mit CBD"
POLLEN = "CBD Pollen"
SAMEN = "CBD Samen"


def _age(title, cg2=None, ref_category=None):
    cat, cls, age = classify(title, ref_category, _ft(cg2) if cg2 else None)
    # the returned flag must always agree with the class table (never drift)
    assert age is class_is_age_restricted(cls), (title, cls, age)
    return age, cls, cat


# ---- MUST be flagged 18+ (the leaks we're closing) ------------------------

def test_branded_cigarette_packs_are_18plus():
    for title in ["Marlboro Gold 10x20cig", "Parisienne Jaune Box Big Pack 8x25cig",
                  "Camel Blue Big Pack 8x26cig", "Winston Original Red 10x20cig",
                  "Gauloises Blond Rouge 10x20cig", "Lucky Strike Amber Box 10x20cig"]:
        age, cls, cat = _age(title, TABAK)
        assert age is True, title
        assert cls == "tobacco_nicotine"
        assert cat == "Tobacco & Cigarettes", title  # not "Other"/"Papers"


def test_branded_cigarettes_flagged_even_without_supplier_category():
    # title alone must now carry it (feeds without category groups, on-the-fly, etc.)
    age, cls, _ = _age("Marlboro Gold 10x20cig")
    assert age is True and cls == "tobacco_nicotine"


def test_loose_tobacco_is_18plus():
    age, cls, _ = _age("American Spirit Tabak Dose 75g", TABAK)
    assert age is True and cls == "tobacco_nicotine"


def test_nicotine_disposable_ecig_is_18plus():
    age, cls, _ = _age("Elf Bar Lux 1500 Mango Disposable Pod 20mg", DISPO)
    assert age is True and cls == "tobacco_nicotine"


def test_twenty_mg_not_mistaken_for_zero_mg():
    # regression: "20mg" contains "0mg" — the nicotine-free guard must NOT fire on it.
    age, _, _ = _age("Vozol Gear 7000 Strawberry Smoothie 20mg", DISPO)
    assert age is True


def test_shisha_tobacco_is_18plus():
    for title in ["Swiss Smoke Double Apple Shisha Tabak 50g", "Al Fakher Blueberry"]:
        age, cls, _ = _age(title, SHISHA)
        assert age is True and cls == "tobacco_nicotine", title


def test_shisha_brands_gate_off_title_even_under_coarse_category():
    # DB reality: the fine "Shisha" group is lost, these sit under "Accessories". The molasses
    # BRAND must still gate them off the title alone.
    for title in ["Al Fakher Grape Mint 50g", "Al Fakher Red Smash Watermelon 200g"]:
        age, cls, _ = _age(title, "Accessories")
        assert age is True and cls == "tobacco_nicotine", title


def test_nicotine_ecig_gates_off_title_under_coarse_category():
    # DB reality: nicotine disposables sit under "Vaporizers" with only a "20mg" nicotine signal.
    for title in ["Vozol Vista Plug Pod Banana Ice 20mg",
                  "Elf Bar 1500 Strawberry Ice Cream Disposable Pod 20mg",
                  "Elf Bar 600v2 Blueberry Kiwi 20mg"]:
        age, cls, _ = _age(title, "Vaporizers")
        assert age is True and cls == "tobacco_nicotine", title


def test_prefilled_pod_and_disposable_form_is_nicotine_by_default():
    # no "mg" token at all — the FORM carries nicotine unless it says No-Nic
    for title in ["Elf Bar ELFA Pro Prefilled Pod (2 x 2ml) Blueberry",
                  "Hoke XXL 1600 Watermelon Disposable Pod"]:
        age, cls, _ = _age(title, "Vaporizers")
        assert age is True and cls == "tobacco_nicotine", title


def test_no_nic_prefilled_pod_stays_open():
    age, _, _ = _age("Elf Bar ELFA Pro No Nic Prefilled Pod (2 x 2ml) Apple Peach", "Vaporizers")
    assert age is False


def test_empty_pod_hardware_stays_open():
    for title in ["Elf Bar ELFX Pro Replacement Pod 0.8Ohm",
                  "Elf Bar ELFA Refillable Pod 1.1Ohm 2ml 2pcs",
                  "Lamu Refillable Pod 1.0 Ohm 2ml 2pcs for Elf Bar ELFA"]:
        age, _, _ = _age(title, "Vaporizers")
        assert age is False, title


def test_cbd_eliquid_is_cbd_not_nicotine():
    # a CBD vape liquid is a smokable CBD form (18+) but NOT nicotine — the mg must not misclass it
    _, cls, _ = _age("Harmony CBD E-Liquid 100mg Mango", "E-Liquids")
    assert cls == "cbd_hemp"


def test_cbd_flower_and_pollen_are_18plus():
    assert _age("CBDeluxe White Widow Deluxe 10gr", BLUETEN)[0] is True
    assert _age("Starbuds OG Kush 3g", BLUETEN)[1] == "cbd_hemp"
    assert _age("Some CBD Pollen 5g", POLLEN)[0] is True


# ---- MUST NOT be flagged (over-flagging is a real cost at the till) --------

def test_zero_nicotine_disposable_stays_open():
    for cat in (DISPO, "Vaporizers"):
        age, cls, _ = _age("Elf Bar No Nic 1500 Strawberry Ice Disposable Pod 0mg", cat)
        assert age is False, cat


def test_empty_vape_device_stays_open():
    # a device with no nicotine strength isn't itself nicotine
    age, _, _ = _age("Elf Bar ELFX Pro Kit Black", "Vaporizers")
    assert age is False


def test_cbd_seeds_and_oil_stay_open():
    assert _age("Kannabia Swiss Dream CBD Autoflower Samen 10 Stk.", SAMEN)[0] is False
    assert _age("CBD Samen", SAMEN)[1] == "cbd_open"
    assert _age("CBD Öl 10% 10ml", BLUETEN)[0] is False  # oil form vetoes flower group


def test_tobacco_accessories_and_herbal_stay_open():
    # filling machine, filter tubes, herbal tobacco-substitute — all in the tobacco GROUP but open
    for title in ["Kulu CPT-25 Filling System Assortiert",
                  "Brookfield Filtertubes King Size 200pcs",
                  "Real Leaf Organic Tabakersatz Kräutermischung 30g",
                  "Greengo Drehtabakersatz ohne Nikotin 30g"]:
        age, _, _ = _age(title, TABAK)
        assert age is False, title


def test_papers_and_filters_stay_open():
    assert _age("OCB Premium Rolls Papers", "Papers")[0] is False
    assert _age("Gizeh Filter Tips 6mm", "Filter")[0] is False


def test_shisha_accessories_stay_open():
    for title in ["Hose Adapter zu Boost Shishas", "Aluminium Folien 50 Stk.",
                  "Shishaschlauch m. kl. Glasmundstück 150cm"]:
        age, _, _ = _age(title, SHISHA)
        assert age is False, title


def test_tobacco_pouch_is_accessory_not_substance():
    # the classic false-positive: "Tabaktasche" is a pouch, not tobacco
    age, _, _ = _age("Kavatza Tabaktasche Small", TABAK)
    assert age is False


# ---- reconcile_age: keep product_class (gate reads it) and the flag consistent ----

def test_reconcile_toggle_on_plain_item_files_under_gating_class():
    cls, flag = reconcile_age("standard", True)
    assert cls == "age_restricted" and flag is True


def test_reconcile_toggle_off_is_standard():
    cls, flag = reconcile_age("standard", False)
    assert cls == "standard" and flag is False


def test_reconcile_respects_an_explicit_specific_class():
    # already tobacco -> keep it (don't clobber to the neutral bucket); flag derives True
    cls, flag = reconcile_age("tobacco_nicotine", True)
    assert cls == "tobacco_nicotine" and flag is True


def test_reconcile_derives_flag_from_class_when_flag_absent():
    # flag None -> derive purely from the class (import path)
    assert reconcile_age("cbd_hemp", None) == ("cbd_hemp", True)
    assert reconcile_age("standard", None) == ("standard", False)


def test_reconcile_toggle_off_demotes_the_neutral_bucket():
    # field 2026-07-08: turning 18+ OFF on an "age_restricted" item must actually un-gate it
    # (was stuck 18+ — the flag got re-derived from the unchanged class)
    assert reconcile_age("age_restricted", False) == ("standard", False)


def test_reconcile_toggle_off_never_ungate_a_real_substance_class():
    # a cigarette / CBD flower / alcohol stays gated even if the flag arrives False —
    # the toggle can't un-gate a substance; reclass it explicitly instead
    assert reconcile_age("tobacco_nicotine", False) == ("tobacco_nicotine", True)
    assert reconcile_age("cbd_hemp", False) == ("cbd_hemp", True)
    assert reconcile_age("alcohol", False) == ("alcohol", True)


# ---- Artemis supplier vocabulary (sandbox import review, 2026-07-07) ----

def test_brand_refill_pods_are_nicotine():
    for title in ["ELFBAR NX 7000 Refill Blueberry Ice",
                  "Lost Mary LUX 7000 Refill Banana Volcano",
                  "Lost Mary BM6000 20mg Nachfüllbehälter Blueberry"]:
        age, cls, _ = _age(title)
        assert age is True and cls == "tobacco_nicotine", title


def test_brand_eliquid_with_mg_is_nicotine():
    age, cls, _ = _age("Lost Mary Maryliq, Cherry ICE 10ml, 20mg")
    assert age is True and cls == "tobacco_nicotine"


def test_zero_mg_prefilled_and_ohne_nikotin_stay_open():
    assert _age("ELFBAR - ELFA PRO - Prefilled Pod (2 x 2ml) 0mg Tropical")[0] is False
    assert _age("ELFBAR 1500 OHNE NIKOTIN Pineapple Peach Mango")[0] is False


def test_lighter_gas_refill_is_not_nicotine():
    # "refill" only counts next to a vape brand — a lighter's gas refill must stay open
    assert _age("Clipper Gas Refill 300ml")[0] is False


def test_absinthe_spoon_is_accessory_not_alcohol():
    age, cls, _ = _age("Absinth Löffel Antique 167mm")
    assert age is False and cls != "alcohol"


def test_nic_salt_eliquid_and_aisu_are_nicotine():
    for title in ["Aisu Bar Salt - Dragonfruit 10ml 20mg Salt",
                  "Twelve Monkeys Tropika Nic Salt 10ml 20mg",
                  "Elf Liq Watermelon 10ml 20mg"]:
        age, cls, _ = _age(title)
        assert age is True and cls == "tobacco_nicotine", title


def test_vape_device_and_cbd_oil_stay_open():
    assert _age("GeekVape AEGIS Legend 5 200W Kit mit Z-Subohm Tank")[0] is False
    assert _age("CBD Öl 10ml 500mg Full Spectrum")[0] is False  # 3-digit mg + cbd = not nicotine


# ---- Field leaks closed (Artemis prod run, 2026-07-08) --------------------

def test_nicotine_pouches_english_spelling_are_18plus():
    # the "nicotin\b" boundary missed the English "Nicotine" (trailing e) → pouches leaked as standard
    for title in ["Elf Nicotine Pouches Max Polar Mint 20mg/g",
                  "Killa Nicotine Pouches Cold Mint 16mg", "Pablo Nicotine Pouch Ice Cold"]:
        age, cls, _ = _age(title)
        assert age is True and cls == "tobacco_nicotine", title


def test_cigars_and_cigarillos_are_18plus():
    for title in ["Swisher Sweets classic", "Smock Woods Natural Mild Cigars",
                  "Backwoods Honey Berry", "Villiger Export Cigarillos 10er",
                  "Al Capone Pockets Cigarillo"]:
        age, cls, cat = _age(title)
        assert age is True and cls == "tobacco_nicotine", title
        assert cat == "Tobacco & Cigarettes", title


def test_blunt_wraps_are_gated_conservatively():
    # tobacco-leaf wraps — over-gating is the safe error (Felix/Treuhänder to confirm CH line)
    age, cls, _ = _age("Blunt Wraps Double Platinum Blueberry 2 in 1")
    assert age is True and cls == "tobacco_nicotine"


def test_nicotine_mg_gates_without_an_ecig_context_word():
    # field 2026-07-09 prod leak: "E-Pack"/"Instaflow"/"Starterkit" 20mg had no disposable/pod/vape token
    for title in ["VAAL E-Pack Kit 20mg Blueberry Ice", "VAAL E-Pack Refill 20mg Grape Ice 8Stk.",
                  "Instaflow O Pro Starterkit - Strawberry - 20mg", "Instaflow O Pro Refill - Cola - 20mg",
                  "Killa Snus 16mg Cold Mint", "Some Nic Strips 6mg Peach"]:
        age, cls, _ = _age(title)
        assert age is True and cls == "tobacco_nicotine", title


def test_mg_alone_still_respects_the_guards():
    # the relaxation must NOT gate: 0mg, no-nic, CBD (3-digit mg), or a filter's mm
    assert _age("VAAL E-Pack Kit 0mg Blueberry Ice")[0] is False              # 0mg veto
    assert _age("VAAL E-Pack Refill No Nic 20mg Grape 8Stk.")[0] is False     # no-nic veto beats the mg
    assert _age("Harmony CBD E-Liquid 100mg Mango", cg2=None, ref_category="E-Liquids")[1] == "cbd_hemp"
    assert _age("Gizeh Filter Tips 6mm 100er")[0] is False                    # mm is not mg


def test_nicotine_free_pouch_and_plain_papers_stay_open():
    # the negative guard still wins; a bare rolling paper is never a cigar/wrap
    assert _age("Nicotine Free Pouches Fresh Mint 0mg")[0] is False
    assert _age("OCB Premium Rolls Papers")[0] is False
    assert _age("RAW Classic King Size Slim Papers")[0] is False


def test_permanent_marker_is_not_cbd_or_age_restricted():
    # over-flag caught in the field: a marker was saved cbd_hemp (operator slip) — the classifier
    # itself must land it as plain standard so a reclassify sweep corrects the row
    age, cls, cat = _age("Natural Rebel - Permanent Marker")
    assert age is False and cls == "standard" and cat != "CBD & Hemp"


# ---- resolve_class_on_create: the on-the-fly compliance safety net --------

def test_safety_net_gates_a_tobacco_name_left_as_standard():
    # cashier forgot the 18+ toggle on a tobacco item → the net gates it anyway
    assert resolve_class_on_create("Swisher Sweets classic", "standard", False) == ("tobacco_nicotine", True)
    assert resolve_class_on_create("Elf Nicotine Pouches 20mg/g", None, None) == ("tobacco_nicotine", True)


def test_safety_net_leaves_a_genuine_standard_alone():
    assert resolve_class_on_create("Bic Lighter Blue", "standard", False) == ("standard", False)
    assert resolve_class_on_create("Remedy Kombucha Ginger 250ml", None, None) == ("standard", False)


def test_safety_net_never_ungate_or_downgrade_an_operator_choice():
    # an explicit 18+ toggle stays gated; an explicit specific class is never clobbered
    assert resolve_class_on_create("Mystery Item", "standard", True) == ("age_restricted", True)
    assert resolve_class_on_create("House CBD Flower 3g", "cbd_hemp", None) == ("cbd_hemp", True)
