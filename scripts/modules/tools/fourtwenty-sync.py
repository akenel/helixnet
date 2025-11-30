#!/usr/bin/env python3
"""
FourTwenty CSV Feed Sync Tool
KB-038: Daily product/stock/specification sync from fourtwenty.ch

Usage:
    python3 fourtwenty-sync.py --test          # Test connectivity and show sample data
    python3 fourtwenty-sync.py --download      # Download all feeds to local files
    python3 fourtwenty-sync.py --analyze       # Analyze feeds and show statistics
    python3 fourtwenty-sync.py --sync          # Full sync to database (future)
"""

import csv
import io
import sys
import argparse
from datetime import datetime
from urllib.request import urlopen
from urllib.error import URLError
from collections import defaultdict

# FourTwenty Feed URLs
FEEDS = {
    'products': 'https://fourtwenty.ch/Dropship/Data/dropship_productfeed_v2.csv',
    'stock': 'https://fourtwenty.ch/Dropship/Data/dropship_stockfeed_v1.csv',
    'specifications': 'https://fourtwenty.ch/Dropship/Data/dropship_specificationfeed_v1.csv'
}

# Output directory (in debllm for user-writable location)
OUTPUT_DIR = '/home/angel/repos/helixnet/debllm/feeds/fourtwenty'


def fetch_csv(url: str, timeout: int = 30) -> list[dict]:
    """Fetch and parse CSV from URL. Auto-detects delimiter."""
    print(f"  Fetching: {url}")
    try:
        with urlopen(url, timeout=timeout) as response:
            content = response.read().decode('utf-8')

            # Auto-detect delimiter by checking first line
            first_line = content.split('\n')[0]
            delimiter = ';' if ';' in first_line and first_line.count(';') > first_line.count(',') else ','

            reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
            rows = list(reader)
            print(f"  ✓ {len(rows):,} rows fetched (delimiter: '{delimiter}')")
            return rows
    except URLError as e:
        print(f"  ✗ Error: {e}")
        return []


def test_connectivity():
    """Test connectivity to all feeds and show sample data."""
    print("\n" + "="*70)
    print("FOURTWENTY CSV FEED CONNECTIVITY TEST")
    print("="*70)

    results = {}

    for feed_name, url in FEEDS.items():
        print(f"\n[{feed_name.upper()}]")
        rows = fetch_csv(url)
        results[feed_name] = len(rows)

        if rows:
            # Filter out None keys
            columns = [k for k in rows[0].keys() if k is not None]
            print(f"  Columns: {', '.join(columns[:10])}{'...' if len(columns) > 10 else ''}")
            print(f"  Sample (first row):")
            for key, value in list(rows[0].items())[:5]:
                if key is not None:
                    val_str = str(value) if value else ''
                    print(f"    {key}: {val_str[:50]}{'...' if len(val_str) > 50 else ''}")

    print("\n" + "-"*70)
    print("SUMMARY")
    print("-"*70)
    for feed_name, count in results.items():
        status = "✓" if count > 0 else "✗"
        print(f"  {status} {feed_name}: {count:,} records")

    return all(count > 0 for count in results.values())


def download_feeds():
    """Download all feeds to local CSV files."""
    import os

    print("\n" + "="*70)
    print("DOWNLOADING FOURTWENTY FEEDS")
    print("="*70)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for feed_name, url in FEEDS.items():
        print(f"\n[{feed_name.upper()}]")
        try:
            with urlopen(url, timeout=60) as response:
                content = response.read()

                # Save with timestamp
                filename = f"{feed_name}_{timestamp}.csv"
                filepath = os.path.join(OUTPUT_DIR, filename)
                with open(filepath, 'wb') as f:
                    f.write(content)
                print(f"  ✓ Saved: {filepath}")
                print(f"    Size: {len(content):,} bytes")

                # Also save as 'latest'
                latest_path = os.path.join(OUTPUT_DIR, f"{feed_name}_latest.csv")
                with open(latest_path, 'wb') as f:
                    f.write(content)
                print(f"  ✓ Updated: {latest_path}")

        except URLError as e:
            print(f"  ✗ Error: {e}")

    print(f"\n✓ All feeds saved to: {OUTPUT_DIR}")


