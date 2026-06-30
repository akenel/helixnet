#!/usr/bin/env python3
"""Artemis 'Papers & Co' ENRICHMENT sample — dry-run review artifact.

Pulls the Papers & Co group from the live Artemis webshop (English, languageId=3),
runs every item through the Banco enrichment recipe (src/services/catalog_enrichment),
and writes a side-by-side RAW -> ENRICHED review HTML for a human to eyeball.

This is step 2-3 of the gated process (docs/BANCO-ARTEMIS-ENRICHMENT-RECIPE.md §8):
  build the recipe -> SAMPLE run (dry-run, no DB) -> REVIEW artifact -> iterate.

HARD CONSTRAINTS (enforced): dry-run only — NO database writes, NO image downloads
(the review HOTLINKS the Artemis coverUrl), NO git commits. Stdlib + the in-tree
src.llm / src.services modules only.

LLM ACCESS (BYO-brain): the LLM (merchandising) step goes through src/llm/run_llm via
turbo_or_local("gpt-oss:120b", ...). Where it runs decides the brain:
  * inside helix-platform-sandbox on the box  -> BH_OLLAMA_KEY set -> Turbo gpt-oss:120b
  * a host with local Ollama up                -> local model
  * neither reachable                          -> RULES-ONLY: LLM fields show [LLM-pending]
The rules half (the bulk of the review value) always runs.

USAGE
  python scripts/import/artemis_enrich_sample.py --out scripts/import/artemis_sample_review.html --max 50
"""
from __future__ import annotations

import argparse
import asyncio
import html
import re
import sys
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# in-tree imports: repo root on path (for src.*) + this dir (for artemis_import)
_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import artemis_import as ai  # the existing importer (Http, discovery, product enumeration)
# Canonical home is src/services/catalog_enrichment.py. On a box where /app/src is a
# read-only mount, the module is dropped beside this runner instead — import either way.
try:
    from src.services.catalog_enrichment import (
        RawProduct, enrich_rules, llm_context, apply_llm, llm_enrich_batch,
        RECIPE_VERSION, SOURCE_PREFIX,
    )
except ImportError:
    from catalog_enrichment import (  # type: ignore
        RawProduct, enrich_rules, llm_context, apply_llm, llm_enrich_batch,
        RECIPE_VERSION, SOURCE_PREFIX,
    )

PAPERS_SLUG = "papers-co"
BATCH = 8

# §6a — the Artemis DETAIL page carries the rich metadata the LIST API omits:
#   * the full description in   <div ... id="Description"> ... </div>
#   * a spec table              <table class="Categorization"> <tr><td class="Title">K</td>
#                                                                 <td class="Name">V</td> ...
# We scrape both (one fetch per product; deltas-aware on the full run) and keep them
# verbatim as raw_facets + detail_description on the RawProduct.
_RX_DESC = re.compile(r'id="Description"[^>]*>(.*?)</div>', re.S | re.I)
_RX_FACET_ROW = re.compile(
    r'<td[^>]*class="Title"[^>]*>(.*?)</td>\s*<td[^>]*class="Name"[^>]*>(.*?)</td>', re.S | re.I)
_RX_TAG = re.compile(r"<[^>]+>")


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_RX_TAG.sub(" ", s or ""))).strip()


def fetch_detail(http: "ai.Http", source_url: str) -> tuple[str, dict]:
    """Fetch a product detail page and return (full_description, raw_facets).
    Best-effort: a 404 / parse miss returns ('', {}) — never fails the item."""
    if not source_url:
        return "", {}
    try:
        page = http.get_text(source_url, cacheable=False)
    except (urllib.error.HTTPError, urllib.error.URLError, Exception):
        return "", {}
    md = _RX_DESC.search(page)
    desc = _clean(md.group(1)) if md else ""
    facets: dict = {}
    for k, v in _RX_FACET_ROW.findall(page):
        key, val = _clean(k), _clean(v)
        if key and val:
            facets.setdefault(key, val)
    return desc, facets


