# Banco Go-Italian — Language + Euro + Regime Seam
### Swiss-working, EU-ready. Italy first.

*Execution plan synthesized 2026-07-01 from a 9-agent ultracode workflow (5 design deep-dives + 3 adversarial critiques + synthesis), grounded in the real code. Companion to `docs/BANCO-GO-ITALIAN-SPEC.md`. Doctrine: `[[banco-go-italian-doctrine]]`.*

## Executive Summary
1. **Make Banco Italian-*presentable* and Swiss-*working*** — Euro + Italian UI + a per-tenant fiscal-regime seam — **without touching the money math or claiming Italian fiscal legality.**
2. **Two cheap horizontal bricks ship now:** (1) currency/locale display, (2) EN/IT i18n. Both are additive; English + CHF stay the default and byte-identical.
3. **The expensive vertical (Italian IVA N-rate engine + RT fiscal cert) is DEFERRED** — held until a real Italian shop signs and a commercialista signs off. We build the *seam*, not the tax law.
4. **Scope is the 5-minute demo path, one screen at a time**, currency + language in a single pass so every shipped screen is *fully* done — the deliverable is *"Banco demos in Italian with Euros; Switzerland is unchanged."*
5. **This is a demand-enabler, not a build-for-a-signed-customer.** Felix is proof-of-concept, not the plan. Depth over breadth: architect for many countries, ship only Italy.

