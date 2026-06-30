#!/usr/bin/env python3
"""Generate the Banco SANDBOX persistent-catalog seed artifact.

The sandbox DB (banco_sandbox) is TRUNCATED nightly by `make sandbox-reset` (the
daily-smoke cron) so every take starts from a clean shop. That wipes the enriched
Artemis demo catalog (the `TAM-*` products + their EN translations) too.

This tool SNAPSHOTS those enriched rows — exactly as they sit in banco_sandbox right
now — into a re-runnable SQL seed (`scripts/sandbox_seed_catalog.sql`). The Makefile's
`sandbox-reset` target re-applies that seed right after the truncate, so the catalog
SURVIVES every reset with NO re-enrichment (no Artemis traffic, no LLM, sub-second).

It runs ON THE BOX (it shells out to the `postgres` Docker container — no Python DB
driver needed). Mechanism: copy the TAM-* rows into two throwaway tables, `pg_dump
--data-only --inserts` them (Postgres does all the type/JSON quoting correctly),
rename the tables back to `products` / `product_translations`, drop the throwaways.
Because the seed is applied straight after a TRUNCATE, the target tables are empty,
so these are plain INSERTs (ids are UUIDs — no sequence/serial fix-ups needed).

USAGE (on the box):
  python3 scripts/ops/gen_sandbox_seed.py
  python3 scripts/ops/gen_sandbox_seed.py --db banco_sandbox --out scripts/sandbox_seed_catalog.sql

Re-run it any time the demo catalog changes (e.g. after loading more products) to
refresh the seed. SAFE: read-only against the real tables (the throwaways are dropped).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone

PG_CONTAINER = "postgres"
PG_USER = "helix_user"
SKU_FILTER = "TAM-%"          # the enriched Artemis catalog namespace
T_PROD = "_seed_products"
T_TR = "_seed_tr"


def _psql(db: str, sql: str) -> str:
    r = subprocess.run(
        ["docker", "exec", "-i", PG_CONTAINER, "psql", "-U", PG_USER, "-d", db,
         "-v", "ON_ERROR_STOP=1", "-At", "-c", sql],
        capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"psql failed: {r.stderr.strip()}")
    return r.stdout.strip()


def _pg_dump(db: str) -> str:
    r = subprocess.run(
        ["docker", "exec", "-i", PG_CONTAINER, "pg_dump", "-U", PG_USER, "-d", db,
         "--data-only", "--inserts", "--no-owner", "--no-privileges",
         "-t", T_PROD, "-t", T_TR],
        capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"pg_dump failed: {r.stderr.strip()}")
    return r.stdout


def main() -> None:
    ap = argparse.ArgumentParser(description="Snapshot the sandbox TAM-* catalog to a reset-survival seed.")
    ap.add_argument("--db", default="banco_sandbox")
    ap.add_argument("--out", default="scripts/sandbox_seed_catalog.sql")
    args = ap.parse_args()

    # 1) build throwaway copies of just the TAM-* products + their translations
    _psql(args.db, f"""
        DROP TABLE IF EXISTS {T_PROD}; DROP TABLE IF EXISTS {T_TR};
        CREATE TABLE {T_PROD} AS SELECT * FROM products WHERE sku LIKE '{SKU_FILTER}';
        CREATE TABLE {T_TR}   AS SELECT t.* FROM product_translations t
              JOIN products p ON p.id = t.product_id WHERE p.sku LIKE '{SKU_FILTER}';
    """)
    n_prod = _psql(args.db, f"SELECT count(*) FROM {T_PROD};")
    n_tr = _psql(args.db, f"SELECT count(*) FROM {T_TR};")

    # 2) dump the throwaways as INSERTs, then 3) rename tables back to the real ones
    dump = _pg_dump(args.db)
    dump = (dump.replace(f"public.{T_PROD}", "public.products")
                .replace(f"public.{T_TR}", "public.product_translations")
                .replace(f" {T_PROD} ", " products ")
                .replace(f" {T_TR} ", " product_translations "))
    # keep only the INSERT lines (drop pg_dump's SET/SELECT pg_catalog noise) so the
    # seed is a clean, idempotent-after-truncate block of inserts.
    inserts = [ln for ln in dump.splitlines() if ln.startswith("INSERT INTO")]

    # 4) drop the throwaways
    _psql(args.db, f"DROP TABLE IF EXISTS {T_PROD}; DROP TABLE IF EXISTS {T_TR};")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = (
        "-- Banco SANDBOX persistent-catalog seed -- AUTO-GENERATED, do not hand-edit.\n"
        f"-- Generated {now} by scripts/ops/gen_sandbox_seed.py from {args.db}.\n"
        f"-- {n_prod} products (sku LIKE '{SKU_FILTER}') + {n_tr} EN translations.\n"
        "--\n"
        "-- Applied by `make sandbox-reset` right AFTER scripts/sandbox_reset.sql truncates,\n"
        "-- so the enriched Artemis demo catalog SURVIVES the nightly sandbox reset with no\n"
        "-- re-enrichment. Target tables are empty at apply time (post-TRUNCATE) -> plain\n"
        "-- INSERTs; all ids are UUIDs so there are no serial/sequence fix-ups.\n"
        "-- Regenerate with: python3 scripts/ops/gen_sandbox_seed.py\n\n"
    )
    out_sql = header + "\n".join(inserts) + "\n"

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(out_sql)
    print(f"wrote {args.out}: {n_prod} products + {n_tr} translations ({len(inserts)} INSERT rows)")


if __name__ == "__main__":
    main()
