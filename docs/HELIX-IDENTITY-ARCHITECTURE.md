# HelixNet Identity Architecture — One Account, Many Modules (the North Star)

*Written 2026-06-24. The grand-vision identity model for the whole ecosystem + the cleanup roadmap
to get there. Supersedes the "realm = a shop" idea in `BANCO-REALM-MODEL.md` (see §3). Extends the
Phase-1 decision in `LP-IDENTITY-CONSOLIDATION-ADR.md` (Bottega → borrowhood) to the full house.*

> **Angel's framing (2026-06-24):** "three environments — sandbox/dev, staging, UAT/prod. These are
> just modules / apps that need users with the right roles. We already have that with Bottega and La
> Piazza — one account, SSO. Same thing for HelixPOS, the Garage / Camper & Tour app, and ISOTTO the
> virtual print house. Let's clean up Keycloak so we can do this properly."

---

## 1. The vision in one breath

**One person, one account, one login — that walks into any module they have a role in.**
Felix signs in once and he's: the **owner of Artemis** (his shop), a **pos-manager** behind the
till, a **verified business** on the public Square, and — if he ever rents a camper or orders prints
— a customer of the Garage and ISOTTO too. Same face, same `sub`, different rooms. The apps are
**modules**; Keycloak is the **front door** to all of them.

We already proved this works: Bottega + La Piazza share one realm and one login today. The grand
vision is just: **do that for everything, across three clean environments.**

---

## 2. The model — four nouns, and only four

The whole thing collapses to four Keycloak concepts. Get these straight and the sprawl disappears:

| Noun | = | There are… | Examples |
|------|---|-----------|----------|
| **Realm** | an **Environment** | exactly **3** | `dev`, `staging`, `prod` |
| **Client** | an **App / Module** | one per app | Square, Bottega, HelixPOS, Garage, Print House |
| **Role** | **what you can DO** in an app | per app | `pos-manager`, `isotto-designer`, `camper-mechanic`, `lapiazza-business` |
| **Group** | **who you BELONG to** (the tenant/shop) | one per shop | `shop:artemis`, `garage:trapani` |

**The mistakes the four-nouns model kills:**
- ❌ *"Realm = a shop"* → would mean a new realm per customer = no SSO, ops nightmare, 100 realms.
  ✅ A shop is a **Group**, not a realm. One realm holds all the shops.
- ❌ *"Realm = an app"* → that's why we have 11 realms today (a POS realm, a camper realm, an isotto
  realm…). ✅ An app is a **Client**. One realm holds all the apps.
- ✅ A **Realm is an Environment** — the boundary that actually matters is *whose data is this and is
  it safe to break*: dev (throwaway), staging (rehearsal), prod (real money, real people).

**One account carries everything.** Felix's token says: realm `prod`, groups `[shop:artemis]`,
roles `[pos-owner, pos-manager, lapiazza-business]`. The POS reads the `pos-*` roles; the Square
reads `lapiazza-business`; both trust the same `sub`. That's the SSO we already have — generalized.

---

## 3. Target end state

### Three realms (one per environment)
| Realm (technical id) | Environment | Login brand | Notes |
|---|---|---|---|
| `helix-dev` (consolidated) | dev / laptop | La Piazza | collapses the ~6 dev realms into one |
| `borrowhood-staging` | staging / UAT | La Piazza | already unified (Bottega + Square) ✅ |
| `borrowhood` | prod | La Piazza | **keep the id** — 262 users keyed by `sub`, can't move; rebrand the *theme* to La Piazza, rename the id only in a dedicated future sweep |

### One client per app/module (in every realm)
`lapiazza` (the Square) · `bottega` (Workshop) · `helixpos` (POS / Banco) · `garage`
(Camper & Tour) · `isotto` (Print House) · `platform` (core / OpenWebUI). Server-side pairs
(`*-api`) as needed.

### Roles stay where they are — just reclassified as client roles
The per-app namespacing already done makes this clean:
- **POS:** `pos-cashier`, `pos-manager`, `pos-developer`, `pos-auditor`, `pos-admin` (+ `pos-owner`)
- **Garage:** `camper-counter`, `camper-mechanic`, `camper-manager`, `camper-admin`, …
- **Print House:** `isotto-counter`, `isotto-designer`, `isotto-operator`, `isotto-manager`, …
- **Square/Workshop:** `bh-member`, `bh-lender`, `bh-moderator`, `lapiazza-business`, `lapiazza-admin`
- **Cross-app tiers (realm roles):** `member`, `business`, `staff`, `admin` — coarse identity level.

### Shops/tenants = Groups (not realms)
Felix's Artemis = `shop:artemis`. His staff are members of that group holding `pos-*` roles. A second
shop = a second group in the *same* realm. (When we upgrade past KC 24 → 26, Groups graduate to
**Organizations** for true self-service tenant admin. Same shape, nicer tooling. Not blocking.)

---

## 4. Where we are today — the honest sprawl (11 realms)

