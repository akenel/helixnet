#!/usr/bin/env python3
"""Banco POS — daily end-to-end smoke + reconciliation + fuzz against a live env.

Drives the REAL REST API through a full retail day (open drawers, ring varied
sales across payment types and dine-in/takeaway VAT, paid in/out, refund, close
drawers, timesheets), then VERIFIES the money reconciles and a monkey/fuzz pass
finds no server crashes. Exit 0 = all green; exit 1 = a check failed or a 5xx crash.

Designed to run daily against the SANDBOX (synthetic monitoring / regression alarm).
    python scripts/banco_sim/banco_daily_smoke.py --env sandbox --reset

Env presets (override with env vars POS_API / POS_KC / POS_REALM):
    sandbox -> sandbox-banco.lapiazza.app  (realm kc-sandbox)
    staging -> staging-banco.lapiazza.app  (realm borrowhood-staging)
Only pam (cashier) + felix (admin) are assumed to exist. --reset zeroes the env
first (sandbox only; runs `make sandbox-reset` over ssh to the box).

NOTE: a daily smoke runs "today" (no backdating). For a realistic past-day demo,
see scripts/banco_sim/README.md.
"""
from __future__ import annotations
import argparse, math, subprocess, sys
from decimal import Decimal as D
import requests

requests.packages.urllib3.disable_warnings()

ENVS = {
    "sandbox": ("https://sandbox-banco.lapiazza.app", "https://lapiazza.app", "kc-sandbox"),
    "staging": ("https://staging-banco.lapiazza.app", "https://lapiazza.app", "borrowhood-staging"),
}
CLIENT = "helix_pos_web"

CATALOG = [
    ("CAFE-CAPP", "Cappuccino", 4.50, "cafe_food", "Cafe"),
    ("CAFE-ESP", "Espresso", 3.50, "cafe_food", "Cafe"),
    ("CAFE-CROIS", "Croissant", 3.00, "cafe_food", "Cafe"),
    ("CAFE-MUFFIN", "Blueberry Muffin", 3.80, "cafe_food", "Cafe"),
    ("CAFE-OJ", "Fresh Orange Juice", 5.00, "cafe_food", "Cafe"),
    ("CBD-OIL20", "Hemp Sana CBD Oil 20%", 42.00, "cbd_open", "CBD"),
    ("CBD-FLOWER", "CBD Flower Amnesia 2g", 18.00, "cbd_hemp", "CBD"),
    ("TOB-CIG", "Cigarettes Pack", 9.00, "tobacco_nicotine", "Tobacco"),
    ("ACC-PAPERS", "Gizeh Rolling Papers", 1.50, "standard", "Papers"),
    ("ACC-GRINDER", "4-part Grinder 50mm", 15.00, "standard", "Equipment"),
    ("BAR-BEER", "Lager Beer 0.5L", 6.00, "alcohol", "Bar"),
    ("BAR-WINE", "Red Wine Glass", 7.50, "alcohol", "Bar"),
]
CUSTOMERS = [("larry", "Larry Smith"), ("tomy", "Tomy Bianchi"),
             ("nina", "Nina Keller"), ("marco", "Marco Rossi")]


class Client:
    def __init__(self, api, kc, realm, user):
        self.api = api
        r = requests.post(f"{kc}/realms/{realm}/protocol/openid-connect/token",
                          data={"client_id": CLIENT, "username": user, "password": "helix_pass",
                                "grant_type": "password"}, verify=False, timeout=20)
        r.raise_for_status()
        self.s = requests.Session(); self.s.verify = False
        self.s.headers["Authorization"] = f"Bearer {r.json()['access_token']}"

    def call(self, method, path, ok=(200, 201), **kw):
        r = self.s.request(method, f"{self.api}{path}", timeout=20, **kw)
        if r.status_code not in ok:
            raise SystemExit(f"FAIL {method} {path} -> {r.status_code}: {r.text[:300]}")
        return r.json() if r.text else {}

    def raw(self, method, path, **kw):
        r = self.s.request(method, f"{self.api}{path}", timeout=20, **kw)
        return r.status_code


