# Training-Video SOP — Voiceover Walkthrough Mode

**SOP-VID-002** | Created: 2026-06-02 | Mode: Human walkthrough + live voiceover
**Companion to:** `videos/keycloak/VIDEO-PRODUCTION-SOP.md` (SOP-VID-001, Puppeteer + title-card mode)

This file doubles as **(a) the spec for the Locandina training video** AND **(b) the copyable template for future training videos** (rename the folder, edit §3 + §5).

---

## INPUT → PROCESS → OUTPUT

- **Input:** a shipped, prod-verified La Piazza feature you want to teach + 25–45 min of focused recording time.
- **Process:** pre-flight (audio!) → script the shots → record screen + voice live → trim/normalize → kit folder ready.
- **Output:** one MP4 + a YouTube/social description + thumbnail screenshot, all in `kit/`.

---

## 1. Pre-flight (MANDATORY — do not skip even when "I know what I'm doing")

This list exists because Angel lost 25 minutes of a real recording on 2026-06-02 with the mic muted. Run it. Every time.

1. **AUDIO CHECK — the one that bit us:**
   ```bash
   # Show the default input source and its mute status. If "Mute: yes" → unmute.
   pactl list sources | grep -E "Name:|Mute:|Description:" | head -20
   # Quick mute toggle:
   pactl set-source-mute @DEFAULT_SOURCE@ false
   # 10-second test recording (talk into the mic):
   ffmpeg -f pulse -i default -t 10 -y /tmp/mic-test.wav 2>&1 | tail -3
   ffprobe /tmp/mic-test.wav 2>&1 | grep -E "Duration|Stream"
   # Play it back. If you hear silence, FIX BEFORE RECORDING.
   aplay /tmp/mic-test.wav 2>&1 | tail -2
   ```
2. **OBS source check** — open OBS, confirm the scene shows your *Audio Input Capture* level meter moving when you talk. If the meter doesn't bounce, OBS isn't seeing the mic regardless of pactl.
3. **OBS source check #2** — confirm the *Screen Capture* (NOT Window Capture) source is selected. Window Capture has bitten us twice (Keycloak EP, ISOTTO demo) by recording the wrong window.
4. **Phone notifications OFF** (Slack, Telegram, system alerts mid-record).
5. **Browser zoom = 100%** and **window size predictable** (1920×1080 is the reliable default).
6. **Tabs closed except the ones the script needs** — surprise tabs leak personal context into prod recordings.
7. **Disk space:** `df -h ~/Videos` — at least 5GB free. OBS at 1080p eats ~150MB/min.

⛔ **STOP rule:** if even one of the seven items above fails, fix it before pressing Record. The cost of a re-take is real (25 min, ask Angel).

---

## 2. Post-flight (run within 60 seconds of pressing Stop)

1. **Verify audio is in the file:**
   ```bash
   F="/home/angel/Videos/OBS/<file>.mp4"
   ffprobe -v error -show_streams "$F" 2>&1 | grep -E "codec_type|codec_name"
   # Must show BOTH a video stream AND an audio stream. If audio missing → discuss before discarding.
   ```
2. **Visual sanity:** extract a frame at ~10s into the recording — does it show the browser/feature, or your desktop?
   ```bash
   ffmpeg -ss 10 -i "$F" -frames:v 1 -y /tmp/sanity-frame.png 2>/dev/null
   xdg-open /tmp/sanity-frame.png
   ```
3. If both pass → move the file from `~/Videos/OBS/` into `videos/<feature>/raw/` with a clean name.

---

## 3. Spec — Locandina training video (this one)

### What it demonstrates
The printable A6 event flyer feature. Owner clicks **Locandina** on an event, picks a language, edits the AI-summary, downloads a print-ready PDF that prints 4 cards per A4 sheet.

### Target audience
A real human owning an event listing on La Piazza. Not a developer. Not a CTO.

### Length budget
**3–5 minutes** of final cut. Anything longer is a tutorial, not a demo.

