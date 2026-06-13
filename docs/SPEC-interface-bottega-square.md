# SPEC · The Interface — Bottega ↔ Square (the iFlow)

> Two modules, one integration layer. The Workshop (Bottega) reads + writes the Square
> (La Piazza marketplace) on a member's behalf — the SAP-style interface Angel described:
> GET/POST/PATCH across the modules, no realm merge required for v1.

**Status:** spec + **Legends-1 (cast read) built**. **Writes approach CHOSEN 2026-06-13: BAPI-style service endpoints (option C), service-key auth, identity-by-email — keeps the two realms, no Keycloak migration.** (The two apps are on separate KC realms — `lapiazza-realm-*` for the Bottega, `borrowhood*` for the Square — proven by distinct JWKS/issuers, so a user token does NOT cross; the service-key BAPI sidesteps that entirely.)

---

## The simple model (keep it this simple — 2026-06-13)

**Two modules. One person. One button. Last write wins.**

- **La Piazza (the Square)** = the storefront / front door. Where you *show, sell, auction, run events, offer services*. Your display window.
- **The Bottega (the Workshop)** = the back door. Where Cleopatra and the masters *guide you* — figure out who you are, build you up, and help you make a **proper, customized profile** instead of winging it freehand in the Square.

It is **one relationship the whole way through** — the same single person in both rooms. Not fifteen people running someone's Bottega. One guy, one account, two doors. Resist the urge to make this an SAP monolith with modules and governance; there are exactly **two modules** and **one user editing their own stuff**.

**The whole feature in one line:** the Workshop builds your profile → you tap **"Push to La Piazza"** → it fills your storefront profile. Want to change it? Push again, or edit it in La Piazza. Last one wins. It's your own window — no merge, no diff, no "are you sure."

The *only* real engineering is **one account that works at both doors** (the identity link). Everything else — building the profile (a recipe we already have) and saving it (`PATCH /me`, already exists) — is wiring two things that already work, behind one button.

---

## The two POCs (the only two journeys that matter)

### POC A — Brand-new user, enters through the Bottega (back door)
1. **Get Started** on the Bottega → name, email, and "tell us about yourself" (CV optional).
2. We create **one account** — same email, works at both doors (La Piazza account made to match, automatically).
3. Cleopatra + the chosen master + the profile recipe build a **draft profile** in the Workshop — byline, story, skills.
4. They tune it with the masters until it feels like *them*.
5. They tap **Push to La Piazza** → their storefront profile is filled in. They walk into the Square with a finished, customized profile — **they never had to wing it freehand.**

### POC B — Existing La Piazza user with a display window, comes into the Bottega to improve it
1. They already have a La Piazza account + a storefront/profile (the display window).
2. They log into the Bottega — **same login, same person** (one account).
3. The Bottega **pulls their current Square profile** so they start from what's *already live*, not a blank page. *(This read already exists: `square_bridge.get_square_profile`.)*
4. Cleopatra + masters help them sharpen the byline / story / a listing.
5. They tap **Push to La Piazza** → the improved version replaces the old. Last-write-wins; it's their own window.

**Is POC B too powerful? No.** It's POC A plus one "pull first" step — and the pull is already built. Same one account, same one button. Both journeys ride the same machinery.

---

## The contract discipline — BAPI, not raw PATCH (chosen 2026-06-13)

