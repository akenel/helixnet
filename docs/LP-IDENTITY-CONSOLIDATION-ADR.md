# La Piazza Identity Consolidation — Decision + Runbook

**Status:** APPROVED (Option A), staging not yet executed
**Date:** 2026-06-18
**Owner:** Angel + Tig
**Blast radius:** HIGH (touches login for live apps) — staging-proven before any prod change.

> Goal in one line: **one Keycloak realm is the single user store ("CUA") for the whole
> app family; each app is a client of it; a user logs in once and crosses every app with
> no barrier.** Phase 1 = Bottega + BorrowHood only.

---

## The SAP mapping (the mental model)

| SAP concept | Meaning | Keycloak mechanism |
|---|---|---|
| **CUA** (Central User Admin) | one system owns users + roles | **one realm** = the canonical user store |
| **SSO** | log in once, move across modules | all apps are **clients** of that realm |
| **Principal propagation** | carry the *user's* identity to the backend | **token exchange** (or direct token reuse — same realm) |
| **Technical / RFC user** | system-to-system, no human | **service account** (client-credentials) |
| (no SAP term) | first visit auto-creates local record | **JIT provisioning** |

---

## The decision: Option A — `borrowhood` is the canonical realm (CUA)

**Why borrowhood and not lapiazza (reversing the prior BL-014 attempt):**

1. **Real prod users live in `borrowhood`** (Corrado, Diego, Flora + the demo set). Option A
   never moves them.
2. **BorrowHood keys users by Keycloak `sub`** (`bh_user.keycloak_id`). Moving BorrowHood
   users changes their `sub` and breaks every relation → needs `lp_remap_sql.py` surgery.
   **The Bottega keys by `username`** — it travels between realms for free.
   ⇒ Move the cheap app (Bottega), never the fragile one (BorrowHood). Option A does exactly that.
3. The realm **name stays `borrowhood`** — by decision. "A neighborhood of borrowing." No rename.

**Superseded:** `scripts/lp_merge_staging.py` (BL-014) unified onto `lapiazza-realm-staging`
(Option B, the fragile direction). We flip direction; the helper *tooling* is reused.

---

## LIVE STATE — preflight on the box (2026-06-18, read-only kcadm)

One Keycloak on Hetzner `46.62.138.218`, **v24.0.4** (token-exchange GA). Live realm/client/user reality:

| Realm | Users | Clients (app) | Meaning |
|---|---|---|---|
| `borrowhood` | **262** | borrowhood-web, borrowhood-api | **PROD marketplace** — all real + demo users. NO lapiazza_web. |
| `lapiazza-realm-dev` | **7** | lapiazza_web | **PROD Bottega** — tiny (demo + angel). |
| `lapiazza-realm-staging` | **162** | **borrowhood-web + lapiazza_web** | **STAGING — already consolidated (Option B!)**. Both staging apps point here. |
| `borrowhood-staging` | 17 | borrowhood-web, borrowhood-api | **Orphaned** — no app points here anymore. NO lapiazza_web. |

Leftover/unused realms also present: `artemis`, `blowup`, `fourtwenty`, `kc-realm-dev`,
`kc-camper-service-realm-dev`, `kc-pos-realm-dev`, `kc-isotto-print-realm-dev` (cleanup, later).

**Two facts that change the plan:**
1. **Staging is already consolidated — onto `lapiazza-realm-staging` (Option B, the direction we’re reversing).** Both `helix-platform-staging` and `borrowhood_staging` authenticate there. So staging does NOT mirror the intended Option-A prod end-state → a parity gap to resolve.
2. **The prod Option-A operation is tiny:** move **7** Bottega users into `borrowhood`; the **262** marketplace users (incl. real Corrado/Diego/Flora) never move. (Option B would move 262 + remap 262 `bh_user.keycloak_id` — confirming Option A is the low-risk direction by a wide margin.)

- The ~315 "Legends" (da Vinci etc.) are **DB-only `bh_user` rows, NOT Keycloak accounts** — never seeded.
- **Role gate:** Bottega requires realm roles `lapiazza-user`/`lapiazza-admin`
  (`src/routes/bottega_router.py:46`); BorrowHood requires `bh-*`. Bottega validates tokens
  with `verify_aud: False` (`src/core/keycloak_auth.py:129`) — audience won't block cross-client.

---

## Phase 1 end-state (Bottega + BorrowHood on `borrowhood`)

1. `borrowhood` realm gains a **`lapiazza_web`** client (Bottega's redirect URIs:
   `https://bottega.lapiazza.app/*`, `https://staging-bottega.lapiazza.app/*`, localhost).
2. Bottega points `LP_REALM` → `borrowhood` (staging twin first: `borrowhood-staging`).
3. Every loginable user carries **both** role sets (`lapiazza-user` + `bh-member`).
4. New Bottega signups (`get_started`) create users **in `borrowhood`** → one signup, both apps.
5. Cross-app write (Cleo drafts → BorrowHood listing): same realm ⇒ the user's token is
   accepted directly (verify_aud off); token-exchange held in reserve if a stricter audience
   check is added later.
