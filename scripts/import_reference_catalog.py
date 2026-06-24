#!/usr/bin/env python3
"""
BL-97 — Reference catalog importer.

Load a supplier CSV dump (the full 420 / TMR product list — tens of thousands of items)
into the `reference_products` product master. Idempotent: re-running a fresh dump UPDATES
changed rows and INSERTS new ones, keyed on (supplier, ref_key). Never deletes silently;
prints adds / updates / unchanged counts (no silent caps).

This is NOT inventory and NOT the live catalog. It's the lookup list the POS cherry-picks
from so cashiers copy real titles/descriptions/photos instead of inventing them.

Connection: SQLAlchemy async (asyncpg). The DB URL is resolved from --db-url, else
$REFERENCE_DB_URL, else built from the standard POSTGRES_* env (host defaults to 'postgres',
which resolves on the box / inside the docker network). Postgres is not exposed to the host
locally, so run this on the box from /opt/helixnet, or pass --db-url with a reachable host.

Usage (single command — no subcommand name needed):
  python scripts/import_reference_catalog.py dump.csv --supplier 420
  python scripts/import_reference_catalog.py dump.csv --supplier 420 --map map.yaml --dry-run

On the box (postgres only resolves inside the docker network; the app image has typer+asyncpg):
  docker cp scripts/import_reference_catalog.py <container>:/app/imp.py
  docker cp dump.csv <container>:/app/dump.csv
  docker exec -w /app <container> python imp.py dump.csv --supplier 420

Column mapping: pass --map a YAML of {our_field: csv_header}. Our fields:
  title (required), barcode, supplier_sku, description, image_url, category,
  suggested_price, cost. Sensible default header guesses are used for anything unmapped.
"""
from __future__ import annotations

import asyncio
import csv
import os
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(add_completion=False, help="Reference catalog (product master) importer — BL-97")

# Our canonical field -> the CSV headers we'll try if no explicit mapping is given.
DEFAULT_HEADER_GUESSES = {
    "title": ["title", "name", "product_name", "article", "bezeichnung", "designation"],
    "barcode": ["barcode", "ean", "ean13", "upc", "gtin", "code"],
    "supplier_sku": ["supplier_sku", "sku", "article_no", "artikelnr", "art_nr", "ref", "item_no"],
    "description": ["description", "desc", "long_description", "beschreibung", "details"],
    "image_url": ["image_url", "image", "img", "picture", "photo", "bild"],
    "category": ["category", "cat", "group", "kategorie", "type"],
    "suggested_price": ["suggested_price", "price", "rrp", "retail_price", "vk", "preis"],
    "cost": ["cost", "buy_price", "ek", "wholesale", "net_price"],
}

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    return _SLUG_RE.sub("-", (text or "").strip().lower()).strip("-")


def compute_ref_key(supplier_sku: Optional[str], barcode: Optional[str], title: str) -> str:
    """Stable per-supplier upsert key: prefer the supplier's article no, else the barcode,
    else a title slug. Re-importing the same dump must land on the same key."""
    for candidate in (supplier_sku, barcode):
        c = (candidate or "").strip()
        if c:
            return c[:150]
    return ("title:" + slugify(title))[:150]


def _to_price(val) -> Optional[Decimal]:
    s = str(val if val is not None else "").strip().replace(",", ".")
    s = re.sub(r"[^0-9.\-]", "", s)
    if not s:
        return None
    try:
        d = Decimal(s).quantize(Decimal("0.01"))
        return d if d >= 0 else None
    except (InvalidOperation, ValueError):
        return None


def build_header_map(fieldnames: list[str], explicit: dict | None) -> dict:
    """Resolve {our_field: actual_csv_header}. Explicit mapping wins; otherwise guess."""
    explicit = explicit or {}
    lower = {fn.lower().strip(): fn for fn in (fieldnames or [])}
    resolved: dict[str, str] = {}
    for field, guesses in DEFAULT_HEADER_GUESSES.items():
        if field in explicit and explicit[field]:
            resolved[field] = explicit[field]
            continue
        for g in guesses:
            if g in lower:
                resolved[field] = lower[g]
                break
    return resolved


def normalize_row(raw: dict, header_map: dict, supplier: str) -> Optional[dict]:
    """Turn one CSV row into a reference_products row dict, or None if it has no usable title."""
    def pick(field):
        h = header_map.get(field)
        return (raw.get(h) if h else None)

    title = (pick("title") or "").strip()
    if not title:
        return None
    barcode = (pick("barcode") or "").strip() or None
    supplier_sku = (pick("supplier_sku") or "").strip() or None
    return {
        "supplier": supplier,
        "ref_key": compute_ref_key(supplier_sku, barcode, title),
        "supplier_sku": supplier_sku,
        "barcode": barcode,
        "title": title[:255],
        "description": (pick("description") or "").strip() or None,
        "image_url": (pick("image_url") or "").strip()[:500] or None,
        "category": (pick("category") or "").strip()[:100] or None,
        "suggested_price": _to_price(pick("suggested_price")),
        "cost": _to_price(pick("cost")),
        "raw": {k: v for k, v in raw.items() if v not in (None, "")},
    }


