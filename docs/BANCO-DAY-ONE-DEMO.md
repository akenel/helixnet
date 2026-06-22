# Banco — Day One: Demo, Go-Live & Replay Test

*Artemis Store · English (v1) · Swiss francs · fresh empty database · Monday 22 June 2026*

The one demo that matters: **the first sale ever**, on a system that knows nothing yet,
watched as it builds itself up. It doubles as the canonical replay test — if Day One
stays green, the spine is alive.

---

## Why there is no cutover plan

A traditional POS go-live is brutal: stop the shop, count all stock, import a catalogue,
reconcile, train staff, pick a date, pray. Banco deletes the two things that make that
brutal:

- **No catalogue to import** — it builds itself by selling (catalogue accretes from real
  sales; we call it *sell-to-seed*).
- **No stock to count** — zero perpetual inventory; the count was always a lie for ~100%
  unmarked goods.

Remove those two and "cutover" mostly evaporates. That is *why* "just start Day One" is
viable instead of reckless. **"You don't set Banco up. You use it, and it sets itself up."**

What still has to be true on Day One is small — see **Go-Live** below.

---

## The props

| Prop | Why it's here |
|------|---------------|
| **Hero — the CHF 40 cream** | Beautifully labelled, fully specced — and the barcode is so small **no phone will ever read it**, no matter the light. The item that proves the point at the *top* of the ticket. |
| **Volume — Gizeh papers + filters** | Half of it has **no code at all**. Proves the point at the *bottom* of the ticket. |

One cheap, one expensive → the pattern holds at both ends.

---

## The three item cases (the born-once spec underneath — for Takes)

| Case | Situation | What Banco does |
|------|-----------|-----------------|
| **A — Known** | Scans, already on file | Show name/price/photo → sell. Fast. |
| **B — Readable code, not on file** | Has a real manufacturer barcode the phone *can* read | Born once on that code. **No label needed** — it brought its own. |
| **C — No usable code** | Nothing on it, **OR** a code too small/bad to scan (the cream) | Banco **generates an internal code** → drops it in the **label queue** → you stick a clean legible label on. Missing code and unreadable code take the **same path**. |

Every case offers **📷 photo** — snap the actual item, camera's already in hand.
**Skippable**: the photo (and any AI draft) is an accelerator, never a gate.

---

## The story — Syd Field, three acts

Shot column: **📱 Phone** = real Fairphone screen-recording (the camera beats can't be
faked — `html5-qrcode` needs a real lens). **🖥️ Pup** = Puppeteer/OBS desktop render
(clean wide shots + title cards).

### Act I — Setup (the problem)
| # | On screen | Card | Shot |
|---|-----------|------|------|
| 0 | Log in. Shop Pulse: 0 sales, catalogue empty | *"Monday, 22 June. Banco knows nothing yet."* | 🖥️ Pup |
| 1 | Customer brings the CHF 40 cream. New Sale → camera → won't read the tiny code | *"A CHF 40 product no phone can scan. Sound familiar?"* | 📱 Phone |

### Act II — Confrontation (the build-up)
| # | On screen | Card | Shot |
|---|-----------|------|------|
| 2 | "Not on file → new item." Type name + price (CHF 40.00) | — | 📱 Phone |
| 3 | Tap **"No scannable code → make a label."** Internal code generated, queued | *"Banco just gave it a code it'll never lose."* | 📱 Phone |
| 4 | "Want a picture?" → snap the actual cream | *"Camera's in your hand. One tap."* | 📱 Phone |
| 5 | Add to cart → CHF 40 cash → receipt prints | *"First sale — on an item it had never seen 60 seconds ago."* | 📱 Phone |
| 6 | Scan Gizeh papers (no code) → born once, quick | *"Half your shelf has no code. Same 20 seconds."* | 📱 Phone |
| 7 | Second customer, same cream → scans **instant**: name, price, photo | *"Scan once. Known forever."* | 📱 Phone |

### Act III — Resolution (the payoff)
| # | On screen | Card | Shot |
|---|-----------|------|------|
| 8 | Open catalogue → picture wall that didn't exist this morning | *"No import. No count. You just sold."* | 🖥️ Pup |
| 9 | Count out the drawer (variance) → Z-report (CHF takings, sales log) → print the queued labels | *"Tomorrow it starts telling you what sells."* | 🖥️ Pup |

Target length: 2–5 min. Angel approves each beat before stitch.

---

## Go-Live — what still has to be true (there IS a small plan)

No cutover, but not blind:

1. **Dress rehearsal** (night before / morning of). On the **real device + camera +
   receipt printer**, ring 5–10 throwaway sales through the full loop:
   `scan → born-once → photo → cash → receipt → re-scan-instant`. If the loop holds, the
   shop can open. *(This is also the replay test.)*
2. **Three index cards by the till** (not a FAQ, not tooltips):
   - Can't scan → **type the code**, or **"make a label."**
   - No internet → **[TBD — confirm Banco offline behaviour with Takes]**
   - Stuck → **call Felix / Angel.**
3. **Hypercare.** First day/week, someone owns the day on-call (Felix/Angel). Not
   set-and-forget.

---

## Daily routine (the open/close ritual — one card, not software)

- **Open:** log in → open the cash drawer with a counted float → glance at Shop Pulse
  (system up? right build?).
- **Sell:** ring sales; born-once as new items appear; labels drop into the queue.
- **Close:** count out the drawer (variance) → pull the Z-report → print the day's queued
  labels.

---

## The replay test — `day-one-first-sale`

Beats 1 → 7 **are** the canonical scenario. Asserts:

- unknown scan → **born-once create** *with photo* and *with internal code*
- sells (cash) → **receipt**
- **re-scan resolves instantly** (scan-once-known-forever)
- **no stock count moved** (zero perpetual inventory holds)

Run it against a **fresh empty DB every time** → deterministic, and it kills the
shared-catalogue flake class (e.g. the old `find_product` limit flake). Playwright for the
camera/UI beats; pytest for the API asserts. → Takes.

---

## The demo instance — the one blocker before filming (→ Takes / Angel)

Nothing films until this exists. It's small.

**`sandbox-banco` instance** — URL: `sandbox-banco.lapiazza.app`
- empty database, **auto-seed OFF**, **isolated** from the prod/staging DB
- **served over HTTPS via Caddy** — non-negotiable: the phone camera (`html5-qrcode`)
  needs a secure context; a plain `http://LAN-IP` will *refuse* to open the camera
- one cashier login (`helix_pass`)
- a **one-command wipe-and-reset** so retakes start from empty
- **DNS:** if `*.lapiazza.app` already has a wildcard A record → no DNS change, just a
  Caddy route. If not → one A record `sandbox-banco` → the Hetzner IP (same box as
  `banco.lapiazza.app`). 2 minutes on Porkbun.

---

## Known, deliberately NOT in v1 (the "shop #2" bucket)

These wait behind **Felix saying yes**, not before:

- **German** (then French / Italian) — a bounded i18n sweep (strings → catalogue → locale
  switch, German first; unlocks most of CH + DE/AT). After the demo, not before.
- **In-app tooltips / FAQ / onboarding** — fine to skip for Felix (steward + on-call +
  obvious-by-design); required when shop #2 has no Angel on the phone.

---

*"Win Felix completely → win the category. The engine earns the right to generalize by
working end-to-end for exactly one shop first."*