## Doctrine Compass (every task honors these)
- **LANGUAGE = cheap horizontal** — string catalog, do-one-do-all, EN+IT now, DE/FR trivial later.
- **FISCAL = expensive vertical** — one country at a time, RENTED cert per country, **out of scope here.**
- **DEPTH over BREADTH** — the seam is general; Italy is the only real customization.
- **NEVER regress Switzerland** — CH default, Swiss VAT (8.1/2.6 + café-split) + CHF byte-identical. The money-path e2e gate is sacred.
- **Multitenant is a SEAM, not a build** — per-tenant columns yes; per-tenant store-*selection* no (that's a later layer). The IT proof rides a **second env**, not two stores in one deployment.
- **Presentable ≠ legal** — a clean 22/10/5/4 receipt is not a *documento commerciale*. Say so on the receipt itself.

---

## DO-NOW vs DEFER

| | Scope | Rationale |
|---|---|---|
| **DO-NOW P0** | Regime seam = **three thin selector columns** (`fiscal_regime`, `currency`, `locale`) on `store_settings`, default CH; `/config` sources them with a CH fallback. **No IT tax-law placeholders in the tree.** | Doctrine-mandated per-tenant; unblocks P1/P2. |
| **DO-NOW P1** | Multicurrency (CHF/EUR, USD near-free) **+ date/time locale seam.** Route all money & dates through one formatter each. Server denom-set becomes currency-keyed (money-critical). | Most-visible, lowest-risk brick; the one correctness landmine is the denom whitelist. |
| **DO-NOW P2** | i18n EN/IT for the **demo path only** (7 screens). Glossary reviewed by a native speaker *first*. | Cheap in risk, expensive in tedium — scope it or abandon it half-done. |
| **DEFER (held)** | **VAT N-rate engine refactor** (`split_vat` → N-stream, class→rate map, N-code display). **NOT first-push.** Land only when a real IT tenant + commercialista exist. | Fiscal-critical surgery with zero live benefit today; writing placeholder Italian tax law now rots and misleads (seal lesson). |
| **OUT OF SCOPE** | **Rented-cert RT plug-in** (fiskaly/Epson/Custom) — the thing that makes an IT receipt *legal*. | Expensive vertical, one country, external cert. |

**Decisive call on the N-rate engine:** the P0 columns are shaped so the engine bolts on later, but P0 ships **no `vat_rates[]` / `class_to_rate` / `consumption_rule`** in the tree. Those arrive with P3 when they're real.

---

## PHASE 0 — Regime seam (invisible; CH byte-identical)
**Goal:** per-tenant `fiscal_regime` / `currency` / `locale`, default CH, surfaced through `/config` with a bulletproof CH fallback. Zero behavior change on a CH tenant.

**Tasks (ordered):**
1. **Model columns** — `src/db/models/store_settings_model.py` (after `vat_rate`, ~line 128): add
   ```python
   fiscal_regime: Mapped[str] = mapped_column(String(8),  nullable=False, default="CH")
   currency:      Mapped[str] = mapped_column(String(8),  nullable=False, default="CHF")
   locale:        Mapped[str] = mapped_column(String(12), nullable=False, default="de-CH")
   ```
   Leave existing scalar `vat_rate` untouched (P3 owns generalizing it).
2. **Additive migration** — append to the `store_settings` block in `src/db/database.py` `_ADDITIVE_COLUMNS` (~line 163), **defaults byte-identical to the model** (`'CH'` / `'CHF'` / `'de-CH'`):
   ```sql
   ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS fiscal_regime VARCHAR(8)  NOT NULL DEFAULT 'CH';
   ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS currency      VARCHAR(8)  NOT NULL DEFAULT 'CHF';
   ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS locale        VARCHAR(12) NOT NULL DEFAULT 'de-CH';
   ```
   (`NOT NULL DEFAULT` backfills Felix's Store #1 to CH — no data step.)
3. **Thin regime resolver** — new `src/services/fiscal_regime.py`, pure/no-DB, modeled on `catalog_taxonomy.class_meta`. **CH only for now.** CH `vat_rate`/`_reduced` are **read from config** (`POS_VAT_RATE`/`_REDUCED`) — single source, so the 8.1→8.5 change stays one edit. `resolve_regime(store|None)` → merged dict; `None` → pure CH from config. **Do NOT populate an IT regime here.**
4. **`/config` sourcing** — `src/routes/pos_router.py:132-150`: add `db: AsyncSession = Depends(get_db_session)`, load Store #1 via `get_active_store_settings`, `resolve_regime(store)`. **Mandatory `try/except → resolve_regime(None)`** so a DB blip degrades to CH, never 500. **Keep every pre-existing scalar key** (`vat_rate`, `vat_rate_reduced`, `vat_decimal`, `vat_year`, `currency`, `locale`) identical; add `regime` + (future) `vat_rates` additively.
5. **Seeding + wizard reconcile** — `store_settings_seeding.py:41-87` seed explicit CH values; `shop_setup_service.py:77-80` already emits `currency`/`default_language` mapping to *no columns* — reconcile key names (`default_language`→`locale`, add `fiscal_regime`), **filter unknown keys** before `StoreSettingsModel(**prefs)` (`prices_include_vat` has no column — don't pass it).

**Swiss-green assertions:**
- Diff CH-store `/config` **pre-existing keys** against a frozen snapshot → **value-for-value equal** (not the whole blob — `regime` is additive by design).
- DB-down test: `/config` returns **200 + CH values**, never 500.
- Fresh-DB store and migrated store **both resolve to CH regime** (defaults must match literally).

**Effort:** ~0.5 day. **Done-when:** `make test` + `make test-pos` + `make e2e-all` green on CH; `/config` pre-existing keys byte-equal to pre-P0; new columns migrate + backfill CH.

---

## PHASE 1 — Currency + date/time locale
**Goal:** every money value through one `formatPrice`, every date through one `formatDate`/`formatTime`, both keyed off `POSConfig.locale`. Euro drawer counts correctly server-side. CH pixel- and cent-identical.

**The one correctness landmine (money-critical):** `cash_shift_service.py:72-91` `denoms_total()` **silently skips any face value not in `_VALID_DENOMS`** and is authoritative at closeout (`pos_router.py:4600,4690`). A €500 note or 1¢/2¢ coin would vanish → phantom shortage. This edit goes through the money-path e2e gate.

**Tasks (ordered):**
1. **Server denom safety** — `cash_shift_service.py:17-23`: add `EUR_DENOMINATIONS = [500,200,100,50,20,10,5,2,1,0.50,0.20,0.10,0.05,0.02,0.01]`; add `denoms_for(currency)`; `denoms_total(denoms, currency="CHF")` validates against the **currency-appropriate** set. **CHF set stays byte-identical** (keep `1000` note + `0.05`, exclude `0.01/0.02`; keys stay `str(Decimal(...))` → `"0.50"` not `"0.5"`). Wire `pos_router.py:4600,4690` to pass tenant currency. `money()` stays `0.01` (no Rappen rounding exists — keep it that way).
   - **USD is then free:** `USD_DENOMINATIONS = [100,50,20,10,5,1,0.25,0.10,0.05,0.01]`, `locale:"en-US"` → `$1,234.55`. Validates the per-currency lookup is the right abstraction.
2. **`/config` serves `denominations[]`** (ordered face-value list) so client grids stop being hardcoded.
3. **Kill the currency-format leaks** (`formatPrice` at `base.html:643-648` is the one good seam):
   - Replace `chf()` helper `base.html:862` → `formatPrice`.
   - Delete duplicate formatter `search.html:532-537` → global `formatPrice`.
   - Sweep `'CHF ' + x.toFixed(2)` → `formatPrice(x)` across: `cash_count.html`, `checkout.html` (incl. the mixed literal at :235), `customer_lookup.html`, `receipt.html`, `receiving.html`, `scan.html`, `shift.html`.
   - `POSConfig` defaults stay `'CHF'`/`'de-CH'` (`base.html:615-616`); `/config` overwrites only on `response.ok`.
4. **NEW date/time locale seam** (the gap all drafts missed) — add `formatDate()`/`formatTime()` in `base.html` keyed off `POSConfig.locale`; sweep the ~15 hardcoded sites and delete per-template copies: `receipt.html:499,509`, `closeout.html:307`, `customer_lookup.html:543`, `kb_approvals.html:358`, `shift.html:326`, `transactions.html:332,500,510`, `my_day.html:336,460`, `my_tickets.html`, `product_sales.html:247,292`, `hypercare.html:163`, `base.html:769,879,897,922`. Also route bare `search.html:95` `toLocaleString()` and CSV *timestamp* headers through the seam.
5. **Client denom grids from `/config`** — `shift.html:293-299`, `cash_count.html:160-178`: render from `denominations[]`; EUR labels (`'50 c'` not `'50 Rp'`, add €500 + 1¢/2¢ rows). Zero-padded string keys must match server exactly.
6. **User-facing server string** — parametrize closeout variance `HTTPException` `pos_router.py:4697` (`"Off by CHF …"`) with tenant currency. (Internal log strings 1289/2160/2463/2642/2719 + docstrings = low-pri, opportunistic.)
7. **CSV integrity** — `product_sales.html:308,319` + `transactions.html:550`: header *labels* currency-aware; **cell values stay raw numeric** — never route CSV cells through `formatPrice` (de-CH apostrophe `1'234.55` and it-IT comma both corrupt delimited data).

**Swiss-green assertions:**
- Existing `denoms_total` unit tests pass **byte-identical**; `denoms_for("CHF") == CHF_DENOMINATIONS` (incl. `1000`, `0.05`; excl. `0.01/0.02`).
- CH e2e-money (refund/variance/drawer) green; CH drawer counts identically.
- CH CSV export still parses (raw numeric cells, apostrophe never reaches data).
- Grep gate: `grep -rn CHF src/templates/pos/` == 0 (captions handed to P2); on an EUR store the DOM contains **no** `CHF`.

**Effort:** ~1–2 days. **Done-when:** EUR store shows `€ 1.234,55` and Italian dates everywhere; Euro drawer totals correctly through the server; CH is cent- and pixel-identical; CHF grep clean.

---

## PHASE 2 — Italian i18n (demo path first)
**Goal:** the 5-minute demo path fully Italian, English unchanged, key-parity gated. **Do NOT sweep all 22 templates now** — half-done i18n reads worse than English.

**Demo path (ship these, complete):** `login → catalog → scan → checkout → receipt → closeout` + the shared `base.html` shell. **Deferred to "when a real IT shop signs":** `hypercare`, `kb_approvals`, `my_tickets`, `suppliers`, `receiving`, `transactions`, `customer_lookup`, `dashboard`, `my_day`, `reports`, `product_sales`, `search`.

**Tasks (ordered):**
1. **Glossary FIRST** — one page, ~40 POS terms (scontrino, resto, IVA, chiusura di cassa, giacenza…), reviewed by **Nino / ISOTTO "Famous Guy"** before writing 600 string values. Fixing a glossary is cheap; re-editing a catalog is not.
2. **Catalog** — new `src/static/pos-i18n.js`, shape `{ it:{…}, en:{…} }` modeled on `isotto-i18n.js` (seed `common.*` from `isotto-i18n.js:52-66`). Namespaces: `checkout.*`, `cash.*`, `vat.*`/`receipt.*`, `closeout.*`, `scan.*`, `settings.*`, `msg.*`.
3. **Wire the engine into `base.html`** — port from `isotto/base.html`: include (`:112`), detection IIFE (`:116-139`), `t()` (`:150-172`), `applyI18n()`+DOMContentLoaded sweep+**MutationObserver** (`:352-393`). **Scope the observer** (subtree + attribute filter, ignore Alpine-managed nodes) — `scan.html` is 1,426 lines of high-frequency Alpine; an unscoped observer risks scan-input lag.
4. **Default language from regime** (fix the hardcode) — detection order: `?lang=` → `localStorage 'pos_lang'` → JWT `locale` claim (from `sessionStorage 'pos_token'`) → **`POSConfig.locale`'s language** (`it-IT`→`it`, else `en`) → `'en'`. **Guard every branch** `if (POS_STRINGS[lang])` so a `de-CH` JWT falls to English, never blank/raw-key.
5. **Sweep the 7 demo templates** — Pass A static `data-i18n`/`-placeholder`/`-html`; **Pass B (the risk)** Alpine `x-text`/JS/`alert`/`confirm`/toast → `t()` calls; Pass C split prose (`t()`) from money (`formatPrice`) — since P1 already did each file, do i18n in the **same screen-by-screen pass** so each file is touched once.
6. **Switcher** — Language/Lingua `<select>` in `settings.html:~56` + compact selector in the `base.html` footer; writes `localStorage 'pos_lang'` + reload; set `.value` to `window._posLang` on load.
7. **Regime-driven labels** (the `vat_number_format` gap) — receipt VAT label `receipt.html:97` `VAT` → `P. IVA` (IT) / `MWST` (CH) driven by regime; settings-form P.IVA placeholder + light validation from `vat_number_format`. (If not wired, **drop the field as YAGNI and say so** — don't carry a decorative seam.)
8. **HONESTY: non-fiscal receipt banner** — for `regime == IT` without a wired RT, receipt prints `Documento non fiscale — Ricevuta non valida ai fini fiscali` (reuse the conditional-banner pattern at `receipt.html:82-88`); Z-report gets the equivalent. **Required by doctrine, not optional.**

**Swiss-green assertions:**
- English default → CH screens render **identical wording** to pre-i18n (audit `?lang=en` vs snapshot; any wording drift in the EN catalog changes the Swiss UI).
- `de-CH`-JWT user gets English, **not blank, not raw keys**.
- No `data-i18n` key falls through to raw-key display.

**Effort:** ~2–3 days (7 screens, not 22). **Done-when:** demo path fully Italian under `?lang=it` incl. dynamic states (empty cart, sale toast, error paths); English byte-identical; key-parity green; native speaker signed the glossary; IT receipt carries the non-fiscal banner.

---

## PHASE 3 — DEFERRED: Italian IVA N-rate engine (held)
**Not first-push. Land only when a real IT tenant + commercialista exist.** Documented so the seam is ready:
- `split_vat` → N-stream `{code: {turnover, vat}}`; the bucketer must be **total-coverage** — any line rate matching no code falls to the **default/standard code, never dropped** (today's `if red else standard` is total; a naive dict drops `7.7`/`0`/null lines → Z-report under-reports). This is the single fiscal-critical hour.
- `vat_rates[]` + `class_to_rate{}` + `consumption_rule` land on the regime **then** (`cafe_split` becomes one rule among `flat_restaurant_10`/`none`).
- Display A/B → N-code loop; `DailySummary` keeps `vat_standard/reduced` as back-compat properties + adds `vat_streams`.
- Lines already snapshot the **numeric** rate (`line_item_model.py:99`) → **no line-item migration** needed; N-code is a display artifact.
- **IT class→rate (22/10/5/4) ships `xfail` until a commercialista confirms** which goods are which. Ship the engine, hold the mapping.

**OUT OF SCOPE entirely:** rented RT cert plug-in (fiskaly/Epson/Custom) — the fiscal-legal layer.

---

## Consolidated RISK Table

| # | Sev | Phase | Risk | Mitigation |
|---|-----|-------|------|-----------|
| 1 | CRIT | P3 | N-stream `split_vat` **drops** lines whose rate matches no code (7.7/0/null) → Z-report under-reports | Total-coverage bucketer: unmatched → default code. Unit test mixed cart w/ 7.7+null under CH: `Σturnover==subtotal`, `Σvat==vat_total` cent-exact. (Deferred to P3.) |
| 2 | CRIT | P0/P1 | `/config` client is **defaults-masked** — drop/rename a scalar key → client silently keeps hardcoded CH; CH tests pass, IT computes stale Swiss numbers | Keep **all** pre-existing flat keys, identical types. Test 1: CH `/config` pre-existing keys byte-equal to snapshot. Test 2: IT store `vat_rate != 8.1` (proves client reads the wire, not fallback). |
| 3 | HIGH | P1 | Denom refactor drops CHF `1000`/`0.05` or emits float keys (`"0.5"≠"0.50"`) → CH drawer miscount | CHF list + `str(Decimal)` keys byte-identical; `currency` defaults CHF; existing `denoms_total` tests unchanged; assert `denoms_for("CHF")==CHF_DENOMINATIONS`. |
| 4 | HIGH | P1 | Naive `formatPrice` sweep hits CSV → de-CH apostrophe `1'234.55` corrupts CH exports (same trap as IT comma) | CSV **cell values raw numeric**; only header labels currency-aware; grep no CSV path calls `formatPrice`; verify CH export parses. |
| 5 | HIGH | P0/P3 | Split-brain: `store_settings.vat_rate` (vestigial) vs config `POS_VAT_RATE` (roll-up reads) drift on rate change | CH standard rate has **one** source = config. Don't read `store_settings.vat_rate` in regime path. Reconciliation test: receipt line-rate == Z-report standard-stream on a CH sale. |
| 6 | MED | P2 | `de-CH` JWT → `undefined` dict → blank till / raw keys; EN catalog wording drift changes Swiss UI | Guard every branch `if (POS_STRINGS[lang])`→`en`; e2e assert `de-CH` user gets English; audit `?lang=en` vs pre-i18n snapshot. |
| 7 | MED | P0/test | Tenant-scoped `/config` resolves to wrong store → CH gate silently validates IT | Pin `/config` to `store_number=1`; CH e2e asserts `config.currency==='CHF'` && `vat_rate===8.1` before trusting the run. |
| 8 | MED | P0 | `/config` gains a DB dependency → new 500 path on a public init-time endpoint | `try/except → resolve_regime(None)`; test DB-down returns 200 CH. |
| 9 | MED | P2 | Document-wide MutationObserver on Alpine-heavy `scan.html` → re-translation churn / input lag | Scope observer (subtree+attr filter, skip Alpine nodes); load-test CH scan before/after. |
| 10 | MED | P1 | **Date/time locale gap** — receipt/dashboard render `de-CH`/`en-GB` dates on an IT till ("looks localized, isn't") | `formatDate`/`formatTime` seam; audit IT store: no `\d{2}\.\d{2}\.\d{4}`, no English weekday/month. |
| 11 | MED | P2/honesty | IT receipt looks like a valid *scontrino* with nothing marking it non-fiscal (seal lesson) | Regime-driven `Documento non fiscale` banner on receipt + Z-report for `regime==IT` w/o RT. |
| 12 | LOW | P0 | Model default ≠ ALTER default → fresh-DB and migrated-DB diverge | Identical literals; test fresh + migrated store both resolve CH. |
| 13 | LOW | P3 | IT cash 5¢ rounding (`arrotondamento`) framed as optional — it's IT-standard for cash | Named tender-time step `cash_round_5c` on IT regime, **never** in `money()`; flag rounding direction for commercialista. |

**Cross-cutting gate:** the sacred rule is not "CH tests pass" — it's "CH tests pass **and** one IT-path test proves the client reads the wire, not the CH default" (risks #1/#2/#5 are all green-because-wrong-value-equals-CH-default). Capture the **CH golden lock** (`tests/pos/golden/ch-{receipt,zreport,closeout}.json`, a *mixed-rate + historical-7.7% cart*) **before P1 starts**; assert after P1 and P2. Freeze the **numbers and A/B split**, not the whole DOM (banners/labels are additive).

---

## External Dependencies (line up early)
| Dependency | Owner | Blocks | When |
|---|---|---|---|
| **Commercialista** — IT class→rate (22/10/5/4) + Partita IVA rules + `arrotondamento` direction | Angel → accountant | P3 IVA mapping (engine can precede) | Start when a real IT shop is in sight; runs in parallel with engine build. |
| **Native-speaker QA** — 40-term glossary, then catalog-in-context | Nino / ISOTTO "Famous Guy" | P2 done-when | **Glossary before writing strings**; catalog review before "done". |
| **First IT tenant fiscal identity** — real Partita IVA, legal name, registered address, Italian `receipt_header` | Customer | IT go-live (P0 wizard has nothing valid to persist without it) | Gate IT tenant creation on it. |
| **Per-tenant migration** — the three additive ALTERs on prod `store_settings` | Angel via deploy ladder | P0 promote | Take the `banco_prod` backup even though "nothing changed" — it touches `store_settings`. |

---

## Honesty Callouts (non-negotiable)
- **Presentable ≠ legal.** Green math tests prove *arithmetically correct + Italian-looking*, **not** a legal Italian *documento commerciale*. Every IVA test file carries that comment.
- **IVA rates are TBD-by-accountant.** No 22/10/5/4 class assignment ships without commercialista sign-off; until then it's `xfail`.
- **The IT receipt says so itself** — `Documento non fiscale` banner until the RT cert is wired.
- **Second-env EUR path is the honest e2e** — it proves the IT *code path*, not that CH+IT coexist in one deployment (that needs unbuilt multitenant; noted in the run log).

---

## Sequencing (one glance)

```
 GLOSSARY REVIEW (Nino) ─┐  (start immediately, async)
                         │
 P0 regime seam ─────────┼──► P1 currency + date/locale ──► P2 i18n EN/IT (7 demo screens)
 (thin columns,          │    (formatPrice + formatDate,      (catalog + engine + sweep,
  /config fallback,      │     denom-set server-safe,          screen-by-screen, one pass
  CH golden lock ◄───────┘     CH cent-identical)              w/ P1 already done per file)
                                                                        │
                                              ┌── CH GOLDEN asserted ───┤ after P1 & P2
                                              │                         ▼
                                   DEPLOY LADDER each phase:   DELIVERABLE:
                                   sandbox→staging→[backup]→prod   "Banco demos in Italian
                                   →re-probe→env-parity            with Euros; CH byte-identical"
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
 DEFERRED (held for a signed IT shop + commercialista):
   P3 IVA N-rate engine ──► RT rented-cert plug-in (fiscal-legal, out of scope)
```

**Per-deploy ritual (reused, unchanged):** `deploy-banco.py sandbox` → full suite → `staging` → re-run → **backup `banco_prod`** (human gate) → `prod` → **re-probe after restart** (health greens before first request serves) → `env-parity.py` shows trio converged.

---

## Smallest Shippable First Brick
**P0 + P1-on-the-receipt-path only** = *"the receipt prints in Euros with Italian dates, Switzerland untouched."*
- P0 three columns + `/config` fallback (~0.5 day).
- P1 `formatPrice` + `formatDate` seam applied to `checkout.html` + `receipt.html` + the server denom-set safety (~1 day).
- CH golden lock captured first; second-env EUR override to prove it.

That is a **walk-into-a-Trapani-shop artifact** in ~1.5 days — a Euro receipt with Italian dates and a `Documento non fiscale` banner — the honest demand-enabler. Then let a real "yes" pull the full i18n sweep, the internal screens, real per-tenant columns in prod, and the P3 IVA vertical. **Everything past the demo path is building ahead of pull — don't.**
