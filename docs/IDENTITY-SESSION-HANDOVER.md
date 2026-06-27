# Identity consolidation — session handover

*Written 2026-06-26, before a laptop reboot. Paste this path into the next session to resume:
`docs/IDENTITY-SESSION-HANDOVER.md`. Companion docs: [`IDENTITY-CONSOLIDATION-PLAN.md`](IDENTITY-CONSOLIDATION-PLAN.md)
(the project board), [`IDENTITY-UNIFIED-REALM-BLUEPRINT.md`](IDENTITY-UNIFIED-REALM-BLUEPRINT.md) (the Phase-2 spec),
[`IDENTITY-THREE-REALMS-LEGO.md`](IDENTITY-THREE-REALMS-LEGO.md) (plain-language model).*

---

## The one-line state

Three-realm identity consolidation is **FOLDED on all three envs** — sandbox (`kc-sandbox`),
staging (`borrowhood-staging`), and **PROD (`borrowhood`, folded 2026-06-27, Angel option A)**.
Every env: POS folded into the env realm, app repointed, single-host login, felix=admin / pam=cashier,
HR/My-Day working. **The ONLY identity work left = the Phase-4 RENAME** (`borrowhood-staging`→`kc-staging`,
`borrowhood`→`kc-production`) — deferred by Angel ("do it after"), its own gated lockstep cutover.

## The locked model (don't relitigate)

Exactly **3 realms, one per environment**: `kc-sandbox` / `kc-staging` / `kc-production`.
Inside each: every app = a **client**, every person = **one account**, workforce-vs-public = a
**role tier** (`member`/`business` = public, `staff`/`admin` = workforce), every shop = a **group**
(`shop:artemis`). No per-app realms, no per-population realms. Emoji dropped from all role names.

## What is DONE and green

- **Phase 1** (code): all apps env-driven for their realm. Committed `f11b1c9`. The POS realm-split
  template/callback fix is on main as `a69ce61`.
- **Phase 2 — sandbox built**: `scripts/build_unified_realm.py` laid `kc-sandbox` on the box KC:
  15 app clients + 4 tier roles (`member` default) + 30 plain app roles + `shop:artemis`. Idempotent.
- **Phase 2 — sandbox proven**: `scripts/proof_unified_realm.py` — `pam` carries `pos-cashier` +
  `member`, one token. PASSED.
- **Phase 2 — sandbox CUTOVER LIVE (2026-06-26, this session):** the running sandbox Banco app is
  repointed to `kc-sandbox` and verified on the real app:
  - `https://sandbox-banco.lapiazza.app/pos` serves `realm: 'kc-sandbox'`
  - KC auth endpoint 200 for `helix_pos_web` w/ sandbox callback
  - `pam / helix_pass` logs in, token has `pos-cashier` + `member`
  - **Login: pam / helix_pass. Catalog empty by design (`HX_SEED_DEMO=false`).**
