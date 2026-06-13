# CONCEPT · The App Mesh — one user, many apps, apps that talk

> **Status: DRAFT / living.** The north star for how every La Piazza app (Bottega, the Square,
> Camper & Tour, the ISOTTO printer app, …) shares ONE user and exchanges data on his behalf.
> Written 2026-06-13 with Angel (ex-SAP PI/PO + ALE/IDoc). Missing pieces marked `// TODO(angel)`.

---

## The vision (Lego-man)

- The same human uses **many separate apps** — Bottega (workshop), the Square (La Piazza marketplace),
  Camper & Tour, the ISOTTO printer app, the POS, … Each is its **own application** (own DB, own deploy).
- He logs in **once** and moves freely between them (single sign-on).
- The **apps themselves exchange data** on his behalf, through his user + his roles — not just the user
  hopping around looking at things. He can **push** a thing from one app into another:
  - a postcard from the Bottega → the ISOTTO printer app (print it)
  - a design spec from the Bottega → Camper & Tour (build it)
  - a profile from the Bottega → the Square (publish it)
- It should **feel like one seamless app** to the user — but the apps stay **modular and independent**
  underneath. Seamless UX, modular architecture. That's the Lego promise.
- No teams yet. One user, all apps. (Designed so teams could slot in later without a rewrite.)

---

## Why this exists (the purpose — it shapes every design call)

We are quietly building a **micro-ERP**: build things in the workshop (Bottega = production), display
and sell on the Square (La Piazza = sales/distribution), build up the person (skills/roles = HR),
service & repair (Camper & Tour = a shop with work-center bays), print (ISOTTO). Underneath, every app
trades in the SAME primitives SAP calls **master data**: people (business partners), materials/goods,
services, vendors/customers.

**The market:** the $5k–$500k/yr operator that Salesforce and SAP Business One ignore — no software
addresses them. AI makes addressing them finally possible.

**The design constraint the purpose imposes: the ERP must be INVISIBLE.** The $5k/yr cook never sees
"master-data views" — she sees *"fill in your profile, push it to your shop."* We carry the ERP rigor
**underneath**; the user sees a seamless, friendly app. **If a feature makes the ERP machinery visible
to the end user, it's wrong.**

---

## The person is ONE master record with VIEWS (this dissolves the "duplicate profile")

The duplicated Bottega-profile vs La-Piazza-profile is NOT duplication to merge into one blob — it's the
SAP **material-master-views** pattern, unrecognized. **One master (the person, keyed by identity), many
views**, each owned where it makes sense:
- **Workshop view** (Bottega): skills, blueprint, the draft — *the building*. (basic + classification)
- **Storefront view** (La Piazza): public byline, listings, what's for sale — *the display*. (sales view)
- **HR view**: roles, what they do / want to do.
- *(later)* Camper view, Printer view — each app's slice.

Views share the **KEY** (the person), not the storage. A message carries only the view being changed —
you never fill the whole structure (basic-view vs classification-view vs sales-view, same material №).

**Reasonable near-term version:** we do NOT build 20 views — we have **two** (workshop + storefront).
The fix for today's pain = recognize the person as one master keyed by identity, let each app own its
view, and **sync the shared fields via a message** instead of keeping two disconnected blobs. The full
master-with-views is the concept to HOLD; two-linked-views is what we BUILD. (Unifying the key = Brick 1.)

---

## The two bricks — keep them SEPARATE

Gluing these together is what corrupts data and confuses everyone. They are independent decisions.

### 🧱 Brick 1 — IDENTITY (who the user is)
One identity, one role set, recognized by every app. SAP name: **SSO + CUA** (Central User Administration).

**Honest current state:** Brick 1 is **cracked**. There are 3+ separate Keycloak realms (camper,
borrowhood, lapiazza). What looks like SSO is **Google-login glue** — the same human is several
different users with different IDs and separate roles. Cross-app calls therefore bridge **by email**,
not by user-ID, and roles do not travel.

**Roadmap item (strategic, not now):** pour Brick 1 properly — one shared realm = real SSO, one
user-ID everywhere, roles that travel. Until then the mesh leans on email-as-join-key (tolerable at
village scale, fragile long-term). *Don't let the mesh grow tall on glue.*

### 🧱 Brick 2 — INTEGRATION (apps exchanging data)
Apps call each other's **published operations** on the user's behalf, over a durable, monitored bus.
This is the rest of this doc. We can start it **today** even with Brick 1 cracked (service-key + email).

---

## The SAP lineage (we are rebuilding the landscape, at village scale)