# --------------------------------------------------------------------------- #
# Pull Papers & Co from Artemis                                               #
# --------------------------------------------------------------------------- #
def pull_papers(http: "ai.Http", lang: str, cap: int, with_detail: bool = True) -> list[RawProduct]:
    print(f"[1/4] discovering categories from sitemap ...", flush=True)
    cats = ai.discover_categories(http)
    papers_leaves = [c for c in cats if c.segments and c.segments[0] == PAPERS_SLUG and c.is_leaf]
    # if the group has no sub-levels, the group landing itself carries products
    if not papers_leaves:
        papers_leaves = [c for c in cats if c.segments and c.segments[0] == PAPERS_SLUG]
    print(f"      Papers & Co leaf categories: {len(papers_leaves)}", flush=True)

    print(f"[2/4] resolving product-API ids ...", flush=True)
    resolved = []
    for c in papers_leaves:
        if ai.resolve_category_api(http, c):
            resolved.append(c)
    print(f"      resolved={len(resolved)}", flush=True)

    print(f"[3/4] enumerating products ({lang.upper()}), round-robin across "
          f"subcategories for a representative spread ...", flush=True)
    # gather each category's product list first, then interleave round-robin so a single
    # large subcategory (e.g. 'blunts') doesn't swallow the whole sample.
    per_cat: list[list[dict]] = []
    for c in resolved:
        try:
            prods = list(ai.iter_category_products(http, c, lang, max_pages=200))
            if prods:
                per_cat.append([(c, p) for p in prods])
        except Exception as e:
            print(f"      ! category {c.breadcrumb}: {e}", flush=True)

    seen: dict[str, RawProduct] = {}
    idx = 0
    while len(seen) < cap and any(per_cat):
        bucket = per_cat[idx % len(per_cat)]
        if bucket:
            c, p = bucket.pop(0)
            ident = p.get("identifier")
            ident = str(ident).strip() if ident is not None else ""
            name = (p.get("name") or "").strip()
            if ident and name and ident not in seen:
                cover = p.get("coverUrl") or ""
                image_url = (ai.BASE + cover) if cover.startswith("/") else (cover or None)
                link = p.get("linkUrl") or ""
                source_url = (ai.BASE + link) if link.startswith("/") else link
                seen[ident] = RawProduct(
                    identifier=ident, name=name, price_text=p.get("salesPriceText"),
                    group=c.banco_group, group_slug=c.segments[0],
                    artemis_path=c.breadcrumb, artemis_segments=list(c.segments),
                    image_url=image_url, source_url=source_url, source_lang=lang,
                    source_id=p.get("id"), facets={},
                )
        idx += 1
        if all(not b for b in per_cat):
            break
    raws = list(seen.values())
    print(f"      unique products pulled: {len(raws)} (cap {cap})", flush=True)

    # §6a rich-metadata pass: one detail fetch per product (sample is small + cheap).
    if with_detail:
        print(f"[3b] fetching detail pages for rich metadata ({len(raws)}) ...", flush=True)
        n_desc = n_facets = 0
        for i, r in enumerate(raws, 1):
            desc, facets = fetch_detail(http, r.source_url or "")
            r.detail_description = desc or None
            r.facets = facets
            n_desc += 1 if desc else 0
            n_facets += 1 if facets else 0
            if i % 10 == 0:
                print(f"      detail {i}/{len(raws)} ...", flush=True)
        print(f"      detail pages: {n_desc}/{len(raws)} with description, "
              f"{n_facets}/{len(raws)} with spec facets", flush=True)
    return raws


