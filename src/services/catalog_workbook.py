"""BL-131 — the Migration Workbench: a catalog worklist as a real .xlsx an operator LIKES using.

Why a spreadsheet at all? Because the enrichment engine only existed as scripts a developer runs from
a terminal — the shop could never drive it. A workbook hands them the keys: export the unfinished rows,
walk the shelf filling in what only a human standing there knows (which variant, the shelf price, and
the BARCODE — scanned straight into the cell, since a scanner gun is just a keyboard), import it back,
and let the AI fill what a machine can find (image, description, specs).

Design rules (learned the hard way):
- **Formulas + data validation, never macros.** A .xlsm macro is blocked by default, dies in Google
  Sheets, and dies in LibreOffice. Formulas/dropdowns/conditional-formatting survive all three.
- **The category column is a DROPDOWN of canonical labels only.** The taxonomy funnel enforced at the
  point of entry — a free-text category can't be invented in the first place (BL-CAT doctrine).
- **A per-row Google link.** The operator's real workflow: search the name, land on the right page in
  ten seconds. Automate the click, not the judgement.
- **Live progress formulas.** The counter that makes a grind feel finite (same reason the test sheets
  carry a X/N counter and a stopwatch).
"""
from __future__ import annotations

import io
from datetime import date
from typing import Iterable, Optional
from urllib.parse import quote_plus

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from src.services.catalog_taxonomy import CANONICAL_CATEGORIES

# La Piazza / Banco house colours (match the SOP + test-sheet artifacts)
RED = "C0392B"
DARK = "8B0000"
INK = "1F2937"
MUT = "6B7280"
LINE = "E5E7EB"
OK_BG = "E7F6EF"
WARN_BG = "FEF3E2"
BAD_BG = "FDEAEA"
HEAD_BG = "1F2937"

ACTIONS = ["ENRICH", "DONE", "SKIP", "DELETE"]

# (header, width, is_operator_editable)
COLUMNS = [
    ("Status",        11, False),   # formula
    ("SKU",           20, False),   # identity — never edit
    ("Product name",  46, True),
    ("Barcode / EAN", 18, True),    # ← scan the gun straight into this cell
    ("Category",      24, True),    # dropdown, canonical only
    ("Price CHF",     11, True),
    ("Cost CHF",      11, True),
    ("Size / variant", 16, True),
    ("Photo?",         8, False),
    ("Text?",          8, False),
    ("Look it up",    14, False),   # hyperlink
    ("Source URL",    34, True),
    ("Action",        12, True),    # dropdown
    ("Notes",         34, True),
]


