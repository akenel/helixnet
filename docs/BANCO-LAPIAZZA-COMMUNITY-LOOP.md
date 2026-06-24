# Banco ⇄ La Piazza — The Community Loop

*Written 2026-06-24. The LOCKED strategy for how the Banco POS (the till) and La Piazza (the
community square) connect. Stop re-deriving this — decisions here are settled; only the build
order is open. Supersedes the "build a Community Catalog inside Banco" idea in
`BANCO-CRM-STRATEGY.md` Phase 4 (we reuse La Piazza instead). Pairs with
`BANCO-ARTEMIS-PREMIUM-CUTOVER-PLAN.md` (the publish bridge) + `BANCO-CRM-STRATEGY.md` (loyalty).*

---

## 1. The thesis, in one breath

**Banco is the funnel. La Piazza is the destination.**

A shop's handpicked special items — plus a QR on every receipt — are *bait* that pulls real people
into the community, where they discover they can do their **own** thing (sell their cookies, teach
growing, run a raffle). Banco *acquires* the customer at the till; La Piazza *keeps* them. The shop
gets reviews + loyalty + repeat business; the community gets supply, content, and new members.

We are **not** selling on La Piazza. La Piazza is where things get **talked about** — reviewed,
upvoted, gathered around. Buying happens in-store / offline, exactly as it does today.

---

## 2. Division of labor — keep each app to its job

| App | Its job | Does NOT do |
|---|---|---|
| **Banco / POS** | catalog · sale · **loyalty (customer + points + tiers)** · reporting · roles | community, reviews, hosting a marketplace |
| **La Piazza** (the square) | display · **comments · reviews · upvotes** · discovery · postcard/promo · the member's own listings | take money / run a checkout |
| **The bridge** (built) | carry ONE handpicked item from the till → the square as a *showcase* | continuous sync (push-once-then-decouple) |

A till is a till. The square is the square. **We do not duplicate either one** — the whole point is
to tie the apps we already have on the Helix platform together, not rebuild + re-host community code
inside the POS (which would make the POS heavier than it should ever be).

---

## 3. The flow (the growth engine)

```
Felix HANDPICKS a few special items
   → pushed to La Piazza as a DISPLAY listing (showcase — discuss, not buy)
   → a buyer at the till gets a receipt with a QR
   → scans it → "Join La Piazza to comment on this"
   → signs up (email confirm) → comments / reviews / upvotes
   → earns CREDITS → redeems them at the till (next purchase)
   → and while they're there: "wait… I could put my edible cookies here. I could teach growing.
      Maybe this is the community for me." → becomes a member → tells Sally + Larry.
```

The receipt QR is the seed. The community is the soil. Commerce funds the community; the community
feeds commerce.

---

## 4. Two ladders, one currency (the points loop)

From `BANCO-CRM-STRATEGY.md` — the unifying frame:

- **Ladder 1 — commerce:** buy at the till → earn credits → climb spend tiers (Bronze/Silver/Gold).
  **✅ BUILT** (CRM Phase 0, Angel-passed on staging: enroll-by-name, attach-to-sale, earn, tier,
  history, receipt).
- **Ladder 2 — community:** review / upvote / contribute on **La Piazza** → earn the **same**
  credits. **NOT built** — this is the new frontier this doc unlocks.
- **One wallet, one place to spend it:** credits redeem at the Banco till.

The no-money customer who only contributes (reviews, upvotes) still earns status + credits → free
content + a flywheel. That's the strategic core, not an afterthought.

---

## 5. Decisions — LOCKED

| # | Decision | Rationale |
|---|---|---|
| L1 | **Reviews/community live on La Piazza, NOT rebuilt in the POS** | Already built there; keeps the POS lean; one community, one place |
| L2 | **Listings are SHOWCASE, not for sale** — no Buy button; "talk here, buy in-store, message the shop" | La Piazza doesn't transact; sidesteps the public-CBD-sale legal exposure; matches "get involved," not "checkout" |
| L3 | **Felix HANDPICKS what goes up** (the ~1% worth a conversation) | Velocity + curation; papers/lighters never go; avoids flooding the square with junk |
| L4 | **The receipt QR is the on-ramp** — scan → join La Piazza → comment | Turns every sale into a community-acquisition event |
| L5 | **The buyer's La Piazza member ↔ their Banco customer get LINKED** | So a review on the square pays credits to the right till wallet (two ladders, one currency) |
| L6 | **Credits are the one shared currency**, earned from both ladders, spent at the till | Already the CRM model ("two ladders, one currency") |

