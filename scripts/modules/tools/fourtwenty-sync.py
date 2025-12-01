#!/usr/bin/env python3
"""
FourTwenty CSV Feed Sync Tool
KB-038: Daily product/stock/specification sync from fourtwenty.ch

Usage:
    python3 fourtwenty-sync.py --test          # Test connectivity
    python3 fourtwenty-sync.py --download      # Download feeds locally
    python3 fourtwenty-sync.py --analyze       # Analyze feed statistics
    python3 fourtwenty-sync.py --sync          # Sync Headshop products to DB
    python3 fourtwenty-sync.py --alerts        # Show price change history
"""

import csv
import io
import os
import sys
import json
import argparse
from datetime import datetime
from urllib.request import urlopen
from urllib.error import URLError
from collections import defaultdict
from decimal import Decimal, InvalidOperation

# Database connection (optional - only needed for --sync)
try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

# =============================================================================
# CONFIGURATION
# =============================================================================

FEEDS = {
    'products': 'https://fourtwenty.ch/Dropship/Data/dropship_productfeed_v2.csv',
    'stock': 'https://fourtwenty.ch/Dropship/Data/dropship_stockfeed_v1.csv',
    'specifications': 'https://fourtwenty.ch/Dropship/Data/dropship_specificationfeed_v1.csv'
}

OUTPUT_DIR = '/home/angel/repos/helixnet/debllm/feeds/fourtwenty'

# Category mapping (FourTwenty → HelixNet)
CATEGORY_MAP = {
    'Headshop': 'Accessories',
    'Vape': 'Vaporizers',
    'Vape Shop': 'Vaporizers',
    'CBD': 'CBD',
    'Liquids Vape ': 'E-Liquids',
    'Themen': 'Themed',
    'Punkteartikel': 'Promotions',
    'Weekly Promotion': 'Promotions',
    'Indoorgrowing': None,  # Skip
}

# Categories to sync (Headshop focus)
HEADSHOP_CATEGORIES = {'Headshop', 'Vape', 'Vape Shop', 'CBD', 'Liquids Vape ', 'Themen', 'Punkteartikel'}

# Default markup
MARKUP = Decimal('1.50')  # 50%

# =============================================================================
# UTILITIES
# =============================================================================

def fetch_csv(url: str, timeout: int = 60) -> list[dict]:
    """Fetch and parse CSV from URL. Auto-detects delimiter."""
    print(f"  Fetching: {url.split('/')[-1]}")
    try:
        with urlopen(url, timeout=timeout) as response:
            content = response.read().decode('utf-8')
            first_line = content.split('\n')[0]
            delimiter = ';' if first_line.count(';') > first_line.count(',') else ','
            reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
            rows = list(reader)
            print(f"  ✓ {len(rows):,} rows (delimiter: '{delimiter}')")
            return rows
    except URLError as e:
        print(f"  ✗ Error: {e}")
        return []


def get_db_connection():
    """Get database connection."""
    if not HAS_PSYCOPG2:
        raise RuntimeError("psycopg2 not installed. Run: pip install psycopg2-binary")

    for host in ['postgres', 'localhost', '127.0.0.1']:
        try:
            conn = psycopg2.connect(
                host=host, port=5432, database='helix_db',
                user='helix_user', password='helix_pass',
                connect_timeout=5
            )
            print(f"  ✓ Connected to DB at {host}")
            return conn
        except psycopg2.OperationalError:
            continue
    raise RuntimeError("Could not connect to database")


def safe_decimal(value: str, default: Decimal = Decimal('0')) -> Decimal:
    """Safely parse decimal from string."""
    try:
        return Decimal(str(value).replace(',', '.').strip())
    except (InvalidOperation, ValueError):
        return default


# =============================================================================
# COMMANDS
# =============================================================================

def test_connectivity():
    """Test feed connectivity."""
    print("\n" + "="*60)
    print("FOURTWENTY FEED TEST")
    print("="*60)

    results = {}
    for name, url in FEEDS.items():
        print(f"\n[{name.upper()}]")
        rows = fetch_csv(url)
        results[name] = len(rows)
        if rows:
            cols = [k for k in rows[0].keys() if k][:5]
            print(f"  Columns: {', '.join(cols)}...")

    print("\n" + "-"*60)
    all_ok = all(c > 0 for c in results.values())
    for name, count in results.items():
        print(f"  {'✓' if count > 0 else '✗'} {name}: {count:,}")
    return all_ok


