"""Catalog enrichment classifier — the 18+ decision is made at IMPORT time.

The whole point (Felix's Artemis UAT, 2026-07-06): a product should come out of the
enrichment already knowing whether it's age-restricted — cigarettes and CBD flower = 18+,
papers and filters = open. The signal that makes this reliable is the SUPPLIER's own
category (stored in `raw`), not just the title: real cigarette packs are titled
"Marlboro Gold 10x20cig" with no "tabak"/"zigarette" token at all, so a title-only
classifier leaked them through as un-gated goods.

Pure function, no DB/network — fast regression guard on classify().
"""
from src.services.catalog_taxonomy import classify, class_is_age_restricted, reconcile_age


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
