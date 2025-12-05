#!/usr/bin/env python3
"""
🎬 THE PLAY: Felix's Delivery Check-In
=====================================

THE SCENE (Before Helix):
- 3 suppliers: Near Dark (DE), 420 (CH), Aldi Run (emergency)
- 4 pages, 100+ line items
- Pam gone home sick
- Felix alone at closing
- 30 minute email search for each order
- 4+ hours to verify everything
- Mahnung arrives at midnight
- Felix works till morning

THE SCENE (With Helix):
- Same 3 deliveries
- Dashboard shows all expected
- Scan/check each item: OK, SHORT, MISSING, WRONG
- Total time: ~15 minutes
- Issues flagged instantly: needs_mahnung = True
- Felix goes HOME

Run this play:
    python -m src.tests.delivery_checkin_play

🦁🐅 Built at the crossroads.
"""

import json
from datetime import datetime, timedelta
from uuid import uuid4
from enum import Enum

# ================================================================
# THE SUPPLIERS
# ================================================================

SUPPLIERS = {
    "near_dark": {
        "id": str(uuid4()),
        "name": "Near Dark GmbH",
        "code": "ND",
        "country": "Germany",
        "type": "cbd",
        "contact": "Klaus",
        "email": "orders@neardark.de",
        "lead_time_days": 5,
        "payment_terms": "30 days net",
    },
    "420": {
        "id": str(uuid4()),
        "name": "420 Wholesale CH",
        "code": "420",
        "country": "Switzerland",
        "type": "cbd",
        "contact": "Marco",
        "email": "supply@420ch.ch",
        "lead_time_days": 2,
        "payment_terms": "14 days net",
    },
    "aldi_run": {
        "id": str(uuid4()),
        "name": "Aldi (Emergency Run)",
        "code": "ALDI",
        "country": "Switzerland",
        "type": "general",
        "contact": "Felix himself",
        "email": None,
        "lead_time_days": 0,
        "payment_terms": "cash",
    },
}

# ================================================================
# THE DELIVERIES (4 Pages, 100+ Items)
# ================================================================

