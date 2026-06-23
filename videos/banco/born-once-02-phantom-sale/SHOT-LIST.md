# Born Once #02 — "The Phantom Sale" — Shot List / Run-Sheet

*Pairs with `TELEPROMPTER.html` (read the VO) and `SCRIPT.md`. This is **where each picture comes
from.** Unlike #01, most footage already exists — your Fairphone filmed the crime this morning.*

---

## Three visual sources
1. **CRIME SCENE** — `docs/testing/banco/fp ... bug video_2026-06-23_13-26-03.mp4` (the real phantom:
   HempSana created, sold, then "No matches"). Harvest stills per the slideshow method (SOP 3.5C / 3C).
2. **CODE SHOTS** — the two create paths + the one-line fix. Clean screenshots (dark editor or the
   `BL-BUG-cashier-barcode-create-phantom.md` table styled). Source lines:
   - `pos_router.py:130` — `POST /products` → `require_roles(manager/dev/admin)` ← the door that slammed
   - `pos_router.py:155` — `POST /products/quick` → `require_any_pos_role` ← the door that worked
   - `scan.html:849` — the fix (now `/products/quick`)
3. **PROOF (fresh)** — record a NEW capture on the **fixed** till (prod or staging): scan a new
   barcode → sell → search → it appears. ~20s, the only thing you shoot fresh.

---

## The shots (in script order)

| Act | Beat / Card | Visual | Source |
|-----|-------------|--------|--------|
| 1 | **"We sold a product that didn't exist."** | black → the mobile till | crime-scene ~0:40 |
| 1 | **"It looked perfect."** | scan barcode → name → price → **photo** → sell → **receipt** | crime-scene ~0:56, 1:12, 2:00, **3:04 (receipt + points)** |
| 2 | **"Two minutes later — gone."** | typing in the search box | crime-scene ~4:00 |
| 2 | *(HOLD)* the reveal | **"No matches"** on screen | **crime-scene ~4:04 (the money frame)** |
| 2 | **"A phantom."** | the empty result / receipt ghost | crime-scene ~4:04 + 3:04 |
| 2 | **"Now imagine that's your shop."** | a "catalogue full of holes" feel — empty search, or a graphic | crime-scene ~4:04 |
| 2 | **"One seal worked. Its twin leaked."** | the **two code paths** side by side, highlight the 403 / manager-only line | CODE SHOT (`pos_router.py:130` vs `:155`) |
| 3 | **"One line. There it is."** | the one-line fix, then the **search finds it** | CODE SHOT (`scan.html:849`) → PROOF capture |
| 3 | *(HOLD)* "…there it is." | the product appears in search | PROOF capture |
| 3 | **"If one seal fails, check all the seals."** | a clean lesson card (red bar) | generated card |
| — | **Outro** | "BORN ONCE — the phantom's dead." | generated card |

---

## Recording plan
1. **VO first.** Open `TELEPROMPTER.html`, record the voice-over in one pass — **honor the HOLD tags**
   (1–2s of silence; the pauses are the suspense). Clean it per the voiceover pipeline (loudnorm, 48k).
2. **Harvest the crime-scene stills** from the bug video at the timestamps above (contact-sheet → exact
   frames → verify you grabbed the *right* moment, e.g. the real "No matches" frame).
3. **Make the code shots** — screenshot the two paths + the fix (or style the BL-BUG table). Keep them
   readable on a phone: big font, one idea per shot.
4. **Shoot the PROOF** — ~20s on the fixed till: new barcode → sell → search → it appears.
5. **Assemble** per the slideshow method (Phase 3C): card bars over each still, cross-fades, VO under,
   intro + outro cards. Same 564-wide portrait frame as #01.
6. **Music:** Brotherhood Run again — OR try a quieter/tenser bed for the noir feel.

## Notes
- **The pauses are everything.** This is a thriller; the held beats on "…nothing." and "…there it is."
  are what make it land. Build them into the edit (a beat of the still before the card flips).
- **Don't over-explain the code.** Two shots max for the hunt — the *door that slammed* and the *one
  line* that opened it. The audience feels the fix; they don't need to read it.
- This is the **payoff of doing #01 honestly** — the search slide we added to #01 is *true* because of
  the fix this short is about. The series is now self-referential. That's a flex.
