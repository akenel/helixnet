# Born Once #04 — "The Drawer That Wouldn't Close" (script)

*First episode on the NEW pipeline: **you record only the voice.** I drive every screen with
Puppeteer and build the whole video. Target ~95s. Genre: a quiet workplace mystery — the nightly
dread of a till that won't balance, then the relief of a drawer that tells the truth.*

**Teaching point:** the **per-cashier cash drawer (cash shift).** Each cashier opens their own
drawer with a counted float; every sale, every paid-in and paid-out ties to *them*; at close they
count out and the till shows **expected vs. counted — the variance, by name, by time.** On an old
shared till, a shortfall is a whodunit with no clues. Banco turns it into a fact.

**Why it hooks:** every shop owner has lived the short drawer at midnight. "Forty francs gone, and
nobody knows where" is a feeling, not a feature — and the resolution is deeply satisfying.

---

## Syd Field, three acts (~95s)
- **ACT 1 — Setup + Hook** (0–18s): midnight, the drawer is short, and the old till can't tell you why.
- **ACT 2 — Confrontation** (18–62s): the shared-drawer trap (many hands, no trail) → the turn (each cashier, their own counted drawer).
- **ACT 3 — Resolution** (62–95s): the variance gets a name and a time → accountability without accusation → the button.

---

## The script — cards + VO

**ACT 1 · COLD OPEN — the hook**
**CARD:** *Midnight. The drawer is short.*
**VO:** "Midnight. You count the till. It's forty francs short."
*(Puppeteer: the close-shift / count-out screen)*

**ACT 1 · THE DREAD**
**CARD:** *And nobody knows why.*
**VO:** "Not a disaster. But forty francs. And here's the thing that keeps an owner up at night — you have no idea where it went. A wrong change? A missed sale? A hand in the drawer? The old till just shrugs. One drawer, all day, every hand in it. The money is a blur."
*(Puppeteer: a busy sales screen / totals)*

**ACT 2 · THE TRAP — the shared drawer**
**CARD:** *One drawer. Every hand. No trail.*
**VO:** "On a shared till, you can't even ask the right question. Three people worked today. The shortfall has no name, no time, no story. So you do what every shop does — you sigh, you eat the forty francs, and you hope it's less tomorrow."
*(Puppeteer: a generic totals / Z-report view)*

**ACT 2 · THE TURN — your own drawer**
**CARD:** *In Banco, the drawer is yours.*
**VO:** "Banco does it differently. You start your shift by counting your float — your drawer, your number. From that second, every sale, every paid-in, every payout is tied to *you.* Not the till. You."
*(Puppeteer: open-drawer / count-the-float screen, then "My Drawer")*

**ACT 2 · THE CLOSE**
**CARD:** *Count out. The till already knows.*
**VO:** "At the end, you count the cash back. And the till tells you what it *should* be — to the franc. Expected. Counted. The difference, right there."
*(Puppeteer: close-shift screen showing expected vs counted vs variance)*

**ACT 3 · THE RESOLUTION — a name and a time**
**CARD:** *Now the shortfall has a name. And a time.*
**VO:** "Now that forty francs isn't a mystery. It's *Maria's drawer, Tuesday, the evening shift.* Maybe it's an honest miscount. Maybe it's a coaching moment. Either way — you can *see* it. That's not suspicion. That's just light."
*(Puppeteer: the per-cashier daily drawer log)*

**ACT 3 · THE BUTTON**
**CARD:** *A drawer that tells the truth.*
**VO:** "You can't fix what you can't see. Banco doesn't accuse anyone. It just counts — so you never have to wonder again. A drawer that closes, because it tells the truth."

**OUTRO**
**CARD:** *BORN ONCE — every franc accounted for.*

---

## Production notes
- **Pipeline:** Angel records VO sections to `TELEPROMPTER.html`; Tigs captures all screens via
  Puppeteer (login → open drawer → My Drawer → sales → close shift / variance → daily log) at a
  portrait viewport, no browser chrome, then builds the slideshow (`scripts/build_cream03.py` is
  the template → `build_drawer04.py`).
- **Tone:** quieter than #03, a little weary at the open ("midnight… forty francs short"), warming
  to relief and steadiness by the button. Slow delivery suits it — let the dread sit.
- **Record in sections** (the method that worked): one take per beat, ~1s holds. Hand them back;
  I check tones and flag any single snippet to redo.
- **Music:** Brotherhood Run at 6%, or a steadier/warmer bed for the late-night feel.
- **Length:** ~210 words ≈ 95s. Trim the TRAP paragraph if you want it under 80s.
