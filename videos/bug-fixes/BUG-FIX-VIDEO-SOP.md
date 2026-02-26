# Bug Fix Video Recording SOP

**SOP-VID-002** | Created: Feb 25, 2026 | Updated: Feb 26, 2026
BUG-020 was the first GOLD bug fix video. Everything here comes from that session.

---

## Overview

Each bug fix video shows: the bug, the fix, the result. Under 8 minutes. Simple, clear, professional.

Two production methods:

| Method | When to Use | Example |
|--------|-------------|---------|
| **Scripted** (Puppeteer + OBS) | Repeatable demos, RBAC walkthroughs | KC episodes, ISOTTO demo |
| **Organic** (OBS only) | Real bug fixes captured live | BUG-020 (GOLD) |

---

## Folder Structure

```
videos/bug-fixes/
├── BUG-FIX-VIDEO-SOP.md              <- This file
├── BUG-020/
│   ├── BUG-020-FINAL.mp4             <- FINAL (upload this)
│   ├── BUG-020-SILENT.mp4            <- Silent version (for re-narration)
│   ├── NARRATOR-CUE-SHEET.html       <- Mobile-friendly voiceover guide
│   ├── record-bug-020.js             <- Puppeteer script (optional)
│   ├── post-production/              <- ALL intermediate files
│   │   ├── cards/                    <- Title card HTML + PNG + screenshot scripts
│   │   ├── seg-*.mp4                 <- Extracted video segments
│   │   ├── clip-*.mp4                <- Title card video clips
│   │   ├── voice-*.wav               <- Audio processing chain
│   │   ├── audio_*.ogg               <- Raw Telegram voiceover
│   │   ├── concat.txt                <- ffmpeg stitch order
│   │   └── video-no-audio.mp4        <- Stitched silent video
│   └── youtube-kit/                  <- YouTube upload assets
│       ├── YOUTUBE-METADATA.md        <- Master reference (title, desc, tags, chapters)
│       ├── description.txt            <- Ready-to-paste YouTube description
│       ├── tags.txt                   <- Comma-separated tags
│       ├── thumbnail.html / .png / .jpg <- 1280x720 custom thumbnail
│       ├── voice-final-limited.srt    <- English subtitles (Whisper)
│       └── linkedin-post.txt          <- Social media announcement
├── BUG-021/
│   └── ...
```

**Rule:** Main folder = final MP4 + cue sheet. Everything intermediate goes in `post-production/`. Everything for YouTube goes in `youtube-kit/`.

---

## Method A: Scripted Recording (Puppeteer + OBS)

See `videos/keycloak/VIDEO-PRODUCTION-SOP.md` for the full Puppeteer pipeline.

### Recording Flow

```
Scene 1: RED "OBS CHECK" card       -> Verify OBS, press ENTER
Scene 2: Bug info card (dark)       -> Auto 5 seconds (bug number, title, severity)
Scene 3: BEFORE                     -> Puppeteer navigates to the bug, shows it
         (press ENTER when ready)
Scene 4: ORANGE "FIXING" card       -> Shows what the fix is
         (apply fix + deploy, press ENTER when done)
Scene 5: AFTER                      -> Puppeteer navigates back, shows it fixed
         (press ENTER when ready)
Scene 6: GREEN "BUG FIXED" card     -> Victory screen
         (press ENTER to close)
```

### Pre-Flight (MANDATORY)
1. Open terminal, cd to bug folder
2. Start OBS -- set to **Screen Capture** (NOT Window Capture)
3. Run: `node record-bug-XXX.js`
4. First screen = **RED "OBS CHECK"** card
5. Verify in OBS preview that you see the red card
6. Press ENTER to begin

### Post-Flight (MANDATORY)
1. STOP OBS recording immediately
2. Play first 10 seconds of raw file -- verify it shows browser, not desktop
3. Note timestamps for trim points

---

## Method B: Organic Recording (The BUG-020 Method)

*Invented Feb 26, 2026 -- PuntaTipa Room 101*

**No script. Just work.** Record yourself fixing a real bug with OBS screen capture. The raw footage is authentic -- you working with the AI, browsing, deploying, verifying. Post-production turns the raw material into a tight, watchable video.

### Why This Works

- Authentic -- no rehearsal, no fake scenarios
- Faster to record -- just press record and work
- More relatable -- developers see a real workflow, not a demo
- The messy parts get cut in post -- you don't need a perfect take

