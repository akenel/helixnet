"""artemis_image_backfill.py — BL-17: pull external supplier images into our own storage (MinIO).

The bulk Artemis import captured image_url as a HOTLINK to artemisluzern.ch (and FourTwenty for
reference-adopted items). A hotlink can rot, be slow, or be blocked by the supplier — so a phone at
the counter sometimes shows "found the name but no picture" (the BL-17 report). This backfills by
downloading each external image ONCE into MinIO and repointing products.image_url at our own
/api/v1/pos/... serve URL — the same thing the adopt path does, but for the already-imported catalog.

Safe: only touches EXTERNAL urls (never re-copies one already in our storage); never overwrites a
good local image; rotation marker (image_checked_at) means a broken/blocked url is looked at once
then sinks to the back of the queue instead of clogging the batch (same pattern as BL-18); polite
delay + real UA; batch-capped. NEVER raises on a single bad image — it stamps and moves on.

Run inside a banco container (scripts/ not mounted — docker cp first):
    docker exec -w /app -e PYTHONPATH=/app <container> \
        python /app/scripts/artemis_image_backfill.py --limit 60 --delay 0.4
Cron drains it: run every few minutes until "remaining ~0".
"""
import argparse
import asyncio
import io
import time
from datetime import datetime, timezone

import httpx
from sqlalchemy import and_, func, or_, select

from src.db.database import get_db_session_context
from src.db.models.product_model import ProductModel, ProductImageModel

UA = "Mozilla/5.0 (BancoCatalog/1.0; +https://banco.lapiazza.app)"


def _process(raw: bytes) -> bytes:
    """Resize/tidy via the shared image pipeline; fall back to the raw bytes if Pillow is absent."""
    try:
        from src.services.image_intake import process, PRODUCT
        return process(raw, PRODUCT).main
    except ImportError:
        return raw


async def _migrate_one(db, p, timeout: float) -> str:
    """Download p.image_url → MinIO, repoint p.image_url. Returns 'ok' | 'empty' | 'err'.
    NEVER raises — a single bad image must not kill the batch."""
    from src.services.minio_service import minio_service
    url = (p.image_url or "").strip()
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as c:
            resp = await c.get(url, headers={"User-Agent": UA})
        if resp.status_code != 200 or not resp.content:
            return "empty"                     # gone / blocked — keep the hotlink, rotate away
        out = _process(resp.content)
    except Exception:
        return "err"                            # transient fetch/decode error — retry later
    try:
        image = ProductImageModel(product_id=p.id, sort_order=0)
        db.add(image)
        await db.flush()
        key = f"pos-products/{p.id}/{image.id}.jpg"
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, minio_service.client.put_object,
            minio_service.bucket_name, key, io.BytesIO(out), len(out), "image/jpeg",
        )
        p.image_url = f"/api/v1/pos/products/{p.id}/images/{image.id}"
        return "ok"
    except Exception:
        return "err"


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=60, help="max products per run (cron batch cap)")
    ap.add_argument("--delay", type=float, default=0.4, help="polite seconds between fetches")
    ap.add_argument("--timeout", type=float, default=20.0, help="per-image fetch timeout")
    ap.add_argument("--sku-prefix", default="", help="limit to a SKU marker (default: all)")
    args = ap.parse_args()

    # External hotlink = an http(s) url that isn't already one of our serve URLs.
    external = and_(
        ProductModel.image_url.like("http%"),
        ProductModel.image_url.notlike("%/api/v1/pos/%"),
    )
    where = [external]
    if args.sku_prefix:
        where.append(ProductModel.sku.like(f"{args.sku_prefix}%"))

    async with get_db_session_context() as db:
        backlog = (await db.execute(
            select(func.count()).select_from(ProductModel).where(*where)
        )).scalar_one()
        # Never-checked first, then least-recently-checked (BL-18 rotation pattern) — a blocked
        # or dead image gets looked at once, stamped, and sinks below the fresh candidates.
        rows = (await db.execute(
            select(ProductModel).where(*where)
            .order_by(ProductModel.image_checked_at.asc().nulls_first(), ProductModel.sku)
            .limit(args.limit)
        )).scalars().all()

        now = datetime.now(timezone.utc)
        ok = empty = err = 0
        for p in rows:
            outcome = await _migrate_one(db, p, args.timeout)
            p.image_checked_at = now            # looked-at regardless of outcome
            if outcome == "ok":
                ok += 1
            elif outcome == "empty":
                empty += 1
            else:
                err += 1
            await db.commit()                    # commit per-image so a later failure can't lose earlier wins
            time.sleep(args.delay)

    print(f"[bl17-image-backfill] backlog {backlog} | tried {len(rows)} | migrated {ok} | "
          f"empty {empty} | err {err} | remaining ~{max(0, backlog - ok)}")


if __name__ == "__main__":
    asyncio.run(main())
