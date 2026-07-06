#!/usr/bin/env python3
"""
CH head-shop DISCOVERY recipe  (free sources, strict core; dry-run safe).

WHAT THIS DOES
--------------
Finds the discoverable universe of Swiss head-shops / grow-shops / CBD shops from
FREE, Swiss-by-construction sources, deduplicates them, and (optionally) enriches +
scores each with the qualification rubric before loading into Postino (the CRM).

    DISCOVER  ->  DEDUP  ->  ENRICH  ->  QUALIFY  ->  LOAD
    (this)        (this)     (--enrich) (--enrich)   (--commit)

Rubric:  docs/business/headshop-crm/QUALIFICATION.md
Plan:    docs/business/headshop-crm/DISCOVERY-RECIPE-PLAN.md
Sink:    crm/ (Postino) — seeded from the CSV this writes.

DECISIONS (2026-07-02): FREE sources only to start; STRICT core (head/hemp/CBD/grow/
vape), no plain tobacconists/kiosks.

PRIMARY SOURCE — search.ch tel API  (verified live 2026-07-02, NO API KEY)
--------------------------------------------------------------------------
    https://tel.search.ch/api/?was=<term>&pos=<start>
Returns an OpenSearch/Atom feed; each <entry> carries a <content> block with, on
separate lines: shop name, (often) a contact person, street, "ZIP City CANTON",
phone. Swiss-only by construction — no German/Austrian pollution. We sweep several
strict-core terms nationally, paginate each, and dedup by normalised name.

WHY NOT hanfplatz.de: it's a GERMAN directory whose CH pages are padded with DE/AT
and online-only shops — too noisy to tell Swiss from German. Left as an OPTIONAL
extra (--hanfplatz) only; not the backbone.

ZEFIX (federal register) needs a FREE API key (returns 401 without) — set ZEFIX_KEY
and pass --zefix to add authoritative CH entities + officer (manager) names.

SAFETY / RULE #11 (Python first)
--------------------------------
DRY-RUN IS THE DEFAULT and STDLIB-ONLY (urllib + argparse + csv): fetch, harvest,
dedup, write CSV. Heavier stages are lazy + gated:
    --enrich   website / email / manager per candidate (httpx + run_llm)
    --commit   upsert into Postino's DB   (run on the box)
"""
from __future__ import annotations

import argparse
import csv
import html
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

USER_AGENT = "Mozilla/5.0 (compatible; PostinoDiscovery/1.0; +postcard outreach research)"

# strict-core search terms for the search.ch national sweep
SEARCH_TERMS = [
    "headshop", "head shop", "growshop", "grow shop",
    "cbd", "hanf", "cannabis", "vaporizer",
]
# drop obvious non-fits that these broad terms drag in
EXCLUDE = re.compile(r"apotheke|drogerie|pharmaci|tankstelle|coop|migros|denner", re.I)

_UML = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "ae", "Ö": "oe",
                      "Ü": "ue", "é": "e", "è": "e", "ê": "e", "à": "a",
                      "â": "a", "ç": "c", "ß": "ss", "ô": "o", "î": "i"})


