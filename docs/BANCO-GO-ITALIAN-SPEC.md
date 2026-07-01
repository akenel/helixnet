# Banco — Go Italian: Language + Euro + IVA Spec

*Created 2026-07-01. Scope: make Banco POS presentable and correct for an Italian shop — Italian UI, Euro currency, Italian IVA. Grounded in an actual code map of `src/` (not a guess).*

---

## 0. Scope & non-scope

**In scope (this spec):**
1. **Language** — Italian UI for the POS (reuse the sibling i18n pattern already shipping in Camper & ISOTTO).
2. **Currency** — CHF → EUR: display, `it-IT` number format (`1.234,55`), Euro cash denominations, per-tenant currency.
3. **VAT → IVA** — generalize the two-rate Swiss engine to an N-rate Italian regime (22 / 10 / 5 / 4).

**Explicitly OUT of scope (deferred — separate work):**
- **Fiscal RT integration** — the *documento commerciale*, daily *corrispettivi telematici* transmission to Agenzia delle Entrate, and the 2026 POS↔RT linkage. Per the fiscalized-markets finding (2026-07-01), Banco does **not** become a certified RT; it **drives a rented certified fiscal engine** (fiskaly / Epson / Custom). That is an API-partnership project, not this spec. **This spec makes Banco Italian-*presentable*, not Italian-*fiscal-legal*.** Do not ship to a real Italian till on this spec alone.
- Multi-currency at point of sale (tourist pays EUR at a CHF shop) — related but separate; this spec is single-currency-per-tenant = EUR.

**Why this spec is still worth doing before the RT plug-in:** it's the 80% of the surface (UI, money, tax display/math) that has to be right regardless of *which* certified RT we rent, and every piece is reusable for Camper/ISOTTO Italian customers today. The RT plug-in bolts onto a Banco that already speaks Italian and euros.

---

## 1. Current state — the three seams (verdicts from the code map)

| Area | Verdict | Why |
|------|---------|-----|
| **Language** | 🔴 Single-language hardcoded — **biggest lift** | POS templates are 100% hardcoded English. i18n engine exists but was **never wired into Banco**. |
| **Currency** | 🟡 Data-driven seam exists but only ~30% used | `POS_CURRENCY`/`POS_LOCALE` config + `formatPrice()` are right; literal `'CHF '` leaks across ~13 templates + helpers + server. |
| **VAT** | 🟠 Rate *numbers* are data; rate *regime* is code | Engine is clean but structurally **two-rate** (standard/reduced + `cafe_split`). Italy needs **four** rates. Real refactor. |

**Key existing assets to reuse:**
- i18n pattern: `src/static/camper-i18n.js`, `src/static/isotto-i18n.js` (IT+EN dicts), `t()` helper + `data-i18n` sweep + `?lang=`/localStorage/JWT selection (`src/templates/isotto/base.html:116-172`). **Proven, copyable.**
- Money: Python `Decimal` end-to-end, quantized to cents ROUND_HALF_UP (`src/services/cash_shift_service.py:12-35`), JSON as strings. Sound — keep it.
- `formatPrice()` = `Intl.NumberFormat(POSConfig.locale, {style:'currency', currency:POSConfig.currency})` (`pos/base.html:643-648`). Flip locale+currency → `€ 1.234,55` for free, *for anything routed through it.*
- VAT engine is **injectable**: `resolve_vat_rate(..., standard_rate, reduced_rate)`, `_rates()` reads config; `PRODUCT_CLASSES[*]["vat"]` is the single source of truth for a product's rate policy.
- **No Swiss 5-cent (Rappen) rounding exists** — `money()` quantizes to `0.01`. Convenient: Italy bills to the cent, so nothing to remove.

---

## 2. Architecture decision — introduce a "Fiscal Regime"

The core move that makes all three areas clean instead of a pile of `if country == "IT"`: replace the scattered Swiss scalars with **one named Regime object**, selected per-tenant.

A **Fiscal Regime** bundles:
```
regime:            "CH" | "IT"            (selector)
currency:          "CHF" | "EUR"
locale:            "de-CH" | "it-IT"
vat_number_format: "CHE-XXX.XXX.XXX MWST" | "IT Partita IVA (11 digits)"
cash_denominations: [Swiss coins/notes] | [Euro coins/notes]
vat_rates:         [ {code, label, rate}, ... ]   # N rates, not 2 scalars
class_to_rate:     { product_class -> rate_code }  # replaces PRODUCT_CLASSES[*]["vat"]
consumption_rule:  "cafe_split" | "flat_restaurant_10" | "none"
```

