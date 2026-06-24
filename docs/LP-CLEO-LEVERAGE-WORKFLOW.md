# La Piazza — Cleo Leverage Workflow (Lego Blocks)

**Status:** DRAFT for review. Nothing is built yet. We agree on the blocks first.

**Decisions locked (2026-06-18):**
- Connoisseur = **a hat Cleo wears** (not a separate persona).
- Scorecard **runs automatically** after the draft.
- First slice to build end-to-end = **service**.

**The one-line:** Cleo reads who you are, suggests a leverage move you can actually do,
the AI does most of the typing, a Connoisseur grades it (and tells you when to stop),
then it posts through La Piazza's existing flow and turns into something you can share.

**Three rules this honors:**
- Leverage, not a jump — use what the person already has.
- Reuse, not reinvent — La Piazza's post flow already works; Bottega feeds it.
- No junk — every run ends in something good enough to be proud of, or it doesn't post.

---

## The blocks (end to end)

```
        BOTTEGA  (the on-ramp + the brain)                         LA PIAZZA  (the storefront)        OUT
  ┌───────────────────────────────────────────────────────┐   ┌──────────────────────────┐   ┌──────────────┐
  │ 1.DOOR → 2.READ → 3.SUGGEST → 4.ROUTE → 5.ASSIST →     │   │ 8. POST                  │   │ 9. SHARE     │
  │                                  6.SCORECARD ⇄ 7.IMPROVE│──▶│   (existing list flow,   │──▶│  WhatsApp /  │
  │                                       (Connoisseur)     │   │    prefilled, you click  │   │  Telegram /  │
  │                                                         │   │    Post)                 │   │  YouTube)    │
  └───────────────────────────────────────────────────────┘   └──────────────────────────┘   └──────────────┘
                              │
                              └────────────▶ 10. BLUEPRINT RECORD  (every run logged + reviewable)
```

### Block 1 — DOOR
Person arrives (often from a shared link) and creates an account, or is already in.
First run is special: it's their first taste, so it has to feel like a win, fast.
- **Have:** login (Google/FB/GitHub), account creation.
- **New:** mark "first run" so Cleo treats it as onboarding, not a cold menu.

### Block 2 — READ (Cleo reads the profile)
Cleo looks at what we know: skills, assets, life-stage, language, location.
Leverages **what they have**, and is honest about **what they don't** (gaps = where she
points them next, never a put-down).
- **Have:** `reception.py` already matches a person → a master/House from their record.
- **New:** read the same record for a *leverage move*, not only a master.

> **WE ALREADY HAVE BLOCKS 2–3 — it's the `find-your-edge` recipe.** It grounds in the
> person's own words, names their edge with evidence, then ends with "Where to Point It"
> (3 directions) + "On La Piazza — one House + one recipe to try next." That IS read →
> suggest. We've under-used it as a standalone toy. Make it the **front door**: its "one
> recipe to try next" becomes a real **routed, pre-filled hand-off** (Block 4), not a
> mention. `find-your-edge` = who you are (identity); `leverage-plan` = turn it into income
> (action). They chain: edge → move → recipe → post. Don't build new suggestion logic —
> extend the recipe we have.

