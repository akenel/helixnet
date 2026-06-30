# Banco Catalog Enrichment Recipe — Spec

*Status: PLAN (pre-build). Think it through here, on paper, before a single item lands.*
*Owner: Angel + Tig. Target: sandbox first, gated review, then prod.*

---

## 1. The principle

Pulling ~5,641 rows from Artemis is the easy 10%. **The enrichment is the 90% that has value.**
So we do not *dump* the catalog — we run every item through an **enrichment recipe** on the way in:
classify it, place it in a *clean* hierarchy (better than Artemis's), flag it, tag it, draft a
description — and keep the raw source **losslessly** so nothing is ever thrown away.

This is not new machinery. The platform already has **recipes (procedure-as-code) + the LLM layer**
(`src/llm/run_llm`, BYO-brain). The enrichment is **one recipe, run per item.**

**Source-agnostic by design:** the recipe's input is a *normalized raw product record*. Artemis is the
first feeder; FourTwenty (or any future source) feeds the *same* recipe. Importers normalize; the recipe enriches.

---

## 2. The two axes (the most important rule in this doc)

| Axis | What it is | Who decides | Tolerance for error |
|------|-----------|-------------|---------------------|
| **Compliance** — `behavior_class`, `age_restricted` | money + law (VAT class, 18+) | **RULES decide. LLM only *suggests* on ambiguous items. Human/fiscal signs off.** | **Zero.** A wrong legal flag is a real problem. |
| **Merchandising** — `category`, `tags`, `description` | how it's found + shown | **LLM + mapping**, bounded by a strict schema | Low. A wrong category is a UX annoyance, fixable, not illegal. |

> **The LLM is never the lawyer.** Age/class come from deterministic rules (`catalog_taxonomy.classify()`
> + a per-group age policy). The model may *propose* a class for an unclear item, but a rule or a human
> confirms it. This keeps the legal axis auditable.

---

## 3. What the recipe produces per item (enrichment record)

```
# --- identity / lossless source (never overwritten) ---
sku                : "ART-21577"        # namespaced from Artemis identifier (no demo collision)
source             : { system: "artemis", id: <guid>, url: <linkUrl>,
                       artemis_path: "headshop/aufbewahrung/drehboxen",   # full 4-level path, verbatim
                       source_lang: "en", image_url: <coverUrl> }
# --- merchandising (LLM + mapping; loose) ---
group              : "Headshop"          # Banco level-1 (from Artemis lvl1)
category           : "Storage"           # clean Banco level-2 (consolidated, shopper-friendly)
tags               : ["brand:raw","material:hemp","size:50g","artemis:headshop/aufbewahrung/drehboxen", ...]
description         : "<short LLM draft from name + facets>"   # flagged needs_description if thin
attributes         : { size: "50g", material: "hemp", brand: "RAW", ... }   # mined
# --- compliance (RULES decide; auditable) ---
behavior_class     : "standard" | "cbd_hemp" | "cbd_open" | "alcohol" | "tobacco"
age_restricted     : true|false
age_reason         : "headshop-smoking-accessory"   # the RULE that set it (traceable)
# --- price / stock ---
price              : 1.90                 # parsed from salesPriceText "CHF 1.90"
cost               : null                 # not in source
stock_quantity     : 1                    # zero-perpetual (not gated)
# --- enrichment metadata ---
confidence         : { category: 0.9, class: 1.0(rule), description: 0.7 }
flags              : ["needs_translation"?, "needs_review"?, "needs_description"?]
enriched_by        : { model: "<id>", recipe_version: "1.0", run_id: ... }
```

**Lossless guarantee:** `source.artemis_path` + the raw record are always kept, so any later decision
(build the real categories table, re-map, re-translate) re-derives from source without re-pulling.

---

## 4. The clean hierarchy (we do NOT inherit Artemis's mess)

Artemis is 4 levels deep and hard to search (Angel: "a nightmare"). We keep its **7 groups** but build a
**clean, consolidated level-2** that a cashier can actually browse. Artemis lvl3–4 fold into `tags` +
`description` (lossless), so we lose nothing and gain a sane tree.

**Groups (level 1, ~1:1 with Artemis):** Headshop · CBD · Shisha · Vape & Co · Papers & Co · Lifestyle · Grow*
*(\*Grow is stale/404 on the site right now — import skips it, flagged, revisit when it's back.)*

**Level-2 (Banco category):** the recipe maps Artemis's ~63 lvl2 names into a tidy consolidated set per
group (e.g. Headshop → Bongs · Pipes · Grinders · Storage · Ashtrays · Scales · Cleaning · Accessories).
The mapping table is **reviewable + editable** — and you can reshape the tree (`make your own`). Anything
the recipe can't confidently place gets `category: "Unsorted"` + `needs_review` (never guessed silently).

---

## 5. Compliance policy (DRAFT — requires fiscal/Felix sign-off)

Per-group **default** age + class. This is a starting rule set, **explicitly pending Treuhänder review** —
the recipe applies it; a human confirms before prod.

| Group | Default age | Default class | Notes |
|-------|-------------|---------------|-------|
| Headshop | 18+ | standard | smoking paraphernalia |
| Papers & Co | 18+ | standard | smoking accessory |
| Shisha | 18+ | tobacco (tabak) / standard (hardware) | tobacco rate where applicable |
| Vape & Co | 18+ | tobacco/standard | nicotine liquids → review |
| CBD | 18+ | cbd_hemp (legal <1% THC) / cbd_open (review) | books may be non-restricted |
| Lifestyle | none (default) | standard | decoration/gifts/textiles — case by case |
| Grow | none (default) | standard | equipment |

Rules run first (`catalog_taxonomy.classify()` + this table). LLM only flags *exceptions* for human review
(e.g. a CBD item that looks like open-THC). **Every age flag stores `age_reason` (the rule that set it) for audit.**

---

## 6. Model, cost, and safety of a 5,641-item run

- **Model:** cheap/fast for per-item enrichment (Turbo `gpt-oss:120b` BYO-brain, or a smaller model) — the
  enrichment task is light (map + tag + 1-line description from short text). **Batch** several items per call.
- **Resumable + checkpointed:** a run can stop/resume; never re-does completed items.
- **Delta-aware:** re-runs only enrich **new/changed** SKUs (the importer's snapshot already does this) — you
  never re-pay to enrich the whole catalog.
- **Bounded output:** the LLM step uses a **StructuredOutput schema** (no free-form) so it can't drift.
- **Rough budget:** ~5.6k items, batched ~10/call ≈ ~560 calls for the first full run; trivial on re-runs (deltas only).
- **Vision is opt-in, not default:** for items whose *name* is too thin to enrich, the recipe can escalate to a
  **read-the-package** vision pass (OCR the front: size/brand/type) — but that's per-item-expensive, so it's a
  **flagged second tier**, not run on all 5,641. (This is the same "photo reads the package" idea from the live flow.)

---

## 6a. Rich metadata — grab the gazillion while we're here (ZPI rationale)

**In zero-perpetual, metadata IS the inventory intelligence.** No stock counts to lean on → the product
record's value is its *descriptive richness*. Capture it in the one pass; backfilling later is brutal.

- **Flexible `attributes` bag (JSON)** on the product: brand, material, size, weight, count, flavor,
  dimensions, color, variants, full description — **plus the raw source facets kept verbatim** (`raw_facets`)
  = lossless. The recipe **normalizes keys** (rules + LLM) so it's queryable; nothing is discarded.
- **Where it lives:** the products LIST API gives only basics (name/price/SKU/image). The **specific attribute
  values + full description live on the product DETAIL page** → one **detail fetch per product** (one-time;
  deltas after). It **folds into the same throttled job** (§10a) — same batch/backoff/delta discipline.
- **The payoff (later, all powered by this):** faceted search ("all hemp papers"), similar-products,
  attribute analytics ("hemp = 30% of paper sales"), the visual/snap flow, auto-tagging. **Cheap now, expensive to backfill.**
- **Cost discipline:** the detail fetch ~doubles the per-item work → it's why §10a's throttle matters; and
  it's **deltas-aware** (only re-fetch changed SKUs). Run it as a tier: basics first (fast), rich-metadata
  pass second, both inside the watched/throttled job.

## 6b. Per-type attributes · multi-image · minted codes + the printed scan catalog

**Attributes are per-TYPE, not fixed.** Papers (material, sheets/pack, length-cm) share nothing with a bong
(height, glass thickness, joint-size, percolator) or a vape (battery, capacity, resistance). So the recipe
carries a **per-category attribute template** — it knows *which* questions to ask per type — and the flexible
`attributes` bag (§6a) holds whatever's relevant. Thin types stay thin; deep types go deep. No rigid columns.

**Multiple images per product = our edge.** Most sources ship one stock photo. We keep **N images** (the
shop's own shots + the source cover). The snap flow already takes pictures — we just retain them all.

**Minted internal barcodes — this SOLVES the no-EAN finding.** Artemis carries no EAN. So we **mint our own
internal EAN-13** (private `20–29` prefix — a real, scannable code we own) for **every** product at import.
Result: the whole imported catalog becomes **scannable even though the source had no barcode.** This is
[[banco-bl97-house-scan-sheet]] (BL-97) — the internal-EAN-13 mechanism — extended from "a binder of unmarked
staples" to "the whole catalog."

**The printed scan catalog (the no-barcode bridge).** Until products carry their own codes, **print the
catalog 20–40 per page** (thumbnail + name + price + minted barcode), using the **same print engine as the
transaction reports**. The cashier **zaps items off the page** — manufacturer barcode or not. A few pages, not
500 labels.

**Closes the new-product loop too:** brand-new item not in the catalog → snap photo(s) → OpenCV clean →
read-the-package draft → **mint a code** → it's in the catalog *and* on the next printed sheet. No dead end,
no missing code. *(ZPI isn't "winging it" — it's pragmatic: a few catalog pages beats barcode-labelling 6,000 items.)*

## 6c. The catalog as funnel — category=type, binder, EAN+QR, postcards

**Category IS type.** Artemis hands us the category; the category *is* the product type, so it **drives the
per-type attribute template** (§6b) — we don't invent a type system, the source provides it. (Rolling Papers →
material/sheets/length; Bongs → height/joint-size/percolator.)

**The printed catalog is a maintainable BINDER, not a one-shot dump:**
- **Table of contents + per-category sections + page numbers** = navigable.
- **Deltas drive page reprints** — change a product → reprint *only that page/section*, slip it into the
  binder. Same delta engine as the till + the catalog. **A few pages, never the whole 6,000-item book.**
- Same print engine as the transaction reports; 20–40 items/page.

**Every item gets EAN *and* QR:**
- **EAN** (minted internal, §6b) → scan to **SELL** (works without a manufacturer barcode).
- **QR** → a **Banco-owned permalink to the item online** → **SHARE**. Catalog page prints name + barcode + QR.
  Peelable QR stickers for the product itself.

**The funnel click (this is the payoff):** with a catalog of items that each carry a photo, data, and a QR
permalink, **every item can become a postcard (UFA business) and a shareable La Piazza listing** — same code,
same permalink. The catalog seeds sharing + marketing, not just the till. The **publish bridge (Banco item →
La Piazza listing) is already ~80% wired** (`square_bridge.create_draft_listing`); the QR-as-permalink was
always the plan. The "Banksy" layer = the QR/share cards carry brand + art, not plain codes. See
[[banco-lapiazza-community-loop]] + [[helix-identity-architecture]] (Artemis Premium cutover).

> **One import → two payoffs: SELL (scan) and SHARE (QR → postcard → listing).** Roadmap, not all build-now —
> but real, because the pieces exist. Build order holds: enrich the catalog first; codes/QR/binder next;
> postcards/sharing after.

## 6d. Multilingual mechanics — shared core + per-language text "skin"

A product = **one language-independent CORE + N text skins.**
- **Core (stored once, shared):** price, EAN, QR, photo, behaviour-class, age-flag, attribute *values* (11 cm is
  11 cm in any language).
- **Skin (per language):** only the **name, description, labels** change. en / de / fr / it.

**Storage:** a per-language text layer keyed by `SKU + lang` — a `product_translations` table OR i18n JSON
(`name_i18n = {en, de, fr, it}`). *(Same migration as the attributes JSON column — do both at once.)* Each skin
carries **provenance: `source` (real, from Artemis) vs `machine` (AI-translated)** — so you always know which
German is the *real* German.

**Where skins come from — three taps:**
1. **Real DE + FR** → Artemis already has them → **re-run the importer with `languageId=2`/`=4`** → store as the
   `de`/`fr` skin. **Free (pure fetch, no AI).**
2. **IT** → not in Artemis → **LLM-translate** from EN/DE → store flagged `machine`. Rides the §10a throttle.
3. **Gaps** (the German stragglers) → same LLM-fill, flagged.

**Display:** POS picks the customer's language → shows that skin → **falls back to EN** if missing. Nothing breaks.

**The seam is already in:** the importer pulls per-`languageId`; the enrichment records `source_lang` +
`needs_translation`. So adding a language later = **"re-run + store the skin," not a redesign** — and it's
**deltas-aware** (re-running DE only touches changed text). Cost: **DE/FR free, IT/gaps = throttled AI.**

## 6e. Maintenance = fix the RECIPE + re-run, NOT a bulk-edit UI (YAGNI)

When enrichment is wrong systematically (the 18+ over-flag, inconsistent category names, a class
mistake), **fix it at the SOURCE — the recipe (rules + LLM prompt) — and re-run the import.** The importer is
**idempotent + delta-aware**, so a re-run re-enriches every affected product automatically and updates them in
place (respecting `sync_override` so manager edits survive). **The re-run IS the mass-update engine** — there
is no need to hand-patch 100 products.

- **Human judgment goes IN as a rule, not a UI:** "which items are 18+" = a curated rule / exception list in
  the recipe (e.g. pure storage/lifestyle ≠ auto-18+). A human sets the POLICY once; the re-run applies it to
  all ~6,000 + every future import. Policy-as-code, not click-50-checkboxes.
- **Bulk-edit / multi-select grid UI = YAGNI** (Angel's call, correct): agony to build (selection state, bulk
  actions, undo), Felix would rarely use it, and the recipe + re-run already does the bulk work. It's exactly
  the ERP bloat a pen-and-paper shop never needs. Per-product Edit covers the genuine one-offs.

## 7. The recipe as procedure-as-code

```
recipe: artemis-enrich  (v1.0)
  input : raw_product   # normalized: {name, artemis_path, facets, price_text, image_url, source_lang, ...}
  steps :
    1. parse_price        (rule)        -> Decimal
    2. classify_compliance(rule)        -> behavior_class, age_restricted, age_reason   # catalog_taxonomy + group policy
    3. map_category       (rule+LLM)    -> group, category (consolidated), confidence    # mapping table; LLM for ambiguous
    4. mine_tags          (rule)        -> tags[] (brand/material/size from name+facets+path)
    5. draft_description  (LLM, schema) -> description, needs_description?
    6. assemble + validate(rule)        -> enrichment record + flags + confidence
  output: enrichment record (section 3)
  guarantees: deterministic steps idempotent; LLM steps schema-bounded; lossless source preserved
```

LLM calls go through `run_llm` / a `model` field on the recipe (BYO-brain default Turbo). `<think>` blocks stripped.

---

## 8. The gated process (the safe path Angel asked for)

1. **Build** the recipe + wire it into `scripts/import/artemis_import.py` (enrich-then-stage, still `--commit`-gated).
2. **Sample run** — enrich a small slice (Papers group, or ~50 items) in **dry-run** (no DB writes).
3. **Review artifact** — emit a side-by-side **raw → enriched** table (HTML) so we eyeball category, class,
   age flag, tags, description per item.
4. **Iterate** — tune the mapping table / rules / prompt; re-run the sample. Repeat **until we're both happy.**
5. **Full enriched run → sandbox** (`--commit`), images to MinIO, deltas active.
6. **End-to-end test on sandbox** — search, scan, photo-flow, sell — with real products.
7. **Prod** — only on Angel's go, fiscal age-rules signed, backup gated.

Nothing reaches the DB until step 5, and nothing reaches prod until step 7.

---

## 9. Open decisions (carry from the dry-run)
1. **Categories table** — ship flat (`group`+`category` on ProductModel, path in tags) now; build the real
   `categories` table later from the lossless path. *(Recommend: flat now.)*
2. **Age policy** — section 5 is a DRAFT; needs Treuhänder/Felix sign-off before prod.
3. **Images** — hotlink for the sandbox test; download to MinIO (`pos-products/`) for the real load.
4. **SKU namespace** — `ART-<id>` to avoid demo collisions. *(Recommend: yes.)*
5. **Model choice** — Turbo vs a smaller model for the enrichment step; decide after the sample-run cost shows.
6. **Source link = feature** — keep `linkUrl` per item → a "View on Artemis" link in the live app (same shop,
   no conflict; doubles as a price-parity check). Free, already captured.
7. **Price parity (Felix's ask)** — price **auto-syncs from Artemis** via deltas (till = online). A manager
   override is preserved (`sync_override`) but **flagged as diverged** so parity is the default and overrides
   are deliberate + visible.
8. **Discounts — RESOLVED, no card feature needed.** Artemis "cards" are just a stated %-off → the cashier
   enters the % at checkout (Banco already does manual discount); big/loyal buyers ("Chuck Norris") get a
   **customer-level discount by name, not a card.** Banco's existing discount handling covers both — nothing to build.

---

## 10a. Operations — an ADMIN job, throttled and watchable (Angel's requirement)

The enrichment run is an **administrator** task (never a cashier action). It lives in the **admin/settings
area**, runs as a **throttled background job**, and is **watchable** — because hammering a free/cheap model
too fast risks getting **rate-limited or cut off**. Be fair; don't abuse.

**Built from what's already in the stack** (cheap): **RabbitMQ** (`pika`/`aio-pika`) + **Celery** +
**Redis** + **Flower** (a Celery monitor) are all present.

- **Throttle:** items enqueued; a **small, configurable batch** is consumed at a time — **default 50, hard
  ceiling ~100, admin-settable lower.** A **delay between batches** (e.g. 10–30s) keeps the rate gentle, with
  **exponential backoff on HTTP 429 / rate-limit** errors. ~5,641 items at this pace ≈ a couple of hours, no hammering.
- **Resumable:** a stopped/paused run resumes; the importer's **SKU snapshot deltas** mean re-runs only touch
  new/changed items — so a re-run is cheap and never re-pays.
- **Which model hits limits:** the **bulk enrichment runs on Turbo (`gpt-oss`)**, not Gemini — so **Google's
  hard free limits are NOT the import bottleneck** (Gemini is reserved for the live snap-photo *vision*, low
  volume). Turbo is paid but can still throttle us if abused → the batch+delay+backoff above keeps us fair.
- **Schedule:** admin can schedule re-runs (Celery-redbeat is in the stack); since re-runs are deltas-only,
  a nightly/weekly refresh is cheap.

**Monitor cockpit (new admin-settings tab):** beside the address/setup tab, a **"Catalog Sync" tab** showing
**queue depth · processed / total · current rate · errors · ETA · Pause/Resume.** Flower already exposes the
raw queue stats; we surface a clean read-only tab so Angel can *watch* a run and stop it if it misbehaves.

> Build order: this operations layer wraps the recipe **after** the enrichment *quality* is approved on the
> sample. Quality first, then the safe-delivery harness around it.

## 10c. Across environments — enrich ONCE, promote through the boxes

The three banco envs are **separate databases** (`banco_sandbox` / `banco_staging` / `banco_prod`) — **not a
unified DB.** Isolation by design (playing in sandbox can't touch prod), same as the 3 code envs.

**The expensive work — the AI enrichment — runs ONCE.** It produces a portable **enriched catalog artifact**
(the SKU-keyed snapshot carrying the full enriched record + translations). Then we **promote that same set
through the envs with a cheap copy** — we do NOT re-run the LLM per environment. It mirrors the code lifecycle:
**build the image once → deploy to each env**; here, **enrich once → load the artifact into each env.**

- **Languages ride along:** the `product_translations` rows are part of the artifact, so EN/DE/FR/IT travel
  *with* the catalog — nothing separate to manage per env.
- **Flow:** fill **sandbox** (build + test) → copy to **staging** (dress-rehearsal) → copy to **prod** (the only
  env that must be *current*; gets it **last**, gated behind fiscal/age sign-off + a backup).
- **Deltas:** Artemis changes → re-enrich only the changed SKUs (cheap) → promote just that delta to each box.
  Never re-enrich the whole 6,000.

**Status:** NOT built yet — the current load writes per-env. The "enrich-once → load-from-artifact (no LLM)"
promotion is the PLAN (a small build) for when we move past sandbox. It's *why* we don't waste AI per env.

## 10d. What "done right" looks like
A cashier searches "rolling ppaers" (fat-fingered) and finds RAW; browses a **clean** Headshop › Storage tree;
every smoking item is correctly 18+ with an auditable reason; nothing was lost from source; and re-running the
importer next month updates only what changed — without touching a single manager edit.

*Built once, thought through, tested in sandbox, retested until we're both happy — then it ships.*
