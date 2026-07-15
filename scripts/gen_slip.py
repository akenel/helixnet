#!/usr/bin/env python3
"""Generate a realistic Swiss Lieferschein (HTML + PNG) for testing the slip reader.

A slip is DATA: a header + a list of {qty, artnr, name, price}. This renders the shared
Tamar Trade -> Artemis Luzern template and shells out to scripts/slip-to-png.js for a crisp
PNG (approximates a clean phone photo). Reuse it to mint edge-case + bulk samples fast.

    python3 scripts/gen_slip.py   # writes slip-03-bulk.{html,png} (edit SLIPS below)
"""
from __future__ import annotations
import html
import subprocess
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

OUT = Path("docs/testing/banco/receiving-slips")

_CSS = """
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:#e9e9e9; padding:24px; font-family:'Helvetica Neue',Arial,sans-serif; color:#111; }
  .slip { width:820px; margin:0 auto; background:#fff; padding:44px 52px; box-shadow:0 2px 10px rgba(0,0,0,.15); }
  .top { display:flex; justify-content:space-between; align-items:flex-start; border-bottom:3px solid #1a4d2e; padding-bottom:16px; }
  .brand { font-size:21px; font-weight:800; color:#1a4d2e; letter-spacing:.5px; }
  .brand small { display:block; font-weight:400; font-size:11.5px; color:#555; margin-top:4px; line-height:1.5; }
  .doc { text-align:right; }
  .doc h1 { font-size:24px; letter-spacing:2px; color:#1a4d2e; }
  .doc table { margin-top:8px; font-size:12.5px; }
  .doc td { padding:1px 0 1px 14px; text-align:right; }
  .doc td.k { color:#666; }
  .parties { display:flex; justify-content:space-between; margin:22px 0 6px; font-size:12.5px; }
  .parties .lbl { font-size:10.5px; text-transform:uppercase; letter-spacing:1px; color:#888; margin-bottom:5px; }
  .parties .box { line-height:1.5; }
  table.items { width:100%; border-collapse:collapse; margin-top:16px; font-size:12.5px; }
  table.items th { background:#1a4d2e; color:#fff; text-align:left; padding:8px 9px; font-weight:600; font-size:11.5px; letter-spacing:.3px; }
  table.items th.num, table.items td.num { text-align:right; }
  table.items td { padding:8px 9px; border-bottom:1px solid #e4e4e4; }
  table.items tr:nth-child(even) td { background:#f7f9f7; }
  .totals { margin-top:12px; display:flex; justify-content:flex-end; }
  .totals table { font-size:13px; }
  .totals td { padding:3px 0 3px 26px; text-align:right; }
  .totals .grand td { font-weight:800; font-size:15px; border-top:2px solid #1a4d2e; padding-top:7px; color:#1a4d2e; }
  .foot { margin-top:28px; font-size:11px; color:#777; line-height:1.6; border-top:1px solid #ddd; padding-top:12px; }
"""


