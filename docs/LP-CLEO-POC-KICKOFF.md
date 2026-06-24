# Cleo Concierge — PoC Kickoff Brief

**Self-contained.** Safe to paste into a fresh session after a compaction. Companion to
the full design: `docs/LP-CLEO-LEVERAGE-WORKFLOW.md` (the ten Lego blocks).

**Decisions locked (2026-06-18):**
- **Scorecard is IN the PoC** (auto-runs on the draft — not a stretch goal).
- **Hand-off = prefilled deep-link** into La Piazza's existing post flow. Built
  **forward-compatible**: Cleo emits a structured listing **payload**; the deep-link
  consumes it now, and a **server-to-server POST consumes the identical payload later** —
  no rewrite. (Same trick as resources-as-cards.)
- First slice = **service**. Front door = `find-your-edge`. Design = **prompt-only**.

---

## The one-liner
Prove, end-to-end, that **Cleo reads who you are, looks at the cards on the table, and
walks you into the one recipe that helps you most — pre-filled, in a mentor's voice — then
you post it through La Piazza's flow that already works.** First slice = **a service**.

## What this PoC proves (and why it's worth doing)
- That the **bridge** works: Cleo → a routed, pre-filled recipe → a real post. This is the
  only genuinely new muscle; everything else we reuse.
- That Cleo is **catalog-aware and dynamic**: she reasons over the live deck of recipes,
  so when we add a service next week she can already suggest it — no retraining.
- It removes the friction for the "lazy / not-sure-what-to-post" person: she does the
  thinking and the typing; they react.

## Success criteria (demoable)
A new-ish member with a thin profile can, in one sitting:
1. Get a **read** from Cleo (via `find-your-edge` as the front door).
2. Receive **one concrete move** + a recipe choice + **pre-filled inputs** + the *why* +
   "try it 2–3×, then report back" — in the masters' "one thing today" voice.
3. Run that recipe and get a usable **service draft**.
4. The **scorecard** auto-runs on the draft and says "good — post it" or "fix these N things."
5. Hand off to La Piazza's existing list flow **pre-filled** (deep-link) and **post it live**.

---

## Cleo's new job: the catalog-aware concierge (the core build)

**Inputs she reads (all are "cards" = Service Interfaces):**
- **The person's card** — profile + their `find-your-edge` output (their leverage, why
  they're good, what they have / don't).