def download_feeds():
    """Download feeds to local files."""
    print("\n" + "="*60)
    print("DOWNLOADING FEEDS")
    print("="*60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    for name, url in FEEDS.items():
        print(f"\n[{name.upper()}]")
        try:
            with urlopen(url, timeout=60) as r:
                content = r.read()
                # Timestamped
                path = os.path.join(OUTPUT_DIR, f"{name}_{ts}.csv")
                with open(path, 'wb') as f:
                    f.write(content)
                # Latest
                latest = os.path.join(OUTPUT_DIR, f"{name}_latest.csv")
                with open(latest, 'wb') as f:
                    f.write(content)
                print(f"  ✓ {len(content):,} bytes → {name}_latest.csv")
        except URLError as e:
            print(f"  ✗ {e}")


def analyze_feeds():
    """Analyze feed statistics."""
    print("\n" + "="*60)
    print("FEED ANALYSIS")
    print("="*60)

    products = fetch_csv(FEEDS['products'])
    stock = fetch_csv(FEEDS['stock'])
    specs = fetch_csv(FEEDS['specifications'])

    if not products:
        return

    # Categories
    cats = defaultdict(int)
    for p in products:
        cats[p.get('categorygroup_1', 'Unknown')] += 1

    print(f"\nTotal Products: {len(products):,}")
    print("\nBy Category:")
    for cat, count in sorted(cats.items(), key=lambda x: -x[1])[:10]:
        marker = "✓" if cat in HEADSHOP_CATEGORIES else "○"
        print(f"  {marker} {cat}: {count:,}")

    # Stock
    if stock:
        in_stock = sum(1 for s in stock if s.get('is_available', '').upper() == 'TRUE')
        print(f"\nStock: {in_stock:,}/{len(stock):,} in stock ({in_stock/len(stock)*100:.0f}%)")

    # Headshop filter
    headshop_count = sum(1 for p in products if p.get('categorygroup_1', '') in HEADSHOP_CATEGORIES)
    print(f"\nHeadshop Products (to sync): {headshop_count:,}")


def sync_to_database(dry_run: bool = False):
    """Sync FourTwenty products to HelixNet database."""
    print("\n" + "="*60)
    print(f"SYNC TO DATABASE {'(DRY RUN)' if dry_run else ''}")
    print("="*60)

    # Fetch feeds
    print("\n[1] Fetching feeds...")
    products = fetch_csv(FEEDS['products'])
    stock = fetch_csv(FEEDS['stock'])
    specs = fetch_csv(FEEDS['specifications'])

    if not products:
        print("✗ No products fetched")
        return False

    # Build lookups
    print("\n[2] Building lookups...")
    stock_lookup = {s.get('sku'): s for s in stock}
    age_restricted = {s.get('ProviderKey') for s in specs if s.get('SpecificationKey') == 'age_verification'}
    print(f"  Stock entries: {len(stock_lookup):,}")
    print(f"  Age-restricted: {len(age_restricted):,}")

    # Filter to Headshop categories
    print("\n[3] Filtering products...")
    filtered = [p for p in products if p.get('categorygroup_1', '') in HEADSHOP_CATEGORIES]
    print(f"  Headshop products: {len(filtered):,}")

    if dry_run:
        print("\n[DRY RUN] Would sync these products. Use --sync without --dry-run to execute.")
        return True

    # Database sync
    print("\n[4] Syncing to database...")
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get existing supplier products
        cur.execute("SELECT supplier_sku, id, supplier_price FROM products WHERE supplier_name = 'FourTwenty'")
        existing = {row[0]: {'id': row[1], 'price': row[2]} for row in cur.fetchall()}
        print(f"  Existing FourTwenty products: {len(existing):,}")

        # Track used barcodes to avoid duplicates
        cur.execute("SELECT barcode FROM products WHERE barcode IS NOT NULL")
        used_barcodes = {row[0] for row in cur.fetchall()}

        stats = {'new': 0, 'updated': 0, 'skipped': 0, 'price_changes': []}
        now = datetime.now()

        for p in filtered:
            supplier_sku = p.get('sku', '').strip()
            if not supplier_sku:
                stats['skipped'] += 1
                continue

            # Parse data
            supplier_price = safe_decimal(p.get('salespriceinclvat', '0'))
            retail_price = supplier_price * MARKUP
            name = (p.get('producttitle_de', '') or '')[:255]
            barcode = (p.get('gtin', '') or '')[:100] or None
            category = CATEGORY_MAP.get(p.get('categorygroup_1', ''), 'Other')
            image_url = (p.get('mainimageurl', '') or '')[:500] or None
            is_age_restricted = supplier_sku in age_restricted

            # Skip duplicate barcodes
            if barcode and barcode in used_barcodes:
                barcode = None

            if supplier_sku in existing:
                # Update existing
                ex = existing[supplier_sku]
                if ex['price'] and supplier_price != ex['price']:
                    change_pct = float((supplier_price - ex['price']) / ex['price'] * 100)
                    stats['price_changes'].append({
                        'sku': supplier_sku,
                        'name': name[:40],
                        'old': float(ex['price']),
                        'new': float(supplier_price),
                        'pct': change_pct
                    })

                cur.execute("""
                    UPDATE products SET
                        supplier_price = %s, price = %s, cost = %s,
                        last_sync_at = %s, updated_at = %s,
                        image_url = COALESCE(image_url, %s)
                    WHERE id = %s AND (sync_override IS NULL OR sync_override = FALSE)
                """, (supplier_price, retail_price, supplier_price, now, now, image_url, ex['id']))
                stats['updated'] += 1
            else:
                # Insert new
                internal_sku = f"FT-{supplier_sku}"
                cur.execute("""
                    INSERT INTO products (
                        id, sku, barcode, name, price, cost, category,
                        supplier_sku, supplier_name, supplier_price, last_sync_at,
                        image_url, is_age_restricted, is_active, stock_quantity,
                        vending_compatible, sync_override, created_at, updated_at
                    ) VALUES (
                        gen_random_uuid(), %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (sku) DO NOTHING
                """, (
                    internal_sku, barcode, name, retail_price, supplier_price, category,
                    supplier_sku, 'FourTwenty', supplier_price, now,
                    image_url, is_age_restricted, True, 0,
                    False, False, now, now
                ))
                stats['new'] += 1
                if barcode:
                    used_barcodes.add(barcode)

        conn.commit()
        cur.close()
        conn.close()

        # Results
        print("\n" + "-"*60)
        print("RESULTS")
        print("-"*60)
        print(f"  ✓ New products: {stats['new']:,}")
        print(f"  ✓ Updated: {stats['updated']:,}")
        print(f"  ○ Skipped: {stats['skipped']:,}")

        if stats['price_changes']:
            print(f"\n  📊 Price changes: {len(stats['price_changes'])}")
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            changes_file = os.path.join(OUTPUT_DIR, f"price_changes_{now.strftime('%Y%m%d_%H%M%S')}.json")
            with open(changes_file, 'w') as f:
                json.dump(stats['price_changes'], f, indent=2)
            print(f"  Saved: {changes_file}")

            # Show significant changes
            significant = [c for c in stats['price_changes'] if abs(c['pct']) > 5]
            if significant:
                print("\n  Significant (>5%):")
                for c in significant[:5]:
                    d = "↑" if c['pct'] > 0 else "↓"
                    print(f"    {d} {c['sku']}: {c['old']:.2f} → {c['new']:.2f} ({c['pct']:+.1f}%)")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_alerts():
    """Show price change history."""
    print("\n" + "="*60)
    print("PRICE CHANGE ALERTS")
    print("="*60)

    if not os.path.exists(OUTPUT_DIR):
        print("  No history found.")
        return

    files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.startswith('price_changes_')], reverse=True)
    if not files:
        print("  No price changes recorded yet.")
        return

    for f in files[:5]:
        with open(os.path.join(OUTPUT_DIR, f)) as fp:
            changes = json.load(fp)
        date = f.replace('price_changes_', '').replace('.json', '')
        print(f"\n[{date}] {len(changes)} changes")
        for c in sorted(changes, key=lambda x: abs(x['pct']), reverse=True)[:3]:
            d = "↑" if c['pct'] > 0 else "↓"
            print(f"  {d} {c['sku']}: CHF {c['old']:.2f} → {c['new']:.2f} ({c['pct']:+.1f}%)")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='FourTwenty CSV Sync Tool')
    parser.add_argument('--test', action='store_true', help='Test feed connectivity')
    parser.add_argument('--download', action='store_true', help='Download feeds locally')
    parser.add_argument('--analyze', action='store_true', help='Analyze feeds')
    parser.add_argument('--sync', action='store_true', help='Sync to database')
    parser.add_argument('--dry-run', action='store_true', help='Preview sync')
    parser.add_argument('--alerts', action='store_true', help='Show price alerts')

    args = parser.parse_args()

    if not any([args.test, args.download, args.analyze, args.sync, args.alerts]):
        args.test = True

    if args.test:
        sys.exit(0 if test_connectivity() else 1)
    if args.download:
        download_feeds()
    if args.analyze:
        analyze_feeds()
    if args.sync:
        sys.exit(0 if sync_to_database(dry_run=args.dry_run) else 1)
    if args.alerts:
        show_alerts()


if __name__ == '__main__':
    main()