- **Phase 2 — STAGING fold + CUTOVER LIVE (2026-06-26):**
  - Realm reality corrected: `borrowhood-staging` has **20 KC users, not ~140** ("140" conflated the
    224 `bh_user` DB personas). Prod `borrowhood` = 311 (was 305). 14 realms on box now (kc-sandbox added).
  - Scaffolding laid on `borrowhood-staging` via `build_unified_realm.py --apply`: +11 app clients,
    +26 roles (4 tiers + pos/camper/isotto/platform), `member` default, `shop:artemis`. Idempotent re-run = all `=`.
    `lapiazza-business` already existed on staging (the missing-role gap is **prod-only**).
  - **One canonical Felix** (`fold_staging.py`): the surviving `felix` (borrowhood-staging) now carries
    BOTH hats — `pos-admin`+`staff` (workforce) alongside `business`+`lapiazza-business`+`bh-*` (public),
    in `shop:artemis`. Email set to canonical `angel.kenel@gmail.com` (Angel's call; **was `felix@artemis.ch`** — revert target).
    The redundant `kc-workforce-stg` felix dies with that realm.
  - `pam` seeded (pos-cashier+member, `helix_pass`); `proof_unified_realm.py borrowhood-staging` PASSED.
  - **CUTOVER:** `docker-compose.banco-staging.yml` `POS_REALM kc-workforce-stg → borrowhood-staging`,
    container recreated. Verified: served `/pos` realm = `borrowhood-staging`, KC auth 200. Seal-check
    PASSED (staging tree login.html + base.html already `{{ pos_realm }}` — fully sealed, unlike sandbox).
  - Backups: `docker-compose.banco-staging.yml.pre-fold-*.bak`. Rollback = restore + recreate.
  - **Smoke:** `staging-banco.lapiazza.app/pos`, login `pam / helix_pass` (or `felix`).
- **Cross-host login 400 found by smoke + FIXED (2026-06-26):** first POS login POST returned 400
  ("cookie not found"). Root cause: shared realm `borrowhood-staging` had a `frontendUrl` override =
  `https://staging-bottega.lapiazza.app`, but the POS template hardcodes the canonical front-door
  `https://lapiazza.app` (per `KC_HOSTNAME_URL`) — auth cookie set on `lapiazza.app`, form POST went
  to `staging-bottega` → split. **The realm was the lone anomaly** (prod `borrowhood` + old
  `kc-workforce-stg` both = `lapiazza.app`). Two-part fix, both reversible, aligns staging to prod:
  1. realm `borrowhood-staging` `frontendUrl` → `https://lapiazza.app` (was `https://staging-bottega.lapiazza.app`;
     issuer now `https://lapiazza.app/realms/borrowhood-staging`). Rollback = `fix_frontendurl.py` w/ old value.
  2. Bottega staging `helix-platform-staging` `LP_KC_PUBLIC_URL` → `https://lapiazza.app` (was
     `staging-bottega`; prod Bottega has no override = uses the `lapiazza.app` default). Backup
     `docker-compose.helix-staging.yml.pre-frontendurl-*.bak`; rollback = restore + recreate.
  Verified: auth GET, login **form action**, and cookies all on `lapiazza.app` (single-host) → 400 gone.
  **NOTE for prod fold:** prod is already consistent (realm + Bottega both `lapiazza.app`); BUT prod
  Banco `helix-platform-banco` has `LP_KC_PUBLIC_URL=staging-bottega` + `LP_REALM=borrowhood-staging`
  (the shelf publish bug) — that is ALSO a login-host bug; fix when prod Banco is folded.
  - **Smoke BOTH after fix:** Banco `staging-banco.lapiazza.app/pos` (pam/helix_pass) AND Bottega
    `staging-bottega.lapiazza.app` (login still works) — both now auth via `lapiazza.app`.
- **Rename method proven** (in-place rename keeps password hashes — no reset). Authorized for Phase 4.

### Missed-seal bug found + fixed (this session)
The sandbox cutover wasn't "flip one env var" — the deployed box code was **half-fixed**. A prior
hand-overlay applied the realm-split fix to `pos_router.py` and `base.html` but **skipped
`login.html`** (still hardcoded `kc-pos-realm-dev`). Fixed that one line to match main's `a69ce61`.
Lesson: the fix that's on `main` was only partially applied on the box — *if one seal fails, check
all the seals.* The box's OTHER uncommitted overlay files (`build_info.py`, `main.py`,
`health_router.py`, `pos_router.py`, `base.html`, etc.) were left untouched.

## How the sandbox cutover was made (for reference / to mirror on staging)

1. `POS_REALM: kc-sandbox` added to `/opt/helixnet/hetzner/docker-compose.banco-sandbox.yml`
   (env block, just above `LP_REALM`).
2. `cd /opt/helixnet/hetzner && docker compose -f docker-compose.uat.yml -f
   docker-compose.helix-staging.yml -f docker-compose.banco-prod.yml -f
   docker-compose.banco-sandbox.yml up -d --no-deps helix-platform-sandbox`
3. Fixed `/opt/helix-sandbox-tree/src/templates/pos/login.html:124` → `{{ pos_realm }}`;
   `docker restart helix-platform-sandbox`.

### Rollback (sandbox), ~20s — backups on the box
- `/opt/helixnet/hetzner/docker-compose.banco-sandbox.yml.pre-kc-sandbox.bak` (remove `POS_REALM`, recreate)
- `/opt/helix-sandbox-tree/src/templates/pos/login.html.pre-realm-fix.bak`

## NEXT STEPS

**1. ✅ DONE — `kc-workforce-stg` retired (2026-06-27):** backed up to
`/opt/helixnet/hetzner/kc-workforce-stg-backup-20260627.json` (7 clients, 8 roles, 1 redundant
`felix`), then deleted (confirmed 404). Box now at 13 realms.

**1b. ✅ DONE — PROD FOLD (2026-06-27, Angel option A "fold now, rename later"):**
Backups: `/opt/helixnet/hetzner/PRODBAK-20260627-{borrowhood,kc-pos-realm-dev}-{config,users}.json`.
- 5 surgical code seals overlaid on `/opt/helix-banco-tree` (`.pre-prodfold.bak` each): `login.html`
  realm→`{{pos_realm}}`, `pos_router.py` ×2 callback realm→env-driven, `base.html` emoji→plain admin
  gate, `hr_router.py` greenlet refresh, `my_day.html` text. (`my_day` goSales already present.)
