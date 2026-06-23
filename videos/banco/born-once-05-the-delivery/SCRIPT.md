# Born Once #05 — "The Delivery" (script)

*The cream gets **restocked** — and Banco's answer to "how many came in?" is "doesn't matter."
Ralph on the dock; the box arrives because the reorder he set in #04 asked for it. Tone: light, a
little dry-comic — the relief of NOT doing the dreaded count. New pipeline: Angel reads, Tigs drives
every screen. Target ~100s. Wraps the restock chapter; leaves the door open for the next.*

**Teaching point:** receiving the Zero-Perpetual-Inventory way. You **log that it came — not how
many.** A delivery slip quantity is *how many labels to print,* never a stock count. The packaging
knows the cost (box → singles). Dock to drawer, nobody counts a thing.

**Continuity:** Ralph set a reorder in #04 → the box shows up here because the system asked. The
cream's life keeps linking, episode to episode.

---

## Syd Field, three acts (~100s)
- **ACT 1** (0–22s): a box arrives; the old way is the worst job in the shop.
- **ACT 2** (22–72s): Ralph doesn't count → the slip is labels, not stock → the packaging knows the cost.
- **ACT 3** (72–100s): logged, not counted → the button (you sell a shop down, you don't count it in).

---

## The script — cards + VO

**ACT 1 · COLD OPEN**
**CARD:** *A box arrives.*
**VO:** "A box lands on the counter. Fifty tubes of the cream — the one that's been selling. The driver wants a signature. 'Fifty units,' he says. 'Count 'em.'"
*(Puppeteer: the receiving screen / a delivery)*

**ACT 1 · THE OLD DREAD**
**CARD:** *The old way: count every one.*
**VO:** "On an old till, this is the worst job in the shop. You count all fifty. You match them to the order. One's missing? Recount. The driver's tapping his foot, the line's backing up — and heaven help you if you're off by one, because now the whole system is lying."

**ACT 2 · THE TURN**
**CARD:** *Ralph doesn't count.*
**VO:** "Ralph doesn't count. He scans one tube — just to say 'this arrived' — and he's done. The box is in. He never typed a quantity. Because here's the thing nobody tells you: Banco doesn't track how many you have. It tracks what you sell. The shelf isn't a number in a database — it's the real shelf, in the real shop."
*(Puppeteer: scan-to-receive, the confirmation)*

**ACT 2 · THE SLIP TRUTH**
**CARD:** *"5 trays" = 5 labels. Not 5 in stock.*
**VO:** "And that slip — the one that says 'five trays'? That's not a stock count. That's how many labels to print. Five trays, five labels. The number on the paper was never about inventory. It was about getting price tags on the shelf."

**ACT 2 · THE COST MAGIC**
**CARD:** *The packaging knows the cost.*
**VO:** "What about the money? The box cost a hundred and twenty francs for fifty. Banco does the math — that's your cost per tube, baked right in. You bought a box; it splits into singles. The margin's already there, before the first one sells."
*(Puppeteer: the "bought a box? split it" box→singles feature)*

**ACT 3 · RESOLUTION**
**CARD:** *Logged that it came. Done.*
**VO:** "So the delivery that used to eat twenty minutes and start an argument? Ralph logged that it came, and walked away. No count. No reconcile. No clipboard. Dock to drawer — and nobody counted a thing."

**ACT 3 · THE BUTTON**
**CARD:** *You don't count it in. You sell it down.*
**VO:** "Because you don't count a shop in. You sell it down. The cream came in quiet — and now it's back on the shelf, waiting for Larry, and Sally, and whoever's next."

**OUTRO**
**CARD:** *BORN ONCE — logged, not counted.*

---

## Production notes (Tigs / Puppeteer)
- Screens: the receiving / scan-to-receive flow (BL-91), the **"bought a box? split it"** box→singles
  feature (seen on the sale screen), Ralph logged in, the cream back in the catalogue. Log in as
  **ralph**; add a receiving route to `capture_banco.js` if needed.
- Tone in the cut: lighter than #04 — the comedy of NOT counting. A beat of the driver waiting.
- The button names Larry, Sally, "whoever's next" → opens the door to #06/#07/#08.
- **Length:** ~255 words ≈ 100–110s. Trim the COST paragraph if you want it under 90s.
