# Artemis Premium — Cutover Plan (Banco item → La Piazza listing)

*Started 2026-06-24. The prep for plugging QR codes + the La Piazza item design + Banco/Artemis
items into a premium public presentation. Angel's framing: "it's more a wiring issue, not the
product itself." This plan proves that true — and shows the wire is ~80% already in the wall.*

> **Read with:** `docs/BANCO-SEASON2-PROJECT-PLAN.md` (the feedback loop this feeds) and
> `docs/BANCO-FEEDBACK-LOOP-SPEC.md` (QR → review → reputation). This doc is **workstream B**
> of that plan, promoted to its own cutover because it's the public-face foundation.

---

## 1. The thesis (Angel, 2026-06-24)

A head shop is ~98% consumables / one-offs — there's no real "service." The *type* of offer
(sell, raffle, rent…) stays **flexible, not fixed**. What matters for a proof-of-concept is the
**wiring**: making an Artemis item exist inside La Piazza, under an account.

The mechanism, in his words:
1. Artemis already has a Banco account with **configuration data** (like a "printing module").
2. Add a switch: *"Enable the La Piazza module? Tie it to your business?"*
3. "Business account" = **VAT number + business name + a verifiable email** (suggest the one on
   file). On approval, behind the scenes → account created → they verify the email.
4. Roles don't matter — they're **a normal La Piazza user that happens to be a business.**
5. Payoff = Artemis appears as a **verified business** (address, go visit, shop link, maybe an
   online shop). It's their **advertisement.**
6. The item Felix sold to Larry & Sally then **comes to rest on La Piazza, public, hosted like
   every other item** — dressed in the premium design + QR.
7. It's **one extra step in the item's lifecycle.** The service interface, working.

**This resolves the old Path-A-vs-B fork: it's Path B.** The item rests on *La Piazza*, not on a
separate Banco page. We reuse the public face we already host instead of building a second one.

---

## 2. Reality check — what's already built (audited 2026-06-24)

The "is it just talk?" pass. Honest status of every piece the mechanism needs:

| Piece the plan needs | Status | Evidence |
|---|---|---|
| Per-shop **configuration store** (VAT, company info, storefront profile: hours/socials) | **BUILT** | `src/db/models/store_settings_model.py:23`; GET/PUT `/pos/settings/{store_number}` in `pos_router.py` |
| A **module toggle** field on that config | **GREENFIELD** (1 column + schema) | no `enabled_modules` / feature-flag anywhere |
| **Product create** (the lifecycle seam) | **BUILT** | `create_product()` `pos_router.py:134`; `quick_create_product()` `:159` — hook goes right after commit |
| **Cross-repo bridge to La Piazza** (write-side) | **BUILT, in prod** | `square_bridge.py:145` `create_draft_listing(user_token, d)` → posts `/api/v1/items` + `/api/v1/listings`; **already used by Bottega** `bottega_router.py:724` |
| Bridge **connectivity/config** | **BUILT** | `config.py:141` — `SQUARE_API_URL`, `SQUARE_ASYNC_URI`, `SQUARE_PUBLIC_URL=https://lapiazza.app` |
| Read-side profile bridge (display_name/slug/workshop/city) | **BUILT** | `square_bridge.py` `get_square_profile()` |
| `lapiazza_listing_id` on the Product (to track + later update/unpublish) | **GREENFIELD** (1 column) | `product_model.py:16` has no such field |
| **Identity to publish AS Artemis** — a La Piazza (`borrowhood` realm) account | **GREENFIELD** — *the real seam* | Banco/Artemis log in on `kc-pos-realm-dev`; the bridge needs a `borrowhood` token |

**Verdict: ~80% of the wire exists.** The greenfield is small and precise — two columns and the
identity bridge. **The one hard seam is identity**, and it *is* exactly Angel's "flip the switch →
create the business account → verify the email."

---

## 3. The cutover — phased, with parallel/sequential called out

Cutover discipline: every step lands **behind the `lapiazza_enabled` flag (default OFF)**, is
tested on **sandbox**, and has a **rollback**. Banco stays the source of truth; the La Piazza
listing is a **mirror** that can always be torn down.

