"""artemis_description_backfill.py — BL-18: fill blank Artemis descriptions from the real page.

The bulk Artemis import captured name/price/image/url but NOT descriptions (they live on each
product's detail page — "a later step"). This backfills `products.description` by fetching each
product's `source_url` and extracting `<div id="Description">` (same extraction the enrich pass
uses). Designed to run as a CRON in small polite batches so it drains the ~5k backlog over many
runs without hammering artemisluzern.ch.

Safe: fills BLANKS only (never overwrites), skips manager-frozen (`sync_override`) rows, idempotent
(a filled row drops out of the next run's query), batch-capped, polite delay + real UA.

Run inside a banco container (scripts/ not mounted — docker cp first):
    docker exec -w /app -e PYTHONPATH=/app <container> \
        python /app/scripts/artemis_description_backfill.py --limit 60 --delay 0.4
Cron drains it: run every few minutes until "remaining ~0".
"""
import argparse
import asyncio
import gzip
import html
import re
import time
import urllib.error
import urllib.request

from sqlalchemy import func, or_, select

from src.db.database import get_db_session_context
from src.db.models.product_model import ProductModel

UA = "Mozilla/5.0 (BancoCatalog/1.0; +https://banco.lapiazza.app)"
_RX_DESC = re.compile(r'id="Description"[^>]*>(.*?)</div>', re.S | re.I)   # same as the enrich pass
_RX_TAG = re.compile(r"<[^>]+>")


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_RX_TAG.sub(" ", s or ""))).strip()


def fetch_description(url: str, timeout: int = 30) -> str | None:
    """Return the cleaned detail-page description, '' if the page has none, None on fetch error."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
    except Exception:
        return None
    page = raw.decode("utf-8", "replace")
    m = _RX_DESC.search(page)
    return _clean(m.group(1)) if m else ""


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=60, help="max products per run (cron batch cap)")
    ap.add_argument("--delay", type=float, default=0.4, help="polite seconds between fetches")
    ap.add_argument("--sku-prefix", default="TAM-", help="Artemis marker (default TAM-)")
    ap.add_argument("--max-chars", type=int, default=2000, help="truncate very long descriptions")
    args = ap.parse_args()

    blank = or_(ProductModel.description.is_(None), ProductModel.description == "")
    where = (ProductModel.sku.like(f"{args.sku_prefix}%"),
             ProductModel.source_url.isnot(None), blank)

    async with get_db_session_context() as db:
        backlog = (await db.execute(
            select(func.count()).select_from(ProductModel).where(*where)
        )).scalar_one()
        rows = (await db.execute(
            select(ProductModel).where(*where).order_by(ProductModel.sku).limit(args.limit)
        )).scalars().all()

        filled = empty = frozen = 0
        for p in rows:
            if getattr(p, "sync_override", False):
                frozen += 1
                continue
            desc = fetch_description(p.source_url)
            if desc:
                p.description = desc[: args.max_chars].strip()
                filled += 1
            else:
                empty += 1          # '' (no desc on page) or None (fetch error) — try again next run
            time.sleep(args.delay)
        await db.commit()

    print(f"[bl18-backfill] backlog {backlog} | tried {len(rows)} | filled {filled} | "
          f"empty/err {empty} | frozen {frozen} | remaining ~{max(0, backlog - filled)}")


if __name__ == "__main__":
    asyncio.run(main())
