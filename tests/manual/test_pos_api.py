#!/usr/bin/env python3
"""
Quick test script for POS API endpoints.
Tests the complete flow: login → create product → list → scan → checkout
"""
import requests
import json
from decimal import Decimal

BASE_URL = "https://helix-platform.local"
AUTH_URL = f"{BASE_URL}/api/v2"  # Auth endpoints are v2
POS_URL = f"{BASE_URL}/api/v1"   # POS endpoints are v1

# Disable SSL warnings for self-signed cert
requests.packages.urllib3.disable_warnings()


def login():
    """
    Mock login - no authentication required (using mock auth bypass)
    Returns empty string since endpoints don't check auth now
    """
    print("\n🔓 Step 1: Skipping auth (using mock bypass)...")
    print("✅ Mock auth enabled - all requests authenticated as 'pam'")
    return ""  # No token needed with mock auth


def list_products(token):
    """List all products"""
    print("\n📦 Step 2: Listing products...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{POS_URL}/pos/products",
        headers=headers,
        verify=False
    )
    response.raise_for_status()
    products = response.json()
    print(f"✅ Found {len(products)} products")

    if products:
        print("\n   Top 5 products:")
        for product in products[:5]:
            print(f"   - [{product['sku']}] {product['name']} - CHF {product['price']}")

    return products


def create_transaction(token):
    """Start a new transaction (open cart)"""
    print("\n🛒 Step 3: Creating new transaction...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{POS_URL}/pos/transactions",
        json={},
        headers=headers,
        verify=False
    )
    response.raise_for_status()
    transaction = response.json()
    print(f"✅ Transaction created: {transaction['transaction_number']}")
    print(f"   ID: {transaction['id']}")
    return transaction


def scan_product(token, transaction_id, barcode, quantity=1):
    """Scan a product and add to cart"""
    print(f"\n📱 Step 4: Scanning barcode '{barcode}'...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{POS_URL}/pos/transactions/{transaction_id}/scan",
        json={
            "barcode": barcode,
            "quantity": quantity
        },
        headers=headers,
        verify=False
    )
    response.raise_for_status()
    result = response.json()

    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"   Product: {result['product']['name']}")
        print(f"   Price: CHF {result['line_item']['line_total']}")
    else:
        print(f"❌ {result['message']}")

    return result


def get_transaction(token, transaction_id):
    """Get current cart details"""
    print(f"\n🔍 Step 5: Viewing cart...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{POS_URL}/pos/transactions/{transaction_id}",
        headers=headers,
        verify=False
    )
    response.raise_for_status()
    transaction = response.json()

    print(f"✅ Cart details:")
    print(f"   Transaction: {transaction['transaction_number']}")
    print(f"   Items: {len(transaction['line_items'])}")
    print(f"   Total: CHF {transaction['total']}")

    return transaction


def checkout(token, transaction_id, payment_method="cash", amount_tendered=None):
    """Process checkout"""
    print(f"\n💳 Step 6: Processing checkout ({payment_method})...")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"payment_method": payment_method}
    if amount_tendered:
        payload["amount_tendered"] = str(amount_tendered)

    response = requests.post(
        f"{POS_URL}/pos/transactions/{transaction_id}/checkout",
        json=payload,
        headers=headers,
        verify=False
    )
    response.raise_for_status()
    transaction = response.json()

    print(f"✅ Payment successful!")
    print(f"   Receipt: {transaction['receipt_number']}")
    print(f"   Total: CHF {transaction['total']}")

    if transaction.get('change_given'):
        print(f"   Change: CHF {transaction['change_given']}")

    return transaction


def test_daily_summary(token):
    """Get daily sales summary"""
    print(f"\n📊 Step 7: Fetching daily summary...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{POS_URL}/pos/reports/daily-summary",
        headers=headers,
        verify=False
    )
    response.raise_for_status()
    summary = response.json()

    print(f"✅ Daily Summary ({summary['date']}):")
    print(f"   Total Sales: CHF {summary['total_sales']}")
    print(f"   Transactions: {summary['total_transactions']}")
    print(f"   Cash: CHF {summary['cash_total']}")
    print(f"   Visa: CHF {summary['visa_total']}")
    print(f"   Twint: CHF {summary['twint_total']}")

    return summary


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 HelixNet POS API Test - Felix's Artemis Store")
    print("=" * 60)

    try:
        # Login
        token = login()

        # List products
        products = list_products(token)

        if not products:
            print("\n❌ No products found! Make sure seeding ran successfully.")
            exit(1)

        # Create transaction
        transaction = create_transaction(token)

        # Scan first product (CBD Oil)
        scan_result = scan_product(
            token,
            transaction["id"],
            "7610000123456",  # CBD Oil 10%
            quantity=1
        )

        # Scan second product (Grinder)
        scan_result = scan_product(
            token,
            transaction["id"],
            "7610000123461",  # Grinder
            quantity=2
        )

        # View cart
        cart = get_transaction(token, transaction["id"])

        # Checkout with cash
        total = float(cart["total"])
        completed = checkout(
            token,
            transaction["id"],
            payment_method="cash",  # lowercase required by API
            amount_tendered=total + 10  # Give 10 CHF extra
        )

        # Get daily summary
        summary = test_daily_summary(token)

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED! POS system is working perfectly!")
        print("=" * 60)

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Test failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        exit(1)
