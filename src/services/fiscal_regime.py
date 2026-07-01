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
    "IT": {
        # IDENTITY ONLY — jurisdiction facts (currency/locale/VAT-number label + regime code
        # that drives the non-fiscal receipt banner). NO Italian tax RATES here: IVA (22/10/5/4)
        # is P3, deferred behind a commercialista gate. Until then an IT tenant honestly carries
        # the current engine rates (Swiss, from config via _ch_rates) AND the receipt prints
        # "Documento non fiscale — Ricevuta non valida ai fini fiscali". This is jurisdiction
        # IDENTITY, not placeholder tax law — the seal lesson stays honored.
        "regime": "IT",
        "currency": "EUR",
        "locale": "it-IT",
        "vat_number_format": "P. IVA",
    },
}


# --- IT RATE TABLE — TBD-BY-COMMERCIALISTA (P3, NOT WIRED) -----------------------------------
# The SHAPE of an Italian IVA rate table (ordinaria 22 / ridotta 10 / ridotta 5 / minima 4), kept
# as flagged DATA so the N-rate engine has something concrete to bolt onto later. It is NOT
# returned by resolve_regime and NOT fed to split_vat: an IT tenant today honestly runs on the
# Swiss rates in force (see resolve_regime → ch_rate_table) and prints "Documento non fiscale".
# WHICH Italian good is 22/10/5/4 is TAX LAW WE CANNOT INVENT — the labels below are generic and
# NO product class is mapped to them until a commercialista signs off (the seal lesson). Do NOT
# treat this constant as legal until that happens.
IT_RATE_TABLE_TBD: list[dict] = [
    {"code": "22", "label": "aliquota ordinaria", "rate": "22", "default": True, "tbd": True},
    {"code": "10", "label": "aliquota ridotta",   "rate": "10", "tbd": True},
    {"code": "5",  "label": "aliquota ridotta",    "rate": "5",  "tbd": True},
    {"code": "4",  "label": "aliquota minima",     "rate": "4",  "tbd": True},
]


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


def _rate_table_for(code: str) -> list[dict]:
    """The N-rate table ACTUALLY IN FORCE for a regime (drives the receipt/Z-report split loop).

    Every regime today resolves to the CH two-rate table from config — including IT, which runs on
    the Swiss rates until a commercialista wires IT_RATE_TABLE_TBD. So the served table always
    matches what split_vat computes, and a CH tenant is byte-identical (A=8.1 / B=2.6). Rates are
    stringified for a clean JSON payload (the client parseFloat's them, mirroring vat_rate).
    """
    from src.services.vat_resolver import ch_rate_table
    return [
        {"code": e["code"], "label": e["label"], "rate": str(e["rate"]),
         "default": bool(e.get("default", False))}
        for e in ch_rate_table()
    ]


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
        # P3 N-rate: the ordered rate table in force (CH A/B from config). The receipt +
        # Z-report loop over this instead of the two hardwired A/B scalars. CH = byte-identical.
        "vat_rates": _rate_table_for(code),
    }