| Realm | Env | Users | Fate |
|---|---|---|---|
| `borrowhood` | prod | 262 | **KEEP** — the canonical prod realm (CUA) |
| `borrowhood-staging` | staging | 17 | **KEEP** — already unified ✅ |
| `lapiazza-realm-dev` | prod(!) Bottega | 7 | **FOLD** into `borrowhood` (Phase 1, in flight) |
| `lapiazza-realm-staging` | — | 1 | **DEAD** — orphaned (only `angel` left), no app points here → export + delete. *(Earlier "162" was an unverified number; live count on 2026-06-24 = 1.)* |
| `kc-pos-realm-dev` | dev/stg/sandbox | 9 | **FOLD** Banco/POS into the unified realm (Phase 2) |
| `artemis` | dev | 4 | **RETIRE** → becomes group `shop:artemis` (Phase 2) |
| `kc-camper-service-realm-dev` | dev | 10 | **FOLD** → `garage` client (Phase 3) |
| `kc-isotto-print-realm-dev` | dev | 5 | **FOLD** → `isotto` client (Phase 3) |
| `kc-realm-dev` | dev | 6 | **FOLD** → `helix-dev` (Phase 4) |
| `fourtwenty` | dev | 4 | **DEAD** — unused POS demo → delete |
| `blowup` | dev | 2 | **DEAD** — unused POS demo → delete |

**KC 24.0.4** — token-exchange GA, multi-realm JWT validation already working (`keycloak_auth.py`
reads the `iss` claim + fetches per-realm JWKS), JIT provisioning ready. Organizations available but
not deployed. **One hardcode to kill:** `keycloak_auth.py:29` pins `POS_REALM = "kc-pos-realm-dev"` —
must become config-driven (env → realm) before POS can join the unified realm.

---

## 5. Cleanup roadmap — phased, parallel/sequential, with rollback

### Phase 0 — Decommission the dead (quick win, zero risk, do now)
Export then delete `fourtwenty`, `blowup`, and (after confirming no `keycloak_id` FKs point at it)
`lapiazza-realm-staging`. **Parallel, independent.** Drops 11 realms → 8 in an afternoon.
*Rollback:* re-import the JSON export.

### Phase 1 — Bottega → `borrowhood` (prod) — IN FLIGHT
Finish the Option-A cutover already live on staging: add the `lapiazza_web` client + `lapiazza-*`
roles to prod `borrowhood`, repoint prod `LP_REALM → borrowhood`, verify real users still work.
*Sequential — it's the template every later fold copies.* Owned by `LP-IDENTITY-CONSOLIDATION-ADR.md`.
*Rollback:* repoint `LP_REALM` back, redeploy (old realm left intact = additive).

### Phase 2 — HelixPOS / Banco → unified realm (unblocks Artemis Premium)
- Kill the `keycloak_auth.py:29` hardcode → realm from config (env → realm), like `LP_REALM`.
- Add `helixpos` client + the `pos-*` roles to `borrowhood`(-staging).
- Retire the `artemis` realm → re-home Felix's 4 users as group `shop:artemis`.
- *Sequential after Phase 1.* **This is also the clean foundation for the Artemis Premium business
  account** — once POS users live in the same realm as the Square, publishing an item needs no
  cross-realm token exchange at all (see §6).

### Phase 3 — Garage + ISOTTO → clients (parallel pair)
Fold `kc-camper-service-realm-dev` → `garage` client and `kc-isotto-print-realm-dev` → `isotto`
client, roles carried as client roles. *These two are independent of each other — do them in
parallel.* Low traffic (POC realms), so low risk.

### Phase 4 — Collapse the dev realms → one `helix-dev`
Build a single dev realm that mirrors prod's clients + roles, retire `kc-realm-dev`,
`lapiazza-realm-dev` (dev side), `kc-pos-realm-dev` (dev side). *Last — tidiness, not urgency.*
End state: **3 realms.**

---

## 6. How this unblocks Artemis Premium (the tie-back)

The cutover we started this morning has exactly ONE hard seam: provisioning a La Piazza identity for
the shop to publish AS (`BANCO-ARTEMIS-PREMIUM-CUTOVER-PLAN.md` §2, R4). The grand vision dissolves it:

- **Today (pre-migration):** Banco/POS users live in `kc-pos-realm-dev`; the Square lives in
  `borrowhood`. Different realms → the business account must be provisioned cross-realm (KC admin API
  creates a `borrowhood` user; we hold its credential). **This still works and is NOT throwaway** —
  it's a realm-agnostic "create the shop's account in *this env's* La Piazza realm" function.
- **After Phase 2:** Banco/POS users already ARE `borrowhood` users. The "business account" is just
  the same person gaining a `lapiazza-business` role + business attributes (VAT, name). No second
  account, no cross-realm dance. The door is already open.

**Sequencing decision (matters now):** we do **NOT** block Artemis Premium on the full Phase-2 POS
migration. We build the provisioning realm-agnostic now (works cross-realm), and when Phase 2 lands it
simplifies to a role grant. Artemis Premium and the identity cleanup proceed in parallel; they meet at
Phase 2. *Decouple them — keep both moving.*

---

## 7. Decisions — LOCKED (Angel, 2026-06-24: "yes to all five")
| # | Decision | Status |
|---|---|---|
| ID1 | **Realm = Environment** (3 realms), app = client, shop = group — the four-nouns model | ✅ LOCKED |
| ID2 | Multi-shop tenancy = **Groups** (→ Organizations on KC 26), not realm-per-shop | ✅ LOCKED — supersedes "realm = shop" |
| ID3 | Keep prod realm id `borrowhood`; rebrand the *theme* to La Piazza; true rename = a separate future sweep | ✅ LOCKED |
| ID4 | Decommission dead realms (`fourtwenty`, `blowup`, `lapiazza-realm-staging`) — export first | ✅ LOCKED |
| ID5 | Artemis Premium provisioning built **realm-agnostic now**, simplifies after Phase 2 — decouple | ✅ LOCKED |

*One account. Many modules. Three environments. Clean the house once, live in it for years.*
