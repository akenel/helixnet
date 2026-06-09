# Dream Weavers — Episode 2: "Ask the Neighbourhood" (shooting script)
*Music-only (NO voice). Sid Field. ~50s. Intro/outro cards. Driven live on the real app (Puppeteer).*

## Logline
Mike has a 1,000-lb crane to move and it's not a one-man job — so he does the bravest thing a
neighbour can do: **he asks.** One post to the Help Board, and the whole town can see it.

## The teach (the feature)
**How to ask the neighbourhood for help** — posting a request on the Help Board. The "dialogue" is
the post Mike writes; the camera reads it as it takes shape.

## Sid Field structure
- **Setup** — the Help Board: this is where neighbours help neighbours.
- **Turn** — Mike opens a new request and writes his ask (the crane, Saturday, 20 hands, Sally's cookies).
- **Payoff** — the post goes LIVE on the board. The ask is out. The town can answer. *(Hook → Ep 3.)*

## The beats (≈50s)
| Time | On screen | Action | Beat |
|------|-----------|--------|------|
| 0:00–0:05 | **Intro card** — "Dream Weavers · Mike's Big Move / Episode 2 · Ask the Neighbourhood" | hold | — |
| 0:05–0:12 | The **Help Board** (Mike logged in) — real posts, the "Ask for help" button | gentle scroll, settle on the button | Setup |
| 0:12–0:17 | The **new-request form** opens | click "Ask for help" → form | Turn ↑ |
| 0:17–0:36 | The **title + body** type out, line by line (the ask takes shape) | type the post (below) | Turn |
| 0:36–0:42 | Category = **Neighbourhood Help / Moving**, then **Post** | pick category → click Post | Commit |
| 0:42–0:48 | Mike's post **appears live at the top of the board** | board reloads, his ask sits there | Payoff |
| 0:48–0:53 | **Outro card** — "Next: The Crew Rallies · Subscribe" | hold | Hook |

## The "dialogue" (the exact post Mike types)
**Title:**
`20 hands needed Saturday — moving a 1,000-lb crane out of my garage`

**Body:**
`Hey neighbours — clearing out the garage before the big move, and there's a 1,000-lb engine crane that is NOT a one-man job. Looking for ~20 good hands this Saturday at 9am. My sister Sally's baking cookies for the crew. Bring gloves. Who's in?`

**Category:** Neighbourhood Help (Moving) · **Urgency:** normal

## 🎵 Music (your "keep it down, Banksy" note)
Music-only episode → the theme IS the audio, but **understated, not blasting** — let the *visual
story* (the cards + the ask appearing) lead. Use the **buildup** section so energy rises as the post
takes shape and peaks as it goes live. Mixed tasteful, a touch low — the story speaks, the music
carries. *(For VOICE episodes like Ep 1, music sits ~5% under the voice — lower than the 9% we used;
I'll re-mix Ep 1 down to ~5% too if you want.)*

## Production notes
- Recorder: `tests/e2e/ep02-record.js` — demo-login as **mike**, drive the Help Board post flow,
  natural-length dwells (let the title/body breathe as they type), zoom for readable text.
- Seed: a clean Help Board state (Mike's post is the new one we create on camera).
- Then: cards → stitch → score with the theme (understated) → ship-sheet (no captions — music-only).
- Joins the regression gate like every episode.
