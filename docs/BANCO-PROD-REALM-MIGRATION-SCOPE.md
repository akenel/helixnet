# Scope — moving Banco prod off `kc-pos-realm-dev` (cleanly)

**Date:** 2026-06-27 · **Status:** SCOPE ONLY (nothing executed) · **Author:** Tigs
**Trigger:** the realm name `kc-pos-realm-dev` is the *old* POS realm; sandbox already moved to
the new naming (`kc-sandbox`). Prod (Felix's live till) still authenticates against the old realm.

---

## 1. Ground truth (verified on the box, 2026-06-27)

**Which realms exist + what each Banco env logs into:**

| Env | Logs into | New-model name | State |
|---|---|---|---|
| sandbox-banco | `kc-sandbox` ✅ | `kc-sandbox` | migrated (fresh, unified blueprint) |
| staging-banco | `borrowhood-staging` | `kc-staging`? | old LP realm |
| **prod (banco)** | **`kc-pos-realm-dev`** | `kc-production`? | **old POS realm** |

`kc-production` and `kc-staging` **do not exist**. `kc-sandbox`, `kc-pos-realm-dev`, `borrowhood`,
`borrowhood-staging`, `artemis` do.

**Inside `kc-pos-realm-dev` (current prod realm):**
- **12 users:** felix, pam, frank, ralph, michael, andy, aleena, leandra, leanna, angel,
  pos-auditor, pos-developer. (Real operators ≈ felix/pam/frank; the rest look like test/demo.)
- **`helix_pos_web` client:** exists, public, standard flow; redirect URIs already include
  `https://banco.lapiazza.app/*` + `/pos/callback`. (That's why prod login works.)
- **Realm roles use EMOJI names:** `💰️ pos-cashier`, `👔️ pos-manager`, `👑️ pos-admin`,
  `📊️ pos-auditor`, `🛠️ pos-developer`.

**Inside `kc-sandbox` (the target shape):**
- 2 users (felix, pam). `helix_pos_web` exists. Roles are the **full unified blueprint** with
  **PLAIN names**: `pos-cashier`, `pos-manager`, `pos-admin` + `camper-*`, `isotto-*`,
  `lapiazza-*`, `platform-*`, `member`, `business`, `staff`, …

**Inside `borrowhood` (prod LP realm):**
- **200 users** (the live public marketplace). `helix_pos_web` is **MISSING**. Roles are `bh-*` /
  `lapiazza-*` only (no `pos-*`). **felix/pam/frank are NOT here.**

**banco_prod DB linkage (what a realm move would disturb):**
- `users.keycloak_id` is the cashier's KC sub: felix `729aec8c…`, pam `63b279e7…`, frank `4b5fc832…`.
  Transactions point at `users.id` (BL-83). A new realm = new subs ⇒ this linkage must be re-mapped
  or the cashier-identity resolver re-heals it (see §4).

---

## 2. The fork (this is the real decision)

There are **two conflicting north-stars** in the notes, and the tooling adds a third nuance:

- **ID6 "three realms"** → `kc-sandbox` / `kc-staging` / `kc-production` (fresh, consistent names).
- **LP consolidation (Option A)** → "unify onto the **borrowhood** realm, *name stays*."
- **`build_unified_realm.py`** (the engine that built kc-sandbox) targets, per its own header:
  `sandbox=kc-sandbox --create`, `staging=borrowhood-staging`, **`prod=borrowhood` (GATED)**.

So "move prod to kc-production" is **not** a settled, pre-decided step — it's one of three end-states.

| | **A. Fresh `kc-production`** | **B. Consolidate onto `borrowhood`** | **C. Defer (keep `kc-pos-realm-dev`)** |
|---|---|---|---|
| Naming | ✅ matches ID6, mirrors sandbox | ❌ stays "borrowhood" | ❌ stays "kc-pos-realm-dev" |
| "One account" (POS+LP) | ❌ separate (but felix isn't in borrowhood anyway) | ✅ the real unification | ❌ |
| Blast radius | low — new empty realm | **high — touches the live 200-user marketplace realm** | none |
| User migration | ~3–4 real users | ~3–4 real users INTO a busy realm | none |
| Effort / risk | medium | high | zero |
| Reversibility | easy (old realm untouched) | harder | n/a |

**Recommendation:** **A (fresh `kc-production`)** *if* we migrate — it matches your stated goal, mirrors
kc-sandbox exactly, and keeps the live `borrowhood` marketplace realm untouched. But be clear-eyed:
**the only benefit is naming consistency.** Prod login + logout already work. So the honest default is
**C (defer)** until there's a functional driver, then do A on a quiet morning. Do **not** do B just for
this — folding workforce into the 200-user public realm is a much bigger, riskier change that deserves
its own decision.

---

## 3. Migration playbook — Option A (`kc-production`), no lockout

Pre-req: pick a quiet window; Felix not mid-sale. Keep `kc-pos-realm-dev` **fully intact** the whole
time (it's the rollback).

1. **Build the realm (mirror sandbox), idempotent dry-run first:**
   `python scripts/build_unified_realm.py kc-production --create --base-domain banco.lapiazza.app`
   (review) → re-run with `--apply`. Lays `helix_pos_web` + plain `pos-*`/tier roles + groups.
2. **Client URIs:** confirm `helix_pos_web` in kc-production has redirect `https://banco.lapiazza.app/*`
   + `/pos/callback` AND a **post-logout redirect URI** for `https://banco.lapiazza.app/pos`
   (kc-pos-realm-dev's post-logout list is effectively empty — fix it here so logout is clean).
3. **Provision the REAL users only** (felix, pam, frank, + any real cashiers — skip the test
   accounts). Assign `pos-manager`/`pos-admin` to felix, `pos-cashier` to the rest. Passwords via the
   **self-set-password email flow** (needs **prod SMTP** configured — `configure_kc_smtp.py`) or set
   temporary ones. ⚠ Felix must be able to get in — verify his credential before cutover.
4. **⚠ App role-name compatibility (CODE) — the sharp edge:** prod `pos_router` (`3547efa`) enforces
   **emoji** role names (`require_roles(["💰️ pos-cashier", …])`). kc-production uses **plain**
   (`pos-cashier`). After cutover the role check would FAIL → cashiers can't ring. So the prod app
   must run a `pos_router` whose role checks match plain names (substring/normalized) — the same code
   sandbox already runs. **Verify how sandbox matches plain roles and bring that to prod with the
   cutover.** This is the step most likely to bite.
5. **Reconcile banco_prod identity:** after users exist in kc-production, capture each new sub and
   `UPDATE banco_prod.users SET keycloak_id = <new kc-production sub> WHERE username = …` so existing
   sales (cashier_id ↔ users) still resolve to the right person. The `_resolve_cashier_uid` resolver
   will also self-heal on first sale (resolves by keycloak_id, self-provisions) — but the explicit
   update preserves **historical** attribution and avoids duplicate cashier rows.
6. **Cutover:** set prod `POS_REALM=kc-production` (compose `environment:` block, like the current
   `kc-pos-realm-dev` line) → recreate `helix-platform-banco`. Token validation follows the token
   issuer, so it'll validate kc-production tokens automatically.
7. **Verify (live):** felix login → app shell → **ring one real sale to receipt** (proves the plain-
   role check) → My Day → drawer → **sign out**. Then pam (cashier) same.
8. **Rollback (instant):** revert `POS_REALM=kc-pos-realm-dev` + recreate. Nothing in the old realm was
   touched, so it's a clean fall-back.

---

## 4. Risks & gotchas (carry into execution)

- **Emoji→plain role names** — #1 risk (step 4). Without the matching app code, everyone is locked out
  of actions even though login works.
- **Sub change → cashier_id** — handled by the resolver + the explicit keycloak_id update (step 5),
  but verify no duplicate "felix"/"pam" rows appear after the first post-cutover sale.
- **Passwords / SMTP** — self-set-password needs **prod SMTP**; otherwise set temp passwords and hand
  them over. Don't cut over until Felix can actually log in to kc-production.
- **Post-logout URIs** — register them in kc-production (the current realm's were empty; we only got
  logout working by matching the login realm — kc-production should have proper post-logout URIs).
- **Staging too** — staging is on `borrowhood-staging`, not `kc-staging`. If the goal is consistent
  `kc-*` naming end-to-end, staging needs the same treatment. Decide whether this is a prod-only tidy
  or a full 3-env consolidation.
- **Test users** — don't migrate the 8 demo/test accounts; only real operators.
- **This is identity-lane work** — coordinate; it overlaps the gated realm-split Phase 2.

---

## 5. TL;DR for Angel

You're right that `kc-pos-realm-dev` is the odd one out. Moving prod to `kc-production` is **doable and
clean (Option A)**, but it's a real ~half-day migration whose **only payoff is naming** — login/logout
already work today. The trap to plan around is the **emoji-vs-plain role names** (prod app code must
match plain roles or cashiers get locked out of actions). If you want it, the safe path is: build
`kc-production` (mirror sandbox) → provision the few real users + verify Felix's login → bring the
plain-role app code → remap `banco_prod.users.keycloak_id` → flip `POS_REALM` → smoke a real sale →
keep the old realm as instant rollback. Otherwise, deferring is a legitimate, zero-risk choice.
