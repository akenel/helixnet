# THE PERFECT TICKET — Banco Hypercare FAQ & SOP
*Reference for writing AND processing the perfect ticket · 2026-06-29*

---

## 1. Purpose — why a perfect ticket fast-tracks everything

When something's wrong on the till — or you just want it to be better — you tap the **💬** button and say so. An AI reads what you wrote and turns it into a clean ticket (BL-NNN). A human then builds the fix, proves it, and ships it down a safe ladder until it reaches your real till. You watch the whole thing in plain words: **Received → Understood → Fixing → Done.**

The cleaner your first message, the less back-and-forth — and the faster the fix lands. A *perfect ticket* is just a message that already answers the questions the builder would otherwise have to come back and ask.

You don't need to write like a programmer. You answer five small questions. Think of them as five Lego bricks: snap them together and you've built a perfect ticket. That one habit is what fast-tracks everything downstream — the AI triages it right the first time, the builder knows exactly what "done" means, and nobody guesses.

---

## 2. Anatomy of a Perfect Ticket

Five bricks. Answer these and you're done.

### Brick 1 — TITLE: say it in one line
A short, plain name for the thing, like a label on a drawer.
- Good: *"Receipt prints the date twice"*
- Good: *"I want a button to email a receipt"*
- Too vague: *"It's broken"* / *"Help"*

**Why it helps:** the title becomes the name of your ticket. You'll see it in your journey. The AI uses it to guess the *type* (a bug? a wish?), and the builder uses it to find the ticket again later.

### Brick 2 — WHAT IT LOOKS LIKE NOW: the current state
Describe what you actually see today. Just the facts, like telling a friend what's on the screen.
- *"When I close the drawer, the total shows 0.00 even though I sold 6 coffees."*
- *"There's no way to reprint a receipt once the customer walks away."*

**Why it helps:** this is the AI's anchor and it tells the builder *where* to look. "It shows 0.00" points straight at the screen and the number. Vague pain ("it's weird") makes everyone guess.

### Brick 3 — WHY: the pain or the value
Tell us why it matters. What does it cost you? What goes wrong because of it?
- *"I can't trust my end-of-day total, so I have to count cash twice."*
- *"Customers ask for a copy and I have to apologize — looks unprofessional."*

**Why it helps:** *why* sets the **severity**. A wrong total at closeout is serious (money). A nicer button color is nice-to-have. The AI uses *why* to sort what gets built first.

### Brick 4 — WHAT GOOD LOOKS LIKE: the test, stated up front
The most powerful brick. Describe how you'll *know it's fixed* — before any work starts.
- *"Done = the closeout total matches the receipts I sold that day, to the cent."*
- *"Done = I tap a button on a past sale and the same receipt prints again."*

**Why it helps:** this is the acceptance test. The builder builds *to* it, and we check the fix *against* it before it reaches you. No guessing whether it's "really done" — it's done when your test passes. This single brick saves the most back-and-forth.

### Brick 5 — WHAT IT ROUGHLY TAKES: plain scope (optional)
Fine to skip. If you have a sense of size or edges, say it in normal words.
- *"Just on the closeout screen — I don't need it on the receipt."*
- *"Only for today's sales, not the whole history."*

**Why it helps:** it draws a fence around the work. It stops a small fix from quietly growing big, and tells the builder what you *don't* need.

### Fill-in block

Copy this into the 💬 box and fill the blanks. Leave a line blank if you don't know — that's okay.

```
TITLE:
(one line — name the thing)

WHAT IT LOOKS LIKE NOW:
(what you actually see today)

WHY IT MATTERS:
(the pain, or what it would be worth)

WHAT GOOD LOOKS LIKE:
(how I'll know it's fixed — my test)

ROUGHLY WHAT IT TAKES (optional):
(where it lives / what I don't need)
```

A filled example:

```
TITLE:
Closeout total shows 0.00

WHAT IT LOOKS LIKE NOW:
At end of day the closeout total reads 0.00, but I sold 6 coffees for CHF 81.80.

WHY IT MATTERS:
I can't trust my day total, so I count the cash twice and still feel unsure.

WHAT GOOD LOOKS LIKE:
The closeout total matches the receipts I sold that day, to the cent.

ROUGHLY WHAT IT TAKES (optional):
Just the closeout screen. Card and TWINT sales should count too, not only cash.
```

---

## 3. The E2E Journey — 💬 to closed

Three rules ride along the whole way. We point at them as they bite.

