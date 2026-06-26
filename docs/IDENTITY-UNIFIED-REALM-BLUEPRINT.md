# Unified realm blueprint — what ONE environment realm must contain

*Written 2026-06-26 from a read-only audit of the box KC (clients + roles of every fold-in realm).
This is the Phase-2 spec: build this once per env realm (`kc-sandbox` → `kc-staging` → `kc-production`),
then repoint each app's `*_REALM` at it. See [[IDENTITY-CONSOLIDATION-PLAN]] + IDENTITY-THREE-REALMS-LEGO.md.*

---

## Clients (apps as clients) — the union, KC built-ins omitted

Built-ins every realm already has (leave alone): `account`, `account-console`, `admin-cli`,
`broker`, `realm-management`, `security-admin-console`.

| Client | App / surface | From realm(s) | Notes |
|---|---|---|---|
| `lapiazza_web` | La Piazza / Bottega (public web) | lapiazza-realm-dev, borrowhood | public client |
| `borrowhood-web` | Marketplace web | borrowhood | public |
| `borrowhood-api` | Marketplace API | borrowhood | bearer/api |
| `lapiazza_publisher` | Artemis Premium publisher (server token-exchange) | borrowhood | **confidential** (secret per env) |
| `helix_pos_web` | Banco POS web | kc-pos-realm-dev | public |
| `helix_pos_mobile` | Banco POS mobile | kc-pos-realm-dev | public |
| `helix_pos_service` | Banco POS service | kc-pos-realm-dev | bearer/api |
| `camper_service_web` | Garage (Camper & Tour) web | kc-camper-service-realm-dev | public |
| `camper_service_api` | Garage API | kc-camper-service-realm-dev | bearer/api |
| `isotto_print_web` | Print shop web | kc-isotto-print-realm-dev | public |
| `isotto_print_mobile` | Print shop mobile | kc-isotto-print-realm-dev | public |
| `isotto_print_api` | Print shop API | kc-isotto-print-realm-dev | bearer/api |
| `helix_account` / `helix_service_account` / `helix_user` | Core platform | kc-realm-dev | platform |

**Dropped:** `artemis_pos` (the `artemis` realm's POS client) — redundant; Felix's shop uses
`helix_pos_web` + the `shop:artemis` group. The `artemis` realm collapses entirely (see Groups).

## Roles — TWO layers (this is ID6 made concrete)

**Layer 1 — cross-app TIERS (realm roles, the workforce-vs-public split that replaces the 6-realm wall):**
| Tier | Side | Who | Self-grant? |
|---|---|---|---|
| `member` | public | individuals (default for self-registration) | yes (default role) |
| `business` | public | shops that sell (has VAT) — was `lapiazza-business` | on verification |
| `staff` | workforce | anyone who operates an app | **admin-granted only** |
| `admin` | workforce | elevated operators / platform admins | **admin-granted only** |

These drive: self-reg default (`member`), conditional MFA (on `staff`/`admin`), and the
security posture we'd otherwise have split realms for. Public users simply never hold `pos-*` etc.

**Layer 2 — per-app CLIENT roles (existing, carried over verbatim, namespaced by app):**
- **POS** (`helix_pos_web`): `pos-cashier`, `pos-manager`, `pos-admin`, `pos-auditor`, `pos-developer`
  *(emoji prefixes today — normalize to plain names during the fold)*
- **Garage** (`camper_service_web`): `camper-counter`, `camper-mechanic`, `camper-manager`,
  `camper-admin`, `camper-auditor`, `camper-accountant`, `camper-hr`, `camper-qa-tester`
- **Print** (`isotto_print_web`): `isotto-counter`, `isotto-operator`, `isotto-designer`,
  `isotto-manager`, `isotto-admin`
- **La Piazza/Bottega** (`lapiazza_web`): `lapiazza-user`, `lapiazza-admin`, `lapiazza-business`
- **Marketplace** (`borrowhood-*`): `bh-member`, `bh-lender`, `bh-operator`, `bh-moderator`,
  `bh-admin`, `bh-qa-tester`
- **Platform** (`helix_*`): `developer`, `guest`, `admin`, `auditor`

## Groups (tenants / shops)

| Group | Is | Members hold |
|---|---|---|
| `shop:artemis` | Felix's head shop (was the `artemis` realm) | `business` + `pos-*` workforce roles |
| *(future)* `garage:trapani`, `shop:isotto`, … | each new business | its workforce roles |

## Gaps & cleanups this audit surfaced

1. **🔴 prod `borrowhood` is MISSING `lapiazza-business`** (staging has it) → **Artemis Premium can't
   publish-as-business on prod until added.** Add it as part of the prod fold (Phase 2-prod), or
   sooner as a standalone unblock.
2. **`artemis` realm duplicates `pos-cashier/manager/admin`** → collapses into `shop:artemis` group +
   the unified `pos-*` client roles. No separate artemis identity.
3. **`lapiazza-realm-staging` (162)** = superseded old staging, mostly test accounts (`art-*`,
   `cara-cardseed`). NOT the staging target. Backup → delete (after a glance for any real account).
   The live staging realm is **`borrowhood-staging` (20 users — our "140" was wrong)** → becomes `kc-staging`.
4. **Emoji role names** (`💰️ pos-cashier`, `👑 admin`…) — **DECISION 2026-06-26 (Angel): drop emoji
   everywhere in the identity config; plain ASCII role names long-term.** Safe to do: `require_roles`
   (`keycloak_auth.py:227`) substring-matches both ways, so a plain KC role `pos-cashier` satisfies
   app checks written as either `pos-cashier` OR `💰️ pos-cashier` — existing checks keep working
   against plain roles. ⚠ One synced cleanup required: `admin_router.py` hardcodes the emoji role
   *catalog* for create/assign (lines ~133–265) — update to plain names **when its target realm is
   plain** (i.e. with the cutover, not before — prod KC still has emoji roles until renamed).
5. **`default-roles-borrowhood` appears inside `borrowhood-staging`** (stray, alongside its own
   `default-roles-borrowhood-staging`) — verify/clean during the staging fold.

## Build order (Phase 2, per env, sandbox first)

1. Create the env realm (sandbox: new `kc-sandbox`; staging/prod: the existing realm, renamed later).
2. Add the clients above (redirect URIs scoped to that env's hosts).
3. Create Layer-1 tier roles + Layer-2 client roles; set `member` as the realm default role.
4. Create groups (`shop:artemis`); map members → tier + client roles.
5. Repoint each app's `*_REALM` env → this realm; restart; smoke (login + core flow per app).
6. **Acceptance:** one person (e.g. Pam) logs in once and is a `pos-cashier` in Banco AND a
   `member` in Bottega — one account, two hats. Then retire the old per-app realms.
</content>