### Phase 0 — Decide & schema (do first; small, unblocks everything)
*Sequential — this is the foundation.*
- **D-decisions locked** (§4 below).
- Add to `StoreSettingsModel`: `lapiazza_enabled: bool = False` and a `lapiazza_business_id`
  (nullable — the linked La Piazza account once provisioned). Additive migration.
- Add to `ProductModel`: `lapiazza_listing_id` (nullable str) + `lapiazza_slug`. Additive.
- **Rollback:** columns are nullable/defaulted off — a no-op until used.

### Phase 1 — The business-account bridge (the hard seam; critical path)
*Sequential — everything publishes AS this account.*
- The switch flip provisions an **Artemis business identity on the `borrowhood` realm** from data
  we already hold: **VAT + business name + the email on file** (suggested, must be verified).
- Mint a token to publish as that identity. **Simplest-primitive PoC path:** a service/business
  account on `borrowhood` (we already read/write that DB + API). Token-exchange is the prod-grade
  version later — keep it open, don't block the PoC on it.
- Store `lapiazza_business_id` back on `StoreSettings`.
- **Rollback:** flag OFF → no provisioning; an already-provisioned account simply goes unused.

### Phase 2 — The lifecycle hook (the "one extra step")
*Sequential after Phase 1.*
- After `create_product()` commits, **if `lapiazza_enabled`**: map product → listing fields and
  call `create_draft_listing(business_token, d)`. Item lands as a **DRAFT** (invisible until
  published — reuses the existing draft status, the same gentle pattern as Cleo/Bottega).
