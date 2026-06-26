# ADR: The Two-Realm Identity Model — workforce + community, per environment

- **Status:** Accepted — 2026-06-26 (Angel)
- **Refines:** `HELIX-IDENTITY-ARCHITECTURE.md` (the "realm = environment, app = client" north-star)
- **Triggered by:** the Banco POS realm split (`BANCO-POS-REALM-SPLIT-PLAN.md`) — building a
  per-app realm made us ask the bigger question before the pattern repeated for every app.

---

## The question

Should each app get its own Keycloak realm per environment, or should one realm per
environment serve all apps? We SWOT'd both extremes and rejected both:

- **One realm per app** → realm sprawl (the 11-realm mess we're cleaning up); a new realm every
  time we ship an app.
- **One realm for everything** → mixes *staff* and *the public* in a single identity pool: one
  password policy for both, self-registration sitting next to payroll-linked employees, and one
  misconfig takes down login for every app (the till included).

## The deciding insight (Angel, 2026-06-26)

**Every app is two-sided.** It doesn't matter what the app does — there are always:

1. **The people who DO the work** — fulfil the service, run the app from the inside.
   *Cashiers (Banco), mechanics (Camper & Tour: Nino, Sebastiano), printers (ISOTTO: Famous Guy),
   employees, admins.* This is **workforce identity**: internal, employer-provisioned, small,
   locked-down, never self-registers, must be rock-stable (the till can't go dark).
2. **The people who RECEIVE the work** — customers, makers, the public.
   *The person whose car gets fixed, who buys the prints, who buys at the counter.* This is
   **customer / community identity** (the industry term is **CIAM**): public, self-registers,
   frictionless, marketing-facing. **For every HelixNet business, this side IS La Piazza / Bottega**
   — the shared town square where all customers already live.

The right split is therefore **by population, not by app.**

## Decision

**Two Keycloak realms per environment, split by population:**

| Realm | Who logs in | Apps/surfaces (clients) |
|-------|-------------|--------------------------|
| **Workforce** | staff of *every* business — the people doing the work | Banco POS, future Camper & Tour garage app, future ISOTTO print app, HR, admin — each is a **client**; each business is a **group** |
| **Community** | customers & makers of *everything* — the public | La Piazza, Bottega (and the marketplace) — clients in this realm |

- It is **two realms total per env — not two per app.** The realm count never grows with the
  number of apps. New app → new **client** (and maybe a new **group**), *never* a new realm.
- The community realm is shared because **all businesses sell to the same town square** — a
  customer of Banco, the garage, and the print shop is one person on one La Piazza.
- The workforce realm is shared because staff isolation is by **client + group**, not by realm:
  a Camper & Tour mechanic and a Banco cashier are in the same realm but different groups and
  see different apps.

## The four nouns (refined from the north-star)

| Noun | Means | Example |
|------|-------|---------|
| **realm** | environment × **population** | `workforce-prod`, `community-prod` |
| **client** | an app / surface | `helix_pos_web` (Banco), `camper_garage_web`, `isotto_print_web`, `lapiazza_web` |
| **role** | a permission | `pos-cashier`, `garage-mechanic`, `print-operator` |
| **group** | a business / shop / tenant | "Artemis Store", "Camper & Tour", "ISOTTO Sport" |

So: *Nino* = user in **workforce realm**, group **Camper & Tour**, client **garage app**, role
**mechanic**. *Nino's customer* = user in **community realm**, on **La Piazza**. Same human is
**never** in both realms — because the customer never logs into the workforce app.

## Why the Banco ⇄ La Piazza loop still works (it doesn't need one shared realm)

The community loop is "receipt QR → customer joins La Piazza." The **customer never logs into
Banco.** The link is *La Piazza customer account ↔ Banco CRM record* (a data link), not a shared
login. So we get the loop **and** keep staff/public isolated. Same pattern for any business: the
garage's customer finds it on La Piazza; the garage's mechanics use the garage app on the
workforce realm.

## The reusable recipe — onboarding ANY new app

This is the part that "works both ways" for every future app (printing, garage, whatever):

1. **List the app's surfaces** (screens / who uses each).
2. For each surface ask: **is this user staff (doing the work) or public (receiving it)?**
3. **Staff surface** → add a **client** in the **workforce realm** (+ a **group** for that
   business if new). Give it roles. *No new realm.*
4. **Public surface** → it's **La Piazza / Bottega** (community realm) — reuse it, or add a
   client there. *No new realm.*
5. **Never create a realm for an app.** Realms are populations × environments — that set is fixed.

## Consequences

**Good**
- **Security posture per population:** workforce can be strict (MFA for admins, no self-reg);
  community can be frictionless (self-reg on). One policy each, not one compromise for both.
- **Blast radius contained:** a community-side auth change can't take the tills down, and vice
  versa. The thing the shop runs on is isolated from the marketing front door.
- **Breach isolation:** a public-pool leak doesn't expose employees, and the reverse.
- **Cleanup target still met:** ~2 realms × 3 envs = **6 realms**, down from 11 — and *stable*
  forever regardless of how many apps we add.
- **Clean SSO scoping:** staff SSO across internal apps; customer SSO across La Piazza/Bottega;
  no cross-bleed between the two worlds (fixes the "already logged in" dead-end at the seam).

**Costs / honest caveats**
- 6 realms means SMTP/theme/password-policy maintained **twice per env** (workforce vs
  community), not once. Acceptable — and they *should* differ anyway.
- A person who is BOTH a worker and a customer (e.g. Nino also shops on La Piazza) will have
  **two accounts** — one per population. That's correct and normal (workforce ≠ customer
  identity); don't try to merge them.
- Naming: the realms we have today are app-named (`kc-pos-realm-*`, `borrowhood`,
  `lapiazza-realm-*`). They map onto the two populations (below) and can be renamed
  opportunistically — the *model* is what's locked, not the strings.

## Current realms → target mapping (no rename forced today)

| Today | Population | Target name (when convenient) |
|-------|-----------|-------------------------------|
| `kc-pos-realm-dev` / `-stg` / `-prd` | **Workforce** (Banco is its first client) | `helix-workforce-<env>` |
| `borrowhood` / `lapiazza-realm-*` / `borrowhood-staging` | **Community** (La Piazza + Bottega) | `helix-community-<env>` |

- The `kc-pos-realm-*` realms from the Banco split **are** the workforce realm — POS is just the
  first client. HR, admin, and future internal apps (garage, print) join as **clients here**,
  **not** as new realms.
- La Piazza / Bottega stay on the community realm. The earlier "unify Bottega + BorrowHood"
  consolidation is the community-realm cleanup; it stays on track.
- Mail routing already follows this: workforce staging/prod → Resend; community → its own; dev +
  sandbox → MailHog. (See `BANCO-POS-REALM-SPLIT-PLAN.md`.)

## What does NOT change right now

No code, no realm renames as a result of this ADR. It locks the **target model and the recipe**.
The Banco realm split (Phase 1 staging live, Phase 2 prod pending) proceeds unchanged — it was
already building the workforce realm; we now just know to add future internal apps as *clients*
in it rather than spinning up `kc-<app>-realm-*` each time.

---

*One line to remember: **Realms are populations, not apps.** Two per environment — the people who
do the work, and the people they do it for.*