def create_near_dark_delivery():
    """
    PAGE 1-2: Near Dark (Germany) - CBD Products
    35 line items - the big monthly order
    """
    return {
        "id": str(uuid4()),
        "supplier": SUPPLIERS["near_dark"],
        "order_reference": "ND-2024-1205",
        "order_date": "2024-11-28",
        "expected_date": "2024-12-05",
        "status": "arrived",
        "pages": 2,
        "items": [
            # CBD Oils
            {"sku": "ND-OIL-5", "name": "CBD Oil 5%", "qty_ordered": 20, "unit_cost": 15.00, "category": "oils"},
            {"sku": "ND-OIL-10", "name": "CBD Oil 10%", "qty_ordered": 15, "unit_cost": 25.00, "category": "oils"},
            {"sku": "ND-OIL-20", "name": "CBD Oil 20%", "qty_ordered": 10, "unit_cost": 45.00, "category": "oils"},
            {"sku": "ND-OIL-PET", "name": "CBD Oil for Pets", "qty_ordered": 8, "unit_cost": 18.00, "category": "oils"},

            # CBD Flowers
            {"sku": "ND-FLW-OG", "name": "OG Kush CBD", "qty_ordered": 500, "unit_cost": 0.80, "category": "flowers"},  # grams
            {"sku": "ND-FLW-HZ", "name": "Haze CBD", "qty_ordered": 500, "unit_cost": 0.75, "category": "flowers"},
            {"sku": "ND-FLW-WW", "name": "White Widow CBD", "qty_ordered": 300, "unit_cost": 0.85, "category": "flowers"},
            {"sku": "ND-FLW-AK", "name": "AK-47 CBD", "qty_ordered": 200, "unit_cost": 0.90, "category": "flowers"},
            {"sku": "ND-FLW-BB", "name": "Blueberry CBD", "qty_ordered": 250, "unit_cost": 0.82, "category": "flowers"},

            # Edibles
            {"sku": "ND-GUM-MIX", "name": "CBD Gummies Mixed", "qty_ordered": 30, "unit_cost": 8.00, "category": "edibles"},
            {"sku": "ND-GUM-SUR", "name": "CBD Gummies Sour", "qty_ordered": 20, "unit_cost": 8.50, "category": "edibles"},
            {"sku": "ND-CHOC-DK", "name": "CBD Dark Chocolate", "qty_ordered": 25, "unit_cost": 6.00, "category": "edibles"},
            {"sku": "ND-CHOC-MLK", "name": "CBD Milk Chocolate", "qty_ordered": 25, "unit_cost": 6.00, "category": "edibles"},
            {"sku": "ND-HONEY", "name": "CBD Honey 250g", "qty_ordered": 12, "unit_cost": 12.00, "category": "edibles"},

            # Vapes
            {"sku": "ND-VAPE-MNT", "name": "CBD Vape Mint", "qty_ordered": 15, "unit_cost": 18.00, "category": "vapes"},
            {"sku": "ND-VAPE-MNG", "name": "CBD Vape Mango", "qty_ordered": 15, "unit_cost": 18.00, "category": "vapes"},
            {"sku": "ND-VAPE-OG", "name": "CBD Vape OG Kush", "qty_ordered": 20, "unit_cost": 18.00, "category": "vapes"},
            {"sku": "ND-CART-5PK", "name": "Vape Cartridge 5-Pack", "qty_ordered": 10, "unit_cost": 35.00, "category": "vapes"},

            # Cosmetics
            {"sku": "ND-CRM-FACE", "name": "CBD Face Cream", "qty_ordered": 15, "unit_cost": 22.00, "category": "cosmetics"},
            {"sku": "ND-CRM-BODY", "name": "CBD Body Lotion", "qty_ordered": 12, "unit_cost": 18.00, "category": "cosmetics"},
            {"sku": "ND-BALM-LIP", "name": "CBD Lip Balm", "qty_ordered": 30, "unit_cost": 4.50, "category": "cosmetics"},
            {"sku": "ND-BALM-MSC", "name": "CBD Muscle Balm", "qty_ordered": 20, "unit_cost": 16.00, "category": "cosmetics"},

            # Accessories
            {"sku": "ND-PIPE-GL", "name": "Glass Pipe Small", "qty_ordered": 10, "unit_cost": 8.00, "category": "accessories"},
            {"sku": "ND-PIPE-WD", "name": "Wood Pipe", "qty_ordered": 8, "unit_cost": 12.00, "category": "accessories"},
            {"sku": "ND-GRIND-SM", "name": "Grinder Small", "qty_ordered": 15, "unit_cost": 6.00, "category": "accessories"},
            {"sku": "ND-GRIND-LG", "name": "Grinder Large", "qty_ordered": 10, "unit_cost": 10.00, "category": "accessories"},
            {"sku": "ND-PAPER-RAW", "name": "RAW Papers King", "qty_ordered": 50, "unit_cost": 2.00, "category": "accessories"},
            {"sku": "ND-PAPER-OCB", "name": "OCB Slim", "qty_ordered": 50, "unit_cost": 1.80, "category": "accessories"},
            {"sku": "ND-FILTER-TIP", "name": "Filter Tips 50pk", "qty_ordered": 30, "unit_cost": 1.50, "category": "accessories"},

            # Tea & Drinks
            {"sku": "ND-TEA-RELAX", "name": "CBD Tea Relax", "qty_ordered": 20, "unit_cost": 7.00, "category": "drinks"},
            {"sku": "ND-TEA-SLEEP", "name": "CBD Tea Sleep", "qty_ordered": 15, "unit_cost": 7.50, "category": "drinks"},
            {"sku": "ND-DRINK-CALM", "name": "CBD Calm Drink 6pk", "qty_ordered": 10, "unit_cost": 15.00, "category": "drinks"},

            # New items this order
            {"sku": "ND-NEW-SPRAY", "name": "CBD Oral Spray (NEW)", "qty_ordered": 12, "unit_cost": 20.00, "category": "oils"},
            {"sku": "ND-NEW-PATCH", "name": "CBD Patches 5pk (NEW)", "qty_ordered": 15, "unit_cost": 25.00, "category": "cosmetics"},
        ],
        "total_value": 0,  # calculated
    }


