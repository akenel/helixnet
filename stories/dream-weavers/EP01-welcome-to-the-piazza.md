# 🎬 EP 1 — "Welcome to the Piazza" · SHOOTING SCRIPT
*Dream Weavers · @theSAPspecialist · target ~3:00 · record on **staging** (resets, safe)*

**Goal of the episode:** hook the viewer, say what La Piazza is in plain words, show a real sign-up
in one motion, and tease the season (Mike, the crane, the cookies). Teaches: **what it is + how to
get in.** LEGO-simple — no jargon.

**You'll need open before you hit record:**
- A fresh **+alias** email ready (e.g. `angel.kenel+ep1@gmail.com`) to sign up live as a "new neighbour".
- Tab 1: `https://staging.lapiazza.app` (the Square). Tab 2: `https://staging-bottega.lapiazza.app/get-started`.
- OBS: **Screen Capture** source confirmed in preview (NOT Window Capture). Mic for voiceover (or record VO after).

---

## THE SCRIPT (voiceover in *italics*, action in **bold**)

### 0:00 – 0:12 · COLD OPEN (the hook)
**[Intro card on screen 2s]** → cut to the La Piazza home.
*"What if your whole neighbourhood had a town square — to lend, borrow, learn, sell, and help each
other — with no fees, no middlemen, and nobody selling your data? That's La Piazza. Let me show you."*

### 0:12 – 0:45 · WHAT IT IS (plain words)
**Slowly scroll the Square home** (browse, a few real listings — the persona items).
*"It's open-source. It's free, forever. Your neighbours post things they'll lend, skills they'll
teach, events, a help board when they're stuck. You see it, you reach out, you meet. That simple —
like the old town square, just online."*

### 0:45 – 2:05 · GET IN (sign up, one motion — the wow)
**Tab 2 → `/get-started`.** Type a name + the `+ep1` email + a password (+ optionally drop a CV or
just one sentence: *"I fix old motorbikes and love to cook."*). **Click → land logged in.**
*"Signing up is one motion. Tell it who you are — even one sentence — and it builds your little
workshop for you: your profile, your skills, the lot. Thirty seconds, and you're a member. No forms,
no fees."*
**Show the result:** the profile/storefront it built. Quick pan over the nav (Square · Workshop · You).

### 2:05 – 2:40 · THE SEASON TEASE (Mike, the crane, the cookies)
**Cut to the Help Board / Mike's event page (briefly).**
*"Over this series, you'll watch the neighbourhood actually use it. Our neighbour Mike asks for 'a
little help' moving his garage… turns out it's a thousand-pound crane that needs twenty hands — and
his sister Sally, who can't leave the house, holds the whole thing together with a tray of cookies.
You'll learn every part of La Piazza by watching them pull it off."*

### 2:40 – 3:00 · OUTRO
*"Next episode: how Mike asks the whole neighbourhood for help — the Help Board. Subscribe so you
don't miss the crane. I'm the SAP Specialist — and I built this. Link's below. A presto."*
**[Outro card 3s → end]**

---

## 🎥 SHOT-LIST (the cuts, in order)
1. Intro card (2s)
2. Square home — slow scroll (hold on 2–3 real listings)
3. `/get-started` — type name/email/password (+ the one-sentence "about you")
4. Click → the logged-in landing / the built profile
5. Quick nav pan (Square · Workshop · You)
6. Help Board / Mike's event (3–4s tease)
7. Outro card (3s)

## ⚙️ POST (per the video SOP)
- **Strip ambient audio** from the raw OBS file; lay the **voiceover** over it; loudnorm @ 48 kHz.
- **Music:** cleared/royalty-free only (YouTube Audio Library or your own) — *not* the sunrise-chain
  (Content-ID claim). Keep it low under the VO.
- Stitch: **intro-card + body + outro-card**. Trim with `-c:v libx264` (re-encode, not `-c copy`).
- Title (no `<>` or `->`): **"La Piazza Ep 1 — A Town Square With No Fees, No Middlemen (Welcome)"**
- Description: 2–3 lines + chapters from `0:00` + the staging/live link.
- **Pre-flight:** play 10s of the raw recording first — confirm it shows the browser, not the desktop.

*Cards: `stories/dream-weavers/cards/ep01-intro.html` + `ep01-outro.html` (screenshot at 1920×1080).*
