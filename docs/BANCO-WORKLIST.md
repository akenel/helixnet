# Banco Go-Live Worklist — THE ordered list

> 🔑 **Code word "ON DECK"** → you're reading the right file. State the top items and start executing the first actionable one. No re-planning, no re-asking.

*Open this, work top-down, finish one tier before opening the next. Don't fan out across five things. 2026-06-28.*

*Owners: 🧍 = Angel's hands needed (physical / decision / external call) · 🐯 = Tigs can do it · 👥 = both, together.*

*Detail lives in: [BANCO-GO-LIVE-READINESS.md](BANCO-GO-LIVE-READINESS.md) (analysis) · [BANCO-DAY-ONE-WISHLIST.md](BANCO-DAY-ONE-WISHLIST.md) (polish backlog).*

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
