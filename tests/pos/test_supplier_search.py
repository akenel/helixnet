"""Unit tests for the live supplier-search adapters — parser logic, no network.

Each adapter's HTML/JSON parsing is exercised with small fixtures that mirror the real
sites (Magento / Tamar / Shopware 5). The live HTTP path is proven separately by hand;
here we lock the extraction (title, price, EAN, image, description, tier ladder, currency).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.services.supplier_search.base import parse_chf, score_title, money2
from src.services.supplier_search.fourtwenty import FourTwentyAdapter
from src.services.supplier_search.artemis import ArtemisAdapter
from src.services.supplier_search.neardark import NearDarkAdapter


# ---- base helpers -----------------------------------------------------------
def test_parse_chf_variants():
    assert parse_chf("CHF 6.90") == 6.90
    assert parse_chf("39.–") == 39.00       # en-dash cents = .00
    assert parse_chf("39.-") == 39.00
    assert parse_chf("7,00") == 7.00        # German comma decimal
    assert parse_chf("CHF 1'234.50") == 1234.50
    assert parse_chf("") is None and parse_chf(None) is None


def test_score_title_substring_beats_fuzzy():
    assert score_title("tycoon", "Tycoon Gas 250ml") >= 0.75
    assert score_title("tycoon", "Cyclones Hülsen") < 0.4


def test_money2_string_cents():
    assert money2(4) == "4.00" and money2(3.5) == "3.50"


# ---- FourTwenty (Magento) ---------------------------------------------------
FT_HTML = '''
<div data-role="priceBox"></div>
<span data-ui-id="page-title-wrapper" itemprop="name">Tycoon Gas 250ml</span>
<meta itemprop="price" content="5" /><meta itemprop="priceCurrency" content="CHF" />
"priceConfig": {"tierPrices":[{"qty":12,"price":4},{"qty":72,"price":3.5}]}
{"thumb":"x","img":"https:\\/\\/fourtwenty.ch\\/media\\/catalog\\/product\\/cache\\/a\\/b\\/xyz.jpeg"}
<th>EAN</th><td data-th="EAN">4035687900004</td>
<div class="product attribute description"><div class="value">100% reinstes Butangas.</div></div>
{"@type": "ListItem","position": 5,"name": "Extraktion"}
{"@type": "ListItem","position": 6,"name": "Tycoon Gas 250ml"}
'''


def test_fourtwenty_parse_product():
    r = FourTwentyAdapter._parse_product(FT_HTML, "https://fourtwenty.ch/tycoon-gas-250ml-cs-gas250.html", "tycoon")
    assert r.title == "Tycoon Gas 250ml"
    assert r.price == 5.0 and r.currency == "CHF"
    assert r.barcode == "4035687900004"
    assert "xyz.jpeg" in r.image_url and "\\" not in r.image_url
    assert r.category == "Extraktion"
    assert r.price_tiers == [
        {"min_qty": 1, "unit_price": "5.00"},
        {"min_qty": 12, "unit_price": "4.00"},
        {"min_qty": 72, "unit_price": "3.50"},
    ]
    d = r.to_dict()
    assert d["is_live"] and d["is_reference"] and d["name"] == r.title


def test_fourtwenty_is_product_page():
    assert FourTwentyAdapter._is_product_page(
        "https://fourtwenty.ch/x.html", 'data-ui-id="page-title-wrapper" data-role="priceBox"')
    assert not FourTwentyAdapter._is_product_page("https://fourtwenty.ch/search/zippo", "grid")


def test_fourtwenty_no_title_returns_none():
    assert FourTwentyAdapter._parse_product("<div>nothing</div>", "u", "q") is None


# ---- Artemis (Tamar) --------------------------------------------------------
ART_HTML = '''
<p class="Breadcrumps"><a href="/en/headshop">Headshop</a><a href="/en/headshop/lighters">Lighters</a>
<a href="/en/headshop/lighters/accessories">Accessories</a></p>
<h1>Feuerzeug Gas Tycoon 250ml</h1>
<span class="SalesPrice">CHF 6.90 </span>
<table class="BulkPrices"><tbody>
<tr><td class="Currency">CHF</td><td class="Price1">4.</td><td class="Price2">70</td><td class="Amount">from 12 pieces</td></tr>
<tr><td class="Currency">CHF</td><td class="Price1">3.</td><td class="Price2">90</td><td class="Amount">from 60 pieces</td></tr>
</tbody></table>
<div id="Description">High-purity, tasteless butane gas.</div>
'''


def test_artemis_build_from_detail():
    listed = {"name": "Feuerzeug Gas Tycoon 250ml", "salesPriceText": "CHF 6.90",
              "coverUrl": "/ProductImage.ashx?id=abc", "linkUrl": "/en/product/feuerzeug-gas-tycoon-250ml-5851"}
    r = ArtemisAdapter._build(listed, ART_HTML, "tycoon")
    assert r.title == "Feuerzeug Gas Tycoon 250ml"
    assert r.price == 6.90 and r.currency == "CHF"
    assert r.barcode is None                       # Artemis publishes no EAN
    assert r.category == "Accessories"
    assert r.image_url.endswith("/ProductImage.ashx?id=abc")
    assert "butane" in r.description.lower()
    assert r.price_tiers == [
        {"min_qty": 1, "unit_price": "6.90"},
        {"min_qty": 12, "unit_price": "4.70"},
        {"min_qty": 60, "unit_price": "3.90"},
    ]


def test_artemis_no_tiers_when_no_table():
    listed = {"name": "Thing", "salesPriceText": "CHF 5.–", "linkUrl": "/en/product/thing-1"}
    r = ArtemisAdapter._build(listed, "<h1>Thing</h1>", "thing")
    assert r.price == 5.0 and r.price_tiers == []


# ---- Near Dark (Shopware 5, EUR) --------------------------------------------
ND_HTML = '''
<h1 class="product--title">Black Leaf Cyber Skull Grinder 4-tlg. rot</h1>
<meta property="product:price" content="7,00" />
<meta property="product:price:currency" content="EUR" />
<div class="ean"><span>EAN:</span> 4250153632122</div>
<meta property="og:image" content="https://www.neardark.de/media/image/x.jpg" />
<div itemprop="description">4-teiliger Aluminium-Grinder mit Diamantschliff.</div>
'''


def test_neardark_parse_eur():
    url = "https://www.neardark.de/marken/sly-art/5561/black-leaf-cyber-skull-grinder-4-tlg.-rot"
    r = NearDarkAdapter._parse(ND_HTML, url, "grinder")
    assert r.title.startswith("Black Leaf Cyber Skull Grinder")
    assert r.price == 7.00 and r.currency == "EUR"
    assert r.barcode == "4250153632122"
    assert r.image_url.endswith("x.jpg")
    assert r.category == "Sly Art"                 # segment before the numeric id
    assert r.price_tiers == []                      # Near Dark publishes no breaks
    assert "grinder" in r.description.lower()
