# Banco Go-Live Worklist — THE ordered list

> 🔑 **Code word "ON DECK"** → you're reading the right file. State the top items and start executing the first actionable one. No re-planning, no re-asking.

*Open this, work top-down, finish one tier before opening the next. Don't fan out across five things. 2026-06-28.*

*Owners: 🧍 = Angel's hands needed (physical / decision / external call) · 🐯 = Tigs can do it · 👥 = both, together.*

*Detail lives in: [BANCO-GO-LIVE-READINESS.md](BANCO-GO-LIVE-READINESS.md) (analysis) · [BANCO-DAY-ONE-WISHLIST.md](BANCO-DAY-ONE-WISHLIST.md) (polish backlog).*

---

## 🃏 ON DECK — 2026-07-11 · THE CATALOGUING WORKSTATION (spec written) ← START HERE

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
