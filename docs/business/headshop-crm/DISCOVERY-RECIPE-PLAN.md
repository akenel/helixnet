# Head-Shop Discovery Recipe — CH (find the universe, then qualify)

*Goal: go from "20 shops Angel pasted off one Maps screen" → "the discoverable universe of
CH head-shops," deduped, enriched, and auto-scored by the existing scorecard, loaded into
Postino. The 20-shop qualify pass proved the back half; this adds the front half (discovery).*

## The honest truth up front
There is **no single registry of head-shops** in Switzerland. "All" = the *union of several
imperfect public sources*, deduplicated. A realistic, deduped, qualified yield is roughly
**150–400 solid candidates**. We log what each source contributed and flag what we likely
miss — no silent "we got everything" claim.

## Pipeline — multi-modal sweep → dedup → enrich → qualify → load

**1. DISCOVER** (several sources in parallel, each blind to the others — one angle finds
what another misses):
- **Aggregator directories** — high precision, already the right category, cheap to scrape:
  `hanfplatz.de` (CH head-shops), `cbd-maps.com`, `cbdx.ch/verkaufsstellen`,
  `cannaviva.ch` city lists. → shop name + city + link.
- **Swiss phone books by category** — `local.ch` / `search.ch`: "Headshop", "Growshop", "CBD".
- **Zefix keyword search** (free federal register API) — purpose contains
  Hanf / CBD / Headshop / Growshop → entity + officer names for free.
- **[optional] Google Places** — text search by category over a grid of CH cities. Highest
  recall (finds shops in no directory), but needs a paid API key.

**2. DEDUP + CANONICALIZE** — merge by normalized name+city, phone, domain, and UID. Keep a
`source_count` (a shop found by 3 sources is more certainly real and more likely open).

**3. ENRICH** — the method already proven on the 20: address (search.ch/local.ch),
website + email (LLM reads the Impressum), manager (Zefix/Moneyhouse). Per-field source +
confidence.

**4. QUALIFY** — apply the `QUALIFICATION.md` rubric → `qualify_score`, `tier`, `persona`.
Gates: working website + a named human. Everything self-sorts top-down.

**5. LOAD** — write the master CSV → seed Postino (idempotent upsert on a stable key).

## Reuse (most of this already exists)
- **Scorer:** `QUALIFICATION.md` — done.
- **Enrichment:** proven on the 20 shops (search.ch + Impressum + Zefix).
- **Sink:** Postino (`crm/`) — done.
- **Pattern:** the Artemis importer (`scripts/import/artemis_import.py`,
  `docs/BANCO-ARTEMIS-ENRICHMENT-RECIPE.md`) — same shape: dry-run → review → full run.
  BYO-brain `run_llm` for the LLM steps, `httpx` for fetch, Pydantic for shapes.

## Build shape (Python, rule 11)
`scripts/import/headshop_discover.py` — Typer CLI (`--source`, `--dry-run`, `--limit`,
`--out`), asyncio + httpx, Pydantic models, `run_llm` for Impressum-read + record-merge.
**Dry-run first** (like Artemis — never a blind full crawl), review a sample, then full.
Be a polite crawler: rate-limit, real user-agent, respect robots.

## Two forks — need your call
1. **Google Places API** — do we have / want a paid key (a big recall boost, finds shops in
   no directory), or run **free-sources-only** (aggregators + Zefix + phone books)?
2. **Scope of "head-shop"** — **strict** head/hemp/CBD/grow/vape core (precise, ~right
   audience), or **broad** including plain tobacconists / kiosks / snus (thousands of hits,
   mostly not our fit — noisy)?