**Principle (Angel's material-master rule):** the write path is a *defined service operation* (a BAPI), not field-poking. A raw `PATCH` is a dumb pipe — changes a field, trusts the caller, can leave the master half-valid. A **BAPI is a smart gate**: it validates the **whole proposed state at the door**, is **all-or-nothing** (commit or rollback — never a half-write), and on failure returns a **structured, actionable error** ("missing X / invalid Y, fix and retry") with **no change made**. The rule for "what is a valid profile" lives in **one place** — so the Bottega, the marketplace's own settings page, and any future client all go through the same gate and get the same guarantee. Call it from anywhere: it's either right, or a clean rejection.

**Scope (so it stays simple, not an SAP monolith):** the BAPI guards the **module border + shared master data** (profile, listings). It does NOT wrap the Bottega's own private/ephemeral state (draft notes, in-progress recipe runs). Rule: *crosses the border or is shared master data → service interface; purely local → don't bother.*

**Auth + identity:** caller authenticates as a trusted service via `X-LP-Service-Key` (env `LP_SERVICE_KEY`, a secret shared Bottega↔Square). The user is identified **by email** (the realms differ, so `sub` can't be the join key); the marketplace resolves-or-creates the `bh_user` by email — `get_user` already matches by email.

### First BAPI contract — `publish_profile`
- **Endpoint (marketplace / BorrowHood):** `POST /api/v1/lp/bapi/publish-profile`
- **Headers:** `X-LP-Service-Key: <LP_SERVICE_KEY>`
- **Request:**
  ```json
  { "email": "person@example.com",        // required — the identity join key
    "display_name": "…",                   // optional
    "bio": "…", "tagline": "…",            // optional
    "skills": ["…"], "categories": ["…"],  // optional arrays
    "workshop_name": "…" }                 // optional
  ```
- **Validation (at the door, before any write):** `email` present + well-formed; `bio` ≤ N chars, `tagline` ≤ M chars; `categories` ∈ the marketplace's real category set (else rejected, not silently dropped); slug uniqueness handled server-side. Bad input → **422** `{ "ok": false, "errors": [ { "field": "...", "code": "...", "message": "..." } ] }`, **nothing written**.
- **Success:** find-or-create `bh_user` by email → update the allowed fields → **commit transactionally** → **200** `{ "ok": true, "profile": { … }, "url": "/u/<slug>" }`.
- **Idempotent:** same payload twice = same result (last-write-wins on fields; no duplicate user). 
- **Bottega side:** `square_bridge.publish_profile(email, fields)` calls it with the service key; the consumer (the "Push to La Piazza" button handler) never sees the transport.

**Later BAPIs (same shape):** `publish-listing` (create/update an item), `retire-listing`. Each: validate-whole → commit-or-reject → structured errors.

---

## Grounded facts (verified 2026-06-07, updated 2026-06-13)
| Fact | Value | Consequence |
|---|---|---|
| Square repo | **FOUND 2026-06-13:** `/home/angel/repos/helixnet/BorrowHood/` (nested git repo, remote `github.com/akenel/borrowhood.git`, branch `main`) | build/deploy path is mappable — no longer a blocker |
| **Write endpoints already exist** | `PATCH /me` (`users/me.py:84`, fields incl. display_name/tagline/bio/workshop_name/skills), `POST /me/skills`, `POST /listings` (`listings.py:91`), `PATCH /listings/{id}` (:208), `DELETE` (:247), `PATCH /listings/{id}/status` (:293) — all `Depends(require_auth)` | **the write API is NOT new work.** "Push to La Piazza" just CALLS these. The only real work is the identity link below. |
| Same Postgres | `helix_db` (Bottega) + `borrowhood` (Square), one instance, `helix_user` can read both | **reads can use a read-only DB connection now** |
| Square identity key | `bh_user.keycloak_id` (sub) + `email` — **no `username` column** | — |
| Bottega identity key | `bottega_profiles.username` (KC preferred_username) | **no shared key** between modules |
| Item ownership | `bh_item.owner_id` → `bh_user.id` (uuid) | per-user item CRUD needs the user's `bh_user.id` |

**The pivotal truth:** the two modules share **no direct key**. So **per-user writes** (push my
bio, edit my items) need an **identity link** (username → KC sub → `bh_user.keycloak_id`, or email).
That link is the SSO/one-realm work ([[SPEC-BL-014]]). **But reading the cast (Legends) needs NO
per-user link** — it's a public browse. So: **read-the-cast now, per-user CRUD after the link.**

---

## Design principle — the swappable boundary
The Bottega calls a single service module, `src/services/square_bridge.py`. The *consumer*
(routers, picker) never changes. Today the implementation is a **read-only DB connection**;
tomorrow it's the **marketplace API key** — swap the body of one function, nothing else moves.
(Rules #6/#7 of [[SPEC-BL-014]]: config-driven boundary, machine-to-machine reads.)

---

## The full CRUD contract (target)

**Auth:** marketplace API endpoints require header `X-LP-Service-Key: <key>` (a shared service
key, env: `LP_SERVICE_KEY`). The read shim uses a read-only DB connection (no key) until the
marketplace API ships.

| Op | Bottega service call | Backed by (now → later) | Needs identity link? |
|---|---|---|---|
| **List legends** (cast) | `square.list_legends(q?, house?, limit)` | read-only DB → `GET /api/v1/lp/legends` | no |
| **Get a legend** | `square.get_legend(id)` | read-only DB → `GET /api/v1/lp/legends/{id}` | no |
| **Get my profile** | `square.get_profile(member)` | API `GET /api/v1/lp/me` | **yes** |
| **Patch my profile** (push bio from CV) | `square.patch_profile(member, {...})` | API `PATCH /api/v1/lp/me` | **yes** |
| **List my items** | `square.list_items(member)` | API `GET /api/v1/lp/items?mine` | **yes** |
| **Create item** | `square.create_item(member, {...})` | API `POST /api/v1/lp/items` | **yes** |
| **Update item** (improve + repost) | `square.update_item(member, id, {...})` | API `PATCH /api/v1/lp/items/{id}` | **yes** |
| **Delete item** | `square.delete_item(member, id)` | API `DELETE /api/v1/lp/items/{id}` | **yes** |

**Identity link (for the `yes` rows):** resolve the Bottega `username` → KC `sub` (via Keycloak
admin lookup or the token's `sub`) → match `bh_user.keycloak_id`. If absent, the member hasn't
linked a Square account → prompt "connect your La Piazza account". Post-one-realm SSO, this is
automatic (same sub everywhere).

---

## Legends-1 (BUILT) — the cast read
- `square_bridge.list_legends()` opens a **read-only async engine** to the `borrowhood` DB
  (derived from the Bottega DB creds, db=`borrowhood`) and returns the cast:
  `{name (display_name), workshop (workshop_name), tagline, bio, ref (keycloak_id)}`.
- `GET /api/v1/compute/legends` (auth: `require_bottega_access`) exposes it to the picker.
- Feeds **Ask a Master**: pick a legend → its `name` prefills `mentor-session`.

## Next slices
- **Legends-2:** AI-derived Houses (classify the cast into ~8–12 Houses; cache).
- **Legends-3:** the picker UI (House → person → bio synopsis → pick → suggested questions).
- **Legends-4:** suggested questions per legend (AI, cached).
- **Interface-write (after BL-014 link):** profile PATCH (the original auto-init-from-CV vision)
  + items CRUD (pull in → improve → repost) via the marketplace API key.

---
*Spec'd 2026-06-07. Two modules, one iFlow. Read the cast now; write back when identity is one. 🐺*
