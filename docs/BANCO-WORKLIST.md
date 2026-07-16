# Banco Go-Live Worklist — THE ordered list

> 🔑 **Code word "ON DECK"** → you're reading the right file. State the top items and start executing the first actionable one. No re-planning, no re-asking.

*Open this, work top-down, finish one tier before opening the next. Don't fan out across five things. 2026-06-28.*

*Owners: 🧍 = Angel's hands needed (physical / decision / external call) · 🐯 = Tigs can do it · 👥 = both, together.*

*Detail lives in: [BANCO-GO-LIVE-READINESS.md](BANCO-GO-LIVE-READINESS.md) (analysis) · [BANCO-DAY-ONE-WISHLIST.md](BANCO-DAY-ONE-WISHLIST.md) (polish backlog).*

---

## ✅ BL-CAT — CATEGORY TAXONOMY CLEANUP — SHIPPED PROD 2026-07-16 (Felix→Angel sign-off)

**✅ LIVE ON PROD 2026-07-16** (`517ee0b` + data migration). Felix delegated → Angel approved the tree.
Backup-gated (`/root/banco_prod-precat-20260716_055555.sql.gz`, 3.8M, gzip-OK, 5179 products/54 txns).
**Migration:** `blcat_migrate.py --commit` remapped **5,533 products** → canonical `category` + `product_group`;
**0 non-canonical categories left**; **product_class/age/VAT invariant asserted UNCHANGED** (standard 4057 /
tobacco_nicotine 802 / cbd_hemp 292 / …). **Labels:** 49 categories + 9 groups × en/de/fr/it in POS_CATEGORY_LABELS
(Felix's German shop shows Feuerzeuge/CBD Blüten/etc.). Verified live: 49 categories under 9 groups via the API;
BIC lighter category = "Lighters" → de "Feuerzeuge"; app health/catalog 200; label map serving on prod.
**▶ FOLLOW-ON (BL-CAT.4 writer funnel — so the mess can't REGROW, not yet shipped):** vision/snap-fill prompt
(`vision.py:270`), adopt path (`pos_router.py:1110`), quick-add→Unsorted, enrichment map, `ensure_description`
source_lang honesty; + kiosk category-label translation; + nl/es labels. Plan: `docs/BANCO-CATEGORY-FUNNEL-PLAN.md`.

## 🗄️ BL-CAT (orig handoff, done) — CATEGORY TAXONOMY CLEANUP · ✅ BL-CAT.1+.2 DONE 2026-07-16

**✅ BL-CAT.1 (verify) + ✅ BL-CAT.2 (Felix review sheet) DONE 2026-07-16 — `docs/testing/banco/BANCO-CATEGORY-TAXONOMY-REVIEW.html`.**
Verify caught + corrected 4 real mis-mappings (Oel Dabbing 157→dab gear, Raw Produkte→cones, Vape Co→prefilled, Treats→system).
Sheet = 9 groups × 49 categories w/ live counts + 3 real samples + 7 tickable decisions; 0 unmapped.
**✅ BL-CAT.3 (dry-run migration scaffold) DONE** — `scripts/blcat_migrate.py`, prod dry-run: 4,984 move / 0 gaps / class untouched
(`docs/testing/reports/prod/blcat3-migration-dryrun-2026-07-16.txt`). **✅ BL-CAT.4 (code-funnel plan) DONE** — `docs/BANCO-CATEGORY-FUNNEL-PLAN.md`.
**▶ ALL 4 pre-sign-off tasks DONE. NEXT (Angel + Felix): walk the sheet, tick the 7 decisions → fold ticks into the JSON → the migration
ships post-sign-off through the gated ladder (BL-CAT.3 `--commit` + BL-CAT.4 writer fixes) as a separate deliberate session.**

**READ [docs/BANCO-CATEGORY-TAXONOMY-HANDOFF.md](BANCO-CATEGORY-TAXONOMY-HANDOFF.md) and execute its
task list (BL-CAT.1–.4). STOP at the Felix sign-off gate — read-only on prod, build artifacts, NO
deploy, NO migration commit.** Root cause (measured prod 2026-07-14): the Artemis importer named
categories from **German URL slugs** → 61 category strings, 49 raw German, "papers" split across 10.
Descriptions are ~96% fine — this is a CATEGORY problem. Fix = ONE canonical 2-level tree, English
hub, the 61 strings become synonyms. Draft tree + full 61→canonical mapping already built:
**`docs/banco-category-taxonomy-draft.json`**. The real deliverable = **BL-CAT.2, the Felix review
sheet** (HTML test-script) with the 6 business decisions §4. Memory: `banco-category-language-mess`.

## 🔴 BACKLOG — PRIORITY (Angel 2026-07-15, "damaging… fat-fingered all over the place")

- **🛟 CLICK-OUTSIDE LOSES EDITS.** **DOCTRINE: clicking a form's backdrop must not discard; only
  ✕/Cancel/Save closes, and ✕/Cancel confirms if dirty.** ✅ SHIPPED SBX b1782 on the **catalog
  create/edit modal** (`tryCloseEdit` + snapshot-vs-current dirty check). ▶ STILL TO ROLL OUT: supplier
  edit, tier editor, order-book lines, settings, + receiving mobile back-button. [[banco-unsaved-work-guard]]
- **🗑️ GUARDED PERMANENT DELETE — ✅ SHIPPED SBX b1782.** "🔥 Delete permanently" shows only for never-sold
  items (`GET /products/{id}/sales-count`); `DELETE /products/{id}/permanent` hard-deletes with a server guard
  (409 if any sales → discontinue instead; clears child rows first). Discontinue stays default for sold items.
- **⏳ "Translating…" indicator — ✅ SHIPPED SBX b1782** (spinner on the desc language flags; slow LLM lookup
  no longer looks dead).

## 🃏 ON DECK — 🧶 ECOLUTION SUPPLIER ONBOARDING (sandbox) · IN FLIGHT · 4 maker-flow fixes SHIPPED PROD

**✅ 2026-07-13 — Ecolution onboarding proved END-TO-END in sandbox** (Angel=Ralph): created supplier
**ECO · Ecolution — Sylvie Thiel** (manual, wholesale), received 2 no-EAN items (glasses case + card wallet),
clean SKUs, postcards render in 4 languages with the maker story + QR + store footer. **Trade discount = 30% OFF
RETAIL** (not 50% — protects Sylvie's margin); shelf = her Etsy price, cost = retail×0.70. The drive surfaced +
shipped **4 fixes sandbox→staging→prod** (backup-gated, live-request re-probed, tag `verified/ecolution-maker-2026-07-13`→68ee69c, b1752):
1. **stale-translation** — editing a description now clears the cached per-lang skins (was: postcard served old text)
2. **barcode-box trap** — a NAME can't become the barcode/immutable SKU (client guard + server backstop, all create paths)
3. **postcard German** — all card chrome localized (Scan me / Handmade / made with love) on card + 4-up sheet
4. **store footer** — pickup CTA + store name/hours/address/phone/logo from `store_settings` (prod = "Artemis Lucerne")

**✅ 2026-07-15 — per-supplier `trade_discount_%` → receiving cost auto-fill BUILT (local, green, NOT deployed).**
A supplier now carries a `trade_discount_pct` (0-100, % off retail). Set it once → receiving auto-fills the cost from
the shelf price: `cost = retail × (1 − pct/100)`. Ecolution = 30 → CHF 34.59 case costs CHF 24.21 (proven). Only fills
a BLANK or auto-filled cost (never clobbers a hand-typed one); a green hint shows the source; box-helper + manual edit
take over cleanly. Files: `supplier_model.py` (column + `cost_from_retail()` half-up cent helper), `database.py`
(ALTER), `pos_schema.py` (0-100 guard), `suppliers.html` (admin field + badge), `receiving.html` (auto-fill + hint),
`pos-i18n.js` (en/fr/it/de, parity 4/4), `sw.js` v103→v104. 16 new unit tests; `make test` **1897 pass / 3 known-flaky**;
column verified live + ORM round-trip. **▶ Needs Angel human-green on sandbox → then `make deploy ENV=sandbox` (gated ladder).**

**▶ 2026-07-15 — receiving workflow round IN SANDBOX (Angel testing, NOTHING shipped past sbx):**
- ✅ **no-barcode photo-first "New item" button** (snap → AI title+price → find-first → cost auto-fills 70% → photo
  = cover). Angel proved it live: 5 Ecolution items created with photos + correct auto-cost (34.59→24.21 etc.).
- ✅ **unsaved-work guard** — `HelixDirtyGuard` (base.html shell) + receiving new-item modal **discard-confirm on
  backdrop/✕ mis-tap**. Desktop swipe-back covered by beforeunload; **mobile hardware BACK button = OPEN, needs
  Angel's on-device test** before wiring. [[banco-unsaved-work-guard]]
- 📋 **SPEC WRITTEN + Angel-approved (A–F + Option 2): [docs/BANCO-RECEIVING-GOODS-RECEIPT-SPEC.md](BANCO-RECEIVING-GOODS-RECEIPT-SPEC.md).**
  Receiving → a flexible **goods-receipt + maker-migration** flow. Key calls: (2) per-item supplier, NOT a session cage;
  (4) `PREFIX-####` server-minted SKU, house prefix from settings, NEVER ART/LZ; (5) minted internal EAN-13; (6) AI
  1-2 sentence description → all langs via `description_i18n`; (7) AI category + "please check" nudge; (8) delivery
  header (note-no/date/received-by/terms/attach slip) = Option 2 goods receipt; (9) daily "goods received today"
  notice on Felix's dashboard (one big number); (10) reviewable CSV→Banana; (11) label **print cockpit** (received-but-
  not-printed queue, checkbox + qty, 62mm, barcode+QR); (12) postcard+label+translation PREVIEWS at receiving (the
  happy moment); price-sanity ✅ shipped b1777; desktop guard ✅, mobile back-button = next test.
- ▶ **BUILD ORDER (spec §15):** ✅3 supplier-mode core SHIPPED SBX b1779 9510cf4 (per-item supplier + `PREFIX-####`
  server-minted SKU + internal EAN-13 + supplier tag; house prefix = `store_settings.house_sku_prefix` default ITEM;
  live-verified ZZ-0001 + valid EAN + house fallback) → **4 AI writes DESCRIPTION + suggested TAGS**
  (Angel 2026-07-15: snap already does title+search — add desc+tags; wire into BOTH catalog "Snap & fill" AND
  receiving photo-first; desc source-lang → all langs via `description_i18n`) → 5 AI cat → 6 delivery header →
  7 daily summary + CSV → 8 label cockpit → 9 previews (incl. **tap a Delivery-list line → photo/postcard
  preview + edit desc/detail before Receive**, Angel 2026-07-15) → 10 mobile guard + partial-barcode search.
  ⚠️ The 5 items Angel entered pre-fix keep their LZ- SKUs + no supplier (SKU immutable) — delete+re-add to re-mint if wanted.
- ▶ still queued outside the spec: variants/colours assortment model; Sylvie's wholesale list.
Spec: **[docs/BANCO-ECOLUTION-ONBOARDING-SPEC.md](BANCO-ECOLUTION-ONBOARDING-SPEC.md)** · memory `banco-ecolution-sylvie-supplier`.
- **Real-world parallel (2026-07-14 AM):** Angel's at Felix's shop in Littau — Felix demo (walk DISC-PROD-01 on
  the phone) + help cover + the new-hire onboarding (kid starts Thu; self-drive kit ONBOARD-KIT-01 is ready). The
  barcode-trap fix now protects that new hire on the live till.

## 📄 2026-07-15 — READ-THE-DELIVERY-SLIP (AI) — CUT #1 SHIPPED SANDBOX b1784 c9353bc

Angel's "ultimate idea": snap the supplier's delivery note → AI reads supplier + note-no + date +
EVERY product line → each line trigram-matched to the live catalogue → operator confirms/adds. Built
on the EXISTING multi-provider vision engine (no reinvention): new `delivery_slip` VisionDomain +
`POST /receiving/read-slip` + a review modal on receiving ("📄 Read delivery slip"). Suggest-only.
- ✅ **End-to-end PROVEN on the box** (gemini 3.7s): synthetic Lieferschein → structured lines, Total
  row correctly skipped. **Text accuracy on the crude synthetic image was rough → real-slip TUNING is
  the next round** (prompt + a real sample). This is cut #1 = plumbing, as promised.
- ▶ **NEXT tuning:** test with a REAL slip photo/PDF; refine the prompt on real formats; attach the slip
  image to the goods-receipt record (spec §8); auto-select the session supplier when the slip names one;
  let a line pick a NON-top match (currently adds matches[0]). Also still queued: AI desc+tags (step 4),
  delivery-line preview (§12), edit-guard rollout to other modals, mobile back-button.

## 🔴 2026-07-14 PROD INCIDENT + BL-100 raised — Tycoon Gas scanned "discontinued" on the mobile till

**Live prod, Angel on mobile:** scan a can of **Tycoon Gas 250ml** → *"discontinued."* Root cause = a **bad match
at intake**, not a bug: a discontinued `REF-FOURTWENTY "Tycoon dupe"` still held the **real can EAN** `4035687900004`
while the live `TAM-5851 "Tycoon Gas 250ml"` (€6.90) only had a synthetic placeholder. Scan hit the dead dupe.
**Patched by hand in prod** (moved real EAN + `42425700` onto the live row, kept placeholder as alias, stripped the
dupe — it keeps its 2 sales). Prod sweep: only 2 other discontinued-with-barcode rows, both harmless synthetic scrap.
- **🐯 BL-100 · Product-matching integrity** (spec: [BANCO-INVENTORY-ROADMAP.md](BANCO-INVENTORY-ROADMAP.md#bl-100)) —
  the durable fixes: (1) **intake dedup / find-first** so attach-to-existing is the default and a true duplicate is
  the harder choice; (2) **deactivation releases barcodes** (a dead row must never keep a scan-live code); (3)
  scan-to-inactive → **offer the active replacement** instead of a dead end; (4) a **standing integrity sweep** in the
  hypercare cockpit (discontinued-rows-with-barcode + active-rows-with-only-synthetic-barcode) so we *find* traps
  instead of scanning into them. **Angel's lesson banked: product setup/matching is the hard part — a bad match is
  paid later at the till, the most expensive place to find it. Leverage is at intake, not patch time.**
- **🐯 BL-101 · Till search RECALL & RANKING — ✅ FAST-FIX SHIPPED PROD 2026-07-14** (b1755 `7e9bce2`, tag
  `verified/bl101-search-recall-2026-07-14`): till `/api/v1/pos/search` now ranks
  `GREATEST(similarity(name,q), 0.5·word_similarity(q, name+description))` — the capture-search's
  language-agnostic trick. Prod-verified live: `bic`/`bic lighter`/`mini bic` surface the Feuerzeug BIC items on
  screen one; grinder/clipper/raw/scale unaffected. **▶ DURABLE remainder (next round):** bare generic English
  words (`lighter`, `scale`) + misspellings (`bick`→Storz & Bickel) still need the brand field + DE↔EN category
  synonym layer (via BL-98 enrichment) — a one-liner can't disambiguate a word that lives in 200 descriptions.
  **Original incident (kept for context):** Angel looked for a **mini BIC lighter** at the till, it looked absent, so he
  went to the **Tamar site**, got the exact German title (`Feuerzeug BIC mini`), came back and found it. A cashier
  without that outside knowledge just concludes *"we don't sell BICs"* — a **silent lost sale, no error.** Diagnosis:
  the item IS there and well-formed; `/pos/search` matches the English `description` but **RANKS by German-name
  similarity ONLY**, so `"lighter"`/`"bic lighter"` bury the real Feuerzeuge under LED-`light` noise. **Fast fix:**
  port the capture-search's `GREATEST(name-sim, word_similarity(q, name||' '||description))` scoring into the till
  ORDER BY (one expression, no schema) + regression test. Durable: brand field + DE↔EN category synonyms (via BL-98
  enrichment). **A false-negative search is the most expensive shop failure because it's SILENT.**
  **✅ SHIPPED PROD 2026-07-14:** name-OR-description ranking (b1755, tag `verified/bl101-search-recall`) + the
  **bilingual/brand synonym layer** (b1757 `3aeb6f7`, tag `verified/bl101-synonym-layer`) — `lighter`→Feuerzeuge,
  `tycoon`→Tycoon Gas #1, `scale`→Waagen, `papers`→Drehpapier; 9 unit tests; search-strategy tip (EN/DE/FR/IT); sw v101.
- **🐯 BL-102.1 · preview-before-bind + 64px match thumbnails — ✅ SHIPPED PROD 2026-07-14** (b1762 `836d8e5`, tag
  `verified/bl102.1-preview-thumbnails-2026-07-14`). Angel's post-test feedback: result thumbnails 48→64px + a 👁
  preview (big image + details) that opens WITHOUT binding (the bind is permanent), "This one" confirms; row-tap still
  binds (fast path). Mobile-tested by Angel (onboarded a Zippo Benzin through the whole scan-miss→photo→bind loop). sw v103.
- **🐯 BL-102 · scan-miss → PHOTO-first — ✅ SHIPPED PROD 2026-07-14** (b1760 `d75de14`, tag `verified/bl102-scan-miss-photo-first-2026-07-14`).
  A pure barcode scan-miss now leads with a **camera hero** ("not found is normal — 📷 take a photo"), not the German
  name box; snap → AI names it → catalog/reference match → tap binds the barcode (BL-90) → sells → re-scan hits. All
  downstream cashier-allowed. Sandbox→staging→prod, backup-gated, live-probed. **▶ Watch on real use:** confirm the
  temp phone photo is replaced by the adopted/real image (Principle 4) — flag if not.
- **🐯 BL-102 (detail) · THE MATCHING DOCTRINE — scan-miss → PHOTO-first** (spec: [BANCO-INVENTORY-ROADMAP.md](BANCO-INVENTORY-ROADMAP.md#bl-102),
  memory `banco-barcode-matching-doctrine`). **Angel's dead-simple rule (2026-07-14):** the barcode on a can is NOT
  in the catalog on first scan (suppliers store minted codes, not the real EAN) — that's NORMAL. On a miss, go
  STRAIGHT to the photo/snap-&-fill (the reliable matcher), skip name-search; capture the can's barcode on first
  sale so it hits forever (BL-90 learn-back, already built). **THE GAP:** scan-miss currently leads with NAME search
  (BL-96), not the camera — BL-102 reorders it to PHOTO-first + confirms barcode auto-link + temp-photo replace.
  Small, high-leverage: the difference between "obvious 99% hit" and "Angel must steward every item himself."

## ✅ 2026-07-13 SHIPPED — discount SEPARATE-LANES (prod-green, tagged) · Test Library BUILT · onboarding kit ready

**✅ HC-PROD-01 (2026-07-13):** rows 1–9 PASS (postcard maker on the whole catalog + Cynthia's 7 balms +
share + short-QR + 4-up + one-page print). **Row 10** (discount didn't apply on a member) → old "Option B"
suppression → **redesigned to separate-lanes + 15/70/100 ladder + safety floor, SHIPPED PROD + PROD-HUMAN-GREEN
(DISC-PROD-01), tagged `verified/disc-prod-01`→85ee89a.** Row 10 CLOSED. (Detail in the shipped section below.)

**✅ TEST SCRIPT LIBRARY BUILT (2026-07-13) — `docs/testing/INDEX.html`.** Catalogs ~90 sheets (env + type
chips, every link verified). New **DISC-PROD-01** discount test sheet (`docs/testing/banco/`) is the flagship +
the Felix demo script. **Housekeeping done:** `banco/Test-Scripts/` junk-drawer dissolved → HTML sheets to
`banco/`, filled PDFs/evidence to `reports/`; `test-scripts/` is now the one canonical scripts folder (pure
HTML); orphan space-name SBX files renamed clean. Convention: blank sheets tracked, filled `*-uat-report.html`
gitignored (local). ⚠️ Loose end: `BANCO-SBX-HYPERCARE-BATCH-TEST.html` (358L) vs `…-TEMPEST.html` (505L) =
two versions of one sheet, pick canonical when fresh.

- **▶ NEXT: FELIX DEMO — Littau, AM 2026-07-14.** Angel sees Felix in the morning; walk DISC-PROD-01 on his
  phone (already prod-rehearsed + passed). Then the **LABEL DESIGN** build (waits for the QL-820 printer ~end-July;
  gun lands before Friday for real prod-migration testing).
- Mobile note: login self-heals as the stale service worker updates (v99+); if a phone is still stuck, clear site data / incognito once.

---

## ✅ SHIPPED PROD 2026-07-13 — DISCOUNT MODEL: member tier + manual = SEPARATE LANES (`85ee89a`, b1740)

**Closes HC-PROD-01 row 10** (bronze member + a manual discount → nothing came off = the old "Option B"
suppression). Redesigned WITH Angel/Felix to the simplest SAFE rule. Shipped sandbox→staging→prod via the
gated ladder, **backup-gated** (`banco_prod-prediscount-20260713_192748.sql.gz`, gzip-verified), re-probed on
prod (build stamp b1740 + separate-lanes/safety-floor markers present in the running container + old
suppression gone). **Manager cap set to 70 on all 3 envs** (cashier 15 / manager 70 / owner 100). Sandbox
human-green (Angel: fat-finger target auto-clamps at checkout, "this is perfect"). 7/7 stacking tests +
1856 in-container (3 known-flaky).
- **✅ PROD HUMAN-GREEN 2026-07-13 20:05** — Angel ran **DISC-PROD-01** on the live till: 9/10 ✓ (row 7
  George-Clooney-solo covered by row 5), overall "good on prod". Report committed + tied to the SHA:
  `docs/testing/reports/prod/disc-prod-01-2026-07-13-85ee89a.pdf` (build stamp in-doc + in the filename).
  **Convention set: a filled prod report lands in `reports/prod/` named `<id>-<date>-<sha>.pdf` — self-tying to the code it validated.**

- **Two lanes, two pockets:** member TIER = the shop's loyalty promise, automatic, ALWAYS applies, stacks on
  top, UNCAPPED by role. Cashier MANUAL = discretion / rounding room, bounded by a per-role **fat-finger cap:
  cashier 15 / manager 70 / owner 100** (lives in Settings → Discounts, not code).
- **George Clooney:** a platinum member (20%) is served SOLO by a 15%-capped cashier and still gets his full
  20% — the cap never touches the tier. **Layla:** a manager can run a big clearance markdown on a scratched
  display unit (up to 70%) that a cashier can't, with the tier still riding on top.
- **🛡️ SAFETY FLOOR (Angel caught the footgun):** lanes stack, so 100% owner + 25% tier = 125% would go
  NEGATIVE ("pay the customer"). Clamped at the point money is decided: combined discount can never exceed the
  discountable items → total floors at the tobacco/alcohol portion, **≥ 0 ALWAYS**, whatever/however settings
  are (fat-)fingered. Both server paths + client preview enforce it; a test literally tries to make it pay out.
- **◻ BANKED — Treuhänder question (VAT on giveaways/on-the-house):** confirm Swiss MWST treatment of FREE
  items (deemed-supply / Eigenverbrauch) — do we accrue VAT on giveaways, and should it show on the Banana
  export? *Motivating story: the smorgasbord restaurant that died on 500 untracked free birthday meals — the
  killer was INVISIBILITY, not generosity. Our giveaways ARE tracked (is_giveaway → daily summary), so the
  data is airtight; the tax-law call is Felix's tax advisor's, we wire whatever he says.*
- **◻ BANKED — audit the custom-line backdoor:** a cashier can ring an on-the-fly custom line ("Scratch tray,
  CHF 1") at ANY price — a useful oddball escape hatch, but an **uncapped discount by another name** (the 15%
  cap can't fire on a hand-priced item). It's already RECORDED (name/price/cashier/time on the day's tape).
  Future: **flag custom / below-normal-price lines for the manager's end-of-day review** so the backdoor is
  *audited*, not just recorded. Belt + suspenders vs. sweethearting/shrinkage.

---

## ✅ SHIPPED PROD 2026-07-13 · next build = LABEL DESIGN (manager-gated, waits for printer)

**✅ POSTCARD MAKER SHIPPED PROD 2026-07-13 (`ad22a0f`, b1728).** Backup-gated (`banco_prod-prepostcardmaker`), re-probed on a REAL Felix product: any product → shareable card, OG unfurl, short-QR `/p/{code}` (low-density, scannable small), trackable scan count, share-in-chosen-language. Works across Felix's whole live catalog. TEST-PC1 = Angel-signed ("platinum gold"). Sandbox-proven: single card + 4-up Format-C sheet + 4-flag desc picker + search-by-supplier + juiced EN-source/authentic-DE + one-page print.

**✅ MAMA CYNTHIA 7 BALMS SEEDED PROD 2026-07-13** (Angel said seed). 14 upserts, her Lavendel card verified rendering in prod (EN story + photo + short-QR). Reversible (`DELETE … WHERE supplier_name='Mama Cynthia'`). (Note: an unrelated pre-existing "Cynthia Bailey" supplier product also matches a "cynthia" search — not a dup.)

**✅ RESOLVED 2026-07-13 (`997333e`, prod) — the mobile-login "bug" was a STALE SERVICE WORKER.** Felix's phone ran an old SW from before the `/pos/callback` bypass (it intercepted the callback + dropped the #token → login bounced). Fix: bump `sw.js` CACHE_NAME v98→v99 + `skipWaiting()` so a stale worker auto-updates on next load (BL-011's wait-for-tap was trapping users on the broken worker). Also shipped same promote: 🌍 **Google-Translate override fixed** (`translate="no"` + `<meta google notranslate>` on pos base + postcard/sheet — mobile no longer re-translates the chosen language); diagnostics stripped. Interim for anyone still stuck: clear site data / incognito. Backup-gated (`banco_prod-pretranslate-sw`), re-probed.
**◻ FOLLOW-UP — Mama Cynthia postcard TITLE stays her German name in FR/EN/IT (description DOES translate).** Auto name-translation was tried + REVERTED (mangles specs/loanwords catalog-wide: "Kingsize"→"Großformat"; source_lang is en/null everywhere). Safe fix = **curated per-language name seeds for her 7 products** in the import script (hand-reviewed), not runtime translation. Small, do when fresh.

**🔴 P1 — MOBILE LOGIN fails on PROD + STAGING (sandbox FINE) — 2026-07-13. [SUPERSEDED — see RESOLVED above]** Fresh login → `/pos/callback` → KC `invalid_grant "Code not valid"`; callback hit TWICE with the SAME code. **KC config is byte-identical across realms** (helix_pos_web public, no PKCE, correct redirect URIs `banco/staging-banco/sandbox-banco.lapiazza.app/*`, code_ttl 60 / login 1800 / sso 36000) — so NOT config; it's live session/cookie/**service-worker** state (something re-fires the callback on stg/prod, not sbx). Desktop "works" = it had a live session; a true fresh desktop login likely fails too. **WORKAROUND: use the desktop/laptop till (works).** **NEXT (with Angel's phone as harness — he can test any env in seconds):** add request-level diagnostic logging to STAGING (safe, log-only) → Angel does one clean phone login → watch the exact sequence (who fires callback #2; is it the service worker / prefetch) → targeted fix on staging → phone-retest → promote prod. Do NOT cowboy a prod-auth change. Callback: `src/routes/pos_router.py:5976`; login init: `src/templates/pos/login.html` kcConfig/loginWithKeycloak; recovery block lines ~101-142. HC sheet tracks it: `docs/testing/banco/BANCO-PROD-HYPERCARE-SHEET.html`.

**◻ LABEL DESIGN — shelf + product/item labels ← (Angel chose it 2026-07-13: "a few more buttons"); JsBarcode fetched to /tmp, ready to vendor.** Reuse the postcard render engine → shelf-sticker + product-sticker templates (barcode for till + QR for phone, per `docs/BANCO-LABEL-KIT.md`).
- 🔑 **PERMISSIONS (Angel): MANAGER stuff, NOT cashier or public.** The label/postcard **MAKER** (design / print / quantity) = manager+ gated. The postcard **VIEW** (the QR target) stays PUBLIC by design.
- ⏳ **Build the PHYSICAL templates when the QL-820 + DK-44205 land (~end July)** so dims match the 62 mm roll. Can build the manager-gated maker UI + on-screen templates sooner; calibrate mm on arrival.
- **Focus line still holds:** basic mechanics, best value, not bells. La Piazza storefront/claim stays PARKED. Detail: [[banco-mama-cynthia-artisan-loop]], [[banco-hardware-procurement]].

---

## FOLLOW-UPS (BL-36/37/38 ✅ PROD · BL-39 KC login ✅ LIVE)

**✅ DONE 2026-07-13 (`a459d65`, prod):** 💱 currency conversion (Near Dark EUR → ≈ CHF, plan rates, `store_settings.fx_rates` per-tenant) · 🏷️ French category labels (53 entries, fr/it/de parity) · 🔧 BH reconcile (theme source pushed to origin branch `banco-kc-login-themes`; Angel's working tree untouched; full main-merge = clean-tree follow-up).

**BL-40 — DARK MODE (queued 2026-07-13, Angel: "Felix is an energy saver, he'll want darkmode — you just know it").** Anticipatory — have it READY before Felix asks. Approach: base.html already has a `:root` var block + component classes (.btn-primary/.card/.input-field/.chip = theming seams), BUT ~77 hardcoded `bg-white` + scattered `text-gray-900/700/500`/`border-gray-200` Tailwind UTILITIES in the templates don't flip. So: a `dark.css` override layer re-skinning the ~20 common surface/text utilities + the component classes under `html.dark`, + a toggle in the status bar (next to the language picker) that respects `prefers-color-scheme` and PERSISTS the choice (localStorage, like `pos_lang`). Do EVERY screen (catalog/scan/checkout/settings/modals) — a half-baked one leaves white patches. Medium block (~half day). NOT for the demo (rushed = broken-looking gaps); ship it clean AFTER, as a bonus for the energy-saver. 

**Candidates (pick next):** 🌍 NL/ES/PL chrome (rerun BL-37 batch-translate) · 💱 currency SETTINGS UI + more pairs (rates editable in-app, not just DB) · BL-36 fill-at-adopt + backfill script · Hemag login-suppliers (stored creds) · compare-panel role split (Your cost vs The market).

**BL-38 — MULTILINGUAL SUPPLIER QUERY ✅ SHIPPED PROD 2026-07-13 (`05bfcd0`).** Live search auto-translates the query to German (Ollama, cached, keeps loanwords) so English/French terms hit the German sites; Tamar queries languageId 3+2; per-adapter variant expansion (multilingual sites skip it) + split fetch budget to stay snappy. Proven prod: "lighter gas"→"Butan"→German butane products. Picker shows "· also searched X".

**BL-37 — FRENCH UI CHROME ✅ SHIPPED PROD 2026-07-13 (`a7239a2`).** 1,513 strings Ollama-batch-translated (0 fallbacks, placeholders+brands preserved, en/fr/it/de parity). NL/ES/PL = same move on request.**|OLD:** BL-36 descriptions work in
FR (Angel validated: *"Patch brodé Motörhead… idéal pour décorer vestes, sacs…"* + 🤖 badge). Now flip
the BUTTONS/labels to French too. Approach: **batch-translate the `en` block of `src/static/pos/pos-i18n.js`
→ a `fr` block via Ollama** (turbo_or_local — same brain as descriptions), then human-review + paste in.
Add `"fr"` to POS_STRINGS (chrome then shows French instead of English fallback). This GENERALIZES to
nl/es/pl (same batch move per language). ~hundreds of keys → automate, don't hand-type. Parity gate:
each key ×N langs. This is the "chrome follows" step of the language architecture [[lp-language-architecture]].

**BL-38 — MULTILINGUAL SUPPLIER QUERY (queued 2026-07-13, Angel).** Live supplier search sends the query in each site's OWN language so an English/French-typed term still hits the German sites: auto-translate the query → German for FourTwenty (Magento German index); query Artemis in multiple languageIds (not just EN=3). Reuse the Ollama translate from BL-36 (`product_translations._translate`) or a tiny query-translate helper; cache per (term,lang). Login language is irrelevant — it's the QUERY word that matches. Ties [[banco-live-supplier-search]].

**BL-39 — KC LOGIN POLISH: 4-LANGUAGE SELECTOR + HEAD-SHOP THEME + SBX-vs-PROD LOOK (queued 2026-07-13, Angel: "kc logins need 4 language selections too").**
The Keycloak login page needs the EN/DE/IT/FR picker like the POS app. MOSTLY A REALM-CONFIG TOGGLE, not a
translation job: the `lapiazza` login theme is `parent=keycloak.v2`, and Keycloak ships built-in login
translations for en/de/it/fr — so the standard fields come FREE. Steps: (1) on each POS realm set
`internationalizationEnabled=true` + `supportedLocales=[en,de,it,fr]` + a `defaultLocale` (kcadm or admin API;
sandbox→staging→prod, verify login still works after each) → the language dropdown renders automatically;
(2) check the custom `BorrowHood/keycloak/themes/lapiazza/login/error.ftl` for any HARDCODED English → move to
message keys if so; (3) style the dropdown in `lapiazza.css` to match the branded wolf theme. Test login in each
lang. Theme path `BorrowHood/keycloak/themes/lapiazza/login/`. **ALSO (Angel 2026-07-13): head-shop LOGIN theme + make SBX vs PROD obviously different** so you never fat-finger the wrong env. Plan: (a) head-shop vibe background baked into `lapiazza.css` — start CSS-only (dark green/gold gradient, self-contained; NO external hotlink on a login page), swap a real photo later (Unsplash per [[decision-unsplash-not-pollinations]]); (b) ENV DIFFERENTIATION via per-realm loginTheme — prod realm = clean theme; sandbox realm = a `lapiazza-sbx` variant with a bold `SANDBOX` ribbon + different tint (or a custom `login.ftl` showing `${realm.name}`). Set each realm's loginTheme (kcadm), restart KC, test login on all 3 envs. **✅ FULLY DONE + LIVE 2026-07-13:** built `BorrowHood/keycloak/themes/banco/` (head-shop green+gold, wolf emblem, gold button, styled locale dropdown) + `banco-sbx/` (parent=banco; amber wash + diagonal SANDBOX ribbon + 'test environment' subtitle). lapiazza theme UNTOUCHED. Files are UNTRACKED in the BorrowHood repo (commit there when wiring). Preview artifact published for sign-off. REMAINING (risky half, do with Angel watching): commit themes in BorrowHood + mount into the KC container, set loginTheme per realm (prod=banco, sandbox=banco-sbx) + enable i18n/supportedLocales, restart, TEST each login. **→ ALL DONE & VERIFIED:** 3 themes built (banco green / banco-staging blue / banco-sbx amber, wolf emblem, self-contained), committed in BorrowHood (`c1fbe7e`), mounted into KC (compose.uat.yml, per-theme binds), KC recreated healthy. Realms wired: kc-production→banco, kc-staging→banco-staging, kc-sandbox→banco-sbx, all i18n en/de/it/fr; **borrowhood/lapiazza UNTOUCHED**. Verified at HTTP: stylesheets+wolf-logo resolve via parent chain, 4-lang selector renders. Angel to browser-confirm the look on each env's /pos (logged out). Ties [[banco-kc-email-theme]] [[banco-login-screen-and-mailhog]] [[banco-catalog-content-translation]].

**🔴 BL-39.1 — the themes shipped BROKEN and "HTTP-verified" hid it (2026-07-14, Angel: "you can't see what you type… it's not workable").** "Stylesheet returns 200" is not verification. What was actually wrong, measured in headless Chrome on the LIVE page: **username + password rendered #151515 on the dark card (1.17:1 — invisible)**. Cause: PatternFly v5 puts `pf-v5-c-form-control` on a **`<span>` WRAPPER**; the real `<input>` is a CHILD with its own `color: var(--pf-v5-c-form-control--Color)`, and PF force-maps LIGHT tokens inside form controls → `#151515`. Our `color:` on the wrapper never reached it. **Fix: drive the PF TOKENS.** Same failure mode elsewhere (checked all the seals): realm name drew pure black (`keycloak.v2` emits NO `.kc-logo-text` — the whole emblem/wordmark block was DEAD CSS and **the wolf had never rendered once**); "Forgot Password?" sat in `.login-pf-settings` (a SIBLING of `#kc-form-options`) so it fell back to PF blue; reveal button + locale menu rendered as white boxes; `:focus` can never match a `<span>` (needs `:focus-within`); `wolf-logo.png` was a **JPEG with no alpha** (white square). Also: KC serves theme CSS with **`max-age=2592000` (30 days)** — a server fix alone reaches nobody, and the old path kept serving stale bytes through Caddy even after restarting KC *and* Caddy. **→ VERSION THE FILENAME** (`banco-v2.css` / `staging-v2.css` / `sandbox-v2.css` + `theme.properties`); bump the suffix on every visual change. **✅ SHIPPED + LIVE all 3 envs 2026-07-14** (BorrowHood `92030eb` + `f823ae4`, committed locally, **NOT pushed** — origin/main is 1 ahead with an unrelated locandina fix). Live-page audit: every text element now **≥10:1** with text typed into the fields (was 4 unreadable). Accent colours are `:root` tokens now, so the child skins restate ~8 tokens. Rollback snapshot: `/root/kc-theme-backup-20260714` on the box. Detail: [[lesson-patternfly-v5-form-control-token]].

**✅✅ BL-39 HUMAN-GREEN — Angel signed off ON HIS PHONE, 2026-07-14: *"check the login on my phone and i did it and it works pam and felix no issues."*** Both accounts, real device, real prod. **THIS is the sign-off — not the contrast numbers, not the HTTP 200.** The machine gates say a human *can* read it; only a human logging in says it *works*. Both were needed, in that order. ([[lesson-machine-green-is-not-human-green]] — and note Angel caught this bug, not the gates: the gates exist so the NEXT one doesn't need him to.)

**✅ BL-39.3 — THE RELEASE GATE: a deploy now has to PROVE it worked (2026-07-14).** Angel: *"add the audit to the release gate so it runs every deploy"* → *"yes fold the app check into the gate too."* The root cause of the black-on-black login was never CSS — it was that **"stylesheet returns HTTP 200" was accepted as verification.** So the proof is now in the deploy path, not in anyone's memory. **Front door (from the LAPTOP, not the box):**
```
make deploy ENV=<sandbox|staging|prod> [REF=feat/x]   # deploy + BOTH gates
make app-gate    ENV=prod [SHA=87f25e1]               # gate 1 standalone
make login-audit ENV=prod                             # gate 2 standalone (no ENV = all 4 screens)
```
**Gate 1/2 `scripts/ops/app-gate.py`** — did the APP come back, and is it serving the code we shipped? The login gate alone had a hole: it proves *Keycloak's* page, but a deploy restarts the **app** (Keycloak isn't restarted at all), so it would pass while the app came back broken. Probes `/health/healthz` (**the exact path the container healthcheck uses — `/health` 404s**), `/pos`, and checks **the RENDERED build stamp == the deployed SHA** — the sharp one, because `build_info` caches per process, so a restart that quietly kept the OLD process still passes health *and* returns 200. **It caught a real failure on its first prod run: Docker said `live + healthy ✅` while the app was still returning 502.** It retries past that window. **Gate 2/2 `scripts/ops/kc-login-audit.js`** — can a human READ the login screen (drives Chrome, TYPES into the fields, measures rendered contrast). **Both gates BLOCK** — verified with a negative test (wrong SHA → exit 1 → make exit 2), not assumed. Hand-running `deploy-banco.py` on the box skips both, so it now prints a loud **"⚠️ LOGIN GATE NOT RUN"** (suppressed via `BANCO_LOGIN_GATE=1` when `make deploy` has it covered — a warning that cries wolf gets ignored). Ladder walked + levelled: **sandbox / staging / prod all serving `b1769 · 87f25e1`**, both gates green, prod backup verified-restorable (53 txns / 5174 products / 163 lines). Detail: [[banco-login-audit-gate]] [[banco-deploy-rails-and-prove-discipline]].

**✅ BL-39.2 — LA PIAZZA LOGIN THEME: AUDITED CLEAN 2026-07-14 (Angel was right, it works).** Run same evening once Felix was off the critical path. 11 text elements measured on the live page with text typed in: **all readable** — username/password **18.26:1** on the white card, lowest is "Remember me" at 4.57:1 (grey-on-white, just over the line; only a concern if that card ever goes dark). The black-on-black bug did **not** touch it — `lapiazza` is a separate theme. **All 4 screens PASS, exit 0.** ⚠️ **But the gate itself lied twice before it told the truth** — see the commit: it first inferred backdrops from computed background-colors (transparent under a gradient → it measured **ZERO elements on LP and printed PASS**, fake green), then a single sample pixel hit the checkbox next to "Remember me" and invented a 1.01:1 failure. It now hides all text, screenshots, and samples the **real rendered pixels** on a grid, and **fails loud if it measures fewer than 4 elements**. Dogfood your own gate before you trust it. *(Original parked note below, kept for the trail.)*

**🟠 BL-39.2 (original, PARKED by Angel 2026-07-14: "check it another time, right now we focus on Felix").** The `lapiazza` login theme (`BorrowHood/keycloak/themes/lapiazza/login/`, realm `borrowhood`, host lapiazza.app) is a **separate theme** from the banco ones and has **NOT been audited** for the PatternFly v5 wrapper bug. Angel reports it "used to work fine" — and it probably does, since LP has **real traffic (~33k views/30d)** and nobody has complained. **But "it looks fine" is exactly the assumption that shipped the banco bug — that theme was never MEASURED either.** ⚠️ Not verified. Not claimed green.
**Do this when Felix is off the critical path — it is ONE command, read-only, no deploy:**
```
node scripts/ops/kc-login-audit.js lapiazza-prod --shots /tmp/kc
```
Exit 0 = every text element readable. Exit 1 = something is unreadable, with the element named. **THE RULE GOING FORWARD (Angel: "test logins and they just work, no issues ever"): no login theme ships on ANY env until `node scripts/ops/kc-login-audit.js` exits 0.** It types into the fields and measures rendered contrast on the LIVE page — because HTTP 200 on a stylesheet is not verification, and that is precisely how the black-on-black login reached prod. Run it for all envs with no args. Also remember: KC caches theme CSS for **30 days** — every visual change needs a **new filename** (`-v2` → `-v3`), or nobody sees the fix. Ties [[lesson-patternfly-v5-form-control-token]] [[lesson-machine-green-is-not-human-green]].

**BL-36 multi-language DESCRIPTIONS ✅ SHIPPED PROD 2026-07-12 (`58fef52`, backup-gated, re-probed: native FR/DE/IT on real Artemis items).**
Sign in a language → description follows: **Artemis serves DE/EN/FR/IT free** (native), else Ollama +
cache. FR content-language switch fixed (isLang() at every gate). **→ Ship to prod (backup-gated) —
Angel confirmed it works.** Follow-ups (memory `banco-catalog-content-translation`): fill-at-adopt +
backfill script (on-demand only today); needs_review queue for machine translations.

---
## 🃏 PREV DECK — 2026-07-12 · BL-36 MULTI-LANGUAGE DESCRIPTIONS (design)

**Live supplier search (BL-35) SHIPPED PROD ✅ — next up is multi-language product descriptions.**
Full design + verified facts in memory **`banco-catalog-content-translation`** (updated 2026-07-12). Plan:
1. **`ADD COLUMN products.description_i18n jsonb`** — a `{en,de,fr,it,nl,es,…}` map (adding a language later =
   config + backfill, ZERO migration). Careful ALTER on sbx→stg→prod ([[schema-create-all-alembic-drift]] landmine).
2. **Artemis serves DE/EN/FR/IT NATIVELY** (verified — fetch `/de/produkt/ /en/product/ /fr/produit/ /it/prodotto/`)
   → the shop's own catalog gets 4 langs FREE, no LLM. Fill at adopt + a backfill script.
3. **NL/ES (+PL?) & German-only suppliers (FourTwenty/Near Dark)** → Ollama-translate, **on-demand + cache**
   (first view in a lang → 1 call → store in the map → instant after). Do NOT pre-blast 5,157 × N langs.
4. **Display** `description_i18n[_posLang] || ['en'] || description`. (Chrome i18n has en/it/de; fr/nl/es = later, bigger.)
Why now: adopting a FourTwenty item gave English-signed-in Felix a GERMAN description — the language gap is the
last rough edge on the find-first/adopt flow.

---
## 🃏 PREV DECK — 2026-07-12 night · ① STALE DATA ✅ FIXED → ② LIVE SUPPLIER SEARCH ✅ SHIPPED PROD

**The root cause of Felix's "I hold the product but Banco can't find it" frustration = STALE / INCOMPLETE data**
(reference table missing common items like Tycoon Gas; Artemis rows use minted barcodes, not the real EANs on
the cans). NOT bad luck. Full detail + the whole plan: memory **`banco-live-supplier-search`**.

**① QUICK WIN — ✅ DONE 2026-07-12 (`50e6f2e`):** refreshed the FourTwenty **reference feed** on ALL 3 envs
(sandbox/staging/prod), **7,272 → 10,282 rows (+3,010)**. Real root cause found: the original load applied a
*headshop-only category filter* that silently dropped the whole **Indoorgrowing** group (2,593) — where FourTwenty
files the **Tycoon Gas 250ml** (real EAN `4035687900004`). reference_products is the LOOKUP master → no category
filter. Fixed `import_reference_catalog.py`: auto-detect `;` delimiter, `--sku-prefix FT-` (stable ref_key → upsert
not duplicate), native supplier-feed header guesses, before→after counts. **Proven on prod:** name "tycoon" →
Tycoon (0.412) ✓ ; barcode scan `4035687900004` → Tycoon exact ✓. Backup-gated (39/5157/131 restore drill passed).
- ▶ The Nov-30 snapshot is 7 mo old — a periodic **live** dropship-feed pull (`dropship_productfeed_v2.csv`) belongs
  in ② / the supplier-sync framework.

**② LIVE SUPPLIER SEARCH — ✅ SHIPPED PROD 2026-07-12 (`bedc44c`, BL-35):** local miss → 🌐 search
FourTwenty (Magento page — their AJAX search WAF-blocks us) + Artemis (JSON `searchTerms` API, English) +
Near Dark (Shopware 5, EUR) concurrently → adopt fills name/photo/EAN/price + **tier ladder** and self-heals
`reference_products`. "⤵ Use all these details" on the compare panel; thin local picks auto-enrich live
(English pref). Proven on prod (3 suppliers, 0 errors). `src/services/supplier_search/`, 9/9 unit tests,
UAT `docs/testing/banco/BANCO-SBX-LIVE-SUPPLIER-SEARCH-UAT.html`. Full detail: memory `banco-live-supplier-search`.
- ▶ Follow-ups: 💱 currency conversion (memory `banco-currency-conversion-plan` — flat plan-rates so Near Dark
  EUR shows ≈ CHF); periodic LIVE dropship-feed pull; multi-image "grab them all"; ~7-8s latency (lazy-enrich).

**✅ SHIPPED PROD TODAY 2026-07-12 (`41fc6d4` · all envs parity):** find-first snap (librarian) + BL-33/34
(inactive items surfaced + reactivate) + 🔎 Search-similar everywhere + **language-agnostic match**
(English can-read → German catalog via word_similarity on the English descriptions). Tier v2, BL-31, tier-editor
console-flood, login-leak also shipped earlier today. Detail: memory `banco-photo-to-product-ai` / `banco-tier-pricing`.
- ▶ Loose end: **BL-33 + BL-34 are FIXED in prod but still show `pending` in the cockpit** — mark them done.
- ▶ Also banked: persisted comparison notes/comments · multi-image "grab them all" · FourTwenty-reference is the
  cache (self-heals via live-search adopt).

## 🃏 ON DECK — 2026-07-11 · THE CATALOGUING WORKSTATION (spec written)

**The rig + the method for getting Felix's ~2,000 items in properly.** Spec:
**[docs/BANCO-CATALOGUING-WORKSTATION.md](BANCO-CATALOGUING-WORKSTATION.md)**.

**THE DOCTRINE (the thing that changed today):** the ring-binder idea is OUT — **paper is a *render*
of the DB, never a second source of truth.** A hand-filed binder rots the day a price changes. The three
needs hiding inside it split cleanly: *"which items are done?"* → a **query** (BL-98) · *"a book on the
counter"* → **`scripts/generate_catalog.py` already exists** — print it Friday, bin it, print a fresh one ·
*"ring up the no-EAN stuff"* → **BL-97 House Scan Sheet** (the one thing that earns its paper).

**🔫 SCANNER — DECIDED: 2× NetumScan NSL8, CHF 98 total.** (Supersedes both the 2026-07-06 *"DECIDED: DS8178"*
line AND yesterday's DS2208 lean — Angel walked the whole Digitec bestseller list and found the better gun.)
**The NSL8 does BOTH jobs in one CHF 49 device:** spec reads *"Cable, Radio Frequency (RF), Wireless"* and a
reviewer confirms — *"operated either via a USB-C cable or a USB-A dongle."*
- 🔌 **Wired at the till** (a keyboard — no battery, nothing a cashier can break) · 📡 **cordless on the floor**
  (2.4G **dongle**, not Bluetooth → presents as plain HID, **no pairing to drop after a reboot**).
- 📱 **CMOS imager reads phone SCREENS** — the listing names it: *"solves the problem that laser scanners
  cannot identify screen code."* **This is exactly why the 1D LS2208 (CHF 64) was rejected.**
- 📦 **Stores 3,000 codes OFFLINE** = a real batch mode → **BL-97 House Scan Sheet + stock counts, solved in
  hardware.** Neither Zebra nor Honeywell does this. Plus **auto-sensing** (hands-free presentation) mode.
- 📊 NetumScan: **0.6% defect** (beats Zebra 0.7%), **0-day warranty turnaround** (beats Honeywell 1 day),
  **1.7% return rate = 2nd best in the category.** Buy **two** → drop-in spare + clears free shipping.
- ⚠️ Spec table says *"Laser"* — **wrong** (machine-translated field). A laser physically can't read QR/DataMatrix
  and this does. The description says CMOS imager; trust that.
- 🪜 **Escalation only if it fails the acceptance bar** (must read ~99% of OUR printed labels): **Honeywell
  Voyager 1470g "Cable · W. Stand" CHF 80.90** (cable+stand named in the listing; 0.5% defect, 1-day turnaround).
- ❌ Rejected + why (don't re-litigate): **LS2208** 1D=can't read screens · **DS2208** two reviewers got it with
  **no cable** (+CHF 30) + no Swiss-QR · **PhoneLook CHF 107** "not enough data" on ALL 3 warranty metrics ·
  **Inateck BT** 0 ratings, BT-only · **DS9308** CHF 128 (NSL8 auto-sense gets most of it) · **Elcode Swiss QR
  CHF 278** = the only real Swiss-QR-bill reader — **parked**, we don't scan invoices. Full table: spec §1.1.

**🏷️ LABELS — sizes × flags, NOT 12 templates.** 3 physical sizes (S price-sticker / M shelf-talker /
L box-card) × content flags (`show_price`, `show_photo`, `show_barcode`, `show_human_code`, `show_age`,
`show_unit`, `show_desc`). "Big label with a picture + description" isn't a template — it's
`size=L, show_photo=1, show_desc=1`. **One renderer reading data.** `show_human_code` always ON → a failed
scan is never a dead end. `show_age` **always derived from `product_class`**, never hand-set.

**🐯 BL-98 · ENRICHMENT QUEUE — ✅ BUILT (local, green) — the back-office migration cockpit.**
Shipped as **a MODE on `/pos/cleanup`**, not a new screen (the prior held). `?mode=bench` →
the workbench: **every** unfinished product (sold or not), gaps = **photo · description · category · cost**,
batched (`limit`/`offset`, default 20), a **`?category=` shelf filter** (a batch = a *shelf*), and the
**`done / total / remaining` counter — the number that replaces the paper binder.** ONE SQL gap-clause feeds
both the list and the counts, so the counter can't drift from the list. `mode=sold` unchanged.
- 🔐 **Role = shop manager** (Angel's call) → rides the existing `require_manager_or_admin()` gate ⇒ **zero
  identity change** across the 3 realms. A `cataloguer` role stays a 1-line change if a temp ever does the migration.
- 🧪 `tests/pos/test_pos_cleanup_queue.py` **12/12** (6 original + 6 new bench) · `make test` **1844 pass / 3
  known-flaky** · POS suite baselined against clean HEAD → **0 new failures**. sw.js **v69→v70** (i18n keys!).
- 🌍 i18n en/it/de — **45 keys each, parity-checked** (a missing key renders raw — the BL-28/29/30 bug class).
- ▶ **NOT deployed** — needs Angel human-green on sandbox, then the gated ladder.

**🐯 BL-99 · Label renderer size×flags** — widen `scripts/generate_label.py` (today: one fixed 62×37,
EAN-13→Code128, Puppeteer PDF, `brother_ql` → QL-820NWB). Bones are right; just needs the matrix. Not started.

**🧍 ANGEL — next:** (1) **order 2× NSL8 (CHF 98)** + the Brother QL-820NWB + **removable** DK rolls.
(2) **Human-green BL-98 on sandbox** → say go and it ships the ladder. (3) Lightbox — buy (~CHF 40) or white
paper + desk lamp first (CHF 0, recommended)?

## ✅ SHIPPED PROD 2026-07-12 — FIND-FIRST snap (the migration fix) (`c4ee6d2` · b1671)
**The grinder lesson, solved.** Photo → the AI reads the item → Banco SEARCHES the real catalog
(`products` = Artemis truth, already imported + `reference_products` = FourTwenty) and shows what's
ALREADY there, ranked by an HONEST trigram match score — instead of INVENTING a product with the
model's inflated self-confidence. The AI is a librarian, not an author. `GET /products/find-matches`
+ `POST /products/snap-find` + `_find_catalog_matches` helper (6/6 black-box tests). Catalog picker
("Is it already in the shop?" — catalog rows open the existing product, no dupe; FourTwenty rows fill
the add-form; "None → new item" fallback). Pick a reference → use the supplier's PRO photo (not the
phone snap). Compare panel upgraded: reference name + price-delta + supplier cost + click-to-enlarge.
Shipped sandbox→staging→prod, backup-gated (39/5157/131), re-probed. Detail: memory `banco-photo-to-product-ai`.
- ▶ **NEXT (banked):** persisted comparison notes/comments (needs storage) · multi-image "grab them
  all" from a supplier feed · finish the AL-scraper deepening (the reference already carries the data).

## ✅ SHIPPED PROD 2026-07-12 — 4 hypercare fixes (tier-editor flood, BL-31, login leak, detail header)
From Angel's prod hypercare capture sheet, all backup-gated + re-probed: **tier v2** (`dcacb03`) ·
**BL-31** bundle-editor-save fold-qty1 (`579275a`) · **tier-editor Alpine `t()` scope collision** that
flooded the console + clunky detail-ladder header (`8ef837f`) · **login demo-credential leak** env-gated
to sandbox-only (`06c1aff`). Detail: memory `banco-tier-pricing` / `banco-photo-to-product-ai`.

## ✅ SHIPPED PROD 2026-07-12 — BL-26 tier pricing v2 (`dcacb03` · b1656)
Two things the v1 UAT surfaced, both fixed + shipped: (1) **per-unit + BUNDLE modes** ("3 for 8,00" vs "10+ →
4,50 each") — `tier_mode` column, mode-aware editor toggle, correct money math (bundle = pack_total/min_qty,
line-level rounded so "3 for 4,00" == exactly 4,00); (2) the **live cart preview** (`tierLineTotal` mirrors the
server → cart shows EXACTLY what the till charges, Felix's idiot-proof ask) + the **tier ladder on BOTH product
detail cards** (sell + catalog — Felix asked 3× to SEE it, like the Artemis site). Fixed a mode-aware
`validate_price_tiers` bug (bundle starts at qty≥2, not qty 1) that blocked the editor from saving bundles.
2 UAT rounds (v1 HOLD → v2 10/0). sw v74→v77. `make test` 1856 pass. Backup-gated (`banco_prod_20260712_1230`,
restore-verified 39/5156/131), re-probed serving each rung. Detail: memory `banco-tier-pricing`.
- ▶ **NEXT-ROUND (banked, Angel deferred):** scan-cart manual-discount preview discounts the full subtotal while
  checkout/server exclude tiered+promo lines (pre-existing shown≠charged in the SCAN preview only; charged is
  right). Fix with the **double-dip override** (manager may stack a discount on a tier line — Felix's call) +
  a **"tier 1/tier 2" line label**. Not a blocker.

## ✅ SHIPPED PROD 2026-07-11 — BL-26 papers tier pricing (`daa3ab5` · b1645)
Per-product quantity breaks (papers-first): buy N+ → that tier's unit price applies to the whole line (a
PRICE, feeds VAT/totals). **A volume break (min_qty≥2) is FINAL** — no member/manual discount stacks (tiered
line excluded from the discount base). Editor = repeatable qty→price rows in the catalog Edit modal (en/it/de).
`price_tiers` JSONB + `tier_unit_price()`/`validate_price_tiers()` (16 unit tests). `make test` 1844 pass.
Shipped sandbox→staging→prod, **backup-gated** (`banco_prod_20260711_0940`, restore-verified 39/5155/131),
**re-probed** each rung (build · sw v70 · tier i18n · price_tiers column on prod). Sandbox tier-UAT green
(GIZEH ladder 1/3/5/10). Detail: memory `banco-tier-pricing`.
- ⚠️ **AI-VISION BRAIN COST (Angel flagged 2026-07-11):** the photo-lookup uses Google's free tier → caps ~10
  scans → then metered. For the photo-first migration (2k+ scans) need unlimited/fixed. **Box is CPU-only
  (2 cores / 7GB) → local vision NOT viable here.** Options: Ollama Turbo vision (flat-rate, if it has a VLM) ·
  Gemini-Flash *paid* (~pennies for the whole migration, predictable) · Groq (free/fast, rate-limited). The AI
  desc is only a SEARCH-SEED (human confirms) → cheaper is fine. Detail: memory `ai-backup-brain-plan`.

## ✅ SHIPPED PROD 2026-07-11 — non-destructive supplier price reference (`c0c2768` · b1637)
**First "ON DECK" build off the price-comparison spec.** Adopting a reference (Mosey/420) item used to
DISCARD the supplier's suggested price (folded into sale price, gone). Now it persists to
`ProductModel.supplier_price` (no migration — column pre-existed) and the catalog EDIT view shows it as a
grayed **"Supplier ref: CHF X · ✓ you beat it / — above supplier"** hint (en/it/de). `make test` 1828 pass
(3 known-flaky). Shipped sandbox→staging→prod via `deploy-banco.py`, **backup-gated**
(`banco_prod_20260710_2216.sql.gz.gpg`, restore-verified 39/5155/131), **re-probed serving** each rung
(build stamp · sw v68 · i18n keys). Human-green: Angel on sandbox ("its fine").
- ✅ **Currency check CLOSED (2026-07-11) — NOT a bug.** Verified: prod store = *Artemis Lucerne* **CHF/de-CH**
  (correct); sandbox = *Artemis Roma* **EUR/it-IT** (the Italian demo instance — € by design). So sandbox
  doubles as the multi-locale/currency test rig; the supplier-ref rendering "30,50 €" in it-IT was a real
  i18n pass. No fix needed.
- ▶ **NEXT slices** (same spec): the two-supplier side-by-side (Tamar vs 420) + the beat-the-online-price
  view; and BL-26 papers tier pricing. Detail: memory `banco-supplier-price-comparison-spec` / `banco-tier-pricing`.

## ✅ SHIPPED PROD 2026-07-10 — hypercare BL-16→22 batch + Felix in-shop fixes (b1632 · 79e73ee)
**A full "ON DECK" → ship day, twice through the gated ladder, human-green both times.** The AI hypercare
cockpit did the triage; Tigs was the engineer; Angel steered + tested on the phone with the branded test sheets.

**PART 1 — the shop's own tickets BL-16→22 (main `467ac85`, b1627).** Six tickets Felix/Ralph filed from the
floor, all live: **BL-16** type-in qty at the cart line · **BL-17** image backfill → MinIO (cron NOT yet wired
on prod — 5,111 hotlinks still to drain; turning it on is an open 🧍 decision) · **BL-18** description-cron
un-jammed (rotation via `description_checked_at`; self-heals on its next run) · **BL-20** CSV viewer + a **VAT
summary in real Turnover/VAT columns** (memo rows — Banana import untouched) · **BL-21/22 the Order Book**
(reorder pencil-list + per-line supplier pick + velocity suggestions) · plus **role-based permission text**
(dropped hardcoded "Felix/Ralph" everywhere) + **HTML-in-i18n render fixes** (intros were showing raw `<b>`).
New table `reorder_items` + columns `description_checked_at`/`image_checked_at` (create_all + IF-NOT-EXISTS
ALTER). 4 UAT rounds (v1 sheet + R3/R4 quick-checks). Backup `banco_prod-prehypercare-20260710_110644.sql.gz`.

**PART 2 — Felix's live in-shop round BL-24→30 (main `79e73ee`, b1632).** Filed WITH Felix on prod, triaged in
the cockpit. Fixed + shipped: **BL-25** no phantom discount on a tobacco/alcohol-only cart ("No discount —
tobacco/alcohol only"; also `Number(discount)` kills the "010%" label) · **BL-27** scan a barcode into the
Order Book — **visible 📷 button** (shared PosScanner camera) + gun/wedge Enter + file fallback. Backup
`banco_prod-prefelixfix-20260710_133114.sql.gz`. Re-probed clean (R5 sheet green).
- 🟢 **BL-28/29/30 = NOT bugs — stale SW translation cache** (raw `reorder.toast_added` toasts). Resolved by a
  hard-refresh (Ctrl+Shift+R). Lesson: a POS deploy that adds i18n keys needs the operator to hard-refresh,
  because the SW cache-firsts `pos-i18n.js` and doesn't auto-activate. **🧍 Felix: hard-refresh to pick it all up.**
- ⚪ **BL-24 ".." descriptions = won't-fix** — Artemis's own source ellipsis (10 of 3,201, mostly stylistic).
- 🎟️ **BL-26 TIER / QUANTITY-BREAK PRICING — PARKED for the Lion's Den discussion.** Felix wants auto
  quantity-break pricing (e.g. 1 pack papers = 4.-, buy **3 → 10.-**, 10 → even better). **Reference: Artemis's
  OWN website already does this** — model their tiers/UX. Real feature, needs design (how to make it easy at the
  till + how it interacts with the promo-restricted/member-discount rules). Discuss back at HQ. Detail → memory `banco-crm-strategy` / a new `banco-tier-pricing` note.

## ✅ SHIPPED PROD 2026-07-09 — batch live (b1610 · 35ef4a0) + compliance sweep lesson
Batch deployed to prod, healthy, code proven (v57 + callback bypass + disclaimer gone). Backup-gated
(`banco_prod-prebatch-20260708_194247.sql.gz`). **The reclassify sweep was eventful — READ THIS:**
- ⚠️ **`reclassify_products` is NAME-ONLY → it UN-GATED context-dependent items** (CBD flower/hash + a
  nicotine vape whose 18+ came from the supplier CATEGORY, not the title). Caught in the flip review;
  **remediated** by re-gating every demotion from the backup (additive-only). **LESSON: never run a
  name-only reclassify as a compliance sweep on a live catalog — it's GATE-then-review or reference-based.**
- 🔎 The sweep also surfaced **pre-existing nicotine-mg leaks** (21 items: VAAL E-Pack / Instaflow O Pro,
  all 20mg) that were ALWAYS `standard` — classifier misses "E-Pack"/"Instaflow" + requires ecig-context
  next to the mg. Closed them via targeted UPDATE (non-CBD `NNmg` → tobacco_nicotine). Final audit: 0
  un-gated nicotine; every substance class 18+ (`bool_and=true`); accessories (cig cases/holders) correctly open.
- **✅ FOLLOW-UP SHIPPED PROD 2026-07-09 (b1612 · 4566169):** (1) classifier — a non-CBD `NNmg` strength now
  gates as tobacco_nicotine ON ITS OWN (no ecig-context word), closing the VAAL/Instaflow leak class (CBD
  3-digit-mg + 0mg + no-nic still veto); (2) `reclassify_products` gained **`--gate-only`** (never removes a
  gate) + **`--dry-run`** + loud ⚠UNGATE flagging. Verified on sandbox (gate-only KEPT 89 gates a plain sweep
  would drop). Backup-gated (`banco_prod-premg-20260709_063441.sql.gz`), gate 1828/3-flaky, 43 taxonomy.
  Prod gate-only sweep = changed 1 (precision reclass), **un-gated 0**. Final audit: every substance class
  18+, 0 un-gated non-CBD NNmg. **Compliance tooling is now safe — a live sweep can never un-gate again.**
- **🧍 Angel: spot-check prod catalog** (up-gates right, nothing legit over-gated) + **verify login one-press on Fairphone.**
- ✅ BL-18 description cron LIVE (`*/10min --limit 80`, first batch filled 67/80, ~5044 draining overnight).

## (batch contents, for reference)
Branch `fix/p0-otf-compliance-20260708` (build **b1609**), all deployed + proven on SANDBOX, prod
UNTOUCHED (Felix live on prod — batch tonight/tomorrow). **Code in the batch:**
1. **P0 compliance** — OTF tobacco can't be born un-gated (classifier `nicotin` + `_CIGAR` + `resolve_class_on_create` net). Proven e2e.
2. **BL-18 description cron** — `scripts/ops/artemis_description_backfill.py` scrapes real Artemis text. Proven (4/5 live).
3. **hide-stock** — dropped "(not a sell gate)" disclaimer on catalog card.
4. **login SW fix** — SW bypasses `/pos/callback` so OAuth `#token` survives (mobile "press Login twice"). ⚠ **Angel: verify on Fairphone.**
5. **18+ toggle bidirectional** — turning 18+ OFF on the neutral `age_restricted` bucket now un-gates (substance classes stay gated). Proven e2e.
6. **BL-17 photo diagnostic** — snapped-photo upload now names WHY it failed (self-diagnosing; not a blind fix).
Tooling (not deployed to prod): `seed_sbx_test_products.py` (40 SBXTEST- playground), `generate_catalog.py` (paper catalog), `generate_label.py` (v1 label, QL-820NWB).

**PROD-PUSH STEPS (gated, backup-gates prod):** (1) merge branch→main (or deploy branch to prod); (2) **backup prod first**;
(3) deploy; (4) **reclassify_products with EMPTY prefix (ALL products, NOT TAM-)** + reclassify_reference — **REVIEW the flip
list before committing** (the sweep un-gates some drifted accessories — correct but sensitive); (5) wire the BL-18 cron crontab
(`*/5 … --limit 80`); (6) re-probe + **human-green on Fairphone** (login one-press; snap a tobacco item → gates). Tests: 41 taxonomy + full gate 1824 (3 known-flaky).

## 🃏 ON DECK — DIRECTION FORK (2026-07-07 night)
**WHERE WE ARE.** Prod solid on `fb81028`, all envs in parity, tree clean. A HUGE day shipped + human-green:
cash type-in, member-discount (eligible-only + option B + Felix-owned tiers), full member CRUD + manual badge,
eligible-only manual discount, real compiled Tailwind (POS), minor-member gate fix, back-button guard. The
small polish is DONE — what's left are genuine DIRECTION choices (multi-hour, need Angel's steer, no urgent driver):
- **CRM/loyalty depth** — credits redemption UX, birthday rewards, member directory (builds on today's member work). `banco-crm-strategy`.
- **Offline/PWA resilience** — POS keeps ringing when the internet drops (real head-shop value). `banco-offline-and-pwa-plan`.
- **Finish Tailwind site-wide** — home/login/La Piazza still on the external CDN (POS is done). Bigger/different surface.
- **Fiscal (fiskaly TSE)** — go-live compliance (DE now / CH readiness). `banco-fiskaly-integration-brief`.
- Also parked: multi-department, full supplier-sync framework (see memory index).
This is also a fine STOP point — everything's clean.

## ✅ 2026-07-07 (night) — TAILWIND real build + MINOR-MEMBER gate fix SHIPPED PROD (`144a363`)
(1) Replaced the 451 KB in-browser Tailwind Play engine with a REAL compiled build (build/tailwind → 91 KB
`src/static/pos/tailwind.css`, `make tailwind`); kills the CDN warning + runtime compile. Rule-9 safe (zero
concat classes), coverage-verified + puppeteer-verified 4 pages + the age modal. (2) Minor-member age gate
LOOP fixed at root: `/checkout/{id}` now returns birthdate/age_confirmed/is_of_age so the client isn't blind;
a DOB-proven minor → STOP modal shows "under 18" + Remove-member, walk-in HIDDEN (no loop). Server was always
authoritative. SBX human-green (Angel tested "upside down"); prod re-probed clean. NOTE: non-POS templates
(home/login/La Piazza) still use the external Tailwind CDN — separate follow-up.

## ✅ 2026-07-07 (late) — SBX UAT 27/29 + 2 findings fixed & shipped (`6627449`)
Angel ran the fav test sheet in SBX. Two findings, both fixed: (1) a MANUAL discount on a tobacco/alcohol
cart hard-blocked the whole sale (400) — now applies ELIGIBLE-only like the member discount (Angel picked
option A; cigarettes full price, the rest takes the %, no dead-end). (2) Edit-member modal was missing the
"18+ confirmed" + "send offers" toggles — added (marketing_consent + age_confirmed in modal/schema/GET).
Known non-today item noted: Tailwind Play CDN warning in prod console (rule-9 candidate, separate build task).

## ✅ 2026-07-07 (late) — CASH CHECKOUT: TYPE-IN AMOUNT + ADDITIVE NOTES (`c05877d`)
Swiss pay OVER (a 50 for gum; 75.00 for a 72.50 bill) and combine notes (50+20=70). Old cash UI only
had fixed single buttons → cashiers faked "exact". Now: free-form "Amount received (CHF)" input (primary),
note buttons +5/+10/+20/+50/+100/+200 that ADD up, EXACT + CLEAR. Server always accepted any amount_tendered
(proven e2e). Member CRUD also E2E-verified 11/11 (create→edit→tier override→deactivate RBAC→reactivate).

## ✅ 2026-07-07 (late) — FULL MEMBER CRUD SHIPPED PROD (`dd097c9`)
The edit button was a stub ("coming soon") — backend PUT existed but was never wired. Now: ✏️ Edit Member
modal on /pos/customer-lookup (handle, name, email, phone, IG/TG, DOB, notes) → PUT /api/v1/customers/{id};
🏅 manual TIER OVERRIDE (any till role — Angel's call) via a tier selector ("Auto" = spend-based, or lock at
a tier); 🚫 Deactivate (soft-delete, manager/admin only) + reactivate endpoint. New `customers.tier_locked`
column (ALTER-migrated per env before deploy — create_all won't add it); `recalculate_tier` keeps a locked
tier's NAME but the % tracks settings; `pct_for_tier()` helper. Proven e2e: Pam sets Gold→survives a sale→
"Auto" reverts; combined edit persists; deactivate Pam=403/Felix=200. Unlocks the parked per-member override.

## ✅ 2026-07-07 (night) — MEMBER DISCOUNT ROUND SHIPPED PROD (`f75373a` + `a00b905`)
(1) Tier discount hits ELIGIBLE (non-tobacco/alcohol) subtotal only — cigarettes full price, lighter gets
the member %, ONE receipt; all-tobacco cart → 0 discount, still completes. (2) Option B: a member SUPPRESSES
the manual cashier discount (no stacking; checkout hides the buttons). (3) Loyalty tiers = DATA in Settings →
Discounts (Felix sets Silver/Gold/Platinum spend + %, admin-only). Proven e2e (bronze/silver/gold/platinum
exact centimes; live threshold change re-tiers on next sale). Unit tests added. Backup-gated; landmine
`tier1_threshold=0` reset on all envs before deploy. **SANDBOX demo ready:** BruceLee (Gold 10%, spend 1200)
+ Marlboro rot 7.10 + Feuerzeug BIC 2.50 → 7.10 + 2.25 = 9.35.

## 🃏 SUPERSEDED — 2026-07-07 eve · MEMBER DISCOUNT vs PROMO-RESTRICTION (done, see above)
**WHERE WE ARE.** Prod is SOLID: full Artemis catalog (5,111 items) live, badges + 18+ gate + readable
errors + blank-discount fix all shipped; Angel can close cash deals on prod, no blocks. Session compacted
here at a clean boundary.

**THE NEXT PROBLEM (Angel spotted it before it bit).** A tier member (Gold etc.) gets an AUTOMATIC
discount at checkout. But tobacco/alcohol are **promo_restricted** (Swiss law — no promo discounts).
Today the two discount paths DISAGREE:
- **Manual/cart discount:** already blocks promo-restricted lines per-line (`pos_router.py` ~2342-2348 /
  2703-2705, the `2b8aefa` fix). ✅ correct.
- **Member TIER discount:** applies `tier% × transaction.total` CART-WIDE (`~2514-2520` & `~2737`), never
  checks promo_restricted → would silently discount the cigarettes too. ❌ the gap.

**THE SENSIBLE DESIGN (agreed, discuss-confirm then build — NO two receipts):**
> Member discount applies ONLY to the **eligible (non-promo-restricted) portion**: `tier% × subtotal of
> non-tobacco/alcohol lines`. Cigarettes ring full price, the lighter gets −5%, **ONE receipt**. Makes the
> auto-discount obey the SAME per-line law the manual discount already does. All-tobacco cart → discount 0,
> sale completes at full price (no block).

**NOT a showstopper now** (Felix has no tier members yet) — becomes one the day he makes his first Gold.

**TEST PLAN (sandbox — do it there):**
1. Seed test members per tier: bronze / silver / gold / platinum (**Bruce Lee**) with discount %.
2. Rings per tier: (a) tobacco-only, (b) lighter-only, (c) mixed tobacco+lighter.
3. Verify: eligible discounted, tobacco full price, ONE receipt, totals+VAT correct, completes (no block).
4. Decide receipt wording ("member −5% on eligible items").

**Doctrine reminder:** talk design first, then build as a Block. Detail in memory `banco-crm-strategy` +
`banco-member-discount-promo-restriction`.

---

## 🐛✅ 2026-07-07 — "[object Object]" checkout-error bug FIXED + SHIPPED PROD (`bf021b2`)
Angel hit "[object Object]" in the checkout toast on prod (mobile; desktop looked fine). Diagnosed from
prod logs: not a crash — a run of `POST /pos/sales` **400s** (the 18+ age gate, expected) then two **422s**
(malformed payload) then a **201** (succeeded on retry). Root cause in the SHARED API helper (base.html):
FastAPI `detail` is a STRING for a business 400 (age/drawer/cap) but an ARRAY of `{loc,msg,type}` for a 422
validation error → `new Error(detail)` coerced the array to "[object Object]". **Fix:** parse the 422 array
into a readable "field: msg" (stringify any other object). Fixes the toast on EVERY POS page + makes 422s
self-diagnosing (names the offending field, e.g. `amount_tendered: Input should be a valid decimal`); the
400 age-gate string still shows verbatim. Ladder-deployed, backup-gated (`banco_prod-preerrfix-…`), trio-clean.
- ⏳ **Open:** the exact field that 422'd on Angel's mobile checkout is still unknown (never logged) — next
  occurrence will now NAME it in the toast → screenshot → fix root cause (likely an empty/null number field,
  amount_tendered / discount_percent, from the mobile keyboard). Watch for it.

## ✅ 2026-07-07 — ARTEMIS CATALOG IMPORTED TO PROD (5,111 items, fresh+clean)
Full Artemis catalog now on Felix's LIVE till: prod 33 → **5,144 products** (5,111 Artemis TAM-, all
active, all images). **1,036 flagged 18+, 0 class/flag drift** — FRESH import with the fixed classifier
(bd22f15 code) → classified right the first time, no reclassify. Cigarettes/nic-salt vapes = 18+, verified.
Backup-gated `banco_prod-preartemis-20260707_144338.sql.gz`; committed 5111, snapshot written. Delta-watch
already tracks the website (5,112) so future changes surface weekly.
- ⚠️ **Follow-up (not a blocker):** images are HOTLINKED from artemisluzern.ch (not in MinIO) — same as
  sandbox (proven). If Artemis blocks hotlinks / is slow, photos degrade → downloading to MinIO
  (`--with-images` / image_intake) is the robustness step. Also: all 5,111 have price but **no cost**
  (webshop doesn't expose it) → margin-blind until a manager fills it (sold ones surface in cleanup cockpit).
- ▶ **Optional later:** LLM enrichment (nicer descriptions + IT/DE translation via artemis_enrich_*.py) — separate merchandising layer, not run.

## ✅ 2026-07-07 — ALL CODE SHIPPED PROD (`bd22f15`, backup-gated, trio-clean)
Item badges + class-derived 18+ + cart→detail + nic-salt/Aisu classifier + delta-watch script — all
live on prod (backup `banco_prod-prebadges-20260707_144121.sql.gz`). Prod healthy, badges rendered,
build b1570. **Deliberately NOT bundled:** the Artemis 5,108-item CATALOG import into prod — that's a
DATA op on the live till (compliance review of 18+ on 5k items + own backup), kept as its own gated
step. Prod live catalog still = ~33 items; the badges/classifier now improve on-the-fly + adopt + the
FourTwenty reference path there. **Artemis→prod = next gated step (deploy done → import → review).**

## ✅ 2026-07-07 — Artemis DELTA-WATCH wired (scheduled, zero-write) + item badges shipped
- **Delta-watch LIVE:** `scripts/ops/artemis_delta_watch.py` (commit `014a694`) — weekly box cron
  **Mon 06:30** runs the importer DRY-RUN (no DB writes), diffs fresh vs previous snapshot, reports
  what changed on the Artemis shop (new / price-or-class-changed / gone) **with names**, to
  `/opt/ops/artemis-watch/latest.txt` + dated report. Baseline set = **5,112 products**; proven
  (2nd run = "✅ no change"). Snapshot lives in `/opt/ops/artemis-watch/` (outside git trees).
  Re-import stays **one-click + backup-gated** on purpose (no scheduled auto-commit → live till).
- **Item TYPE + 🔞 18+ badges** on search list, cart, and the tap-for-details card (build fc651ca+);
  18+ now DERIVED FROM CLASS (matches the gate, no column drift); cart lines tappable → detail card.
  UAT R2 = 18/18, Angel happy. Classifier also learned nic-salt/Aisu vapes + absinthe-spoon guard
  (FourTwenty 674→731, all legit); sandbox re-classified in place. Discount cap prod: cashier 15 / mgr 25.
- **▶ NEXT-ROUND PROJECT — Supplier-sync framework:** the bones exist (SupplierModel.adapter_type
  tamar|magento|csv|manual + 2 delta-aware importers + /pos/suppliers CRUD). To finish: adapter
  DISPATCHER (adapter_type→importer), a "Sync now" service+endpoint on the Suppliers page, an
  import-RUN LOG, a scheduler, and a **review queue** (scheduled commits land inactive/flagged until
  a manager approves — so 18+ is always human-checked before sale). Detail: memory `banco-supplier-sync-framework`.
- 🧍 **Angel: still free to poke SBX.** Prod Artemis import = gated next step (deploy fixed classifier → import → review → prod).

## 🧪 2026-07-07 — ARTEMIS CATALOG imported to SANDBOX (5,108 items, reviewed)
Full Artemis Luzern webshop catalog **committed to `banco_sandbox`** (was 274 products → now 5,108):
all with images, classified, **956 flagged 18+**, searchable/sellable. Ran `artemis_import.py --commit`
in the sandbox container (mirrors the gated plan: sandbox first, review, THEN prod).
- **Review caught + fixed** two supplier-vocab gaps (commit `c153c10`): nicotine vapes named the Artemis
  way ("…Refill", "…BM6000 20mg Nachfüllbehälter") leaked as standard → taught the classifier the vape
  brands + a brand-scoped refill rule; excluded absinthe *spoons* from alcohol. Re-classified IN PLACE via
  new `scripts/reclassify_products.py` (no re-crawl) → 42 fixed, **re-audit 0 leaks, 0 class/flag drift**.
  FourTwenty feed unchanged (674); 29 taxonomy unit tests green.
- 🧍 **Angel: poking around SBX to test** the catalog. `https://sandbox-banco.lapiazza.app` (login pam/felix).
- **NEXT (gated, Angel's go):** import to PROD — backup-gated, same steps. Note: all 5,108 have price but
  **no cost** (webshop doesn't expose it) → margin-blind until a manager fills it (sold ones surface in the
  cleanup cockpit). LLM enrichment (descriptions/translation) = separate later layer. Detail: memory
  `banco-artemis-catalog-import`. (This live-catalog import is SEPARATE from `reference_products` = 7,272 FourTwenty lookup.)

## ✅ SHIPPED PROD 2026-07-07 (pt.2) — live discount cap + UAT sign-off (`b93ee26`, trio-clean)
- **Discount cap reads LIVE from settings (client seal)** — `1851eb4` fixed the server; the till still
  hardcoded cashier=10 / checkout=25. New `GET /pos/discount-cap` (reuses `_max_discount_pct`); scan +
  checkout read it (dynamic "(Max N%)" label, input max, clamp, over-cap toast). Proven: admin sets
  cashier 33.33 → pam's till reads 33.33; manager 42 → ralph 42; admin 100. Tests `test_pos_discount_cap.py` (3).
- **UAT: Angel ran the HTML runbook `LP-UAT-20260707-BANCO-SBX` — 29/29, verdict SHIP.** (§7 `NS_BINDING_ABORTED`
  = benign Firefox nav-abort, not our code.) Sheet: `docs/testing/banco/BANCO-SBX-BATCH-TEST-SCRIPT.html`.
- ⚠️ **Prod caps NOW LIVE:** store#1 cashier=**33.33** / manager=**75** (Angel's test values). They actually
  take effect now — dial to shop-sensible numbers in Settings (👑 admin) if 33/75 is too generous.
- Backups: `banco_prod-prediscountcap-20260707_101706.sql.gz`.

## ✅ SHIPPED PROD 2026-07-07 — cockpit + UX batch (`5791639`, backup-gated, trio-clean)
Whole batch live on all 3 envs (backup `banco_prod-prebatch5791639-20260707_090138.sql.gz`):
- **Cleanup cockpit** (`/pos/cleanup`) — sold-but-half-baked queue, manager-gated + dashboard card w/ count badge.
- **18+ toggle** on quick-add (#1) + **tobacco enrichment** flag fix (#2) shipped earlier this day.
- **Consistent 🏠 home button** — icon-only, top-left, one per page, dupes removed (14 POS pages).
- **Always-on "➕ Add New CRACK"** on member lookup + **idempotent `/shift/start`** (killed the console 400).
- **Role-based settings** — cashier view-only (👁️ Store Info card) · manager edits all EXCEPT discount caps
  (server-stripped, not just UI) · admin all. Tests: cleanup(5)+settings-roles(5)+taxonomy(24)+age-gate(13).
- ⚠️ Carry-forward (non-blocking): KC login-page font cosmetics (PatternFly `kern: Too large subtable`
  warnings on the default `keycloak` theme) — separate KC-theme task, one-driver-on-KC. Not a bug.

---

## 🃏 ON DECK — 2026-07-06 NIGHT · WEDNESDAY HANDOVER ← START HERE

**WHERE WE ARE.** First in-shop UAT done (Layla, on prod, ~19 products, real sales). Two prod bugs
found IN THE FIELD and SHIPPED tonight (backup-gated + proven on prod):
- `346a2a2` member-enrol 422 on blank birthday · `1851eb4` discount-caps phantom-setting (cashier
  cap was 20 but till hardcoded 10 — now reads Settings live; Felix dials manager to 70 and it obeys).
Written + committed: **CUTOVER-PLAN.md**, **Ecolution→Artemis proposal** (1-pager + SWOT, rendered
artifact). Scanner **DECIDED: Zebra DS8178** (`DS8178-SR7U2100PFW`).

**💰 RATE LOCKED: CHF 120/hr standard · CHF 100/hr Felix (founder).**

**THE MODEL (one line):** the *prescription* delivered as a *subscription* — **CHF 100/mo**, hardware
bundled + managed server + backups/DR + unlimited users; **1-yr min** (bail early → pay the ~CHF 1,200
hardware); Felix's setup absorbed as acquisition; extra stores/features billed hourly. (Public rate
should be CHF 130–160/mo — 100 is Felix's founder price, don't make it the market anchor.)

**NEXT ACTIONS — in order:**
1. 🧍 **Angel · Tuesday (home):** more testing + jot coding ideas (drop them here or tell Tigs).
   Get from Felix: the **report-preset list** he actually wants.
2. 🧍 **Angel · order hardware from Digitec (you own this).** MINIMUM = the **gun** (Zebra DS8178
   kit) + **label printer** (Brother QL-820NWB) — both a MUST (label prints the OTF barcode on the
   spot). Receipt printer NOT needed (tablet screen / QR). Won't arrive by Wed.
3. 🧍 **Angel · Wednesday after lunch (~1 hr, parking-limited):** hit list, **~50 products, on the
   PHONE** (hardware not here yet). Log throughput (min/100) — it's the estimate for everything.
4. 🐯 **Tigs build queue** (when Angel greenlights each): P1 price-confirm · ~~P2 18+ toggle~~ ✅ SHIPPED
   PROD `a6f7b02` (see field-report #1) · P3 cleanup cockpit · R1 report fast-buttons
   (after Felix names them) · QR order-view receipt (small) · `/pos/scanner-test` + wedge-input check
   (before the gun lands).

**OPEN DECISIONS (Angel):** hypercare duration — parallel-run (pen+paper + POS + cash reconciled
daily) for **2 / 3 / 6 weeks?** then cutover · report presets (Felix names) · managers may edit
Settings? (self-cap risk — lean no) · Artemis catalog into prod (currently 0 Artemis, 100% FourTwenty).

**Detail:** `docs/CUTOVER-PLAN.md` (doctrines, ladder, roles, hardware, punch list) ·
`docs/business/BANCO-ARTEMIS-PROPOSAL.md` (BOM + SWOT) · the dated field-report block just below.

---

## 🃏 2026-07-06 FIELD REPORT (in-shop UAT with Layla, prod)

**First real over-the-shoulder run at Artemis (Trapani head shop). Signed in as `felix` (admin). ~5pm.
Scanned/added ~19 products, rang real sales, tried enrolling a member. Nothing was a showstopper.**
*Staffing reality: Pam off (likely permanent, sick) · Ralph on holiday · **Layla** — 8-yr veteran, called
back to cover, broken foot, "dynamite," says she can categorize/manage → she's **manager-level, not just
cashier**. Angel returns **Wednesday** (Layla likely Tue/Thu/Fri; Wed a wildcard) for a big run-through.*

**🐛 SHIPPED TODAY (all 3 envs, backup-gated, proven on prod `346a2a2`):** member-enrol 422 on blank
birthday — an empty `<input type=date>` posted `""` → Pydantic rejected the whole enrol before the
endpoint's own coercion ran. Fixed at both seals (schema `field_validator` blank→None on create+edit;
form strips empty fields). 0 orphan rows. See git `fix: member enrol 422 on blank birthday`.

**THE ORDERED TO-DO from the field (finish one before the next):**

1. **✅ 18+ checkbox on on-the-fly quick-add — SHIPPED ALL 3 ENVS (main `a6f7b02` / b1546), backup-gated,
   proven on prod.** Big obvious **18+ toggle** (default OFF, 🔞/✅, EN/IT/DE) sits between price and photo
   in the quick-add. **Seal-inspection catch:** the checkout age gate reads `product_class`, NOT the
   `is_age_restricted` column — a bare column flag would've been cosmetic. Fixed at source: new neutral
   **`age_restricted`** class (18+ with no promo/VAT/THC baggage, unlike tobacco/alcohol/cbd — manager
   re-classes precisely later in the cockpit); `/products/quick` binds the toggle to that class +
   re-derives the column so they can't drift. Proven `tests/pos/test_pos_age_gate.py` **13/13** local +
   **6/6** on sandbox (backend gate, not just static). sw.js v32→v33. **Deploy:** ladder sandbox→staging→prod;
   pre-prod backup `banco_prod-pre18plus-20260707_062609.sql.gz` (1.3 MB, gzip-t OK); trio parity-clean on
   `a6f7b02`; served-bytes verified each env (toggle in HTML, i18n×3, sw v33); prod serves 200.
   *Category = still take reference as-is / "On the fly"; photo/description role-gating = item #4.*
   - ⚠️ **NEW OBSERVATION (pre-existing, NOT this change):** prod startup logs a non-fatal
     `IntegrityError: null value in column "keycloak_id" of relation "users"` during user-seeding — a
     prod-DATA quirk (a seed user lacks a KC id). Identical code on sandbox = **zero** occurrences; app
     reaches "startup complete" + serves 200 regardless. Worth a look later (seed hygiene), not a blocker.
2. **✅ Reference data under-flags tobacco — FIXED + SHIPPED ALL 3 ENVS (`d90bffd`), re-enriched, prod
   verified.** The 18+ decision now happens in the ENRICHER (`catalog_taxonomy.classify`) — Angel's call:
   the import recipe should decide it. Was **408/7,272** flagged; now **640/7,272**, and it's the RIGHT set.
   - **What leaked & why:** branded cigarette packs ("Marlboro/Parisienne … 10x20cig"), nicotine
     disposables/pods ("Vozol … 20mg", "Elf Bar Prefilled Pod"), and shisha tobacco ("Al Fakher") carry
     NO "tabak"/"zigarette" token in the title → the old title-regex missed them.
   - **The fix (3 layers, most-certain first):** (1) title-decisive (cig brands + NNxNNcig + MYO/RYO +
     shisha molasses brands + nicotine-mg/prefilled/disposable FORM); (2) **supplier's own category**
     (already in `raw` — categorygroup_2) for feeds that carry it; (3) title-CBD fallback. Negative +
     accessory guards veto at every layer: `Tabaktasche` (pouch), filling machines, filter tubes, herbal
     `Tabakersatz`, **0mg/No-Nic**, refillable/replacement hardware, and CBD seeds/oils all stay OPEN.
     Fixed a latent guard bug: `\b0\s*mg\b` so "20mg" nicotine isn't read as "0mg".
   - **Proven:** new `src/tests/test_catalog_taxonomy.py` (20 tests), per-bucket verified on the live feed,
     re-enriched all 3 env DBs (0 shisha leak, 0 true e-cig leak — remainder is all No-Nic/0mg). **Full
     compliance chain intact:** enricher→reference row→adopt (copies `our_class`→`product_class`)→sale
     age gate. Prod cigarettes/e-cigs/shisha now `tobacco_nicotine` age_restricted. Backups
     `banco_prod-pre18flag-20260707_070631.sql.gz`.
   - ⚠️ **FOLLOW-UP (deeper, for Angel):** the existing DB `raw` holds only the coarse bucket
     (Accessories/Vaporizers/CBD), not FourTwenty's fine `categorygroup_2` — so layer (2) is currently
     future-proofing, and the current DB is carried by the title rules. A clean **re-import from the raw
     FourTwenty feed** (`debllm/feeds/fourtwenty/products_latest.csv`, 10,082 rows w/ categorygroups) would
     let the category-layer shine + future-proof new suppliers. Not a blocker — title rules cover today.
3. **✅ "Sold-but-not-set-up" cleanup COCKPIT — BUILT + on SANDBOX+STAGING (`f6de318`); ⏳ HOLDING PROD
   for Angel's human-green (new UI).** Manager-only `/pos/cleanup` (linked from Reports hub, EN/IT/DE):
   products that **sold** but are still half-baked, **busiest first**. "Half-baked" = objective gaps:
   category blank/"On the fly" OR cost null (18+ + photo surfaced for review, not gated). Inline fix per
   card — category (datalist) + cost + 18+ toggle → `PUT /products/{id}`; drops off when both gaps filled.
   Cashier never edits catalog/cost — rings it in, manager tidies here. **Seal reused:** `update_product`
   now runs the shared `reconcile_age` (same as the quick-add) so a manager flipping 18+ files it under the
   gating `age_restricted` class → checkout gate fires. Tests: `tests/pos/test_pos_cleanup_queue.py` (5
   black-box lifecycle+gate+reconcile, green on sandbox) + 4 `reconcile_age` units; full suite green.
   **→ 🧍 Angel: eyeball `https://sandbox-banco.lapiazza.app/pos/cleanup` (login felix) — say go for prod.**
4. **👥 Role model: cashier vs manager — CONFIRM what's gated today.** Angel was `felix` (admin) so he COULD
   take photos + voice-dictate descriptions on-the-fly (the mic dictation was "cool" — worked). Untested as
   `pam` (cashier) — do cashiers even get photo/description? Decision: **cashier = name + price, move on;
   manager (well-equipped, in-store) = photo/category/description/voice.** Test as `pam` Wednesday.
5. **🧍 Provision Layla as a MANAGER-level user** (she's effectively running the store). Identity task.
6. **👥 Artemis is NOT in prod — decide.** `reference_products` in prod = **7,272 rows, 100% FourTwenty,
   0 Artemis.** The "Artemis-first, FourTwenty-fallback" never had an Artemis rung — every hit fell to
   FourTwenty because that's all that's loaded. Angel's hunch was right. Decide: import+enrich Artemis into
   prod, or run FourTwenty-only for now. (Artemis import spec: memory `banco-artemis-catalog-import`.)
7. **👥 Tiny-barcode scanning — camera hits a wall.** Very small barcodes wouldn't read (one small one
   worked, a similar one never did; magnifying glass didn't help). Two tracks: (a) 🐯 improve the in-app
   scanner — **zoom / torch / continuous-autofocus / larger scan box** on `html5-qrcode`; (b) 🧍 evaluate a
   proper **USB/Bluetooth handheld scanner** (keyboard-wedge → "just works"). Likely need both.
8. **🐯 CHECK: the "0.75" thing on the Sputnik hash edit.** Angel: on-the-fly "didn't do the point seven
   five," went back to edit to clean it up (price/decimal? weight 3.5g?). Reproduce — possible small
   decimal-entry bug in quick-add. Low priority, verify before assuming.

---

## 🃏 ON DECK — 2026-07-04 (Freehold WENT LIVE) ← START HERE

**🚀🟢 Freehold is LIVE at https://wolfhold.app** — deployed to a Hetzner box (167.233.125.248, ssh key `~/.ssh/wolfhold_ed25519`, box `/root/freehold`), Porkbun domain, **real Let's Encrypt cert**, APP_ENV=production. **Locked down** (demo/sam removed, registration off, admin=`akenel`; public pages open=showcase). **Backed up** (nightly cron, encrypted+restore-verified, 14-day). KC admin console `https://wolfhold.app/admin/` (trailing slash!), pw in box `.env`. Full detail: memory `freehold-starter-kit`.
**Freehold open threads:** (1) OFFSITE backups (rclone→Drive) ← next, (2) real Pi hardware bridge, (3) events/raffles slices, (4) share it (India/McKinsey/Felix), (5) sslRequired=external.
**Also still open (Banco/campaign):** Rudestore card ready to mail; Felix reopen msg.

---

## 🃏 ON DECK — 2026-07-03 (end of the backup-brain + Freehold session) ← START HERE

**TWO live threads — check with Angel which one he wants first.**

**① 🐺 FREEHOLD — the legacy starter kit (born today; what Angel reached for next).** Repo `/home/angel/repos/freehold` (git init'd, **NOT pushed**). *"Own your stack. Owe no one."* — a teachable, production-grade, own-it-outright app foundation harvested from helixnet: the anti-Vercel/lock-in answer, a gift to teach real craft, and a resilience hedge. **Done:** manifesto + spec + favicon + **✅ Phase 1 SKELETON (boot-proven 2026-07-03)** — `docker compose up -d` = postgres + keycloak(3 realms) + FastAPI + Caddy; app renders via Caddy `localhost:8080`, DB connected (PG 16.13), all 3 realms 200. Commit `7708788`. **✅ Phase 2 (the door, `8ab876b`) + ✅ Phase 3 (the rails, `950e92b`) DONE + proven.** Rails = stdlib Python `ops/`: deploy (stamp→backup-gates-prod→rebuild→health→prove served==stamped), backup (AES-256 encrypt + RESTORE DRILL), env-parity; app serves `/version`. VERIFIED: deploy b5·950e92b served==stamped, RESTORE VERIFIED, parity clean+matches HEAD. **✅ Phases 1-5 + enterprise-taste + manifesto DONE (browser-proven, 12 commits, latest `1de9b0a`).** Skeleton→door(OIDC+RBAC)→rails(deploy/backup-gate/parity)→loop(SQLAlchemy+Alembic feedback→QA)→base pages→**i18n EN+हिन्दी incl KC login**→**multi-currency ₹lakh/crore**→**manifesto** (/manifesto editorial 'New Evolution'). **CAPSTONE = La Piazza LISTINGS**, built ONE CLEAN SLICE AT A TIME (Angel: rebuild-all=overkill): a listing = post+photo(MinIO)+desc+category+profile+RBAC + BYO-brain 'write my description'; then events/raffles as further slices; BYOH compute-exchange = crown jewel last. **✅ GitHub PUSHED (github.com/akenel/freehold, MIT, 15 commits) + BASE ESSENTIALS DONE: HTTPS (Caddy internal CA, https://localhost:8443), test suite (make test 14 green), system pulse (/pulse diagnostics), PWA (installable+offline).** **✅ Profile slice (MinIO+Markdown+CRUD) + Swagger(/docs) + /sitemap + shared Banco-style nav/status bar (health dot·env·clock-w-seconds·build·SHA·lang·avatar·hamburger) DONE — 18 commits.** NEXT: bottom app bar (PWA) + more La Piazza slices (events/raffles). ⚠️ Freehold LOCAL-ONLY/unpushed — Angel making GitHub repo → then PUSH + wire footer GitHub icon. Detail: memory `freehold-starter-kit`. Frontend LOCKED = server-HTML + Tailwind + Alpine + `fetch()` (React is *rented*, Freehold is *owned*). Full detail: memory `freehold-starter-kit`.

**② 📮 Head-shop campaign — Rudestore card READY TO MAIL.** Stephan's handshake card (№4, DE) is locked; the landing (opaque token `/kaffee/VSWkHkZYVdst`) + 3-option CTA + Resend email-notify are **LIVE + proven on prod**. **🧍 Angel action:** print the 2-up A4, stamp, POST it → Stephan scans Monday → email pings. In parallel: the Felix re-open message (drafted) + the Discovery→Replicate→Reveal engine (field kits served at `/scope` + `/discovery`). Detail: memory `banco-headshop-vertical-mosey-gtm`.

**Also SHIPPED this session (Banco, all 3 envs, verified + backed up):** login-page dynamic build footer; status-bar trim (removed "System OK" text → dot only; clock → HH:MM, no seconds/tz; SHA off the bar, kept in tooltip; killed the stale "Sprint 4" line). **The backup-brain PARACHUTE is rigged + PROVEN** (memory `ai-backup-brain-plan`): `scripts/code-with-openrouter.sh` = Aider+OpenRouter/DeepSeek edits+commits hands-free (~$0.002/edit); Turbo direct; Groq spare; keys persisted in `uat.env`. ⚠️ OpenRouter key was rotated (old one had printed in-transcript — Angel revoked it).

---nco Go-Live Worklist — THE ordered list

> 🔑 **Code word "ON DECK"** → you're reading the right file. State the top items and start executing the first actionable one. No re-planning, no re-asking.

*Open this, work top-down, finish one tier before opening the next. Don't fan out across five things. 2026-06-28.*

*Owners: 🧍 = Angel's hands needed (physical / decision / external call) · 🐯 = Tigs can do it · 👥 = both, together.*

*Detail lives in: [BANCO-GO-LIVE-READINESS.md](BANCO-GO-LIVE-READINESS.md) (analysis) · [BANCO-DAY-ONE-WISHLIST.md](BANCO-DAY-ONE-WISHLIST.md) (polish backlog).*

---

## 🃏 ON DECK — HEAD-SHOP CAMPAIGN (2026-07-02 eve) ← START HERE

**CUSTOMER #1 (Rudestore, Luzern · Stephan Frei · Postino #11) — FULL PIPELINE LIVE + PROVEN on prod:**
scope-out → handshake card (№ 4, DE, his shopfront) → QR **opaque token** `/kaffee/VSWkHkZYVdst` (enumeration-proof) → personalized landing (**3-option CTA**: Ruf mich an / Komm vorbei / Zusammensitzen + comment; **Ecolution GmbH · Mattenweg 5 · 6375 Beckenried** identity; no video) → captured lead → **email notification via Resend → ecolution.gmbh@gmail.com**. Tested end-to-end with Angel's phone + inbox (real scan tracked + 2 notification emails received). Card PDF + **2-up A4** ready (`docs/business/postcards/headshop-campaign/out/rudestore-stephan{,-2up}.pdf`).

**🧍 Angel:** print (2-up A4 = keep one + mail one), stamp, POST → lands ~Mon 2026-07-07 → Stephan scans → email pings you.

**🐯 NEXT (top of deck):**
1. **`/app/data` persistent volume** — scan/lead log lives IN the container; `docker restart` (normal deploys) preserves it, but a RECREATE wipes it. Add a named volume before real leads flow. NOT urgent (restart-safe) but real.
2. **Systemic opaque tokens** — only Rudestore's ext_id is opaque; randomize token generation for ALL leads before card #2 (decouple Postino ext_id from the seed-dedupe key).
3. **FR/IT/EN native review** of card + landing before mailing a non-DE shop.
4. **Scale:** same first card to the next A-list (Hanfbob's / Zauber / Paff Paff) — sniper, one card, never a second.

**Prod:** all 3 banco envs on `main`; coffee landing + email LIVE (banco.lapiazza.app); `uat.env` has `COFFEE_SMTP_*` (Resend); encrypted backups via `banco_backup.sh`.

---nco Go-Live Worklist — THE ordered list

> 🔑 **Code word "ON DECK"** → you're reading the right file. State the top items and start executing the first actionable one. No re-planning, no re-asking.

*Open this, work top-down, finish one tier before opening the next. Don't fan out across five things. 2026-06-28.*

*Owners: 🧍 = Angel's hands needed (physical / decision / external call) · 🐯 = Tigs can do it · 👥 = both, together.*

*Detail lives in: [BANCO-GO-LIVE-READINESS.md](BANCO-GO-LIVE-READINESS.md) (analysis) · [BANCO-DAY-ONE-WISHLIST.md](BANCO-DAY-ONE-WISHLIST.md) (polish backlog).*

---

## 🃏 ON DECK — HEAD-SHOP CAMPAIGN (2026-07-02, ~2:30pm) ← START HERE

**IN FLIGHT:** Angel is out doing the **Rudestore (#11, Luzern) scope-out** — the secret-shopper dry-run (first-customer test, before Felix). Back ~4:20pm with a **shop photo + one line of scoop**.

**THE MACHINE (built + committed on main):** Handshake card (DE/FR/IT/EN, № serial, photos/logo, 2-up) + `render_card.py` · personalized multilingual landing (event/invite CTA, {{LANDING_INTRO}}) served by Banco `/kaffee/{token}` · tracking + web→CRM loop (scan/Ja → log + ecolution email + Telegram → Postino by ext_id) · **Postino CRM** (`crm/postino`, LOCAL `crm/start.sh` → :8900 / phone 192.168.178.24:8900) — **184 leads** (11 A), **journey checklist** (scope-out→close, time-of-day + quick-checks), **artifact store** (FS/MinIO), **scope survey** at `/scope` (offline, phone, GPS, 120% guard) · docs: `MASTER-LIST-RECIPE.md`, `LEAD-TO-CLOSE-PROCESS.md`, `scope-sheet.html`.

**🐯 WHEN ANGEL IS BACK (top of deck):**
1. **Finish the Rudestore dry-run** — paste his scope summary into Postino #11's scope note; take his **photo + scoop** → generate **Stephan's card** (DE, "war grad bei dir im Laden…", his photo, № serial) → he prints + mails → watch #11 walk the board.
2. **Tune the process end-to-end** — real feedback from the live run (smooth the scope→Postino handoff).
3. **CRM glow-up (ONE pass):** deploy ONE hosted Postino (phone-reachable) + simple login (one password, NOT a KC realm) + build/env footer + Banco look-and-feel + photo-attach. AFTER the KC-realm terminal is clear (one driver per shared surface).

**LOCKED DECISIONS:** postcard (not letter) = warm opener, letter later = the formal close · Postino = solo tool → ONE instance + simple auth (NOT 3-tier/KC — right-sized) · ONE driver per shared surface · Felix→Mosey run in parallel (highest-odds first customer).

**Full context (memory):** `banco-headshop-vertical-mosey-gtm` · `one-driver-orchestration-preference`.

---

## ✅ RESOLVED 2026-06-29 — identity terminal collision recovery
The 2026-06-28 collision (a `checkout --force` reverted the identity terminal's uncommitted patches on sandbox + banco-staging) is **fully recovered**:
- [x] Identity terminal's commits **landed on `main`** — `92aabaa` is in `main` history.
- [x] All 3 envs **redeployed from updated main** — sandbox/staging/prod parity-green at `aae0629`, build stamp `b1384` uniform.
- [x] **Zero orphan `.bak` files** remain anywhere in the tree (the collision fingerprint is gone); `origin/main` = local `main` = live prod.
- [ ] *Carry-forward into P4:* confirm prod's KC-realm config carries the fold (code is verified; realm config is the open piece — folded into the prod-identity blocker below).
*Full detail: memory `banco-terminal-collision-2026-06-28`.*

---

## ✅ SHIPPED + SIGNED OFF — 2026-06-28
- [x] **Product Sales report** — what sold, tap → who-bought-it (cards), category drill + emoji, card → receipt, origin-gated ← Back, CSV/print, manager-gated (pam 403). LIVE on prod, human-green.
- [x] **Mobile responsive pass** — POS was tablet-sized; added a ≤480px breakpoint (tablet untouched) + per-screen fixes. iPhone SE clean. Audit harness = `scripts/testing/mobile-overflow-audit.js`.
- [x] **EXACT cash-payment bug** — false "Insufficient payment" on `.17`-type totals (JSON number → imprecise Decimal). Fixed at cent precision + regression test. Angel verified the sale on prod.
- [x] **Refund policy = manager-only** (confirmed keep) — pam can't refund, felix can; enforced UI + server.
- **Sign-off:** TEST-B03 hypercare 14/15 PASS, "really good". All 3 envs byte-identical to main `0707093`. Fresh verified prod backup taken before deploy.

---

## 🚧 GO-LIVE BLOCKERS — must be done before Felix runs his shop (in this order)

- [x] **P1 — Fiscal sign-off. ✅ ASSUMED-APPROVED (SIMULATION).** 🧍 For the sim we assume the
  Treuhänder reviewed the samples and signed off clean — gapless/immutable numbering + per-rate VAT
  are approved, nothing done wrong. **This is a simulation stand-in, NOT a real sign-off.** The package
  is send-ready (`docs/business/banco-fiscal/`: receipt + Z-report PDFs + bilingual cover note).
  **⚠ At the REAL cutover, actually run the process:** fill `[Name]`/`[Angel]`, send to the real
  Treuhänder, get the written thumbs-up, THEN flip this to truly done. Until then it's green *for the
  simulation only.*
- **P2 — Network resilience.** *Re-scoped 2026-06-29 (see `BANCO-OFFLINE-AND-PWA-PLAN.md` decision banner).*
  - [x] **P2.1 — atomic, idempotent `POST /pos/sales`** (whole cart + payment in ONE call, idempotent on a client UUID; till switched). **SHIPPED prod `9cf8f9e`/`b1391`** — human-green TEST-P21 (11/11 Fairphone, signed PDF in `docs/testing/banco/Test-Scripts/`), per-env `client_uuid` proof, atomic==legacy parity test, backup-gated. Kept the better online checkout.
  - [x] **Offline = clear warning + block (NOT offline sales).** Built P2.2 outbox, tested it (TEST-P22), then **Angel killed offline-mode** (tiny use case, huge fiscal cost). Instead: big "⚠ no internet — sales paused, use mobile data/hotspot" banner + honest checkout block (cart kept safe). Outbox branch deleted.
  - ~~P2.2 outbox / P2.3 sync~~ **DROPPED** — don't re-open without a named customer demand.
- [ ] **P3 — Hardware dry-run at the shop.** Thermal printer + barcode scanner on real metal — never tested live. 👥 (must be at Artemis). *Effort: half a day on-site.*
- [~] **P4 — Prod identity cleanup + SMTP.** 👥
  - [x] **SMTP wired 2026-07-01** — all 3 banco KC realms had NO email. Hybrid: `kc-sandbox`→MailHog, `borrowhood-staging` + `borrowhood`→**Resend** (`lapiazza.app` verified, smtp.resend.com:587). `testSMTPConnection` = **HTTP 204 all three**; sandbox PROVEN via MailHog. Persists across restart (IGNORE_EXISTING import, `helix_db`). Set master admin `helix_user` email = angel's Gmail (enables KC test button). ⏳ Angel confirm the 2 Resend tests hit Gmail; optional real user-flow (forgot-password) proof. Detail: memory `banco-kc-smtp-resend`.
  - [x] **helix_pass quick-patch 2026-07-01** — GitGuardian flagged the shared demo password (`helix_pass`) in the PUBLIC repo. Assessed: no cloud keys leaked, Postgres not internet-exposed; the real door was KC logins. Rotated **8 real accounts** (felix/akenel/angel/pam/ralph on `borrowhood` + `borrowhood-staging`) off `helix_pass` to Angel's strong password via `scripts/ops/set-kc-passwords.py` (getpass, refuses helix_pass). Sandbox stays open by design. Detail: memory `banco-shared-password-cleanup`.
  - [x] **Clean Banco POS realms — 3-realm rebuild DONE + HUMAN-GREEN 2026-07-02.** Banco's till is off the 365-bot `borrowhood` swamp and on a dedicated clean realm per env. (The `helix-identity-architecture` 3-realm plan; detail in `docs/IDENTITY-CONSOLIDATION-PLAN.md`.)
    - [x] **`kc-sandbox`** — already built + live (sandbox Banco runs on it).
    - [x] **`kc-staging` — built, folded, cut over, HUMAN-GREEN.** Fresh realm (21 clients + tier/app roles + `shop:artemis`); folded felix(pos-admin)/pam(pos-cashier)/ralph(pos-manager) with `+tag` emails; Resend SMTP (working key pulled from `borrowhood-staging` DB); branded wolf email theme + display "La Piazza · Banco" + i18n(en,it) + "close this window" message; `POS_REALM`→kc-staging (LP left on borrowhood-staging). **Angel proved all 3: login + self-service forgot-password → reset → login, flawless.** `helix_pass` on staging (rehearsal, like sandbox).
    - [x] **`kc-production` — built, folded, cut over, HUMAN-GREEN.** Same recipe: backup-gated (`banco_prod` + `helix_db` dumps first), fresh realm, folded felix/pam/ralph with `+tag` emails + **NO `helix_pass`** (passwords set via the reset flow — clean prod), Resend SMTP (key from `borrowhood` DB, from=noreply@lapiazza.app), branded theme (logo→`banco.lapiazza.app`) + display + i18n + message. `POS_REALM: borrowhood→kc-production` in prod compose, recreated prod only (`--no-deps`), proven (realm/JWKS/`/pos/`/health; staging + KC untouched). **Angel proved felix/pam/ralph forgot-password→reset→login on banco.lapiazza.app — clean, "just works."**
    - [ ] **Retire `borrowhood` / `borrowhood-staging`** — separate, later, gated. POS is safely OFF them now (LP_REALM/marketplace still uses `borrowhood`, so audit + quarantine the 365 bots without breaking the Square). No rush, no risk to leave parked.
  - [ ] **Infra passwords still `helix_pass`** (network-gated, not urgent): Postgres `helix_user` DB pw + KC admin pw. Careful coordinated rotation (touches every container's DATABASE_URL + compose + the DB role); `scripts/rotate-secrets.sh` exists.
  - [ ] **Hygiene:** drop `|| 'helix_pass'` default in the e2e script + move DSN pw out of tracked compose; mark the GitGuardian incident resolved.

---

## 🛡️ HARDEN — right after the blockers, before relaxing
- [x] **P5 — Offsite backup copy. DONE 2026-07-01.** 🐯 The DB dumps used to live ONLY on the box (the one hole in the "disaster-proof" table — the Fishbowl checklist's step 6 "restore from backup" had nothing to restore from if the box died). Closed it: `scripts/ops/banco_offsite_pull.py` scp's the GPG-encrypted blobs box→laptop (sha256-verified bit-identical), **then `rclone copy` → Google Drive** `ecolution-gdrive:HelixNet-DB-Backups/banco` (MD5-verified, `rclone check` clean, 0 diffs / 13 files) — the SAME personal Drive as the kdbx + DR SOP, so the DR checklist stays ONE place. **Backups now in 3 places: box + laptop + Drive.** Wired `@hourly` on the laptop crontab. Safety: copy + age-delete, never `rclone sync` (laptop wipe can't nuke the cloud copy); cloud push non-fatal if offline. Also fixed IaC drift (repo `banco_backup.sh` was stale plaintext → now matches the live encrypted box script).
  - *Open follow-ups (small):* (a) 🧍 **backup KEY into the kdbx** — offsite ciphertext is unrecoverable without `/root/.banco-backup-key` (fp `4de994a0ef02fd82`); belongs in the KeePass kdbx that's already on Drive. (b) 📄 **DR SOP is `borrowhood`-only + stale** (last tested Apr 6) — doesn't cover `banco_prod` (the DB Felix's shop runs on) or its encrypted decrypt→restore path; needs a Banco section. (c) 🟡 **DigitalOcean later** (Angel's ask) — add DO Spaces as a 2nd remote for provider-diversity (survives a Google lockout); one line in `DEFAULT_REMOTES` + a token refresh. (d) side seal: `borrowhood` dumps are **plaintext** on the box (unencrypted PII) — Banco's are encrypted; worth aligning.
- [ ] **P6 — Push alerting.** Today the daily smoke writes pull-only status files; add a push so a failure reaches you. 🐯
- [ ] **P7 — Fiscal-robustness fix.** The subtotal≤0 Z-report drift on messy mixed data — defensive fix is queued. 🐯
- [ ] **P8 — Runbook + rollback + staff SOP + invoice/contract + DPA.** The paperwork that makes it a business, not a demo. 👥

---

## ✨ POLISH BACKLOG — after go-live, only on demand
*(Most specced in [BANCO-DAY-ONE-WISHLIST.md](BANCO-DAY-ONE-WISHLIST.md). Don't build ahead of need.)*
- **✅ P0 COMPLIANCE — BUILT + PROVEN ON SANDBOX, HELD FROM PROD (2026-07-08 eve).** Branch
  `fix/p0-otf-compliance-20260708` (build b1601) deployed to sandbox ONLY (Angel: Felix is live on prod,
  don't disturb; batch to prod tonight/tomorrow). Fix = classifier (`nicotin\b`→`nicotin` English catch +
  new `_CIGAR` cigars/cigarillos/Swisher/blunt-wraps) + `resolve_class_on_create` gate-only safety net wired
  into on-the-fly create. PROVEN end-to-end on the live sandbox server: OTF "Swisher Sweets" (no 18+ toggle)
  → `tobacco_nicotine`/18+ ✓; "Bic Lighter" → standard/open ✓. Reference reclassify: tobacco_nicotine
  **325→442 (+117** under-flagged pouches/cigars/cigarillos now gated — fixes the ADOPT path). Products
  (TAM-) sweep: 89 changes, mostly DRIFT-FIX (accessories wrongly flagged 18+ → un-flagged; Backwoods→tobacco).
  Tests: 39 taxonomy + full gate 1824 pass (3 known-flaky). **⚠ PROD-STEP CAVEATS:** (1) prod leaked SKUs are
  NOT `TAM-` (REF-FOURTWENTY/LZ-/SKU-/OTF-) → prod `reclassify_products` MUST run with **empty prefix (ALL
  products)**, not default TAM-. (2) REVIEW the products flip list before prod — the sweep un-gates some
  accessories (drift-fix, correct but sensitive). (3) blunt wraps gated conservatively (Felix/Treuhänder confirm
  CH line); "Cream Haschisch"→cbd_open via cream-veto is pre-existing, flag for review.
- **🐛 DIAGNOSED 2026-07-08 — mobile login "press Login twice" race (fix teed up, NOT shipped).** Angel: on
  mobile (repro'd on staging) after entering KC creds you land back on the login screen ("you're not logged
  in"); a 2nd Login press (KC SSO still alive → silent, no re-typing) then works. **Root cause (confirmed
  chain):** `/pos/callback` hands the token back in the URL **fragment** via a 302 → `/pos/dashboard#token=…`
  (`pos_router.py:5318`); the dashboard reads the fragment (`dashboard.html:265`) but **hard-bounces to `/pos`
  the instant no token is found** (`dashboard.html:282-286`). On mobile the `/pos/` **service worker**
  intercepts the navigation and follows the redirect via `fetch()` (`sw.js:83`) — **URL fragments don't
  reliably survive a SW-followed redirect**, so `#token` is eaten → bounce. (Same fragment-timing seal that
  the `_revealChrome`/`_authInFlight`/"dead page until refresh" comments already bandaged in `base.html` —
  fix the seal, not the drip.) **FIX (smallest→robust):** (1) one line — SW ignores `/pos/callback`
  (`if(url.pathname==='/pos/callback') return;` in sw.js) so the browser follows natively + keeps the
  fragment [most likely cure, low risk]; (2) real fix — `/pos/callback` returns a tiny 200 interstitial that
  stores the token inline then `location.replace('/pos/dashboard')` — no fragment for anything to eat, AND
  gets the token out of the `Location:` header (small security win); (3) soften the instant hard-bounce (one
  retry/grace) so a transient miss never logs a cashier out mid-shift. **DEFER reason:** only reproduces on
  mobile → must be verified on the Fairphone (machine-green ≠ human-green for an auth race). Do the 1-line SW
  fix + interstitial, then Angel confirms on the phone in ~2 min. Non-blocking today (worst case = press twice).
- **🧹 LOGGED 2026-07-08 — hide "Stock (info)" on the cashier sale card (zero-perpetual UX).** Angel (in-shop,
  Ralph) hit the Lighter detail: `Stock 0 (not a sell gate)` and rightly asked why we show a field we have to
  disclaim. **Decision:** stock is a MANAGER/reorder concept, not a point-of-sale concept — show it where it's
  acted on, hide it where it only confuses. **Do:** (1) cashier / sale-detail card → **hide the bare stock
  line + drop the "(not a sell gate)" disclaimer** (a naked `0` just makes a cashier hesitate; the label is a
  band-aid over confusion the line itself creates); optionally surface a small "⚠ reorder" flag ONLY on a real
  low-stock signal (min_stock set AND stock ≤ it) — never a naked zero. (2) manager catalog / receiving /
  reorder report → **keep stock** (its real home; feeds the Order-Book). (3) **do NOT touch the data model** —
  `stock`/`min_stock` seed the [[banco-zero-perpetual-and-order-book]] reorder report (P4) + receiving already
  writes to it; residual on the sale card, foundational there. Small conditional-render change; verify the
  manager view still shows stock. Non-blocking.
- **🏷️ HARDWARE 2026-07-08 — LABEL PRINTER COMMITTED: Brother QL-820NWB (Angel confirmed).** Runs on
  **Debian 12 / Linux — no Windows** via **`brother_ql`** (open Python lib: render label → PNG raster → send
  over the printer's WiFi/USB, NO proprietary driver). Fallback = Brother's official Linux CUPS driver.
  Best path = network backend (printer on WiFi → print to its IP), fits "Banco/laptop prints directly."
  Thermal (no ink); barcode/QR = **always mono black** (colour hurts scanning); red is optional-accent only
  (2-colour DK-22251 roll) for a 🔞 flag later. **v1 label = 1D barcode (EAN-13/Code128) + title + price**
  (operational, for the GUN at checkout). v2 = customer label adds a small QR → La Piazza (community loop).
  Draft roll = 62mm continuous DK-22205 (cut-to-length while tuning) → die-cut later for speed. Label
  generator = next build (python-barcode + qrcode → HTML/PNG preview now, brother_ql to the printer when it lands).
- **🔫 HARDWARE 2026-07-08 — scanner ALTERNATIVE pick: Datalogic QuickScan QBT2500** (Digitec 23483940),
  next to the earlier **Zebra DS8178** decision. Both are premium 2D Bluetooth imagers from top-3 brands.
  Datalogic = mid-range general-retail, **fully capable + usually cheaper**; Zebra DS8178 = higher-end "hero"
  gun (more aggressive engine + tougher build, pricier) — its extra cost mostly buys ruggedness/speed a
  single-counter head shop won't notice. QBT2500 is a **2D area imager** (reads 1D + 2D/QR — reads small/dense/
  damaged 1D far better than a laser, reads QR too), Bluetooth cordless + charging base, keyboard-wedge (BT HID
  to phone/tablet, USB via base to desktop → fits the desktop cataloging rig). **Verify before buying:** (1)
  it's the BT kit WITH the base/cradle (not scanner-only); (2) HID keyboard-wedge mode (QuickScan supports it,
  set via programming barcode); (3) price delta vs the Zebra; (4) THE decider — does it read Artemis's *worst
  tiny barcode* (both should; prove it on Felix's smallest cig-pack code, not the spec sheet). Verdict: sensible
  cheaper alternative; brand isn't the thing — "reads the shelf + types into the browser" is, and this does both.
- **🖥️ IDEA 2026-07-08 — desktop "cataloging rig" for the one-time catalog/cutover pass.** The Zebra DS8178 is
  a keyboard-wedge → device-agnostic (USB cradle to a desktop = acts as a USB keyboard + charges; or Bluetooth
  HID to phone/tablet). Insight: for the BIG one-time cataloging/labeling pass, a **desktop + gun + label
  printer** beats thumbing the phone — big screen to see the catalog, real keyboard for names/prices/categories,
  gun for instant barcode capture, printer to assign+print a code for unmarked goods on the spot ("born once,
  known forever" made physical). Station flow: scan/type item → assign code → print label → stick → next.
  Then the **phone/tablet is for daily *selling*** at the counter (cordless gun in hand). Same one gun bridges
  both. **Prereq (already queued):** `/pos/scanner-test` wedge-input check — Banco needs a focused field that
  takes the typed barcode + Enter (not just the camera) for the gun to work in the browser. Non-blocking;
  informs the hardware-dry-run (P3) + cutover setup.
- **✅ DONE 2026-06-28:** Feedback button → small corner 💬 icon (`17fa4ba`) · **Promo-restricted discount block** — no discounts on tobacco/alcohol, cashier+manager (`2b8aefa`, Angel: Pam discounted cigs; was role-cap-only). Both LIVE all 3 envs + regression tests.
- **✅ SHIPPED 2026-06-29 — Catalog pass + Ticket Timing tracker (both LIVE all 3 envs, `e43843f` / `b1386`):**
  - **Catalog pass** (infinite scroll / Sort / tap-to-PREVIEW) — Angel-tested green; was ALREADY on prod (merged to main before the `aae0629` build-stamp deploy → rode along), confirmed by parity + ancestry. No separate promote needed.
  - **Ticket Timing tracker** — "🩹 Healed in 2h 37m" SLA pill on the Resolution card + story header (open tickets show "⏳ Open 3h"). Pure `src/services/ticket_timing.py` (7 unit tests), timeline + resolution endpoints return a `timing` block. Promoted sandbox→staging→prod, backup-gated (`banco_prod_20260629_1434`, verified-restore 24/13/87), re-probed (HTTP 200, code present, catalog no-regression).
  - *Catalog future (Angel ideas, NOT built):* ellipsis (⋯) per-item menu (preview/edit/delete/flag) · **mass-select / mass-edit** for hundreds–thousands of items · "**preview the listing**" (La Piazza listing look) inside the edit screen. Keep it "quick + simple"; build at need.
  - *No stock filter* on purpose — zero-perpetual ([[banco-zero-perpetual-and-order-book]]).
- **Cosmetics queue (2026-06-28, in progress):** Pagination on the **buyer drill + transactions** (catalog done above; transactions needs its summary moved server-side). ← *next*.
- **Discount UX follow-up:** in the till, grey-out/hide the discount field for promo-restricted items so the cashier sees it can't be discounted BEFORE trying (server already blocks; this is the hint).
- **Tiered / quantity-break pricing (Angel idea 2026-06-28):** "buy 5 → price A, buy 10 → price B" auto in cart. A price-rules layer (product → qty thresholds → unit price). MODERATE build; MUST respect the promo-restricted guard (a volume break is still a promotion → none on tobacco/alcohol) + VAT/receipt/reconciliation. Ad-hoc discounts cover today; build only when a real shop asks.
- **Category** chart on the report + the **hierarchy/CRUD + emoji picker** (specced in `BANCO-CATEGORY-MANAGEMENT-PLAN.md`; emoji seam already shipped).
- Mobile tail: catalog card overflow on sub-375 phones (prod data); `cdn.tailwindcss.com` prod warning → proper Tailwind build (rule #9).
- Product Sales #2 customer-detail screen · #3 dashboard cards · XLSX export · **Export-to-Google-Drive (sellable feature)** · audited PII/HR export.

---

*The blockers (P1–P4) are the only things standing between Felix and a clean Monday open. Everything below them makes it sturdier; everything in Polish makes him love it. Top-down. One tier at a time.*