# --------------------------------------------------------------------------- #
# Enrich (rules everywhere; LLM where reachable)                              #
# --------------------------------------------------------------------------- #
async def enrich_all(raws: list[RawProduct]) -> tuple[list, dict]:
    print(f"[4/4] enriching {len(raws)} items (rules) + LLM merchandising pass ...", flush=True)
    records = [enrich_rules(r) for r in raws]
    ctxs = [llm_context(r) for r in raws]

    meta = {"llm_method": None, "llm_model": None, "llm_ok": False, "llm_error": None,
            "n_llm_resolved_category": 0}

    # resolve the brain target
    from src.llm.targets import turbo_or_local
    import os
    target = turbo_or_local("gpt-oss:120b", "tinyllama:latest")
    has_key = bool(os.getenv("BH_OLLAMA_KEY"))
    meta["llm_method"] = (
        f"Turbo ({target.model} @ {target.base_url}) — BH_OLLAMA_KEY present"
        if has_key else
        f"local Ollama ({target.model} @ {target.base_url}) — no Turbo key"
    )

    # build LLM batch payload from rules records
    payload = []
    for rec, ctx in zip(records, ctxs):
        payload.append({
            "sku": rec.sku, "name": rec.source["raw_name"], "group": rec.group,
            "artemis_path": rec.source["artemis_path"], "attributes": rec.attributes,
            "allowed": ctx.get("allowed"),
        })

    llm_results: dict = {}
    model_used = None
    try:
        import httpx
        async with httpx.AsyncClient(timeout=target.timeout) as client:
            for i in range(0, len(payload), BATCH):
                chunk = payload[i:i + BATCH]
                out, model_used = await llm_enrich_batch(chunk, target, client=client)
                llm_results.update(out)
                print(f"      LLM batch {i//BATCH + 1}: {len(out)}/{len(chunk)} items", flush=True)
        meta["llm_ok"] = True
        meta["llm_model"] = model_used
    except Exception as e:
        meta["llm_ok"] = False
        meta["llm_error"] = f"{type(e).__name__}: {e}"
        print(f"      LLM unreachable -> RULES-ONLY ({meta['llm_error']})", flush=True)

    # fold LLM onto rules
    for rec, ctx in zip(records, ctxs):
        row = llm_results.get(rec.sku) if meta["llm_ok"] else None
        before = rec.category
        apply_llm(rec, row, model_used, ctx)
        if ctx.get("must_resolve_category") and rec.category != before:
            meta["n_llm_resolved_category"] += 1

    return records, meta