6. JIT provisioning: first visit to each app builds its local row from the token.

Later phases absorb Camper & Tour, POS, eyesight as additional clients — same pattern.

---

## Runbook — STAGING REHEARSAL FIRST (no prod identity touched)

> Canonical staging realm = **`borrowhood-staging`** (the safe twin of prod `borrowhood`).

**Preflight (DONE 2026-06-18 — see LIVE STATE table):**
- [x] Staging reality: BOTH staging apps already share `lapiazza-realm-staging` (Option B,
      162 users). `borrowhood-staging` (17 users) is orphaned. So staging is consolidated the
      WRONG way vs our Option-A prod target → a realignment decision is needed (below).
- [x] Prod reality: `borrowhood` (262) + `lapiazza-realm-dev` (7), split. Option-A op = move 7.

**OPEN FORK — how to make staging rehearse Option A (Angel to decide):**
- **Path 1 (clean parity, more churn now):** rebuild the orphaned `borrowhood-staging` as the
  canonical staging realm — add `lapiazza_web` + roles, repoint BOTH staging apps there, re-seed
  demo users. Staging then mirrors prod exactly (borrowhood = the one realm). Cost: repoint the
  staging marketplace + likely re-remap its `bh_user.keycloak_id` (17 rows, safe).
- **Path 2 (least churn):** leave staging on `lapiazza-realm-staging` (it already proves SSO +
  the bridge work — both clients present). Rehearse only the prod-specific delta (adding
  `lapiazza_web` to a `borrowhood` realm) on `borrowhood-staging` in isolation. Accept that
  staging's canonical realm NAME won't match prod's (the parity gap Angel dislikes).

**STATUS 2026-06-18 — Path 1 chosen + EXECUTED on staging (✅ token-proven):**
`borrowhood-staging` made a twin of the proven realm (added `lapiazza_web` client + `lapiazza-user`/
`lapiazza-admin` roles, granted `lapiazza-user` to all 17 users, aligned `frontendUrl`). Repointed
BOTH staging apps (`LP_REALM` + `BH_KC_REALM` → `borrowhood-staging`, file backups `.bak-20260618`,
realm snapshots in `/root/kc-backup-20260618`). Verified: mike's token from the unified realm carries
`bh-member,bh-lender,lapiazza-user`, issuer `…/realms/borrowhood-staging`, both containers healthy.
REMAINING: browser SSO proof (mike on staging-bottega → staging.lapiazza.app, marketplace self-relinks
by username) + the draft-listing bridge; THEN the prod window (move the 7 Bottega users onto `borrowhood`).

**Execute on staging:**
1. [ ] Add `lapiazza_web` client + `lapiazza-user`/`lapiazza-admin` roles to `borrowhood-staging`
       (reuse `lp_create_realm.py` logic / admin API; idempotent).
2. [ ] Grant `lapiazza-user` to all existing `borrowhood-staging` users; grant `bh-member`
       to any Bottega-only demo users (`lp_seed_demo_users.py` for the demo set).
3. [ ] Repoint Bottega-staging `LP_REALM=borrowhood-staging`, redeploy the staging container.
4. [ ] **Prove SSO:** log in as `mike` on staging-bottega → confirm same `mike` on
       staging marketplace (same `sub`, same account).
5. [ ] **Prove the bridge:** Cleo drafts a listing → write it as `mike` into the staging
       marketplace as a **DRAFT** listing → `mike` sees it waiting. (Verify via browser, not
       just the bearer script — cookie-session caveat.)
6. [ ] Smoke + console-sweep both apps on staging. Every login path green.

**Only then — prod (separate, gated, reversible window):**
7. [ ] Export prod `borrowhood` realm JSON (rollback artifact).
8. [ ] Add `lapiazza_web` client + `lapiazza-*` roles to prod `borrowhood`; grant roles.
9. [ ] Repoint prod Bottega `LP_REALM=borrowhood`; redeploy ONLY the Bottega container.
10. [ ] Verify a real user (or `angel`) logs into BOTH apps; verify existing BorrowHood
        logins (Corrado/Diego/Flora) **still work** — they must be untouched.
11. [ ] Roll back = repoint `LP_REALM` to `lapiazza-realm-dev` + redeploy (client/roles added
        are additive and harmless).

---

## Guardrails (the seal lesson)

- A realm change can break **every** app's login at once. Staging-proven, never rushed.
- Real prod users are **read-only** until staging is fully green.
- Each prod step is **additive + reversible**; the rollback is one env flip + redeploy.
- Do NOT migrate the 315 DB personas — they were never accounts.

---

## Open items to confirm with Angel before prod

- Phase-1 scope = Bottega + BorrowHood only (Camper/POS/eyesight later). [pending confirm]
- Real prod users untouched until staging green. [pending confirm]
- Reconcile `borrowhood.env` realm name discrepancy (committed `borrowhood` vs template `borrowhood-staging`).
