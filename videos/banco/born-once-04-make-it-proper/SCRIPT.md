# Born Once #04 — "Make It Proper" (script)

*The keystone of Season 1 — the chapter where the cream gets **raised up**, and all three
characters do their jobs in one clean relay. Pam borns it → Felix notices from the road → Ralph
makes it proper. New pipeline: Angel records VO, Tigs drives every screen with Puppeteer.
Target ~95s. Tone: warm, a quiet pride — a team raising up a product.*

**Teaching point:** the **born-once lifecycle + RBAC as a relay team**, and the principle that
holds the whole season: **effort follows velocity.** A rough on-the-fly item that proves it sells
*earns* its photos, specs, cost, and reorder. You don't polish a dead shelf.

**The three roles, in order:**
- **Pam** (cashier) borns it on the fly — rough, fast, so the line keeps moving.
- **Felix** (owner) sees the velocity from the road; texts Ralph a URL. Can't fix it from there.
- **Ralph** (manager) makes it proper — pulls the real photo + specs from the website (no
  integration, by hand), **verifies the scanned barcode is really this product** (the approval
  gate), sets the cost and a reorder quantity.

---

## Syd Field, three acts (~95s)
- **ACT 1** (0–22s): a product born in a hurry — and then it sells, twice.
- **ACT 2** (22–68s): Felix notices from the road → texts Ralph → Ralph makes it proper.
- **ACT 3** (68–95s): next shift it's ready → the principle (effort follows velocity) → the button.

---

## The script — cards + VO

**ACT 1 · COLD OPEN**
**CARD:** *Born in a hurry.*
**VO:** "Friday rush. Pam scans something new — a cream, no barcode. She names it, prices it, snaps a quick photo, sells it. Forty francs, done. It's rough — a fast photo, no details. But the line's moving, and that's the job."
*(Puppeteer: the on-the-fly create — name, price, photo)*

**ACT 1 · IT PROVES ITSELF**
**CARD:** *Then it sold again. And again.*
**VO:** "Then Larry buys one. An hour later, Sally buys another. Two in a day — this brand-new little cream nobody had heard of yesterday."
*(Puppeteer: the catalogue / a sale, the cream moving)*

**ACT 2 · FELIX, FROM THE ROAD**
**CARD:** *Felix is 200 km away.*
**VO:** "Felix isn't in the shop. He's on the road. But he opens his phone, checks the dashboard — and there it is, selling. He knows a hit when he sees one. He also knows the entry is rough. He can't fix it from the highway, and it's not his job. So he sends Ralph one text: a link — the cream's page on the Artemis website."
*(Puppeteer: the dashboard — sales, velocity. The SBX badge.)*

**ACT 2 · RALPH MAKES IT PROPER**
**CARD:** *Ralph makes it proper.*
**VO:** "Ralph opens that link. Beautiful photos, full specs, the whole story — sitting on the website, a different system, not wired to the till. So he brings it across by hand. The real photo. The details. And he checks the one thing that matters — that the barcode Pam scanned really is this product. Because sometimes it isn't. He confirms it. Then he sets the cost, and a reorder number. The rough little cream just grew up."
*(Puppeteer: the manager catalogue edit — photo, specs, cost, reorder. Log in as Ralph.)*

**ACT 3 · NEXT SHIFT**
**CARD:** *Next shift, it's ready.*
**VO:** "Next morning, Pam opens the catalogue — and the cream's got a face now. A real photo. Specs she can read straight to the customer. A margin behind it. A reorder that won't let it run dry."
*(Puppeteer: the enriched product — the 'after')*

**ACT 3 · THE BUTTON**
**CARD:** *You only polish what sells.*
**VO:** "Here's the secret — nobody touched the seven thousand products that never sell. You don't polish a dead shelf. You wait for the shop to tell you what's worth it, and it tells you in sales. A cashier borns it. A manager raises it. The owner just has to notice. Effort follows velocity."

**OUTRO**
**CARD:** *BORN ONCE — born rough, made proper.*

---

## Production notes (Tigs / Puppeteer)
- Screens: on-the-fly create (Pam) · dashboard with velocity (Felix view, SBX badge) · the
  manager catalogue **edit** screen (log in as **ralph**) showing photo + specs + **cost** +
  **reorder** · the before/after of the product. `scripts/capture_banco.js` is the engine — add a
  Ralph login + the catalog edit route.
- The "approval gate" beat wants a visual of the barcode being confirmed — even just the product's
  barcode field highlighted works.
- Tone in the cut: warmer than #03, a little proud. Hold the "after" reveal (the enriched product).
- **Length:** ~245 words ≈ 95–100s. Trim Ralph's paragraph if you want it under 85s.