def create_420_delivery():
    """
    PAGE 3: 420 Wholesale - Swiss CBD + Headshop
    25 line items
    """
    return {
        "id": str(uuid4()),
        "supplier": SUPPLIERS["420"],
        "order_reference": "420-CH-8834",
        "order_date": "2024-12-01",
        "expected_date": "2024-12-05",
        "status": "arrived",
        "pages": 1,
        "items": [
            # Swiss CBD (higher quality, higher price)
            {"sku": "420-OIL-SWISS10", "name": "Swiss CBD Oil 10%", "qty_ordered": 10, "unit_cost": 35.00, "category": "oils"},
            {"sku": "420-OIL-SWISS20", "name": "Swiss CBD Oil 20%", "qty_ordered": 8, "unit_cost": 55.00, "category": "oils"},
            {"sku": "420-FLW-ALPEN", "name": "Alpenkraut CBD", "qty_ordered": 200, "unit_cost": 1.20, "category": "flowers"},
            {"sku": "420-FLW-SWISS", "name": "Swiss Dream CBD", "qty_ordered": 150, "unit_cost": 1.30, "category": "flowers"},
            {"sku": "420-HASH-BLK", "name": "CBD Hash Black", "qty_ordered": 100, "unit_cost": 2.50, "category": "hash"},
            {"sku": "420-HASH-BLD", "name": "CBD Hash Blond", "qty_ordered": 100, "unit_cost": 2.80, "category": "hash"},

            # Headshop items
            {"sku": "420-BONG-SM", "name": "Bong Small 20cm", "qty_ordered": 5, "unit_cost": 25.00, "category": "glass"},
            {"sku": "420-BONG-MD", "name": "Bong Medium 30cm", "qty_ordered": 3, "unit_cost": 45.00, "category": "glass"},
            {"sku": "420-BONG-LG", "name": "Bong Large 40cm", "qty_ordered": 2, "unit_cost": 75.00, "category": "glass"},
            {"sku": "420-PIPE-SHER", "name": "Sherlock Pipe", "qty_ordered": 6, "unit_cost": 15.00, "category": "glass"},
            {"sku": "420-PIPE-SPOON", "name": "Spoon Pipe", "qty_ordered": 10, "unit_cost": 10.00, "category": "glass"},
            {"sku": "420-LIGHT-CLIP", "name": "Clipper Lighter 4pk", "qty_ordered": 20, "unit_cost": 6.00, "category": "accessories"},
            {"sku": "420-LIGHT-ZIPPO", "name": "Zippo Style", "qty_ordered": 10, "unit_cost": 12.00, "category": "accessories"},
            {"sku": "420-FLINT-ZIPPO", "name": "Zippo Flints 6pk", "qty_ordered": 30, "unit_cost": 3.00, "category": "accessories"},
            {"sku": "420-WICK-ZIPPO", "name": "Zippo Wicks 3pk", "qty_ordered": 20, "unit_cost": 4.00, "category": "accessories"},
            {"sku": "420-TRAY-SM", "name": "Rolling Tray Small", "qty_ordered": 10, "unit_cost": 8.00, "category": "accessories"},
            {"sku": "420-TRAY-LG", "name": "Rolling Tray Large", "qty_ordered": 6, "unit_cost": 15.00, "category": "accessories"},
            {"sku": "420-SCALE-001", "name": "Digital Scale 0.01g", "qty_ordered": 5, "unit_cost": 20.00, "category": "accessories"},
            {"sku": "420-STASH-SM", "name": "Stash Jar Small", "qty_ordered": 15, "unit_cost": 5.00, "category": "accessories"},
            {"sku": "420-STASH-LG", "name": "Stash Jar Large", "qty_ordered": 10, "unit_cost": 8.00, "category": "accessories"},

            # Clothing
            {"sku": "420-SHIRT-M", "name": "420 T-Shirt M", "qty_ordered": 5, "unit_cost": 15.00, "category": "clothing"},
            {"sku": "420-SHIRT-L", "name": "420 T-Shirt L", "qty_ordered": 5, "unit_cost": 15.00, "category": "clothing"},
            {"sku": "420-SHIRT-XL", "name": "420 T-Shirt XL", "qty_ordered": 3, "unit_cost": 15.00, "category": "clothing"},
            {"sku": "420-CAP-BLK", "name": "420 Cap Black", "qty_ordered": 8, "unit_cost": 12.00, "category": "clothing"},
            {"sku": "420-SOCK-LEAF", "name": "Leaf Socks Pair", "qty_ordered": 12, "unit_cost": 6.00, "category": "clothing"},
        ],
        "total_value": 0,
    }