def _money(d: Decimal) -> str:
    return str(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def render(slip: dict) -> str:
    rows = []
    subtotal = Decimal("0")
    for i, it in enumerate(slip["items"], 1):
        qty = Decimal(str(it["qty"]))
        price = Decimal(str(it["price"]))
        line = qty * price
        subtotal += line
        rows.append(
            f'<tr><td>{i}</td><td class="num">{it["qty"]}</td>'
            f'<td>{html.escape(it["artnr"])}</td>'
            f'<td>{html.escape(it["name"])}</td>'
            f'<td class="num">{_money(price)}</td>'
            f'<td class="num">{_money(line)}</td></tr>'
        )
    vat = subtotal * Decimal("0.081")
    total = subtotal + vat
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>{_CSS}</style></head><body>
  <div class="slip">
    <div class="top">
      <div class="brand">TAMAR TRADE GmbH
        <small>Blegistrasse 1 · 6340 Baar · Schweiz<br>UID: CHE-116.281.277 MWST · Tel. 041 500 12 34 · bestellung@tamar.ch</small>
      </div>
      <div class="doc"><h1>LIEFERSCHEIN</h1><table>
        <tr><td class="k">Nr.</td><td>{html.escape(slip["note_no"])}</td></tr>
        <tr><td class="k">Datum</td><td>{html.escape(slip["date"])}</td></tr>
        <tr><td class="k">Kunden-Nr.</td><td>K-1042</td></tr>
        <tr><td class="k">Bestellung</td><td>{html.escape(slip.get("order_no","WEB-88300"))}</td></tr>
        {f'<tr><td class="k">Seite</td><td>{html.escape(slip["page_label"])}</td></tr>' if slip.get("page_label") else ''}
      </table></div>
    </div>
    <div class="parties">
      <div><div class="lbl">Lieferadresse</div><div class="box"><b>Artemis Luzern</b><br>z.H. Felix<br>Baselstrasse 11<br>6003 Luzern</div></div>
      <div style="text-align:right"><div class="lbl">Versand</div><div class="box">Post PostPac Priority<br>{html.escape(slip.get("tracking","99.34.7788.1122"))}<br>{slip.get("parcels","2 Pakete")} · {slip.get("weight","7.8 kg")}</div></div>
    </div>
    <table class="items"><thead><tr>
      <th style="width:38px">Pos.</th><th class="num" style="width:60px">Menge</th>
      <th style="width:110px">Art.-Nr.</th><th>Bezeichnung</th>
      <th class="num" style="width:88px">Preis/Stk</th><th class="num" style="width:92px">Total CHF</th>
    </tr></thead><tbody>{''.join(rows)}</tbody></table>
    {'' if not slip.get("show_totals", True) else f'''<div class="totals"><table>
      <tr><td>Zwischensumme</td><td>{_money(subtotal)}</td></tr>
      <tr><td>MwSt 8.1&nbsp;%</td><td>{_money(vat)}</td></tr>
      <tr class="grand"><td>Total CHF</td><td>{_money(total)}</td></tr>
    </table></div>'''}
    {f'<div class="foot" style="text-align:center;color:#999">— Fortsetzung auf Seite 2 —</div>' if slip.get("page_label","").startswith("1") else '<div class="foot">Die Ware bleibt bis zur vollständigen Bezahlung unser Eigentum. Beanstandungen innert 8 Tagen. Vielen Dank für Ihre Bestellung — Tamar Trade GmbH.</div>'}
  </div></body></html>"""


def build(name: str, slip: dict):
    htmlp = OUT / f"{name}.html"
    pngp = OUT / f"{name}.png"
    htmlp.write_text(render(slip), encoding="utf-8")
    subprocess.run(["node", "scripts/slip-to-png.js", str(htmlp), str(pngp)], check=True)
    print(f"built {name}: {len(slip['items'])} items -> {pngp}")


# ~28 real Artemis (Tamar) catalogue items — guaranteed matches — with varied quantities.
_BULK = [
    (10, "TAM-5660", "Aktivkohlefilter actiTube 8mm 100stk", 12.90),
    (4,  "TAM-25967", "Amy Deluxe Carbonmundstück - Schwarz", 24.90),
    (12, "TAM-9071", "Aufnäher Alchemy Motörhead", 4.90),
    (6,  "TAM-26331", "Backwoods Blunt Bold 5 stk.", 16.00),
    (8,  "TAM-22446", "Beamer Candles Co Cocanna Banana", 20.00),
    (8,  "TAM-22468", "Beamer Candles Co Get Baked", 20.00),
    (3,  "TAM-22121", "Black Leaf Füllhilf-Konsole Dollar", 22.00),
    (24, "TAM-25981", "Cannabis Gummi Bears", 6.00),
    (30, "TAM-26406", "Chapo Blunt Hemp Wraps Cheri 2 stk.", 2.50),
    (20, "TAM-10031", "Dichtung für Shisha Tabak-Kopf dick", 2.90),
    (2,  "TAM-19806", "DOLOCAN CBD Face Cream 50ml", 49.00),
    (6,  "TAM-15278", "Drehmaschine Elements 110mm", 9.90),
    (4,  "TAM-1518", "Duftlampe Speckstein 2-teilig klein", 18.00),
    (40, "TAM-23222", "Elements King Size Phantom Slim", 4.90),
    (100,"TAM-21669", "Gizeh King Size", 1.40),
    (2,  "TAM-21477", "Greenfire Black Cream Haschisch 9g", 50.00),
    (60, "TAM-7011", "Greengo King Size", 1.70),
    (10, "TAM-24613", "G-Rollz Prerolled Mango 2 Stk.", 4.90),
    (3,  "TAM-20499", "Hash Gang Double Zero 4.20gr.", 25.00),
    (3,  "TAM-20500", "Hash Gang Manali Cream 4.20gr.", 29.00),
    (5,  "TAM-22605", "Hempsana Hanf Gel Roller", 39.00),
    (50, "TAM-8617", "Juicy Jays King Size Cannabis", 1.90),
    (6,  "TAM-10856", "Mundstück Ice Bazooka gelb", 15.90),
    (80, "TAM-8219", "OCB DW kurz Organic Hemp", 2.00),
    (5,  "TAM-21248", "Old School Papers", 25.00),
    (50, "TAM-21577", "Raw KS Classic black Extra Fine", 1.90),
    (40, "TAM-3964", "Rizla DW kurz silver", 2.00),
    (40, "TAM-4504", "RS Rolls grün", 2.00),
]

def _items(rows):
    return [{"qty": q, "artnr": a, "name": n, "price": p} for (q, a, n, p) in rows]


if __name__ == "__main__":
    build("slip-03-bulk", {
        "note_no": "LS-2026-4512", "date": "2026-07-15", "order_no": "WEB-88300",
        "parcels": "2 Pakete", "weight": "9.4 kg", "items": _items(_BULK),
    })
    # A 2-PAGE slip: same Nr./date, items split across pages. Load both pics → lines merge.
    build("slip-04-page1", {
        "note_no": "LS-2026-4530", "date": "2026-07-15", "order_no": "WEB-88317",
        "parcels": "3 Pakete", "weight": "12.6 kg", "page_label": "1 / 2",
        "show_totals": False, "items": _items(_BULK[:15]),
    })
    build("slip-04-page2", {
        "note_no": "LS-2026-4530", "date": "2026-07-15", "order_no": "WEB-88317",
        "parcels": "3 Pakete", "weight": "12.6 kg", "page_label": "2 / 2",
        "show_totals": True, "items": _items(_BULK[15:]),
    })
