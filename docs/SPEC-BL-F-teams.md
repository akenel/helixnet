# SPEC · Block F — Teams & Groups (two rails: Access + Affinity)

> **Angel's insight (2026-06-08):** "Groups are the apps in a way… teams are what mentors a
> person uses or what items they have… their bio puts them in a group… with Keycloak, people
> are automatically in a group, therefore these are the apps they can use." — Yes. And it's
> **two clean layers, never conflated.**

**Status:** spec. Builds on the one-realm SSO ([[SPEC-BL-014]]) and the Legends Houses (already live).

---

## The two rails

| | **ACCESS groups** | **AFFINITY groups** |
|---|---|---|
| **Question** | *what can you open?* | *who are your people / mentors?* |
| **Home** | **Keycloak Groups** (carry role-mappings) | **app data** — profile tags · House · items · interests |
| **Nature** | hard, secure boundary (entitlement) | soft, social, discovery |
| **Set how** | auto on signup + admin/role | derived from bio (Ollama) + chosen tags |
| **Drives** | which apps/logins appear (POS, Camper, ISOTTO…) | mentor-matching · community · the Square's "your people" |
| **Example** | baker → `pos` group → POS app | bio "cook/gardener" → **The Hearth** → Flora-type mentors |

**Rule:** Keycloak is the **hard rail** (access). App data is the **soft layer** on top (affinity).
Never use a KC group to mean "interest", never use a bio tag to grant access.

---

## Rail 1 — Access groups (Keycloak)
- **A KC Group carries realm-role mappings.** Membership ⇒ roles ⇒ app entitlement. "In the group = these are your apps."
- **Group → app mapping** (in the unified `lapiazza-realm-{env}`):
  - `lapiazza-user` (everyone — base): Bottega + Square.
  - `pos`, `camper`, `isotto`, `marketplace` … : each unlocks its module/app.
- **Auto-assignment on signup:** new member → `lapiazza-user` automatically (KC *Default Groups*). Module groups added when they pick/buy a module (or an admin adds them).
- **Teams = a business/org** (the B2B angle, the heart of Block F): a shop with staff = **one KC group** (e.g. `team:camper-and-tour`) whose members share the app + get **per-seat roles** (`*-admin`, `*-manager`, `*-staff`). This is how Nino's 3 mechanics all use the one repairs app with the right permissions. A Team is just an Access group scoped to one business.
- **The UI reads groups from the token** (`groups`/roles claim) → renders only the apps you're entitled to (the sitemap/app-directory becomes *per-user*).

**KC primitives:** Groups API (`/admin/realms/{realm}/groups`), group role-mappings, Default Groups,
the `groups` client-scope/mapper so the claim lands in the token. (Mirror the `lp_*` script pattern,
e.g. `scripts/lp_seed_demo_users.py`, for a `lp_groups.py`.)

## Rail 2 — Affinity groups (app data / Houses)
- **Reuse the Legends House taxonomy** (`square_bridge.HOUSES`: The Forge / Atelier / Hearth / …).
  Today it classifies the *master personas*; **extend the same `classify` to USERS** — derive a
  user's House from their bio (the Ollama classify already exists, `/legends/classify` pattern).
- **Stored as profile data** (a `house` + `tags` on `bottega_profiles` / the person-schema), NOT KC.
- **Drives:** mentor-matching (your House → suggested masters), community ("others in The Hearth"),
  the Square's discovery ("people like you"), and the daily-coach tone. Soft, changeable, no security.
- **Items/interests** are affinity too — what you list/own/teach clusters you, for discovery only.

---

## Build order (when Block F is picked up)
1. **Groups claim in the token** (client-scope/mapper) so apps can read entitlement. (cheap)
2. **Default Group** `lapiazza-user` on the realm; per-module groups created. (cheap)
3. **Per-user app-directory:** `/sitemap` shows only entitled apps (reads the claim).
4. **Teams (B2B):** a `team:<business>` group + a tiny admin to add staff + assign seat roles.
   *This is the revenue rail — a shop = a paid team.* Pairs with the HelixNet SME offer sheet.
5. **User Houses:** run `classify` on the user's bio → store `house`; surface "your House + your
   mentors" (extends Legends to the member, not just the cast).

## Boundaries / gotchas
- **One realm only** (BL-014) — groups live in `lapiazza-realm-{env}`, never a new realm per team.
- Don't put affinity in KC (groups don't belong to a marketing taxonomy — they bloat the token + couple security to interests).
- A user is in **many** affinity tags but a **bounded** set of access groups — keep the token lean.
- Relates to [[lp-platform-architecture-shared-services]] (KC = the hard rail), Legends (the Houses), and [[lp-state-coach-daily-onepager]] (the coach reads House for tone).

---
*Spec'd 2026-06-08. Two rails: Keycloak opens the doors; the bio finds your people.* 🐺
