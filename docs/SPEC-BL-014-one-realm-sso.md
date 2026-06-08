# SPEC · BL-014 — One-Realm SSO (the keystone)

> **Goal:** log in once, be the same person everywhere — the Square (`lapiazza.app`), the
> Workshop (`bottega.lapiazza.app`), and any future lab. SSO is the *payoff*; **one realm**
> is the *mechanism*. NOT federation (federation = two realms brokering = account-linking,
> extra prompts, double-account risk, more to maintain — a worse SSO).

**Status:** spec — **DEFERRED until the pain is real. Do NOT build now.** (See "When / don't" below.)

> ## ⚠️ When to do this — and what to do instead now (BHT, 2026-06-07)
> **Don't migrate live prod users for a pain nobody's feeling yet.** SSO only matters for the
> *customer-facing* Square↔Workshop being one product — and today almost no one bounces between
> the two faces, so the "log in twice / two accounts" pain isn't being felt. Migrating real
> marketplace users between realms is genuine risk; doing it now is gold-plating an unused door.
>
> **Two different problems, two different tools:**
> - **Integrations** (WhatsApp, Telegram, Ollama, Stripe) and **admin tools** (Portainer, Grafana)
>   → **API keys / their own logins. Fine. No SSO.** (You already have these.)
> - **The near-term data bridge** (Legends picker reading marketplace personas, `/u/` unified view)
>   → a **service API key between Bottega ↔ Square** (machine-to-machine). **No user migration, no
>   SSO.** This is the right "now" move. Build it with Legends-1.
> - **True human SSO** (one login, both faces) → THIS spec. Pull it off the shelf only when people
>   actually flow between Square and Workshop and hit the double-login wall.
>
> **Trigger to revisit:** real members bouncing Square↔Workshop + complaining they're two accounts
> / must log in twice. Until then: API-key bridge, and leave the realms alone.

---

## Long-term goal + design-for-it-NOW (so the migration is a piece of cake)
We don't migrate today — but we spell out the destination now and obey 7 cheap rules so the
eventual switch is trivial with Keycloak, never a rewrite:

1. **Realm = environment, Client = module, Role = access.** A NEW module/lab is a **client in the
   `lapiazza-realm-{env}` realm — NEVER a new realm.** Stops the split from widening, today.
2. **One Keycloak server.** Already true (`keycloak.helix.local`). Never spin a second KC.
3. **IdPs live on the REALM** (Google/GitHub/Facebook), not per app → every client inherits, and the
   unified realm is born ready. (This is the Door block — do it at realm level per env.)
4. **Stable join keys, preserved forever.** Each app keys user data on something that survives a
   realm move: Bottega = `username`, Square = `keycloak_id` (sub). Keep both **stable**; never mint
   per-app user ids that can't map back to a KC identity.
5. **Email is the human anchor.** Every user gets a **verified email** — it's the merge key for any
   future consolidation. Make email-verified the norm now.
6. **The realm pointer is config, not code.** Both apps already read realm/client from config
   (`BorrowHood/src/config.py`, `settings.LP_REALM`). Keep it that way → migration = change one line + import users.
7. **Cross-app reads use a service API key (now), not shared sessions.** The data bridge (Legends,
   cross-profile) is machine-to-machine today; don't fake-couple via sessions before the realm is one.

Obey these and the eventual migration is literally: build the `square` client in the unified realm,
import users preserving `id`+`username`+hashes, repoint one config line, smoke-test, keep the old
realm as rollback. **A piece of cake — because we spelled it out now.**

## What SSO unlocks (why this is the keystone)
One realm simultaneously fixes five things we've hit:
1. **SSO** — Keycloak's session cookie silently re-auths you across every *client* in the realm, across subdomains (both apps bounce to the same KC).
2. `lapiazza.app/u/<slug>` → "user not found" disappears (one identity space).
3. **Legends picker** data bridge (one user space to read).
4. **Profile edit in one place** (no Bottega-vs-Square duplication).
5. One **300-credit grant** + one **points/token balance** for the reward engine.

---

