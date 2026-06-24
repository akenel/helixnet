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

## NEXT SESSION — start the DESIGN CUTOVER PLAN (Angel's ask 2026-06-24)
Before/alongside the loop build, draft a **cutover plan** for the prep on the design concept:
plugging in **QR codes** + the **La Piazza item design** + **Banco/Artemis items** → a premium
public presentation ("**Artemis Premium**" — the rich, La Piazza-style face for the shop's items).
This is the execution prep for **Path A** (port La Piazza's design into Banco's public product page)
with **Path B** (publish to the La Piazza marketplace) kept open. Deliverable: a phased cutover plan
(what migrates, in what order, behind a flag, with rollback) — write it next session. Pairs with
`BANCO-SEASON2-PROJECT-PLAN.md` (workstream B + the architectural forks A2/A3).

## The records (so nothing gets re-taught)
- `videos/banco/BORN-ONCE-VIDEO-SOP.md` — end-to-end video procedure (the cycle + capture/build commands).
- `videos/banco/SERIES-BIBLE.md` — the world (cast, cream, customers, season arc).
- `memory/banco-born-once-series.md` — the one-line index.

*Build it true, then film it. That's the whole ethos.*