- **Prove, don't assume.** After anything restarts, go look. Don't trust that it worked — check.
- **Re-probe after every restart.** Same idea, said twice on purpose: a restart is the moment lies sneak in.
- **Backup gates prod.** You never touch the real shop's data without a fresh backup first. No backup, no prod.

**Step 1 — Paste the perfect report (💬).** The shop owner taps 💬 and describes what they see, in plain words. A good report names *what they saw*, *what they expected*, and *where*. They don't need the technical name for anything.

**Step 2 — The AI auto-triages → a clean spec.** The messy report becomes a tidy ticket everyone can hold:

| Field | What it is |
|---|---|
| **Ticket** | BL-NNN |
| **Title** | One-line name |
| **Description** | The facts, plus where it lives |
| **Type** | Bug / Improvement |
| **Severity** | How urgent (set from the *why*) |
| **Confidence** | How sure the AI is it understood |

The reporter's journey shows **Received → Understood**. No jargon.

**Step 3 — Confirm, or add detail (re-triage if needed).** Show the owner the clean spec: *"Did I get this right?"* If **yes** → lock it. If they **add detail**, that new detail goes back through the AI and the ticket **re-triages live** — title, description, and severity re-settle around the new facts. The owner can correct it as many times as they like.

**Step 4 — Write the test script FIRST.** Before any code, write down how we'll *know it works*. This is the yardstick, written before the thing exists, so it can't be bent to fit a sloppy fix. (This is just Brick 4, turned into a checklist.) *If the fix can't pass every line, it isn't done.*

**Step 5 — Build it, sandbox-first, on a `feat/` branch.** Never build straight on `main`. Sandbox is the playground — nothing the owner depends on lives there. **A fix with no database migration is the safest kind** (nothing to migrate, nothing to break in the shop's data).

**Step 6 — Deploy to sandbox + PROVE it.** Deploy with the real tool, `scripts/ops/deploy-banco.py`, which stamps the **real git SHA** and **build date** into the app — no hand-typed numbers. Then — **prove, don't assume** — the container restarted, so **re-probe**: open sandbox and check with your own eyes. *(← prove-don't-assume bites here.)*

**Step 7 — Run the test script on sandbox.** Pull out the Step-4 yardstick and walk every line. One red = not shipped.

**Step 8 — The gate ladder: staging → backup → prod.** One rung at a time, higher stakes each step.
1. **Staging** — deploy, **re-probe** the restart, re-run the test script. The dress rehearsal; it should look exactly like prod will. *(← re-probe bites here.)*
2. **Backup** — before prod, take a fresh backup of the real shop's data. **No backup → stop.** The rule doesn't bend for "easy" fixes — easy fixes are exactly when people skip the backup and get bitten. *(← backup-gates-prod bites here.)*
3. **Prod** — deploy, **re-probe** the live till one final time. *(← re-probe bites here.)*

**Step 9 — Mark fixed → reporter closes → AI writes the Resolution.** Mark the ticket fixed **with the real commit SHA** (the one `deploy-banco.py` stamped) — no vague "done," so anyone can trace the exact code that shipped. The journey flips to **Done**, and the reporter taps to **close** it (closing is theirs, not ours). The AI writes a plain-language Resolution the owner actually understands.

**The whole ladder, at a glance:**
```
💬 report → AI triage → confirm/add-detail (re-triage) → TEST SCRIPT FIRST
   → build on feat/ branch (sandbox-first)
   → deploy sandbox → PROVE (re-probe) → run test script
   → staging (re-probe, re-test)
   → BACKUP → prod (re-probe)
   → mark fixed w/ real SHA → reporter closes → AI Resolution
```

---

## 4. Worked Example — CalVer (#3)

The fix: make the version number at the bottom of the till **real** instead of a frozen `3.3.0` that never moves.

### 4a. Paste-ready perfect feedback (Felix's voice)

> **The version number at the bottom never changes**
>
> Down at the bottom of the till it says **3.3.0 · fd902c2 · 29 Jun**. The little code and the date keep up — they change when you push something new, I've watched them move. But that **3.3.0** has sat there frozen the whole time. It was 3.3.0 weeks ago and it's still 3.3.0 today, even on days I know you've sent me a fix.
>
> So it's a bit of a fib. It looks like a "you're up to date" number, but it's just painted on — it doesn't mean anything. If something ever does go stale, that number won't tell me; it'll happily say 3.3.0 forever.
>
> What I'd love: make that first number tell the truth too, like the date next to it already does. If it were the build *date* — say **26.06.29** — I could glance at the till and know in one second how fresh it is. A number that can't lie, because it's just "when was this made." No one has to remember to bump it; it bumps itself every time you ship.
>
> Not urgent, nothing's broken. It's a trust thing — the bottom bar is the one place I look to know the till's current, and right now two-thirds of it is honest and one-third is a sticker. Make all of it honest.

