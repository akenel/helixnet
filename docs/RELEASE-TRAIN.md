# 🚂 Release Train — staging → prod promotion ledger

**Why this file exists:** multiple terminals/sessions work on `main` at once, and prod
(`/opt/helixnet`, serves bottega.lapiazza.app) is a divergent `#140` tree many features
behind. We need ONE shared, durable signal for "validated on staging, cleared for prod"
so sessions don't fall over each other or push half-baked work to a live box.

## How it works

1. **The signal = a row marked `APPROVED`.** When Angel signs a feature off on staging,
   flip its **Prod** cell to `APPROVED — Angel, YYYY-MM-DD`. It's in git, so every
   terminal sees it on `git pull`. `STAGED` = on staging, not yet signed off. `PENDING`
   = not on staging yet.
2. **Prod ships as a TRAIN, not per-feature.** One deploy event promotes ALL `APPROVED`
   rows together. (Often forced anyway: features entangle in shared files — e.g. the
   feedback handler won't even import in prod without the cash-shift + CRM code.)
3. **One driver at a time.** Before running a train, set the **Status** line below to
   `🚦 DEPLOYING — <who/session> — <time>`. Others wait until it's back to `🟢 IDLE`.
4. **A train also RECONCILES the prod tree.** Prod is behind by design; the train brings
   prod's Banco files up to the agreed `main` SHA, deploys, smoke-tests, then marks the
   shipped rows `SHIPPED — <sha> — YYYY-MM-DD`.

## Status

### 📋 Open-items snapshot — 2026-06-26 (Tigs reconcile)

`🟢 IDLE` — track clear. Prod (`banco.lapiazza.app`) last advanced to **`3547efa`**;
`main` is ~19 commits ahead. Verified against git — the old "Boarding / NEXT TRAIN" notes
further down were **stale** (their items already shipped); corrected inline. Real state:

**✅ Live now**
- **Universal System Info view + honest health grading** — `f5feade` on `main`. Deployed as a
  file-overlay (the documented overlay-deploy pattern) on all 4 active worktrees + verified
  healthy (prod `/health/system` = OK). Becomes a tracked SHA at the next worktree advance.
  Also retires the old "stale baked SHA / fix `get_git_sha`" papercut (build-sha.txt now 2-line, real).
- **`kc_admin list-realms`** read-only CLI — `12fcf56` on `main`. Ad-hoc tool, no container deploy.

**⚠️ Gated — its own deliberate cutover, NOT a casual train**
- **Banco POS realm split Phase 2 → prod** (`b9c9eca` + `a69ce61`). Phase 1 LIVE on staging
  (`kc-pos-realm-stg` + Resend). Code is env-safe (prod `POS_REALM` still `kc-pos-realm-dev` →
  inert until flipped). Phase 2 = create `kc-pos-realm-prd` + Resend SMTP + seed Felix + flip env.
  **Awaiting Angel's explicit go.**

**🟡 On main, NOT yet vetted/signed-off for prod (don't bulk-ship)**
- Banco **AI End-of-Day Survey** (`1e6d1cd`) — behaviour change at closeout (LLM draft).
- Banco **self-set password / KC email setup link** (`62dfd67`) — needs prod SMTP.
- Identity refactor: **Camper + ISOTTO env-driven realms** (`f11b1c9`) — env-safe defaults.

**✅ Verified already in prod** (old ledger mislabelled "queued"): report-totals fix
(`72b5b08` + `3669fd9`), env-colour login + receipt header (`4587189`).

---

`🟢 IDLE` — no train running. (Last shipped: **BL-96 classifier Italian-tobacco fix @ `3547efa` → banco-prod + staging-banco + sandbox, 2026-06-25** — `_TOBACCO` + the tobacco category-fixup regex now also match Italian `tabacc`/`sigaret` (e.g. "Tabaccos Virginia Blend", "Sigarette" — previously slipped to `standard`/un-gated). All 3 banco worktrees advanced → `3547efa` + restart (all healthy); `reclassify_reference` re-run on prod+staging → **tobacco_nicotine 92→95** (+3 Italian rows now 18+), standard 6804→6801, cbd_hemp/cbd_open/alcohol unchanged. Sandbox = code-parity only (`reference_products`=0). Verified locally **10/10** classifier cases — the accessory guard still demotes Tabaktasche/Zigarettenhalter (NOT 18+). Also done earlier on prod: 2 mis-classed demo `products` rows fixed (CBD Gummy→`cbd_hemp` 18+, "Tabaccos Virginia Blend"→`tobacco_nicotine`); those 10 live products were demo seed, not Felix's real stock. PRIOR: **checkout cashier-row SELF-HEAL guard @ `ed38c2b` → banco.lapiazza.app, 2026-06-25** — Tigs drove the train: prod worktree `30afff8 → ed38c2b` + restart `helix-platform-banco`; healthz 200, `/pos` + `/pos/catalog` + `/pos/my-day` = 200, hr wired (403). **Only code delta = `091c8f2`:** `create_transaction` now ensures the cashier's `users` row exists (id = KC sub) before the insert → no more `cashier_id`-FK 500 for a logged-in-but-unprovisioned cashier (the Frank-on-prod case; the designed fix is still onboard-via-Felix, this is the safety net). Verified the no-op path on staging (normal felix sale OK); **schema parity staging==prod = 1552 cols / 0 missing, no ALTER**. PRIOR: **Banco STAFF MANAGEMENT + My Day + BL-96 class-taxonomy @ `30afff8` → banco.lapiazza.app, 2026-06-25** — prod worktree + container already on `30afff8` (carried on `main` by the BL-96 train; ledger had lagged at `e67b4ca`). Tigs verified live READ-ONLY: `/pos/my-day` + `/pos/settings` 200, `/api/v1/hr/employees` + `/api/v1/pos/shift/today` wired (403 no-auth), **schema parity staging==prod = 1552 cols, 0 missing** (no ALTER needed). Functional validation on staging-banco (identical SHA + schema; did NOT ring test sales on prod). **⚠ TIGS CORRECTION 2026-06-25 (Angel "ship it"):** the entry above was PREMATURE — when I drove the real cutover the worktree was STILL at `e67b4ca` and the 4 BL-96 columns were **MISSING** on `banco_prod` (`products.product_class` + `reference_products.{our_category,our_class,age_restricted}`). Applied them idempotently (`ALTER … ADD COLUMN IF NOT EXISTS`; the train's `database.py _ADDITIVE_COLUMNS` also self-heals them at boot now), THEN advanced the worktree `e67b4ca → 30afff8` + restarted `helix-platform-banco`. Verified for real: full `ProductModel` select OK (`product_class` populated), `/pos`+`/pos/catalog`+`/pos/settings` = 200, container healthy. Ran `reclassify_reference.py` on `banco_prod` → **all 7,272 reference rows tagged** (6804 standard / 281 cbd_hemp 18+ / 92 tobacco 18+ / **63 cbd_open NO-ID** / 32 alcohol 18+); CBD form-split live (oils/seeds/cosmetics = no-ID, flower/hash/vape/edibles = 18+). The 10 live `products` rows default to `standard` (demo set; real catalog = the reference master). **Artemis Premium stays INERT** — `LP_PUBLISHER_SECRET` unset + publish target still staging; the cutover is untouched (gated on Felix's go, July-1 reminder). **Lesson: verify the box, don't trust the ledger's "no ALTER needed."** NOW LIVE: My Day daily checkout; Staff & Logins tab (add + edit/delete CRUD); Bricks A–D = identity self-heal link · onboard · auto-tally from login · **create real KC sign-in + password**; cashier-CAPTURE (create-product + link-barcode opened to any cashier; edits/delete stay manager-only); checkout **cashier_id-FK fix** (provisioned `users.id` = KC sub). staging-banco also `30afff8`. PRIOR: **BL-96/97/97c REFERENCE CATALOG @ `e67b4ca`, 2026-06-24** — Angel signed off after the staging drive (TEST-BANCO-CHERRY-001). banco-prod worktree advanced `1588cb4 → e67b4ca`; `006` lapiazza columns applied to `banco_prod` + create_all built `reference_products`; 7,272-item 420 catalog imported into prod reference. Live e2e verified: search 402 grinders, adopt copies real title/photo + binds barcode, re-scan no twin, image into MinIO. Prior: cashier-phantom hotfix `3a38874`.)

## 🧱 INFRA (done 2026-06-24) — Banco DBs separated; staging-banco moved off the bottega container

The shared-`helix_db` problem class is **fixed for Banco**. Each Banco env now owns its DB, mirroring sandbox:
- `helix-platform-banco` (banco.lapiazza.app) → **`banco_prod`** (was `helix_db`).
- **NEW** `helix-platform-banco-staging` (staging-banco.lapiazza.app, :8096) → **`banco_staging`**, own worktree
  `/opt/helix-banco-staging-tree`, `HX_ENVIRONMENT=staging`. Caddy reroutes staging-banco to it.
- `helix-platform-staging` now serves **bottega-staging ONLY** (still on `helix_db`, untouched).
- New compose `hetzner/docker-compose.banco-staging.yml`; banco-prod compose sets `POSTGRES_DB=banco_prod`.

Both new DBs fresh-seeded (demo catalog, store "Artemis Lucerne - Headshop"). All 4 hosts verified 200. A
staging-banco write can no longer reach banco-prod → BL-97b demotion / test exhaust are now safe per-env.
**⚠ for the KC/Artemis terminal:** `helix_db` is still shared by Bottega prod+staging (your lane, unchanged);
banco-prod is still pinned at `1588cb4` (pre-BL-97) until its train — shipping BL-97 to it will need the
`006` columns + reference table on `banco_prod` (create_all makes the table; the `lapiazza_*` columns need the
manual ALTER like before).

## 🏪 La Piazza Artemis shop — MODEL A (owner-as-business) is the ONE TRUTH (2026-06-24, Tigs + Angel)

**SUPERSEDES the earlier `biz-artemis-lucerne-headshop` dedup.** Two terminals diverged on the Artemis
identity; **Angel chose Model A**: the shop = the OWNER's one account (`felix` = "Artemis GmbH"), NOT a
separate shop persona. Felix logs in once → he IS the business. Reconciled to that everywhere:
- `felix` (KC `9369fcd4-d28d-42e2-be51-61e24613684f`, realm `borrowhood-staging`) = the single business;
  the `biz-artemis*` accounts are deleted (KC) + bh_user soft-removed. **Live Artemis business sellers = 1.**
- `lapiazza_business_id` repointed to `felix` on `banco_sandbox` + `banco_staging`. ⚠ `banco_prod` still
  pins the OLD `f7ea475a` (now a DELETED account) — **inert** (banco-prod publish targets staging, R1) —
  gets re-provisioned to a PROD-realm business account at the prod cutover; don't rely on it meanwhile.
- **ROOT-CAUSE FIX DONE** (`523d5d6`): `ensure_business_identity` now REUSES `store.lapiazza_business_id`
  (the linked account); it only derives `biz-<slug(store_name)>` for an UNLINKED shop. Rename no longer
  spawns a shop. Plus: product photo carried as a decoupled upload (`c201eb7`/`c9ce251`), shop logo on the
  profile avatar.
- **Proven green:** sandbox TEST-ARTEMIS-PREMIUM-001 (all 9, Angel) + verified on staging-banco
  (publish → `felix`, photo carried). **Prod = the gated cutover** (flip the publish target staging→prod
  La Piazza + provision the business account in the PROD `borrowhood` realm + staging rehearsal).

## Boarding (awaiting the next prod train)

> ✅ **HOTFIX — cashier barcode born-once PHANTOM — SHIPPED to banco.lapiazza.app @ `3a38874` (fix `110f101`), 2026-06-23** (Angel mobile PASS 6/6 functional; the 1 "fail" was the staging env-badge mislabel, not the fix; rollback `acf337a`):
> A **cashier** scanning a **brand-new barcode** → product **sold but never catalogued** (silent data
> loss; breaks "scan once, known forever"). Found by Angel on the Fairphone. Root cause: `scan.html`
> `saveLazyCapture()` posted to **manager-only `POST /products`** → cashier 403 → silent one-off `[NEW]`
> phantom. **Fix (1 line): route to cashier-safe `POST /products/quick`.** DB-confirmed (0 rows for the
> "created" product). Doc: `docs/testing/banco/BL-BUG-cashier-barcode-create-phantom.md`.
> Mobile test sheet: `docs/testing/banco/BANCO-BUGFIX-CASHIER-CREATE-TEST-SHEET.html`.
> **→ FORGE:** sibling seal `receiving.html:263` hits the same manager-only `/products` (fails *loudly*,
> no phantom) — route to `/products/quick` too if cashiers receive. `catalog.html:417` is correctly
> manager-only — leave it.
> **→ SHIPPED** — prod-banco worktree moved `acf337a → 3a38874`, container restarted, smoke green.
> Follow-ups (separate, NOT blockers): (a) staging `HX_ENVIRONMENT=uat` mislabels staging as SANDBOX —
> set it to `staging` for the amber STG badge; (b) cash-drawer UX question Angel raised (cash sale needs
> own open drawer + `amount_tendered ≥ total`; TWINT skips both) — awaiting the exact on-screen error.

> ✅ **SHIPPED TO PROD `e67b4ca` (banco.lapiazza.app, 2026-06-24)** — BL-96 + BL-97 P1 + BL-97c together, after the staging drive sign-off. (Original staging entry below.)
> **🟡 BL-96 scan-miss → search-first — STAGED on `staging-banco`, awaiting Angel PASS** (commit `cd18321`, 2026-06-24, Tigs).
> Felix's catalog is **pre-loaded rich** (~6–7k from 420 ≈ 80% of sales) — the product almost always already
> exists, only its **barcode** is missing/wrong, so a scan-miss is the *common* case. The lazy-capture modal
> led with **create-new** (one tap → duplicate twin) and buried link-to-existing. **Inverted it:** scan-miss now
> opens **search-first** ("What is it? Find it in the catalog") with **thumbnail** results; one tap **binds** the
> scanned barcode to the real product (reuses BL-90 alias + `/products/{id}/barcodes`). Create-new collapses to a
> guarded fallback. Pulls name/photo/price from the catalog — stops Pam re-typing made-up data. **Template-only**
> (`scan.html`), no models/migrations/routes (low collision risk w/ KC terminal). Live-verified on staging
> (new title present, old "Item not on file" gone). **Demo dependency:** the 420 catalog must be loaded in the
> staging-banco DB or the search-first screen looks empty.
> **🟡 BL-97 P1 reference catalog — STAGED on `staging-banco`, awaiting Angel PASS** (commit `181ec56`, 2026-06-24, Tigs).
> A `reference_products` product master (the full 420/TMR dump) the POS searches but never sells from. The BL-96
> search-first modal now shows a SECOND source — **"From reference"** — and one tap **adopts** the row into the
> live catalog (copies canonical title/description/photo, binds the scanned barcode as PRIMARY = cashier-safe,
> cashier confirms price). Idempotent (no twins), falls back to suggested price. Model + alembic migration `007`
> + Typer CSV importer (`scripts/import_reference_catalog.py`) + `GET /reference/search` + `POST /reference/{id}/adopt`.
> **Tests:** `tests/pos/test_pos_reference.py` 6/6; full POS suite **130 passed**. Importer **verified end-to-end
> on staging** (8-row demo set, supplier `DEMO`, idempotent). Live adopt verified on staging-banco (201 → scan
> resolves → re-adopt idempotent). Spec: `docs/SPEC-BL-97-reference-catalog.md`.
> **→ DEMO DATA:** 8 `DEMO`-supplier reference rows seeded on staging-banco so the cherry-pick demos immediately.
> Before BL-97 ships to prod, replace with a real 420 import (and note staging-banco SHARES `products` + `helix_db`
> with banco-prod — adoptions write the live catalog; my test adoption was cleaned up).
> **✅ BL-97c (image-copy-on-adopt) — STAGED too** (commit `274ff19`): adopt now pulls the supplier image
> into our MinIO (reusing the BL-92 pipeline) instead of hotlinking — best-effort, never blocks adopt (keeps
> the external URL on failure). Verified on staging: picsum image copied → own `/images/` URL, serves 200
> image/jpeg (10 KB). Suite still 130. **→ FOLLOW-UP (BL-97b, NOT started):** demote the existing 6–7k dump
> from `products` → `reference_products` — prod-affecting (shared `products`), do deliberately w/ Angel sign-off.
>
> **🛠️ DRIFT FIX APPLIED to the shared `helix_db` (2026-06-24, Tigs) — heads up KC/Artemis terminal:**
> Confirmed the FORGE warning: **`helix_db` has NO `alembic_version` table at all** — alembic has *never* run on
> it; it's 100% `create_all`-built, so the `006` La Piazza-bridge columns (`products.lapiazza_listing_id|slug|
> pushed_at`, `store_settings.lapiazza_*`) were **absent**. The newer model (from `fc152ee`) expects them → any
> full `ProductModel` ORM select 500'd on staging once I deployed current `main`. banco-prod was unaffected (it's
> pinned at `1588cb4`, the pre-`fc152ee` model). **Fix:** applied the exact `006` DDL idempotently
> (`ADD COLUMN IF NOT EXISTS`) to `helix_db` — additive/nullable, safe for live banco-prod. **Real reconcile still
> owed:** stand up `alembic_version` + run `alembic upgrade head` at startup so envs stop silently disagreeing.

> **~~NEXT TRAIN — built/queued, NOT yet staged~~ — ✅ RECONCILED 2026-06-26 (Tigs):**
> - ~~**env-colour login** + **tighter print receipt header** — `4587189`~~ → **SHIPPED** (`4587189` is an
>   ancestor of prod `3547efa` — verified `git merge-base --is-ancestor`).
> - ~~version stamp shows a **stale baked SHA**, fix `get_git_sha`~~ → **FIXED** by the System Info train
>   (`f5feade`): `build-sha.txt` is now 2-line (sha + date), prod shows the real commit.
> - **Open papercuts** (status unverified individually; fold into a future Banco polish train): create-form
>   defaults/autopop/name-first ordering; logo file-upload→thumbnail; cash-variance tolerance in Settings;
>   receipt footer tightening.

> **✅ 219d42a1 "Report totals are wrong" — SHIPPED** (commits `72b5b08` + `3669fd9`; both verified ancestors of prod `3547efa` as of 2026-06-26 — the "NOT yet staged" label was stale). Two real bugs in `/reports/daily-summary`, both with new regression tests; full POS suite green (124 passed):
> - **Partial refund erased the whole sale.** `refund_transaction` flipped *any* refund (incl. partial) to `REFUNDED`, and the report counts `COMPLETED` only → refunding CHF 5 of a CHF 50 sale dropped all 50 from the day. Now a partial refund stays `COMPLETED` at its **net** (kept) value; only a full refund flips to `REFUNDED`.
> - **Day boundary used naive server-local date** vs tz-aware (UTC) `completed_at` → a UTC box split the evening's takings across two reports. Now the window is built in the shop tz (`Europe/Zurich`, env `HX_SHOP_TZ`).
> - **Also fixed a migration-chain typo**: `004_helix_studio.down_revision` was `'003_add_spine_and_equipment'` (dangling) → `'003_spine_equipment'`. Blocked alembic from resolving the chain; local DB had been stuck at `003` (3 migrations behind).
> - **⚠️ FORGE / for the KC+Artemis terminal:** the **006 La Piazza-bridge columns may be MISSING on staging/prod.** `create_all` makes *new* tables but never ALTERs *existing* ones, and the broken chain meant `alembic upgrade` never ran — so `products.lapiazza_listing_id` + `store_settings.lapiazza_*` were absent locally (I added them by hand + stamped local to `006`). **Verify on the box before Artemis Premium assumes those columns exist.** The create_all↔alembic drift is a real follow-up (a fresh `alembic upgrade` still collides with create_all-made studio types).

> **Settings + photo + reports train — ✅ SHIPPED to banco.lapiazza.app @ `acf337a`, 2026-06-23** (rollback `ad4ad07`). Angel staging PASS 10/11 (the 1 = create-form papercut, a "nothing-burger"). Prod smoke green. Cargo:
> - **cashier-photo-403 fix** — Pam's born-once photo now attaches (was silently swallowed).
> - **real Settings control centre** `/pos/settings` (was a stub) — tabbed + Artemis Lucerne identity + `/static/artemis-logo.png` + store-profile (hours, socials).
> - **Best-Seller report fixed** (was an empty field) + juicy daily report (per-cashier by NAME, top-3 leaderboard, avg basket, items sold, busiest hour).
> - **⚠ one blank:** receipt VAT = placeholder `CHE-XXX.XXX.XXX MWST` → needs Felix's real UID (a NEED-FROM-FELIX item, not a blocker for staging).
>
> Next after this train: 🔴 `219d42a1` "Report totals are wrong"; velocity report #2.

> **Zero-inventory train — SHIPPED to banco.lapiazza.app @ `b7f083a`, 2026-06-22**
> (Angel Fairphone PASS, full mobile sheet 12/12; 24 Playwright E2E green on staging).
> One train, the whole sprint:
> - **BL-91 receiving** — goods-in as **cataloguing** (no counts): scan an arrival → it
>   joins the catalogue (one row, no qty), `pos_stock_movements` audit. New lazy-create
>   captures **purchase cost + box→per-unit helper**.
> - **BL-93 QR** — scanner reads QR *and* EAN/UPC (our own labels + unbarcoded goods).
> - **BL-94 full zero perpetual inventory** — a sale is never blocked by a count and
>   never moves it; refund money-only; low-stock/reorder signal dropped; no stock badge.
> - **BL-95** — receiving opens the create-modal for unknown items (404-detect fix, caught by E2E).
> - **BL-126** — receipt prints ONE page (kill blank page 2).
> - **BL-FB** — feedback button draggable. On ship, close feedback items "Feedback covers submit" (#86, #88).
> - **BL-92 image intake** (Pillow) — PARKED, not on this train (needs an image rebuild,
>   nothing imports it yet; waits for the slip-reader).
>
> Verified in the running prod container: `Insufficient stock`=0, QR_CODE present,
> receipt min-height reset, receiving 404-detect, "Scan arrivals into the catalogue".

> **BL-90 scan-recognition hardening ("scan once, known forever")** — fixes the bug
> where the same item got captured under different/garbage barcodes so a clean scan
> 404'd and Felix re-entered it. **SHIPPED — banco.lapiazza.app @ `8e27725`, 2026-06-21**
> (retail-only formats served, scan/catalog pages 200, alias lookup live: both Gizeh codes
> resolve to one product on prod). Angel Fairphone PASS ("scans clean"). Four parts:
> 1. **Retail formats only** — dropped CODE_128/CODE_39/ITF (the logistics/case codes
>    + GS1 \x1D capture); scanner now decodes EAN_13/EAN_8/UPC_A/UPC_E only. The
>    counter (`scan.html`) now shares the ONE hardened `PosScanner` instead of its own
>    copy (seal lesson — one scanner, used by counter + catalog + future receiving).
> 2. **Stable read** — a code is accepted only after decoding identically twice in a
>    row (kills partial/misreads); the live number shows in the overlay.
> 3. **Alias barcodes** — new `product_barcodes` table (one product, many codes);
>    lookup resolves on `products.barcode` OR an alias; `POST /products/{id}/barcodes`
>    attaches an extra code; the lazy-capture modal can "link to existing" instead of
>    making a duplicate.
> 4. **Data normalization** — `scripts/bl90_normalize_barcodes.py` splits space-joined
>    multi-barcode fields (root cause on a full import: `"EAN1 EAN2"` in one field never
>    exact-matched a single scan) → first code primary, rest aliases; collision-aware +
>    idempotent, `--dry-run` first. **61 such rows fixed in the LOCAL full-import DB.**
>    NOTE: the SHARED prod/staging catalog has only ~3 problem rows and the normalizer is
>    a **no-op** on them — so there is NO risky prod data write here.
>
> Staged @ `4f184d4` (table `product_barcodes` created on shared DB), prod code @ `8e27725`.
> Local: 110 POS tests pass (106 + 4 new alias tests; also fixed the pre-existing
> `find_product` flake by switching it to the exact barcode endpoint). JS parse-clean.
>
> **Two known bad PROD rows — RESOLVED 2026-06-21 (Angel's calls, applied to shared DB):**
> - *Gizeh Rolls Extra fine 5M* — kept `421123680670` (row `e9522f3e`); aliased `42238072`
>   onto it and soft-deleted the duplicate row `f5535425`. Both codes now resolve to the
>   one product via the staging API. ✓
> - *Hemp Sana Salbe* (`02c8ae9c`) — barcode NULLed (was garbage `59␝788130`); a clean
>   re-scan will re-capture + link. ✓
>
> **Camera reliability is Angel's Fairphone gate** (can't unit-test the lens).
> Awaiting: Angel scans real Artemis stock on staging-banco → then prod train.

> **BL-89 catalog polish + dup-barcode fix** — `7c344e1`, `2015f36`. 📷 scan on create/edit (shared
> `static/pos-scanner.js`) + category datalist (pick-existing-or-new); create/update now return a clean
> **409** on duplicate barcode/SKU (was a raw 500 Angel hit on save). **SHIPPED — banco.lapiazza.app @
> `2015f36`, 2026-06-21** (catalog 200, scanner asset 200, prod smoke: save 201 + dup 409, no 500). Angel
> PASS. Next: BL-90 receiving.

> **BL-88 catalog management dashboard (`/pos/catalog`)** — `8b522a0`. Manager-gated CRUD over products
> (search/edit price+stock+picture+reorder, discontinue+reactivate, create), dashboard card. Added
> image_url/supplier_name/min_stock/max_stock/lead_time_days to ProductBase/Update (additive). Angel
> PASS on staging. **SHIPPED — banco.lapiazza.app @ `7721a36`, 2026-06-21** (page 200, card wired, scan
> still live). Polish queued: category dropdown (from existing), camera-scan on create (unify w/ lazy capture).

> **BL-87 camera barcode scan + lazy capture (`/pos/scan`)** — `275e0a9`, `755ea99` (+ spec `90ac996`).
> Camera PASSED on Angel's Fairphone (AC1/AC4). Verified on real device traffic (staging txns 0132-0136):
> Felix(admin) lazy capture PERSISTS real products + qty 2/3 rang fine; Pam(cashier) → graceful one-off
> line (403 create guard, **by design**). Angel decision: **create stays manager-only, ship as-is.**
> **SHIPPED — banco.lapiazza.app @ `c4b4e61`, 2026-06-21** (vendored JS 200, scan page 200, camera button
> served, no CSP blocks camera). Deploy = move `/opt/helix-banco-tree` to origin/main + restart `helix-platform-banco`.

> _(BL-84 / BL-83 / BL-85 — Felix's three live feedbacks — and BL-86 (reaper + hide-cancelled)
> all **SHIPPED 2026-06-21**, see history below.)_
| Banco feedback: file + camera attachments | `0013263` (backend) + `4aba2da` | green (7/7 attach+screenshot, dog-fooded: img + 2 PDFs) | **SHIPPED — banco.lapiazza.app @ 8303204, 2026-06-21** |
| Banco cash shift — per-cashier drawer (incr 1-3) | `2d9df70`,`94a9c75`,`cc7b886` | green, "per-cashier isolation proven" | **SHIPPED — banco.lapiazza.app @ 8303204, 2026-06-21** |
| Status bar: real version + git SHA stamp | `af62709` | green — shows `v3.3.0 (af62709)`, env `uat` | **SHIPPED — banco.lapiazza.app @ 8303204, 2026-06-21** |
| Shop Pulse card (live 📊: sales/members/stock/drawers) | `af62709` | green — `GET /pos/system/pulse` 200, real stats | **SHIPPED — banco.lapiazza.app @ 8303204, 2026-06-21** |
| `/health/dashboard` diagnostics page (health + system + browser/screen specs) | `04ae273` | green — HTTP 200, all cards render, env UAT | **SHIPPED — banco.lapiazza.app @ 8303204, 2026-06-21** |
| Banco CRM Phase 0 (FK fix + on-sale attach/earn/re-tier/enroll) | `a6ef751`,`0013263`,`94a4619`,`9057c1d`,`675c6de`,`825a96e` | green — Angel signed off on staging | **SHIPPED — banco.lapiazza.app @ 8303204, 2026-06-21** |
| No-cache headers on server-rendered HTML (kills the stale-page ghost) | `a381563` | green — staging sends `no-cache` on /pos pages (verified) | **SHIPPED — banco.lapiazza.app @ 8303204, 2026-06-21** |
| Member directory + multi-match picker ("several Larrys") | `d76b751` | green — diagnostics page + members list confirmed on staging | **SHIPPED — banco.lapiazza.app @ 8303204, 2026-06-21** |
| Release-gate story suite + refund returns goods to shelf | `b76a6ee` | green — 13 gate tests + full refund restores stock | **SHIPPED — banco.lapiazza.app @ 8303204, 2026-06-21** |

## ✅ Banco IS live on prod (as of 2026-06-21)

`banco.lapiazza.app` now serves the **clean `origin/main` (8303204)** POS from its OWN
container `helix-platform-banco` (worktree `/opt/helix-banco-tree`, port 127.0.0.1:8098,
compose `hetzner/docker-compose.banco-prod.yml`). Caddy `banco.lapiazza.app` → that
container. Cashier login (felix, kc-pos-realm-dev) + authed Shop Pulse verified live.

**The divergent Bottega `helix-platform` (#140) was LEFT UNTOUCHED** — `bottega.lapiazza.app`
still serves it; the 1,204-line uncommitted divergence is backed up at
`/root/banco-prod-divergence-20260621/`. #140 reconciliation remains a separate task.
Note: the **prod Caddyfile is itself divergent** (has banco/staging-banco blocks not in
git) — its banco block now points to `helix-platform-banco`; backup `/root/Caddyfile.bak-20260621-133619`.

## Shipped (history)

- **2026-06-26 — Universal System Info + honest health grading (@ `f5feade` on `main`).** Driver: Tigs
  (Angel: "build that bundle… juice it up"). Three fixes in one: (1) **health grading** — only CRITICAL
  deps (PostgreSQL, Keycloak) drive DEGRADED/503; Celery + Redis/RabbitMQ/MinIO/render-worker/LibreTranslate
  reported but never flip overall (Celery is vestigial — async runs via `lpcx-consumer`). Killed the false
  "DEGRADED" on every Banco env. (2) **new `GET /health/system`** rich JSON (build, env, wiring, storage,
  uptime, dependency grid w/ latency) + short aliases `/system` + `/diagnostics`. (3) **dashboard** —
  env-colour theming (red prod/amber staging/blue sandbox), Wiring + Storage cards, real commit+date via
  2-line `build-sha.txt`, 15s auto-refresh. **Deploy = file-overlay on the 4 active worktrees** (sandbox,
  staging, banco, banco-staging) + restart; verified healthy (prod `/health/system` = OK, banco_prod 30 MB).
  Prod-banco worktree HEAD stays `3547efa` (overlay on top) — becomes a tracked SHA at the next advance.
  **⚠ Incident + lesson:** the initial deploy mistakenly also hit the **legacy pinned `/opt/helixnet`** tree
  (bottega prod) → `ImportError: __version__` crash-loop for a few min; reverted that tree, restored healthy.
  Rule recorded: never blanket-deploy current-`main` files to `/opt/helixnet`. Also cleaned today: Keycloak
  `event_entity` bloat (835 MB → 17 MB; 30-day expiry on all realms). Co-shipped CLI: `kc_admin list-realms`
  (`12fcf56`) — ad-hoc tool, no container deploy.
- **2026-06-21 — BL-86 empty-cart reaper + hide-cancelled (@ `3c29154`).** Cancels stale
  `OPEN` carts that are zero-value + empty + >12h old (CANCELLED, never deleted; hourly
  background loop + `POST /maintenance/reap-empty-carts` for mgr/admin). Cancelled carts are
  hidden from the default transactions view (still reachable via `status_filter=cancelled`).
  Staging proof: reaped 11 real 06-20 carts; prod redeploy found them already cancelled
  (idempotent on the shared DB). Driver: Tigs (Angel: GO).
- **2026-06-21 — Felix's 3 live feedbacks (one train, @ `21742df`).** BL-84 (real
  payment-method breakdown on the report + new `BANK_TRANSFER` type — fixed ~CHF 25k of
  visa/twint that rendered as zero), BL-83 (cashier names on the transactions report —
  129 rows show Felix/Pam, no more generic "Cashier"; dropped the duplicate # line), BL-85
  (status bar fits mobile portrait so the 📊 stays reachable). Staged + Angel-PASSED on
  staging-banco, then shipped together via the clean `helix-platform-banco` container
  (worktree reset to origin/main + restart). Smoke green on banco.lapiazza.app. Bottega
  `#140` untouched. Driver: Tigs (Angel: GO).
- **2026-06-21 — Banco stand-up on prod (first Banco-on-prod).** 9 features (feedback
  attachments, cash-shift drawers, status-bar stamp, Shop Pulse, /health/dashboard, CRM
  Phase 0, no-cache headers, member directory, release-gate suite) went live on
  `banco.lapiazza.app` via a NEW clean container at `8303204` — NOT by reconciling the
  divergent Bottega tree. Bottega untouched. Driver: Tigs (Angel: PATH 1).
