# Video Production SOP -- Puppeteer + OBS Automated Recording

**SOP-VID-001** | Created: Feb 10, 2026 | Updated: Feb 15, 2026
Invented at McDonald's Trapani | Scene Title Cards invented at PuntaTipa Room 101

---

## What This Is

Automated video production using Puppeteer to drive a browser while OBS records the screen. Tiger writes the script, Angel presses GO, OBS captures it. Scene title cards explain what the viewer is about to see. Background music adds atmosphere.

**Result:** Deterministic, repeatable video recordings. Same quality every take. No voiceover needed -- title cards do the talking.

---

## Prerequisites

| Tool | Purpose | Check |
|------|---------|-------|
| Node.js + Puppeteer | Browser automation + title card screenshots | `node -v` |
| OBS Studio | Screen recording | Open OBS |
| ffmpeg | Trim, stitch, strip audio, add music | `ffmpeg -version` |
| Chrome/Chromium | Launched by Puppeteer | Comes with Puppeteer |
| pactl | Mic muting (PipeWire/PulseAudio) | `pactl info` |

---

## Phase 1: Script Development

### 1.1 Write the Probe Script (optional, first time only)

Discover selectors for the target application:

```bash
node scripts/kc-probe.js
```

This runs headless, logs all buttons/links/data-testid elements, takes screenshots. Use output to write the real recording script.

### 1.2 Write the Recording Script

File: `scripts/{app}-demo-record.js`

**Template structure:**
```javascript
const puppeteer = require('puppeteer');
const { execSync } = require('child_process');
const readline = require('readline');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const PAUSE = {
  SHORT: 2500,    // Quick view
  MEDIUM: 4000,   // Read content
  LONG: 6000,     // Study screen
  XLONG: 8000,    // Money shots
  TYPE: 90,       // Per character (human speed)
};

// Mute all microphones (OBS captures ambient noise)
function muteMicrophones() {
  try {
    const sources = execSync('pactl list sources short', { encoding: 'utf8' });
    sources.split('\n').filter(l => l.trim()).forEach(line => {
      const id = line.split('\t')[0];
      execSync(`pactl set-source-mute ${id} 1`);
    });
    console.log('  Microphones MUTED');
  } catch (e) { console.log('  (mic mute skipped)'); }
}

function unmuteMicrophones() {
  try {
    const sources = execSync('pactl list sources short', { encoding: 'utf8' });
    sources.split('\n').filter(l => l.trim()).forEach(line => {
      const id = line.split('\t')[0];
      execSync(`pactl set-source-mute ${id} 0`);
    });
    console.log('  Microphones UNMUTED');
  } catch (e) {}
}

(async () => {
  muteMicrophones();

  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: null,
    args: ['--no-sandbox', '--ignore-certificate-errors', '--start-fullscreen']
  });
  const page = (await browser.pages())[0];

  // === PRE-FLIGHT OBS CHECK ===
  await page.setContent(`<html><body style="background:#ff0000;display:flex;
    align-items:center;justify-content:center;height:100vh;font-family:Arial">
    <div style="text-align:center;color:#fff">
    <h1 style="font-size:80px">OBS CHECK</h1>
    <p style="font-size:30px">Can you see this RED card in OBS preview?</p>
    </div></body></html>`);

  const rl = readline.createInterface({ input: process.stdin });
  console.log('\n>>> CHECK OBS PREVIEW -- Do you see the RED card?');
  console.log('>>> Press ENTER to start recording...');
  await new Promise(resolve => rl.once('line', resolve));
  rl.close();

  // === SCENES GO HERE ===

  await browser.close();
  unmuteMicrophones();
  console.log('RECORDING COMPLETE');
})();
```