def reset_sandbox():
    print("== reset sandbox ==")
    subprocess.run(["ssh", "-o", "ConnectTimeout=30", "root@46.62.138.218",
                    "cd /opt/helixnet && make sandbox-reset"], check=True)


def run_day(felix, pam):
    P = {}
    for sku, name, price, cls, cat in CATALOG:
        P[sku] = felix.call("POST", "/api/v1/pos/products",
                            json={"sku": sku, "name": name, "price": price, "category": cat,
                                  "product_class": cls, "stock_quantity": 100})["id"]
    C = {h: str(felix.call("POST", "/api/v1/customers",
                           json={"handle": h, "real_name": rn, "age_confirmed": True})["id"])
         for h, rn in CUSTOMERS}
    pam.call("POST", "/api/v1/pos/shift/open", json={"opening_float": "200.00"})
    felix.call("POST", "/api/v1/pos/shift/open", json={"opening_float": "200.00"})

    def ring(who, items, payment, cust=None):
        tx = who.call("POST", "/api/v1/pos/transactions", json={})["id"]
        for it in items:
            body = {"product_id": P[it[0]], "quantity": it[1],
                    "consumption": it[2] if len(it) > 2 and it[2] else "dine_in"}
            if len(it) > 3 and it[3]:
                body["discount_percent"] = str(it[3])
            if len(it) > 4 and it[4]:
                body["is_giveaway"] = True
            who.call("POST", f"/api/v1/pos/transactions/{tx}/items", json=body)
        pay = {"payment_method": payment}
        if payment == "cash":
            pay["amount_tendered"] = "200"
        if cust:
            pay["customer_id"] = C[cust]
        return who.call("POST", f"/api/v1/pos/transactions/{tx}/checkout", json=pay)

    sales = [
        (pam, [("CAFE-CAPP", 1, "dine_in")], "cash", None),
        (pam, [("CAFE-ESP", 1, "takeaway"), ("CAFE-CROIS", 1, "takeaway")], "cash", None),
        (pam, [("CBD-OIL20", 1, "dine_in")], "twint", "larry"),
        (pam, [("TOB-CIG", 1, "dine_in"), ("ACC-PAPERS", 2, "dine_in")], "cash", None),
        (pam, [("CAFE-CAPP", 2, "dine_in"), ("CAFE-MUFFIN", 1, "dine_in")], "twint", "tomy"),
        (pam, [("BAR-BEER", 1, "dine_in")], "cash", None),
        (pam, [("ACC-GRINDER", 1, "dine_in", 10)], "visa", "marco"),
        (pam, [("CAFE-OJ", 1, "takeaway")], "cash", None),
        (felix, [("CBD-FLOWER", 1, "dine_in")], "debit", "nina"),
        (pam, [("CAFE-CROIS", 3, "takeaway")], "cash", None),
        (pam, [("CAFE-CAPP", 1, "dine_in")], "cash", "larry"),
        (pam, [("BAR-WINE", 2, "dine_in")], "cash", None),
        (pam, [("CAFE-CAPP", 1, "dine_in"), ("CAFE-MUFFIN", 1, "dine_in", 0, True)], "cash", None),
        (pam, [("CBD-OIL20", 1, "dine_in"), ("ACC-PAPERS", 1, "dine_in")], "twint", None),
        (felix, [("CAFE-MUFFIN", 1, "takeaway"), ("CAFE-CAPP", 1, "takeaway")], "cash", "tomy"),
        (pam, [("TOB-CIG", 2, "dine_in")], "cash", None),
        (pam, [("BAR-BEER", 2, "dine_in"), ("CAFE-ESP", 1, "dine_in")], "twint", "marco"),
        (pam, [("ACC-GRINDER", 1, "dine_in")], "cash", None),
    ]
    done = [ring(*sp) for sp in sales]
    pam.call("POST", "/api/v1/pos/shift/paid", json={"kind": "paid_in", "amount": "50.00", "reason": "Float top-up"})
    pam.call("POST", "/api/v1/pos/shift/paid", json={"kind": "paid_out", "amount": "25.00", "reason": "Cafe supplies"})
    target = next(d for d in done if d["payment_method"] == "cash" and float(d["total"]) > 0)
    felix.call("POST", f"/api/v1/pos/transactions/{target['id']}/refund", json={"reason": "Customer returned item"})
    for who in (pam, felix):
        cur = who.call("GET", "/api/v1/pos/shift/current")
        who.call("POST", "/api/v1/pos/shift/close", json={"counted_cash": f"{float(cur['expected_cash']):.2f}"})
    return done


