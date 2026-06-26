# Identity in LEGO terms — THREE realms, not six (the back-on-track note)

*Locked by Angel 2026-06-26. This is the plain-language version of
[`HELIX-IDENTITY-ARCHITECTURE.md`](HELIX-IDENTITY-ARCHITECTURE.md) — same model, no jargon.
Written because one terminal started building a **workforce realm + a public realm** (6 realms);
the correct answer is **3 realms** with workforce-vs-public handled as **roles**, not realms.*

---

## The decision, one line

**Three realms total — one per environment: `sandbox`, `staging`, `prod`.**
Everything else (apps, people, workforce-vs-public, shops) lives *inside* those three.

---

## The LEGO model

| LEGO piece | = | In Keycloak | How many |
|---|---|---|---|
| **Baseplate** | a world / environment | **Realm** | **exactly 3**: sandbox, staging, prod |
| **Building on the baseplate** | an app / module | **Client** | one per app: Banco POS, La Piazza, print shop, garage, lab |
| **Minifig** | one person | **User** | one account per human |
| **Hats the minifig wears** | what you're allowed to do | **Roles** | many per person, worn at once |
| **Team sticker on the minifig** | which shop you belong to | **Group** | one per shop: `shop:artemis`, `shop:isotto` |

### The rule that decides everything

> **A minifig cannot walk from one baseplate to another.**

In Keycloak a realm is a sealed box: a person in realm A is a *different* person in realm B —
different login, different `sub`, no SSO between them. So if "workforce" and "public" were two
**realms**, then anyone who is both — Pam the cashier who also shops on La Piazza, Felix the admin
who also has a business shopfront — would need **two separate accounts** that can never be the same
person. That is exactly the silo we are trying to kill.

**Therefore: workforce vs public is NOT two baseplates. It is two HATS on the same minifig.**

---

## Workforce vs public = two sets of hats (role tiers)

| Side | Hats (roles) | Who hands them out |
|---|---|---|
| **Public** (customer) | `member` (individual), `business` (has VAT, sells) | anyone grabs `member` at the door; `business` needs a VAT check |
| **Workforce** (staff) | `pos-cashier`, `pos-manager`, `pos-admin`, `isotto-operator`, `camper-mechanic`, … `admin` | **only an admin grants these** — never self-serve |

- The **Banco POS** building reads the **workforce** hats (`pos-*`).
- The **La Piazza** building reads the **public** hats (`member` / `business`).
- **Same baseplate, same minifig.** Pam clocks out as a cashier and opens Bottega as a member —
  one account, no switching.

The protection you wanted ("don't let randos become cashiers") is **the hat, not the baseplate**:
a public member simply *has no* `pos-*` role, so they cannot touch the till — and only an admin can
grant that role. The role is the wall.

---

## The cast — one minifig each, all on the same baseplate

| Person | Public hat | Workforce hat | Team (group) | Accounts |
|---|---|---|---|---|
| Tourist | `member` | — | — | **1** |
| Pam | `member` | `pos-cashier` | `shop:artemis` | **1** |
| Ralph | `member` | `pos-manager` | `shop:artemis` | **1** |
| Felix | `business` (VAT) | `pos-admin` | `shop:artemis` | **1** |
| Famous Guy | `member` | `isotto-operator` | `shop:isotto` | **1** |

If workforce and public were separate realms, every row with two hats becomes **two accounts**.
That is the whole reason we don't split them.

---

## What "global" was reaching for (you don't need a third tenant realm)

The instinct for a "global realm" is two things, neither a new realm:

1. **Platform admins** (you, the stewards who run things across all shops) = an `admin` /
   `platform-admin` **role** in the same realm.
2. **Keycloak's own `master` realm** = already exists, it's where KC itself is administered.
   Keep it, never touch it. It's plumbing, not people — the only "global" realm, and it's not a
   tenant.

---

## End state (and why it's *fewer* parts)

- ❌ Workforce realm + public realm × 3 envs = **6–9 realms**, double accounts, broken SSO.
- ✅ **3 realms** (sandbox / staging / prod). Inside each:
  - every app = a **client**
  - every person = **one account**
  - workforce vs public = **role tiers** (`member`/`business` vs `staff`/`admin`)
  - every shop = a **group** (`shop:artemis`)

**One baseplate per world. One minifig per person. Many hats per minifig.** Every cross-app flow
you want — Felix orders labels from the print shop, Pam rings a sale then sells on La Piazza after
work — runs off that single identity.

---

## The industry words (for pitches)

The two sides have real names: **Workforce Identity** (staff, admin-provisioned) vs **Customer
Identity / CIAM** (the public, self-registered). Big platforms (Auth0, Okta, Azure AD vs Azure AD
**B2C**) often *do* split these into separate identity stores — but they do it precisely because
their staff and customers are almost never the same people. In our world the *same* people wear both
hats constantly (Pam, Ralph, Felix), so seamless crossover is the whole point — which is why we keep
them in one realm and split by role, not by realm.

*Three baseplates. One minifig per person. Hats, not walls.*
</content>
</invoke>
