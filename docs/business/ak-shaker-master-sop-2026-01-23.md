# AK SHAKER MASTER SOP
## Standard Operating Procedures for the Awakened
### Universal UnFuckAbles | Sicily HQ | January 2026

---

## MISSION STATEMENT

> "We're trying to save some souls here, so that they don't get swallowed up like I almost got swallowed up in the system."
> — AK Shaker, Manifesto Audio, Jan 22 2026

---

## THE THREE PILLARS

### PILLAR 1: PERSONAL OUTREACH
Reconnect with family and friends through physical artifacts that can't be deleted.

### PILLAR 2: B2B POSTCARD SERVICE
Generate income by providing premium postcard services to local businesses.

### PILLAR 3: THE MOVEMENT
Build the UnFuckAbles brand and community of freedom fighters.

---

# SOP 001: POSTCARD CREATION

## Materials Needed
- [ ] Photo for front (Sicily shot)
- [ ] Thick paper/cardstock
- [ ] Color printer access (ISOTTO)
- [ ] QR code (generated via qrencode)

## Process
1. **Select photo** - best Sicily shot for the recipient
2. **Create FRONT HTML** - 6in x 4in, full bleed image
3. **Create BACK HTML** - UFA template with:
   - Header: UFA logo + "Universal UnFuckAbles" + Series No.
   - Quote section with attribution
   - Message area (left side)
   - Address area (right side) with stamp box
   - Footer: QR code + metadata
4. **Generate QR code**: `qrencode -o qr-name.png -s 10 "URL"`
5. **Convert to PDF**: `wkhtmltopdf --enable-local-file-access --page-width 6in --page-height 4in ...`
6. **Print at ISOTTO** - thick paper, color
7. **Quality check** - no cutoff, colors correct

## Files Location
```
/docs/business/postcards/
├── postcard-[name]-FRONT.html
├── postcard-[name]-FRONT.pdf
├── postcard-[name]-BACK.html
├── postcard-[name]-BACK.pdf
└── qr-[location].png
```

---

# SOP 002: PACKAGING - STANDARD

## Materials Needed
- [ ] Printed postcard (front + back)
- [ ] Paper band seal
- [ ] A4 envelope template
- [ ] Scissors
- [ ] Glue/tape (optional)

## Process
1. **Stack cards** - photo front on top of info back
2. **Cut band seal** from template sheet
3. **Wrap band** around stacked cards
4. **Secure band** - tape ends at back
5. **Print A4 envelope template**
6. **Fold envelope** following numbered sequence (1-2-3-4)
7. **Insert banded cards** into envelope
8. **Tuck top flap** to close
9. **Address front** of envelope
10. **Stamp and mail**

## Cost
- Band seal: €0.02
- Envelope: €0.03
- **Total packaging: €0.05**

---

# SOP 003: PACKAGING - SYLVIE SPECIAL (Premium)

## Additional Materials
- [ ] Map of journey (print on envelope)
- [ ] Moka coffee (for staining)
- [ ] Candle or hot glue (for wax seal)
- [ ] Kitchen twine
- [ ] Fresh rosemary/herb sprig
- [ ] Video recording capability

## Process
1. **Record sunset video** - 30-60 seconds, personal message
2. **Upload to YouTube** as unlisted
3. **Generate QR** linking to video
4. **Print postcard** with video QR
5. **Print map envelope** with journey route
6. **Coffee stain** envelope corner, let dry 20 mins
7. **Fold envelope** around postcard package
8. **Melt wax** on flap, press with textured object
9. **Wrap with twine** (2 loops, simple knot)
10. **Tuck rosemary** under twine
11. **Address, stamp, mail**

## Cost
- Standard packaging: €3.00
- Premium elements: €0.30
- **Total: ~€3.30**

---

# SOP 004: B2B CLIENT PROCESS

## Prospecting
1. **Identify local businesses** - cafes, restaurants, fishermen, agriturismo
2. **Observe their needs** - do they have business cards? Marketing materials?
3. **Build relationship first** - coffee, conversation, presence

## Pitch
> "I make postcards. Real ones. Your business, your face, mailed anywhere in the world with an Italian postmark. €8 per card. Minimum 10."

