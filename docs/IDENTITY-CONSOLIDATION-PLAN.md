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

> **Naming decision (supersedes ID3's "keep `borrowhood`"):** Angel wants the clean `kc-<env>`
> names *done*, not deferred. So the prod realm **is** renamed `borrowhood → kc-production` — but as
> the **last, separately-gated step**, rehearsed on sandbox + staging first (see Phase 4). Until that
> cutover, prod keeps id `borrowhood` and just carries a clean display name.

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

### Phase 4 — The rename to clean names (LAST, rehearsed, gated)
Only after each env runs on ONE realm:
- [ ] **Prove the rename method on sandbox:** in-place rename via KC admin API (PUT realm `realm`
      field) — confirm it **preserves users + password hashes + sub**, only changing `iss`. If it
      loses passwords (i.e. it's really export/reimport), STOP and reassess prod.
- [ ] sandbox realm → `kc-sandbox`; update app config + redirect URIs; re-login smoke.
- [ ] **staging:** `borrowhood-staging` → `kc-staging` (rehearsal on 140 real users).
- [ ] **prod:** `borrowhood` → `kc-production` — own cutover window, full backup first, every client
      redirect + app `*_REALM` + the `bottega_router.py:280` literal updated, 305 users re-login.
      **Explicit Angel go.**

---

## What's needed from Angel
1. **Run the read-only box `list-realms`** (Phase 0) — the one command from the prior message.
2. **Authorize the prod-realm rename** as the final gated step (it touches 305 live logins —
   rehearsed on sandbox+staging first, full backup, re-login required). This is the one genuinely
   risky decision; the rest is reversible.

*3 realms. One account per person. Hats, not walls. Clean the house once.*
</content>