- Store the returned `listing_id` + `slug` on the product.
- **Field map** (Product → listing): `name→name`, `description→description`, `price→price`,
  `category→category`, `image_url→cover_url`, `item_type="good"` (head-shop default; NOT the
  bridge's "service" default), `currency="CHF"`, `content_language="en"`.
- **Rollback:** failure is swallowed + logged (bridge already does this) — a publish hiccup never
  blocks a sale. Flag OFF stops all new publishes.

### Phase 3 — Verified-business face + premium item design (the payoff)
*Parallel-capable, but lives partly in the La Piazza repo → needs coordination.*
- La Piazza renders Artemis as a **verified business**: name, VAT, **address (go visit)**, hours,
  socials, shop link — sourced from the business account + the StoreSettings storefront profile.
- Item listing wears the **premium design** (the La Piazza item template we built for the postcard
  items) — this is the "Artemis Premium" look.
- **QR on the receipt → the listing's `view_url`** (`/items/{slug}`). This is where the cutover
  meets Season 2: the QR points at the resting item, and reviews/reputation accrue **on the
  listing**. (Confirm review-anchor decision in the Season-2 plan.)
- **Rollback:** premium face is render-only; revert to plain listing template.

### Phase 4 — Publish & watch (PoC go-live)
- Flip Artemis's flag ON in sandbox, create the HempSana cream, watch it come to rest on La Piazza
  as a draft, publish it, scan the QR, see it. **That's the PoC.** Then film it (Season 2).

---

## 4. Decision register — decide-now vs flexible

### Locks us in (decide now)
| # | Decision | Recommendation | Why it locks |
|---|---|---|---|
| D1 | Public face = **La Piazza listing** (Path B), not a separate Banco page | **Path B** | Reuses hosted face; commits to `borrowhood` as the public home |
| D2 | Listing owner = **business account** (VAT+name) vs the manager's personal La Piazza login | **Business account** | Items rest under *the shop*, not a person; matches "as a business" |
| D3 | Identity realm for the business account = **`borrowhood`** | **Yes** | It's where items + the bridge already live |
| D4 | Publish trigger = **draft-on-create**, manager publishes | **Draft-on-create** | Safe, invisible until ready; reuses existing draft status |
| D5 | Sync direction (PoC) = **one-way create only** (no price/stock sync back) | **One-way** | Keeps PoC small; Banco stays source of truth |

### Keeps it open (flexible, decide later)
- Offer **type** beyond a plain good — raffle / rent / service (Angel: "anything is possible, not
  fixed"). The `item_type`/`listing_type` fields already carry this.
- **Auto-publish** (skip the draft step) once trust is there.
- **Two-way sync** — price/stock/soft-delete propagation Banco ↔ listing.
- **Online shop / purchase on La Piazza** (vs. advertisement-only).
- **Token-exchange** as the grown-up replacement for the PoC service token.
- **Review anchor** — on the La Piazza listing (leaning) vs. a Banco reputation block. Settle in
  the Season-2 plan; the QR target follows it.

---

## 5. Dependencies at a glance

```
Phase 0 (schema + decisions)
        │  (critical path)
        ▼
Phase 1 (business-account identity on borrowhood)  ◄── THE HARD SEAM
        │
        ▼
Phase 2 (lifecycle hook → create_draft_listing)
        │
        ├──────────────► Phase 3 (verified-business face + premium design)  [La Piazza repo — coordinate]
        ▼
Phase 4 (flip flag in sandbox → publish → QR → watch)  ──► feeds Season 2 reviews
```

Parallel-today (no dependency): the two additive columns (Phase 0) and Phase 3's premium item
template can be designed while Phase 1 identity work proceeds.

---

## 6. Decisions — LOCKED (Angel, 2026-06-24: "yes to all four")
1. **One shared business identity** per shop publishes everything. ✅
2. **Draft-on-create** — owner publishes on La Piazza. ✅ (+ optional `lapiazza_autodraft` override)
3. **One-shot create, then DECOUPLE** (refined — see §7). ✅
4. **Receipt QR → the La Piazza listing**, via a Banco-owned permalink (see §7). ✅

---

## 7. Refinements from the 2026-06-24 architecture talk

**R1 — Environment parity is a hard rule.** Banco-env publishes to the *matching* La Piazza-env:
sandbox/staging Banco → **La Piazza staging** (`staging.lapiazza.app`, realm `borrowhood-staging`,
DB `borrowhood_staging`); prod Banco → **La Piazza prod** (`lapiazza.app`, realm `borrowhood`).
The "business account" literally signs into that env's La Piazza. **Achievable today** — all targets
are env-overridable (`SQUARE_API_URL`/`SQUARE_PUBLIC_URL`/`SQUARE_DB` in `config.py:141`), and
staging fully exists. **⚠ LANDMINE FOUND:** `hetzner/docker-compose.banco-prod.yml` currently points
prod Banco at **staging** La Piazza (`borrowhood_staging`). Inert today (nothing publishes yet) but
**MUST be fixed before any prod publish** or prod listings orphan into staging. → fix in Phase 1.

**R2 — Push-once, then decouple (NOT continuous sync).** The push seeds a **draft**; once the owner
publishes/maintains it on La Piazza, Banco stops touching it. Banco stays the source of truth *at the
counter*; the listing becomes the owner's to edit/copy/delete however they like. A re-push = a **new
product/listing**, not an update. This deliberately dodges the hardest integration problem
(bidirectional sync + conflict resolution) — we never reconcile "Banco says 45, owner edited to 40."
The `products.lapiazza_*` columns just record *that* it was seeded + where.

**R3 — The QR is the whole connection → so Banco must OWN the QR's target.** The QR can't point raw at
the La Piazza slug, because (a) a fresh push is a *draft* (not public yet at receipt time), and (b)
decouple means the owner may delete/recreate → the slug changes → a raw QR dies. **Recommendation:**
the QR encodes a **stable Banco permalink** (e.g. `banco.lapiazza.app/p/{product_id}`) that 302-redirects
to the live La Piazza `/items/{slug}` when published, else shows a graceful "coming soon / leave a review"
page. *We* host the connection (Angel's point), La Piazza hosts the destination — and publish-state,
re-creates, and even a Path-A fallback all hide behind one permanent URL. **This is the load-bearing
design choice of the whole cutover.**

**R4 — The business account = a normal Keycloak user.** Flipping the switch provisions a standard
`borrowhood`(-env) Keycloak user with the SAME rights as any member (no special role) from VAT +
business name + the email on file (suggested, must be verified). They can sign in and use La Piazza
like anyone. We hold a credential/token to push drafts in the background.

**R5 — The drafting dashboard.** A place in Banco's catalog to push drafts: **manual per-product push
by default**, with the `lapiazza_autodraft` override to auto-seed every new product as a draft. Publish/
activate always happens on the owner's side in La Piazza. No new publishing UI to build on the La Piazza
side — we reuse its listing management.

**R6 — La Piazza is for the world, not Artemis-only.** No "Artemis La Piazza" needed — any verified
business lists its goods on the one public square. Artemis is just customer #1 of a general capability.

---

*Build it true, then film it. The wire's already in the wall — we just need the switch.*