- Scaffolding applied to `borrowhood` (additive: POS clients + tier/pos roles + `lapiazza-business`
  + `shop:artemis` + `member` default). 313 marketplace users + issuer UNCHANGED.
- Real staff created in `borrowhood`: `felix`(pos-admin+staff+business), `pam`(pos-cashier),
  `ralph`(pos-manager+staff), all `helix_pass`, emails `*@artemis-store.local` (NOT gmail — taken by
  `angel`). The 9 dev/test personas in `kc-pos-realm-dev` were NOT folded.
- Repointed `docker-compose.banco-prod.yml` (`.pre-prodfold-*.bak`): `POS_REALM`→`borrowhood`, +
  **fixed the two bugs** `LP_REALM borrowhood-staging→borrowhood` & `LP_KC_PUBLIC_URL staging-bottega→lapiazza.app`.
- Verified: served realm `borrowhood`, KC auth 200, E2E felix=admin/pam=cashier(403 gate), HR 200,
  prod Bottega healthy, marketplace issuer unchanged. Rollback = restore the `.bak`s + recreate.
- ⚠ Pre-existing non-fatal startup error noted: `user_service.create_initial_users` seeds "taxman"
  with null `keycloak_id` (constraint) — every restart, non-blocking, not from this work.
- `kc-pos-realm-dev` (old prod POS realm) NOT deleted yet — retire after prod soak.

**2. Phase-4 RENAME** (deferred by Angel — "do it after"), mirroring staging+prod together:
```
PW=$(docker exec keycloak printenv KEYCLOAK_ADMIN_PASSWORD)
# DRY-RUN first:
docker exec -e KC_ADMIN_PASSWORD="$PW" helix-platform-sandbox /app/venv/bin/python \
  /tmp/build_unified_realm.py borrowhood --kc-url http://keycloak:8080 \
  --admin-user helix_user --base-domain banco.lapiazza.app
```
Prod specifics: **ADD missing `lapiazza-business` role** (gap is prod-only); prod Banco currently runs
on `kc-pos-realm-dev` (no override in `docker-compose.banco-prod.yml`) → repoint `POS_REALM` to
`borrowhood`; check the staging-tree-style seal (login.html/base.html `{{ pos_realm }}`) on the prod
banco tree before relying on the env flip; full export-backup before any prod write.

**3. Then** Phase 4 rename to clean names (`borrowhood→kc-production`, `borrowhood-staging→kc-staging`),
then Phase 3 delete dead realms.

## Sandbox login bug found by test sheet + FIXED (2026-06-27)
Staging sheet = 100% green (POS no-400, Bottega intact, one Felix both hats). **Sandbox failed: login
served `realm: ''` (empty).** Root cause: the sandbox tree's `pos_router.py` was an OLDER copy
**missing the entire realm-split fix** — no `templates.env.globals["pos_realm"] = get_settings().POS_REALM`
(so `{{ pos_realm }}` rendered empty) AND two callback/token spots still hardcoded `kc-pos-realm-dev`.
A prior session fixed sandbox `login.html` but never folded `pos_router.py` — *the seal lesson, one
level deeper.* Fix: synced `pos_router.py` from the proven `helix-banco-staging-tree` (full diff was
ONLY the realm-split fix + 1 cosmetic docstring) + restart. Backup
`/opt/helix-sandbox-tree/src/routes/pos_router.py.pre-realmfix-*.bak`. Verified: served realm now
`kc-sandbox`, pam direct-grant 200, form host `lapiazza.app`.
**🔴 PROD-FOLD BLOCKER — HR self-heal greenlet 500 (found on staging 2026-06-27, fixed):**
After the fold, every user logs in with a NEW `sub`, which forces `hr_router.get_employee_from_token`'s
username self-heal path. That path had a latent bug: `await db.commit()` expired the ORM object, then
`logger.info` read `employee.first_name` → `sqlalchemy MissingGreenlet` 500; the bare `except` rolled
back (undoing the heal) and returned the expired object → caller's `employee.id` 500'd too → **permanent
500 on My Day / all `/api/v1/hr/*` for every post-fold user.** Fix (committed-pending): log with
`username` only + `await db.refresh(employee)` after commit/rollback. Deployed to `helix-banco-staging-tree`
(backup `hr_router.py.pre-hrgreenlet.bak`), verified pam → 200 on me/time-entries/stats. **MUST be on
prod BEFORE the prod fold** or every staff member's My Day breaks on first login. (Also a BL-012 fix:
`my_day.html` "See each sale" → `/pos/transactions`, deployed staging, backup `my_day.html.pre-bl012.bak`.)
Both edits are uncommitted in the local repo (branch `feat/banco-offline-pwa`) — commit so they ride the
release train to prod rather than living as hand-overlays.

