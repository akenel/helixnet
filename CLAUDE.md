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
| ISOTTO Sport | Print + merch partner, Via Buscaino area, since 1968, WhatsApp +39 349 972 9418, Famous Guy knows his stuff |
| Mixology Trapani | Beverage wholesale, Via M. Buscaino 15, Tel 0923 390052, FB @mixologytp |
| Marcello Virzi | Sales Manager, Tenute Parrinello winery (since 1936), Marsala - meeting end of week |
| Kevin Galilee | World passport holder, insane in a good way, camping/shower host near HQ |
| Color Clean | Lavanderia, Via Virgilio 71/73, loved the tent card + review, wants full card set |
| Pizza Planet | Ciccio's place, Via Vespucci 13 Bonagia, 38°03'51"N 12°35'49"E, forno a legna dal 2000 |
| Piccolo Bistratto | Giovanni's place, Jonathan the chef, Paolo (friend), wants card set |

### Core
| Name | Role |
|------|------|
| Sylvie | Called Dec 31 at 11:11am from Room 205 |

---

## CURRENT SITUATION (Feb 3, 2026)

- **Location:** Trapani, Sicily - PuntaTipa Hotel Room 101
- **Vehicle:** MAX (camper) - stove install Thursday at Sebastino's
- **Insurance:** AXA claim 22.831.735/0001 - no deductible, waiting on adjuster
- **RAV:** CLOSED OUT - benefits ended Jan 31
- **Mission:** The Great Escape - building UFA postcard/merch business in Sicily
- **HQ:** Baglio Xiare (38°04'40"N 12°38'39"E) - Kevin offers camping + showers
- **Print partner:** ISOTTO Sport, Trapani - printing, clothing, merch, since 1968
- **Dharma Life:** Meeting done Feb 3, Vyoma demo, waiting for instance access + recording
- **Postcard pipeline:** Pizza Planet (tonight), Color Clean (card set), Piccolo Bistratto (card set)

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

**Bifold tent card design (B2B):**
- Image rotated 180° on front
- When folded and standing, both sides right-side up
- QR code replaces stamp box (top right)
- Box is mailable directly (address on lid)

**Duplex postcard design (B2C):**
- Single HTML file, 2 pages: page 1 = front (images), page 2 = back (postcard info)
- A4 portrait, de-personalized: blank message lines, blank address, stamp box
- Each card has unique series number, quote, and front image
- Source: `postcards/duplex-a4/duplex-NNN-name.html`

**Format A: 2-card layout (001-003):**
- 148mm x 100mm cards, stacked vertically, centered
- Dashed cut line between cards, registration marks at corners + midpoints
- Page labels top/bottom centered
- Cost: 50 cents per card (1 EUR per A4 = 2 cards)

**Format B: 3-card layout (004+):**
- 137.6mm x 93mm cards (5% proportional scale), 3 per A4 sheet
- 6mm gaps between cards (3mm safety each side for hand-cutting)
- 3mm frame: cards positioned top-left (`position: absolute; top: 3mm; left: 3mm`)
- NO registration marks on front page (clean image side)
- Registration marks on back page only
- Page labels rotated 90° in right margin (`left: 175mm; rotate(90deg)`) -- invisible in card zone
- Layout: 3mm + 93 + 6 + 93 + 6 + 93 + 3 = 297mm (fills A4 exactly)
- Cost: **33 cents per card** (1 EUR per A4 = 3 cards)
- SVG for graphic-only fronts (e.g., 005 Italian flag) -- no raster images needed, prints razor sharp

**Format C: 4-UP layout (Feb 3, 2026) -- PREFERRED for B2B:**
Two templates, same math, different orientation:

**C1: A4 PORTRAIT page = PORTRAIT images**
- `@page { size: A4 portrait; }` (210mm x 297mm)
- Card size: **99mm x 142.5mm** (taller than wide)
- 2x2 grid, 3mm frame all edges, 6mm gap middle
- Math: 3 + 99 + 6 + 99 + 3 = 210mm width ✓
- Math: 3 + 142.5 + 6 + 142.5 + 3 = 297mm height ✓
- Template: `postcards-pizza-planet-A4-PORTRAIT.html`

**C2: A4 LANDSCAPE page = LANDSCAPE images**
- `@page { size: A4 landscape; }` (297mm x 210mm)
- Card size: **142.5mm x 99mm** (wider than tall)
- 2x2 grid, 3mm frame all edges, 6mm gap middle
- Math: 3 + 142.5 + 6 + 142.5 + 3 = 297mm width ✓
- Math: 3 + 99 + 6 + 99 + 3 = 210mm height ✓
- Template: `postcards-pizza-planet-A4-LANDSCAPE.html`

**4-UP Cutting:**
- 1 horizontal cut through center
- 1 vertical cut through center
- Result: 4 cards with 3mm white frame on all sides
- Cost: **25 cents per card** (1 EUR per A4 = 4 cards)

**4-UP Duplex Printing:**
- Page 1: Fronts (A, B, C, D)
- Page 2: Backs (B, A, D, C) -- mirrored for short-edge flip
- Tell printer: "PORTRAIT PDF = Portrait orientation, LANDSCAPE PDF = Landscape orientation"

**4-UP GOLD Templates (Feb 3, 2026 - LOCKED IN):**

| Template | File | QR Size | Footer Style |
|----------|------|---------|--------------|
| Portrait | `templates/4UP-PORTRAIT-GOLD.html` | 30mm | QR stacked, label below |
| Landscape | `templates/4UP-LANDSCAPE-GOLD.html` | 24mm | QR + label side by side |

**Landscape footer layout (space-optimized):**
```
[QR 24mm] Google Maps        [coords]       [address]
          Reviews•Directions  [tagline]      [phone]
```

**Key design decisions (DO NOT CHANGE):**
- Landscape: QR + "Google Maps" side by side (saves vertical space)
- Landscape: "Reviews • Directions" sublabel (tells what they get)
- Landscape: NO "Your Message" label (blank space is obvious)
- Portrait: QR stacked with label below (more vertical room)
- Both: Footer has red top border (1px solid #8B0000)
- Both: Phone number bold + red (#8B0000)

**To create new client postcards:**
1. Copy the GOLD template for the orientation you need
2. Replace images, quotes, business info, QR code
3. DO NOT touch the footer layout - it's perfected

**UFA Wolf Philosophy (QR codes):**
- One shot, one kill
- Don't give people choices, give them THE choice
- A QR code is a command: "Scan this." Not "scan one of these three things maybe."
- All cards get Google Maps QR only -- directions + reviews + call in one scan

**QR Code URLs - CRITICAL DISTINCTION (Feb 3, 2026 lesson):**

| Type | URL Format | Result | USE THIS? |
|------|------------|--------|-----------|
| **PLACE link** | `https://maps.google.com/?cid=XXXXX` or `https://g.page/shortname` | Reviews, directions, call, hours, photos | YES |
| **Coordinates** | `https://www.google.com/maps?q=38.064,12.597` | Pin on map, street view only | NO |

**How to get the PLACE link:**
1. Search business on Google Maps
2. Click "Share" → "Copy link"
3. That's the link with `?cid=` or `g.page` - use THIS for QR

**NEVER use DMS coordinates for QR** - they just drop a pin with no business info.

**QR Verification Checklist (before print):**
- [ ] Scan the QR with phone
- [ ] Confirm it opens Google Maps PLACE (not just coordinates)
- [ ] Confirm you see: business name, reviews, "Directions" button, "Call" button
- [ ] If you only see a pin with street view = WRONG QR, regenerate

**PDF generation:** `node scripts/postcard-to-pdf.js input.html output.pdf`

### Print Kit Structure (ISOTTO Runs) - Feb 3, 2026

**Every print run gets a complete kit. No loose files. No guessing.**

**Folder naming:**
```
ClientName-ISOTTO/YYYY-MM-DD - Description/
```

**Required contents:**
```
ClientName-ISOTTO/
└── YYYY-MM-DD - Description/
    ├── PRINT-INSTRUCTIONS.md      ← SOURCE (edit this)
    ├── PRINT-INSTRUCTIONS.html    ← STYLED (show to printer)
    ├── client-4UP-PORTRAIT.pdf    ← Print file
    ├── client-4UP-LANDSCAPE.pdf   ← Print file
    ├── client-4UP-PORTRAIT.html   ← Source HTML (for on-site fixes)
    ├── client-4UP-LANDSCAPE.html  ← Source HTML (for on-site fixes)
    └── images-pollinations/       ← Images used by HTML
```

**PRINT-INSTRUCTIONS.md must include:**
1. **Files to Print** - Table with filename, orientation, result
2. **Print Settings** - Paper weight, duplex mode, scale, margins
3. **CRITICAL setting** - SHORT EDGE FLIP (Voltare sul lato corto)
4. **Order Quantity** - Sheets, cards, budget
5. **Cut Dimensions for Cutter Machine** - Exact numbers so printer doesn't do math
6. **Cutting Guide** - ASCII diagram showing 2-cut method
7. **Quality Checklist** - Checkboxes for printer to verify
8. **Backup Files** - What to use if edits needed on-site

**Standard 4-UP Cut Dimensions (enter directly into cutter):**
| PDF | Page Size | Horizontal Cut | Vertical Cut |
|-----|-----------|----------------|--------------|
| PORTRAIT | 210 x 297mm | 148.5mm | 105mm |
| LANDSCAPE | 297 x 210mm | 105mm | 148.5mm |

**PRINT-INSTRUCTIONS.html features:**
- Red header with client name and date
- Tables for settings and files
- Orange warning box for CRITICAL settings
- Blue cutting diagram
- Green checklist with empty checkboxes
- Professional look - printer takes you seriously

**Workflow:**
1. Create .md first (easy to edit)
2. Generate .html from .md template (or hand-code)
3. **VERIFY QR CODE** - Scan it, confirm Google Maps PLACE opens (not just coordinates)
4. Copy entire folder to USB
5. Tell printer: "Open PRINT-INSTRUCTIONS.html first"

**Template location:** `/UFA_r2p/PRINT-INSTRUCTIONS.html` (copy and customize)

**ONLY use Puppeteer (Chrome headless)** for all PDF generation. wkhtmltopdf and weasyprint are UNINSTALLED.
- wkhtmltopdf (Qt WebKit ~2016) caused blank second pages, black bars from CSS gradients, broken flexbox. Uninstalled Jan 29, 2026.
- weasyprint chokes on flexbox/floats/gradients. Never worked. Uninstalled.
- Puppeteer uses real Chrome 144 -- modern CSS, exact 1-page output, printBackground support. Foo Fighters use real tools.
- **Key setting:** `preferCSSPageSize: true` -- respects `@page { size: A4 landscape; }` from CSS (added Feb 3, 2026)

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

**What works (Puppeteer/Chrome):**
- Everything -- flexbox, grid, gradients, absolute positioning, modern CSS
- Fixed heights that add up to page height (A4 = 297mm portrait, 210mm landscape)
- `@page { size: A4 landscape; }` respected by Chrome
- `printBackground: true` renders all colors and backgrounds

**What to avoid:**
- JavaScript-dependent layouts (Chrome renders before JS settles)
- External fonts without @font-face (use system fonts or embed)

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
- **puppeteer** - HTML to PDF (ONLY tool -- Chrome 144 headless, real headers/footers/page numbers)
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
- Puppeteer ONLY for PDF -- wkhtmltopdf uninstalled Jan 29, 2026

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

### Specifications v2 (Full A4 Portrait - 210mm × 297mm)

```
┌────────────────────────────┐
│     TOP FLAP (50mm)        │ ← Folds DOWN inside
│─ ─                     ─ ─ │ ← Tick marks (8mm) at edges only
│                            │
│   BACK PANEL (98.5mm)      │ ← Rotated 180° (details, QR, message)
│   [Business Info]          │
│                            │
│─ ─                     ─ ─ │ ← MAIN FOLD (peak of tent)
│                            │
│   FRONT PANEL (98.5mm)     │ ← Normal orientation (theme, flag, tagline)
│   [Theme + Flag]           │
│                            │
│─ ─                     ─ ─ │ ← Tick marks at edges only
│     BOTTOM FLAP (50mm)     │ ← Folds UP inside
└────────────────────────────┘

50 + 98.5 + 98.5 + 50 = 297mm ✓
Equal flaps = fits envelopes cleanly
```

### Key Design Rules

1. **ZERO CUTS** - Full A4, just fold and tape
2. **Equal flaps (50mm)** - Clean fold, fits envelopes
3. **Tick marks only** - 8mm lines at corners, NOT full borders
4. **Back panel rotated 180°** - Reads right when tent stands
5. **White backgrounds** - Dark kills printers
6. **Bilingual** - Italian + English for Sicily market
7. **QR to Google Maps** - Reviews, directions, one scan
8. **No flexbox on page** - Stacked blocks with fixed heights, float inside panels
9. **SVG flag** - CSS backgrounds don't survive PDF pipeline

### Template File (v2 - CURRENT)

`/docs/business/postcards/camperandtour/postcard-camperandtour-TENT-v2.html`

**To create a new business postcard:**
1. Copy TENT-v2.html
2. Change theme (e.g., "Libertà" → "Spirito")
3. Update business info, contact, QR code
4. Update quote/tagline
5. Generate PDF: `node scripts/postcard-to-pdf.js input.html output.pdf`
6. Verify output before claiming done

### Clients

| # | Business | Format | Status |
|---|----------|--------|--------|
| 1 | Camper & Tour | Tent Card | PRINTED + APPROVED by Nino |
| 2 | Mixology Trapani | Tent Card | PoC draft, needs approval |
| 3 | Pizza Planet | 4-UP (Portrait + Landscape) | Ready for print, Feb 3 |
| 4 | Color Clean | 4-UP | Pipeline |
| 5 | Piccolo Bistratto | 4-UP | Pipeline |

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
- **Own the mistakes** - "My HTML was bad" not "the PDF tool can't handle it"
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

## THE SEAL INSPECTION LESSON (Feb 6, 2026)

**What happened:** MAX camper van had a bathroom window seal fail. Water leaked behind plastic ceiling panels for years. Entire roof structure rotted end-to-end. Estimated repair: EUR 5,000-10,000+, 4-6 weeks.

**The pattern:**
- Sleeping area window seal failed immediately after purchase from Bantam
- Bantam fixed ONE window, never inspected the other two
- Swiss repair shops did work over the years, never did proper seal inspections
- Even at Camper & Tour (Trapani), technicians were inside the van for DAYS and didn't see the damage
- Only discovered because Angel INSISTED on a ladder inspection of the roof

**The lesson:** When ONE component fails, check ALL similar components.

If one seal is bad, ALL seals are suspect -- same age, same manufacturer, same exposure. This applies to:
- Software: If one API endpoint has a bug, check the similar ones
- Hardware: If one seal fails, inspect all seals
- Systems: If one health check is fake, audit all health checks
- People: If one person cuts corners, verify everyone's work

**The bigger problem:** The senior people who would have caught this are gone. Retired, laid off, pushed out. Juniors fix what's on the ticket and close the job. Nobody thinks two steps ahead anymore. Institutional knowledge is disappearing.

**Why Angel has to ask four times:** Because he's become the "old guy who catches things" by necessity. The mentorship chain is broken. Knowledge now passes customer-to-technician, the hard way.

**The rule:** When you find one problem, ask: "What else has the same failure mode?" Don't fix the symptom and close the ticket. Find the pattern.

> "If one seal fails, check all the seals. If one window leaks, inspect all the windows. The problem you find is rarely the only problem."

---

*Last updated: February 6, 2026, 2:00pm - Seal inspection lesson learned at Camper & Tour, Trapani*
*"NEVER say fixed without verifying the output."*
*"Casa è dove parcheggi." - Home is where you park it.*
*"ZERO CUTS - just fold and tape!"*
*"Don't poke the dragon on your way out the door."*
*"The postcard is the handshake. The coffee is the close."*
*"If one seal fails, check all the seals."*