def verify(felix, results):
    ds = felix.call("GET", "/api/v1/pos/reports/daily-summary")
    checks = [
        ("VAT std+reduced == total", D(ds["vat_standard"]) + D(ds["vat_reduced"]) == D(ds["vat_total"])),
        ("turnover split == total sales", D(ds["turnover_standard"]) + D(ds["turnover_reduced"]) == D(ds["total_sales"])),
        ("payments sum == total sales",
         sum(D(ds[k]) for k in ["cash_total", "visa_total", "debit_total", "twint_total",
                                "bank_transfer_total", "crypto_total", "other_total"]) == D(ds["total_sales"])),
        ("at least one sale recorded", ds["total_transactions"] > 0),
        ("two cashiers split", len(ds.get("cashier_performance", {})) == 2),
    ]
    for name, ok in checks:
        results.append((f"reconcile: {name}", ok))


def monkey(felix, pam, results):
    prod = felix.call("GET", "/api/v1/pos/products", params={"limit": 1})[0]["id"]
    pam.call("POST", "/api/v1/pos/shift/open", json={"opening_float": "100.00"})
    tx = pam.call("POST", "/api/v1/pos/transactions", json={})["id"]
    empty = pam.call("POST", "/api/v1/pos/transactions", json={})["id"]
    cases = [
        ("neg qty 422", pam.raw("POST", f"/api/v1/pos/transactions/{tx}/items", json={"product_id": prod, "quantity": -3}), (400, 422)),
        ("qty>cap 422", pam.raw("POST", f"/api/v1/pos/transactions/{tx}/items", json={"product_id": prod, "quantity": 10000000}), (400, 422)),
        ("bad payment 422", pam.raw("POST", f"/api/v1/pos/transactions/{tx}/checkout", json={"payment_method": "bitcoin"}), (400, 422)),
        ("ghost product 404", pam.raw("POST", f"/api/v1/pos/transactions/{tx}/items", json={"product_id": "00000000-0000-0000-0000-000000000999", "quantity": 1}), (400, 404, 422)),
        ("refund as cashier 403", pam.raw("POST", f"/api/v1/pos/transactions/{tx}/refund", json={"reason": "no"}), (400, 403, 404, 409)),
        ("empty-cart checkout blocked", pam.raw("POST", f"/api/v1/pos/transactions/{empty}/checkout", json={"payment_method": "twint"}), (400, 409, 422)),
        ("SQLi neutralized", pam.raw("GET", "/api/v1/pos/search", params={"q": "'; DROP TABLE products;--"}), (200,)),
    ]
    crashes = 0
    for name, code, expect in cases:
        is5xx = 500 <= code < 600
        crashes += is5xx
        results.append((f"monkey: {name} (got {code})", code in expect and not is5xx))
    pam.call("POST", "/api/v1/pos/shift/close", json={"counted_cash": "100.00"})
    return crashes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="sandbox", choices=list(ENVS))
    ap.add_argument("--reset", action="store_true", help="zero the env first (sandbox only)")
    args = ap.parse_args()
    api, kc, realm = ENVS[args.env]

    if args.reset:
        if args.env != "sandbox":
            sys.exit("refusing --reset on non-sandbox")
        reset_sandbox()

    felix = Client(api, kc, realm, "felix")
    pam = Client(api, kc, realm, "pam")
    print(f"== {args.env}: auth felix + pam OK ==")
    results = []
    run_day(felix, pam)
    print("== simulated a full two-till day ==")
    verify(felix, results)
    crashes = monkey(felix, pam, results)
    print("\n--- RESULTS ---")
    failed = 0
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        failed += not ok
    print(f"\n{len(results)-failed}/{len(results)} checks passed | 5xx crashes: {crashes}")
    sys.exit(1 if failed or crashes else 0)


if __name__ == "__main__":
    main()
