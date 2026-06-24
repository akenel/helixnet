# Banco Season 2 — Project Plan (the customer feedback loop + the cream's public face)

*The rollout, structured: workstreams, dependencies, what runs in parallel, and a decision register
(decide-now vs flexible · locks-us-in vs keeps-it-open). Pairs with the design spec
`BANCO-FEEDBACK-LOOP-SPEC.md`. Status: PLAN — 2026-06-24.*

> Goal: a customer with only a first name can scan a receipt QR, complete a 10-second product
> survey (optional photo/clip), earn credit, and their words become the product's public reputation —
> which Felix sees tied to velocity.

---

## Workstreams (with dependencies)
| ID | Workstream | Depends on | Parallel? |
|----|-----------|-----------|-----------|
| **A** | `Review` model + migration (review ⇒ product, nullable customer, optional transaction; metadata fields) | — (FOUNDATION) | start FIRST |
| **B** | Public product/survey page (the "face"), tokenized, no login | A | after A; parallel with C |
| **C** | Award-credit + set-favourite wiring (reuse existing ledger + `favorite_products`) | A | parallel with B |
| **D** | Reputation block on the product (count, ⭐, words, media) | A, B | after B |
| **E** | Receipt **one-pager cleanup** + survey QR | — (cleanup) / A (QR token) | **cleanup starts NOW in parallel**; QR waits for A |
| **F** | Media upload (photo + short clip, configurable caps) | A, B | after v1 (deferrable) |
| **G** | Metadata capture (who/when/where/how, time-to-complete) | A | **bake into A/B from the start** |
| **H** | Felix dashboard: velocity **+ reason** | A | after A; parallel |
| **I** | Telegram push (opt-in members only) | A, bot | deferrable bonus |
| **J** | Publish items to La Piazza marketplace (Path B) | identity/realm consolidation | **deferred epic** |

## Critical path
**A (Review model) is the bottleneck** — almost everything hangs off it. Get A right, then B/C/D/H
fan out in parallel. **E's receipt cleanup is the one thing we can start TODAY** with zero
dependency (and we need it anyway — the QR lives there).

## Decision register
### Decide NOW (needed to start) — and these LOCK things
1. **Review schema core** — review belongs to: **product (required) · customer (nullable, for
   anonymous) · transaction (optional)**, plus answers + media refs + metadata. *Migratable but
   semantics are semi-locking — get it right once.* → my rec: as stated.
2. **Public face location — the big architectural fork:**
   - **Path A (now):** the public page lives **in Banco**, wearing La Piazza's design. Ships with the
     loop, no cross-repo lift. *Keeps Path B open.*
   - **Path B (later epic):** publish items to the **La Piazza marketplace** (real accounts, the
     Square). *Bigger — needs identity/realm consolidation; a heavier door.*
   → my rec: **Path A now, Path B as a deliberate epic.** (Staged — nothing is foreclosed.)
3. **Design reuse:** **port La Piazza's item templates/CSS** into Banco vs rebuild the look.
   → my rec: **port** (don't redraw what's perfected). *Reversible.*

### Already DECIDED (locked 2026-06-24)
- Channel: **QR-scan spine, Telegram opt-in bonus.** Instagram = identity/reach, not a push API.
- Gating: **any record can review; adding a handle unlocks the points payout** (gentle upsell).
- Identity: **customers are CRM (`CustomerModel`), never Keycloak, never the till.** *(This one is a
  deliberate one-way door we're choosing to keep CLOSED — putting customers in Keycloak would lock us
  into auth complexity we don't want.)*

### FLEXIBLE — defer, keep wide open (two-way doors, don't agonize)
- Exact survey questions (iterate freely).
- Media size/length caps (config: start ~photo 10MB / clip 25MB ~30s).
- Credit amounts per action (rules already config-driven).
- Page/card styling.
- Q&A / discussion threads (the fuller "forum") — v2 of the public face.
- Telegram bot specifics; moderation workflow details.

## Architectural decisions (the forks that matter)
- **A1 — Customers ≠ auth accounts.** CRM record + token, not Keycloak. *(closed door, on purpose)*
- **A2 — Public face: Banco-hosted now, La Piazza-published later.** *(staged — open)*
- **A3 — Review is product-anchored, customer-optional.** Enables anonymous reviews + later
  attribution when a handle is added. *(semi-locking — decide with A)*
- **A4 — Media stored off the app DB** (path/object ref on the Review), transcode/moderate async.
  *(open)*

## Suggested execution order (phased)
- **Phase 0 (parallel, start now):** E receipt one-pager cleanup (no dependency) + finalize A's schema.
- **Phase 1:** A (model+migration, with G metadata baked in).
- **Phase 2 (parallel):** B (public page) ‖ C (credit/favourite) ‖ H (Felix velocity+reason).
- **Phase 3:** D (reputation on product) → E's QR token onto the cleaned receipt.
- **Phase 4 (optional):** F media · I Telegram.
- **Epic (separate):** J La Piazza publishing.
- **Then:** film Season 2 against the REAL thing.

*Everything behind a feature flag; test on sandbox; build true, then film.*