| SAP / ALE | App Mesh | What it is |
|---|---|---|
| SSO + CUA | the identity brick | one user + roles, everywhere |
| PI/PO (mostly **async**) | the bus | carries messages between apps |
| **Message type** (`MATMAS`, `DEBMAS`) | the **intent**: `PUBLISH_PROFILE`, `SUBMIT_PRINT_JOB`, `SUBMIT_BUILD_SPEC` | stable name, never changes meaning |
| **IDoc type / structure** | the **message contract** (JSON) | extend by adding an OPTIONAL field = "add a segment" (backward-compatible) |
| **Inbound function module** | the **handler** (a BAPI) on the receiving app | validate-whole → commit-or-reject → status |
| **qRFC queue** | the **queue / outbox** (RabbitMQ — already running for LPCX) | durable delivery, retry, nothing lost |
| **WE05 monitor** | the **Message Console** | partner · direction · message type · status · payload · error · reprocess |
| **User exits** | **hooks** on a handler | customize without changing the core message |
| Logical system / partner (WE20) | a **registered app** (partner) | Bottega, Square, Printer, Camper, … |
| **Sender / receiver adapter** | per-partner **adapter** | translates canonical ↔ the partner's real API (REST/JSON, SOAP, email/CSV) |
| **Message mapping** | the adapter's **translation** | canonical fields → the partner's field shape |

---

## The middleware — the broker + adapters (the PI/PO heart)

**Apps do NOT call each other point-to-point.** That's N×N spaghetti — every new app rewires all the
others. Instead, every app speaks **one canonical message** to a **central broker**; the broker has a
**per-partner adapter** that translates that message into whatever the target actually speaks, and
delivers it. This is the core value PI/PO was built for: a **hub**, not a web of direct wires.

- **Canonical message** (our IDoc-equivalent): app-neutral, stable (`PUBLISH_PROFILE`,
  `SUBMIT_PRINT_JOB`). An app learns ONE language — never every other app's API.
- **Adapter** (per partner): translates canonical → the partner's real protocol. Our apps = **REST +
  JSON**; a third party = whatever they speak (REST, SOAP, email/CSV). *Same principle as IDoc; only the
  wire format differs.* The adapter is the ONLY place a partner's dialect lives.
- **Partner registry** — each partner = `{name, adapter, endpoint, auth/creds, status}`. The **status**
  is the key trick:
  - **prepare-only** (no creds yet): the broker still **builds + validates** the outbound payload and
    **stages** it in the outbox — it just can't deliver. *We can integrate with apps we can't log into
    yet.*
  - **active** (creds registered — "refrigerate it"): the broker **flushes** staged messages and
    delivers live — **no code change**, just config.
- **Adding the 5th app = one new adapter + one registry row.** The other four don't move.

**This broker IS the heart of PI/PO — and it is literally the HelixOPS / "SAP-alternative" product,
dogfooded on our own apps.**

**Where the broker lives (decision — `// TODO(angel)` to confirm):** start as a **module inside one app**
(the compute/Bottega app already hosts the bus pieces) — cheapest, no new deployable. **Graduate to a
standalone broker service** when the mesh justifies it (3+ partners, or heavy async). Reserve the shape;
don't stand up a separate service for one flow.

---

## The BAPI contract discipline (the gate, not the pipe)

A raw `PATCH` is a **dumb pipe** — pokes a field, trusts the caller, can leave the master half-valid.
A **BAPI is a smart gate**: validates the **whole proposed state at the door**, is **all-or-nothing**
(commit or rollback — never a half-write), and on failure returns a **structured, actionable error**
("missing X / invalid Y, fix and retry") with **no change made**. The rule for "what is valid" lives in
**one place** — so every caller (Bottega, the app's own UI, a future mobile app) gets the same guarantee.
Call it from anywhere: it's either right, or a clean rejection.

**First contract — `PUBLISH_PROFILE` (see [[SPEC-interface-bottega-square]]):**
`POST /api/v1/lp/bapi/publish-profile`, header `X-LP-Service-Key`, body `{email(req), display_name?,
bio?, tagline?, skills[]?, categories[]?, workshop_name?}`. Validate-at-door → 422 `{ok:false,
errors:[…]}` with NO write on bad input; success → find-or-create `bh_user` by email → commit → 200
`{ok:true, profile, url}`. Idempotent.

---

## Recipes ARE the service interfaces (the spine — and we mostly built them right)

A recipe already has the **WSDL-operation shape**: `inputs[]` = the inbound structure (request),
`output_schema` = the outbound structure (response), the recipe name = the operation. That IS a service
interface. The basis of the whole platform is correct.

**What's missing to make them "correct" as *published* interfaces** (not a rewrite — a promotion):
a stable, **named + versioned contract** the broker can route to. Today the in/out live as an internal
convenience inside each recipe; we promote them to declared **message types** (`PUBLISH_PROFILE` is the
first). We likely have ~80% already in the recipe definitions.

> **Rule: don't rewrite the recipes — formalize their contracts** (name + in-schema + out-schema +
> version). A recipe run inside one app and a message sent to another app are the SAME act — a service
> interface called in a uniform way.