### 4b. Now / Why / What-it-takes

**NOW** — The bar reads `3.3.0 · fd902c2 · 29 Jun`. The sha (`fd902c2`) and the date (`29 Jun`) are *real* — the deploy stamps them every time (`build_info.py` reads them from the git SHA and the build date). But the `3.3.0` is a hardcoded string in one file (`src/__init__.py`, `__version__ = "3.3.0"`). Nobody changes it, so it never moves. It's painted on, pretending to be a status.

**WHY** — The status bar is the one spot Felix looks to know "is my till current?" A number that *can* go stale *can* lie — it'll say 3.3.0 even on a day we shipped a fix. A number *derived from the build* can't lie: it's just "when was this made." Truth at a glance = trust, freshness readable in one second. Severity: **Low** — cosmetic, but it's a trust signal, so worth doing right.

**WHAT IT TAKES** — Stop hardcoding the version; *derive* it. We already capture the real build date (`get_build_date()`). Turn that into a CalVer string — `26.06.29` (yy.mm.dd) — instead of returning a frozen `"3.3.0"`, plus a numeric dd/mm date in everyday form. The sha and date pieces already work; this feeds the same real build date into the front slot. Result: `26.06.29 · fd902c2`, and it bumps itself on every deploy. **No database change — the safest kind of fix.** No release ritual, nothing to remember, and it can never go stale.

### 4c. The test script — written FIRST

**What we're proving:** the version in the status bar is a **real, date-based number** that moves on every deploy — never the frozen `3.3.0` again.

**Where:** `https://sandbox-banco.lapiazza.app` — log in as `pam` / `helix_pass`. The bar lives in the bottom status strip, the `⚙` chip. Today it reads `⚙ 3.3.0·<sha> · <DD Mon>`. After the fix it should read like `⚙ 26.06.29·fd902c2 · 29/06` (version · sha · numeric date).

**Moving parts (so a tester knows where to look):**
- Version source: `src/__init__.py` → `__version__` (the hardcoded `3.3.0` is the bug).
- Bar template: `src/templates/pos/base.html` (~line 712) — `app_version` · `git_sha[:7]` · `build_date`.
- Inject point: `src/main.py` (lines 372-375) feeds `app_version`/`git_sha`/`build_date`.
- Machine truth: `GET /health/system` returns `version`, `build.sha`, `build.date` (public, no login).
- Pulse: `GET /api/v1/pos/system/pulse` returns `build.version`, `build.sha`.

