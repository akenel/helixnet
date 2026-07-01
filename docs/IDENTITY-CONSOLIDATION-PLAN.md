# Identity consolidation — execution plan to 3 realms

*Written 2026-06-26. The "how we actually get there" for the locked model in
[`IDENTITY-THREE-REALMS-LEGO.md`](IDENTITY-THREE-REALMS-LEGO.md) /
[`HELIX-IDENTITY-ARCHITECTURE.md`](HELIX-IDENTITY-ARCHITECTURE.md) ID1–ID6. This is the
project board for the cleanup. Sequential, gated, rehearsed — touching live prod identity.*

---

## The target (locked)

**Three realms, one per environment. Clean env-only names:**

| Environment | Target realm id | Today's realm(s) | Users today |
|---|---|---|---|
| sandbox | **`kc-sandbox`** | `kc-pos-realm-dev` (shared w/ dev) | throwaway |
| staging | **`kc-staging`** | `borrowhood-staging` (140) + `kc-workforce-stg` (Banco) | ~140 |
| production | **`kc-production`** | `borrowhood` (305) | 305 |

Inside each realm: every app is a **client**, every person is **one account**, workforce-vs-public
is a **role tier** (`member`/`business` vs `staff`/`admin`), every shop is a **group**
(`shop:artemis`). No per-app realms, no per-population realms.