## The grounded facts (verified 2026-06-07)
| Fact | Value | Consequence |
|---|---|---|
| Keycloak server | **ONE** — both apps use `keycloak.helix.local` | Realm consolidation, not a KC merge ✅ |
| Square realm/client | realm `borrowhood`, client `borrowhood-web` (`BorrowHood/src/config.py`) | repoint to the unified realm |
| Workshop realm/client | realm `lapiazza-realm-{env}`, client `lapiazza_web` | already there; becomes a client in the unified realm |
| Square identity join | `bh_user.keycloak_id` (KC sub/UUID) + `email` | **must preserve KC user id on import** |
| Workshop identity join | `bottega_profiles.username` | **must preserve username on import** |
| App DBs | separate (`helix_db`, `borrowhood`) | stay separate — unify identity, not data |

**Migration rule that falls out:** preserve **both** the KC user id (sub) **and** the username
on every imported user → both apps' existing data joins survive untouched. No FK remap, no
data migration — just identity consolidation.

---

## Target model
- **Realm = environment:** `lapiazza-realm-dev` · `lapiazza-realm-staging` · `lapiazza-realm-prod`. (3, forever.)
- **Client = module:** `bottega` (helix-platform), `square` (the marketplace, was `borrowhood-web`), future labs. Each: own client-id, own redirect URIs, own secret. Keep existing client-ids as aliases to avoid app rewrites if cheaper.
- **Roles = access:** `lapiazza-user` (everyone), `lapiazza-admin`; add `square-*` / `bottega-*` only if a real boundary needs it.
- **IdPs configured ONCE on the realm** (Google/GitHub/Facebook) → every client inherits. *(This absorbs the Door block — do IdPs at the realm level, per env.)*
- **frontendUrl** pinned per host where needed (gotcha #3) so OIDC discovery returns the right host for each subdomain.

---

## Migration approach (the careful part)
Keycloak's user export/import **carries credential hashes and federated-identity links**, so
passwords and Google logins keep working across the move. Plan:

1. **Build the unified realm** (extend the existing `lapiazza-realm-{env}`): add the `square`
   client + all redirect URIs (lapiazza.app, staging.lapiazza.app, bottega.lapiazza.app,
   staging-bottega, localhost), add realm IdPs, roles.
2. **Import the `borrowhood` users** into it, **preserving `id` (sub) and `username`** + credential
   hashes + federated links. The ~315 personas + real members come in clean (they exist only in `borrowhood`).
3. **Resolve dual-realm users** (people who exist in BOTH realms today — likely just `angel` +
   test users): merge by **email**. Decide which sub survives; if `bh_user.keycloak_id` must stay
   valid, keep the borrowhood sub for that user and repoint the (few) Bottega rows by username.
   *Small, bounded set — handle by hand/script, not a generic merge engine.*
4. **Repoint the Square app** (`BorrowHood/src/config.py`): `kc_realm` → `lapiazza-realm-{env}`,
   `kc_client_id` → `square` (or keep `borrowhood-web` as the client-id to avoid churn).
5. **Bottega** already on the realm — just ensure its client + redirect URIs coexist.

---

## Recon 2026-06-08 — READY TO EXECUTE (no architectural blockers)
- **Marketplace source is on the box:** `/opt/helixnet/BorrowHood` (compose build context `../BorrowHood`). Rebuildable: `docker compose -f docker-compose.uat.yml -f docker-compose.staging.yml build borrowhood_staging`.
- **Realm is config-driven (env):** `BH_KC_REALM` / `BH_KC_CLIENT_ID` / `BH_KC_CLIENT_SECRET`. Repoint = change env + recreate. (staging today: `BH_KC_REALM=borrowhood-staging`, client `borrowhood-web` confidential w/ secret.)
- **⚠️ PREREQUISITE:** `borrowhood_staging` is currently **unhealthy** (Up 2d). Fix that FIRST — do not migrate onto a broken foundation.
- **Do NOT run tired.** This moves real logins; the prod cutover touches ~315 live `lapiazza.app` users. Execute rested, top-of-session, rollback-ready.

**Wake-up-and-execute order (staging first, prod gated):**
1. Fix `borrowhood_staging` health (whatever's red) so the baseline is green.
2. Add the `borrowhood-web` client to `lapiazza-realm-staging` (confidential, secret, staging.lapiazza.app redirect URIs).
3. Import `borrowhood-staging` users into `lapiazza-realm-staging` (KC partial export/import; preserve `id`+`username`+credential hashes+federated links). Only ~11 users on staging = low risk.
4. Flip `borrowhood_staging` env `BH_KC_REALM` -> `lapiazza-realm-staging` (+ the new client secret); recreate.
5. **Test SSO:** log into staging Bottega -> land authed on staging Square (same realm session); both `/u/<slug>` resolve; `bh_user.keycloak_id` still joins. Human-green.
6. ONLY THEN, rested + signed off: repeat on prod (`borrowhood` -> `lapiazza-realm-dev`), keep the old realm hot as rollback.

## Phased runbook (dev → staging → prod, with rollback)
**Phase 0 — Audit (before touching anything):**
- Count prod `borrowhood` users; list dual-realm collisions by email; confirm `bh_user.keycloak_id`
  is the only KC-linked column (any other FK to a sub?); confirm IdP config exportable.

**Phase 1 — DEV:** build unified `lapiazza-realm-dev` (square client + IdPs + roles); import local
borrowhood users (only 11 locally) preserving id+username; repoint local Square; test:
- existing user login, Google login, new signup, **SSO across Square↔Workshop** (log into one, land in the other already authed), `bh_user` data still resolves, `/u/<slug>` resolves both sides.

**Phase 2 — STAGING:** same on `lapiazza-realm-staging` + `borrowhood_staging`. Run smoke +
console-sweep + the SSO click-through. **Human-green (Angel).**

**Phase 3 — PROD:** import prod `borrowhood` users into `lapiazza-realm-prod` (preserve id+username),
repoint prod Square, smoke-test via public hostnames. **Keep the old `borrowhood` realm intact**
as the rollback (repoint back if login breaks). Decommission only after a clean soak.

---

## Risks → mitigations
| Risk | Mitigation |
|---|---|
| Passwords/Google break on move | KC export/import preserves credential hashes + federated links; verify on staging with a real account first |
| `bh_user.keycloak_id` orphaned (sub changed) | Preserve sub on import; for merged dual-realm users, keep the borrowhood sub + repoint the few Bottega rows |
| Username/email collisions | Merge by email; suffix only true distinct collisions; bounded set, scripted |
| Redirect-uri / frontendUrl misconfig | All hosts in the client; pin frontendUrl per host (gotcha #3); test discovery per subdomain |
| Prod login downtime | Phased; old realm kept as live rollback; cut over off-peak |
| SSO cookie not shared across subdomains | Both apps redirect to the SAME KC — SSO session lives on the KC host, works across subdomains by design; verify in Phase 1 |

---

## Open decisions (lock before Phase 1)
1. **Client-ids:** rename `borrowhood-web` → `square` (clean) or keep the id (zero app churn)? *Lean: keep the id, alias later.*
2. **Dual-realm merge:** for users in both realms, which sub wins? *Lean: keep the borrowhood sub (more downstream FKs) + repoint Bottega's few rows by username.*
3. **Cutover window:** prod is live with real traffic — when? *Lean: low-traffic window, old realm hot as rollback.*
4. **Scope of v1:** SSO + shared identity only. Cross-module *features* (showing a Bottega storefront inside the Square, shared points balance) ride on top AFTER identity is one. Keep v1 to the realm.

---

## Sequence relative to other work
- The **Door** block (IdPs on every env) is **absorbed into Phase 1** — configure Google/GitHub/FB on the unified realm.
- The **Legends picker** and **unified profile edit** become trivial *after* this lands (one user space).
- This is the wheel that turns five others — but it touches **live prod marketplace users**, so it is a *gated, staged, rollback-ready* operation, not a quick block. Do it deliberately.

---
*Spec'd 2026-06-07. One realm. Log in once. Be the same you, everywhere. 🐺*
