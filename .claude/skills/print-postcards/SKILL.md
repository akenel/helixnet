---
name: print-postcards
description: How to make UFA postcards, tent cards, print kits, and ISO-9001 SOPs — formats, cut math, QR rules, Puppeteer PDF gen, and the "1-pager" contract. Load when doing ANY postcard / print / SOP / PDF work. Migrated verbatim from CLAUDE.md 2026-07-17 to keep it out of every session's always-loaded context.
---

# UFA Print & Postcard Production

Everything here was Angel's hard-won print procedure. It's task-specific — only needed when you're
actually making a card, a print kit, or an SOP — so it lives here (loaded on demand) instead of in
CLAUDE.md (loaded every session). Nothing was changed; this is the verbatim playbook.

**PDF generation is Puppeteer ONLY** (Chrome headless). wkhtmltopdf + weasyprint are UNINSTALLED (see why below).

---

## Print-Ready Files (UFA_r2p/)
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

---

## Workflow
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

---

## Print Kit Structure (ISOTTO Runs) - Feb 3, 2026

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

---

## CRITICAL: What "1-Pager" Means (Jan 25, 2026 Late Night Lesson)

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

## HOW TO WRITE A PROPER SOP (ISO 9001 Standard)

**This is NOT optional. This is the standard. No shortcuts. No "good enough."**

### Required Elements

1. **Document Header (on every page)** — Left: HelixNet brand · Center: Document title · Right: Document ID (SOP-XXX)
2. **Document Footer (on every page)** — Left: "Confidential - Internal Use Only" · Center: "Page X of Y" (DYNAMIC, not hardcoded) · Right: Revision + Date
3. **Table of Contents** — Every section listed, page numbers next to each item, indented sub-sections
4. **Content Structure** — Purpose (why this SOP exists) · Scope (who/what it applies to) · Procedure (step-by-step) · Verification (how to confirm it worked) · References (related documents)

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