# --------------------------------------------------------------------------- #
# Review HTML                                                                 #
# --------------------------------------------------------------------------- #
def _counter(items):
    out = {}
    for x in items:
        out[x] = out.get(x, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def _chip(text, kind="tag"):
    return f'<span class="chip {kind}">{html.escape(str(text))}</span>'


def render_html(records: list, meta: dict, lang: str) -> str:
    n = len(records)
    by_cat = _counter([r.category for r in records])
    by_class = _counter([r.behavior_class for r in records])
    n_age = sum(1 for r in records if r.age_restricted)
    n_review = sum(1 for r in records if "needs_review" in r.flags)
    n_descpend = sum(1 for r in records if "needs_description" in r.flags)
    n_transl = sum(1 for r in records if "needs_translation" in r.flags)
    n_src_desc = sum(1 for r in records if r.confidence.get("description", 0) >= 1.0)
    n_facets = sum(1 for r in records if (r.attributes or {}).get("raw_facets"))
    n_attrs_total = sum(len([k for k in (r.attributes or {}) if k != "raw_facets"]) for r in records)
    avg_attrs = (n_attrs_total / len(records)) if records else 0
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def kv_table(d):
        return "".join(f"<tr><td>{html.escape(k)}</td><td class='num'>{v}</td></tr>" for k, v in d.items())

    rows = []
    for r in records:
        s = r.source
        thumb = (f'<img class="thumb" src="{html.escape(s["image_url"])}" loading="lazy" '
                 f'alt="" referrerpolicy="no-referrer">' if s.get("image_url") else
                 '<div class="thumb noimg">no image</div>')
        raw_price = html.escape(s.get("raw_price_text") or "—")
        link = s.get("url") or "#"
        flags_html = "".join(_chip(f, "flag") for f in r.flags) or '<span class="muted">clean</span>'
        tags_html = "".join(_chip(t) for t in r.tags)
        age_badge = ('<span class="chip age">18+</span>' if r.age_restricted
                     else '<span class="chip ok">no age gate</span>')
        cls_badge = _chip(r.behavior_class, "cls")
        cconf = r.confidence.get("category", 0)
        conf_cls = "good" if cconf >= 0.85 else ("mid" if cconf >= 0.6 else "low")
        # §6a attributes bag — normalized keys (raw_facets shown verbatim, collapsed)
        attrs = dict(r.attributes or {})
        raw_facets = attrs.pop("raw_facets", None)
        attr_rows = "".join(
            f"<tr><td class='ak'>{html.escape(str(k))}</td>"
            f"<td class='av'>{html.escape(str(v))}</td></tr>"
            for k, v in attrs.items())
        attrs_html = (f"<table class='attrs'>{attr_rows}</table>" if attr_rows
                      else "<span class='muted'>none mined</span>")
        if raw_facets:
            rf = " · ".join(f"{html.escape(str(k))}={html.escape(str(v))}" for k, v in raw_facets.items())
            attrs_html += (f"<details class='rawfacets'><summary>raw_facets "
                           f"({len(raw_facets)}, verbatim)</summary>{rf}</details>")
        desc_src = ("source detail page" if r.confidence.get("description", 0) >= 1.0
                    else ("LLM draft" if r.description and not r.description.startswith("[LLM")
                          else "—"))
        rows.append(f"""
        <tr>
          <td class="raw">
            <a href="{html.escape(link)}" target="_blank" rel="noopener">{thumb}</a>
            <div class="rawname">{html.escape(s.get('raw_name',''))}</div>
            <div class="path">{html.escape(s.get('artemis_path',''))}</div>
            <div class="rawprice">{raw_price}</div>
          </td>
          <td class="enriched">
            <div class="line"><span class="lbl">SKU</span> <code>{html.escape(r.sku)}</code></div>
            <div class="line"><span class="lbl">Group › Category</span>
                 <b>{html.escape(r.group)}</b> › <b>{html.escape(r.category)}</b>
                 <span class="conf {conf_cls}">cat {cconf:.2f}</span></div>
            <div class="line"><span class="lbl">Compliance</span> {age_badge} {cls_badge}
                 <span class="reason">{html.escape(r.age_reason)}</span></div>
            <div class="line"><span class="lbl">Price</span>
                 {('CHF ' + html.escape(r.price)) if r.price else '<span class="flag chip">no price</span>'}</div>
            <div class="line desc"><span class="lbl">Description</span>
                 {html.escape(r.description)}
                 <span class="reason">({html.escape(desc_src)})</span></div>
            <div class="line"><span class="lbl">Attributes</span> {attrs_html}</div>
            <div class="line"><span class="lbl">Tags</span> <div class="tags">{tags_html}</div></div>
            <div class="line"><span class="lbl">Flags</span> {flags_html}</div>
          </td>
        </tr>""")

    llm_banner_cls = "ok" if meta["llm_ok"] else "warn"
    llm_status = (f'LLM ON — {html.escape(meta.get("llm_model") or "")}'
                  if meta["llm_ok"] else
                  f'RULES-ONLY (LLM unreachable: {html.escape(meta.get("llm_error") or "")})')

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Banco · Artemis "Papers &amp; Co" enrichment review</title>
<style>
 :root {{ --red:#8B0000; --ink:#1d2125; --mut:#6b7280; --line:#e5e7eb; --bg:#f7f7f5; }}
 * {{ box-sizing:border-box; }}
 body {{ font:14px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; color:var(--ink);
        margin:0; background:var(--bg); }}
 header {{ background:#fff; border-bottom:3px solid var(--red); padding:18px 24px; }}
 h1 {{ margin:0 0 4px; font-size:20px; }}
 .sub {{ color:var(--mut); font-size:13px; }}
 .wrap {{ padding:20px 24px 60px; }}
 .summary {{ display:flex; flex-wrap:wrap; gap:16px; margin-bottom:18px; }}
 .card {{ background:#fff; border:1px solid var(--line); border-radius:10px; padding:14px 16px; min-width:180px; }}
 .card h3 {{ margin:0 0 8px; font-size:12px; text-transform:uppercase; letter-spacing:.05em; color:var(--mut); }}
 .big {{ font-size:26px; font-weight:700; }}
 table.kv {{ border-collapse:collapse; font-size:13px; }}
 table.kv td {{ padding:2px 10px 2px 0; }}
 table.kv td.num {{ text-align:right; font-variant-numeric:tabular-nums; color:var(--red); font-weight:600; }}
 .banner {{ padding:10px 14px; border-radius:8px; font-weight:600; margin-bottom:16px; }}
 .banner.ok {{ background:#e8f5e9; color:#1b5e20; border:1px solid #a5d6a7; }}
 .banner.warn {{ background:#fff4e5; color:#8a5300; border:1px solid #ffcc80; }}
 table.grid {{ width:100%; border-collapse:collapse; background:#fff; border:1px solid var(--line);
              border-radius:10px; overflow:hidden; }}
 table.grid thead th {{ text-align:left; background:#fafafa; border-bottom:2px solid var(--line);
              padding:10px 14px; font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:var(--mut); }}
 table.grid td {{ vertical-align:top; padding:14px; border-bottom:1px solid var(--line); }}
 td.raw {{ width:300px; border-right:1px solid var(--line); background:#fcfcfb; }}
 .thumb {{ width:120px; height:120px; object-fit:contain; background:#fff; border:1px solid var(--line);
          border-radius:8px; }}
 .thumb.noimg {{ display:flex; align-items:center; justify-content:center; color:var(--mut); font-size:12px; }}
 .rawname {{ font-weight:600; margin-top:8px; }}
 .path {{ color:var(--mut); font-size:12px; font-family:ui-monospace,monospace; margin-top:2px; }}
 .rawprice {{ margin-top:4px; color:var(--red); font-weight:600; }}
 .line {{ margin-bottom:6px; }}
 .line.desc {{ background:#fbfbf8; padding:6px 8px; border-left:3px solid var(--red); border-radius:0 6px 6px 0; }}
 .lbl {{ display:inline-block; min-width:120px; color:var(--mut); font-size:11px; text-transform:uppercase;
        letter-spacing:.04em; vertical-align:top; }}
 code {{ background:#f1f1ef; padding:1px 6px; border-radius:5px; }}
 .chip {{ display:inline-block; padding:1px 8px; margin:1px 2px; border-radius:999px; font-size:11px;
         background:#eef1f4; color:#333; }}
 .chip.flag {{ background:#fde2e2; color:#9b1c1c; }}
 .chip.age {{ background:#9b1c1c; color:#fff; }}
 .chip.ok {{ background:#e8f5e9; color:#1b5e20; }}
 .chip.cls {{ background:#e7e0ff; color:#4527a0; }}
 .tags {{ display:inline-block; max-width:520px; }}
 .reason {{ color:var(--mut); font-size:12px; font-family:ui-monospace,monospace; }}
 table.attrs {{ border-collapse:collapse; font-size:12px; margin-top:2px; }}
 table.attrs td {{ padding:1px 10px 1px 0; vertical-align:top; }}
 table.attrs td.ak {{ color:var(--mut); white-space:nowrap; }}
 table.attrs td.av {{ font-weight:600; }}
 details.rawfacets {{ margin-top:4px; font-size:11px; color:var(--mut); }}
 details.rawfacets summary {{ cursor:pointer; color:#4527a0; }}
 .conf {{ font-size:11px; padding:1px 6px; border-radius:5px; margin-left:4px; }}
 .conf.good {{ background:#e8f5e9; color:#1b5e20; }}
 .conf.mid {{ background:#fff4e5; color:#8a5300; }}
 .conf.low {{ background:#fde2e2; color:#9b1c1c; }}
 .muted {{ color:var(--mut); }}
</style></head>
<body>
<header>
  <h1>Banco catalog enrichment — RAW → ENRICHED review</h1>
  <div class="sub">Source: Artemis Luzern · group <b>Papers &amp; Co</b> · language {lang.upper()} (id 3)
    · recipe v{RECIPE_VERSION} · SKU prefix <code>{SOURCE_PREFIX}-</code> · generated {now}
    · <b>dry-run</b> (no DB writes, no image downloads, thumbnails hotlinked)</div>
</header>
<div class="wrap">
  <div class="banner {llm_banner_cls}">Brain: {llm_status}
     &nbsp;·&nbsp; LLM access: {html.escape(meta.get('llm_method') or '')}
     &nbsp;·&nbsp; LLM-resolved categories: {meta['n_llm_resolved_category']}</div>

  <div class="summary">
    <div class="card"><h3>Products</h3><div class="big">{n}</div>
       <div class="muted">{n_age} age-restricted (18+)</div></div>
    <div class="card"><h3>Clean categories</h3><table class="kv">{kv_table(by_cat)}</table></div>
    <div class="card"><h3>Behaviour class</h3><table class="kv">{kv_table(by_class)}</table></div>
    <div class="card"><h3>Flags</h3><table class="kv">{kv_table({'needs_review':n_review,'needs_description':n_descpend,'needs_translation':n_transl})}</table></div>
    <div class="card"><h3>Rich metadata (§6a)</h3><table class="kv">{kv_table({'detail descriptions':n_src_desc,'with spec facets':n_facets,'avg attrs/item':round(avg_attrs,1)})}</table></div>
  </div>

  <table class="grid">
    <thead><tr><th>RAW (Artemis source)</th><th>ENRICHED (Banco record)</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</div>
</body></html>"""


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Artemis Papers & Co enrichment sample (dry-run review).")
    ap.add_argument("--out", default=str(Path(__file__).with_name("artemis_sample_review.html")))
    ap.add_argument("--max", type=int, default=50, help="cap products (default 50)")
    ap.add_argument("--lang", default="en", choices=list(ai.LANG_IDS))
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--no-detail", action="store_true",
                    help="skip the §6a detail-page rich-metadata fetch (faster, basics only)")
    args = ap.parse_args()

    http = ai.Http(delay=args.delay, retries=4, cache_dir=None)  # no on-disk cache (dry-run)
    raws = pull_papers(http, args.lang, args.max, with_detail=not args.no_detail)
    if not raws:
        print("No products pulled — aborting.", file=sys.stderr)
        sys.exit(2)

    records, meta = asyncio.run(enrich_all(raws))
    out_html = render_html(records, meta, args.lang)
    Path(args.out).write_text(out_html, encoding="utf-8")

    # console summary
    print("\n" + "=" * 64)
    print(f" ENRICHMENT SAMPLE — Papers & Co  ({len(records)} products)")
    print("=" * 64)
    print(f" LLM: {'ON ' + str(meta.get('llm_model')) if meta['llm_ok'] else 'RULES-ONLY (' + str(meta.get('llm_error')) + ')'}")
    print(f" LLM access     : {meta.get('llm_method')}")
    print(f" categories     : {_counter([r.category for r in records])}")
    print(f" classes        : {_counter([r.behavior_class for r in records])}")
    print(f" age-restricted : {sum(1 for r in records if r.age_restricted)}/{len(records)}")
    print(f" needs_review   : {sum(1 for r in records if 'needs_review' in r.flags)}")
    print(f" needs_descr    : {sum(1 for r in records if 'needs_description' in r.flags)}")
    print(f" http requests  : {http.n_requests}")
    print(f" review HTML    : {args.out}")
    print("=" * 64)
    print(" DRY-RUN: nothing written to the DB, no images downloaded.")


if __name__ == "__main__":
    main()
