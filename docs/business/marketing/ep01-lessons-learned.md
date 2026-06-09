# Lessons Learned — Shipping Episode 1 (2026-06-09)
*From the OBS tape (~65 min, the real upload grind) + the session. The recipe → real-world → report → tune loop, applied to ourselves.*

## What the tape shows
~65 minutes for ONE upload: heavy **context-switching** between the chat and YouTube Studio, the full
flow (details → thumbnail → cards → captions → publish), then LinkedIn + answering a comment. Real
struggles, some "where is X / what do I say" stalls. It worked — Ep 1 is live — but it was slow.

## The lessons
1. **A 65-min first upload is NORMAL — don't judge the process by it.** First time = learning YouTube's
   flow + captions + cards + thumbnail all at once. Routine, it's ~10 min. The cost is front-loaded.
2. **The real drag was context-switching + mid-flow questions** ("where's the .srt", "how do cards
   work", "what goes in the description"). Every time he left YouTube to come ask, momentum died.
   → **Fix: the ship-sheet must be 100% self-contained** — every field pre-written, every file linked,
   every YouTube quirk (cards, end-screen, captions) explained IN the sheet. We patched it live; now
   it's baked, so Ep 2's sheet is zero-question.
3. **Automate the recurring.** Don't do the 65-min dance 12 times. `scripts/yt_upload.py` turns the
   whole manual flow into one command after a one-time Google auth. Biggest single time-saver ahead.
4. **The OBS footage IS an asset** — "watch me ship my first episode in public" is itself build-in-public
   content. The struggle is the story.
5. **Energy management: the upload is mechanical; distribution is the real work.** Don't let the upload
   burn the fire you need for Reddit/Telegram/LinkedIn. Upload fast, distribute hard.
6. **What was missing becomes the checklist.** Every stall on the tape → a line in the ship-sheet so it
   never happens again. The gaps are the gift.

## Forward fix (so Ep 2 ships in minutes, not an hour)
- The ship-sheet is now complete (download, title, desc, tags, thumbnail, captions, playlist, cards,
  end-screen) — Ep 2 just swaps the content.
- Music-only episodes skip the voiceover + captions entirely → far less to do.
- Do the one-time `yt_upload.py` auth once → future publishes are a single command.
- Keep the OBS rolling occasionally — it's free content.
