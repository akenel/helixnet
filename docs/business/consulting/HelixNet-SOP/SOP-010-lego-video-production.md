# SOP-010: Lego-Style AI Video Production
## Standard Operating Procedure

**Document ID:** SOP-010
**Revision:** 1.0
**Date:** March 31, 2026
**Author:** Angel Kenel & Tigs
**Status:** Initial -- improve after next production

---

## 1. Purpose

Step-by-step procedure for producing short-form Lego-style animated videos using AI video generators, ffmpeg post-production, and the Syd Field three-act structure. Zero budget. One session. Telegram-ready output.

---

## 2. Scope

Applies to all HELIX COMICS Lego-style video productions. Covers: scripting, AI generation, file management, post-production, and distribution.

---

## 3. Prerequisites

| Item | Details |
|------|---------|
| AI Video Tool | Hailuo AI (hailuoai.video) -- free tier, 25 credits/day |
| Backup Tools | Kling AI ($9.80 trial), Pika (free tier), PixVerse (free tier) |
| Static Image Backup | Leonardo AI (free), DALL-E via ChatGPT (free), Playground AI (free) |
| ffmpeg | Installed locally, for stitching + captions + music |
| Font | DejaVu Sans Bold (`/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`) |
| Music Library | `/home/angel/repos/helixnet/assets/comics/video/music-clips/` |
| Output Folder | `/home/angel/Videos/Legos Season 1/` (or Season N) |

---

## 4. Procedure

### Phase 1: Script (30 min)

1. **Pick the theme.** What's the mirror? Not propaganda -- a mirror.
2. **Write three-act structure** in Syd Field format:
   - ACT 1: Setup (15 sec) -- establish the absurdity
   - ACT 2: Confrontation (25 sec) -- escalate the comedy
   - ACT 3: Resolution (20 sec) -- the punchline that hits
3. **Write captions** for each scene. One-liners. Punchy. Two lines max per scene.
4. **Save script** to: `assets/comics/[project-name]/scripts/[project-name].md`

**Deliverables:**
- Full script with ASCII panel layouts
- Caption text per scene
- Music notes (mood per act)

### Phase 2: AI Prompts (15 min)

1. **Write one prompt per scene.** Include:
   - Camera angle (wide shot, close-up, etc.)
   - LEGO minifigure style (always include this)
   - Specific action happening
   - Lighting mood
   - End with: "LEGO brick stop-motion animation style. 4K cinematic."
2. **Write negative prompts** (if tool supports): `realistic humans, photorealistic, gore, blood, real weapons, flags of real countries`
3. **Save prompts** to: `assets/comics/[project-name]/scripts/video-prompts.md`
4. **Save static image prompts** as backup: `assets/comics/[project-name]/scripts/static-prompts.md`

**Prompt template:**
```
[Camera angle]. [Subject description]. [Action]. [Setting details].
[Lighting/mood]. LEGO brick stop-motion animation style. [Comedy tone]. 4K cinematic.
```

### Phase 3: AI Generation (30-60 min)

1. **Open Hailuo AI** (hailuoai.video)
2. **Settings:** Hailuo 2.3, 768p, 6s duration
3. **For each scene:**
   a. Paste prompt into text box
   b. Click "+ Create"
   c. Wait 1-3 minutes for generation
   d. Download the clip
   e. Drop file path to Tigs for rename
4. **Tigs renames** with convention: `NN-scene-name.mp4`
   ```
   01-act1-the-table.mp4
   02-act2a-accusation.mp4
   03-act2b-dead-battery.mp4
   ...
   07-title-card.mp4
   08-end-card.mp4
   ```

**Naming convention:** `NN-` prefix = stitch order. Title card and end card get numbered for their position in the final edit, NOT their generation order.

**Credit budget:** ~1 credit per clip. 25 free credits/day = 25 clips = 3 full videos per day.

**Quality check per clip:**
- [ ] Lego/blockhead style (no realistic humans)
- [ ] Action matches the script intent
- [ ] No watermarks obscuring key areas
- [ ] Consistent with other clips (lighting, style)

**If a clip is bad:** Regenerate. Don't settle. Foo Fighters don't settle.

### Phase 4: Post-Production (15 min)

**Tigs handles this. One build script does everything.**

#### 4a. Captions