def create_aldi_delivery():
    """
    PAGE 4: Emergency Aldi Run - Café supplies
    15 line items - Felix's emergency run
    """
    return {
        "id": str(uuid4()),
        "supplier": SUPPLIERS["aldi_run"],
        "order_reference": "ALDI-FELIX-1205",
        "order_date": "2024-12-05",
        "expected_date": "2024-12-05",
        "status": "arrived",
        "pages": 1,
        "items": [
            # Coffee & Drinks
            {"sku": "ALDI-COFFEE-1KG", "name": "Coffee Beans 1kg", "qty_ordered": 3, "unit_cost": 12.00, "category": "cafe"},
            {"sku": "ALDI-MILK-1L", "name": "Oat Milk 1L", "qty_ordered": 12, "unit_cost": 2.50, "category": "cafe"},
            {"sku": "ALDI-SUGAR-1KG", "name": "Sugar 1kg", "qty_ordered": 2, "unit_cost": 1.50, "category": "cafe"},
            {"sku": "ALDI-TEA-BOX", "name": "Tea Variety Box", "qty_ordered": 3, "unit_cost": 4.00, "category": "cafe"},
            {"sku": "ALDI-WATER-6PK", "name": "Water 6x1.5L", "qty_ordered": 4, "unit_cost": 3.00, "category": "cafe"},
            {"sku": "ALDI-JUICE-ORG", "name": "Orange Juice 1L", "qty_ordered": 6, "unit_cost": 2.80, "category": "cafe"},

            # Snacks
            {"sku": "ALDI-CHIPS-MIX", "name": "Chips Variety 6pk", "qty_ordered": 4, "unit_cost": 5.00, "category": "snacks"},
            {"sku": "ALDI-NUTS-MIX", "name": "Mixed Nuts 500g", "qty_ordered": 3, "unit_cost": 6.00, "category": "snacks"},
            {"sku": "ALDI-CHOC-BAR", "name": "Chocolate Bars 10pk", "qty_ordered": 2, "unit_cost": 8.00, "category": "snacks"},
            {"sku": "ALDI-COOKIE-PKT", "name": "Cookies Pack", "qty_ordered": 4, "unit_cost": 3.50, "category": "snacks"},

            # Cleaning
            {"sku": "ALDI-CLEAN-SPRAY", "name": "Surface Cleaner", "qty_ordered": 2, "unit_cost": 3.00, "category": "cleaning"},
            {"sku": "ALDI-PAPER-ROLL", "name": "Paper Towels 4pk", "qty_ordered": 2, "unit_cost": 4.00, "category": "cleaning"},
            {"sku": "ALDI-TRASH-BAG", "name": "Trash Bags 50pk", "qty_ordered": 1, "unit_cost": 5.00, "category": "cleaning"},

            # Emergency
            {"sku": "ALDI-LIGHT-BULB", "name": "Light Bulbs 3pk", "qty_ordered": 1, "unit_cost": 6.00, "category": "emergency"},
            {"sku": "ALDI-BATTERY-AA", "name": "AA Batteries 8pk", "qty_ordered": 2, "unit_cost": 5.00, "category": "emergency"},
        ],
        "total_value": 0,
    }


# ================================================================
# THE CHECK-IN SIMULATION
# ================================================================

def calculate_totals(delivery):
    """Calculate total value for delivery"""
    total = sum(item["qty_ordered"] * item["unit_cost"] for item in delivery["items"])
    delivery["total_value"] = total
    return delivery


def simulate_real_delivery(delivery, issues=None):
    """
    Simulate what ACTUALLY arrived vs what was ordered.
    issues: dict of sku -> {qty_received, status, notes}
    """
    if issues is None:
        issues = {}

    checked_items = []
    for item in delivery["items"]:
        sku = item["sku"]
        if sku in issues:
            issue = issues[sku]
            checked_items.append({
                **item,
                "qty_received": issue.get("qty_received", item["qty_ordered"]),
                "status": issue.get("status", "ok"),
                "notes": issue.get("notes", ""),
            })
        else:
            checked_items.append({
                **item,
                "qty_received": item["qty_ordered"],
                "status": "ok",
                "notes": "",
            })

    delivery["checked_items"] = checked_items
    return delivery


