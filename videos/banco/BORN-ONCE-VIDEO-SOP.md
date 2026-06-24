# SOP — Born Once Video Production (end-to-end)

*The authoritative record of how we make a Born Once Short, refined over episodes #01–#08
(2026-06-23 → 24). Goal: Angel never re-teaches the procedure; Tigs follows this every time.
Roles: **Angel = voice + approval. Tigs = everything else.***

---

## The format (locked)
- Portrait **1080×1920**, ~**1:30–2:15**, auto-classifies as a YouTube **Short**.
- **Banco Method slideshow:** crisp app screenshots with a red card-bar over the browser chrome +
  dark title cards, cross-faded on the VO beat map, Brotherhood Run bedded at **6%**.
- One recurring world (cast + cream — see `SERIES-BIBLE.md`). Title carries **"#NN"** up front.

## The cycle (the SOP — follow in order)
1. **Premise** — agree the episode premise (one principle, one beat-sheet) before writing.
2. **Script + teleprompter** — Tigs writes `SCRIPT.md` + `TELEPROMPTER.html` (Syd Field 3 acts).
3. **Record (Angel)** — read the teleprompter in **ONE continuous take** (never stitch sections —
   seams cause static pops + tone drift). Note the **start/end timestamps**. Send as a Telegram
   voice message (.ogg).
4. **Process VO (Tigs)** — trim to Angel's marks → `loudnorm I=-16:TP=-1.5` → cap long pauses
   (`silenceremove stop_silence≈0.6 stop_duration≈1.0 threshold≈-38dB`) → 48k mono. Whisper-verify
   the read is complete; flag any single snippet to redo (Angel redoes only that piece).
5. **Capture screens (Tigs)** — Puppeteer drives the app headless and screenshots each beat at a
   portrait viewport (no browser chrome, no upscaling). See "Capture" below.
6. **Build (Tigs)** — `scripts/build_<ep>.py`: PIL composes slides (red bars + cards), ffmpeg
   xfade-chains them on the whisper beat map, mixes VO + music. Outputs the DRAFT mp4.
7. **Captions (Tigs)** — regenerate `CAPTIONS.srt` from the final VO (whisper word-timestamps,
   light spelling fixes). Maps 1:1 because the VO starts at 0:00.
8. **DRAFT → Angel watches → feedback → polish.** Tigs does NOT cut the YouTube package until
   Angel approves. (Ask, don't assume.)
9. **Package (on approval)** — `DESCRIPTION.txt`, `TAGS.txt`, `YOUTUBE-KIT.md` with **title options
   (#NN up front)**. No thumbnail (Shorts have no slot). SRT already done.
10. **Publish (Angel)** → drop the link → Tigs logs it in the kit + series log.

## Capture (Puppeteer) — the technical record
- Host **sandbox-banco.lapiazza.app**; users **pam / ralph / felix**, all `helix_pass`.
- Login flow: click the "Login" control → Keycloak `kc-pos-realm-dev` → fill `#username`/`#password`
  → submit → app. Scripts: `scripts/capture_banco.js` (pam sale flow), `capture_edit.js`
  (`CAP_USER`, manager edit), `capture_drawer.js` (cash shift), `capture_delivery.js` (receiving).
- Viewport `{width:432,height:768,deviceScaleFactor:2.5}` = **1080×1920** crisp portrait.
- Known routes: `/pos/dashboard`, `/pos/catalog`, `/pos/shift` (My Drawer), `/pos/receiving`.
- Reset the sandbox before fresh recordings: `ssh root@46.62.138.218 'cd /opt/helixnet && make sandbox-reset'`.

## Build — the technical record
- Template scripts: `scripts/build_cream03_v2.py` (current canonical), `build_makeproper.py`,
  `build_delivery.py`, `build_felix.py` (has a `prd` badge card), `build_drawer.py`,
  `build_finale.py` (has a drawn `qr` card).
- Canvas/colours/fonts constant across episodes (DejaVuSans-Bold; Banco red #8B0000; card bg
  #0c0e12). **No emoji in PIL cards** (DejaVu won't render colour emoji — use words or drawn shapes).
- xfade T=0.6; each slide input dur = window + T; total ≈ VO length.
- Audio: `amix normalize=0 duration=first`; **atrim the music** (apad alone won't shorten it — that
  bug made a 214s file once). Music fade-out last 3s.

## Honesty rules (non-negotiable)
- Never claim a feature is live if it isn't — frame unbuilt loops as "here's what's coming" (#08).
- Verify the VO transcript is complete before building; verify the final duration + a contact sheet
  before calling it done. Never "fixed" without looking.

## Standard kit per episode (the deliverables)
`*-DRAFT.mp4` · `DESCRIPTION.txt` · `TAGS.txt` · `CAPTIONS.srt` · `YOUTUBE-KIT.md` · (`SCRIPT.md`
+ `TELEPROMPTER.html` source). Media (mp4/wav/ogg) stays local; text kits are committed.

*Pairs with `SERIES-BIBLE.md` (the world) and `memory/banco-born-once-series.md` (the index).*