- **The recipe deck** — the live menu. Each recipe already exposes
  `slug, title, category, inputs, outcome, steps, blurb`. We **add one field per recipe —
  `cleo_hint`** (a plain-language "what it's for / when to suggest it / what it pairs
  with") so her suggestions are grounded in data, not guessed.
- **(Later phases) Resource cards** — live compute/hardware (e.g. "Larry's GPU, Blender,
  online, +N credits"), and masters as design-prompt sources.

**What she outputs (the mentor voice):**
> "Here's the one move for today: run *X*. Put this in (pre-filled), because <reason>.
> Look for <this and that>. Run it two or three times, keep the best, then bring it back
> to me and I'll take you further."

**Why dynamic falls out for free:** she reads the deck at *runtime*. Add a recipe → it's
in the menu → `cleo_hint` tells her what it's for → she can recommend it immediately.
"This one's new in the deck; here's what you'd use it for." No retraining, ever.

---

## Architecture & reuse map (don't reinvent)

| Block | Reuse (exists) | New in this PoC |
|------|-----------------|-----------------|
| Read / Suggest | `find-your-edge` recipe | use it as the front door |
| Cleo concierge | `reception.py` (person→master today) | a concierge step: read profile + deck → recommend move+recipe+prefill+why, mentor voice |
| Recipe cards | `recipes.py` menu | add `cleo_hint` field per recipe |
| Route / pre-fill | recipe runner | pass Cleo's pre-filled inputs into the recipe |
| Assist (service draft) | `product-posting` (or a `service-posting` variant) | minor: a service-shaped recipe |
| Post | onboarding → `POST /api/v1/items` (verified live on staging) | prefilled deep-link hand-off (payload-shaped for later server-to-server) |
| Scorecard (in PoC) | judge pattern (#149), the video scorecard | a Cleo "hat" that auto-grades the draft: "good — post it" / "fix these N" |

**Where the model call happens:** `src/llm/` (`run_llm` / `ModelTarget`) — the one place.
Cleo's recommendation is just a recipe-shaped LLM call over the deck + the person's card.

---

## Scope OUT — deferred, on purpose (so the PoC stays small)
- **Live resource brokering** ("Larry's GPU is online, +N credits… now he's offline, here
  are other options") → **Phase 3.** Designed-for now: resources are just another *card*
  Cleo reads, so when the live registry (LPCX worker exchange) exists she gains it without
  a redesign.
- **Image generation** beyond prompt-only → **Phase 2** (BYO-key) / **Phase 3** (our GPU
  on credits). PoC ships **prompt-only**: the design recipe outputs a master-grade,
  portable prompt the person pastes into any maker (DALL·E / Nano Banana / ChatGPT).
- **Attachments / screenshots / reference images** to feed the prompt (a magazine photo of
  a thing they liked) → **Phase 4–5.** Cleo does not ingest images in the PoC.
- **Server-to-server auto-posting** → later. PoC uses the prefilled deep-link, but Cleo's
  output is a **structured payload** so the server-to-server path is a drop-in later.
- **Deep SWOT / anti-copycat scorecard** → the auto "good — post it / fix these N" grade
  **is in the PoC**; the full strategy SWOT (copycat/pricing defensibility) comes after.

## Phase ladder (the whole arc, for orientation)
1. **PoC (now):** catalog-aware Cleo → pre-filled service recipe → auto scorecard →
   prefilled deep-link into the existing post flow; prompt-only design.
2. **BYO-key images** — they paste their own provider key; image returns into the flow.
3. **House / BYOH GPU** — Stable Diffusion / Blender on a member's machine, brokered with
   credits; Cleo surfaces live resource cards (Larry's box) + fallbacks.
4–5. **Reference attachments** — screenshots / magazine pics enrich the prompt; richer
   scorecard SWOT; share-out polish.

---

## Suggested build order (small steps, human-green between)
1. Add `cleo_hint` to each recipe card in `recipes.py` (data only).
2. Add a **service-shaped recipe** (or confirm `product-posting` covers a service draft).
3. Build the **concierge step**: input = person card + deck; output = {move, recipe_slug,
   prefilled_inputs, why, technique, "report back"} in the mentor voice. (One LLM call.)
4. Wire **front door**: `find-your-edge` result feeds the concierge.
5. Build the **scorecard** Cleo-hat: auto-grade the draft → "good — post it" / "fix these N".
6. Wire **hand-off**: Cleo emits a **structured listing payload**; deep-link it into La
   Piazza's list flow, pre-filled. (Keep the payload clean so a later server-to-server
   `POST` consumes the same shape.)
7. Verify on **staging** end-to-end; run the smoke + console-sweep gates before showing Angel.

## Decisions resolved (was "open")
- **Hand-off:** ✅ prefilled deep-link now; payload shaped so server-to-server is a drop-in later.
- **Scorecard:** ✅ in the PoC (auto-runs).
- **Service recipe (still to confirm at build):** reuse `product-posting` for the draft,
  or add a `service-posting` variant? (Small — decide when we open the code.)

## Test gate (from house rules)
- Run on **staging only** until Angel signs off (never straight to prod).
- `scripts/smoke-test.sh staging` + `tests/e2e/console-sweep.js` before handing it over.
- The post-flow verifier (`BorrowHood/scripts/verify_post_flow.py`) is bearer-based and
  trips on cookie-session auth; do a **browser-driven** check for the live post.