def print_delivery_check(delivery, title):
    """Print delivery check results"""
    print(f"\n{'='*60}")
    print(f"📦 {title}")
    print(f"{'='*60}")
    print(f"Supplier: {delivery['supplier']['name']}")
    print(f"Order Ref: {delivery['order_reference']}")
    print(f"Total Items: {len(delivery['items'])}")
    print(f"Total Value: CHF {delivery['total_value']:.2f}")
    print(f"\n{'─'*60}")

    ok_count = 0
    short_count = 0
    missing_count = 0
    wrong_count = 0

    issues_list = []

    for item in delivery.get("checked_items", delivery["items"]):
        status = item.get("status", "ok")
        qty_ord = item["qty_ordered"]
        qty_rec = item.get("qty_received", qty_ord)

        if status == "ok":
            ok_count += 1
            icon = "✅"
        elif status == "short":
            short_count += 1
            icon = "⚠️"
            issues_list.append(f"  SHORT: {item['name']} - ordered {qty_ord}, got {qty_rec}")
        elif status == "missing":
            missing_count += 1
            icon = "🚫"
            issues_list.append(f"  MISSING: {item['name']} - ordered {qty_ord}, got 0")
        elif status == "wrong":
            wrong_count += 1
            icon = "❌"
            issues_list.append(f"  WRONG: {item['name']} - {item.get('notes', 'wrong item')}")
        elif status == "damaged":
            wrong_count += 1
            icon = "💥"
            issues_list.append(f"  DAMAGED: {item['name']} - {item.get('notes', 'damaged')}")
        else:
            ok_count += 1
            icon = "✅"

    print(f"\n📊 CHECK RESULTS:")
    print(f"   ✅ OK:      {ok_count}")
    print(f"   ⚠️ Short:   {short_count}")
    print(f"   🚫 Missing: {missing_count}")
    print(f"   ❌ Wrong:   {wrong_count}")

    needs_mahnung = (short_count + missing_count + wrong_count) > 0

    if needs_mahnung:
        print(f"\n🚨 NEEDS MAHNUNG: YES")
        print(f"\n📝 ISSUES TO REPORT:")
        for issue in issues_list:
            print(issue)
    else:
        print(f"\n✅ NEEDS MAHNUNG: NO - All good!")

    return {
        "ok": ok_count,
        "short": short_count,
        "missing": missing_count,
        "wrong": wrong_count,
        "needs_mahnung": needs_mahnung,
    }


def print_time_comparison():
    """Show the time saved"""
    print(f"\n{'='*60}")
    print(f"⏱️  TIME COMPARISON")
    print(f"{'='*60}")

    print(f"""
┌─────────────────────────────────────────────────────────┐
│  WITHOUT HELIX (Felix's Old Night)                      │
├─────────────────────────────────────────────────────────┤
│  📧 Search email for Near Dark order:     30 min        │
│  📧 Search email for 420 order:           25 min        │
│  📧 Search email for Aldi receipt:        10 min        │
│  📝 Manual count Near Dark (35 items):    45 min        │
│  📝 Manual count 420 (25 items):          30 min        │
│  📝 Manual count Aldi (15 items):         15 min        │
│  🔍 Find discrepancies:                   30 min        │
│  📞 Call supplier about issues:           20 min        │
│  📄 Write Mahnung email:                  30 min        │
│  😰 Stress, mistakes, re-counting:        45 min        │
├─────────────────────────────────────────────────────────┤
│  TOTAL:                                   4h 40min      │
│  Felix goes home:                         MIDNIGHT      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  WITH HELIX (Felix's New Way)                           │
├─────────────────────────────────────────────────────────┤
│  📱 Open Delivery Dashboard:              10 sec        │
│  📦 Start Check-In Near Dark:             5 min         │
│  📦 Start Check-In 420:                   4 min         │
│  📦 Start Check-In Aldi:                  2 min         │
│  ✅ Auto-flag issues:                     0 sec         │
│  📧 Auto-generate Mahnung:                1 min         │
│  ✅ Accept & Update Inventory:            30 sec        │
├─────────────────────────────────────────────────────────┤
│  TOTAL:                                   ~13 min       │
│  Felix goes home:                         ON TIME       │
└─────────────────────────────────────────────────────────┘

    ⏱️  TIME SAVED: 4 hours 27 minutes
    😊 STRESS SAVED: Priceless
    🏠 Felix goes HOME
""")