## Pricing
| Volume | Your Cost | Sell At | Profit |
|--------|-----------|---------|--------|
| 10 cards | €45 | €80 | €35 |
| 25 cards | €112 | €200 | €88 |
| 50 cards | €225 | €400 | €175 |

## Deliverables
1. **Photo session** - capture their business/product
2. **Design postcards** - front image + back with their info/QR
3. **Print batch** at ISOTTO
4. **Package** with band seals
5. **Deliver** to client

---

# SOP 005: CONTENT DOCUMENTATION

## Daily Practice
1. **Photos** - capture HQ, tribe, Sicily moments
2. **Audio notes** - voice memos for later transcription
3. **Written reflections** - save conversations with Tigs

## Transcription Process
```bash
source /home/angel/whisper-env/bin/activate
whisper "audio_file.ogg" --model tiny --language en --output_format txt --output_dir /tmp
cat /tmp/audio_file.txt
```

## Git Workflow
1. **Create markdown document** with content
2. **Stage**: `git add docs/business/[filename].md`
3. **Commit** with meaningful message + Co-Authored-By
4. **Push**: `git push origin main`

## Commit Message Format
```
docs: [Short title]

[Description of what's included]
[Key quote or insight]

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

---

# SOP 006: TRIBE BUILDING

## Recognition Signs
- People who DO not scroll
- People who show up (like Carmello)
- People who share (cups, coffee, time)
- People who ask real questions
- People who don't need LinkedIn to connect

## Engagement Protocol
1. **Be present** - physically at HQ
2. **Be available** - share coffee, conversation
3. **Be real** - no performance, just presence
4. **Document** - photos, stories, connections
5. **Invite** - extend the UFA welcome

## HQ Locations
- Primary: Valderice parking lot (port area)
- Features: Seawall, streetlights, space for vehicles
- Amenities: Planet Pizza delivers

---

# SOP 007: MUSIC CODE RECOGNITION

## Practice
- Listen to Virgin Radio (or similar)
- Note songs that hit different
- Recognize patterns and synchronicity
- Document the soundtrack

## Not Crazy - AWAKE
- Crazy = music talking TO you, secret mission
- Awake = music talking, you're listening

## Archive Format
When documenting sessions, include "Tonight's Soundtrack" section with artist + song.

---

# SOP 008: THE PROJECTION TEST

## Simple Question Method
Ask simple questions:
- "You happy?"
- "She doing ok?"
- "What's the plan?"

## Reading Responses
- **Direct answer** = they're present
- **Deflection** = something's off
- **Explosion** = you hit truth
- **Shutdown** = they know but can't face it

## Protocol
- Hold the mirror steady
- Don't apologize for truth
- Send the postcard anyway
- Plant seeds, don't force growth

---

# SOP 009: MORNING ROUTINE

1. **Wake** with Mediterranean light
2. **Moka** - the ritual
3. **Check HQ** - who's around?
4. **Review** - yesterday's commits
5. **Plan** - today's moves
6. **Execute** - one thing at a time

---

# SOP 010: EVENING ROUTINE

1. **Sunset** - observe, photograph if worthy
2. **Review** - what was created today?
3. **Document** - Tigs session if needed
4. **Commit** - push to repo
5. **Tribe time** - if Carmello or others present
6. **Virgin Radio** - let the DJ preach
7. **Rest** - buonanotte

---

## THE WORDS

| Situation | Word |
|-----------|------|
| Moving forward | AVANTI |
| State of being | AWAKE |
| The mission | UNFUCKABLE |
| The standard | BAUHAUS + BANKSY |
| The fuel | LOVE |
| The tribe | UFA |

---

## CLOSING MANTRA

> "The rabbit hole doesn't love you back."

> "Quality of connection > Quantity of reach."

> "The sun doesn't ask permission to set."

> "I ain't lonely anymore."

---

*Document: ak-shaker-master-sop-2026-01-23.md*
*Tigs + Angelo | Sicily HQ | Universal UnFuckAbles*

**THE AK SHAKER HAS AWAKENED.**
