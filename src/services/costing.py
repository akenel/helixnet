"""BL-047b — the cost EYEBALL: a semi-educated guess for a product's cost from its selling price.

Angel: "the guesses should be kind of semi-educated and reasonable and easy to humanly say ok — like an
ABC thing. Cigs are not the same as handmade or papers or incense. Default comes from Settings, but a
pull-down to pick. Leave costs BLANK until the manager edits them from the sold-but-unfinished list. And
it's still a guess until verified — maybe a dead number in 6 months from inflation."

So this NEVER writes a cost automatically. It only powers a button that FILLS the cost box with a
defensible estimate the manager can accept, tweak, or replace with the real delivery-slip number. Cost
stays blank until a human chooses to.

Two layers:
  • CLASS_MARKUP — industry-standard markup% per product class (the "ABC"). A head-shop rule of thumb:
    branded consumables run high margin; regulated tobacco/alcohol run thin (near fixed retail); CBD and
    café sit in between. These are STARTING guesses, deliberately round.
  • the shop's own default (Settings) — overrides the generic default for anything without a class rule.

cost = price × (1 − markup%). All estimates; a real cost always wins once entered.
"""
from __future__ import annotations

# Markup = (price − cost) / price, as a percentage. Higher markup = cheaper cost relative to price.
# Rounded, defensible, head-shop rules of thumb — NOT gospel; the shop tunes the default in Settings and
# overrides per product with the pull-down.
CLASS_MARKUP = {
    "standard":         50,   # branded consumables (papers, filters, glass, accessories)
    "age_restricted":   50,   # neutral 18+ bucket — treat like standard until re-classed
    "tobacco_nicotine": 10,   # thin: fixed retail, tight trade terms (Parisienne sits near 0 in the data)
    "alcohol":          15,   # thin, regulated
    "cbd_hemp":         45,   # flower/hash/vape — decent margin
    "cbd_open":         45,   # oils/seeds/cosmetics
    "cafe_food":        60,   # food & drink run high
}

DEFAULT_MARKUP = 50           # the fallback when a shop hasn't set its own default

# The pull-down the operator sees on the card — labelled, round, easy to reason about.
MARKUP_CHOICES = [10, 25, 33, 50, 60, 75]


def class_markup(product_class: str | None) -> int:
    """The industry-standard markup for a class (the ABC guess)."""
    return CLASS_MARKUP.get((product_class or "").strip().lower(), DEFAULT_MARKUP)


def estimate_cost(price, markup_pct) -> float | None:
    """cost = price × (1 − markup%). None if there's no price to work from (can't guess a cost from
    nothing — the whole reason a zero-priced item shows no eyeball)."""
    try:
        p = float(price)
        m = float(markup_pct)
    except (TypeError, ValueError):
        return None
    if p <= 0 or not (0 <= m < 100):
        return None
    return round(p * (1 - m / 100.0), 2)