Each scene gets burned-in captions via ffmpeg `drawtext`:
- Font: DejaVu Sans Bold, 22-28pt
- Color: White with black border (2px)
- Position: Bottom center, 48-80px from bottom
- Timing: Appear at 1-1.5s, hold to 5.5s
- Special: Key words in gold (#FFD700) or red (#FF4444) for emphasis

#### 4b. Transitions

Crossfade between every scene:
- Duration: 0.5 seconds
- Type: `xfade=transition=fade`
- ffmpeg xfade offset formula: `offset_n = (n * clip_duration) - (n * crossfade_duration)`

#### 4c. Music Bed

- Source: `/home/angel/repos/helixnet/assets/comics/video/music-clips/`
- Volume: **0.25** (background, not competing with visuals)
- Fade in: 2 seconds at start
- Fade out: 3 seconds before end
- Sample rate: Force 48000Hz (loudnorm upsamples silently!)
- Trim to video duration

#### 4d. Build Command

```bash
bash build-final.sh
```

**Output:** `WORLD-WAR-LEGO-POLISHED.mp4` (or `[PROJECT]-POLISHED.mp4`)

**Post-production checklist:**
- [ ] All captions readable (not cut off, not overlapping scene content)
- [ ] Crossfades smooth (no jump cuts, no black frames)
- [ ] Music audible but not overpowering
- [ ] Title card fades in
- [ ] End card fades out
- [ ] Total duration feels right (40-90 seconds for short-form)
- [ ] Watch the ENTIRE video start to finish before declaring done

### Phase 5: Distribution (5 min)

#### Telegram Post

1. Write post copy: tagline, story summary, hashtags
2. Save to `TELEGRAM-POST.txt` in project folder
3. Open Telegram Desktop
4. Drag video into target chat
5. Paste caption from TELEGRAM-POST.txt
6. **Right-click Send button** → "Schedule Message"
7. Set date/time (pick golden hour: 6-7am or 7-9pm local)
8. Click "Schedule"

#### Post Copy Template
```
[TITLE IN CAPS]

[One-line hook]

[3-4 line story summary]

--

"[Closing quote]"

HELIX COMICS | [Year]
Made with [tools used]
[Production flex: budget, time, truth]

#[Hashtags]
```

---

## 5. File Structure

```
/home/angel/Videos/Legos Season N/
├── 01-scene-name.mp4          # Raw renamed clips
├── 02-scene-name.mp4
├── ...
├── NN-scene-name.mp4
├── work/                      # Intermediate files (captioned clips, crossfaded)
├── concat.txt                 # ffmpeg concat list
├── build-final.sh             # Production build script
├── [PROJECT]-POLISHED.mp4     # FINAL OUTPUT
├── [PROJECT]-FINAL.mp4        # Raw stitch (no captions/music)
└── TELEGRAM-POST.txt          # Distribution copy

assets/comics/[project-name]/
├── scripts/
│   ├── [project-name].md      # Full SF script
│   ├── video-prompts.md       # AI video prompts
│   └── static-prompts.md      # Static image prompts (backup)
├── strips/                    # Generated static images (if used)
└── video/                     # Alternate video workspace
```

---

## 6. Lessons Learned (World War Lego -- S01E01)

| # | Lesson | Action |
|---|--------|--------|
| 1 | Hailuo free tier works. 25 credits = 1 full video with retake room | Start with Hailuo, don't pay until you have to |
| 2 | 768p / 6s / Hailuo 2.3 is the sweet spot for free tier | Don't change settings unless quality demands it |
| 3 | Numbered file convention (01-, 02-) makes stitching brainless | Always rename immediately after download |
| 4 | One build script for entire post-production | Don't do captions/music manually -- script it |
| 5 | Crossfade 0.5s keeps flow without eating clip time | Don't go over 0.75s or scenes feel rushed |
| 6 | Music at 0.25 volume -- any louder and it fights the visuals | Background means BACKGROUND |
| 7 | 43 seconds is tight and punchy for Telegram/social | Don't pad. If it's done, it's done |
| 8 | Entire pipeline: script to scheduled post in ~2 hours | Can improve to 1 hour with practice |
| 9 | "The mirror, not the megaphone" -- no sides, no propaganda | The joke is ALL the leaders, the hero is the kid |

---

## 7. Improvement Queue (Next Session)

- [ ] Voiceover track (narrator or scene dialogue)
- [ ] Try 1080p if Hailuo supports on free tier
- [ ] A/B test different music beds
- [ ] YouTube Shorts version (vertical crop / 9:16)
- [ ] Instagram Reels version
- [ ] Caption font upgrade (find a bolder, more cinematic font)
- [ ] Automate prompt pasting (Puppeteer + Hailuo?)
- [ ] Template the build-final.sh for any project (pass project name as arg)
- [ ] Add "HELIX COMICS" watermark in corner

---

## 8. Production Log

| Date | Project | Scenes | Tool | Time | Cost | Output |
|------|---------|--------|------|------|------|--------|
| 2026-03-31 | World War Lego | 8 clips | Hailuo 2.3 | ~2 hrs | $0 | 43.5s, 6.8MB |

---

*"The kids will teach the generals."*
*"Execute, don't note."*
*"Foo Fighters don't settle."*