### Hero shot
The downloaded PDF opened in a viewer — the four identical cards on one A4 sheet — followed by the printed paper held up to the camera (if you can physically print mid-record). That's the "I get it" moment.

---

## 4. Shot list (write yours in `shot-list.md`, this is the starting frame)

| # | Shot | Roughly | Notes |
|---|---|---|---|
| 1 | Title slate (Inkscape or in-app) | 3s | "La Piazza — Event Flyer in 30 seconds" |
| 2 | The event listing page | 8–10s | Hover the new "Locandina" button — show it's *there* |
| 3 | Click → preview opens | 5s | Pause on the language picker |
| 4 | AI summary populated | 8s | Read it on screen ("here's what AI suggested") |
| 5 | Edit the summary live | 10–15s | Char-counter visible — your voiceover explains why we cap |
| 6 | Download PDF | 5s | Quick — emphasise filename ends in `.pdf`, not gibberish |
| 7 | Open PDF in viewer | 8s | The four cards on one sheet. Money shot. |
| 8 | Print instructions panel | 6s | Read the "100% scale, no fit-to-page" line out loud |
| 9 | (Optional) physical print held up | 6s | Cut along the lines, hold one card up |
| 10 | End slate + URL | 4s | "lapiazza.app — make an event, print the card" |

---

## 5. Voiceover script (live, in `script.md`)

Live voiceover during the record (don't post-dub unless you have to). Keep it conversational — you're the friend showing a neighbour how to use the new thing, not the corporate narrator.

Two cheat lines that worked in past LP videos:
- *"No fees. No login required to scan. The QR opens La Piazza for the buyer."* (trust line)
- *"You cut along the line with scissors. The thin white border is your tolerance — slightly off is fine."* (print line)

---

## 6. Post-production (after the post-flight)

If you got clean live audio → the trim + normalize is the whole job. Don't add background music to a voiceover video — it competes with your voice. End slate music optional (last 4s only).

```bash
# Trim head/tail dead air, normalize voice loudness, output to kit/
INPUT="videos/locandina/raw/take-N.mp4"
ffmpeg -ss <start> -to <end> -i "$INPUT" \
  -c:v libx264 -crf 20 -preset slow \
  -af "loudnorm=I=-16:LRA=11:TP=-1.5" -ar 48000 -c:a aac -b:a 192k \
  -y videos/locandina/kit/locandina-demo-v1.mp4
```

(If audio is missing entirely → see `videos/locandina/voice-recordings/README.md` once we write it. The Whisper + per-clip pipeline from `videos/keycloak/` works for silent-source rescue; mention it in §7 below.)

---

## 7. Kit deliverables (what lands in `kit/` when you're done)

- `locandina-demo-v1.mp4` — final cut, 3–5 min, with audio
- `locandina-demo-thumb.png` — single 1920×1080 frame for YouTube thumbnail
- `locandina-demo-description.txt` — YouTube/X description, ≤ 5000 chars, **no `<` or `>` characters** (YouTube strips them — see memory: `YouTube Description Rules`)
- `locandina-demo-chapters.txt` — chapter timestamps starting at `0:00`
- `locandina-demo-transcript.txt` — Whisper transcript for accessibility / search

---

## 8. After ship — close the loop

- File a backlog entry: "Locandina training video shipped (commit `<sha>`, URL `<youtube link>`)"
- Add the YouTube URL to `videos/locandina/kit/README.md` so future-you can find the published version
- Update this SOP only if something bit you that wasn't already in §1 pre-flight. The whole point of the file is it gets sharper each time.

---

## Carry-forward checklist (for the NEXT training video that copies this folder)

```
cp -r videos/locandina videos/<next-feature>
# Then edit: §3 spec, §4 shot list, §5 script lines, §7 file names
# Pre-flight (§1) and post-flight (§2) stay identical — they're the studs.
```

That's the test of whether this SOP is real: the pre-flight + post-flight + structure survive a feature swap. The content is the variable.