def _style_header(ws, row=1):
    for c in range(1, len(COLUMNS) + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = PatternFill("solid", fgColor=HEAD_BG)
        cell.font = Font(color="FFFFFF", bold=True, size=10)
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        cell.border = Border(bottom=Side("thin", color=RED))
    ws.row_dimensions[row].height = 26


def _title(ws, text, sub=""):
    ws["A1"] = text
    ws["A1"].font = Font(bold=True, size=15, color=DARK)
    if sub:
        ws["A2"] = sub
        ws["A2"].font = Font(size=10, color=MUT)


def build_worklist_workbook(rows: Iterable[dict], *, section: Optional[str] = None,
                            env: str = "sandbox", stamp: Optional[str] = None) -> bytes:
    """rows: dicts with sku/name/barcode/category/price/cost/size/has_image/has_text.

    Returns .xlsx bytes: START HERE · Worklist · Summary · Lists.
    """
    rows = list(rows)
    stamp = stamp or date.today().isoformat()
    wb = Workbook()

    # ---------------- Lists (feeds the dropdowns; kept last & hidden) ----------------
    lists = wb.create_sheet("Lists")
    lists["A1"] = "Categories (canonical — do not edit)"
    lists["A1"].font = Font(bold=True, size=10, color=MUT)
    for i, c in enumerate(CANONICAL_CATEGORIES, start=2):
        lists.cell(row=i, column=1, value=c)
    lists["C1"] = "Actions"
    lists["C1"].font = Font(bold=True, size=10, color=MUT)
    for i, a in enumerate(ACTIONS, start=2):
        lists.cell(row=i, column=3, value=a)
    lists.column_dimensions["A"].width = 30

    # ---------------- START HERE ----------------
    intro = wb.active
    intro.title = "START HERE"
    serial = (section or "ALL").upper().replace(" ", "-").replace("&", "AND")[:16]
    _title(intro, "📦 Banco — Catalog Worklist",
           f"🐺 La Piazza · № LP-WB-{stamp.replace('-','')}-{serial} · env: {env} · {len(rows)} products")
    guide = [
        ("", ""),
        ("How this works", ""),
        ("1.", "Open the Worklist tab. Each row is a product that still needs finishing."),
        ("2.", "Walk the shelf. Fill in ONLY what you can see: the exact variant, the shelf price, and the BARCODE."),
        ("3.", "💡 Your scanner gun is just a keyboard — click the Barcode cell and SCAN. It types straight in."),
        ("4.", "Don't know something? Leave it blank. Blank is fine — never guess."),
        ("5.", "Click '🔎 Look it up' on any row to Google it — grab the exact name in seconds."),
        ("6.", "Save the file and import it back into Banco. The AI fills in the picture and the description."),
        ("", ""),
        ("The rules", ""),
        ("⏱️", "If one product fights you for more than a minute — set Action = SKIP and move on. Never rabbit-hole."),
        ("🎯", "Category is a dropdown. Only real categories. If none fit, leave it and add a Note."),
        ("💰", "Price = what it sells for on the shelf. Cost can wait — leave it blank."),
        ("📷", "Photo? / Text? show what Banco already has. 'no' = the AI will go find it."),
        ("", ""),
        ("Which pile is this?", "(the 6 types — see the Catalog Playbook)"),
        ("FAST", "Branded consumables (papers, filters, lighters, e-liquids) — scan, confirm, done."),
        ("CONFIRM", "Variant families — same brand, 50 look-alikes. Read the pack, get the exact one."),
        ("SLOW", "Generic glass / CBD — no barcode, no catalog. Delivery slip → our own photo + label."),
        ("LINE", "Artisan (jewelry, oils) — don't name every piece. One line + options + price tiers."),
    ]
    r = 4
    for a, b in guide:
        intro.cell(row=r, column=1, value=a).font = Font(bold=True, size=10, color=DARK)
        intro.cell(row=r, column=2, value=b).font = Font(size=10.5, color=INK)
        intro.cell(row=r, column=2).alignment = Alignment(wrap_text=True, vertical="top")
        r += 1
    intro.column_dimensions["A"].width = 12
    intro.column_dimensions["B"].width = 104
    intro.sheet_view.showGridLines = False

    # ---------------- Worklist ----------------
    ws = wb.create_sheet("Worklist")
    for i, (h, w, _) in enumerate(COLUMNS, start=1):
        ws.cell(row=1, column=i, value=h)
        ws.column_dimensions[get_column_letter(i)].width = w
    _style_header(ws)

    col = {h: get_column_letter(i) for i, (h, _, _) in enumerate(COLUMNS, start=1)}
    locked_fill = PatternFill("solid", fgColor="F3F4F6")

    for n, row in enumerate(rows, start=2):
        name = (row.get("name") or "").strip()
        ws[f"{col['SKU']}{n}"] = row.get("sku") or ""
        ws[f"{col['Product name']}{n}"] = name
        ws[f"{col['Barcode / EAN']}{n}"] = row.get("barcode") or ""
        ws[f"{col['Barcode / EAN']}{n}"].number_format = "@"      # text — never mangle a long EAN
        ws[f"{col['Category']}{n}"] = row.get("category") or ""
        if row.get("price") is not None:
            ws[f"{col['Price CHF']}{n}"] = float(row["price"])
        ws[f"{col['Price CHF']}{n}"].number_format = '#,##0.00'
        if row.get("cost") is not None:
            ws[f"{col['Cost CHF']}{n}"] = float(row["cost"])
        ws[f"{col['Cost CHF']}{n}"].number_format = '#,##0.00'
        ws[f"{col['Size / variant']}{n}"] = row.get("size") or ""
        ws[f"{col['Photo?']}{n}"] = "yes" if row.get("has_image") else "no"
        ws[f"{col['Text?']}{n}"] = "yes" if row.get("has_text") else "no"

        # the operator's real workflow, one click
        if name:
            link = ws[f"{col['Look it up']}{n}"]
            link.value = "🔎 Google"
            link.hyperlink = f"https://www.google.com/search?q={quote_plus(name)}"
            link.font = Font(color="0563C1", underline="single", size=10)

        ws[f"{col['Action']}{n}"] = "ENRICH"
        # Status formula: ready only when the human bits are in
        ws[f"{col['Status']}{n}"] = (
            f'=IF({col["Action"]}{n}="SKIP","⏭ skip",'
            f'IF(AND({col["Product name"]}{n}<>"",{col["Price CHF"]}{n}>0,{col["Category"]}{n}<>""),"✅ ready",'
            f'IF({col["Product name"]}{n}="","❌ no name","⏳ needs work")))'
        )
        for h in ("Status", "SKU", "Photo?", "Text?"):
            ws[f"{col[h]}{n}"].fill = locked_fill
        for h in ("Photo?", "Text?", "Status"):
            ws[f"{col[h]}{n}"].alignment = Alignment(horizontal="center")

    last = max(len(rows) + 1, 2)

    # dropdowns — the funnel, enforced at the point of entry
    dv_cat = DataValidation(type="list", formula1=f"=Lists!$A$2:$A${len(CANONICAL_CATEGORIES)+1}",
                            allow_blank=True, showDropDown=False)
    dv_cat.error = "Pick a category from the list — new categories are not allowed here."
    dv_cat.errorTitle = "Use the dropdown"
    ws.add_data_validation(dv_cat)
    dv_cat.add(f"{col['Category']}2:{col['Category']}{last}")

    dv_act = DataValidation(type="list", formula1=f"=Lists!$C$2:$C${len(ACTIONS)+1}",
                            allow_blank=True, showDropDown=False)
    ws.add_data_validation(dv_act)
    dv_act.add(f"{col['Action']}2:{col['Action']}{last}")

    # traffic lights on Status
    rng = f"{col['Status']}2:{col['Status']}{last}"
    ws.conditional_formatting.add(rng, FormulaRule(
        formula=[f'ISNUMBER(SEARCH("ready",{col["Status"]}2))'],
        fill=PatternFill("solid", fgColor=OK_BG), stopIfTrue=False))
    ws.conditional_formatting.add(rng, FormulaRule(
        formula=[f'ISNUMBER(SEARCH("needs",{col["Status"]}2))'],
        fill=PatternFill("solid", fgColor=WARN_BG), stopIfTrue=False))
    ws.conditional_formatting.add(rng, FormulaRule(
        formula=[f'ISNUMBER(SEARCH("no name",{col["Status"]}2))'],
        fill=PatternFill("solid", fgColor=BAD_BG), stopIfTrue=False))
    # highlight a missing price — the #1 thing only a human at the shelf can supply
    ws.conditional_formatting.add(f"{col['Price CHF']}2:{col['Price CHF']}{last}", FormulaRule(
        formula=[f'AND({col["Action"]}2<>"SKIP",OR({col["Price CHF"]}2="",{col["Price CHF"]}2=0))'],
        fill=PatternFill("solid", fgColor=WARN_BG), stopIfTrue=False))

    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUMNS))}{last}"

    # ---------------- Summary ----------------
    s = wb.create_sheet("Summary")
    _title(s, "📊 Progress", f"Live — it updates as you fill the Worklist · {stamp}")
    W = "Worklist"
    stats = [
        ("Products in this list", f'=COUNTA({W}!B2:B{last})'),
        ("✅ Ready to import", f'=COUNTIF({W}!A2:A{last},"*ready*")'),
        ("⏳ Still need work", f'=COUNTIF({W}!A2:A{last},"*needs*")'),
        ("⏭ Skipped", f'=COUNTIF({W}!A2:A{last},"*skip*")'),
        ("", ""),
        ("Barcodes captured 🔫", f'=COUNTA({W}!D2:D{last})'),
        ("Prices filled 💰", f'=COUNTIF({W}!F2:F{last},">0")'),
        ("Categories set 🗂", f'=COUNTA({W}!E2:E{last})'),
        ("", ""),
        ("Photos Banco already has 📷", f'=COUNTIF({W}!I2:I{last},"yes")'),
        ("Descriptions it already has ✍", f'=COUNTIF({W}!J2:J{last},"yes")'),
    ]
    r = 4
    for label, formula in stats:
        if label:
            s.cell(row=r, column=1, value=label).font = Font(size=11, color=INK)
            c = s.cell(row=r, column=2, value=formula)
            c.font = Font(size=13, bold=True, color=DARK)
            c.alignment = Alignment(horizontal="right")
        r += 1
    s.cell(row=r + 1, column=1, value="% ready").font = Font(size=11, bold=True, color=INK)
    pc = s.cell(row=r + 1, column=2, value=f'=IF(B4=0,0,B5/B4)')
    pc.number_format = "0%"
    pc.font = Font(size=18, bold=True, color=RED)
    pc.alignment = Alignment(horizontal="right")
    s.cell(row=r + 3, column=1,
           value="Work one shelf at a time. When this hits 100%, save and import it back into Banco.").font = \
        Font(size=10, italic=True, color=MUT)
    s.column_dimensions["A"].width = 34
    s.column_dimensions["B"].width = 14
    s.sheet_view.showGridLines = False

    wb.move_sheet("Lists", offset=3)
    lists.sheet_state = "hidden"
    wb.active = 0

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
