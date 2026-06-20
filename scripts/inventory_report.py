#!/usr/bin/env python3
"""
Banco POS — inventory report (reusable).

Read-only. Pulls the full product catalog from the POS API (paginated) and writes
a timestamped report: a per-item CSV + a Markdown summary (totals, by-category,
low-stock, out-of-stock, inventory value). Works against any environment over
HTTPS with a real Keycloak token -- no DB credentials needed.

Usage:
    source .venv/bin/activate
    python scripts/inventory_report.py --env local
    python scripts/inventory_report.py --env prod
    python scripts/inventory_report.py --env staging --out docs/business/inventory

All test users = helix_pass.
"""
import argparse
import csv
import datetime as _dt
import os
from collections import defaultdict

import requests

requests.packages.urllib3.disable_warnings()

ENVS = {
    "local":   ("https://helix-platform.local",        "https://keycloak.helix.local"),
    "staging": ("https://staging-banco.lapiazza.app",  "https://lapiazza.app"),
    "prod":    ("https://banco.lapiazza.app",           "https://lapiazza.app"),
}
REALM, CLIENT = "kc-pos-realm-dev", "helix_pos_web"


def get_token(kc, user="felix", pw="helix_pass"):
    r = requests.post(
        f"{kc}/realms/{REALM}/protocol/openid-connect/token",
        data={"client_id": CLIENT, "username": user, "password": pw, "grant_type": "password"},
        verify=False, timeout=20,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def fetch_all(api, token, page=200):
    """Paginate the whole catalog (active + inactive)."""
    h = {"Authorization": f"Bearer {token}"}
    items, skip = [], 0
    while True:
        r = requests.get(f"{api}/api/v1/pos/products",
                         params={"skip": skip, "limit": page, "active_only": "false"},
                         headers=h, verify=False, timeout=30)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        items.extend(batch)
        if len(batch) < page:
            break
        skip += page
    return items


def num(x):
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def build_report(items):
    cats = defaultdict(lambda: {"count": 0, "units": 0, "retail": 0.0, "cost": 0.0})
    total = {"count": 0, "active": 0, "inactive": 0, "with_barcode": 0,
             "units": 0, "retail": 0.0, "cost": 0.0}
    low, out = [], []
    for p in items:
        stock = int(p.get("stock_quantity") or 0)
        price, cost = num(p.get("price")), num(p.get("cost"))
        cat = p.get("category") or "(uncategorised)"
        total["count"] += 1
        total["active"] += 1 if p.get("is_active") else 0
        total["inactive"] += 0 if p.get("is_active") else 1
        total["with_barcode"] += 1 if p.get("barcode") else 0
        total["units"] += stock
        total["retail"] += stock * price
        total["cost"] += stock * cost
        c = cats[cat]
        c["count"] += 1; c["units"] += stock
        c["retail"] += stock * price; c["cost"] += stock * cost
        thr = p.get("stock_alert_threshold")
        if stock <= 0:
            out.append(p)
        elif thr is not None and stock <= int(thr):
            low.append(p)
    return total, cats, low, out


def main():
    ap = argparse.ArgumentParser(description="Banco POS inventory report")
    ap.add_argument("--env", choices=ENVS.keys(), default="local")
    ap.add_argument("--out", default="docs/business/inventory")
    args = ap.parse_args()

    api, kc = ENVS[args.env]
    print(f"Inventory report · env={args.env} · {api}")
    token = get_token(kc)
    items = fetch_all(api, token)
    total, cats, low, out = build_report(items)

    os.makedirs(args.out, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y-%m-%d-%H%M")
    base = os.path.join(args.out, f"inventory-{args.env}-{stamp}")

    # Per-item CSV
    with open(base + ".csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["SKU", "Name", "Category", "Barcode", "Price", "Cost",
                    "Stock", "RetailValue", "CostValue", "Active"])
        for p in sorted(items, key=lambda x: (x.get("category") or "", x.get("name") or "")):
            stock = int(p.get("stock_quantity") or 0)
            w.writerow([p.get("sku"), p.get("name"), p.get("category"), p.get("barcode"),
                        f"{num(p.get('price')):.2f}", f"{num(p.get('cost')):.2f}", stock,
                        f"{stock*num(p.get('price')):.2f}", f"{stock*num(p.get('cost')):.2f}",
                        "yes" if p.get("is_active") else "no"])

    # Markdown summary
    lines = [
        f"# Banco Inventory Report — {args.env}",
        f"_Generated {_dt.datetime.now().strftime('%Y-%m-%d %H:%M')} · source {api}_",
        "",
        "## Summary",
        f"- **Unique items (SKUs):** {total['count']:,}  (active {total['active']:,} · inactive {total['inactive']:,})",
        f"- **With barcode:** {total['with_barcode']:,}",
        f"- **Categories:** {len(cats)}",
        f"- **Total stock units:** {total['units']:,}",
        f"- **Inventory value (retail):** CHF {total['retail']:,.2f}",
        f"- **Inventory value (cost):** CHF {total['cost']:,.2f}",
        f"- **Potential margin:** CHF {total['retail']-total['cost']:,.2f}",
        f"- **Low stock (≤ alert threshold):** {len(low):,}  ·  **Out of stock:** {len(out):,}",
        "",
        "## By category",
        "| Category | Items | Units | Retail CHF | Cost CHF |",
        "|---|--:|--:|--:|--:|",
    ]
    for cat, c in sorted(cats.items(), key=lambda kv: kv[1]["count"], reverse=True):
        lines.append(f"| {cat} | {c['count']:,} | {c['units']:,} | {c['retail']:,.2f} | {c['cost']:,.2f} |")
    if out:
        lines += ["", f"## Out of stock ({len(out)})", "| SKU | Name | Category |", "|---|---|---|"]
        for p in out[:100]:
            lines.append(f"| {p.get('sku')} | {p.get('name')} | {p.get('category') or ''} |")
        if len(out) > 100:
            lines.append(f"| … | _+{len(out)-100} more (see CSV)_ | |")
    if low:
        lines += ["", f"## Low stock ({len(low)})", "| SKU | Name | Stock | Threshold |", "|---|---|--:|--:|"]
        for p in sorted(low, key=lambda x: int(x.get("stock_quantity") or 0))[:100]:
            lines.append(f"| {p.get('sku')} | {p.get('name')} | {p.get('stock_quantity')} | {p.get('stock_alert_threshold')} |")
        if len(low) > 100:
            lines.append(f"| … | _+{len(low)-100} more (see CSV)_ | | |")
    with open(base + ".md", "w") as f:
        f.write("\n".join(lines) + "\n")

    # Console summary
    print(f"\nUnique items: {total['count']:,} (active {total['active']:,}, inactive {total['inactive']:,})")
    print(f"Categories: {len(cats)} · Stock units: {total['units']:,}")
    print(f"Value retail: CHF {total['retail']:,.2f} · cost: CHF {total['cost']:,.2f}")
    print(f"Low stock: {len(low):,} · Out of stock: {len(out):,}")
    print(f"\nWrote:\n  {base}.csv\n  {base}.md")


if __name__ == "__main__":
    main()