def _norm(s: str) -> str:
    s = (s or "").lower().strip().translate(_UML)
    s = re.sub(r"\b(gmbh|ag|sa|sarl|sagl|the|der|die|das)\b", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


@dataclass
class Candidate:
    name: str
    person: str = ""
    street: str = ""
    zip: str = ""
    city: str = ""
    canton: str = ""
    phone: str = ""
    website: str = ""
    url: str = ""
    sources: list[str] = field(default_factory=list)
    source_count: int = 0

    def key(self) -> str:
        return _norm(self.name)


def _fetch(url: str, timeout: float = 25.0, retries: int = 3) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (trusted CH hosts)
                charset = r.headers.get_content_charset() or "utf-8"
                return r.read().decode(charset, errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < retries:
                time.sleep(2.0 * (attempt + 1))  # back off — search.ch throttles bursts
                continue
            raise
        except urllib.error.URLError:
            if attempt < retries:
                time.sleep(2.0 * (attempt + 1))
                continue
            raise
    raise RuntimeError("unreachable")


# --------------------------------------------------------------- source: search.ch

_ENTRY = re.compile(r"<entry>.*?</entry>", re.S)
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.S)
_CONTENT = re.compile(r"<content[^>]*>(.*?)</content>", re.S)
_ALT = re.compile(r'<link href="([^"]+)"[^>]*rel="alternate"[^>]*type="text/html"')
_TOTAL = re.compile(r"totalResults>\s*(\d+)")
_ZIPCITY = re.compile(r"\b(\d{4})\s+([^\d\n<][^\n<]*?)\s+([A-Z]{2})\b")
_PHONE = re.compile(r"\*?\s*(0\d[\d ]{6,}\d)")


def _parse_entry(block: str) -> Candidate | None:
    tm = _TITLE.search(block)
    if not tm:
        return None
    name = html.unescape(tm.group(1)).strip()
    if not name or EXCLUDE.search(name):
        return None
    cm = _CONTENT.search(block)
    content = html.unescape(cm.group(1)) if cm else ""
    lines = [l.strip() for l in content.splitlines() if l.strip()]

    zc = _ZIPCITY.search(content)
    zip_, city, canton = (zc.group(1), zc.group(2).strip(), zc.group(3)) if zc else ("", "", "")
    ph = _PHONE.search(content)
    phone = ph.group(1).strip() if ph else ""

    street, person = "", ""
    if zc:
        for i, l in enumerate(lines):
            if l.startswith(zip_):
                if i >= 1:
                    street = lines[i - 1]
                # a non-numeric line between the name (line 0) and the street = a person
                for l2 in lines[1:max(1, i - 1)]:
                    if not re.search(r"\d", l2) and l2 != name:
                        person = l2
                        break
                break
    alt = _ALT.search(block)
    return Candidate(
        name=name, person=person, street=street, zip=zip_, city=city,
        canton=canton, phone=phone,
        url=alt.group(1) if alt else "",
    )


def searchch_term(term: str, limit: int | None) -> list[Candidate]:
    out: list[Candidate] = []
    pos, total, seen = 1, None, 0
    while True:
        url = f"https://tel.search.ch/api/?was={urllib.parse.quote(term)}&pos={pos}"
        try:
            body = _fetch(url)
        except Exception as e:
            print(f"    search.ch '{term}' pos={pos}: {type(e).__name__}", file=sys.stderr)
            break
        if total is None:
            tm = _TOTAL.search(body)
            total = int(tm.group(1)) if tm else 0
        blocks = _ENTRY.findall(body)
        if not blocks:
            break
        for b in blocks:
            c = _parse_entry(b)
            if c:
                c.sources = [f"search.ch:{term}"]
                out.append(c)
        seen += len(blocks)
        pos += len(blocks)
        if limit and len(out) >= limit:
            return out[:limit]
        if total and seen >= total:
            break
        if len(blocks) < 10:
            break
        time.sleep(1.2)  # be gentle — search.ch throttles fast pagination
    return out


def discover_searchch(limit: int | None) -> list[Candidate]:
    found: list[Candidate] = []
    for term in SEARCH_TERMS:
        batch = searchch_term(term, limit)
        print(f"  search.ch '{term}': {len(batch)}")
        found.extend(batch)
        time.sleep(0.4)
        if limit and len(found) >= limit:
            return found[:limit]
    return found


# --------------------------------------------------------------- source: Zefix (opt)

def zefix_search(terms: list[str]) -> list[Candidate]:
    """Free federal register — needs a FREE API key (ZEFIX_KEY). Returns [] if absent."""
    import json
    import os
    key = os.environ.get("ZEFIX_KEY", "")
    if not key:
        print("    zefix: no ZEFIX_KEY set — skipping (register free at zefix.ch)", file=sys.stderr)
        return []
    base = "https://www.zefix.ch/ZefixPublicREST/api/v1/firm/search.json"
    out: dict[str, Candidate] = {}
    for term in terms:
        body = json.dumps({"name": term, "activeOnly": True}).encode()
        req = urllib.request.Request(
            base, data=body,
            headers={"User-Agent": USER_AGENT, "Content-Type": "application/json",
                     "Authorization": f"Bearer {key}"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310
                data = json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:
            print(f"    zefix '{term}': {type(e).__name__}", file=sys.stderr)
            continue
        for row in (data.get("list") if isinstance(data, dict) else data) or []:
            name = row.get("name") or ""
            if not name or EXCLUDE.search(name):
                continue
            c = Candidate(name=name, city=row.get("legalSeat") or "", sources=[f"zefix:{term}"])
            out.setdefault(c.key(), c)
    return list(out.values())


# --------------------------------------------------------------- source: hanfplatz (opt/noisy)

_SHOP_LINK = re.compile(
    r'<a\b[^>]*href="(?P<href>/cbd-shop/[^"?#]+)"[^>]*>'
    r'(?P<text>(?:(?!</a>|<a\b).)*?)</a>', re.I | re.S)


def discover_hanfplatz(regions: list[str]) -> list[Candidate]:
    print("  (hanfplatz is a German directory — expect DE/AT/online noise; filter at enrich)")
    out: list[Candidate] = []
    for region in regions:
        for st in ("head-shop", "grow-shop"):
            url = f"https://hanfplatz.de/hanf-shops/{urllib.parse.quote(region, safe='-')}/{st}"
            try:
                page = _fetch(url)
            except Exception:
                continue
            for m in _SHOP_LINK.finditer(page):
                name = html.unescape(re.sub(r"<[^>]+>", " ", m.group("text"))).strip()
                if name and not EXCLUDE.search(name):
                    out.append(Candidate(name=name, url="https://hanfplatz.de" + m.group("href"),
                                         sources=[f"hanfplatz:{region}:{st}"]))
            time.sleep(0.6)
    return out


# --------------------------------------------------------------- dedup + output

def dedup(cands: list[Candidate]) -> list[Candidate]:
    merged: dict[str, Candidate] = {}
    for c in cands:
        k = c.key()
        if k in merged:
            m = merged[k]
            m.sources = sorted(set(m.sources) | set(c.sources))
            for fld in ("person", "street", "zip", "city", "canton", "phone", "website", "url"):
                if not getattr(m, fld) and getattr(c, fld):
                    setattr(m, fld, getattr(c, fld))
        else:
            merged[k] = c
    result = list(merged.values())
    for c in result:
        c.source_count = len(c.sources)
    result.sort(key=lambda x: (-x.source_count, x.name.lower()))
    return result


CSV_COLS = ["name", "person", "street", "zip", "city", "canton", "phone",
            "website", "source_count", "sources", "url"]


def write_csv(cands: list[Candidate], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CSV_COLS)
        for c in cands:
            w.writerow([c.name, c.person, c.street, c.zip, c.city, c.canton, c.phone,
                        c.website, c.source_count, "; ".join(c.sources), c.url])
    print(f"\nwrote {len(cands)} candidates -> {path}")


def enrich(cands: list[Candidate]) -> None:
    raise SystemExit(
        "--enrich not wired yet: review the discovered candidates first, then we build the\n"
        "enrich+score stage (website <- shop page, email <- Impressum via run_llm, manager\n"
        "<- Zefix; score/tier/persona <- QUALIFICATION.md).")


# --------------------------------------------------------------- CLI

def main() -> None:
    ap = argparse.ArgumentParser(description="Discover CH head-shops (search.ch; free, strict core).")
    ap.add_argument("--out", default="docs/business/headshop-crm/discovered-candidates.csv")
    ap.add_argument("--limit", type=int, default=None, help="cap per term (testing)")
    ap.add_argument("--zefix", action="store_true", help="also query Zefix (needs ZEFIX_KEY)")
    ap.add_argument("--hanfplatz", nargs="*", metavar="REGION",
                    help="also crawl hanfplatz for these regions (noisy DE directory)")
    ap.add_argument("--enrich", action="store_true", help="(heavy) website/email/manager + score")
    ap.add_argument("--commit", action="store_true", help="(box) upsert into Postino DB")
    args = ap.parse_args()

    print("DISCOVER — search.ch tel API (Swiss-only, free, strict core)\n")
    cands = discover_searchch(args.limit)
    if args.zefix:
        print("\nDISCOVER — Zefix register")
        cands += zefix_search(["headshop", "growshop", "hanf", "cbd"])
    if args.hanfplatz is not None:
        print("\nDISCOVER — hanfplatz (optional extra)")
        cands += discover_hanfplatz(args.hanfplatz or ["zürich", "bern", "luzern"])

    print(f"\nraw candidates: {len(cands)}")
    cands = dedup(cands)
    with_addr = sum(1 for c in cands if c.zip)
    with_person = sum(1 for c in cands if c.person)
    print(f"after dedup:    {len(cands)}   (with address: {with_addr}, with a person: {with_person}, "
          f"found by 2+ terms: {sum(1 for c in cands if c.source_count > 1)})")

    if args.enrich:
        enrich(cands)
    if args.commit:
        raise SystemExit("--commit: wire after --enrich review (Postino seed).")

    write_csv(cands, args.out)
    print("\nDRY-RUN complete. Review the CSV, then --enrich to score, then --commit to load Postino.")


if __name__ == "__main__":
    main()
