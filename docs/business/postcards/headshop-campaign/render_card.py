#!/usr/bin/env python3
"""Render a personalized handshake card per language, from card-chrome.json + the template.

`render(shop, out_pdf)` is the reusable entry point (Phase 3 calls it per selected shop).
`shop` keys: lang, first_name, shop_name, token, street, zip_city, qr, img_front, img_back,
logo, and optional `card_letter` (the recipe's per-shop letter HTML; else the default is built
from card-chrome.json). One card design, four language fills — the twin of the landing catalog.
"""
import json
import os
import subprocess

CAMP = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(CAMP, "..", "..", "..", ".."))
CHROME = json.load(open(os.path.join(CAMP, "card-chrome.json"), encoding="utf-8"))


def build_letter(lang: str, name: str) -> str:
    """Assemble the letter HTML (hi / body / sign) from the per-language default paragraphs."""
    paras = CHROME[lang]["LETTER"]
    parts = []
    for i, p in enumerate(paras):
        p = p.replace("{name}", name)
        cls = "hi" if i == 0 else ("sign" if i == len(paras) - 1 else "")
        parts.append(f'<p class="{cls}">{p}</p>' if cls else f"<p>{p}</p>")
    return "\n        ".join(parts)


def render(shop: dict, out_pdf: str) -> str:
    lang = shop.get("lang", "de")
    if lang not in CHROME:
        lang = "de"
    c = CHROME[lang]
    tpl = open(os.path.join(CAMP, "templates", "card-handshake.html"), encoding="utf-8").read()
    fields = {
        "{{C_CARD_HEAD}}": c["CARD_HEAD"], "{{C_CARD_TAG}}": c["CARD_TAG"], "{{C_CARD_QR}}": c["CARD_QR"],
        "{{C_ATTN}}": c["CARD_ATTN"], "{{C_STAMP}}": c["CARD_STAMP"],
        "{{CARD_LETTER}}": shop.get("card_letter") or build_letter(lang, shop["first_name"]),
        "{{FIRST_NAME}}": shop["first_name"], "{{SHOP_NAME}}": shop["shop_name"],
        "{{SHOP_STREET}}": shop.get("street", ""), "{{SHOP_ZIP_CITY}}": shop.get("zip_city", ""),
        "{{QR_SRC}}": shop.get("qr", ""), "{{TOKEN}}": shop["token"],
        "{{IMG_FRONT}}": shop.get("img_front", ""), "{{IMG_BACK}}": shop.get("img_back", ""),
        "{{SHOP_LOGO}}": shop.get("logo", ""),
    }
    tmp = out_pdf[:-4] + ".html"
    for k, v in fields.items():
        tpl = tpl.replace(k, v)
    open(tmp, "w", encoding="utf-8").write(tpl)
    subprocess.run(["node", os.path.join(REPO, "scripts", "postcard-to-pdf.js"), tmp, out_pdf],
                   check=True, stdout=subprocess.DEVNULL)
    return out_pdf
