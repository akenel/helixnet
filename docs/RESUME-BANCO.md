# PASTE-IN — Resume Banco (head-shop POS) · staging is LIVE, VAT just fixed

**Read first:** `docs/BANCO-REALM-MODEL.md` (realm=shop north star), then this. The big plan docs:
`HEADSHOP-ERP-GRAND-PLAN.md`, `HEADSHOP-ERP-EXECUTION-AND-CUTOVER.md`, `HELIXNET-ESTATE-MAP.md`, `BANCO-LAPIAZZA-RUNBOOK.md`.

## What Banco IS (one line)
**Banco** (the counter) = Swiss-native head-shop POS/ERP on the HelixNet engine. **Felix's Artemis shop = customer #1.**
URL `banco.lapiazza.app` → existing `helix-platform` → `/pos`. Realm = a SHOP; environment (dev/staging/prod) = where it runs.

## STATE as of 2026-06-20 (end of session "HelixNet-Banco-POS-Artemis")
**Staging is REAL and login WORKS.** `https://staging-banco.lapiazza.app/pos` — log in `felix`/`helix_pass` (or `pam`),
realm `kc-pos-realm-dev`, client `helix_pos_web`. Verified working end-to-end via OBS video (felix + pam both in).
**Everything below is committed on `origin/main` and deployed to STAGING ONLY. PROD UNTOUCHED.**

### What shipped to staging this session
- **Till bricks** (earlier): Banana CSV (`/api/v1/pos/reports/daily-summary.csv`), stock-deduct on checkout, printable Z-report.
- **staging-banco.lapiazza.app wired**: DNS A records added (Porkbun: banco, staging-banco, both → 46.62.138.218),
  Caddy block appended (`hetzner/Caddyfile`, root→/pos), stale-inode mount healed via `up -d --force-recreate caddy`.
- **POS login fixed** (3-bug chain, the painful one): (1) templates hardcoded `keycloak.helix.local` → now use the
  **canonical KC host** `lapiazza.app` for the login/logout leg (commit b7a631c); (2) added staging redirect URIs to
  `helix_pos_web` AND `artemis_pos`; (3) cleared `kc-pos-realm-dev` realm `frontendUrl`/`adminUrl` (they were pinned to
  keycloak.helix.local → forced the login form to POST to the wrong host → "Cookie not found"/400).
  **Root lesson:** KC has ONE front door (`KC_HOSTNAME_URL=https://lapiazza.app`); the whole login leg must run on it.
- **Login page UX**: Sign Up / Forgot Password / Log Out buttons added (commit 0b1c021); realm `registrationAllowed` +
  `resetPasswordAllowed` enabled. Log Out is the escape hatch for "already logged in".
- **⭐ Inclusive Swiss VAT FIXED** (commit 1013395 — the headline): `tax_amount` was hardcoded 0 everywhere. Now
  `_inclusive_vat(gross)=gross*rate/(100+rate)` computed on add_item + re-asserted at checkout; subtotal & total stay
  GROSS (what's paid); receipt shows TOTAL (gross) with `incl. VAT (8.1%)` below + real product name (was "Product");
  daily summary returns `vat_total`; Z-report prints the VAT line. Files: `pos_router.py`, `pos_schema.py`,
  `templates/pos/receipt.html`, `templates/pos/closeout.html`.

### Test sheets (in `docs/testing/banco/`)
- **TEST-BANCO-002 = `BANCO-POS-TEST-RUN.html`** ← the ROBUST one (DOOR-RELEASE engine): per-step PASS/FAIL/ISSUE,
  🎤 mic everywhere, 📋 screenshot attach (paste/drop/pick), timer, autosave, Export-report-with-screenshots. **USE THIS.**
- TEST-BANCO-001 = `BANCO-STAGING-TEST-SHEET.html` (older, lighter).

## NEXT (in order)
1. **Angel runs TEST-BANCO-002 on staging** to verify the VAT fix + catalog stock + bricks. Ring a FRESH sale
   (old transactions are already-wrong historical rows). Export the report → Tigs reads it.
2. **If PASS → deploy to PROD** per `BANCO-LAPIAZZA-RUNBOOK.md`: `git checkout origin/main -- <files>` + `docker restart
   helix-platform` (NEVER `git pull` in /opt/helixnet), add prod redirect URIs (`banco`/`bottega`.lapiazza.app) to
   `helix_pos_web`, wire prod `banco.lapiazza.app` Caddy block. Smoke-test.
3. **Open findings still to fix** (logged from the first test run):
   - **P2** "Agreed Final Total" override mangles price (90→83.26) — client-side in checkout.html; revisit with inclusive model.
   - **Catalog doesn't show on-hand stock** — UX gap ("catalog is key").
   - **Navigation**: back button → cart instead of catalog.
4. **Later / deliberate**: artemis realm rename (realm=shop, both KCs already have `artemis`+`artemis_pos`, redirect URIs
   half-done); per-env Keycloak split (kills SSO bleed); the setup wizard (brain `shop_setup_service.py` done — needs
   currency+language columns migration, `POST /api/v1/pos/setup`, form page, realm provisioning via `lp_create_realm.py`).

## Hard-won rules (don't relearn the painful way)
- Keep testing/fixing on **staging** (`staging-banco`/`staging-bottega`.lapiazza.app); **prod only on Angel's PASS**.
- KC = one front door (`KC_HOSTNAME_URL=lapiazza.app`); login leg runs there, returns via redirect_uri. Realm `frontendUrl`
  must be EMPTY (not pinned to keycloak.helix.local) or the form posts cross-host → cookie 400.
- Caddy: edit `hetzner/Caddyfile` **in place**, verify `md5sum` host == container; if stale → `up -d --force-recreate caddy`.
- **Screenshots > video > voice** for feedback. Video only for flow/sequence bugs (it cracked the login chain). Mic needs Chrome.
- Sample/dummy data is fine for demos (VAT/AHV = 12345…); real config comes from the wizard, in staging.
- Box = `ssh root@46.62.138.218`; all test users = `helix_pass`; staging shares the prod DB.