def run_the_play():
    """
    🎬 THE PLAY: Run the full simulation
    """
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  🎬 THE PLAY: Felix's Delivery Check-In                      ║
║                                                              ║
║  "Like Honey" 🍯                                             ║
║                                                              ║
║  Built by LEO 🦁 and TONY 🐅 at the crossroads               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Create the deliveries
    near_dark = calculate_totals(create_near_dark_delivery())
    four20 = calculate_totals(create_420_delivery())
    aldi = calculate_totals(create_aldi_delivery())

    # Simulate REAL delivery with some issues
    near_dark_issues = {
        "ND-OIL-10": {"qty_received": 12, "status": "short", "notes": "3 missing"},
        "ND-FLW-WW": {"qty_received": 250, "status": "short", "notes": "50g short"},
        "ND-NEW-PATCH": {"qty_received": 0, "status": "missing", "notes": "Not in box"},
        "ND-VAPE-MNT": {"qty_received": 15, "status": "wrong", "notes": "Sent Strawberry instead"},
    }

    four20_issues = {
        "420-BONG-LG": {"qty_received": 1, "status": "damaged", "notes": "1 broken in shipping"},
        "420-FLINT-ZIPPO": {"qty_received": 25, "status": "short", "notes": "5 packs missing"},
    }

    aldi_issues = {}  # Felix's run - all correct

    # Run checks
    near_dark = simulate_real_delivery(near_dark, near_dark_issues)
    four20 = simulate_real_delivery(four20, four20_issues)
    aldi = simulate_real_delivery(aldi, aldi_issues)

    # Print results
    nd_result = print_delivery_check(near_dark, "NEAR DARK (Germany) - Pages 1-2")
    f20_result = print_delivery_check(four20, "420 WHOLESALE (Switzerland) - Page 3")
    aldi_result = print_delivery_check(aldi, "ALDI RUN (Emergency) - Page 4")

    # Summary
    print(f"\n{'='*60}")
    print(f"📊 DELIVERY DASHBOARD - ALL SUPPLIERS")
    print(f"{'='*60}")

    total_items = len(near_dark["items"]) + len(four20["items"]) + len(aldi["items"])
    total_ok = nd_result["ok"] + f20_result["ok"] + aldi_result["ok"]
    total_issues = (nd_result["short"] + nd_result["missing"] + nd_result["wrong"] +
                   f20_result["short"] + f20_result["missing"] + f20_result["wrong"] +
                   aldi_result["short"] + aldi_result["missing"] + aldi_result["wrong"])

    total_value = near_dark["total_value"] + four20["total_value"] + aldi["total_value"]

    print(f"""
┌─────────────────────────────────────────────────────────┐
│  📦 TOTAL DELIVERIES: 3                                 │
│  📄 TOTAL PAGES: 4                                      │
│  📝 TOTAL LINE ITEMS: {total_items:3d}                              │
│  💰 TOTAL VALUE: CHF {total_value:,.2f}                       │
├─────────────────────────────────────────────────────────┤
│  ✅ Items OK: {total_ok:3d}                                       │
│  ⚠️  Items with Issues: {total_issues:3d}                            │
├─────────────────────────────────────────────────────────┤
│  🚨 MAHNUNGEN NEEDED:                                   │
│     • Near Dark: YES - 4 issues                         │
│     • 420 Wholesale: YES - 2 issues                     │
│     • Aldi Run: NO - All good                           │
└─────────────────────────────────────────────────────────┘
    """)

    # Time comparison
    print_time_comparison()

    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  🍯 LIKE HONEY                                               ║
║                                                              ║
║  Felix scans. Helix checks. Issues flagged. Home by 7.       ║
║                                                              ║
║  No more midnight. No more email search. No more Mahnung     ║
║  surprises at 2 AM.                                          ║
║                                                              ║
║  The Tiger and Lion built this at the crossroads.            ║
║                                                              ║
║  🦁🐅💧 Be water, my friend.                                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    run_the_play()
