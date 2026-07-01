# File: src/services/shop_setup_service.py
"""Banco shop-setup wizard -- the "set up any head shop" brain.

Turns a few facts (name, country, VAT number) into a COMPLETE, sensibly-defaulted set of shop
preferences -- the control data every company needs to run. Assume European; the owner overrides
anything. The output dict maps 1:1 onto StoreSettingsModel (+ the two new prefs currency/language),
so the wizard endpoint can seed store_settings directly.

Pairs with the Banco reference role model: every shop starts with Cashier / Manager / Owner.
Pure + testable -- no DB, no Keycloak, no side effects. The endpoint and form layer on top of this.
"""
from decimal import Decimal

# Country -> sensible European defaults. The owner can override every one of these in the wizard.
# `locale` is BCP-47 (matches the store_settings.locale column); `regime` is the fiscal-regime
# code (PHASE 0). Only CH is a REAL regime today (fiscal_regime.py) — a non-CH code stored here is
# a harmless seam label: resolve_regime() falls back to CH facts for any code it doesn't yet know,
# so this introduces NO Italian/foreign tax law. P2/P3 fill in real per-country regimes + rates.
EUROPEAN_DEFAULTS: dict[str, dict] = {
    "Switzerland": {"currency": "CHF", "vat_rate": Decimal("8.1"),  "language": "de", "locale": "de-CH", "regime": "CH", "prices_include_vat": True},
    "Germany":     {"currency": "EUR", "vat_rate": Decimal("19.0"), "language": "de", "locale": "de-DE", "regime": "DE", "prices_include_vat": True},
    "Austria":     {"currency": "EUR", "vat_rate": Decimal("20.0"), "language": "de", "locale": "de-AT", "regime": "AT", "prices_include_vat": True},
    "Italy":       {"currency": "EUR", "vat_rate": Decimal("22.0"), "language": "it", "locale": "it-IT", "regime": "IT", "prices_include_vat": True},
    "France":      {"currency": "EUR", "vat_rate": Decimal("20.0"), "language": "fr", "locale": "fr-FR", "regime": "FR", "prices_include_vat": True},
    "Netherlands": {"currency": "EUR", "vat_rate": Decimal("21.0"), "language": "en", "locale": "nl-NL", "regime": "NL", "prices_include_vat": True},
}
# When the country isn't in the map, stay European-shaped rather than guess wrong.
_FALLBACK = {"currency": "EUR", "vat_rate": Decimal("20.0"), "language": "en", "locale": "en-GB", "regime": "CH", "prices_include_vat": True}

# The Banco reference role model -- the 3-person shop you described. Every new shop starts here.
REFERENCE_ROLES: list[dict] = [
    {"role": "cashier", "label": "Cashier", "who": "runs the floor day to day",
     "signs_off": [], "max_discount": Decimal("10.0")},
    {"role": "manager", "label": "Manager", "who": "approves refunds, voids, and big discounts",
     "signs_off": ["refund", "void", "discount_over_limit"], "max_discount": Decimal("100.0")},
    {"role": "owner",   "label": "Owner",   "who": "sets the rules; may run several shops",
     "signs_off": ["all"], "max_discount": Decimal("100.0")},
]


def defaults_for(country: str) -> dict:
    """The European defaults for a country (currency, VAT rate, language, prices-include-VAT)."""
    return dict(EUROPEAN_DEFAULTS.get((country or "").strip(), _FALLBACK))


def build_shop_preferences(
    *,
    store_name: str,
    vat_number: str = "",
    country: str = "Switzerland",
    legal_name: str | None = None,
    address_line1: str = "",
    city: str = "",
    postal_code: str = "",
    website: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    store_number: int = 1,
    **overrides,
) -> dict:
    """Assemble a COMPLETE preferences dict from minimal input.

    Country drives currency / VAT rate / language / prices-include-VAT; everything else falls back to
    sensible shop defaults; then any explicit `overrides` win. The result is store_settings-shaped.
    """
    d = defaults_for(country)
    prefs: dict = {
        # identity + control data
        "store_number": store_number,
        "store_name": store_name,
        "legal_name": (legal_name or store_name),
        "vat_number": vat_number,
        "country": (country or "Switzerland"),
        "address_line1": address_line1,
        "city": city,
        "postal_code": postal_code,
        "website": website,
        "phone": phone,
        "email": email,
        # commerce (defaulted from country -- "assume European")
        "currency": d["currency"],
        "vat_rate": d["vat_rate"],
        # PHASE 0 regime seam: reconcile to the real store_settings columns.
        #   default_language -> locale (BCP-47, e.g. de-CH — matches the model, not bare "de")
        #   fiscal_regime added (CH today; non-CH codes are seam labels — see EUROPEAN_DEFAULTS)
        # `prices_include_vat` is deliberately NOT emitted — it has no store_settings column, so
        # every key produced here maps 1:1 onto StoreSettingsModel and StoreSettingsModel(**prefs)
        # never chokes on an unknown kwarg (the plan's "filter unknown keys" — done by construction).
        "locale": d["locale"],
        "fiscal_regime": d["regime"],
        # sign-off rules (the reference role model's discount ceilings)
        "cashier_max_discount": Decimal("10.0"),
        "manager_max_discount": Decimal("100.0"),
        "is_active": True,
    }
    prefs.update(overrides)
    return prefs


def missing_required(prefs: dict) -> list[str]:
    """Which must-fill fields the owner still has to provide before the shop can go live."""
    required = ("store_name", "legal_name", "vat_number", "address_line1", "city", "postal_code")
    return [k for k in required if not str(prefs.get(k) or "").strip()]