---

## Sync vs async (same message, two delivery modes)

- **Synchronous** — caller waits for the receipt. Use when **the user is watching** and wants instant
  confirmation (the "Push to La Piazza" button). Start here for `PUBLISH_PROFILE`.
- **Asynchronous (queued)** — the message goes on the queue; the caller doesn't wait; the receiving app
  processes it and records a status; failures **retry** and are visible in the Console. Use for
  app-to-app flows where the target may be slow/down and nothing may be lost (print job, build spec).

The **message type and contract are identical** in both modes — only the transport differs.

---

## THE ONE RULE (this is what protects the databases)

> **An app is the ONLY writer of its own master data. Every other app reaches it ONLY through its
> published message/BAPI — NEVER by writing its database directly, even though they share one Postgres.**

This single rule is what prevents the two databases from being messed up. (Read-only cross-DB reads —
e.g. the Legends cast bridge — are tolerated; cross-DB *writes* are forbidden. Always.)

---

## Security & robustness rules

- **Each app gets its OWN service key**, scoped to only the messages it's allowed to send. Rotatable.
  No single master key. (Limits breach blast radius.)
- **On-behalf-of authorization:** the message carries the user identity + the action; the **receiving**
  app authorizes against *the user's* roles (not the calling app's). Cleanest once Brick 1 is one realm.
- **Partial failure:** two apps never share one transaction. Each handler is atomic *within its own app*;
  the caller treats a push like mailing a letter — accepted-receipt or retry. (Outbox pattern.)
- **Versioning:** extend a contract only by **adding optional fields**; never repurpose or remove one.
  Breaking changes = a new message type / version.

---

## SWOT (short)

- **S:** one pattern everywhere (less confusion), DBs protected by The One Rule, apps independently
  deployable + rollback-able, mirrors Angel's PI/PO expertise.
- **W:** identity fragmented (Brick 1 cracked) until fixed; more moving parts than a monolith; each
  message/handler is real work.
- **O:** network effect of flows (postcard→printer→camper); the bus + Console **is** the HelixOPS /
  "SAP-alternative" product, dogfooded; audit/trust as a selling feature.
- **T:** distributed partial failure; service-key sprawl; silent identity drift (two emails = a twin);
  versioning rot.

---

## Build order (rich concept, lean increments)

1. **Now:** `PUBLISH_PROFILE` BAPI, delivered **sync**, shaped as a **canonical message through a thin
   broker call** (not a hardcoded point-to-point call) so it can grow adapters + the queue later.
   (Marketplace endpoint first, then the Bottega button. The "broker" can be ~10 lines today.)
2. **Next:** the **queue + Message Console** (WE05-style), built when the first **async** flow lands
   (e.g. the print-job push) — not before.
3. **Then:** new partners publish their small message catalogs (Printer: `SUBMIT_PRINT_JOB`; Camper:
   `SUBMIT_BUILD_SPEC`; …).
4. **Strategic, parallel track:** pour **Brick 1** (one identity / CUA — one realm, real SSO, roles that
   travel) before the mesh gets heavy.

---

## Missing pieces to discuss
- `// TODO(angel)`: the "other stuff we have to consider" — name them and we fold them in.
- `// TODO(angel)`: where the broker lives — module-in-one-app now → standalone service later? (recommended)
- `// TODO`: do we want a user-facing version of this (so it reads as "one app" to members)?
- `// TODO`: message-type naming convention + where the **partner registry** is stored (DB table? config file?).
- `// TODO`: adapter interface — the contract every adapter implements (`prepare(payload)` / `deliver(payload, creds)`).
- `// TODO`: retry/dead-letter policy + how long a failed message lives in the Console.

---
*Living doc. The bus starts today; the single identity is the foundation we pour before the mesh gets heavy.
Doing PUBLISH_PROFILE now commits us to neither — it proves the pattern. 🐺*