> **Naming decision — AUTHORIZED by Angel 2026-06-26 (supersedes ID3's "keep `borrowhood`"):**
> the prod realm **is** renamed `borrowhood → kc-production`, "gated and rehearsed." It is the
> **last, separately-gated step**, rehearsed on a throwaway realm + sandbox + staging first (see
> Phase 4). Until that cutover, prod keeps id `borrowhood` with a clean display name.
> **Pre-req proven before any real rename:** an in-place rename must preserve password hashes (else
> it's export/reimport = mass password reset; if so, STOP and reassess). Probed on local KC first.

---

## 2026-07-01 — progress refresh + the account-handover pattern

**What moved since 2026-06-26 (verified live):**
- ✅ **`kc-sandbox` now EXISTS** and sandbox Banco uses it (`POS_REALM=kc-sandbox`, 3 users). Sandbox is
  already on the clean name — one env done.
- Prod Banco is now on **`borrowhood`** (`POS_REALM=borrowhood`) and staging on **`borrowhood-staging`**
  — those two env-community realms are the live Banco realms today. **Counts now:** `borrowhood`
  **365** (bot-heavy — old public signups, random usernames + gmail-dot-trick emails),
  `borrowhood-staging` **21**, `kc-sandbox` **3**.
- **SMTP wired 2026-07-01** on all three (MailHog sandbox / Resend staging+prod) — KC email
  (verify/reset) works now. Detail: memory `banco-kc-smtp-resend`.
- **`helix_pass` rotated** off the real accounts (felix/akenel/angel/pam/ralph) on `borrowhood` +
  `borrowhood-staging`. Sandbox stays open by design. Detail: memory `banco-shared-password-cleanup`.

**Finish line unchanged, just clearer:** build **`kc-staging`** + **`kc-production`** (the two names that
never got made), fold Banco POS in as a client, migrate the *real* staff accounts, then retire
`borrowhood`/`borrowhood-staging` after auditing their users (`borrowhood` is mostly bots → most get
**deleted, not migrated**).

### Account-handover pattern (decided 2026-07-01) — how a real owner takes over
When a real shop-owner (e.g. the real Felix) comes on, do NOT create-from-scratch, and do NOT hand over
your only admin. Instead:
1. **One account per person.** Felix gets his OWN owner account; Angel keeps a **steward/admin** account
   in the same realm so he can still support/rescue the shop. Never hand over the sole admin.
2. **Born in the clean realm.** The real account lives in **`kc-production`** (clean), not the
   `borrowhood` swamp. Today's role-play `felix` (borrowhood) is the **template**, not the keys handed over.
3. **Self-set password, zero sharing.** Set the account's email to the person's real address → fire
   Keycloak's `UPDATE_PASSWORD` action email → they click and set their OWN password. Neither party ever
   knows the other's. (Same mechanism as forgot-password.)
4. **No `helix_pass` on real accounts, ever.** Strong per-user passwords only.

> Angel's framing (2026-07-01): *"I don't make a new Felix — I hand him this one, swap to his email, he
> sets his password."* Right mechanism — just do it in `kc-production`, with **him getting his account
> and you keeping yours.**

---

## Current reality (verified 2026-06-26 — code + infra sweep)

**Realm wiring:**
- `config.py:57` `POS_REALM` default `kc-pos-realm-dev`; `config.py:46` `LP_REALM` default `lapiazza-realm-dev`.
- staging Banco → `kc-workforce-stg` (renamed in place from `kc-pos-realm-stg`; box-only).
- **prod Banco → `kc-pos-realm-dev`** (no override in `docker-compose.banco-prod.yml` → uses the dev default). Phase-2-prod never ran; there is no `kc-pos-realm-prd`/`kc-workforce-prd`.
- Local KC untouched: 8 realms, no `kc-workforce-*`.

**The good seam:** `keycloak_auth.py` reads the realm from each token's `iss` and fetches per-realm
JWKS dynamically (falls back to `POS_REALM`). → the app already validates tokens from *any* realm,
so during migration old + new realms coexist. This is what makes the fold low-risk.

**Hardcoded realm strings to fix (NOT env-driven):**
| File | Realm pinned |
|---|---|
| `src/routes/camper_router.py:3925`, `backlog_router.py:435`, `qa_router.py:556` | `kc-camper-service-realm-dev` |
| `src/templates/camper/{login,base}.html`, `backlog/{login,base}.html`, `testing/{login,base}.html` | `kc-camper-service-realm-dev` (JS const) |
| `src/routes/isotto_router.py:1297`, `src/templates/isotto/{login,base}.html` | `kc-isotto-print-realm-dev` |

**Already env-driven (low risk):** POS (`settings.POS_REALM`), La Piazza/Bottega (`settings.LP_REALM`),
all JWT extraction, master bootstrap (`"master"`, correct). Guard `bottega_router.py:280`
`if LP_REALM == "borrowhood"` — update the literal when prod is renamed.

**🔴 Found during the sweep (separate prod bug, fix independently):**
`docker-compose.banco-prod.yml` sets `LP_REALM=borrowhood-staging` + `staging-bottega.lapiazza.app`
→ prod Banco may publish to the **staging** marketplace. Verify vs live container, then fix.

**⚠ To investigate before deleting anything:** `lapiazza-realm-staging` holds **162 real users** on
the box (not the empty local one). Audit before disposition.

---

## Box realm reconciliation — CONFIRMED 2026-06-26 (read-only `list-realms`)

The box KC holds **13 realms**. The staging rename happened and went exactly one realm deep —
**no stray `kc-community-*`/`kc-workforce-sbx/prd`**; the 6-realm detour is contained.

| Box realm | Role today | Verdict → 3-realm model |
|---|---|---|
| `borrowhood` (305) | PROD community | **rename → `kc-production`** (Phase 4); apps fold in as clients |
| `borrowhood-staging` (140) | STAGING community | **rename → `kc-staging`**; apps fold in |
| `kc-workforce-stg` | STAGING Banco (the rename) | fold into `kc-staging` as `helixpos` client → **DELETE** |
| `kc-pos-realm-dev` (~12) | dev+sandbox+**prod** Banco | split: sandbox→`kc-sandbox`, prod Banco→`kc-production`; retire |
| `artemis` (~4) | Felix's shop POC | → group `shop:artemis`; retire realm |
| `kc-camper-service-realm-dev` (~10) | Camper POC | → `garage` client; retire |
| `kc-isotto-print-realm-dev` (~5) | ISOTTO POC | → `isotto` client; retire |
| `lapiazza-realm-dev` (~7) | Bottega POC | → fold into env realm; retire |
| `kc-realm-dev` (~6) | HelixNet core POC | → `platform` client; retire |
| `lapiazza-realm-staging` (~162) | old LP staging | **⚠ INVESTIGATE** before disposition (likely superseded by borrowhood-staging) |
| `blowup`, `fourtwenty` | dead demos | **DELETE** (backup first — gated box deletes never done) |
| `master` (2) | KC admin | **KEEP, untouched** |

Must also **CREATE `kc-sandbox`** (no sandbox realm exists; sandbox borrows `kc-pos-realm-dev` today).
End state: `master` + `kc-sandbox` + `kc-staging` + `kc-production`.

## Guiding rules

1. **One environment at a time, throwaway first:** sandbox → staging → prod. Sandbox is the full rehearsal.
2. **Backup before every destructive step:** `kc_admin.py export-realm <r> --apply` (banks users + roles + clients).
3. **Additive then cutover then cleanup:** build the target realm fully (clients+roles+groups+users)
   *before* repointing any container; delete old realms only after the new one is green.
4. **One-env-var rollback** at every cutover (`POS_REALM`/`LP_REALM`/`*_REALM` back, restart).
5. **Prod is gated:** every prod step needs Angel's explicit go. Nothing outward-facing runs blind.
6. **Read-only first:** `kc_admin.py list-realms` against each KC before and after each phase.

---

## Phases

### Phase 0 — Confirm + freeze the picture (no changes)
- [ ] `list-realms` against the **box** KC → confirm exactly what the staging rename left (only
      `kc-workforce-stg`? any stray `kc-community-*`/`kc-workforce-*`?). *(needs Angel's read-only SSH.)*
- [ ] Verify the live `docker-compose.banco-prod.yml` `LP_REALM` against the running container (the prod-publish bug).
- [ ] Export-backup every realm slated to fold.

### Phase 1 — Make ALL app realms env-driven (code; zero infra risk)
Kill the 7 hardcodes so every app picks its realm from config, exactly like POS/La Piazza already do.
- [ ] Camper realm → config var (route + the 6 templates inject it like `pos_realm`).
- [ ] ISOTTO realm → config var (route + 2 templates).
- [ ] Decide the config shape: during transition each app keeps its own `*_REALM` knob; at end state
      they all default to the env realm. (A single `APP_REALM` per env is the destination.)
- [ ] `make test` green. Ship to staging behind unchanged realm values (no behaviour change yet).

### Phase 2 — Build the unified realm per env + fold the apps in
**✅ Engine built + sandbox realm LIVE (2026-06-26):** `scripts/build_unified_realm.py` (idempotent,
dry-run default) created **`kc-sandbox`** on the box with all 15 app clients + 4 tier roles
(`member`/`business`/`staff`/`admin`, member=default) + 30 plain app roles + `shop:artemis` group.
Idempotent verified (re-run = all `=`). Run pattern: `docker exec -e KC_ADMIN_PASSWORD=$(from kc
container) helix-platform-sandbox /app/venv/bin/python /tmp/build_unified_realm.py …`.
**✅ Proof passed (`scripts/proof_unified_realm.py`):** one account `pam` in `kc-sandbox` carries
`pos-cashier` (workforce) + `member` (public tier) — token issued, both roles present. **Fold
lesson:** migrated users need a complete profile (email + first/last name) or KC's Verify-Profile
required action blocks direct-grant login ("Account is not fully set up").
Per environment (sandbox first), in the env realm:
- [ ] Add clients: `lapiazza`, `bottega`, `helixpos`, `garage`, `isotto`, `platform` (+ `*-api` pairs).
- [ ] Add roles as client roles (`pos-*`, `camper-*`, `isotto-*`) + the cross-app tiers
      (`member`, `business`, `staff`, `admin`).
- [ ] Create groups for shops (`shop:artemis`, …); move users in, grant tier + client roles.
- [ ] Repoint each app's `*_REALM` → the env realm; restart; smoke (login + the app's core flow).
- [ ] **Sandbox:** re-seed fresh (throwaway) — proves the whole recipe end to end.
- [ ] **Staging:** fold Banco (`kc-workforce-stg`) + Bottega + camper + isotto into `borrowhood-staging`;
      prove **Pam = one account on both POS and Bottega**; then retire `kc-workforce-stg`.
- [ ] **Prod:** fold Banco (off `kc-pos-realm-dev`) + others into `borrowhood`. **Gated.**

### Phase 3 — Delete the dead realms (after backups + green)
Per env, remove the folded realms: `lapiazza-realm-dev`, `artemis` (→ group), `kc-realm-dev`,
`kc-camper-service-realm-dev`, `kc-isotto-print-realm-dev`, the Banco POS realms. Resolve the
`lapiazza-realm-staging` 162 users first.

### Phase 4 — The rename to clean names (LAST, rehearsed, gated) — AUTHORIZED
Only after each env runs on ONE realm. **Rename is AUTHORIZED** (Angel 2026-06-26).
- [x] **Rename method proven (local KC, 2026-06-26):** in-place rename = PUT realm rep with a changed
      `realm` field. **Preserves the password credential row untouched** (identical credential
      id+hash+createdDate before/after; old name → 404 = true rename, not a copy). Verdict: **no
      password reset** — users only re-login (the `iss` changes → sessions invalidate). Probe =
      `scratchpad/rename_probe.py` (credential-fingerprint method; login-flow can't be used on the
      customized local KC). ⚠ Re-confirm on the box during the sandbox/staging rehearsal.
- [ ] **The lockstep that MUST accompany each rename** (or logins break): every `helix_pos_web` /
      `lapiazza_web` / app client's **redirect URIs**; each app's `*_REALM` env (`POS_REALM`,
      `LP_REALM`, `CAMPER_REALM`, `ISOTTO_REALM`, `KEYCLOAK_REALM`); the realm **`frontendUrl`**;
      the `bottega_router.py:280` `if LP_REALM == "borrowhood"` literal; `LP_KC_PUBLIC_URL`.
- [ ] sandbox realm → `kc-sandbox`; update the above; re-login smoke. (throwaway = real rehearsal)
- [ ] **staging:** `borrowhood-staging` → `kc-staging` (rehearsal on 140 real users + the box).
- [ ] **prod:** `borrowhood` → `kc-production` — own quiet cutover window, full `export-realm --apply`
      backup first, the lockstep above applied, 305 users re-login. **Final explicit Angel go.**

---

## What's needed from Angel
1. **Run the read-only box `list-realms`** (Phase 0) — the one command from the prior message.
2. ✅ **Prod-realm rename AUTHORIZED 2026-06-26** ("yes rename prod to kc-production, gated and
   rehearsed"). Executed only at Phase 4, after the rename method is proven (password hashes
   survive) on a throwaway realm + sandbox + staging, with a full backup, at a quiet window.

*3 realms. One account per person. Hats, not walls. Clean the house once.*
</content>