**🔴 PROD-FOLD BLOCKER #2 — frontend admin gate is emoji-only (found 2026-06-27, fixed):**
`pos/base.html` `AuthHelper.isAdmin/isManager/isCashier` exact-matched EMOJI role names
(`'👑️ pos-admin'`). The unified realm uses PLAIN names → after the fold felix's `pos-admin` failed
`isAdmin()` and he dropped to a cashier screen (backend was fine — `keycloak_auth.role_matches` does
substring, so no 403s; UI was the only break). Fix: emoji-tolerant `hasRole` (`r.includes(role)`) +
plain names. Applied to repo + both trees (`base.html.pre-emojirole.bak`), verified felix=admin /
pam=cashier on both envs. **The prod Banco tree's `base.html` has the SAME emoji gate — fix it with
the prod fold or every manager/admin loses their UI.** (Backend emoji role names in `pos_router.py`
require_roles are fine via substring, but cleaning them to plain is the noted cutover tidy-up.)

**✅ Full E2E + regression run (2026-06-27):** both users × both envs — pam=cashier(403 on admin
gate), felix=admin(passes), served `base.html`=plain, HR/My-Day 200. POS regression suite vs staging
= **149 passed / 18 failed / 6 skipped**; ALL 18 failures are missing test-seed SKUs (`CBD-Oil-20ml`
etc. not in staging's 436-product catalog) — **zero regressions** from the identity work. Self-test
sheet for Angel: `https://sandbox-banco.lapiazza.app/static/TEST-banco-roles-sandbox.html` (11 checks,
admin+cashier, 5 seeded products w/ barcode chips; sandbox = 5 products / 0 sales / felix+pam both work).

**⚠ PROD-FOLD SEAL CHECK (do before repointing prod Banco):** the prod Banco tree
(`/opt/helix-banco-tree`) may have the SAME older `pos_router.py`. Before/with the prod repoint, diff
its `pos_router.py` + `templates/pos/{login,base}.html` against `helix-banco-staging-tree` and sync the
realm-split fix, or the empty-realm login bug repeats on prod. Check ALL the seals.

## Human test sheets (phone-friendly, served live on the box)
- **Staging:** `https://staging-banco.lapiazza.app/static/TEST-identity-staging.html` (TEST-IDN-STG, 7 checks:
  POS login no-400, Bottega still works, one Felix both hats). Source `docs/testing/TEST-identity-staging.html`.
- **Sandbox:** `https://sandbox-banco.lapiazza.app/static/TEST-identity-sandbox.html` (TEST-IDN-SBX, 5 checks).
  Source `docs/testing/TEST-identity-sandbox.html`.
- Served from each env's `src/static/` (StaticFiles, no restart needed). Built from
  `docs/testing/QUICK-TEST-SHEET-TEMPLATE.html` via `scratchpad/gen_test_sheets.py`.
- Test creds: `pam / helix_pass` (both envs) + `felix / helix_pass` (staging dual-hat; felix's staging
  password was set to `helix_pass` for deterministic testing). **Prod gate = both sheets green.**

## Box facts (helixnet-uat, root@46.62.138.218)
- KC container has **no curl** (minimal image) → use the app venv `/app/venv/bin/python` (httpx) for admin calls.
- KC admin: user `helix_user`, password = `docker exec keycloak printenv KEYCLOAK_ADMIN_PASSWORD`.
- Realm issuers are global: `https://lapiazza.app/realms/<realm>` (consistent across realms).
- Sandbox container `helix-platform-sandbox` :8097, DB `banco_sandbox`, mounts
  `/opt/helix-sandbox-tree/src:ro`.

## Shelf items (don't block staging)
- `lapiazza-realm-staging` (162 users) — investigate before any delete.
- prod `borrowhood` MISSING `lapiazza-business` role — add during prod fold.
- `banco-prod.yml` `LP_REALM=borrowhood-staging` — prod-publishes-to-staging bug; verify vs live, fix independently.
- 4 uncommitted box overlay files (closed terminal's work) — review, don't clobber.
- `admin_router.py` emoji role catalog (~lines 133–265) — clean to plain names AT cutover, not before.

## Driving mode
Option (a): Tig drives the box via ssh. Sandbox writes OK. **STOP for explicit Angel "go" before any
staging/prod write.** Read-only first, dry-run before apply, one-env-var rollback at every cutover.

---
*Resume cue: read this file. Sandbox + staging are DONE (unified, repointed, dead realm retired).
Next is the PROD fold of `borrowhood` — say "go prod" to start (read-only list → dry-run → apply on
confirm → add missing `lapiazza-business` → repoint prod Banco + fix its LP_KC_PUBLIC_URL=staging-bottega bug).*
