# Postino — Architecture Plan (draft for decisions)

*Angel wants: Postgres, MinIO, Keycloak (owner + auditor + guardian/tester), AND a
Keycloak realm where the head-shops themselves sign in for a forum. Let's plan before we
build further.*

## The one thing we MUST get right first: the wall

Postino has **two populations with opposite trust models**, and mixing them is the
single biggest risk in this whole design:

1. **The cockpit (internal).** You, an auditor, a tester. Here a head-shop is a *prospect*
   — with a qualify score, a persona tag ("drowning owner-operator"), private notes, a
   call history. This data is **reputationally radioactive**. If Werner Bösch ever logged
   in and saw *"score 45, at breaking point, easy close,"* the relationship is dead.

2. **The town square (external).** The head-shops themselves — Bösch, Mosimann, Fischer —
   sign in as members of a community/forum. They see each other, post, get resources.

These are near-opposite in sensitivity. **The prospect must never be able to read the
CRM's opinion of them.** This is the seal-inspection lesson applied to data: design the
wall before the plumbing, or one leak ends the business.

### How we build the wall
- **Two apps, two audiences, two Keycloak realms, two MinIO buckets.**
  - `Postino CRM` → realm `postino` (roles: owner / auditor / tester), bucket `postino-private`.
  - `Piazza Forum` → realm `piazza-community` (external self-signup, email-verified),
    bucket `forum-public`.
- Data flows **one way only**: the CRM may record "this lead became forum member #123";
  the forum can never query the CRM. No shared tables, no shared login.
- This also fits your multi-tenant doctrine (realm = boundary) and the "export =
  exfiltration" discipline already in memory.

## Reuse the house stack — don't reinvent

You already run every piece of this for Banco/HelixNet. Reusing it is *less* work than
maintaining a SQLite snowflake:

| Need | Use | New thing, not new server |
|------|-----|---------------------------|
| Relational data | **Postgres** | new DB `postino` (SQLAlchemy already abstracts it — swap the engine URL) |
| Files (postcard PDFs, shop photos, print kits) | **MinIO** | new bucket `postino-private` |
| Identity | **Keycloak** | new realm `postino` + roles |
| Routing | **Traefik** | `crm.lapiazza.app` (internal, IP-gated) |
| Orchestration | **Docker Compose** | one more service |

## Roles (internal realm `postino`)

| Role | Can |
|------|-----|
| `owner` (Angel) | everything: edit leads, run campaigns, export, manage |
| `auditor` | read-only + see the audit log; **cannot** export PII (export = exfiltration) |
| `tester` / `guardian` | drive the app in a sandbox, file issues; no access to prod prospect data |

## The phased roadmap (don't build it all before the first postcard ships)

- **Phase 0 — DONE today.** SQLite Postino: 20 qualified leads, board / table / lead detail,
  touch-logging, CSV export. **Usable tonight, single user.**
- **Phase 1 — Make it "proper" (internal).** Postgres + MinIO + Keycloak realm
  (owner/auditor/tester login). Attach files to a lead (the postcard PDF, a photo of the
  shop). Audit log of every change. → your team can log in; data is durable and backed up.
- **Phase 2 — Campaign ops.** Print postcards + address labels for a whole stage straight
  from the board (reuse the Puppeteer pipeline). Run the enrichment recipe to add 100+
  leads that self-qualify by the scorecard rubric. Per-campaign views (Isotto, Camper&Tour).
- **Phase 3 — The town square (external).** Separate realm + forum app for head-shops.
  Community, shared resources, support tickets (reuses the hypercare / tickets-as-knowledge
  pattern).

## Honest discipline note (the felix lesson)

Phase 3 (the forum) is **supply-push risk**: building a community before any head-shop has
asked to be in one is the same trap as building more app for a customer who said no. The
CRM (Phases 0–1) earns its keep the day it goes live — it's *your* cockpit, no external
demand required. Build the forum when a real shop *pulls* for it, not before.

So: the forum belongs in the plan (design the wall now so we never paint ourselves into a
corner), but not in the near-term build queue unless you know a shop who wants in.

## Decisions LOCKED (2026-07-01)

1. **The wall = two realms, two apps, two buckets.** CRM (realm `postino`, bucket
   `postino-private`) fully separate from the future forum (realm `piazza-community`,
   bucket `forum-public`). Data flows one way only — the forum can NEVER read the CRM.
   This is the non-negotiable design constraint; everything else is built around it.
2. **Next = PLAN ONLY. Do not build more CRM yet.** Phase 0 (SQLite tracker) stays as the
   working prototype. Energy goes to **postcards**, not infrastructure.
3. **Forum = captured & deferred (Phase 3).** Building a town square before a head-shop
   asks to be in one is supply-push (the Felix lesson). Design the wall now so we never
   corner ourselves; build the forum only when a real shop *pulls* for it.

### What that means for the build queue
- **LIVE track:** the postcard campaign to the qualified A-list. This is the priority.
- **PARKED (designed, not built):** Postgres migration, MinIO, Keycloak realms, the forum.
  When we un-park Phase 1, the two-realm wall above is the blueprint.
