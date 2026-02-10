# Video Production SOP -- Puppeteer + OBS Automated Recording

**SOP-VID-001** | Created: Feb 10, 2026 | Invented at McDonald's Trapani

---

## What This Is

Automated video production using Puppeteer to drive a browser while OBS records the screen. Tiger writes the script, Angel presses GO, OBS captures it. Voiceover added later in post.

**Result:** Deterministic, repeatable video recordings. Same quality every take.

---

## Prerequisites

| Tool | Purpose | Check |
|------|---------|-------|
| Node.js + Puppeteer | Browser automation | `node -v` |
| OBS Studio | Screen recording | Open OBS |
| ffmpeg | Trim, stitch, strip audio | `ffmpeg -version` |
| Chrome/Chromium | Launched by Puppeteer | Comes with Puppeteer |

---

## Phase 1: Script Development

### 1.1 Write the Probe Script (optional, first time only)

Discover selectors for the target application:

```bash
node scripts/kc-probe.js
```

This runs headless, logs all buttons/links/data-testid elements, takes screenshots. Use output to write the real recording script.

### 1.2 Write the Recording Script

File: `scripts/kc-record-epN.js`

**Template structure:**
```javascript
const puppeteer = require('puppeteer');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const PAUSE = {
  SHORT: 2500,    // Quick view
  MEDIUM: 4000,   // Read content
  LONG: 6000,     // Study screen
  XLONG: 8000,    // Money shots
  TYPE: 90,       // Per character (human speed)
};

(async () => {
  console.log('>>> Chrome opening in 3 seconds...');
  await sleep(3000);

  const browser = await puppeteer.launch({
    headless: false,          // VISIBLE browser
    defaultViewport: null,    // Use system resolution
    args: ['--no-sandbox', '--ignore-certificate-errors', '--start-maximized']
  });
  const page = (await browser.pages())[0];

  // === SCENES GO HERE ===

  await browser.close();
  console.log('RECORDING COMPLETE');
})();
```

**Key rules:**
- `headless: false` -- browser must be visible for OBS
- `--start-maximized` -- full screen, no wasted space
- Use `page.goto()` for navigation, NOT dropdown clicks (unreliable)
- Use `humanType()` for credential entry (looks natural on camera)
- PAUSE.XLONG for money shots (8 seconds to let viewer absorb)

### 1.3 Dry Run (Headless)

Write a test version that runs headless with screenshots:

```bash
node scripts/kc-record-epN-test.js
```

Check screenshots in `/tmp/`. Verify all selectors work before real recording.

---

## Phase 2: Recording

### 2.1 Setup (30 seconds)

1. **Close ALL browser windows** (Firefox, Chrome, everything)
2. **Minimize terminal/VS Code** (clean desktop)
3. **Open OBS** -- set source to **Screen Capture (PipeWire)**
4. **Verify** OBS preview shows your desktop

### 2.2 Record (2-5 minutes)

5. **Hit Record** in OBS
6. **Tell Tigs "GO"** -- he runs the script
7. **Don't touch ANYTHING** -- Chrome opens, script drives all clicks
8. **Wait for** "RECORDING COMPLETE" in terminal
9. **Stop OBS recording**

### 2.3 Verify

10. Check OBS output folder: `/home/angel/Videos/OBS/`
11. Play the MP4 -- confirm Chrome was captured (not wrong window)

---

## Phase 3: Post-Production

### 3.1 Strip Audio

Always strip audio from raw recording (ambient noise from location):

```bash
ffmpeg -y -i raw-recording.mp4 -an -c:v libx264 -crf 18 -preset slow \
  -pix_fmt yuv420p -r 30 silent-video.mp4
```

### 3.2 Trim

Cut pre-roll (before Chrome) and post-roll (after Chrome closes):

```bash
ffmpeg -y -i raw-recording.mp4 -ss START_SEC -to END_SEC \
  -c:v libx264 -crf 18 -preset slow -c:a copy trimmed.mp4
```

**How to find trim points:**
- Extract frames: `ffmpeg -ss N -i video.mp4 -vframes 1 frame.jpg`
- First frame should be Chrome loading or login page
- Last frame should be the final dashboard view

### 3.3 Create Intro/Outro

1. Edit `EP{N}-folder/intro.html` and `outro.html`
2. Screenshot with Puppeteer: `node scripts/video-stitch.js`
3. Create video clips from stills:

```bash
ffmpeg -y -loop 1 -i intro.png -c:v libx264 -t 4 -pix_fmt yuv420p -r 30 intro-clip.mp4
ffmpeg -y -loop 1 -i outro.png -c:v libx264 -t 6 -pix_fmt yuv420p -r 30 outro-clip.mp4
```

### 3.4 Stitch Final Video

```bash
# Create concat list
printf "file 'intro-clip.mp4'\nfile 'silent-trimmed.mp4'\nfile 'outro-clip.mp4'\n" > concat.txt

# Concatenate
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy FINAL.mp4
```

### 3.5 Verify Final

- Play the full video start to finish
- Check: intro appears, content plays, outro appears
- Check: NO audio (silent until voiceover is added)
- Check: no black frames at transitions

---

## Phase 4: Distribution

### 4.1 File Organization

```
videos/keycloak/EP{N}-title/
├── KC-EP{N}-Title-FINAL.mp4    <- The one you share
├── voiceover-script.md          <- Talking points
├── intro.html                   <- Source (editable)
├── outro.html                   <- Source (editable)
├── intro.png                    <- Screenshot
├── outro.png                    <- Screenshot
└── raw/
    └── take{N}-description.mp4  <- OBS raw recordings
```

### 4.2 Git vs GDrive

| What | Where | Why |
|------|-------|-----|
| HTML, MD, JS files | GitHub | Small, editable, versioned |
| MP4 video files | Google Drive | Large binary, not for git |
| PNG screenshots | Local only | Regenerable from HTML |

### 4.3 Voiceover (Later)

Record audio narration separately using the `voiceover-script.md` as a guide. Mix audio onto the silent video:

```bash
ffmpeg -y -i FINAL-silent.mp4 -i voiceover.m4a \
  -c:v copy -c:a aac -shortest FINAL-with-audio.mp4
```

---

## Quick Reference Card

```
RECORD:  Close browsers → OBS Record → "GO" → Wait → Stop OBS
TRIM:    ffmpeg -ss START -to END -i raw.mp4 ... trimmed.mp4
STRIP:   ffmpeg -i video.mp4 -an ... silent.mp4
INTRO:   ffmpeg -loop 1 -i intro.png -t 4 ... intro-clip.mp4
STITCH:  ffmpeg -f concat -i list.txt -c copy FINAL.mp4
AUDIO:   ffmpeg -i silent.mp4 -i voice.m4a ... final.mp4
```

---

*"You write a script, I press the clicker, OBS does the rest."*
*Invented Feb 10, 2026 -- McDonald's Trapani, 9:20 PM*
