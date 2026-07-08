#!/usr/bin/env python3
"""generate_catalog.py — turn defined products into a printable PAPER CATALOG.

The on-site artifact (Angel 2026-07-08): photo + title + badges + price + short description
per item, in a clean A4 card grid → Puppeteer PDF. Same source of truth as the digital till;
the BL-18 cron's descriptions flow straight in here.

Usage:
    python3 scripts/generate_catalog.py products.json out/catalog.html ["Artemis — Product Catalog"]
    node scripts/postcard-to-pdf.js out/catalog.html out/catalog.pdf

products.json = list of {name, price, product_class, is_age_restricted, category, description, image_url}
"""
import html as _html
import json
import sys

# product_class -> (emoji, short label). CATEGORY drives merchandising; CLASS drives the badge.
CLASS_BADGE = {
    "tobacco_nicotine": ("🚬", "Tobacco"),
    "alcohol":          ("🍺", "Alcohol"),
    "cbd_hemp":         ("🌿", "CBD 18+"),
    "cbd_open":         ("🌿", "CBD"),
    "cafe_food":        ("☕", "Café"),
    "age_restricted":   ("🔞", "18+"),
    "standard":         ("📦", ""),
}


def esc(s) -> str:
    return _html.escape(str(s or ""))


def card(p: dict) -> str:
    emoji, label = CLASS_BADGE.get(p.get("product_class") or "standard", ("📦", ""))
    age = bool(p.get("is_age_restricted"))
    price = p.get("price")
    try:
        price_txt = f"CHF {float(price):.2f}"
    except (TypeError, ValueError):
        price_txt = ""
    img = esc(p.get("image_url"))
    img_html = (f'<div class="ph"><img src="{img}" loading="eager" alt=""></div>'
                if img else '<div class="ph noimg">no photo</div>')
    badges = f'<span class="chip">{emoji} {esc(label)}</span>' if label else f'<span class="chip">{emoji}</span>'
    if age:
        badges += '<span class="chip age">🔞 18+</span>'
    cat = esc(p.get("category"))
    return f'''<div class="card">
      {img_html}
      <div class="body">
        <div class="badges">{badges}</div>
        <div class="title">{esc(p.get("name"))}</div>
        <div class="meta">{cat}</div>
        <div class="desc">{esc(p.get("description"))}</div>
        <div class="price">{price_txt}</div>
      </div>
    </div>'''


def build(products: list, title: str) -> str:
    cards = "\n".join(card(p) for p in products)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<style>
  @page {{ size: A4 portrait; margin: 0; }}
  * {{ box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  body {{ margin: 0; font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
         color: #1f2937; background: #fff; }}
  .page {{ padding: 10mm 8mm 8mm; }}
  header {{ display: flex; align-items: baseline; justify-content: space-between;
           border-bottom: 2px solid #C0392B; padding-bottom: 6px; margin-bottom: 10px; }}
  header h1 {{ font-size: 18px; margin: 0; color: #8B0000; }}
  header .sub {{ font-size: 11px; color: #6b7280; }}
  .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 6mm; }}
  .card {{ border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; display: flex;
          flex-direction: column; break-inside: avoid; background: #fff; }}
  .ph {{ height: 34mm; display: flex; align-items: center; justify-content: center; background: #f7f7f8; }}
  .ph img {{ max-width: 100%; max-height: 34mm; object-fit: contain; }}
  .ph.noimg {{ color: #b0b4bb; font-size: 10px; }}
  .body {{ padding: 7px 8px 8px; display: flex; flex-direction: column; gap: 3px; flex: 1; }}
  .badges {{ display: flex; gap: 4px; flex-wrap: wrap; }}
  .chip {{ font-size: 9px; font-weight: 700; background: #eef0f2; color: #374151;
          border-radius: 99px; padding: 1px 7px; }}
  .chip.age {{ background: #fde8e6; color: #8B0000; }}
  .title {{ font-size: 12px; font-weight: 700; line-height: 1.2;
           display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
  .meta {{ font-size: 9px; color: #9ca3af; }}
  .desc {{ font-size: 9.5px; color: #4b5563; line-height: 1.3; flex: 1;
          display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; }}
  .price {{ font-size: 14px; font-weight: 800; color: #8B0000; margin-top: 2px; }}
</style></head>
<body><div class="page">
  <header><h1>{esc(title)}</h1><span class="sub">{len(products)} items · Banco material master</span></header>
  <div class="grid">
{cards}
  </div>
</div></body></html>'''


def main() -> None:
    if len(sys.argv) < 3:
        print("usage: generate_catalog.py <products.json> <out.html> [title]")
        sys.exit(2)
    src, out = sys.argv[1], sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else "Product Catalog"
    products = json.load(open(src, encoding="utf-8"))
    with open(out, "w", encoding="utf-8") as f:
        f.write(build(products, title))
    print(f"✓ {out} — {len(products)} cards")


if __name__ == "__main__":
    main()
