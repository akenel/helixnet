# Born Once #02 — "The Phantom Sale" (script)

*A true-crime short. The footage is REAL — your Fairphone caught the phantom in the act this
morning (the `fp ... bug video` recording). Target ~90s. Genre shift from #01: this isn't an
explainer, it's a **detective story.** Tone: noir, suspense, then the satisfying catch.*

**Why this one hooks harder than #01:** "We sold a product that didn't exist" beats "stop counting"
— it's a mystery, and you can't not watch a mystery resolve.

---

## Syd Field, three acts (for 90 seconds)
- **ACT 1 — Setup + Hook** (0–15s): the world looks perfect. The inciting line lands cold.
- **ACT 2 — Confrontation** (15–60s): the turn (it's gone), the stakes (imagine your shop), the hunt.
- **ACT 3 — Resolution** (60–90s): the catch, the proof, the lesson-button.

---

## The script — cards + VO

**ACT 1 · COLD OPEN — the hook**
**CARD:** *We sold a product that didn't exist.*
**VO:** "We sold a product… that didn't exist."
*(visual: hold black a half-beat, then the mobile till)*

**ACT 1 · SETUP — it looks perfect**
**CARD:** *It looked perfect.*
**VO:** "Watch. A cashier scans something brand new. Names it. Prices it. Snaps a photo. Sells it.
The receipt prints. The points land. The customer walks out happy. Everything… looks… perfect."
*(visual: the real mobile flow — scan barcode → name → price → photo → sale → receipt)*

**ACT 2 · THE TURN — it's gone**
**CARD:** *Two minutes later — gone.*
**VO:** "Two minutes later, she goes to ring up another one. She searches the name…"
*(visual: typing in the search box — the real "He" search)*
**VO (after a beat):** "…nothing. No matches. The product she just made — and sold — is gone."
*(visual: the real "No matches" frame. Let it sit.)*

**ACT 2 · THE NATURE OF IT — a phantom**
**CARD:** *A phantom.*
**VO:** "The sale was real. The money was real. The points were real. But the product? Never saved.
Never in the catalogue. It vanished the second the receipt printed. A phantom."

**ACT 2 · THE STAKES — your shop**
**CARD:** *Now imagine that's your shop.*
**VO:** "Now imagine that's your shop. Every new barcode a cashier scans — sold once, then gone. A
catalogue full of holes. The one promise this whole thing makes — *scan once, known forever* —
silently broken. And nobody notices… because the sale never fails."

**ACT 2 · THE HUNT — the twin seal**
**CARD:** *One seal worked. Its twin leaked.*
**VO:** "So we hunted it. There are two ways to make a product. One let the cashier straight through.
Its twin — the one that fires when you scan a *fresh barcode* — slammed the door. A permission error,
swallowed in silence. One seal worked. The identical seal right next to it… leaked."
*(visual: the two code paths side by side; highlight the 403 / the manager-only line)*

**ACT 3 · THE CATCH**
**CARD:** *One line. There it is.*
**VO:** "We found it. One line. We sent the barcode through the same door the cashier was already
allowed through. And now — she scans, creates, sells, searches…"
*(visual: the fixed flow → the search → the product appears)*
**VO:** "…there it is. It stuck. Forever."

**ACT 3 · THE BUTTON — the lesson**
**CARD:** *If one seal fails, check all the seals.*
**VO:** "Found on a phone. Killed before it ever touched a real shop. Because if one seal fails — you
check *all* the seals. That's the difference between software that's been tested… and software that's
been *lived in.*"

**OUTRO**
**CARD:** *BORN ONCE — the phantom's dead.*

---

## Production notes
- **This one has real footage** — the `fp ... bug video_2026-06-23` mobile recording IS the crime
  scene (the HempSana create → sell → "No matches"). Harvest those exact moments per the slideshow
  method (Phase 3C): scan, name+price, receipt, the "No matches" reveal.
- **The hunt + catch need code shots** — the two create paths (`/products` manager-only vs
  `/products/quick` cashier-safe), the 403, and the one-line fix. A clean screenshot of the diff, or
  the `BL-BUG-cashier-barcode-create-phantom.md` lines, styled.
- **The proof shot** can be a fresh capture on the *fixed* till: scan a new barcode → sell → search →
  it appears. (Now true on prod.)
- **Pacing:** this is a thriller — leave **silence** on the turns ("…nothing." / "…there it is.").
  Don't rush the reveal. The pauses are the suspense.
- **Music:** Brotherhood Run again, OR a tenser/quieter bed for the noir feel — your call.
- **Length:** ~230 words VO ≈ 90s. Cut the STAKES paragraph if you want it under 75s.
