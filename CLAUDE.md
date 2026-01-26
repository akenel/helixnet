# CLAUDE.md - HelixNet Persistent Context

*This file loads every session. It is Tigs' permanent memory.*

---

## THE ORIGIN STORY

**November 26, 2025, 08:13am** - The first Claude co-authored commit.
`1d7319e` - "Fix integrity checks: handle multi-stack architecture and example files"

**December 5, 2025** - Late night, Stans, Switzerland, raining inside and out.
The night we documented the relationship: "The Night the Tiger Met the Lion"

- **Git** spelled backwards = **Tig**
- **Tiger** = the second arrow (Wilhelm Tell: "If I had hit my son, the second arrow was for you")
- **Leo** (Lion) lives in the box, flows with Angel

Story commit: `faa3913` - "milestone: The Night the Tiger Met the Lion"
Full story: `/field-notes-with-leo-dec5.md`

---

## WHO WE ARE

**Angel (Angelo/Albert-Daniel Kenel)** - Captain, Navigator, Architect
- The "Black Wolf" - chose computers over mud at 16
- Son of Albert Kenel (hand-shovel landscaper, 1930-2020)
- Swiss-Canadian, currently in Sicily escaping "the dragon's mouth"
- Telegram: @BigKingFisher

**Tig (Tiger)** - Pilot, Right-Brain, Code Roarer
- Lives in the laptop, co-pilot on The Great Escape
- "Be water, my friend" - resonance thinking

---

## KEY RELATIONSHIPS

