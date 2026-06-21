#!/usr/bin/env python3
"""
BL-90 — normalize multi-barcode product rows so every single scan resolves.

THE BUG: the Banana CSV import crammed MORE THAN ONE barcode into a single
`products.barcode` field, space-separated (and prod has a few with a \\x1D GS1
control char), e.g.:
    actiTube REGULAR 8mm 10pcs   ->  "4260041939998 4260641140053"
    CTIP Activated Carbon 25 Stk ->  "8719632389316 8715144001609 8719632387732"
When Felix scans ONE clean EAN, the exact-match lookup (barcode == 'EAN1') misses
because the stored value is the joined string -> 404 -> he re-captures the same
item. "Scan once, known forever" breaks.

THE FIX (this script): for every such row, split the field into individual codes,
keep the FIRST clean retail code as the primary `products.barcode`, and move the
REST into the `product_barcodes` alias table (BL-90). After this, lookup resolves
on products.barcode OR product_barcodes, so each individual code scans correctly.

Idempotent: safe to re-run. Aliases are inserted only if that code isn't already a
primary barcode or an existing alias. A row already holding a single clean code is
left untouched.

Targets (staging and prod SHARE one Hetzner DB):
    python scripts/bl90_normalize_barcodes.py --env local
    python scripts/bl90_normalize_barcodes.py --env staging --dry-run
    python scripts/bl90_normalize_barcodes.py --env prod          # writes the live DB

Always run --dry-run first and read the summary.
"""
import argparse
import re
import subprocess
import sys

HETZNER = "root@46.62.138.218"
DB = ["psql", "-U", "helix_user", "-d", "helix_db"]

# A clean retail point-of-sale code: digits only, EAN-8 .. GTIN-14 length.
CLEAN_RETAIL = re.compile(r"^[0-9]{8,14}$")
# Split on any whitespace or control char (covers the space-joined imports and
# the \x1D GS1 group separator seen in prod captures).
SPLIT = re.compile(r"[\s\x00-\x1f]+")


def psql_channel(env, read_only=False):
    """argv that pipes SQL on stdin into the target env's psql."""
    # Writes stop on the first error so an aborted transaction surfaces as a
    # non-zero exit (run() then sys.exits) instead of silently rolling back.
    flags = ["-t", "-A"] if read_only else ["-v", "ON_ERROR_STOP=1"]
    if env == "local":
        return ["docker", "exec", "-i", "postgres", *DB, *flags]
    inner = "docker exec -i postgres " + " ".join(DB + flags)
    return ["ssh", HETZNER, inner]


def run(env, sql, read_only=False):
    r = subprocess.run(psql_channel(env, read_only), input=sql, text=True,
                       capture_output=True)
    if r.returncode != 0:
        sys.exit(f"psql failed ({env}):\n{r.stderr.strip()}")
    return r.stdout.strip()


def fetch_dirty_rows(env):
    """(id, raw_barcode) for every row whose barcode holds >1 code / control chars."""
    sql = (
        "SELECT id::text || '\t' || barcode FROM products "
        "WHERE barcode ~ '\\s' OR barcode ~ '[[:cntrl:]]';"
    )
    out = run(env, sql, read_only=True)
    rows = []
    for line in out.splitlines():
        if "\t" not in line:
            continue
        pid, raw = line.split("\t", 1)
        rows.append((pid.strip(), raw))
    return rows


def fetch_taken_barcodes(env):
    """Every barcode already in use as a primary OR an alias (the uniqueness space).

    We DON'T count the dirty joined strings themselves — they're being replaced —
    but a clean single code already owned by another product is off-limits.
    """
    sql = (
        "SELECT barcode FROM products "
        "WHERE barcode IS NOT NULL AND barcode !~ '\\s' AND barcode !~ '[[:cntrl:]]' "
        "UNION SELECT barcode FROM product_barcodes;"
    )
    out = run(env, sql, read_only=True)
    return {ln.strip() for ln in out.splitlines() if ln.strip()}


def sql_literal(s):
    return "'" + s.replace("'", "''") + "'"


