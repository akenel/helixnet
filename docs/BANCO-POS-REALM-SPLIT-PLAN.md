# Banco POS realm split — dev/sbx → staging → prod (the simple fix)

*Scoped 2026-06-26. Implements the locked identity north-star (realm = environment) for the
POS/Banco realm. Pairs with [[helix-identity-architecture]] and BANCO-CLOSEOUT email path.*

---

## The problem (why we're here)

All four Banco environments share **one** Keycloak realm, `kc-pos-realm-dev`, and that realm's
SMTP points at **MailHog** (a dev mail-*catcher*). So the "📧 Email a sign-in link" feature
works — but every env's mail lands in the dev sink, never a real inbox. We can't just flip the
shared realm to a real mail provider, because that would also send **dev and test-run mail to
real people**, and because one realm means one blast radius for every auth change.

The fix is the thing the architecture already calls for: **one realm per environment.**

## The target — 3 POS realms, mail routed per env

| Env | App container | **POS realm** | Mail (SMTP) | Login host |
|-----|---------------|---------------|-------------|------------|
| dev (local) | `helix-platform` | `kc-pos-realm-dev` *(unchanged)* | **MailHog** | helix-platform.local |
| sandbox | `helix-platform-sandbox` | `kc-pos-realm-dev` *(unchanged)* | **MailHog** | sandbox-banco.lapiazza.app |
| staging | `helix-platform-banco-staging` | **`kc-pos-realm-stg`** *(new)* | **Resend** | staging-banco.lapiazza.app |
| prod | `helix-platform-banco` | **`kc-pos-realm-prd`** *(new)* | **Resend** | banco.lapiazza.app |

- **Dev + sandbox keep `kc-pos-realm-dev` + MailHog** — nothing changes; test mail never escapes.
- **Staging + prod get their own realm + Resend** — real delivery to real inboxes.
- Resend is already proven on this box: the `borrowhood` realm runs `smtp.resend.com:587`,
  `auth=true`, `from=noreply@lapiazza.app` (verified domain). We copy that exact shape.

## Why this is a *simple* fix, not a migration

1. **Zero code change.** `POS_REALM` is already an env-driven setting
   (`src/core/config.py:57`, default `kc-pos-realm-dev`). Pointing an env at its own realm =
   set `POS_REALM=kc-pos-realm-stg|prd` on that one container + restart. Nothing else in the app.
2. **The checkout self-heal guard already makes it safe.** A new realm mints **new Keycloak
   subs** for the same usernames. Because `users.id == sub` and `transactions.cashier_id`
   FK→`users.id`, the first sale by a re-provisioned cashier would have hit the old 500 — but
   the guard shipped to prod (`ed38c2b`) now **auto-creates the users row on first sale**.
   Old transactions keep their old `cashier_id` (history intact); new ones use the new sub.
3. **One-env-var rollback.** If anything's wrong, set `POS_REALM` back to `kc-pos-realm-dev`
   and restart that container. Done.

## The mechanism — clone, retarget, route, re-provision

Per new realm (`-stg`, then `-prd`), four small steps:

1. **Clone the config** from `kc-pos-realm-dev` — clients + roles, **not** users — via KC
   partial-export → create-realm. (`POST /admin/realms/{src}/partial-export?exportClients=true
   &exportGroupsAndRoles=true` → edit `realm` id + trim → `POST /admin/realms`.) A small Typer
   tool `scripts/clone_pos_realm.py` does this end-to-end (to be built on go).
2. **Trim redirect URIs** on the new realm's `helix_pos_web` client to **only that env's host**
   (staging realm allows `https://staging-banco.lapiazza.app/*`; prod realm allows
   `https://banco.lapiazza.app/*`). Keep `publicClient=true`, `standardFlow`, `directAccess`.
   Keep realm `frontendUrl = https://lapiazza.app` so email links resolve (the MailHog test
   link already used `lapiazza.app` — correct).
3. **Set SMTP = Resend** with the existing one-shot script (Angel supplies the Resend API key
   at the prompt — it's the SMTP password; KC masks it so it can't be copied from borrowhood):
   ```
   python scripts/configure_kc_smtp.py --kc-url https://lapiazza.app --realm kc-pos-realm-prd \
     --host smtp.resend.com --port 587 --starttls --auth --smtp-user resend \
     --from noreply@lapiazza.app --from-name "Banco" --test angel.kenel@gmail.com
   ```