**Key rules:**
- `headless: false` -- browser must be visible for OBS
- `--start-fullscreen` -- TRUE F11 fullscreen (covers taskbar + terminal)
- **NEVER use `--start-maximized`** -- leaves taskbar visible, terminal bleeds through
- Mute mics BEFORE launching Chrome, unmute AFTER closing
- Pre-flight OBS CHECK card with ENTER confirmation -- MANDATORY
- Use `page.goto()` for navigation, NOT dropdown clicks (unreliable)
- Use `humanType()` for credential entry (looks natural on camera)
- PAUSE.XLONG for money shots (8 seconds to let viewer absorb)
- Clear Keycloak SSO cookies with CDP before second-user login (RBAC demos)

### 1.3 Dry Run (Headless)

Write a test version that runs headless with screenshots:

```bash
node scripts/{app}-demo-dryrun.js
```

Check screenshots in `/tmp/`. Verify all selectors work before real recording.

---

## Phase 2: Recording

### 2.1 Setup (30 seconds)

1. **Close ALL browser windows** (Firefox, Chrome, everything)
2. **Minimize terminal/VS Code** (clean desktop)
3. **Open OBS** -- set source to **Screen Capture (PipeWire)**
4. **Verify** OBS preview shows your desktop

### 2.2 Pre-Flight OBS Check (MANDATORY)

5. **Run the recording script** -- `node scripts/{app}-demo-record.js`
6. Script **mutes all microphones** automatically
7. A **bright RED "OBS CHECK"** card appears in FULLSCREEN Chrome
8. **Look at OBS PREVIEW** (not the browser!) -- do you see the red card?
   - **YES:** Hit Record in OBS, then press ENTER in terminal
   - **NO:** STOP. Fix OBS source. You're capturing the wrong screen/window.
9. **Never skip this step.** We have lost recordings to:
   - OBS capturing GNOME Settings instead of browser (ISOTTO demo, Feb 13)
   - OBS capturing wrong window (KC EP series, Feb 10)

### 2.3 Record (2-5 minutes)

10. **Don't touch ANYTHING** -- Chrome runs in F11 fullscreen, script drives all clicks
11. **Wait for** "RECORDING COMPLETE" in terminal
12. **Stop OBS recording**
13. Script **unmutes microphones** automatically

### 2.4 Verify (MANDATORY)

14. **IMMEDIATELY play 10 seconds** of the raw recording
15. Confirm you see the INTRO card or browser content -- NOT your desktop, NOT a terminal
16. If it's wrong, re-record NOW while the stack is still running
17. Check OBS output folder: `/home/angel/Videos/OBS/`

---

## Phase 3: Post-Production

### 3.1 Strip Audio + Verify Content

Always strip audio from raw recording (OBS captures ambient noise even from "silent" rooms):

```bash
# Step 0: Verify what we captured (extract frame at 10s)
ffmpeg -y -ss 10 -i raw-recording.mp4 -vframes 1 verify-frame.jpg
# LOOK AT IT. If it shows your desktop, STOP. Re-record.

# Step 1: Strip audio
ffmpeg -y -i raw-recording.mp4 -an -c:v copy silent.mp4
```

### 3.2 Trim

Cut pre-roll (before Chrome content) and post-roll (after Chrome closes):

```bash
ffmpeg -y -i silent.mp4 -ss START_SEC -to END_SEC -c copy content-trimmed.mp4
```

**How to find trim points:**
- Extract frames: `ffmpeg -ss N -i video.mp4 -vframes 1 frame.jpg`
- Start: first frame with app content (after OBS CHECK card)
- End: last frame before outro card / Chrome close

### 3.3 Re-encode Content (IMPORTANT)

Re-encode trimmed content to match intro/outro encoding. This prevents timestamp metadata issues with ffmpeg concat:

```bash
ffmpeg -y -i content-trimmed.mp4 -c:v libx264 -crf 18 -preset slow \
  -pix_fmt yuv420p -r 30 -an content-fixed.mp4
```

**Why:** Raw OBS recordings have different codec parameters than intro/outro clips created from PNGs. Without re-encoding, `ffmpeg -f concat -c copy` produces videos with broken timestamps and seeking.

