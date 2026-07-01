"""Fiscal regime resolver — the single seam for how a tenant's till behaves per fiscal
jurisdiction (regime code, currency, locale, VAT rates + VAT-number format).

PHASE 0 of docs/BANCO-GO-ITALIAN-PLAN.md: a THIN, PURE, no-DB selector. CH ONLY for now —
an IT regime is DEFERRED until a real Italian shop + commercialista sign off. Do NOT add
placeholder Italian tax law here (it would rot and mislead — the seal lesson).

Modeled on catalog_taxonomy.class_meta: a module-level REGIMES dict of static jurisdiction
facts + a resolver that falls back to the default (CH) for None / unknown. The Swiss VAT
RATES are READ LIVE FROM config (POS_VAT_RATE / POS_VAT_RATE_REDUCED) — the single source,
so an 8.1 → 8.5 change stays one edit in config.py and is never duplicated here.
"""

DEFAULT_REGIME = "CH"

# Static, jurisdiction-level facts ONLY — NOT the VAT rates (those are read live from config
# so there is exactly one source of truth for Swiss VAT). CH only; IT deferred by design.
REGIMES: dict[str, dict] = {
    "CH": {
        "regime": "CH",
        "currency": "CHF",
        "locale": "de-CH",
        "vat_number_format": "CHE-XXX.XXX.XXX MWST",
    },
}


def _ch_rates() -> dict:
    """Swiss VAT rates, read live from config — the single source (never hardcoded here).

    Config is imported LAZILY (inside the function, like vat_resolver._rates) so this module
    stays host-importable: src.core.config boots Settings() at import and would fail without
    a full env, which would break pure host tests that import fiscal_regime.
    """
    from src.core.config import get_settings
    s = get_settings()
    return {
        "vat_rate": s.POS_VAT_RATE,
        "vat_rate_reduced": s.POS_VAT_RATE_REDUCED,
    }


def regime_meta(code: str | None) -> dict:
    """Static regime facts for a code; defaults to CH for None / unknown (like class_meta)."""
    base = REGIMES.get(code or DEFAULT_REGIME, REGIMES[DEFAULT_REGIME])
    return dict(base)


def resolve_regime(store=None) -> dict:
    """Merged regime dict for a store_settings row (or None → pure CH from config).

    Pure, no DB, never raises on a missing/None store. The store's `fiscal_regime` selects
    the jurisdiction facts; the store's own `currency`/`locale` win when set (the future
    per-tenant override), else the regime defaults apply. VAT rates always come live from
    config. For a CH tenant every field seeds to CHF / de-CH / CH, so the resolved dict is
    byte-identical whether it came from Store #1 or the None fallback.
    """
    code = getattr(store, "fiscal_regime", None) or DEFAULT_REGIME
    meta = regime_meta(code)
    currency = getattr(store, "currency", None) or meta["currency"]
    locale = getattr(store, "locale", None) or meta["locale"]
    return {
        **meta,
        "currency": currency,
        "locale": locale,
        **_ch_rates(),
    }
