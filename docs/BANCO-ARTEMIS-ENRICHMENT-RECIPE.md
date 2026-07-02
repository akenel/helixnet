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

---

## 10. What "done right" looks like
A cashier searches "rolling ppaers" (fat-fingered) and finds RAW; browses a **clean** Headshop › Storage tree;
every smoking item is correctly 18+ with an auditable reason; nothing was lost from source; and re-running the
importer next month updates only what changed — without touching a single manager edit.

*Built once, thought through, tested in sandbox, retested until we're both happy — then it ships.*
