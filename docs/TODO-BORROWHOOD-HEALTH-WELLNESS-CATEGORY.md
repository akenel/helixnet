# TODO (BorrowHood repo) — add a Health & Wellness category

**Status:** OPEN · raised 2026-06-24 during the Artemis Premium proof
**Where it lives:** the **BorrowHood / La Piazza marketplace repo** (NOT helixnet — that repo
isn't on this machine; this note is here so the task isn't lost).

## The gap

BorrowHood's `ItemCategory` enum (`src/models/item.py`) has Tools, Home, Sports, Creative, Tech,
Spaces, Services, Property, Jobs, Events, plus `food`/`fashion`/`experiences`/`other` — but **no
Health, Wellness, Fitness, Beauty, or Personal-Care category.** For a head shop (CBD creams, balms,
tinctures, supplements) — and honestly for any marketplace — that's the single most natural missing
category. Today these items fall through as a free-string and the edit form defaults to "apartment".

Until this lands, the Artemis Premium publish maps every head-shop item to **`other`** (honest;
beats guessing). See `scripts/artemis_premium_proof.py` canonical mapping.

## The fix (small — NO DB migration; `category` is a free string `max_length=50`)

```python
# src/models/item.py → class ItemCategory(str, enum.Enum):
    # Health & Wellness
    HEALTH_WELLNESS = "health_wellness"
    FITNESS         = "fitness"
    BEAUTY          = "beauty"          # cosmetics, skincare, personal care
```
```python
# the category GROUPS dict (near line 113):
    "health_wellness": ["health_wellness", "fitness", "beauty"],
```
The frontend dropdown is built from the enum, so it picks these up automatically.

## After it lands
- Update the publish mapping (`scripts/artemis_premium_proof.py`, future P2 endpoint) so head-shop
  wellness items map to `health_wellness` instead of `other`.
- Optional BorrowHood UI bug also noticed: the listing **edit form doesn't pre-select the saved
  category** (shows the first option). Worth fixing separately.

## Recommendation
Start with just `health_wellness` (the essential one); add `fitness`/`beauty` if useful. Keep it small.
