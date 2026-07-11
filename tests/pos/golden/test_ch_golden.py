"""CH GOLDEN LOCK (P0 of docs/BANCO-GO-ITALIAN-PLAN.md).

Freezes the Swiss VAT numbers, the A/B turnover/VAT split, the reconciliation
invariants, and the /config scalar keys as a canonical baseline. Later euro / i18n /
date-locale work re-runs this file UNCHANGED; any drift in a single CH franc, a flipped
A/B bucket, a broken reconciliation, or a changed /config scalar default fails HERE.

Doctrine (see the plan): we freeze the NUMBERS + the A/B split + the pre-existing /config
scalar keys — NOT the rendered HTML (banners/labels are additive and will legitimately
change). The golden truth is HAND-VERIFIED (see ch-canonical-cart.json + the roll-up in
test_reconciliation_cent_exact), not "snapshot whatever the code emits" — so a broken
baseline cannot be frozen.

Pure host test — no server, no docker, no Keycloak. `_rates` skips settings when rates are
injected (vat_resolver.py), and the /config scalars are read by text-parsing config.py
defaults (config.py cannot import on the host — its module body boots Settings()). The
parent tests/pos autouse server fixture is neutralised by this dir's conftest.py.

Run:
    . .venv/bin/activate && pytest tests/pos/golden -v
Also auto-collected by `make test-pos` (recurses tests/pos/).
"""
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from src.services.vat_resolver import split_vat, contained_vat  # noqa: E402

GOLDEN = json.loads((Path(__file__).parent / "ch-canonical-cart.json").read_text())
STD = GOLDEN["rates"]["standard"]
RED = GOLDEN["rates"]["reduced"]


# The parent tests/pos/conftest.py has an autouse `_ensure_open_drawer` fixture that mints a
# real Keycloak token + opens a cash drawer before every test — i.e. it needs a live server.
# These golden tests are PURE (host .venv, no server), so no-op that fixture here.
# NB: this override lives in the test MODULE, not a sibling conftest.py — a second conftest.py
# would collide on the `conftest` module name in prepend import mode and break
# `from conftest import ...` in every other tests/pos file (the old 28-error collection bug).
@pytest.fixture(autouse=True)
def _ensure_open_drawer():
    yield


def _D(s):  # exact money
    return Decimal(str(s))


def _split():
    """Run the real engine on the frozen cart with the frozen injected rates."""
    lines = [(l["expected_rate"], l["gross"]) for l in GOLDEN["lines"]]
    basis = GOLDEN["expected_basis"]
    return split_vat(lines, basis["total"], basis["subtotal"],
                     standard_rate=STD, reduced_rate=RED)


# ---- (1) per-line contained VAT is frozen ----------------------------------
@pytest.mark.parametrize("ln", GOLDEN["lines"], ids=[l["id"] for l in GOLDEN["lines"]])
def test_line_contained_vat_frozen(ln):
    got = contained_vat(ln["gross"], ln["expected_rate"])
    assert got == _D(ln["expected_contained_vat"]), (
        f"line {ln['id']} contained VAT drift: got {got} "
        f"expected {ln['expected_contained_vat']}"
    )


# ---- (2) the split matches the frozen golden EXACTLY ------------------------
def test_split_matches_golden():
    got = _split()
    exp = GOLDEN["expected_split"]
    for k in ("turnover_standard", "turnover_reduced",
              "vat_standard", "vat_reduced", "vat_total"):
        assert got[k] == _D(exp[k]), f"{k} drift: got {got[k]} expected {exp[k]}"


# ---- (3) reconciliation invariants (anti-circular; baseline not broken) -----
def test_reconciliation_cent_exact():
    got = _split()
    basis = GOLDEN["expected_basis"]
    # Sum of the two turnover streams == the sale basis, cent-exact.
    assert got["turnover_standard"] + got["turnover_reduced"] == _D(basis["subtotal"])
    assert _D(basis["subtotal"]) == _D(basis["total"])
    # vat_total == vat_standard + vat_reduced, cent-exact.
    assert got["vat_total"] == got["vat_standard"] + got["vat_reduced"]
    # And that sum equals the INDEPENDENTLY hand-verified golden roll-up:
    #   standard: 6.74 + 0.90 + 7.70 = 15.34 ; reduced: 0.13 + 0.20 + 0.00 = 0.33
    #   vat_total = 15.34 + 0.33 = 15.67 ; turnover = 209.60 + 13.00 = 222.60
    assert got["vat_total"] == _D("15.67")
    assert got["turnover_standard"] + got["turnover_reduced"] == _D("222.60")


# ---- (4) /config scalar keys frozen (host-safe: parse config.py defaults) ---
def test_config_scalar_defaults_frozen():
    src = (REPO / "src" / "core" / "config.py").read_text()

    def _default(name):
        # Anchor on ":" so POS_VAT_RATE does not match POS_VAT_RATE_REDUCED.
        m = re.search(rf"^\s*{name}\s*:\s*\w+\s*=\s*([^\s#]+)", src, re.M)
        assert m, f"{name} default not found in config.py"
        return m.group(1)

    exp = GOLDEN["expected_config"]
    assert float(_default("POS_VAT_RATE")) == exp["vat_rate"]["value"]
    assert float(_default("POS_VAT_RATE_REDUCED")) == exp["vat_rate_reduced"]["value"]
    assert int(_default("POS_VAT_YEAR")) == exp["vat_year"]["value"]
    assert _default("POS_CURRENCY").strip('"') == exp["currency"]["value"]
    assert _default("POS_LOCALE").strip('"') == exp["locale"]["value"]
    # vat_decimal is the /config endpoint's computed field (POS_VAT_RATE / 100).
    assert round(exp["vat_rate"]["value"] / 100, 6) == exp["vat_decimal"]["value"]