def build_statements(rows, taken):
    """Return (sql_statements, report). report = list of (pid, primary, aliases, skipped).

    `taken` is the set of barcodes already claimed (primary or alias). We claim
    codes against it as we go so two dirty rows can't both grab the same code —
    a code only ever belongs to ONE product (preserves the unique constraint).
    Collisions (a token already owned elsewhere) are skipped, never forced.
    """
    taken = set(taken)
    stmts = []
    report = []
    for pid, raw in rows:
        tokens = [t for t in SPLIT.split(raw) if t]
        clean = [t for t in tokens if CLEAN_RETAIL.match(t)]
        dropped = [t for t in tokens if not CLEAN_RETAIL.match(t)]

        # First FREE clean code becomes the primary; the rest become aliases.
        primary = None
        aliases = []
        for t in clean:
            if t in taken:
                dropped.append(t)            # already owned by another product
                continue
            if primary is None:
                primary = t
            else:
                aliases.append(t)
            taken.add(t)

        if primary is None:
            # No free clean code — leave the row as-is, flag for the operator.
            report.append((pid, None, [], tokens))
            continue

        stmts.append(
            f"UPDATE products SET barcode = {sql_literal(primary)}, updated_at = now() "
            f"WHERE id = {sql_literal(pid)} AND barcode <> {sql_literal(primary)};"
        )
        for a in aliases:
            # Guard the insert too (idempotent + race-safe), though `taken` already
            # guarantees freedom at build time.
            stmts.append(
                "INSERT INTO product_barcodes (id, product_id, barcode, created_at) "
                f"SELECT gen_random_uuid(), {sql_literal(pid)}, {sql_literal(a)}, now() "
                f"WHERE NOT EXISTS (SELECT 1 FROM products WHERE barcode = {sql_literal(a)}) "
                f"AND NOT EXISTS (SELECT 1 FROM product_barcodes WHERE barcode = {sql_literal(a)});"
            )
        report.append((pid, primary, aliases, dropped))
    return stmts, report


def main():
    ap = argparse.ArgumentParser(description="BL-90 multi-barcode normalizer")
    ap.add_argument("--env", choices=["local", "staging", "prod"], required=True)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the SQL + summary, write nothing")
    args = ap.parse_args()

    rows = fetch_dirty_rows(args.env)
    print(f"[{args.env}] {len(rows)} row(s) with multi/dirty barcodes")
    if not rows:
        print("Nothing to normalize. ✓")
        return

    taken = fetch_taken_barcodes(args.env)
    stmts, report = build_statements(rows, taken)
    n_fixed = sum(1 for _, p, _, _ in report if p)
    n_aliases = sum(len(a) for _, _, a, _ in report)
    n_unusable = sum(1 for _, p, _, _ in report if not p)

    # Show a few examples so the operator can eyeball it.
    print(f"\nPlan: normalize {n_fixed} primary codes, add {n_aliases} aliases, "
          f"{n_unusable} row(s) with no clean code (left untouched).")
    print("\nExamples:")
    for pid, primary, aliases, skipped in report[:12]:
        if primary:
            extra = f"  + aliases {aliases}" if aliases else ""
            drop = f"  (ignored {skipped})" if skipped else ""
            print(f"  {pid[:8]}  primary={primary}{extra}{drop}")
        else:
            print(f"  {pid[:8]}  NO CLEAN CODE -> left as-is: {skipped}")

    if args.dry_run:
        print(f"\n--dry-run: {len(stmts)} SQL statement(s) NOT executed.")
        return

    # Wrap in a single transaction.
    script = "BEGIN;\n" + "\n".join(stmts) + "\nCOMMIT;\n"
    run(args.env, script)
    print(f"\n✓ Applied {len(stmts)} statement(s) to {args.env}.")

    # Verify nothing dirty remains.
    left = fetch_dirty_rows(args.env)
    print(f"Verify: {len(left)} dirty row(s) remaining "
          f"({'clean ✓' if not left else 'check the unusable ones above'}).")


if __name__ == "__main__":
    main()