### 3.4 Create Intro/Outro

1. Edit `intro.html` and `outro.html` (dark theme, 1920x1080)
2. Screenshot with Puppeteer at 1920x1080
3. Create video clips from stills:

```bash
ffmpeg -y -loop 1 -i intro.png -c:v libx264 -t 4 -pix_fmt yuv420p -r 30 intro-clip.mp4
ffmpeg -y -loop 1 -i outro.png -c:v libx264 -t 5 -pix_fmt yuv420p -r 30 outro-clip.mp4
```

### 3.5 Choose Post-Production Path

You now have THREE options:

**Option A: Baked-in Intro/Outro (PREFERRED -- CT EP1 Method)**
```
Recording script renders intro card + demo + outro card inside the browser.
Post-production = strip audio + trim OBS CHECK from start.
NO separate stitch step. Fastest pipeline.
```
Use when: recording script handles everything (Puppeteer renders cards inline).
Result: single clean MP4 ready for YouTube.

**Option B: Simple Stitch (voiceover or silent)**
```
intro-clip.mp4 + content-fixed.mp4 + outro-clip.mp4
```
Use when: voiceover will be added, or content is self-explanatory.

**Option C: Scene Title Cards (ISOTTO Method)**
```
intro + [card-1 + scene-1 + card-2 + scene-2 + ...] + outro
```
Use when: no voiceover, viewer needs context for each scene.

See Phase 3B below for the scene title card workflow.

### 3.6 Verify Final

- Play the full video start to finish
- Check: intro appears, content plays, outro appears
- Check: no black frames at transitions
- Check: audio level is appropriate (if music added)

---

## Phase 3B: Scene Title Cards (The ISOTTO Method)

*Invented Feb 13, 2026 -- PuntaTipa Room 101, 11:00 PM*

Instead of voiceover narration, insert text slides between scenes. Each card tells the viewer what they're about to see. Subtle background music provides atmosphere.

**Why this is better than voiceover:**
- No re-recording when script changes -- just update the card text
- Works in any language -- change the text, not the voice
- Professional look -- dark themed cards matching intro/outro
- Faster production -- no voice recording, no audio sync, no retakes
- Repeatable -- same pipeline every time

### 3B.1 Map Scene Boundaries

Extract frames every 2-4 seconds from the content video:

```bash
for t in $(seq 0 2 170); do
  ffmpeg -y -ss $t -i content.mp4 -vframes 1 frame-${t}s.jpg 2>/dev/null
done
```

Review frames to identify scene transitions. Record exact second for each:

| Scene | Start | End | Content |
|-------|-------|-----|---------|
| 1 | Xs | Ys | Description |
| 2 | Ys | Zs | Description |
| ... | | | |

**Cut at clean moments** (page fully loaded, not mid-navigation). Title cards hide the messy transition frames between scenes.

### 3B.2 Create Scene Title Card Generator

Create a Node.js script that generates PNG screenshots of title cards:

```javascript
// scene-cards-generator.js
const SCENES = [
  { num: 1, titleIT: 'Italian Title', titleEN: 'English Title',
    icon: '&#x1F512;', bullets: ['Point 1', 'Point 2', 'Point 3'] },
  // ...
];
```

