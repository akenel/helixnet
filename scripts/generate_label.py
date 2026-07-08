#!/usr/bin/env python3
"""generate_label.py — v1 product LABEL: barcode + title + price (Brother QL-820NWB, 62mm).

Renders a print-preview strip of 62mm labels: SVG barcode (python-barcode) + title + price →
HTML → Puppeteer PDF. On-site, brother_ql sends the SAME layout as a raster to the QL-820NWB
over WiFi/USB (Debian, no Windows). Mono black for scan reliability.

Usage:
    python3 scripts/generate_label.py labels.json out/labels.html
    node scripts/postcard-to-pdf.js out/labels.html out/labels.pdf
labels.json = list of {barcode, name, price}  (barcode: 12/13-digit EAN, else any SKU → Code128)
"""
import base64
import html as _html
import json
import sys
from io import BytesIO

import barcode
from barcode.writer import SVGWriter

LABEL_W_MM = 62      # DK-22205 continuous roll
LABEL_H_MM = 37


def esc(s) -> str:
    return _html.escape(str(s or ""))


def barcode_datauri(value) -> str:
    """EAN-13 for 12/13-digit numerics (retail), else Code128 (any SKU). Mono black SVG."""
    val = str(value or "").strip()
    if val.isdigit() and len(val) in (12, 13):
        cls, payload = barcode.get_barcode_class("ean13"), val[:12]
    else:
        cls, payload = barcode.get_barcode_class("code128"), (val or "0000")
    buf = BytesIO()
    cls(payload, writer=SVGWriter()).write(
        buf, options={"module_height": 11.0, "module_width": 0.30, "font_size": 9,
                      "text_distance": 3.0, "quiet_zone": 2.0})
    return "data:image/svg+xml;base64," + base64.b64encode(buf.getvalue()).decode()


def label(p: dict) -> str:
    try:
        price = f"CHF {float(p.get('price')):.2f}"
    except (TypeError, ValueError):
        price = ""
    return f'''<div class="label">
      <div class="top"><div class="title">{esc(p.get("name"))}</div><div class="price">{price}</div></div>
      <img class="bc" src="{barcode_datauri(p.get("barcode"))}" alt="">
    </div>'''


def build(items: list) -> str:
    page_h = len(items) * (LABEL_H_MM + 3) + 6
    labels = "\n".join(label(p) for p in items)
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
  @page {{ size: {LABEL_W_MM}mm {page_h}mm; margin: 0; }}
  * {{ box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #fff; padding: 3mm 0; }}
  .label {{ width: {LABEL_W_MM}mm; height: {LABEL_H_MM}mm; padding: 2mm 3mm; border-bottom: 1px dashed #bbb;
           display: flex; flex-direction: column; justify-content: space-between; }}
  .top {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 3mm; }}
  .title {{ font-size: 10px; font-weight: 700; line-height: 1.15;
           display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
  .price {{ font-size: 15px; font-weight: 800; white-space: nowrap; }}
  .bc {{ width: 100%; height: 15mm; object-fit: contain; }}
</style></head><body>
{labels}
</body></html>'''


def main() -> None:
    if len(sys.argv) < 3:
        print("usage: generate_label.py <labels.json> <out.html>")
        sys.exit(2)
    items = json.load(open(sys.argv[1], encoding="utf-8"))
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(build(items))
    print(f"✓ {sys.argv[2]} — {len(items)} labels ({LABEL_W_MM}×{LABEL_H_MM}mm)")


if __name__ == "__main__":
    main()
