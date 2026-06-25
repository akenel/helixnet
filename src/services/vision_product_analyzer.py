"""
Photo → draft product — the PRODUCT consumer of the vision engine (src/services/vision).

The Banco pain: head-shop goods are mostly loose / unbarcoded and will never be
cleanly searchable. So the cashier SNAPS the item and a vision model drafts the
fields; the human confirms. This module is now a thin wrapper — the actual brain,
provider selection and parsing live in the shared engine (`vision.py`) so ISOTTO,
La Piazza listings and seed-to-sale lab reports reuse the same capability.

Kept for back-compat: `suggest_product_from_image()` and `VisionImageError` (so the
POS route and tests don't change). The response keeps its original shape
({"suggestion": {...}, ...}); the engine returns it under "data".
"""
from __future__ import annotations

from src.services.vision import PRODUCT, VisionImageError, analyze_image

__all__ = ["suggest_product_from_image", "VisionImageError"]


async def suggest_product_from_image(
    raw: bytes,
    content_type: str = "image/jpeg",
    *,
    hint: str | None = None,
    provider: str | None = None,
) -> dict:
    """Photo bytes → draft product fields.

    Returns {"suggestion": {...}, "provider", "model", "elapsed_ms", "note"}. NEVER
    raises for model/transport problems (blank suggestion + a `note` so the cashier
    can just type it). Raises VisionImageError for un-decodable bytes (route → 400)."""
    r = await analyze_image(raw, content_type, domain=PRODUCT, hint=hint, provider=provider)
    return {
        "suggestion": r["data"], "provider": r["provider"], "model": r["model"],
        "elapsed_ms": r["elapsed_ms"], "note": r["note"],
    }