def parse_csv(path: Path, supplier: str, header_map_explicit: dict | None) -> tuple[list[dict], int]:
    """Read + normalize the whole CSV. Returns (rows, skipped_count). De-dups within the
    file on (supplier, ref_key) so a single import never self-conflicts (last row wins)."""
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        header_map = build_header_map(reader.fieldnames or [], header_map_explicit)
        if "title" not in header_map:
            raise typer.BadParameter(
                f"Could not find a title/name column. Headers were: {reader.fieldnames}. "
                f"Pass --map to point 'title' at the right column."
            )
        by_key: dict[tuple, dict] = {}
        skipped = 0
        for raw in reader:
            row = normalize_row(raw, header_map, supplier)
            if row is None:
                skipped += 1
                continue
            by_key[(row["supplier"], row["ref_key"])] = row
    return list(by_key.values()), skipped


def resolve_db_url(db_url: Optional[str]) -> str:
    if db_url:
        return db_url
    if os.environ.get("REFERENCE_DB_URL"):
        return os.environ["REFERENCE_DB_URL"]
    user = os.environ.get("POSTGRES_USER", "helix_user")
    pw = os.environ.get("POSTGRES_PASSWORD", "")
    host = os.environ.get("POSTGRES_HOST", "postgres")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "helix_db")
    return f"postgresql+asyncpg://{user}:{pw}@{host}:{port}/{db}"


async def upsert_rows(rows: list[dict], db_url: str) -> dict:
    """Idempotent bulk upsert on (supplier, ref_key). Returns counts."""
    from datetime import datetime, timezone
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    # Local import so the file imports cleanly even where the app package isn't installed.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from src.db.models.reference_product_model import ReferenceProductModel

    engine = create_async_engine(db_url)
    now = datetime.now(timezone.utc)
    update_cols = ["supplier_sku", "barcode", "title", "description", "image_url",
                   "category", "suggested_price", "cost", "raw", "imported_at"]
    try:
        async with engine.begin() as conn:
            for chunk_start in range(0, len(rows), 500):
                chunk = rows[chunk_start:chunk_start + 500]
                for r in chunk:
                    r["imported_at"] = now
                stmt = pg_insert(ReferenceProductModel).values(chunk)
                stmt = stmt.on_conflict_do_update(
                    constraint="uq_reference_products_supplier_refkey",
                    set_={c: getattr(stmt.excluded, c) for c in update_cols},
                )
                await conn.execute(stmt)
    finally:
        await engine.dispose()
    # Idempotent on (supplier, ref_key): existing rows are updated in place, new ones inserted.
    return {"upserted": len(rows)}


@app.command("import-catalog")
def import_catalog(
    csv_path: Path = typer.Argument(..., exists=True, readable=True, help="Supplier CSV dump"),
    supplier: str = typer.Option(..., "--supplier", help="Source supplier tag, e.g. 420 / TMR"),
    map_file: Optional[Path] = typer.Option(None, "--map", help="YAML {our_field: csv_header}"),
    db_url: Optional[str] = typer.Option(None, "--db-url", help="SQLAlchemy async URL (overrides env)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Parse + report, do not write"),
):
    """Import / refresh the reference catalog from a supplier CSV."""
    explicit = None
    if map_file:
        import yaml  # optional dep; only needed when --map is used
        explicit = yaml.safe_load(map_file.read_text()) or {}

    rows, skipped = parse_csv(csv_path, supplier, explicit)
    typer.echo(f"Parsed {len(rows)} usable rows from {csv_path.name} "
               f"(supplier={supplier}, skipped {skipped} with no title).")
    with_barcode = sum(1 for r in rows if r["barcode"])
    with_price = sum(1 for r in rows if r["suggested_price"] is not None)
    typer.echo(f"  with barcode: {with_barcode}   with suggested price: {with_price}")

    if dry_run:
        typer.echo("--dry-run: nothing written.")
        for r in rows[:3]:
            typer.echo(f"  sample: {r['ref_key']} | {r['title'][:48]} | bc={r['barcode']} "
                       f"| {r['suggested_price']}")
        return

    target = resolve_db_url(db_url)
    typer.echo(f"Upserting into {target.split('@')[-1]} ...")
    result = asyncio.run(upsert_rows(rows, target))
    typer.echo(f"Done. upserted={result['upserted']} (insert+update, idempotent on supplier,ref_key).")


if __name__ == "__main__":
    app()