- **CH regime:** EUR→CHF, `de-CH`, rates `[{A,standard,8.1},{B,reduced,2.6}]`, `cafe_split` (dine-in 8.1 / takeaway 2.6).
- **IT regime:** EUR, `it-IT`, rates `[{22,ordinaria,22},{10,ridotta,10},{5,ridotta,5},{4,minima,4}]`, restaurant food generally flat **10%** → `consumption_rule = flat_restaurant_10` (no dine-in/takeaway split). **⚠ The class→rate mapping for Italy MUST be confirmed by an Italian commercialista — do not invent which goods are 10 vs 5 vs 4.**

This maps cleanly onto the existing **per-tenant** direction ([[banco-multi-tenant]]) and the **vertical-packs** model ([[banco-vertical-packs]]): regime is tenant/country config, VAT numbers stay data.

---

## 3. Workstreams

### 3A. Currency (🟡 medium — do first, most visible, lowest risk)

1. **Add per-tenant currency/locale** to `src/db/models/store_settings_model.py` (currently has neither; `country` defaults `"Switzerland"`). Fields: `currency`, `locale` (+ regime — see 3C).
2. **Serve them** from `GET /api/v1/pos/config` (`pos_router.py:132-150`) — already returns `currency`/`locale` from global config; source from store_settings instead.
3. **Route ALL money display through `formatPrice`.** Kill the leaks:
   - `pos/base.html:862` `chf()` helper — delete or parametrize.
   - `pos/search.html:534-535` — duplicate `currency:'CHF'` formatter — remove, use `formatPrice`.
   - Sweep literal `'CHF '` in: `checkout.html`, `receipt.html`, `cash_count.html`, `customer_lookup.html`, `catalog.html`, `scan.html`, `receiving.html`, `shift.html`, `closeout.html`, `transactions.html`, `product_sales.html`.
   - Server strings: `pos_router.py` "CHF" in log lines + closeout variance message (`:4697`) + voucher/CRM comments (1279, 1289, 2463, 2642, 2719).