### Recording

1. Start OBS -- **Screen Capture**, 1920x1080, 30fps
2. Work normally -- fix the bug, deploy, verify
3. Don't worry about mistakes, extra browsing, or dead time
4. Stop OBS when done
5. Raw file goes to `/home/angel/Videos/OBS/`

### Post-Production Pipeline (Heavy Lifting)

This is where the magic happens. The organic method front-loads editing work.

#### Step 1: Map the Raw Video

Extract frames every 10 seconds to understand what you captured:

```bash
mkdir -p /tmp/bug-frames
ffmpeg -i raw-recording.mp4 -vf fps=1/10 /tmp/bug-frames/frame-%04d.jpg
```

Review ALL frames. Build a content map:

| Time | Content | Keep? |
|------|---------|-------|
| 0:00-2:00 | Login + QA dashboard | YES |
| 2:00-3:20 | VS Code fix | YES |
| 3:20-4:10 | Deploy + smoke test | YES |
| 4:10-4:48 | Browser mess, file:/// | NO |
| 4:48-7:30 | AFTER -- buttons fixed | YES |
| 7:30-13:00 | Extra browsing | NO |
| 13:00-13:20 | BUG COMPLETE summary | YES |
| 15:40-16:00 | QA verification | YES |
| 16:00-19:24 | API errors, session expired | NO |

**Key insight:** You'll keep maybe 40-50% of the raw footage. The rest is noise.

#### Step 2: Extract Segments

Cut each "keep" section as a separate segment. ALWAYS re-encode:

```bash
# Segment A: Bug discovery + fix (0:00 to 4:10)
ffmpeg -y -ss 0 -to 250 -i raw.mp4 -c:v libx264 -crf 20 -an seg-A.mp4

# Segment B: AFTER state (4:48 to 7:30)
ffmpeg -y -ss 288 -to 450 -i raw.mp4 -c:v libx264 -crf 20 -an seg-B.mp4

# Segment C: Summary (13:00 to 13:20)
ffmpeg -y -ss 780 -to 800 -i raw.mp4 -c:v libx264 -crf 20 -an seg-C.mp4
```

**Split segments further** if a title card needs to go in the middle:

```bash
# A1: Before the fix (0:00 to 2:20)
ffmpeg -y -ss 0 -to 140 -i raw.mp4 -c:v libx264 -crf 20 -an seg-A1.mp4

# A2: After the fix card (2:20 to 4:10)
ffmpeg -y -ss 140 -to 250 -i raw.mp4 -c:v libx264 -crf 20 -an seg-A2.mp4
```

#### Step 3: Create Section Title Cards

Simple, bold, mobile-friendly. Not detailed scene descriptions -- just section headers.

**BUG-020 used 6 cards:**

| Card | Duration | Purpose |
|------|----------|---------|
| INTRO | 5s | Bug number, title, one-liner |
| THE BUG | 3s | "What's broken" |
| THE FIX | 3s | "One line change" |
| DEPLOYED | 3s | "Git push, smoke test" |
| VERIFIED | 3s | "Buttons working" |
| OUTRO | 6s | Sign-off, links |