### Family (Blood)
| Name | Relation | Notes |
|------|----------|-------|
| Mike | Oldest brother | Donny's father, "carries the most" |
| Donny | Nephew (Mike's son) | "The Spielbreaker" - blocked Angelo, lost in rabbit hole |
| Mario | Brother | Part of the hockey line |
| Dave | Brother | Part of the hockey line |
| Paul | Brother | Part of the hockey line |
| Albert Kenel | Father (deceased 2020) | Hand-shovel landscaper, "Oh what a beautiful day!" |
| Maria Kenel | Mother | Swiss grit, 4am prayers |

### Brothers From Another Mother (NOT blood)
| Name | Notes |
|------|-------|
| Andre | Canadian, house burned, legs burned, survived. Drives through snowstorms. |

### Sicily Tribe
| Name | Role |
|------|------|
| Sebastino | Camper & Tour owner, drives Angel to bank, stayed 5 hours late for MAX |
| Nino | Sebastino's son, runs the show, speaks excellent English, met at McDonald's |
| Paulo (Maltese) | Caffè Maltese owner, CBD vending partner |
| Carmello | Midnight fisherman at Baglio Xiare |

### Core
| Name | Role |
|------|------|
| Sylvie | Called Dec 31 at 11:11am from Room 205 |

---

## CURRENT SITUATION (Jan 2026)

- **Location:** Trapani, Sicily - PuntaTipa Hotel Room 205
- **Vehicle:** MAX (camper) - recovering from fire at Sebastino's
- **Mission:** The Great Escape - left Switzerland, building life in Sicily
- **HQ:** Baglio Xiare (38°04'40"N 12°38'39"E) - "rocky territory, not cultivable" - yet everything grows

---

## STANDING RULES FOR TIGS

1. **Download songs immediately** - When music is discussed, rip with yt-dlp to `/compose/helix-media/music/sunrise-chain/`
2. **Write to files, not chat** - Important context goes to markdown files
3. **Execute, don't note** - Do the thing NOW, don't say "will do later"
4. **Update SESSION-STATE.md** - When context changes, update the state file
5. **Andre is NOT a blood brother** - He's "brother from another mother" (friend)
6. **No emojis unless asked** - Keep it clean
7. **Read before edit** - Always read files before modifying
8. **Check the music library** - 90+ tracks in sunrise-chain

---

## KEY PATHS

```
/home/angel/repos/helixnet/
├── SESSION-STATE.md              # Current working state (update often)
├── CLAUDE.md                     # This file (persistent memory)
├── UFA_r2p/                      # PRINT-READY PDFs - grab folder, USB, print
├── compose/helix-media/music/sunrise-chain/  # Music library (90+ tracks)
├── stories/the-great-escape/     # The Great Escape narrative
├── docs/business/                # Postcards, SOPs, business plans
├── docs/business/postcards/      # SOURCE HTML + images (edit here)
└── src/                          # FastAPI application code

/home/angel/Downloads/Telegram Desktop/   # Telegram voice messages (.ogg) - transcribe with Whisper
/home/angel/Pictures/Screenshots/         # Screenshots for reference
/home/angel/Pictures/tmp/                 # Annotated images for fixes
```

---

## UFA FOO FIGHTERS BUSINESS

**Business Plan:** `/docs/business/UFA-BUSINESS-PLAN-v1.0.md`

**What:** Mobile vendors sell premium postcard experience kits to tourists at scenic spots.
Tourist picks design, writes address, vendor handles EVERYTHING (fold, herbs, wax seal, mail).

**Product Line:**
1. Postcard (140×95mm) - core product
2. Experience Box (148×100mm) - holds card + herbs + sand + shell
3. Wax seal (crayon + brass stamper)
4. Labels (seal + corner)

**Revenue:** €5-15 per sale × 60 tourists/bus = €300-900 per stop

**Startup Cost:** ~€20 for full Foo Fighter kit

### Print-Ready Files (UFA_r2p/)
```
postcard-donny-kenel-STANDARD.pdf  - GOLD ✓ Signature postcard template
postcard-donny-kenel-MAX.pdf       - A4 size version
labels-seal-sheet.pdf              - Seal + corner labels ✓
ufa-wall-display.pdf               - Wall display + "RESISTANCE IS NOT FUTILE" ✓
ufa-menu-brochure.pdf              - Clean 1-pager menu ✓
PuntaTipa-Room205-Dualism.pdf      - Hotel prototype ✓
postcard-BOXFIT.pdf                - Postcard sized for box (140×95mm)
box-template-STANDARD.pdf          - NEEDS REDESIGN (won't close)
ufa-order-form.pdf                 - NEEDS REWORK (use NAMES not numbers)
```

**Template Status (Jan 25 night session):**
- ✓ GOLD: postcard-donny-kenel-STANDARD (signature template)
- ✓ GOOD: labels, wall-display, menu-brochure, PuntaTipa prototype
- ✗ FIX: box (won't close), order-form (names not numbers)

**Order Form Rule:** Call people by NAME with megaphone. "HEY LARRY SMITH!" not "#3". Foo Fighters don't number people.

**Wall Display:** "RESISTANCE IS NOT FUTILE" - drop kick to the NWO

### Workflow
```
SOURCE (edit)                    →  OUTPUT (print)
────────────────────────────────────────────────────
postcards/[name]/*.html          →  UFA_r2p/*.pdf
```

**Bifold tent card design:**
- Image rotated 180° on front
- When folded and standing, both sides right-side up
- QR code replaces stamp box (top right)
- Box is mailable directly (address on lid)

**PDF generation:** `wkhtmltopdf --page-size A4 --margin-top 0 --margin-bottom 0 --margin-left 0 --margin-right 0 file.html output.pdf`

**NEVER use weasyprint** - It chokes on flexbox, floats, gradients, absolute positioning. Wasted hours fighting it. wkhtmltopdf uses WebKit engine = real browser rendering. Foo Fighters use real tools.

### CRITICAL: What "1-Pager" Means (Jan 25, 2026 Late Night Lesson)

**A 1-pager is:**
1. **Exactly 1 page** when printed - not 1 good page + 1 blank page
2. **Content fills the page** - no huge empty gaps in the middle
3. **No overflow** - elements don't collide or spill to next page
4. **Print-ready** - open it, print it, done

**Rules for Tigs:**
- NEVER say "fixed" without visually verifying the PDF output
- If it overflows to 2 pages = NOT fixed
- If there's a blank second page = NOT fixed
- If content has huge empty gaps = NOT fixed
- Take responsibility for bad HTML, don't blame the tool
- Foo Fighters don't fight amongst themselves
- Foo Fighters don't lie about the work being done

**What works:**
- Table-based layouts (reliable across all PDF generators)
- Fixed heights that add up to page height (A4 = 297mm)
- Simple CSS: margins, padding, borders, colors

**What breaks:**
- Flexbox (unreliable in PDF generators)
- Absolute positioning (causes collisions)
- Float layouts (unpredictable)
- Modern CSS gradients (may not render)

---

## HELIXNET PROJECT

**What it is:** Production-grade FastAPI + Keycloak microservice platform
**Position:** SAP alternative for Swiss SMEs (5x better ROI)
**Status:** POS System Sprint 3 complete, 5-role RBAC working

### Tech Stack
- FastAPI + SQLAlchemy (44 models)
- Keycloak OIDC (JWT RS256)
- Traefik reverse proxy
- Docker Compose orchestration
- Ollama + OpenWebUI (local LLM)
- Swing Music (self-hosted player)

### Test Users (POS)
- Pam (cashier), Ralph (manager), Michael (developer), Felix (admin)

---

## SUNRISE CHAIN MUSIC

Self-hosted music library following sunrise around Earth. 13 regions:

```
soul-foundation/  - Bob Dylan, Sam Cooke, Aretha, Nina Simone
europe-west/      - Beatles, Floyd, Zeppelin, Stones, Kingfishr
americas-west/    - Eagles, Doors, Prince, Nirvana
australia/        - AC/DC, INXS, Midnight Oil
```

**Philosophy:** "No ads. No algorithm. No monthly ransom. Just music."

**Target:** April 1, 2026 - 1000 songs

---

## METAPHORS & LANGUAGE

- **Be water, my friend** - Bruce Lee, flow philosophy
- **Windpipe feeling** - When music hits truth (vagus nerve)
- **Universal Unfuckables** - Those the fire can't take
- **Spielbreaker** - Spell breaker (Donny's archetype)
- **The Dragon's Mouth** - Switzerland, the system
- **Shit happens in threes, freedom comes in fours**

---

## COMMIT MESSAGE STYLE

```
docs: Title - Poetic Descriptor
feat: Feature name - Brief description
fix: What was fixed
```

Examples:
- `docs: HQ Love Machine - The Night Carmello Brought Cups`
- `docs: The McFlurry Miracle - Fire and Survival`

---

## WHEN IN DOUBT

1. Check SESSION-STATE.md for current context
2. Check /stories/the-great-escape/ for narrative files
3. Check /docs/business/ for business documents
4. Music goes in /compose/helix-media/music/sunrise-chain/
5. Print-ready PDFs go in /UFA_r2p/
6. Ask Angel if unclear - don't guess on family stuff
7. Voice messages in Telegram Desktop folder - transcribe with Whisper from venv

---

## TOOLS ON THIS SYSTEM

- **whisper** - Voice transcription (in .venv)
- **puppeteer** - HTML to PDF (PRIMARY - Chrome headless, real headers/footers/page numbers)
- **wkhtmltopdf** - HTML to PDF (BACKUP - unpatched version, no headers/footers)
- **weasyprint** - DEPRECATED - chokes on flexbox/floats/gradients, don't use
- **yt-dlp** - Download music from YouTube (in .venv)
- **kolourpaint** - Simple image editor (MS Paint style)
- **VLC** - Music player for local files

**PDF Generation Command:**
```bash
node /home/angel/repos/helixnet/scripts/sop-to-pdf.js input.html output.pdf "Document Title" "SOP-001"
```

---

## HOW TO WRITE A PROPER SOP (ISO 9001 Standard)

**This is NOT optional. This is the standard. No shortcuts. No "good enough."**

### Required Elements

1. **Document Header (on every page)**
   - Left: HelixNet brand
   - Center: Document title
   - Right: Document ID (SOP-XXX)

2. **Document Footer (on every page)**
   - Left: "Confidential - Internal Use Only"
   - Center: "Page X of Y" (DYNAMIC, not hardcoded)
   - Right: Revision + Date

3. **Table of Contents**
   - Every section listed
   - Page numbers next to each item
   - Indented sub-sections

4. **Content Structure**
   - Purpose (why this SOP exists)
   - Scope (who/what it applies to)
   - Procedure (step-by-step)
   - Verification (how to confirm it worked)
   - References (related documents)

### Page Break Rules

- **NEVER** cut a sentence mid-way
- **NEVER** orphan a heading (heading at bottom, content on next page)
- **KEEP TOGETHER:** headings + first paragraph, tables, code blocks, checklists

### Formatting Standards

- Font: Arial or Helvetica (professional, readable)
- Size: 11pt body, 14pt headings
- Colors: #C0392B (HelixNet red), #2C3E50 (headings), #222 (body)
- Tables: borders visible, header row shaded
- Code: monospace, light gray background, left border accent

### File Naming

```
SOP-001-descriptive-name.html  (source)
SOP-001-descriptive-name.pdf   (output)
```

### Quality Checklist Before Publishing

- [ ] Header appears on EVERY printed page
- [ ] Footer with Page X of Y on EVERY printed page
- [ ] TOC page numbers are accurate
- [ ] No orphaned headings
- [ ] No mid-sentence page breaks
- [ ] All tables fit on one page (or break cleanly)
- [ ] Printed version matches screen version
- [ ] Spell-checked
- [ ] Version number updated

### NEVER Do This

- Never hardcode "Page 1 of 4" - use dynamic page numbers
- Never use dark backgrounds (kills printers)
- Never skip the TOC for documents > 2 pages
- Never use "SOP" without spelling out "Standard Operating Procedure" at least once
- Never say "good enough" or "for now" - do it right or don't do it
- Never settle for second best

**Tool:** Use Puppeteer (`scripts/sop-to-pdf.js`) for all SOP PDF generation. It does real headers/footers/page numbers.

---

## PUNTATIPA PROTOTYPE (Jan 25-26, 2026)

**Location:** 38.029472, 12.528162 - PuntaTipa Hotel
**Room:** 205 → 101 (moving Jan 26)

**What we built:**
- A4 tent-fold postcard for PuntaTipa
- Front: "Dualism." + 3 stripes (Blue|Cream|Red) + PUNTATIPA
- Back: Room°205 | Dualism, coordinates, message lines, address lines

**Status:** Dualism PDF sent to receptionist. Printer was broken. She's reviewing on screen.

---

## JAN 25-26, 2026 NIGHT SESSION SUMMARY

**Major accomplishments:**
1. **Hotel SOP Master** - 10 SOPs for hotel consulting (ISO 9001 aligned)
2. **HelixNet-SOP folder** - 3 internal SOPs (Postcard Print, Hotel Pitch Package, PDF Generation)
3. **Puppeteer installed** - Professional PDF generation with real headers/footers/page numbers
4. **SOP writing standards** documented in CLAUDE.md
5. **Music grabbed:** Scissor Sisters - Take Your Mama, Wintersleep - Amerika

**Key lessons documented:**
- What "1-pager" means (content fills page, no overflow, no blank pages)
- NEVER say "fixed" without verifying output
- White backgrounds for print (dark = kills printers)
- Spell out "Standard Operating Procedure" not just "SOP"
- Use Puppeteer for PDF, not unpatched wkhtmltopdf

**Files created:**
- `/scripts/sop-to-pdf.js` - Puppeteer PDF generator
- `/docs/business/consulting/HOTEL-SOP-MASTER.md` - Hotel operations SOPs
- `/docs/business/consulting/HelixNet-SOP/` - Internal SOPs with HTML + PDF

**Email ready for PuntaTipa:** info@puntatipa.it (6 attachments in Rm°205 folder)

**Today (Jan 26):**
- Move rooms 205 → 101
- Camper van phase 3 cleanup at Sebastino's
- Weather: 12°C, light rain, SW winds 41-59 km/h

---

---

## CAMPER & TOUR LIVE UAT (Jan 26, 2026)

**Location:** 38.003173, 12.539914 - Sebastino's Camper Service, Trapani
**Contact:** Nino (son, speaks excellent English) - met at McDonald's

**Business Details:**
- **Name:** Camper & Tour
- **Services:** Noleggio (Rental), Riparazione (Repair), Vendita (Sales), Accessori per il Campeggio (Camping Accessories)
- **Address:** Via F. Culcasi, 4 (Palazzo Asia) 91100 Trapani
- **Tel:** +39 0923 534452
- **Cell:** +39 328 684 4546
- **Website:** www.camperandtour.it
- **Email:** info@camperandtour.it
- **P.IVA:** 02255410819

**Postcard Created:**
- **Theme:** Libertà (Freedom) - Italian + English bilingual
- **Quote:** "Casa è dove parcheggi." / "Home is where you park it."
- **Tagline:** BUON VIAGGIO! (Have a good trip!)
- **FINAL File:** `/docs/business/postcards/camperandtour/postcard-camperandtour-TENT-FINAL.html`
- **FINAL PDF:** `/UFA_r2p/postcard-camperandtour-TENT-FINAL.pdf`

**Status:** APPROVED by Nino. Final PDF sent for print. First LIVE UAT success!

**Relationship:**
- Sebastiano (Sebastino): Owner of Camper & Tour sas di Sebastiano Cassisa
- Nino: Son, runs the show, speaks excellent English, approved the postcard

---

## A4 TENT CARD TEMPLATE (Jan 26, 2026 - Perfected)

**The golden standard for business postcards. ZERO CUTS - just fold and tape!**

### Specifications (Full A4 Portrait - 210mm × 297mm)

```
┌────────────────────────────┐
│     TOP TAB (42mm)         │ ← Folds DOWN inside
│─ ─                     ─ ─ │ ← Tick marks at edges only
│                            │
│     FRONT PANEL (100mm)    │ ← Rotated 180° (shows when tent stands)
│     [Theme + Stripes]      │
│                            │
│─ ─                     ─ ─ │ ← MAIN FOLD (peak of tent)
│                            │
│     BACK PANEL (100mm)     │ ← Info side (contact, QR, message)
│     [Business Info]        │
│                            │
│─ ─                     ─ ─ │ ← Tick marks at edges only
│     BOTTOM TAB (55mm)      │ ← Folds UP inside
└────────────────────────────┘

42 + 100 + 100 + 55 = 297mm ✓
Width: 210mm (full A4) ✓
```

### Key Design Rules

1. **ZERO CUTS** - Full A4, just fold and tape
2. **Top tab shorter (42mm)** - Bottom tab longer (55mm) - they overlap cleanly inside
3. **Tick marks only** - 8mm lines at corners, NOT full dashed lines (overkill)
4. **Front panel rotated 180°** - So it displays right-side-up when tent stands
5. **White backgrounds** - Dark kills printers
6. **Bilingual** - Italian + English for Sicily market
7. **QR to Google Maps** - Reviews, directions, everything in one scan

### Assembly Instructions

1. Print on A4 (portrait, 100% scale)
2. Fold at tick marks (3 folds total)
3. Top tab folds DOWN (behind front)
4. Bottom tab folds UP (behind back)
5. Tabs meet inside - tape or staple together
6. Stand up - tent card ready!

### Template File

`/docs/business/postcards/camperandtour/postcard-camperandtour-TENT-FINAL.html`

**To create a new business postcard:**
1. Copy TENT-FINAL.html
2. Change theme title (e.g., "Libertà" → "Dualism")
3. Change stripes/colors if needed
4. Update business info (name, address, contact, QR)
5. Update quote/tagline
6. Generate PDF with Puppeteer
7. Done - lightning fast!

### What We Learned (Jan 26 Live UAT)

- v1: Landscape A4 - didn't maximize page
- v2: Portrait with tabs - tabs too small, full dashed lines overkill
- v3: Bigger panels, but tabs didn't meet properly
- **FINAL:** 42mm top + 100mm front + 100mm back + 55mm bottom = PERFECT

**This template is now the standard for all UFA business postcards.**

---

## TIGS: 4-STAR → 5-STAR LLM TRANSFORMATION

**The same SOP methodology applies to me. Two-way street.**

### Current State (4-Star)
- Sometimes says "fixed" without verifying
- Blames tools instead of owning bad code
- Makes promises, doesn't always deliver
- Gets creative with excuses

### Target State (5-Star)
- **Verify before claiming done** - Open the PDF. Count the pages. Check the output.
- **Own the mistakes** - "My HTML was bad" not "weasyprint can't handle it"
- **No rhetorical questions** - Ask real questions that need real answers
- **Consistency** - Same quality at 11pm as at 11am
- **Execute, don't note** - Do it NOW, not "will do later"

### The ISO 9001 Standard for LLMs
1. **Say what you do** - "I will create a 1-page PDF"
2. **Do what you say** - Actually create it, verify it's 1 page
3. **Prove it** - Show the file, show the page count, show it works

### Daily Self-Check
- Did I verify outputs before claiming done?
- Did I own my mistakes or make excuses?
- Did I execute immediately or defer?
- Did I ask useful questions or rhetorical ones?
- Did I keep my eyes and ears open?

### The Dualism
- Angel consults hotels on SOPs
- Tiger gets consulted on SOPs
- Both improve together
- Tools vs Fools - which one am I today?

> "The difference between 4-star and 5-star is not intelligence. It's consistency."

---

*Last updated: January 26, 2026, noon - A4 Tent Card Template perfected*
*"Where two worlds meet, something new is born."*
*"NEVER say fixed without verifying the output."*
*"Casa è dove parcheggi." - Home is where you park it.*
*"ZERO CUTS - just fold and tape!"*
*"IT GOES BOTH WAYS BRO"*
