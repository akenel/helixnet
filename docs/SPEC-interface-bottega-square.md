# SPEC · The Interface — Bottega ↔ Square (the iFlow)

> Two modules, one integration layer. The Workshop (Bottega) reads + writes the Square
> (La Piazza marketplace) on a member's behalf — the SAP-style interface Angel described:
> GET/POST/PATCH across the modules, no realm merge required for v1.

**Status:** spec + **Legends-1 (cast read) built**. Writes specced, phased behind the identity link.

---

## Grounded facts (verified 2026-06-07)
| Fact | Value | Consequence |
|---|---|---|
| Square repo | **separate git repo** (`BorrowHood/`), image `borrowhood:staging`, no `/opt` checkout on box | marketplace-side endpoints need its own build/deploy (unmapped) → defer write API |
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