4. **Re-provision the staff** for that env via Banco's **Settings ▸ Staff ▸ 🔑 Create sign-in**
   (Felix first, then cashiers). This creates them fresh in the new realm with the cashier role
   — the exact flow already shipped. Then **flip the container**: `POS_REALM=kc-pos-realm-<env>`
   + restart, and smoke-test.

## Cutover runbook (one env at a time, prod last)

**Phase 1 — staging** (rehearse the whole thing where it's cheap):
1. `clone_pos_realm.py kc-pos-realm-dev → kc-pos-realm-stg` (clients+roles only).
2. Trim `helix_pos_web` redirects to `staging-banco.lapiazza.app`.
3. `configure_kc_smtp.py … --realm kc-pos-realm-stg …` (Resend) + `--test` to a real inbox.
4. Set `POS_REALM=kc-pos-realm-stg` on `helix-platform-banco-staging`, restart.
5. Re-provision Felix via Staff tab → log in → ring one sale → 📧 email-setup → **link lands
   in the real inbox** (not MailHog). ✅ = green.

**Phase 2 — prod** (same steps, after staging is green):
1. `clone_pos_realm.py kc-pos-realm-dev → kc-pos-realm-prd`.
2. Trim redirects to `banco.lapiazza.app`.
3. `configure_kc_smtp.py … --realm kc-pos-realm-prd …` (Resend) + `--test`.
4. Set `POS_REALM=kc-pos-realm-prd` on `helix-platform-banco`, restart.
5. Re-provision the **real** prod staff (Felix + cashiers) via Staff tab. First sale each =
   self-heal guard creates their users row. Smoke: login + sale + email-setup to a real inbox.

**Rollback (either phase):** set `POS_REALM` back to `kc-pos-realm-dev`, restart. (Cashiers
provisioned in the new realm simply go unused; no data loss.)

## Risks & the honest caveats

- **Re-provisioning is required, not optional.** Existing prod cashiers were created in
  `-dev`; they do **not** exist in `-prd` until re-provisioned (new password set by Felix).
  Plan a 5-minute "set everyone up again" pass at cutover. (Small cast — see roster below.)
- **Old transaction history** keeps old `cashier_id`s that won't match the new users rows;
  name resolution falls back to an id-prefix for those legacy rows (cosmetic only, money is
  unaffected). New sales resolve correctly.
- **Resend "from" domain** must stay `noreply@lapiazza.app` (already verified in Resend for
  borrowhood). Don't use `angel.kenel@gmail.com` as `from` — Gmail isn't a Resend domain.
- **`POS_REALM` must be set where the container actually reads env** (the prod/staging
  `docker-compose.*.yml` on the box, not a code default). Verify with `docker inspect`.
- **Don't touch `kc-pos-realm-dev`.** Dev + sandbox keep it; leaving it on MailHog is correct.

## Current state (scanned 2026-06-26, the box KC)

- Realms today: `kc-pos-realm-dev` (MailHog), `borrowhood` (**Resend** ✓ template),
  `artemis`, `lapiazza-realm-dev/-staging`, `borrowhood-staging`, +others.
- `kc-pos-realm-dev` users (12): aleena, andy, angel, felix, frank, leandra, leanna, michael,
  pam, pos-auditor, pos-developer, ralph. Roles carry emoji (`💰️ pos-cashier`, `👔️ pos-manager`,
  `👑️ pos-admin`, `📊️ pos-auditor`, `🛠️ pos-developer`) — clone copies them as-is.
- All three Banco containers currently resolve `POS_REALM=kc-pos-realm-dev` (the default; no
  per-container override yet — that's the one knob we add).

## Build list (on Angel's go)

1. `scripts/clone_pos_realm.py` — Typer: partial-export `-dev` → retarget id + redirects →
   create realm. (`--src`, `--dst`, `--host` for redirect trim, `--dry-run`.)
2. Run Phase 1 (staging) end-to-end; green-light on a real inbox.
3. Run Phase 2 (prod) at a quiet moment; re-provision staff; smoke.
4. Persist `POS_REALM` in the staging/prod compose files so a redeploy keeps the realm.

*Net: dev/sbx unchanged on MailHog; staging + prod each get their own realm on Resend; real
hires get real mail; rollback is one env var. No app code changes.*
