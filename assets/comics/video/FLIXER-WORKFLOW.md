# FLIXER WORKFLOW
> Comic Strip Animation Pipeline | Helix Comics

---

## WHAT IS FLIXER?

Flixer = Comic strips that MOVE. Simple animations from static panels.
Think: motion comics, animatics, Ken Burns on blockheads.

**The Goal:** Turn 25 comic pieces into an 8-12 minute animated short.

---

## PRODUCTION PIPELINE

```
STAGE 1: GENERATE          STAGE 2: PREP           STAGE 3: ANIMATE
─────────────────          ──────────────          ────────────────
AI-PROMPTS.md         →    /strips/ PNGs     →    Flixer Assembly
Copy prompt           →    Save renders      →    Add motion + audio
Generate in AI tool   →    Name correctly    →    Export video
```

---

## STAGE 1: IMAGE GENERATION

### Tools (Pick One)
- Midjourney (best for style consistency)
- DALL-E 3 (fastest iteration)
- Leonardo AI (good free tier)
- Stable Diffusion (local control)

### Process
1. Open `AI-PROMPTS.md`
2. Copy the prompt for your scene
3. Paste into AI generator
4. Generate 2-4 variations
5. Pick the blockhead-iest one
6. Download at highest resolution

### Naming Convention
```
/strips/scene-001-toast-button.png
/strips/scene-008-deployment.png
/one-shots/farside-006-estimate.png
```

---

## STAGE 2: ASSET PREP

### Folder Structure
```
assets/comics/
├── strips/              # Final rendered strips
├── one-shots/           # Single panel farside comics
├── video/
│   ├── titles/          # Episode title cards
│   ├── transitions/     # Scene transitions
│   └── exports/         # Final video renders
└── templates/
    └── heads/           # Character head shots for cutaways
```

### Title Cards Needed
Create simple title cards for each scene:

| File | Text |
|------|------|
| title-001.png | "THE TOAST BUTTON" |
| title-002.png | "THE CERTIFICATE" |
| title-003.png | "FLOOR SCRUBBING SEPTEMBER" |
| title-004.png | "THE BABBLING BROOK" |
| title-008.png | "THE DEPLOYMENT" |
| title-009.png | "THE RETRO" |
| title-010.png | "DEMO DAY" |
| title-011.png | "THE DOCUMENTATION" |
| title-012.png | "THE GRADUATION" |

**Style:** EDO SZ font, white text, dark background, simple.

### Character Heads (Optional)
For reaction shots and interstitials:
- CTO (toast-head blockhead)
- Kid (simple round head)
- Leo (tiger face, zen)
- Charlie (three-eyed)
- Pam (music note hair)
- Sal (tired but wise)

---

## STAGE 3: FLIXER ANIMATION

### Software Options
- **DaVinci Resolve** (free, powerful)
- **CapCut** (free, fast, mobile)
- **Premiere Pro** (if you have it)
- **Final Cut Pro** (Mac)
- **Kdenlive** (free, Linux)

### Animation Techniques

#### Ken Burns Effect
Slow pan/zoom across panel. Creates movement from static image.
```
Start: Full panel
End: Zoom 120% to focal point (character face, punchline)
Duration: 4-8 seconds
```

#### Panel Reveal
Show panels one at a time, left to right.
```
Panel 1: Fade in, hold 3-4 sec
Panel 2: Slide in from right, hold 3-4 sec
Panel 3: Slide in, hold 3-4 sec
Panel 4: Zoom in on punchline, hold 5 sec
```

#### Shake/Pop
For emphasis. Quick scale up + shake on key moment.
```
Scale: 100% → 105% → 100%
Duration: 0.3 seconds
Use on: Punchlines, reactions, "NOOOO!" moments
```

#### Caption Timing
```
[Panel animation plays]
[Brief pause - 0.5 sec]
[Caption fades in at bottom]
[Hold for read time - 3-5 sec based on length]
```

---

## AUDIO LAYERS

### Layer 1: Music Bed
Lofi beats, subtle, doesn't compete with dialogue.
- Earth Wind & Fire for Scene 003 (Floor Scrubbing)
- Dylan for Scene 012 (Graduation)
- Zen ambience for Scene 004 (Babbling Brook)

### Layer 2: Sound Effects (Optional)
- Toaster pop
- Coffee slurp
- Keyboard clacking
- Meeting room ambience
- Water babbling (Leo's brook)

### Layer 3: Voice (Future Enhancement)
If doing voiceover later:
- Kid: Innocent, matter-of-fact
- CTO: Corporate buzzword energy
- Leo: Zen, calm, slightly amused

---

## EPISODE STRUCTURE

### Cold Open (30 sec)
Quick farside gag. Sets the tone.

### Main Strip (2-3 min)
Full 4-panel strip with animations.

### Interstitial (30 sec)
Another farside gag or transition card.

### Next Strip...

### Finale (3-4 min)
Scene 012: The Graduation
Dylan plays. Golden toast. Everyone floats.

---

## EXPORT SETTINGS

### For YouTube/General
- Resolution: 1920x1080 (16:9)
- Frame Rate: 30fps
- Codec: H.264
- Bitrate: 15-20 Mbps

### For Instagram/TikTok
- Resolution: 1080x1920 (9:16)
- Or 1080x1080 (square)
- Keep under 60 seconds per clip

### For Archive
- Resolution: 4K if source allows
- ProRes or DNxHD
- Save project files

---

## BATCH PRODUCTION ORDER

Generate images in this sequence for narrative flow:

```
BATCH 1 - FOUNDATION (8 pieces)
├── strip-001  Toast Button
├── strip-002  Certificate Coffee
├── strip-003  Floor Scrubbing
├── strip-004  Babbling Brook
├── farside-001  Microservices
├── farside-002  Standup
├── farside-003  Pivot
└── farside-004  Sync

BATCH 2 - EXPANSION (9 pieces)
├── strip-008  Deployment
├── strip-009  Retro
├── strip-010  Demo Day
├── strip-011  Documentation
├── farside-005  Dylan
├── farside-006  Estimate
├── farside-007  Meeting
├── farside-008  Blockchain
└── farside-009  Password

BATCH 3 - FINALE (8 pieces)
├── strip-012  Graduation (THE FINALE)
├── farside-010  Legacy Code
├── farside-011  Consultant
├── farside-012  Agile
├── farside-013  AI Fix It
├── title cards (batch)
└── transition cards (batch)
```

---

## QUALITY CHECKLIST

Before export, verify:

- [ ] All panels readable at 1080p
- [ ] Captions have enough hold time
- [ ] Audio levels consistent (-14 to -10 LUFS)
- [ ] No jarring cuts between scenes
- [ ] Blockhead style consistent throughout
- [ ] Dylan plays during graduation (THIS IS MANDATORY)
- [ ] Golden toast GLOWS in finale

---

## QUICK START

**Minimum Viable Flixer:**

1. Generate ONE strip (start with strip-001)
2. Import into video editor
3. Apply Ken Burns zoom (full → punchline)
4. Add caption at end
5. Export
6. You made a flixer

**Then iterate.**

---

## THE PHILOSOPHY

```
The animation should be SIMPLE.
Like the comics.
Like the kid's wisdom.

Don't over-engineer the flixer.
The toaster has a button.
Push it.
```

---

*Float. Listen. Render.*
