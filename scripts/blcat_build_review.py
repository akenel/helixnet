#!/usr/bin/env python3
"""BL-CAT.2 — build the Felix category-taxonomy review sheet (HTML test-script).

Reads the corrected draft mapping + the live prod samples, aggregates per canonical
category, and emits a self-contained HTML review sheet Angel walks Felix through.
Read-only: consumes JSON, writes one HTML file. Nothing touches prod.

  python3 scripts/blcat_build_review.py \
      --draft docs/banco-category-taxonomy-draft.json \
      --samples /tmp/blcat_samples.json \
      --out docs/testing/banco/BANCO-CATEGORY-TAXONOMY-REVIEW.html
"""
import argparse
import html
import json
from collections import defaultdict


def esc(s):
    return html.escape(str(s or ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", required=True)
    ap.add_argument("--samples", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    draft = json.load(open(a.draft, encoding="utf-8"))
    samples = json.load(open(a.samples, encoding="utf-8"))

    groups = {g["key"]: g for g in draft["groups"]}
    cats = {c["key"]: c for c in draft["canonical_categories"]}
    mapping = draft["mapping"]

    # Aggregate per canonical category: count + samples, from the raw strings that map to it.
    agg = defaultdict(lambda: {"count": 0, "samples": [], "raws": []})
    unmapped_prod = dict(samples)  # prod categories not covered by the mapping
    for m in mapping:
        raw, to = m["raw"], m["to"]
        live = samples.get(raw)
        cnt = live["n"] if live else m.get("count", 0)
        agg[to]["count"] += cnt
        agg[to]["raws"].append((raw, cnt, m.get("verified"), m.get("note"), m.get("verify")))
        if live:
            for s in live["samples"]:
                if s and s not in agg[to]["samples"]:
                    agg[to]["samples"].append(s)
        unmapped_prod.pop(raw, None)

    # Group totals (fresh from the aggregation)
    group_totals = defaultdict(int)
    for ck, data in agg.items():
        group_totals[cats[ck]["group"]] += data["count"]
    grand = sum(group_totals.values())

    # --- build HTML ---
    P = []
    P.append("""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Category Taxonomy — Felix Review</title><style>
:root{--green:#1a4d2e;--em:#10b981;--warn:#8B0000;--gold:#b8860b;}
*{box-sizing:border-box;}body{margin:0;font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#12261c;background:#eef4f0;line-height:1.5;}
header{background:radial-gradient(800px 380px at 30% -40%,#1c5138,#113024 60%,#0a1a14);color:#eafff2;padding:30px 26px;}
header .k{letter-spacing:.3em;text-transform:uppercase;font-size:12px;color:#7CFFB2;}
header h1{margin:6px 0 4px;font-size:30px;font-weight:900;}header .s{color:#bfe9cf;font-size:14px;}
.wrap{max-width:960px;margin:0 auto;padding:22px 20px 70px;}
.why{background:#fff;border-left:4px solid var(--em);border-radius:9px;padding:14px 18px;margin:16px 0;font-size:14px;color:#37473f;box-shadow:0 1px 3px rgba(0,0,0,.05);}
.fix{background:#fffdf3;border-left:4px solid var(--gold);border-radius:9px;padding:12px 18px;margin:16px 0;font-size:14px;}
.fix b{color:#8a6d0b;} .fix ul{margin:8px 0 0;padding-left:18px;} .fix li{margin:3px 0;}
h2{margin:30px 0 4px;font-size:21px;color:var(--green);display:flex;gap:10px;align-items:center;}
h2 .n{background:var(--green);color:#fff;border-radius:8px;padding:2px 10px;font-size:14px;}
h2 .ct{margin-left:auto;font-size:14px;color:#5a6b62;font-weight:600;}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.05);margin:8px 0 4px;}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid #eef2f0;font-size:13.5px;vertical-align:top;}
th{background:#f3f8f5;color:var(--green);font-size:12px;text-transform:uppercase;letter-spacing:.03em;}
td.cat{font-weight:700;white-space:nowrap;}td.cnt{text-align:right;font-weight:700;color:var(--green);white-space:nowrap;}
td.samp{color:#5a6b62;}td.samp span{display:inline-block;background:#f0f5f2;border-radius:5px;padding:1px 7px;margin:1px 3px 1px 0;font-size:12.5px;}
.flag{display:inline-block;font-size:11px;font-weight:700;padding:1px 6px;border-radius:5px;margin-left:6px;}
.flag.corr{background:#fef3c7;color:#92600b;} .flag.dec{background:#e0e7ff;color:#3730a3;}
.dec{background:#fff;border:2px solid #d9e6df;border-radius:12px;padding:16px 18px;margin:14px 0;}
.dec h3{margin:0 0 4px;font-size:16px;color:var(--green);}
.dec p{margin:0 0 8px;font-size:14px;color:#4a5a52;}
.dec label{display:block;padding:6px 10px;border:1px solid #dde7e2;border-radius:8px;margin:4px 0;font-size:14px;cursor:pointer;}
.dec label:hover{background:#f6faf8;} .dec .rec{border-color:var(--em);background:#effaf3;}
.signoff{background:var(--green);color:#eafff2;border-radius:12px;padding:16px 20px;margin-top:26px;font-size:15px;}
footer{text-align:center;color:#7a8b82;font-size:12px;padding:20px;}
@media print{.dec label{-webkit-print-color-adjust:exact;}}
</style></head><body>
<header><div class="k">HelixPOS · Banco · BL-CAT</div>
<h1>🗂️ Category Taxonomy — Felix Review</h1>
<div class="s">One clean 2-level tree to replace 61 messy German-slug categories. Verified against live prod 2026-07-16.</div></header>
<div class="wrap">""")

    P.append(f"""<div class="why"><b>What this is:</b> the shop's catalogue has <b>61 category names</b>, most of them
raw German URL-slugs ("Feuerzeuge", "Aufbewahrung") that mean nothing to an English/French customer, and
"papers" is split across ten of them. This proposes <b>ONE tidy tree</b> — {len(groups)} groups, {len(cats)} categories,
English as the hub, every old name kept as a hidden synonym (nothing is lost). <b>Category = the shelf sign only</b> —
it does NOT touch age-flags (18+) or VAT. Below: every group, its categories with a live item count and 3 real
products, then the {'six'} calls that are <b>yours</b>, Felix. Tick your choices; that's the sign-off.</div>""")

    P.append("""<div class="fix"><b>⚠ 4 fixes the live check caught (already corrected in the proposal):</b>
<ul>
<li><b>Oel Dabbing (157)</b> was filed as CBD oils — it's actually all <b>dab gear</b> (e-rigs, dabbers, silicone
containers). Moved to <b>Smoking Gear → Dab &amp; Concentrate Gear</b>.</li>
<li><b>Raw Produkte (9)</b> are <b>cones</b>, not papers → <b>Cones &amp; Tubes</b>.</li>
<li><b>Vape Co (17)</b> are CBD <b>vape pens</b> (disposable) → <b>Prefilled &amp; Disposables</b>.</li>
<li><b>Treats (7)</b> are the checkout <b>giveaway</b> items (sticker/lighter/lollipop) → <b>system</b>, not CBD edibles.</li>
</ul></div>""")

    # Groups + categories
    group_order = [g["key"] for g in draft["groups"]]
    for gk in group_order:
        g = groups[gk]
        cat_keys = [c["key"] for c in draft["canonical_categories"] if c["group"] == gk and c["key"] in agg]
        if not cat_keys:
            continue
        gt = group_totals[gk]
        P.append(f'<h2><span class="n">{esc(g["label_en"])}</span><span class="ct">{gt} items</span></h2>')
        P.append('<table><tr><th>Category</th><th style="text-align:right">Items</th><th>Real products in the shop</th></tr>')
        cat_keys.sort(key=lambda k: -agg[k]["count"])
        for ck in cat_keys:
            d = agg[ck]
            flags = ""
            for (raw, cnt, verified, note, verify) in d["raws"]:
                if verified and ("Corrected" in verified or "->" in verified):
                    flags = '<span class="flag corr">corrected</span>'
                if verify:
                    flags += '<span class="flag dec">Felix decides</span>'
            samp = "".join(f"<span>{esc(s)}</span>" for s in d["samples"][:3]) or "<i>—</i>"
            P.append(f'<tr><td class="cat">{esc(cats[ck]["label_en"])}{flags}</td>'
                     f'<td class="cnt">{d["count"]}</td><td class="samp">{samp}</td></tr>')
        P.append("</table>")

    # Decisions
    P.append(f'<h2><span class="n">Your calls, Felix</span></h2>')

    def dec(num, title, desc, options):
        h = [f'<div class="dec"><h3>{num}. {esc(title)}</h3><p>{desc}</p>']
        for opt, rec in options:
            h.append(f'<label class="{"rec" if rec else ""}"><input type="checkbox"> {opt}</label>')
        h.append("</div>")
        return "".join(h)

    P.append(dec(1, "“Marijuana” (203) — the shelf name",
                 "Legally it's CBD/hemp flower in CH. What should the shelf sign say?",
                 [("<b>CBD Flower</b> (recommended)", True), ("Hemp Flower", False),
                  ("Keep “Marijuana”", False)]))
    P.append(dec(2, "“Oel Dabbing” (157) — confirm the move",
                 "The live check showed it's all dab GEAR, not oils, so it moved to Dab &amp; Concentrate Gear. Confirm?",
                 [("<b>Confirm — all 157 → Dab &amp; Concentrate Gear</b> (recommended)", True),
                  ("Wait — some are real CBD oils, split those out", False)]))
    P.append(dec(3, f"Group count — {len(groups)} groups",
                 "9 top groups (CBD, Papers, Smoking Gear, Vape, Tobacco &amp; Shisha, Cafe, Lifestyle, Grow/Lab, System). Too many?",
                 [("<b>Keep 9</b> (recommended)", True),
                  ("Merge some (tell us which — e.g. fold Grow/Lab into Lifestyle)", False)]))
    P.append(dec(4, "“Zubehoer” (74) — the junk drawer",
                 "Generic “accessories,” but the live check showed it's mostly VAPE parts (coils, drip tips, wire, chargers).",
                 [("<b>Re-map → Vape Accessories</b> (recommended — that's what they mostly are)", True),
                  ("Keep as “Accessories (general)”", False),
                  ("Manually re-split by product during migration", False)]))
    P.append(dec(5, "“Stash Safes” (31)",
                 "Diversion safes disguised as everyday objects (battery, deo can, ring). Their own shelf, or tucked into Storage?",
                 [("Fold into <b>Storage &amp; Stash</b>", False),
                  ("<b>Give them their own “Stash Safes” shelf</b> (fun retail category)", False)]))
    P.append(dec(6, "Tobacco &amp; Shisha — together or apart?",
                 "Currently one group “Tobacco &amp; Shisha.” Split into two?",
                 [("<b>Keep together</b> (recommended)", True), ("Split into Tobacco / Shisha", False)]))
    P.append(dec(7, "Bonus: “Entertainment” (32) — it's books &amp; comics",
                 "Grow books, Freak Brothers comics, the Kiffer Lexikon. Rename the category?",
                 [("Keep “Entertainment &amp; Games”", False),
                  ("<b>Rename “Books &amp; Media”</b>", False)]))

    unmapped_note = ""
    if unmapped_prod:
        rows = ", ".join(f"{esc(k)} ({v['n']})" for k, v in unmapped_prod.items())
        unmapped_note = f'<div class="fix"><b>⚠ Coverage gap:</b> {len(unmapped_prod)} prod categories not in the map — {rows}. Handle before commit.</div>'
    P.append(unmapped_note)

    P.append(f"""<div class="signoff"><b>Sign-off:</b> tick your choices above. On your yes, the migration ships through
the normal gated ladder (backup-first, re-probed) as a separate, deliberate step — <b>nothing is written until you
approve this tree.</b> Coverage: {grand} of ~5,170 active products mapped across {len(agg)} categories.</div>""")

    P.append('</div><footer>BL-CAT · Category Taxonomy Review · Tigs + Angel · walk Felix through it, tick, sign off</footer></body></html>')

    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(P))
    print(f"wrote {a.out}")
    print(f"groups={len(group_totals)} categories={len(agg)} mapped_items={grand} unmapped_cats={len(unmapped_prod)}")


if __name__ == "__main__":
    main()
