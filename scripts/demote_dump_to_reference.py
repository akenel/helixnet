#!/usr/bin/env python3
"""
BL-97b — Demote the bulk supplier dump from the LIVE catalog to the REFERENCE catalog.

The 420/FourTwenty CSV import seeded thousands of rows straight into `products` (the live
catalog). That makes "what's in my store" dishonest — it lists items Felix may never stock.
This moves the untouched dump rows OUT of `products` and INTO `reference_products`, so the
live catalog means "what Felix actually sells" and the dump becomes the lookup the POS
cherry-picks from (BL-97). When a demoted item is next scanned/searched it re-adopts back in.

SAFE BY DEFAULT — dry-run unless --apply. REVERSIBLE — each row is copied into reference_products
FIRST, then the product is deleted; re-adopt restores it. Only ever touches dump rows that are
UNTOUCHED:
  - supplier_name = 'FourTwenty' (or sku LIKE 'FT-%')      -- from the bulk import
  - never sold (no line_items)                              -- keep all sales history intact
  - no alias barcode (product_barcodes)                     -- an alias = someone curated it
  - category <> 'On the fly'                                -- not cashier-created
Sold / curated / hand-added items STAY in the live catalog. FK surprises (e.g. a received item
with stock movements) are caught per-row and SKIPPED, not forced.

Connection: like the importer — runs in the app container on the box (postgres resolves there);
DB URL from --db-url / $REFERENCE_DB_URL / POSTGRES_*. Shared helix_db = staging + banco-prod, so
--apply there changes the LIVE prod catalog: run --dry-run, eyeball the counts, then --apply.

Usage:
  python scripts/demote_dump_to_reference.py            # dry-run: counts + samples
  python scripts/demote_dump_to_reference.py --apply    # actually move them
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(add_completion=False, help="Demote the bulk supplier dump to the reference catalog — BL-97b")

CANDIDATE_WHERE = """
    (p.supplier_name = 'FourTwenty' OR p.sku LIKE 'FT-%')
    AND NOT EXISTS (SELECT 1 FROM line_items li WHERE li.product_id = p.id)
    AND NOT EXISTS (SELECT 1 FROM product_barcodes pb WHERE pb.product_id = p.id)
    AND COALESCE(p.category, '') <> 'On the fly'
"""


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


async def _run(db_url: str, apply: bool, limit: Optional[int]) -> dict:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from src.db.models.reference_product_model import ReferenceProductModel
    from src.db.models.product_model import ProductModel

    engine = create_async_engine(db_url)
    moved, skipped, samples = 0, 0, []
    try:
        # Snapshot before/after live counts so the report is honest.
        async with engine.connect() as conn:
            total = (await conn.execute(text(
                f"SELECT count(*) FROM products p WHERE {CANDIDATE_WHERE}"))).scalar() or 0
            live_before = (await conn.execute(text("SELECT count(*) FROM products"))).scalar() or 0
            sample_rows = (await conn.execute(text(
                f"SELECT p.sku, p.name, p.barcode, p.price FROM products p "
                f"WHERE {CANDIDATE_WHERE} ORDER BY p.name LIMIT 5"))).fetchall()
            samples = [f"{r.sku} | {(r.name or '')[:40]} | bc={r.barcode} | {r.price}" for r in sample_rows]

        if not apply:
            return {"candidates": total, "live_before": live_before, "moved": 0,
                    "skipped": 0, "samples": samples, "applied": False}

        # Apply: page through candidates, copy → reference, delete product, per-row safe.
        async with engine.connect() as conn:
            rows = (await conn.execute(text(f"""
                SELECT p.id, p.sku, p.barcode, p.name, p.description, p.image_url,
                       p.category, p.price, p.cost
                FROM products p WHERE {CANDIDATE_WHERE}
                {('LIMIT ' + str(limit)) if limit else ''}
            """))).fetchall()

        for r in rows:
            async with engine.begin() as tx:
                try:
                    ins = pg_insert(ReferenceProductModel).values(
                        supplier="FourTwenty", ref_key=(r.sku or str(r.id))[:150],
                        supplier_sku=r.sku, barcode=r.barcode, title=(r.name or "")[:255],
                        description=r.description, image_url=(r.image_url or None),
                        category=r.category, suggested_price=r.price, cost=r.cost,
                    ).on_conflict_do_update(
                        constraint="uq_reference_products_supplier_refkey",
                        set_={"barcode": r.barcode, "title": (r.name or "")[:255],
                              "description": r.description, "image_url": (r.image_url or None),
                              "category": r.category, "suggested_price": r.price, "cost": r.cost},
                    )
                    await tx.execute(ins)
                    await tx.execute(text("DELETE FROM products WHERE id = :id"), {"id": r.id})
                    moved += 1
                except Exception as e:
                    skipped += 1
                    if skipped <= 5:
                        typer.echo(f"  skip {r.sku}: {type(e).__name__}: {str(e)[:80]}")
        async with engine.connect() as conn:
            live_after = (await conn.execute(text("SELECT count(*) FROM products"))).scalar() or 0
    finally:
        await engine.dispose()
    return {"candidates": total, "live_before": live_before, "live_after": live_after,
            "moved": moved, "skipped": skipped, "samples": samples, "applied": True}


@app.command()
def demote(
    apply: bool = typer.Option(False, "--apply", help="Actually move them (default is dry-run)"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Cap rows moved (testing)"),
    db_url: Optional[str] = typer.Option(None, "--db-url", help="SQLAlchemy async URL (overrides env)"),
):
    """Demote untouched FourTwenty dump rows from products -> reference_products."""
    target = resolve_db_url(db_url)
    res = asyncio.run(_run(target, apply, limit))
    typer.echo(f"\nDB: {target.split('@')[-1]}")
    typer.echo(f"Candidates (FourTwenty, unsold, uncurated): {res['candidates']}")
    typer.echo(f"Live catalog size before: {res['live_before']}")
    if res["samples"]:
        typer.echo("Sample of what would move:")
        for s in res["samples"]:
            typer.echo(f"  {s}")
    if res["applied"]:
        typer.echo(f"\nAPPLIED: moved={res['moved']} skipped={res['skipped']} "
                   f"(FK-touched, left in place)")
        typer.echo(f"Live catalog size after: {res['live_after']}")
    else:
        typer.echo("\n--dry-run: nothing moved. Re-run with --apply to move them.")


if __name__ == "__main__":
    app()