**Title card design rules:**
- Match intro/outro theme (dark background #0a0a0a, blue accent #2563eb)
- Scene number ("SCENE 1 OF 7")
- Italian title (large, 56px, white)
- English subtitle (smaller, 22px, gray)
- Blue divider line
- 3 bullet points describing what viewer will see
- Brand footer at bottom
- 1920x1080 PNG output

### 3B.3 Create Title Card Video Clips

```bash
# 7 seconds per card (enough time to read 3 bullet points + 3s buffer)
for i in 1 2 3 4 5 6 7; do
  ffmpeg -y -loop 1 -i scene-card-${i}.png \
    -c:v libx264 -t 7 -pix_fmt yuv420p -r 30 -an card-${i}.mp4
done
```

### 3B.4 Extract Scene Clips

```bash
# Re-encode each scene to match card encoding
ffmpeg -y -ss START -to END -i source.mp4 \
  -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -r 30 -an scene-N.mp4
```

### 3B.5 Stitch with Title Cards

```bash
cat > concat-titled.txt <<EOF
file 'intro-clip.mp4'
file 'card-1.mp4'
file 'scene-1.mp4'
file 'card-2.mp4'
file 'scene-2.mp4'
...
file 'outro-clip.mp4'
EOF

ffmpeg -y -f concat -safe 0 -i concat-titled.txt -c copy TITLED.mp4
```

### 3B.6 Add Background Music

**Two-step method** (avoids filter_complex + streamcopy conflict):

```bash
# Step 1: Process music separately (trim, volume, fades)
ffmpeg -y -i music.mp3 \
  -af "atrim=0:VIDEO_DURATION,asetpts=PTS-STARTPTS,volume=LEVEL,afade=t=in:st=0:d=2,afade=t=out:st=FADE_START:d=3.5" \
  -c:a aac -b:a 128k -ar 48000 music-processed.m4a

# Step 2: Mux video + processed audio (no re-encode!)
ffmpeg -y -i video.mp4 -i music-processed.m4a -c:v copy -c:a copy -shortest FINAL.mp4

# Step 3: Clean up
rm music-processed.m4a
```

**Volume levels:**
- **Music-only (no voice):** `volume=0.35-0.40` -- present, sets the mood, not overwhelming
- **Music under voiceover:** `volume=0.10-0.15` -- barely audible, voice dominates
- **Rule of thumb:** If you can't hear it on laptop speakers, it's too quiet. If you notice it more than the content, it's too loud.

**Music source -- ALWAYS use royalty-free for YouTube:**
- **Kevin MacLeod (incompetech.com)** -- CC BY 4.0, 2000+ tracks, proven
- Add credit in YouTube description: `"Track Name" by Kevin MacLeod (incompetech.com) / Licensed under Creative Commons: By Attribution 4.0`
- Browse by feel: incompetech.com → filter by "Bright", "Calm", "Warm"
- **DO NOT use sunrise-chain library on YouTube** -- copyrighted tracks trigger Content ID

**Proven tracks:**
| Track | Feel | Used On |
|-------|------|---------|
| Wholesome | Warm, positive, homey | CT EP1 (camper shop) |
| Slow Burn | Gentle, atmospheric | ISOTTO Demo (print shop) |

**Fade timing:**
- Fade-in: 2s (subtle entrance)
- Fade-out: 3-3.5s before video end (clean exit, no abrupt cut)
- `FADE_START` = VIDEO_DURATION - 3.5

---

## Phase 4: Distribution

### 4.1 File Organization

**Main folder = YouTube upload kit.** 5 files max. Everything else goes in `arc/`.

```
videos/{app}/DEMO-{feature}/
├── {APP}-EP{N}-{Title}.mp4            <- FINAL VIDEO (upload this)
├── {APP}-EP{N}-YOUTUBE-DESCRIPTION.txt <- Select all, paste into YouTube
├── {APP}-EP{N}-YOUTUBE-TAGS.txt       <- Copy-paste into YouTube tags
├── thumbnail.png                       <- Upload as custom thumbnail
├── thumbnail.html                      <- Source (for future edits)
└── arc/                                <- ALL production artifacts
    ├── Raw OBS .mp4 recordings
    ├── silent.mp4, trimmed.mp4         <- Intermediate steps
    ├── wholesome-kevin-macleod.mp3     <- Music source file
    ├── voiceover-script.md             <- Script / scene descriptions
    ├── EP{N}-{episode}/                <- Recording scripts, card generators
    ├── voice-recordings/               <- Voiceover .ogg files (if used)
    ├── intro-clip.mp4, outro-clip.mp4  <- Separate clips (if used)
    ├── Old takes, concat.txt, etc.
    └── take{N}-frames/                 <- Debug frame extractions
```

**Naming convention:** `{APP}-EP{N}-{Short-Title}.mp4`
- `CT-EP1-First-Impressions.mp4`
- `ISOTTO-Demo-Titled.mp4`
- `KC-EP5-RBAC-Deep-Dive.mp4`

**Rule:** If you can't upload it to YouTube or edit it for the next video, it goes in `arc/`. The main folder should be so clean you can hand someone a USB and say "upload everything in here."

### 4.2 Git vs GDrive

| What | Where | Why |
|------|-------|-----|
| HTML, MD, JS, SH files | GitHub | Small, editable, versioned |
| MP4 video files | Google Drive / YouTube | Large binary, not for git |
| PNG screenshots | Local only | Regenerable from HTML |

### 4.3 YouTube Kit (create BEFORE uploading)

Every video needs a complete YouTube kit. Create these files during post-production:

**1. Tags file** (`{APP}-EP{N}-YOUTUBE-TAGS.txt`)
- Comma-separated keywords, one line, copy-paste into YouTube tags field
- Mix broad terms (camper, vanlife, workshop) with specific features shown in the episode
- Include: business name, location, tech stack keywords, feature names
- Create during post-production -- don't leave it for upload time

**2. Description file** (`{APP}-EP{N}-YOUTUBE-DESCRIPTION.txt`)
- **Max 5000 characters** (YouTube limit) -- aim for 4500-4800
- Must be select-all-paste-ready (no editing needed at upload time)
- Structure:
  ```
  Title line

  Hook (1-2 sentences)

  Context paragraph (what this is, who it's for)

  CHAPTERS:
  0:00 Intro
  0:04 Scene 1
  ...

  WHAT THIS SYSTEM DOES:
  (detailed feature descriptions)

  BUILT WITH:
  (tech stack)

  MUSIC:
  "Track Name" by Kevin MacLeod (incompetech.com)
  Licensed under Creative Commons: By Attribution 4.0

  ---
  Business contact info

  "Signature quote"

  #tag1 #tag2 #tag3 ...
  ```
- Tags go at the BOTTOM of description (YouTube reads them)
- Music credit is MANDATORY for CC BY tracks
- Verify char count: `wc -c DESCRIPTION.txt` (must be < 5000)

**3. Thumbnail** (`thumbnail.html` + `thumbnail.png`)
- 1280x720 pixels (YouTube standard)
- **Big fonts** -- must be readable on mobile phone screens
- Title: 100-130px, subtitle: 30-36px, stat numbers: 50px+
- Dark background with brand accent color
- Generate: `node -e "..." > thumbnail.png` (Puppeteer screenshot)
- Match the video's visual theme (same colors as intro/outro)

**4. Title** (under 70 chars)
- Format: `{Business} -- {Feature} | EP{N}: {Subtitle}`
- Example: `Camper & Tour -- Service Management System | EP1: First Impressions`

### 4.4 YouTube Upload Checklist

- [ ] Upload MP4
- [ ] Paste description from .txt file (select all, paste)
- [ ] Upload custom thumbnail (thumbnail.png)
- [ ] Set title
- [ ] Verify chapters appear in timeline after processing
- [ ] Set visibility (unlisted for review, public when ready)

---

## Lessons Learned (The Hard Way)

### OBS Captures the Wrong Thing (Feb 10 + Feb 13, 2026)
- OBS captured the WRONG window/screen on TWO separate occasions
- First time: KC episode, captured wrong window
- Second time: ISOTTO demo, every frame was GNOME Wi-Fi Settings panel
- **Fix:** Mandatory RED "OBS CHECK" card with ENTER confirmation
- **Rule:** If you don't see the red card in OBS preview, DO NOT proceed

### Terminal Bleeds Through (Feb 13, 2026)
- `--start-maximized` leaves the terminal visible on half the screen
- **Fix:** Use `--start-fullscreen` (true F11 mode, covers taskbar + everything)
- **Rule:** NEVER use `--start-maximized` for recording scripts

### Microphone Left On (Feb 13, 2026)
- OBS recorded ambient noise even in "quiet" rooms
- Stripping audio in post works, but adds an unnecessary step
- **Fix:** Script mutes all mic sources with `pactl` before recording
- **Rule:** Always mute programmatically, don't trust manual OBS settings

### Re-encode Before Concat (Feb 13, 2026)
- Raw OBS recordings + PNG-based clips have different codec parameters
- `ffmpeg -f concat -c copy` produces broken timestamps
- **Fix:** Re-encode content with matching params: `-c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -r 30`
- **Rule:** Always re-encode trimmed content before stitching

### Keycloak SSO Session Persists (Feb 13, 2026)
- Logging out of app doesn't clear KC session cookies
- Second user login auto-redirects back as first user
- **Fix:** Clear cookies via CDP: `client.send('Network.clearBrowserCookies')`
- **Rule:** Always clear cookies before switching users in RBAC demos

---

## Quick Reference Card

```
PREFLIGHT:
  Run script → RED card appears → Check OBS preview → ENTER

RECORD:
  Script runs (fullscreen) → Wait → "RECORDING COMPLETE" → Stop OBS
  → Play 10s to verify content

POST-PRODUCTION (Baked-in -- FASTEST):
  Strip audio → Trim OBS CHECK → Done. Final MP4 ready.

POST-PRODUCTION (Simple Stitch):
  Strip audio → Trim → Re-encode → Intro/Outro → Stitch → Verify

POST-PRODUCTION (Scene Title Cards):
  Strip → Trim → Re-encode → Map scenes → Generate cards → Split → Stitch → Music

MUSIC (royalty-free only for YouTube!):
  Music-only: volume=0.40 | Under voice: volume=0.12
  Fade in 2s → Fade out 3.5s → Two-step method (process audio, then mux)

YOUTUBE KIT:
  Description.txt (< 5000 chars) + Tags.txt + thumbnail.png (1280x720) + title (< 70 chars)

TRIM VERIFICATION:
  Extract end frames → Find exact transition → Cut 0.5s BEFORE junk appears

COMMANDS:
  STRIP:    ffmpeg -i raw.mp4 -an -c:v copy silent.mp4
  TRIM:     ffmpeg -i silent.mp4 -t END_SEC -c copy trimmed.mp4
  REENCODE: ffmpeg -i trimmed.mp4 -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -r 30 fixed.mp4
  CARD:     ffmpeg -loop 1 -i card.png -c:v libx264 -t 7 -pix_fmt yuv420p -r 30 card.mp4
  STITCH:   ffmpeg -f concat -safe 0 -i list.txt -c copy output.mp4
  MUSIC-1:  ffmpeg -i music.mp3 -af "atrim=0:DUR,volume=0.40,afade=in:d=2,afade=out:st=X:d=3.5" -c:a aac -ar 48000 music.m4a
  MUSIC-2:  ffmpeg -i video.mp4 -i music.m4a -c:v copy -c:a copy -shortest FINAL.mp4
```

---

## Production Log

| Date | Video | Takes | Notes |
|------|-------|-------|-------|
| Feb 10 | KC EP4 | 2 | First production. OBS wrong window on take 1. |
| Feb 11 | KC EP5 | 1 | Voiceover pipeline invented (Telegram → Whisper → ffmpeg) |
| Feb 11 | KC EP6 | 1 | Clean run |
| Feb 13 | ISOTTO Demo | 3 | Take 1: OBS captured GNOME Settings. Take 2: terminal visible + mic on. Take 3: GOLD. Scene title card method invented in post. |
| Feb 15 | CT EP1 - First Impressions | 2 | Take 1: bad timing, alt-tab visible. Take 2: GOLD. Baked-in intro/outro method -- no separate stitch step. Folder cleanup SOP added. |
| Feb 15 | CT EP2 - Quote to Invoice | 1 | Clean run. YouTube kit + post-production in one session. |
| Feb 16 | CT EP3 - The Full Lifecycle | 3 | Take 1: broken logout + quotation error. Take 2: logout fixed, quotation still broken. Take 3: GOLD. Fixed Alpine.js row clicks, re-encode trim for intro card. Chrome translate hack for English. |
| Feb 16 | CT EP4 - The Workshop Floor | 2 | Take 1: empty appointments (stale seed data). Take 2: same seed issue but walk-in + bay timeline GOLD. Baked-in pipeline, 1:38 final. Tags file added to SOP. |

---

## Lessons Learned (continued)

### Bake Intro/Outro Into the Recording Script (Feb 15, 2026)
- Old method: record raw, trim, create separate intro/outro clips, re-encode, stitch
- New method: Puppeteer renders intro card -> demo -> outro card inside the browser
- Post-production = just strip audio + trim OBS CHECK from start
- **Saves 30+ minutes** of post-production per video
- **Rule:** If the recording script can render cards inline, do it. Only use separate stitch for complex multi-take edits.

### Verify Trim Points Frame-by-Frame (Feb 15, 2026)
- First trim of CT EP1 cut at 153s -- 2 seconds of terminal/desktop leaked into the final video
- The outro card ended at 150.5s but we didn't check precisely enough
- **Fix:** Extract frames at 0.5s intervals near the cut point: `ffmpeg -ss N.5 -i video.mp4 -frames:v 1 frame.jpg`
- Find the EXACT frame where junk appears, then cut 0.5s BEFORE it
- **Rule:** Always verify the last 3-4 frames of the final video. Desktop/terminal leak is the #1 amateur mistake.

### No Angled Brackets in YouTube Descriptions (Feb 16, 2026)
- YouTube strips `<` and `>` characters from descriptions
- Arrows like `->` get broken -- use `to` or a dash instead
- Example: "Simona to Nino" not "Simona -> Nino"
- **Rule:** Never use `<`, `>`, or `->` in YouTube description text files

### Stream Copy Skips Keyframes on Trim (Feb 16, 2026)
- `ffmpeg -ss 35 -c:v copy` can only cut at keyframes
- If the intro card is between keyframes, it gets skipped entirely
- First take of CT EP3 started at the login page -- missing the entire intro card
- **Fix:** Use `-c:v libx264` (re-encode) when trimming, not `-c:v copy`
- **Rule:** When precision trim matters (intro cards), always re-encode

### Alpine.js @click Rows Don't Work in Puppeteer (Feb 16, 2026)
- Table rows with `@click="window.location.href=..."` won't navigate when clicked via `page.evaluate(() => row.click())`
- `document.querySelector('a[href*="/quotations/"]')` matched the "New Quotation" BUTTON, not a table row
- This navigated to `/camper/quotations/new` which tried to load quotation ID "new" from the API
- **Fix:** Fetch entity IDs from the API with the session token, then `page.goto()` directly
- **Rule:** For Alpine.js apps, never click table rows in Puppeteer -- navigate by URL

### Clean Folders Make YouTube Loading Faster (Feb 15, 2026)
- After post-production, folders had 10+ files mixed together
- Raw recordings, intermediates, frames, debug files -- all in one place
- Finding the final MP4 = digging through junk
- **Fix:** Main folder = ONLY final MP4 + production sources. Everything else in `arc/`
- **Rule:** If you can't upload it or edit it, it goes in `arc/`

---

*"You write a script, I press the clicker, OBS does the rest."*
*Invented Feb 10, 2026 -- McDonald's Trapani, 9:20 PM*

*"Title cards do the talking. Music sets the mood. No voice needed."*
*The ISOTTO Method -- Feb 13, 2026 -- PuntaTipa Room 101, 11:00 PM*

*"Bake the intro into the script. One file in, one file out."*
*The CT Method -- Feb 15, 2026 -- PuntaTipa Room 101*
