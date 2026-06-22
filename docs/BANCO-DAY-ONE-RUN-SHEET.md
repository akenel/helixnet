# Banco — Day One: Run-Sheet (on-set)

*The document you hold while filming. Setup checklist is ready now; the click-for-click
beat steps get filled once Takes lands the born-once/photo/label flow and `sandbox-banco`
is live. Pairs with `BANCO-DAY-ONE-VO-SCRIPT.md` (cards + voice) and `BANCO-DAY-ONE-DEMO.md`.*

---

## 1. Recording setup — DO THIS BEFORE YOU HIT RECORD

### Device & capture quality
- [ ] **Get the RAW file off the phone afterwards — NOT via Telegram.** USB cable, Google
      Drive, or "Save to Files." *(The 22 Jun test came through Telegram and got crushed to
      640×1280 — soft on YouTube. Telegram is for voice notes only, never the video.)*
- [ ] **Check the screen-recorder is at full resolution** (1080p+, high bitrate). Some
      phones default the recorder to "low" — set it to highest before recording.
- [ ] **Show Touches ON** (Developer Options → Show taps). Keep it — viewers see what you
      press. *(It was on in the test. Good.)*
- [ ] Portrait orientation; hold steady or prop the phone. Brightness up.

### Clean screen (no clutter, no interruptions)
- [ ] **Do Not Disturb ON** — silence WhatsApp, messages, badges (the "1" notification).
- [ ] **Kill any media-player notification** — stop whatever's playing so the
      "HelixPOS AI playback" banner over the bottom nav is gone.
- [ ] Close other apps so nothing pops in mid-take.

### Right instance
- [ ] Record on **`sandbox-banco.lapiazza.app`** (empty DB) — **NOT** `staging-banco`
      (full catalogue + the "already logged in" SSO friction).
- [ ] Confirm it's **HTTPS** (it must be — the camera won't open otherwise).
- [ ] Logged in as the demo cashier; battery healthy.
- [ ] Sandbox DB freshly reset (empty catalogue, 0 sales) before the first beat.

---

## 2. The shoot — beat by beat

**How:** record each beat as its own short **silent** clip (no live narration — voice-over
is recorded separately into Telegram afterward). A flubbed beat only costs that beat.
On any real mess-up, **reset the sandbox DB** and retake from a clean slate.

> **⏳ Click-for-click steps: TO BE FILLED.** They point at the exact final buttons, so
> they wait until Takes lands the born-once + photo + label flow and the sandbox is up —
> otherwise a renamed button makes the sheet wrong. Beats and their card/VO are already
> locked in `BANCO-DAY-ONE-VO-SCRIPT.md`.

Beat order to capture (📱 = phone, 🖥️ = Puppeteer card, added later):
- **Cold open** (pain-first): the CHF 40 item the camera can't read 📱
- **Beat 0** — logged-in empty shop, Shop Pulse at zero 📱
- **Beat 1** — camera won't read the tiny barcode 📱
- **Beat 2** — "Not on file → new item": type name + price (CHF 40) 📱
- **Beat 3** — "No scannable code → make a label" (internal code, queued) 📱
- **Beat 4** — "Want a picture?" → snap the real item 📱
- **Beat 5** — add to cart → CHF 40 cash → receipt 📱
- **Beat 6** — Gizeh papers (no code) → born once, quick 📱
- **Beat 7** — second customer, same item → scans **instant** 📱
- **Beat 8** — open catalogue → the picture wall that built itself 📱
- **Beat 9** — close the day: drawer count → Z-report → print queued labels 📱

---

## 3. After EACH take (post-flight — don't skip)
- [ ] Play back **10 seconds** immediately — confirm it captured the **app**, not a frozen
      frame or the desktop. *(The video SOP got burned twice by skipping this.)*
- [ ] If a notification or the media banner snuck in → retake.

## 4. Hand-off
- [ ] Transfer **raw clips** (full resolution) to the shared folder — not Telegram.
- [ ] Record the **voice-over** separately: read each VO line from the script into
      Telegram (one clip per beat). Voice via Telegram is fine; video is not.
- [ ] Ping this terminal — I render the cards, stitch (phone clips + cards + VO + music),
      you approve, we ship to YouTube.
