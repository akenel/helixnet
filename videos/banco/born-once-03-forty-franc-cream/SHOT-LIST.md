# Born Once #03 — "The Forty-Franc Cream" — Shot List / Run-Sheet

*Pairs with `TELEPROMPTER.html` and `SCRIPT.md`. Good news: **most of the footage already exists**
in tonight's 14-minute walkthrough. You shot the cream tube and the picture-catalogue without
knowing you were filming #03.*

---

## Source footage
**Master walkthrough (tonight):** `screen-20260623-181739 (2).mp4` (currently in
`~/Downloads/Telegram Desktop/`). **Copy it into `assets/` so it doesn't get cleared** — it's the
raw for #03 (and #04+). Timestamps below are in that file.

| Beat | What you need | Where it is (mm:ss) |
|------|---------------|---------------------|
| Hook — the cream | the green-cap cream tube in hand / on counter | **~2:40–3:00** |
| The shelf / look-alikes | catalogue grid, multiple products, "Product Catalog" | **~12:00–12:10** + the catalogue list ~13:00 |
| Create-with-photo | snapping a tube's photo while making the product | **~1:00–1:40** (tub) and **~2:40–3:00** (cream) |
| **The turn — tap the picture** | Find Product → category → product **with its photo** → into cart | **~13:09–13:27** (the "On the fly" catalogue, photo + price + Add) |
| Born once — the face | the photo being taken at creation | **~2:45** |

> The **13:09 catalogue** is the same gorgeous footage that gave #02 its resurrection — here it
> plays a different role: *proof you can sell by picture.* Reusing it across episodes is a feature,
> not a cheat — it's the same shop, the same truth.

---

## The ONE fresh pickup (~15s) — shoot this slow
The turn deserves a clean, dedicated capture:
1. Open the **catalogue / Find Product**.
2. **Tap the cream's photo** (not a barcode — the *picture*).
3. It drops into the cart at the **right price (40)**.
4. Hold a beat on the cart line.

That single tap is the whole short. Film it deliberately, no rush — 2 takes.
*(If the cream isn't priced at 40 in the sandbox, create it first at 40 with a photo, then do the
tap. Reset the sandbox before recording: `ssh root@46.62.138.218 'cd /opt/helixnet && make sandbox-reset'`.)*

---

## Cards to generate (abstract beats only — keep them few)
- *Half this shop has no barcode.*
- *Now sell it.*
- *The old way: a sticky note and a prayer.* (a messy sticky-note / manual-keypad feel)
- *She doesn't scan. She taps the picture.*
- *Born once — given a face.*
- *A barcode is the factory's. A picture is yours.*
- *Sell what you can see.*
- Outro: *BORN ONCE — sell by sight.*

---

## Assembly notes (apply the #02 lesson)
- **Less choppy than #02.** Fewer cards, **longer holds** (1.5–2s) on the real screens, crossfades
  ~0.7s. Let the *tap-the-picture* beat breathe — that's the payoff, don't rush it.
- Same portrait **1080×1920**, red card-bars over the chrome, dark title cards — the Banco Method
  (`scripts/build_phantom02.py` is the template; copy it to `build_cream03.py` and swap the timeline).
- Same machine as #01/#02: VO → trim long pauses → harvest frames at the timestamps above →
  compose slides → xfade on the beat map → bed Brotherhood Run at 5–7.5%.

## Recording plan
1. **VO first** — read `TELEPROMPTER.html`, easy-and-sly tone, ~1s holds. Send as a voice message.
2. **Copy the master walkthrough** into `assets/` (don't lose it).
3. **Shoot the one pickup** — the picture-tap, slow, 2 takes.
4. Drop both here; I harvest the timestamps above + your pickup and assemble.