### Block 3 — SUGGEST (the leverage move)
Cleo proposes ONE concrete move and asks "want suggestions?" — the anti-coach to
"figure it out yourself." She picks the **output type** that fits the person:
- an **item** (sell what you own) · a **service** ("I'll decorate / I'll teach")
- **made-to-order** ("Sally's cookies") · a **space** · an **event** · a **raffle**
- a **giveaway** · or a **help-board question** ("who near me can help / needs this?")
- **Have:** all of these are already real types in the marketplace.
- **New:** Cleo converges to ONE and names why it fits *this* person. (Don't scatter 10.)

### Block 4 — ROUTE (Cleo walks them in — she doesn't just point)
This is what turns Cleo from greeter into guide (the anti-coach: she doesn't say "figure
it out" and leave). She:
1. **Picks the recipe** and **pre-fills the inputs** from the profile — no blank box.
2. **Explains the why** — "run *Find Your Edge* now; here's what to put, and here's why."
3. **Coaches the technique** — "run it two or three times, compare, keep the best."
4. **Sets the round-trip** — "come back to me with your results."
   → The output RETURNS to Cleo; she reads it and picks the next move. Recipes become
   steps in a conversation she holds, not dead-ends. (Feeds Block 10's record.)
- **Kills two problems at once:** the blank-box / lazy-user problem (she fills it, you
  react) and the going-in-circles problem (she sets the rep count + when to return).
- **Voice (reuse a proven pattern):** the `mentor-session` masters already close with
  "ONE small action you can take today" — people love it. Cleo wears the SAME voice: one
  doable move, the prompt, "how I'd do it and why, look for this and that, try it 2-3×,"
  then **continuity of care** — "report back and I'll get you further." The master gives
  one move and leaves; Cleo gives one move and keeps the door open. Anti-rejection as habit.
- **Have:** the recipe chassis (`recipes.py`); `find-your-edge` as the first routed recipe.
- **New:** Cleo selects + pre-fills + explains + sets the rep count + reads the returned result.

### Block 5 — ASSIST (the slick part — AI does the typing)
The person types a *little* about the thing. The AI pumps out a decent draft —
title, description, price, deposit, tags, story. Not perfect, maybe a touch generic,
**but they have a posting in seconds instead of a blank page.**
- **Have:** `POST /ai/smart-listing` already returns the whole listing.
- **Change:** image source = **Unsplash** (Pollinations now charges — drop it).

### Block 6 — SCORECARD (the Connoisseur grades it) — A CHASSIS FEATURE, NOT JUST LISTINGS
This rides on **every recipe**, the same way `outcome` and `steps` already do — define it
once, every recipe inherits it. Every output (CV, cover letter, listing, event, cookies)
ends with a certification: **"this is tuned up, done properly, everything checked off."**
Two layers:
- **Universal (every recipe):** a completeness + quality check — is it properly filled
  out, nothing left blank, good enough to be proud of? A clear grade + a short
  "fix these N things" list. *Why it matters:* people are lazy — the AI does the 80%
  they won't, and the scorecard catches the gaps they'd skip. We make it easy, so the
  floor of quality rises across the whole shop.
- **Listing-specific add-on:** a quality + *strategy* critic — the **SWOT**: 
- **Strengths** — what's working.
- **Weaknesses** — "this is weak here; add a photo / a price reason."
- **Opportunities** — how to make it stand out.
- **Threats** — *the copycat problem*: "this is easy to copy; a cheaper maker can
  clone it. Make it complex enough that copying costs them the same effort, and give
  your price a reason." (Defensibility, not just polish.)
- **The STOP verdict (important):** when it's good enough, the Connoisseur says
  **"post it now."** No going in circles chasing a perfect item you already have.
- **Have:** the judge pattern from the reception eval (#149); the video had a
  translation-quality scorecard — same idea, applied to a posting.
- **New:** the Connoisseur persona + a SWOT scorecard on listing output.

### Block 7 — IMPROVE (optional loop)
They act on the scorecard or accept it. The loop is short and *bounded* by the STOP
verdict — assistance, not perfectionism.

### Block 8 — POST (La Piazza's existing flow)
Hand off to the list flow they'll use forever, **pre-filled**, and they press Post.
The item goes live. We do **not** rebuild this — it's fast and it works.
- **Have:** onboarding → `POST /api/v1/items`, verified live on staging.
- **Decision pending:** hand-off = (a) prefilled deep-link into the existing flow
  [lean], or (b) Bottega posts server-to-server.

### Block 9 — SHARE (the reach)
The posting becomes something shareable — a postcard or a short clip — pushed to the
person's own WhatsApp / Telegram groups or a YouTube video. Their network, not ours.
- **Have:** postcard + voiceover-reel recipes already make shareable artifacts.

### Block 10 — BLUEPRINT RECORD
Every run is logged as a reviewable blueprint (who, what move, what got posted, the
score). We look at it now and then to see what's actually happening and improve the
recipes — so we're not reinventing, and people aren't circling.
- **Have:** the recipe-run ledger / spine.
- **New:** surface it as a readable "blueprint" view.

---

## What's already built vs. what's new (so we don't reinvent)

| Block | Already have | New work |
|------|---------------|----------|
| 1 Door | login, accounts | "first run" flag |
| 2 Read | reception matches person→master | read profile for a *move* |
| 3 Suggest | all output types modeled | converge to ONE + why |
| 4 Route | recipe chassis | Cleo picks + pre-fills recipe |
| 5 Assist | smart-listing | swap Pollinations→Unsplash |
| 6 Scorecard | judge pattern, video scorecard | Connoisseur + SWOT + STOP verdict |
| 7 Improve | — | bounded loop |
| 8 Post | list flow, POST /items (live) | hand-off style (a or b) |
| 9 Share | postcard / voiceover recipes | wire share-out |
| 10 Record | recipe-run ledger | blueprint view |

**Most of it exists.** The genuinely new muscle is: Cleo routing to a *move+recipe*,
and **the Connoisseur scorecard** (Blocks 3, 4, 6) — and the scorecard is a *chassis*
feature (every recipe inherits it, like `outcome`/`steps`), not a one-off for listings.

**Design principle (Angel, 2026-06-18):** people are lazy — most won't fill things out
properly. So the AI does the heavy lifting (assist) and the scorecard certifies it's
properly done ("everything checked off"). Make it easy, raise the floor, every recipe.

---

## The Design recipe + the image problem (its own recipe)

**The need:** a *maker* wants to SEE the finished thing before making it — Sylvie's
Trapanese-geometric pillow, the matching round-bottom handbag, cat-shaped cookies, a
car part, a model, a domain layout. Cleo interviews them (style, colours, shape,
material, "round bottom"), then it produces a **design vision**. This is a separate
recipe from listing — the interview and the output are different.

**The distinction that changes everything:**
- **Stock retrieval (Unsplash)** = finds an *existing* photo ("a cosy kitchen"). Good
  for generic listing mood, or use the maker's own photo of the real item. It CANNOT
  draw Sylvie's specific pillow.
- **Generation (Gemini "Nano Banana", Stable Diffusion, DALL·E)** = *creates* a new
  image from a prompt. This is what the design use case needs — and it needs a GPU /
  paid API we don't own. Unsplash ≠ this.

**THE KEY INSIGHT (Angel, 2026-06-18): the prompt IS the product.** We don't host images;
we generate a **master-grade prompt** and the person feeds it into *any* image maker they
like. The image model is swappable — free DALL·E, Nano Banana, ChatGPT, or a member's GPU
running Stable Diffusion. In every case the call is the **same shape: our prompt in → an
image out.** So the three phases below aren't three systems — they're the same pipe with a
different spout. The scarce, hard thing (a great prompt by the masters) is what we own; the
GPU is the commodity. *This dissolves the hardware problem.*

**Real evidence — Sylvie's actual workflow:** ChatGPT generates her drawing → she finishes
it in Canva (Canva's own AI gives junk). She already does *prompt-elsewhere → finish-in-tool*.
We're upgrading the weakest link (the prompt) in a habit she already has. Most users have no
API key or paid plan — they burn a free tier (e.g. ~10 DALL·E images), then hop to Nano
Banana or ChatGPT. So the prompt must be **portable across makers**, and we can hand them a
ranked list of free options to hop between.

**The honest constraint:** we have no image-gen hardware. Pollinations generated images
but now charges. So for *design* we have three routes — same call, different spout: 

| Phase | Route | Who pays / runs | Effort | Ships |
|------|-------|-----------------|--------|-------|
| **1** | **Prompt-only** — the recipe is a master prompt-engineer; it outputs a polished, copy-paste image prompt + "paste this into Gemini / Canva / Nano Banana." | Them, manually, in their own tool | Tiny — pure text recipe | **Now** |
| **2** | **BYO-Appy (bring your own key)** — they paste their own provider key (Google AI Studio / Replicate / OpenAI); we call it with the prompt, the image comes back into the flow. | Them (their key, their quota) | One integration per provider + secure key storage | PoC next |
| **3** | **House / BYOH worker** — an image worker on a member's GPU (Stable Diffusion), brokered through the exchange — same pattern as the voiceover render worker. | Us / the network | New worker capability (the BYOH "C" lane) | Later |

**On "Google sign-in = free Nano Banana?"** — No. Google OIDC sign-in gives us their
*identity*, not Gemini API access. Calling Nano Banana programmatically needs a Gemini
**API key** (AI Studio) or Vertex. A logged-in Google user does not hand us image quota.
So the realistic automated path is Phase 2 (they paste an AI Studio key), or they stay
manual in Phase 1.

**Recommendation:** Design is **its own recipe**, and Phase 1 (prompt-only) ships now
with zero new infra. AND we add an **"image policy" field to the recipe SOP** so every
recipe declares how it handles images: `none | stock(Unsplash) | own-photo | prompt-only
| byo-key | worker`. That makes the choice per-recipe data, not a rebuild — same spirit
as the chassis. This is a clean instance of the BYOH thesis (bring your own brain/appy).

## Open questions for review
1. Is the **Connoisseur** a separate master/persona, or another hat Cleo wears?
2. Does the scorecard run **automatically** after the draft, or only when they **ask for help**?
3. First slice to prove end-to-end: **service**, **item**, or **made-to-order**?
4. Hand-off: prefilled deep-link **(a)** or server-to-server **(b)**?
5. Anything in the blocks that's wrong, missing, or in the wrong order?