**Design rules for title cards:**
- Dark background (#0f172a to #1e293b gradient)
- Large fonts (60-90px headings, 24-36px body)
- Must be readable on MOBILE PHONE screens
- 1920x1080 PNG via Puppeteer screenshot
- Simple -- 3-5 lines max per card

**Create card HTML -> screenshot -> convert to video clip:**

```bash
# Screenshot all cards with Puppeteer
node post-production/cards/screenshot-cards.js

# Convert each PNG to a video clip
ffmpeg -y -loop 1 -i card-intro.png -c:v libx264 -t 5 -pix_fmt yuv420p -r 30 -an clip-intro.mp4
ffmpeg -y -loop 1 -i card-the-bug.png -c:v libx264 -t 3 -pix_fmt yuv420p -r 30 -an clip-the-bug.mp4
# ... repeat for each card
```

#### Step 4: Stitch Everything Together

Create concat list in story order (cards interleaved with segments):

```
file 'clip-intro.mp4'
file 'clip-the-bug.mp4'
file 'seg-A1.mp4'
file 'clip-the-fix.mp4'
file 'seg-A2.mp4'
file 'clip-deployed.mp4'
file 'seg-B.mp4'
file 'clip-verified.mp4'
file 'seg-C.mp4'
file 'seg-D.mp4'
file 'clip-outro.mp4'
```

```bash
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy video-no-audio.mp4
```

This produces the **silent version** (BUG-020-SILENT.mp4). Good checkpoint -- watch it all the way through.

#### Step 5: Create Narrator Cue Sheet

Write a mobile-friendly HTML cue sheet with timestamps and suggested narration:

```
| Time     | On Screen              | Say This                                    |
|----------|------------------------|---------------------------------------------|
| 0:00     | INTRO card             | "This is Bug 20. A real bug fix..."         |
| 0:08     | ISOTTO login           | "I'm logging into the live server..."       |
| 2:28     | THE FIX card           | "There it is. One line..."                  |
| 4:21     | DEPLOYED card          | "52 passed, zero failed..."                 |
```

**Design:** Large fonts, high contrast, scrollable on phone. Angel reads this on his Fairphone while narrating.

#### Step 6: Record Voiceover

Angel records a single Telegram voice message (.ogg) while watching the silent video and reading the cue sheet.

- Watch the video on laptop
- Read the cue sheet on phone
- Record into Telegram on phone
- Send to self, copy .ogg to post-production/

#### Step 7: Process Voiceover Audio

```bash
# 1. Trim dead air at start/end (voice starts at ~29s, ends at ~8:23)
ffmpeg -y -ss 29 -to 503 -i audio_2026-02-26_15-09-49.ogg voice-trimmed.wav

# 2. Normalize loudness (-16 LUFS broadcast standard)
ffmpeg -y -i voice-trimmed.wav \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11" \
  -ar 48000 voice-normalized.wav

# 3. CRITICAL: Add limiter to prevent clipping
# loudnorm alone can push peaks to 0.0dB which causes audible distortion
ffmpeg -y -i voice-normalized.wav \
  -af "alimiter=limit=0.95" \
  -ar 48000 voice-final-limited.wav

# 4. Pad with silence to match video length + add fades
ffmpeg -y -i voice-final-limited.wav \
  -af "apad=whole_dur=VIDEO_DURATION,afade=t=in:st=0:d=0.5,afade=t=out:st=FADE_START:d=3" \
  -ar 48000 -c:a pcm_s16le voice-padded.wav
```

**CRITICAL LESSON:** Always add `alimiter=limit=0.95` AFTER loudnorm. Without it, loudnorm pushes peaks to exactly 0.0dB which clips on playback. BUG-020 had audible clipping on first attempt until we added the limiter.

**CRITICAL:** Force `-ar 48000` on EVERY ffmpeg audio step. loudnorm silently upsamples to 192kHz.

#### Step 8: Merge Voice + Video

```bash
ffmpeg -y -i video-no-audio.mp4 -i voice-padded.wav \
  -c:v copy -c:a aac -b:a 128k -ar 48000 BUG-020-FINAL.mp4
```

#### Step 9: Generate SRT Subtitles

```bash
source .venv/bin/activate
whisper voice-final-limited.wav --model base --language en --output_format srt --output_dir ./
```

Copy the .srt to youtube-kit/. Upload as English captions on YouTube.

---

## YouTube Kit

Every bug fix video gets a complete `youtube-kit/` subfolder. Create BEFORE uploading.

### Required Files

| File | Purpose | Create With |
|------|---------|-------------|
| `YOUTUBE-METADATA.md` | Master reference -- title, description, tags, chapters, all metadata | Write manually |
| `description.txt` | Ready-to-paste YouTube description | Copy from METADATA |
| `tags.txt` | Comma-separated, one line | Copy from METADATA |
| `thumbnail.html` | Source for thumbnail (1280x720) | Write HTML |
| `thumbnail.png` | High quality screenshot | Puppeteer |
| `thumbnail.jpg` | YouTube upload (1280x720) | Convert from PNG |
| `voice-final-limited.srt` | English subtitles | Whisper transcription |
| `linkedin-post.txt` | Social media announcement | Write manually |

### Thumbnail Design Rules

- 1280x720 pixels (YouTube standard)
- **Big fonts** -- must be readable on mobile phone screens
- Bug number: 80-100px, title: 36px, subtitle: 20px
- Dark background with code panel on the right
- Show the actual fix (before/after code diff)
- Result badge ("52 passed, 0 failed")

### Description Rules

- Max 5000 characters
- No `<`, `>`, or `->` (YouTube strips them)
- Chapters must start at `0:00`
- Include: hook, what the bug was, what the fix was, chapters, tech stack, hashtags
- Hashtags at the BOTTOM of description

### LinkedIn Post

Write a developer-friendly post that:
- Opens with a hook (one short line)
- Tells the story: what broke, why, the fix
- Links the YouTube video
- Lists the tech stack for the curious
- Uses relevant hashtags
- Tone: authentic, not corporate

---

## OBS Settings

| Setting | Value |
|---------|-------|
| Capture | Screen Capture (full screen) |
| Resolution | 1920x1080 |
| FPS | 30 |
| Format | mp4 (or mkv, remux after) |
| Audio | Disabled (voiceover added in post) |

---

## Key Rules

1. **Screen Capture, not Window Capture** -- OBS captured the wrong window on KC EP + ISOTTO demos
2. **Always re-encode** when trimming -- `-c:v copy` loses content at keyframe boundaries
3. **Play 10 seconds immediately** after recording -- verify content before moving on
4. **Force `-ar 48000`** on ALL audio processing -- loudnorm upsamples silently to 192kHz
5. **Always add `alimiter=limit=0.95`** after loudnorm -- prevents 0.0dB clipping
6. **MP4s to Google Drive / YouTube** -- not GitHub (*.mp4 in .gitignore)
7. **Map the raw video with frames FIRST** -- don't start cutting blind
8. **Keep both SILENT and FINAL** -- silent version allows re-narration without re-editing
9. **Watch the final video end-to-end** before declaring done

---

## Production Log

| Date | Bug | Method | Raw | Final | Notes |
|------|-----|--------|-----|-------|-------|
| Feb 26 | BUG-020 | Organic | 19:24 | 7:55 | GOLD. Button styling fix. First organic recording. Voiceover via Telegram. YouTube: youtu.be/ROJOV_v-sbA |

---

## Lessons Learned (BUG-020 Session)

### The Organic Method Works (Feb 26, 2026)
- No Puppeteer script needed for bug fixes
- Just record yourself working, cut the good parts
- 19:24 raw -> 7:55 final (41% kept)
- More authentic than scripted demos
- **Rule:** For real bug fixes, use organic recording. Save scripted for repeatable demos.

### Map Before You Cut (Feb 26, 2026)
- Extracted 116 frames (every 10s) to map the entire 19:24 raw video
- Built a content table before touching ffmpeg
- Identified 4 keepable segments and 3 junk sections
- **Rule:** Always extract frames and build a content map first. Don't cut blind.

### Multi-Segment Extraction (Feb 26, 2026)
- Raw footage had good content scattered across 19 minutes
- Cut 4 separate segments from different timestamps (A, B, C, D)
- Split segment A into A1/A2 to insert a title card in the middle
- Stitched with title cards as section dividers
- **Rule:** Don't try to salvage one continuous take. Extract the good parts, stitch with cards.

### Loudnorm Clips at 0.0dB (Feb 26, 2026)
- `loudnorm=I=-16:TP=-1.5` normalized the voiceover but pushed peaks to exactly 0.0dB
- This caused audible clipping/distortion on playback
- **Fix:** Add `alimiter=limit=0.95` as a second filter step after loudnorm
- **Rule:** NEVER use loudnorm without a limiter. Two-step: normalize, then limit.

### Sine Wave Audio Is Not Music (Feb 26, 2026)
- Tried generating ambient pad from sine waves (A minor chord at 220/330/440/554 Hz)
- Result: "just a buzz" -- rejected immediately
- **Fix:** Human narration via Telegram voice message
- **Rule:** Don't generate audio. Either use royalty-free music or record a voiceover. Nothing in between.

### Narrator Cue Sheet as Mobile HTML (Feb 26, 2026)
- Angel narrates while watching the silent video on laptop
- Reads cue sheet on Fairphone (mobile-friendly HTML)
- One take, one Telegram voice message
- Trim start/end dead air, normalize, merge
- **Rule:** Always create a mobile-friendly cue sheet. Narrating without one produces rambling audio.

### Keep the Silent Version (Feb 26, 2026)
- BUG-020-SILENT.mp4 = complete edit without audio
- If voiceover is bad, re-narrate without re-editing video
- If different language needed, just record new voice and merge
- **Rule:** Always save the silent version alongside the final.

---

*"No scripts, no fakes, just a human and an AI fixing bugs in a real system."*
*The Organic Method -- Feb 26, 2026 -- PuntaTipa Room 101*