---

## 6. What's already built (REUSE — zero rebuild)

- ✅ **The publish bridge** — Banco product → La Piazza listing under the verified shop, with photo +
  shop logo, decoupled. (`src/services/lp_publish.py`, proven; token-exchange done for prod.)
- ✅ **La Piazza reviews / upvotes / comments** — BorrowHood, live.
- ✅ **The loyalty engine** — customer (enroll-by-name, no login needed), credits ledger, spend tiers,
  purchase history, receipt member block. (CRM Phase 0, Angel-passed.)
- ✅ **The receipt** — exists; just needs the QR added.

**The heavy lifting is done.** What remains is connective tissue, not a platform.

---

## 7. The FOUR WIRES (all that's new)

1. **Showcase listing type** *(La Piazza side)* — a display listing with **no Buy button** ("discuss /
   buy in-store / message the shop"). Small one-time BorrowHood addition (like the health-wellness
   category fix). The Banco publish then maps handpicked items to `showcase` instead of `sell`.

2. **Receipt QR → join-La-Piazza on-ramp** — a QR on the receipt that opens La Piazza with a "join to
   comment on this" hook. Uses a **Banco-owned permalink** (`banco.lapiazza.app/p/{product_id}`, R3)
   so the code is known at sale time regardless of publish state, and 302s to the listing (or a "this
   shop on La Piazza" / join page if the item isn't showcased).

3. **Identity link** *(Banco customer ↔ La Piazza member)* — when a buyer joins La Piazza from the
   receipt QR, tie that new member to the Banco customer (DB row) the sale was rung under. The one
   real cross-system integration; it's the North Star (`HELIX-IDENTITY-ARCHITECTURE.md`) paying off.
   Note: a Banco member is a DB row (no login); becoming a La Piazza member is the optional login
   upgrade — the link is what makes "review here → credit there" possible.

4. **Credit event** *(La Piazza contribution → Banco wallet)* — a La Piazza review/upvote/approved
   contribution emits an event that awards credits to the linked Banco customer's ledger (the value
   ladder + anti-junk gates are already settled in `BANCO-CRM-STRATEGY.md`: pay for value not volume,
   Verified-Buyer-gated, daily caps, staff/trusted-CRACK approval). Depends on wire 3.

**Dependencies:** wire 1 is independent. Wires 2 + 3 are the on-ramp pair (the QR establishes the
link). Wire 4 needs wire 3 (identity) first. So the natural order is **1 → 2+3 → 4**, but the build
order is the open question to decide next.

---

## 8. Deferred / open (not blocking)

- Automated "these product types never showcase" rules (start handpicked; automate later).
- Whether the showcase needs its own visual treatment on La Piazza vs. a flagged normal listing.
- Self-claim sign-in beyond email magic-link (Google/Meta) — per `BANCO-CRM-STRATEGY.md`.
- The legal sign-off on showcasing CBD-adjacent items publicly (showcase-not-sell lowers it, but
  confirm — see the members-club/smoking legal briefs).

---

## 9. Related docs
- `BANCO-ARTEMIS-PREMIUM-CUTOVER-PLAN.md` — the publish bridge (the connective tissue).
- `BANCO-CRM-STRATEGY.md` — the loyalty engine + the contribution economy (the credit rules).
- `HELIX-IDENTITY-ARCHITECTURE.md` — the one-account North Star (wire 3 stands on it).
- `TODO-BORROWHOOD-HEALTH-WELLNESS-CATEGORY.md` — the pattern for a La Piazza-side taxonomy add (wire 1).

*Don't reinvent the wheel. Everything heavy already exists — we connect four dots and people walk
from the till into the square.*
