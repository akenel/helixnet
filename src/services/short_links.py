"""Short links for scannable QR codes.

A product's postcard QR should encode as FEW characters as possible: the fewer characters, the
lower the QR's module density, the smaller it can be printed and still scan on a normal phone
(~20 mm on a Brother label). So instead of the full `/pos/products/{uuid}/postcard`, the QR encodes
`/p/{code}` where {code} is a short base62 handle. Hitting `/p/{code}` bumps a scan counter (the QR
is trackable — free analytics off every label) and redirects to the card.

Store-agnostic and tiny: the code + counters live on `products` (additive columns in database.py).
"""
import secrets
from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# base62 minus lookalikes (0/O, 1/l/I) so a code read off a printed label by eye isn't ambiguous.
_ALPHABET = "23456789abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
_CODE_LEN = 6  # 55^6 ≈ 27.7 billion — collisions are astronomically rare, and we retry anyway.


def _mint() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(_CODE_LEN))


async def ensure_short_code(db: AsyncSession, product_id: str) -> Optional[str]:
    """Return the product's short code, minting + persisting one on first use. Idempotent."""
    existing = (await db.execute(
        text("SELECT short_code FROM products WHERE id = :pid"),
        {"pid": product_id},
    )).scalar_one_or_none()
    if existing:
        return existing
    for _ in range(6):  # retry on the (astronomically rare) code collision
        code = _mint()
        try:
            updated = (await db.execute(
                text("""UPDATE products SET short_code = :code
                        WHERE id = :pid AND short_code IS NULL
                        RETURNING short_code"""),
                {"code": code, "pid": product_id},
            )).scalar_one_or_none()
            await db.commit()
            if updated:
                return updated
            # a concurrent request set it first — read the winner back
            return (await db.execute(
                text("SELECT short_code FROM products WHERE id = :pid"),
                {"pid": product_id},
            )).scalar_one_or_none()
        except IntegrityError:
            await db.rollback()  # code already used by another product — mint a new one
    return None


async def resolve_and_bump(db: AsyncSession, code: str) -> Optional[str]:
    """Resolve a short code → product_id, incrementing its scan counter. None if unknown."""
    pid = (await db.execute(
        text("""UPDATE products
                   SET qr_scan_count = COALESCE(qr_scan_count, 0) + 1,
                       qr_last_scanned_at = now()
                 WHERE short_code = :code
             RETURNING id"""),
        {"code": code},
    )).scalar_one_or_none()
    await db.commit()
    return str(pid) if pid else None
