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

`🟢 IDLE` — no train running. (Last shipped: **Settings + photo + reports train @ `acf337a` → banco.lapiazza.app, 2026-06-23** — Angel staging PASS 10/11; prod smoke green: `artemis-logo.png` 200, login 200. Rollback `ad4ad07`.)

## Boarding (awaiting the next prod train)

> 🔴 **HOTFIX — cashier barcode born-once PHANTOM — `110f101`, STAGED, awaiting Angel mobile PASS** (2026-06-23):
> A **cashier** scanning a **brand-new barcode** → product **sold but never catalogued** (silent data
> loss; breaks "scan once, known forever"). Found by Angel on the Fairphone. Root cause: `scan.html`
> `saveLazyCapture()` posted to **manager-only `POST /products`** → cashier 403 → silent one-off `[NEW]`
> phantom. **Fix (1 line): route to cashier-safe `POST /products/quick`.** DB-confirmed (0 rows for the
> "created" product). Doc: `docs/testing/banco/BL-BUG-cashier-barcode-create-phantom.md`.
> Mobile test sheet: `docs/testing/banco/BANCO-BUGFIX-CASHIER-CREATE-TEST-SHEET.html`.
> **→ FORGE:** sibling seal `receiving.html:263` hits the same manager-only `/products` (fails *loudly*,
> no phantom) — route to `/products/quick` too if cashiers receive. `catalog.html:417` is correctly
> manager-only — leave it.
> **→ ANGEL:** test on your phone as **pam**; all-green = flip this to `APPROVED` → rolls on the next prod train.

> **NEXT TRAIN — built/queued, NOT yet staged:**
> - **env-colour login** (organic/mystical, per-env) + **tighter print receipt header** — committed `4587189`, local only.
> - **Fix-after from Angel's staging PASS (2026-06-23):**
>   - create-form papercuts ("Pam's fat fingers"): category needs a default, description should autopop, name-first ordering — make it forgiving.
>   - logo: simple **file-upload → auto thumbnail + logo** (not a URL field).
>   - cash-variance **tolerance configurable in Settings** (±0.20 / 5-CHF).
>   - receipt: header+footer double-spacing — header capped (`4587189`), **footer still needs tightening**.
>   - version stamp shows a **stale baked SHA** (`5f0cef7`) not the live worktree HEAD — cosmetic, fix `get_git_sha`.

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