| # | Do this | Expect this | P/F |
|---|---------|-------------|-----|
| 1 | Log in as pam. Look at the `⚙` chip in the bottom bar. | Version reads as a **date** (`26.06.29` / `2026.06.29`). **NOT** `3.3.0`. | ☐ |
| 2 | Read the date segment of the version. | **Numeric** — digits and separators only (`26.06.29` / `29/06`), no month words inside the version. | ☐ |
| 3 | Confirm the SHA is still in the bar, right after the version. | A 7-char git sha (e.g. `fd902c2`), unchanged in position. Version didn't eat the sha. | ☐ |
| 4 | Hover (or long-press) the `⚙` chip for its tooltip. | Same real date-version + sha + build date — no `3.3.0`, no `dev` placeholder. | ☐ |
| 5 | Open `/health/system`. Read `version`. | Same date-based string as the bar (machine truth matches screen). NOT `3.3.0`. | ☐ |
| 6 | In the same JSON read `build.sha` and `build.date`. | `build.sha` matches the bar; `build.date` is a real ISO date, not blank. | ☐ |
| 7 | Open `/api/v1/pos/system/pulse`. Read `build.version`. | Matches the bar and `/health/system`. All three agree. | ☐ |
| 8 | Note the version + sha. Deploy a fresh build to sandbox, then hard-refresh. | Version + sha **both update**. The number moved — not frozen. **(The real proof.)** | ☐ |
| 9 | Click through Sell, Catalog, Closeout. Check the `⚙` chip on each. | Same real date-version on every screen, no blanks, no fallback to `3.3.0` / `dev`. | ☐ |
| 10 | Reopen on a phone (Fairphone width). Look at the bar. | Version + sha + date readable, not clipped or overflowing; layout unchanged. | ☐ |
| 11 | Check the "New version — tap to update" path and the `· DD Mon` freshness label. | Update banner / pulse-build still render; nothing regressed (don't break BL-010). | ☐ |
| 12 | Grep the running tree for the literal `3.3.0`. | Nothing — no screen, JSON, or tooltip shows `3.3.0`. The stale number is gone for good. | ☐ |

**Acceptance bar — all green = ship:**
- [ ] Bar shows a **date-based version** (CalVer), never `3.3.0`.
- [ ] Version's date part is **numeric dd/mm style** (no month words inside the version).
- [ ] The **7-char SHA still shows**, in place, after the version.
- [ ] Version + sha **change on a new deploy** (step 8 *proven*, not assumed).
- [ ] `/health/system` and `/system/pulse` JSON **agree with the screen**.
- [ ] **Nothing else broke** — every POS screen, mobile layout, tooltip, and the update/freshness banner render clean.

> **Deploy discipline:** PROVE step 8 by re-probing after the restart — do not tick it from memory. One red = not shipped.

### 4d. The E2E, applied to CalVer

1. **💬 report** — Felix pastes 4a.
2. **AI triage** — Title: *"Version number is hardcoded and never updates."* Type: Improvement. Severity: Low (trust signal). Confidence: High.
3. **Confirm / add detail** — Felix adds: *"Make it date-based so it can never go stale, and keep a dd/mm date too."* Re-triage locks the target: `26.06.29 · fd902c2` plus a numeric dd/mm date.
4. **Test script first** — write 4c before touching code.
5. **Build, sandbox-first** — branch `feat/calver-version`. In `src/__init__.py`, stop hardcoding `"3.3.0"`; derive CalVer `YY.MM.DD` from the real build date `build_info.py` already uses. **No migration.**
6. **Deploy sandbox + PROVE** — `deploy-banco.py` stamps the real SHA + date. Re-probe: expect `26.06.29 · <real-sha> · 28 Jun`. Still `3.3.0`? The deploy didn't take — stop and fix.
7. **Run the test script on sandbox** — all 12 rows green, step 8 the clincher.
8. **Ladder** — staging (re-probe, re-test) → **backup** (yes, even with no migration) → prod (re-probe the live till).
9. **Mark fixed w/ real SHA** → journey flips to **Done** → Felix closes → AI Resolution:
   > *"The version number at the bottom of Banco is no longer stuck. It now shows today's date (like 26.06.29), so every time we ship an update, the number moves on its own. You'll always be able to tell at a glance how fresh your Banco is."*

---

## 5. FAQ

**How much detail should I write?**
Enough to answer the five bricks, no more. Three honest sentences beat three paragraphs. Unsure? Lead with Brick 2 (what you see) and Brick 4 (what good looks like) — those two alone get you most of the way.

**Should I attach a screenshot?**
Yes, whenever the problem is something you can *see* — a wrong number, a button in the wrong place, text cut off. A picture often replaces a whole paragraph. For a wish ("I'd like a new button"), words are usually enough.

**Do I pick the severity (how urgent it is)?**
You don't have to. The AI reads your *why* and proposes one. If it feels wrong, say so in plain words — "this is blocking me, I can't close the till" — and it gets bumped.

**What if the AI reads it wrong?**
No problem, and nothing is stuck. Reopen the ticket or add a line of detail and it **re-triages on the spot** — the AI re-reads everything and rebuilds a fresh clean ticket. Correct it as many times as you like. You're always the one who closes it at the end.

**Do I need the right words for things?**
No. Call it what you call it — "the drawer thing," "the print button," "that number at the bottom." The AI matches your plain words to the real parts. Never hold back a report because you don't know the technical name.

**What happens after I send it?**
You watch a simple journey — **Received → Understood → Fixing → Done** — no jargon. When it's done, the AI writes a short plain-language note of what changed, and you get the final say on closing it.

**Why does even a tiny fix go through staging and a backup?**
Because "easy" is exactly when corners get cut and people get bitten. A backup always gates prod, and every restart gets re-probed with real eyes — no exceptions, even for a no-migration one-liner like CalVer. It's slower by minutes and safer by a mile.

**Why mark the ticket fixed with a commit SHA?**
So "done" is never vague. The deploy tool stamps the real git SHA into the app, and we record that exact SHA on the ticket — anyone can trace precisely which code reached your till.

---

*One line, what you see, why it hurts, how you'll know it's fixed. Five bricks. That's a perfect ticket.*