4. **Euro cash denominations** — `cash_shift_service.py:18-21` Swiss `DENOMS` → Euro (500/200/100/50/20/10/5 notes; 2/1 € + 50/20/10/5/2/1 cent coins). Mirror in `pos/shift.html:292`, `cash_count.html:171-173`, and `pos_router.py:5209-5210` labels. (Decide whether to stock 1/2-cent coins — most Italian shops don't; may cash-round to 5 cents *at tender only*, not on price.)

**Done-when:** a tenant flagged EUR/it-IT shows `€ 1.234,55` everywhere, counts a Euro drawer, and no `CHF` string survives a grep of `pos/`.

### 3B. Language (🔴 largest — mechanical, proven pattern)

1. **Create `src/static/pos-i18n.js`** modeled on `isotto-i18n.js` — `POS_STRINGS = { it:{...}, en:{...} }`. Seed generic keys from the sibling catalogs (`common.*`, nav, status). Author the POS-domain strings that don't exist yet: checkout, cash count, VAT/receipt, closeout, scan, receiving, reports.
2. **Wire the layer into `pos/base.html`** — copy the `t()` helper + language detection (`?lang=` → localStorage `pos_lang` → JWT `locale` → default) from `isotto/base.html:116-172`; include `pos-i18n.js`.
3. **Sweep every `pos/*.html`** — replace hardcoded English with `data-i18n="..."` attributes (auto-swapped on `DOMContentLoaded`) or `t()` calls. This is the bulk of the work; it's tedious, not hard.
4. **Language switcher** in `pos/settings.html` (mirror ISOTTO's `switchLanguage()`).

**Done-when:** `?lang=it` renders the whole POS in Italian; nothing falls back to raw English; an Italian native (Nino / ISOTTO's "Famous Guy") sanity-checks the strings.

**Note:** the "4 languages" claim in older notes is **not** in the code — catalogs are IT+EN only. Scope this as **IT + EN**; add DE/FR later if a customer needs them.

### 3C. VAT → IVA (🟠 real refactor — highest design risk, money-critical)

1. **Model:** replace the two `POS_VAT_RATE`/`POS_VAT_RATE_REDUCED` scalars (`config.py:131-134`) and the single `vat_rate` on `store_settings_model.py` with the **Regime rate table** (§2). Store per-tenant.
2. **Engine (`vat_resolver.py`):** generalize `split_vat` from exactly-two turnover streams to **N streams keyed by rate code**. Make `Consumption`/`cafe_split` one *consumption_rule* among several (`flat_restaurant_10`, `none`). Keep `contained_vat()` inclusive math (`G*r/(100+r)`) — it's rate-agnostic already.
3. **Class map (`catalog_taxonomy.py:75-95`):** `PRODUCT_CLASSES[*]["vat"]` policy strings (`standard`/`reduced`/`cafe_split`) → indirection through `regime.class_to_rate`. **⚠ Italian class→rate mapping needs a commercialista.**
4. **Display (two-code A/B → N codes):**
   - `receipt.html:132-179` — hardwired `A`=std / `B`=reduced legend → render one row per active rate code (`22/10/5/4`).
   - `reports.html:31-81`, `closeout.html:81-83,199-201` — Z-report/closeout VAT split → N rows.
   - VAT-number format `store_settings_model.py:117-120` — Swiss `CHE-… MWST` → Italian *Partita IVA*.

**Done-when:** an IT-regime tenant rings a mixed cart and the receipt + Z-report show correct per-rate IVA across 22/10/(5/4), reconciling exactly — **verified by the money-path e2e gate** (same rigor as the Swiss VAT proof; this is fiscal-correctness-critical). ⚠ Correct *display/math* ≠ *legal fiscal document* — that's the deferred RT plug-in.

---

## 4. Phasing

| Phase | Work | Rationale |
|-------|------|-----------|
| **P0** | Regime data model (§2) in config + store_settings, per-tenant, default = CH (no behavior change) | Foundation; ships invisibly, seams for the rest. Mirror the "seam now, build when tenant #2 is real" discipline from [[banco-multi-tenant]]. |
| **P1** | Currency sweep (3A) | Independent, visible, low-risk win. EUR shop looks right. |
| **P2** | Italian i18n (3B) | Independent, largest but mechanical. |
| **P3** | IVA regime (3C) | Hardest, money-critical, gated on P0. Needs commercialista + e2e gate. |
| **deferred** | RT fiscal plug-in (rented cert) | Separate API-partnership project. |

P1 and P2 are parallelizable once P0 lands. P3 last because it carries the fiscal risk and the external dependency (Italian accountant).

---

## 5. Honest flags

- **Fiscal legality is NOT in this spec.** A Banco that speaks Italian and euros and computes IVA is still **not** a legal Italian till until it drives a certified RT. Never let the polish of P1–P3 masquerade as compliance. (The seal lesson: don't close the ticket at "looks Italian.")
- **Italian tax law is not ours to invent.** The class→rate mapping (what's 22 vs 10 vs 5 vs 4) and the *Partita IVA* rules need an Italian commercialista sign-off, same as the Swiss Treuhänder gates the CH fiscal samples.
- **"4 languages" was aspirational** — code has IT+EN only. Scope honestly.
- **Money precision stays as-is** — Decimal/cents/strings is correct; do not refactor it.

---

## 6. Files to touch (index)

- **Config/model:** `src/core/config.py:131-136` · `src/db/models/store_settings_model.py:91-128` · `src/routes/pos_router.py:132-150` (+ CHF strings 1279/1289/2463/2642/2719/4697/5209-5210)
- **VAT engine:** `src/services/vat_resolver.py` (whole) · `src/services/catalog_taxonomy.py:75-95`
- **Money/denoms:** `src/services/cash_shift_service.py:12-35, 18-21`
- **Currency display:** `src/templates/pos/base.html:610-648, 862` · `search.html:534-535` · sweep `checkout/receipt/cash_count/customer_lookup/catalog/scan/receiving/shift/closeout/transactions/product_sales.html`
- **VAT display:** `src/templates/pos/receipt.html:132-179` · `reports.html:31-81` · `closeout.html:81-83, 199-201`
- **i18n (new):** `src/static/pos-i18n.js` (model on `isotto-i18n.js`) · wire into `src/templates/pos/base.html` · externalize strings across every `src/templates/pos/*.html`