def analyze_feeds():
    """Analyze feeds and show detailed statistics."""
    print("\n" + "="*70)
    print("FOURTWENTY FEED ANALYSIS")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*70)

    # Fetch all feeds
    products = fetch_csv(FEEDS['products'])
    stock = fetch_csv(FEEDS['stock'])
    specs = fetch_csv(FEEDS['specifications'])

    if not products:
        print("\n✗ Could not fetch product feed. Aborting analysis.")
        return

    # Product Analysis
    print("\n" + "-"*70)
    print("PRODUCT CATALOG ANALYSIS")
    print("-"*70)

    # Categories
    categories = defaultdict(int)
    brands = defaultdict(int)
    price_ranges = {'0-10': 0, '10-25': 0, '25-50': 0, '50-100': 0, '100+': 0}

    for p in products:
        cat = p.get('categorygroup_1', 'Unknown')
        categories[cat] += 1

        brand = p.get('brandname', 'Unknown')
        brands[brand] += 1

        try:
            price = float(p.get('salespriceinclvat', 0))
            if price < 10:
                price_ranges['0-10'] += 1
            elif price < 25:
                price_ranges['10-25'] += 1
            elif price < 50:
                price_ranges['25-50'] += 1
            elif price < 100:
                price_ranges['50-100'] += 1
            else:
                price_ranges['100+'] += 1
        except ValueError:
            pass

    print(f"\nTotal Products: {len(products):,}")

    print("\nBy Category:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:10]:
        print(f"  {cat}: {count:,}")

    print(f"\nUnique Brands: {len(brands)}")
    print("Top 10 Brands:")
    for brand, count in sorted(brands.items(), key=lambda x: -x[1])[:10]:
        print(f"  {brand}: {count:,}")

    print("\nPrice Distribution (CHF incl. VAT):")
    for range_name, count in price_ranges.items():
        pct = (count / len(products)) * 100 if products else 0
        bar = "█" * int(pct / 2)
        print(f"  {range_name:>6}: {count:>5,} ({pct:5.1f}%) {bar}")

    # Stock Analysis
    if stock:
        print("\n" + "-"*70)
        print("STOCK ANALYSIS")
        print("-"*70)

        in_stock = sum(1 for s in stock if s.get('is_available', '').upper() == 'TRUE')
        out_of_stock = len(stock) - in_stock

        total_qty = 0
        for s in stock:
            try:
                total_qty += int(s.get('qty', 0))
            except ValueError:
                pass

        print(f"\nTotal SKUs: {len(stock):,}")
        print(f"In Stock: {in_stock:,} ({(in_stock/len(stock)*100):.1f}%)")
        print(f"Out of Stock: {out_of_stock:,} ({(out_of_stock/len(stock)*100):.1f}%)")
        print(f"Total Units: {total_qty:,}")

    # Specification Analysis
    if specs:
        print("\n" + "-"*70)
        print("SPECIFICATION ANALYSIS")
        print("-"*70)

        spec_types = defaultdict(int)
        for s in specs:
            spec_key = s.get('SpecificationKey', 'Unknown')
            spec_types[spec_key] += 1

        print(f"\nTotal Specifications: {len(specs):,}")
        print(f"Unique Spec Types: {len(spec_types)}")
        print("\nTop 15 Specification Types:")
        for spec, count in sorted(spec_types.items(), key=lambda x: -x[1])[:15]:
            print(f"  {spec}: {count:,}")

    # Cross-reference check
    print("\n" + "-"*70)
    print("DATA INTEGRITY CHECK")
    print("-"*70)

    product_skus = {p.get('sku') for p in products}
    stock_skus = {s.get('sku') for s in stock}
    spec_skus = {s.get('ProviderKey') for s in specs}

    products_without_stock = product_skus - stock_skus
    stock_without_products = stock_skus - product_skus

    print(f"\nProducts in catalog: {len(product_skus):,}")
    print(f"SKUs in stock feed: {len(stock_skus):,}")
    print(f"SKUs in spec feed: {len(spec_skus):,}")
    print(f"\n⚠ Products without stock info: {len(products_without_stock)}")
    print(f"⚠ Stock entries without products: {len(stock_without_products)}")

    if products_without_stock and len(products_without_stock) <= 10:
        print(f"  Missing: {', '.join(list(products_without_stock)[:10])}")


def main():
    parser = argparse.ArgumentParser(description='FourTwenty CSV Feed Sync Tool')
    parser.add_argument('--test', action='store_true', help='Test connectivity')
    parser.add_argument('--download', action='store_true', help='Download feeds to local files')
    parser.add_argument('--analyze', action='store_true', help='Analyze feed contents')
    parser.add_argument('--sync', action='store_true', help='Sync to database (not yet implemented)')

    args = parser.parse_args()

    if not any([args.test, args.download, args.analyze, args.sync]):
        # Default: run test
        args.test = True

    if args.test:
        success = test_connectivity()
        sys.exit(0 if success else 1)

    if args.download:
        download_feeds()

    if args.analyze:
        analyze_feeds()

    if args.sync:
        print("\n⚠ Database sync not yet implemented.")
        print("  This will map FourTwenty products to HelixNet products table.")
        print("  See KB-038 for mapping specification.")


if __name__ == '__main__':
    main()
