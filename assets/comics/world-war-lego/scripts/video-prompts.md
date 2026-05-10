# WORLD WAR LEGO -- AI Video Prompts
## Copy-Paste Ready for Kling AI / Runway / Minimax
> HELIX COMICS | March 2026

---

## HOW TO USE

1. Pick your AI video tool (Kling AI recommended -- free tier, best for Lego style)
2. Copy the prompt for the scene
3. Paste into the text-to-video generator
4. Generate 5-10 second clip
5. Download highest quality
6. Save to `/assets/comics/world-war-lego/video/`
7. Stitch in order with ffmpeg

**Naming:**
```
act1-the-table.mp4
act2a-accusation.mp4
act2b-dead-battery.mp4
act2c-kid-corner.mp4
act3a-the-reveal.mp4
act3b-the-freeze.mp4
```

---

## SCENE 1A: THE TABLE (Wide Shot)

### Kling / Runway Prompt:
```
Cinematic wide shot of a kindergarten classroom. Three LEGO minifigure military generals in oversized uniforms with medals sit at a tiny children's table. Each has a large red button, a juice box with straw, and a child's crayon drawing labeled "MY COUNTRY" taped on the wall behind them. The table is comically small for them. Colorful finger paintings on walls. Warm classroom lighting contrasts with stern military faces. LEGO brick stop-motion animation style. Dark comedy tone. Camera slowly zooms in. 4K cinematic.
```

### Negative prompt (if tool supports it):
```
realistic humans, photorealistic, dark lighting, gore, blood, real weapons, flags of real countries
```

---

## SCENE 2A: THE ACCUSATION

### Prompt:
```
LEGO minifigure military general stands up angrily from tiny kindergarten chair, chair falls over. He points furiously at another general's crayon drawing on the wall. Second general slams juice box on table, juice splashes everywhere on his medals. Third general watches nervously. Kindergarten table with red buttons and spilled juice. Dramatic lighting. LEGO brick stop-motion animation style. Quick camera movement. Dark comedy. Playground argument energy. 4K cinematic.
```

---

## SCENE 2B: THE DEAD BATTERY

### Prompt:
```
Close-up of LEGO minifigure military general frantically pressing a large red button that does nothing. He flips it over to reveal empty battery compartment. He shakes it, confused and embarrassed. Blows into it. Two other LEGO generals at kindergarten table stop arguing to stare at him in disbelief. Juice boxes on table. LEGO brick stop-motion animation style. Comedy timing. Absurdist dark humor. Warm kindergarten lighting. 4K cinematic.
```

---

## SCENE 2C: THE KID IN THE CORNER

### Prompt:
```
Small LEGO minifigure child sitting cross-legged on kindergarten floor in corner of room. Quietly and carefully stacking three colored blocks -- red, blue, yellow -- building a small bridge. Background shows blurred chaos of three arguing military generals at a tiny table. A juice box rolls toward the child, child catches it calmly and takes a sip. Peaceful focus amid chaos. LEGO brick stop-motion style. Soft warm lighting on child, harsh lighting on background chaos. Cinematic depth of field. 4K.
```

---

## SCENE 3A: THE REVEAL

### Prompt:
```
Dramatic slow-motion. Small LEGO minifigure child walks to kindergarten table where three exhausted military generals sit -- one with crayon on his face, one holding broken red button, one with juice stain on uniform. Child places three colored LEGO blocks (red, blue, yellow) between three crayon drawings on the wall, forming a small bridge connecting all three "countries." Generals stare in stunned silence. Camera slowly pushes in on the three-block bridge. Golden warm light blooms. LEGO brick stop-motion style. Emotional. Powerful. Simple. 4K cinematic.
```

---

## SCENE 3B: THE FREEZE

### Prompt:
```
Wide shot. LEGO minifigure child walks away from table, picks up juice box, sits back in corner. Three LEGO military generals frozen in place staring at three small colored blocks forming a bridge between their crayon drawings. One general slowly puts his broken red button in his pocket. Another wipes crayon off his face. Silence. Still. Kindergarten classroom. Late afternoon golden light through windows. LEGO brick stop-motion style. Bittersweet. Contemplative. Camera holds steady. 4K cinematic.
```

---

## END CARD

### Option A: Generate with AI
```
Black background. White text in angular bold font. Text reads: "The kids will teach the generals." Below in smaller text: "WORLD WAR LEGO" and "HELIX COMICS 2026". Minimalist. Clean. Banksy street art subtle texture in background. Single small LEGO brick in bottom corner glowing softly. 4K.
```

### Option B: Create in HTML (our way)
Use Puppeteer to screenshot an HTML end card -- same as our Keycloak video pipeline. Faster, exact control.

---

## TITLE CARD (Opening)

### Prompt:
```
Dramatic title card. Large bold angular text "WORLD WAR LEGO" made of actual LEGO bricks on a dark background. Subtitle below: "The Adults Broke The World." Military toy soldiers and alphabet blocks scattered around the text. Dramatic spotlight lighting from above. Smoke/dust in air. LEGO brick stop-motion style. Cinematic. Dark comedy tone. 4K.
```

---

## STYLE MODIFIERS

Add any of these to the end of prompts to adjust:

### More stop-motion feel:
```
, authentic stop-motion animation, visible fingerprints on bricks, slightly jerky movement, practical lighting, miniature set design
```

### More cinematic:
```
, Christopher Nolan cinematography, shallow depth of field, anamorphic lens flare, dramatic score feeling, epic scale in miniature
```

### More Banksy/street art:
```
, Banksy street art aesthetic, stencil art overlay, subversive political commentary, urban wall texture, spray paint drips
```

### More Peanuts/gentle:
```
, Charles Schulz warmth, gentle humor, nostalgic, soft colors, childhood innocence, simple emotional truth
```

---

## STITCHING ORDER (ffmpeg)

```bash
# After all clips are generated and saved:

cat > /home/angel/repos/helixnet/assets/comics/world-war-lego/video/concat.txt << 'EOF'
file 'title-card.mp4'
file 'act1-the-table.mp4'
file 'act2a-accusation.mp4'
file 'act2b-dead-battery.mp4'
file 'act2c-kid-corner.mp4'
file 'act3a-the-reveal.mp4'
file 'act3b-the-freeze.mp4'
file 'end-card.mp4'
EOF

ffmpeg -f concat -safe 0 -i concat.txt \
  -c:v libx264 -pix_fmt yuv420p \
  -c:a aac -b:a 128k \
  world-war-lego-final.mp4
```

---

## RECOMMENDED TOOLS (Free Tier)

| Tool | URL | Free Tier | Best For |
|------|-----|-----------|----------|
| **Kling AI** | klingai.com | 66 credits/day | Best Lego style, longest clips |
| **Minimax / Hailuo** | hailuoai.video | Limited daily | Good motion, fast |
| **Pika** | pika.art | 150 credits/month | Quick iterations |
| **Runway Gen-3** | runwayml.com | Trial credits | Highest quality |

**Recommendation:** Start with Kling AI. Free, handles the blockhead/Lego aesthetic best, generates up to 10-second clips.

---

## QUALITY CHECKLIST

Before stitching:

- [ ] All clips are LEGO style (no realistic humans leaked in)
- [ ] No real country flags visible (generic crayon drawings only)
- [ ] Kid is clearly the hero, not a side character
- [ ] The three-block bridge is visible and clear in Act 3
- [ ] Consistent lighting across all clips
- [ ] No text/watermarks obscuring the scene
- [ ] Resolution matches across clips (all 1080p or all 4K)

---

*Copy. Paste. Generate. Stitch. Upload.*
*"The kids will teach the generals."*
