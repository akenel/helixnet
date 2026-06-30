# Banco Multi-Tenant Plan — Organizations within Realms

*Status: PLAN (the "eventually"). The SEAM is cheap to add now; the full build lands when a real second
tenant (Michael's own shop, a different business) arrives. Extends the locked identity architecture
(helix-identity-architecture: realm=environment ×3, client=app, role=permission, group=shop).*

---

## 1. The model the user described (and it's right)

This is the SAP / Azure / every-cloud-vendor model: **one codebase, give each customer a tenant, run the same
software for everyone, isolate their data.** Map it onto Banco like this:

```
Realm          = ENVIRONMENT     sandbox / staging / production        ×3, FIXED (the dev→live lifecycle)
  Organization = TENANT          a legal entity + VAT number           Artemis · Michael's Shop · Bakery X
    Location   = branch / shop   a physical till location              Artemis: Lucerne · Bern · Zurich
      Group    = team            (the existing group=shop noun)        per-location staff
        User   = cashier + role
```

**Key correction the user made himself:** realms are **environments**, NOT tenants. There are exactly three
(sandbox/staging/production), forever. **Every tenant lives *inside* each realm.** Tenants are **Organizations**,
not realms.

- **Organization / Tenant** = the isolation unit. One **VAT number**, its own **catalog**, its own **stock**,
  its own **sales / reports / closeout**. Tenant A can never see Tenant B's data.
- **Keycloak has Organizations** (KC 24+) — a first-class in-realm multi-tenancy feature. The user's instinct
  ("organizations is better") matches the actual tool. Use KC Organizations for the identity/login side.

## 2. Internal vs external (the two cases)

- **Internal — the Artemis umbrella (SAP "sales organization"):** ONE tenant (Artemis, one VAT) with MULTIPLE
  **locations** (Lucerne / Bern / Zurich). Shared catalog, per-location sales/closeout/"what sold where". This is
  the multi-location story from [[banco-vertical-packs]]. *Same legal entity → one tenant, many locations.*
- **External — Michael goes independent:** a SEPARATE **tenant** — own VAT, own catalog, own stock, own sales —
  fully isolated from Artemis. *Different legal entity → different tenant.* (Michael = the trigger that makes
  multi-tenancy real; until then Banco is effectively single-tenant = Artemis.)

## 3. The data model — row-level isolation by `tenant_id`

Shared schema, partitioned data (the standard SaaS pattern, and what SAP/Azure do under the hood):
- Add a **`tenant_id`** (organization id) to the key tables: products, transactions, customers, shifts,
  translations, images, etc.
- **Every query is scoped by `tenant_id`.** Enforced centrally (a tenant-context dependency / a query filter),
  not per-endpoint — so a missed filter can't leak data.
- It's the **same isolation pattern as the source-scoped SKU prefix** (`TAM-`/`MOS-`/`LZ-`, [[banco-artemis-catalog-import]]),
  one level up: there a discriminator partitions *products by source*; here `tenant_id` partitions *everything by
  business*.

## 4. Security — the one rule that can never break

**Tenant A must NEVER see Tenant B's data.** A cross-tenant leak is catastrophic (someone else's sales, customers,
prices). So:
- Tenant scoping is enforced in ONE place (middleware / a base query), never hand-rolled per query.
- A **"Tenant Isolation" e2e scenario** goes in the standard suite: tenant A's token must get 0 rows of tenant B's
  data, on every endpoint. This is a release gate.

## 5. Sequencing — seam now, full build when tenant #2 is real (YAGNI-aware)

- **Now (cheap):** add `tenant_id` to the model, **default every existing row to "Artemis"**. One migration, a
  tenant-context resolver, queries scoped. Costs little; saves a rewrite later.
- **When Michael (or any 2nd business) arrives:** create his Organization (KC) + tenant row, scope his data, set
  his VAT number + branding. Adding a tenant becomes "create an org + load its catalog," not a re-architecture.
- **Full build** (per-tenant settings, branding, billing, the KC Organizations wiring, the isolation gate) is the
  "eventually" — done carefully, test-gated, when there's a real second tenant to justify it.

## 6. Why this fits "one source code, one sandbox"
The user's whole constraint — **maintain one codebase, everybody on the same envs** — is exactly what row-level
multi-tenancy delivers: one app, one DB per env, N tenants isolated by `tenant_id`, identity via KC Organizations.
Maintain once, serve many. That *is* the SAP-alternative thesis ([[banco-why-not-the-big-guys]]) made structural.

> One realm = one environment. One Organization = one business (VAT). One location = one till. One `tenant_id`
> on every row. Everybody fits; nobody collides; you maintain one thing.
