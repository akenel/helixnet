# RESUME — Born Once / Banco videos (open this first next session)

*Handoff written 2026-06-24 ~08:35 after the all-night → morning video sprint. Season 1 is done.*

## Where we are
- **Season 1 = COMPLETE — 8 episodes.** #01–#07 are LIVE on YouTube (channel WilhelmTell).
  **#08 "Word of Mouth" is APPROVED + packaged, awaiting Angel's publish.**
- We invented + locked the **voice-plus-Puppeteer pipeline**: Angel reads a teleprompter in one
  take; Tigs processes the VO, captures app screens headless, builds the slideshow, cuts the kit.
- The cream (HempSana SALBE) is the season's protagonist — born → proven → raised → restocked →
  watched → counted → remembered.

## IMMEDIATE next actions (in order)
1. **Angel publishes #08** — kit is ready in `videos/banco/born-once-08-word-of-mouth/`
   (title `#08 Word of Mouth — Season 1 finale`, DESCRIPTION/TAGS/CAPTIONS.srt done). Then he drops
   the link → Tigs logs it in the kit + series log. **Season 1 fully live.**
2. **Commit the haul** (when Angel says): the new docs + scripts + #06/#07/#08 kits. (Media stays
   local; commit text only — see prior commits 64face3 / 0c449a3 for the pattern.)

## THEN — Season 2 (the real build, then film it)
**Goal:** the customer feedback loop — QR on the receipt → 10-second product survey (+ optional
photo/clip) → earn loyalty credit → reviews become the product's public reputation → Felix sees
velocity *and the reason behind it*. We're ~85% there (CustomerModel, credits ledger, and the
sale-attaches-a-customer all already exist — verified in code 2026-06-24).

**Read first:** `docs/BANCO-SEASON2-PROJECT-PLAN.md` (workstreams, dependencies, decision register)
and `docs/BANCO-FEEDBACK-LOOP-SPEC.md` (the design).

**3 decisions to lock before building (Tigs' recs in the plan):**
1. `Review` schema — product-anchored, customer-nullable, transaction-optional.
2. Public face: **Path A (page in Banco now)** vs Path B (publish to La Piazza later) → rec: A now.
3. Port La Piazza's item design vs rebuild → rec: port.

**Already decided:** QR-scan spine + Telegram opt-in bonus · any record can review, adding a handle
unlocks the points payout · customers are CRM (`CustomerModel`), never Keycloak.

**Critical path:** build the `Review` model FIRST (everything hangs off it). The **receipt
one-pager cleanup** can run in parallel today (no dependency, and the QR lives there). Build behind
a flag, test on sandbox, then film Season 2 against the real thing.

## ✅ ARTEMIS PREMIUM CUTOVER PLAN — STARTED 2026-06-24
Written → **`docs/BANCO-ARTEMIS-PREMIUM-CUTOVER-PLAN.md`**. The prep for plugging **QR codes** +
the **La Piazza item design** + **Banco/Artemis items** → a premium public face ("Artemis Premium").
**Key finding (audited, not talk): the wiring is ~80% already built.** `create_draft_listing()` in
`square_bridge.py:145` already publishes items into La Piazza (Bottega uses it); `StoreSettingsModel`
already holds Artemis's VAT + company + storefront profile; `create_product()` `pos_router.py:134` is
the lifecycle seam. **Greenfield = small:** a module-toggle column, a `lapiazza_listing_id` column, and
the ONE hard seam — a **business-account identity on the `borrowhood` realm** to publish AS Artemis
(= Angel's "flip the switch → create account → verify email"). **The fork resolved to Path B** (item
rests on La Piazza, reuse the hosted face — no separate Banco page).
**Awaiting Angel** on the 4 open questions in §6 of the plan (business-account-singular? draft-on-create?
one-way-only? QR→La-Piazza-listing?). Then Phase 0 schema → Phase 1 identity → Phase 2 hook.

## The records (so nothing gets re-taught)
- `videos/banco/BORN-ONCE-VIDEO-SOP.md` — end-to-end video procedure (the cycle + capture/build commands).
- `videos/banco/SERIES-BIBLE.md` — the world (cast, cream, customers, season arc).
- `memory/banco-born-once-series.md` — the one-line index.

*Build it true, then film it. That's the whole ethos.*
