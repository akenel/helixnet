# SOP-004: Restaurant Menu Design
## From Photos to Print-Ready A5 Bifold Menu
### HelixNet Standard Operating Procedure | ISO 9001 Aligned

---

## PURPOSE

Produce bilingual (IT/EN) restaurant menus for Trapani businesses. One intake visit, one SOP, print-ready output. The A5 bifold format matches what restaurants already use -- half A4, folded, no cuts.

---

## THE FORMAT: A5 BIFOLD

One A4 sheet, printed duplex (front + back), folded once down the middle.

```
OUTSIDE (Print Side 1):                  INSIDE (Print Side 2):
┌──────────────┬──────────────┐          ┌──────────────┬──────────────┐
│              │              │          │              │              │
│   PANEL 4    │   PANEL 1    │          │   PANEL 2    │   PANEL 3    │
│   (BACK)     │   (COVER)    │          │  (LEFT PAGE) │ (RIGHT PAGE) │
│              │              │          │              │              │
│  Drinks      │  Logo        │          │  Antipasti   │  Secondi     │
│  Beer        │  "Menu"      │          │  Primi       │  Contorni    │
│  Breakfast   │  Tagline     │          │  (Terra+Mare)│  Taglieri    │
│  Bar/Coffee  │  Address     │          │              │  Wines       │
│  Coperto     │  Phone       │          │              │              │
│  WiFi        │              │          │              │              │
│              │              │          │              │              │
│  ROTATED 180°│  NORMAL      │          │  NORMAL      │  NORMAL      │
└──────────────┴──────────────┘          └──────────────┴──────────────┘
        A4 Landscape (297 × 210mm)               A4 Landscape (297 × 210mm)
        Each panel = 148.5 × 210mm               Each panel = 148.5 × 210mm
```

**Why this works:**
- Matches existing restaurant menu size (A5 = 148.5 × 210mm)
- ZERO CUTS -- fold and done
- 1 EUR per menu at ISOTTO (1 A4 duplex print)
- Charge 100-300 EUR for design = 100-300x markup

---

## TOOLS

| Tool | Use | Status |
|------|-----|--------|
| Puppeteer (Chrome headless) | HTML to PDF | PRIMARY + ONLY |
| ISOTTO Sport, Trapani | Duplex printing | PRINT PARTNER |
| Camera / phone | Menu photos for extraction | INTAKE |

---

## FILE STRUCTURE

```
docs/business/PB/                    # One folder per restaurant
├── photos/                          # Reference photos from intake
│   ├── photo-1.jpg
│   └── ...
├── menu/
│   ├── menu-[name]-A5-bifold.html   # SOURCE (edit here)
│   └── menu-[name]-A5-bifold.pdf    # OUTPUT (print this)
└── notes.md                         # Client notes, preferences
```

---

## PROCEDURE

### Step 1: Intake (On-Site Visit)

Photograph the existing menu -- every page, both sides. Get:

**Required:**
- [ ] Business name (exact spelling)
- [ ] Address
- [ ] Phone number(s)
- [ ] All menu items with prices (every section)
- [ ] Wine list with prices
- [ ] Cover charge (coperto) amount
- [ ] WiFi network + password (tourists love this)

**Nice to have:**
- [ ] Logo or brand colors
- [ ] Tagline or slogan
- [ ] Social media / Google Maps
- [ ] Opening hours
- [ ] Photo of the exterior (for design reference)

### Step 2: Extract Menu Content

Read every photo. Extract ALL items, prices, and sections. Rules:

1. **Italian names are primary** -- bold, regular weight, dark color
2. **English translations are secondary** -- italic, smaller, gray
3. **Prices in EUR** -- right-aligned, burgundy/accent color, comma decimal (Italian style: 12,00 not 12.00)
4. **Group by section** -- follow the restaurant's own grouping
5. **Terra/Mare split** -- if the restaurant separates land/sea dishes, keep it
6. **Daily specials** -- mark as "Piatto del giorno" with "--" for price

### Step 3: Build HTML from Template

Copy the A5 bifold template. Fill in content following the panel layout:

**Panel 1 (Cover):** Logo, "Menu" title, subtitle, tagline (IT + EN), address, phone
**Panel 2 (Inside Left):** Antipasti, Primi (Terra + Mare)
**Panel 3 (Inside Right):** Secondi (Terra + Mare), Contorni, Taglieri, Wines
**Panel 4 (Back):** Dolci, Bibite, Birra, Colazione, Bar, Coperto, WiFi

**CSS Rules:**
```css
@page { size: A4 landscape; margin: 0; }

/* Each panel = half the A4 width */
.panel { width: 148.5mm; height: 210mm; position: absolute; }
.panel-left { left: 0; }
.panel-right { left: 148.5mm; }

/* Back panel rotated so it reads right when menu is flipped */
.panel-left .back-content { transform: rotate(180deg); }
```

**Typography:**
- Body font: Georgia or Times New Roman (serif = restaurant feel)
- UI font: Helvetica Neue or Arial (prices, labels, subtitles)
- Section titles: 10-12pt italic, accent color, bottom border
- Menu items: 7-8pt, flex row with dotted leader to price
- Wine items: 6.5-7pt (tighter to fit the list)

**Colors (adapt per restaurant):**
- Background: cream (#FDFAF5) -- warm, not stark white
- Accent: burgundy (#6B2D3E) for PB, adapt to restaurant brand
- Body text: dark (#2C2C2C)
- English/secondary: gray (#999)
- Prices: accent color, semibold

### Step 4: Generate PDF

```bash
node scripts/postcard-to-pdf.js menu-[name]-A5-bifold.html menu-[name]-A5-bifold.pdf
```

### Step 5: VERIFY (Critical)

```bash
# Must be exactly 2 pages
pdfinfo menu-[name]-A5-bifold.pdf | grep Pages
# Expected: Pages: 2

# Open and check
xdg-open menu-[name]-A5-bifold.pdf
```

**Verification Checklist:**
- [ ] Exactly 2 pages (outside + inside)
- [ ] Page 1: Cover reads normally (right side), Back reads upside-down (left side)
- [ ] Page 2: Both inside panels read normally
- [ ] All prices match the original menu
- [ ] No content overflow or cut-off
- [ ] No blank gaps
- [ ] Dotted leaders connect item names to prices
- [ ] Wine list fits without overflow
- [ ] Fold line is centered (148.5mm from left)
- [ ] Print a test copy at ISOTTO before the full run

### Step 6: Client Approval

Print ONE test copy. Bring it to the restaurant. Fold it. Stand it on the table.

- Does it look like their menu? (Same size, same feel, better design)
- Are all items correct? (Owner checks every price)
- Any items to add/remove? (Seasonal changes)

**Only after owner approval: print the full run.**

### Step 7: Print at ISOTTO

- Format: A4 duplex (front + back on same sheet)
- Paper: 160-200gsm (thicker = more professional, holds up to sauce stains)
- Quantity: Start with 50 (test batch), then 100-200 per order
- Cost: ~1 EUR per menu (A4 duplex on quality paper)

---

## SECTION ORDER STANDARD

This order works for Sicilian restaurants. Adapt if the restaurant has a different structure.

| Panel | Sections |
|-------|----------|
| Cover (Panel 1) | Logo, Title, Subtitle, Tagline, Address, Phone |
| Inside Left (Panel 2) | Antipasti, Primi (Terra, Mare) |
| Inside Right (Panel 3) | Secondi (Terra, Mare), Contorni, Taglieri, Vini |
| Back (Panel 4) | Dolci, Bibite, Birra, Colazione, Bar, Coperto, WiFi |

**Logic:** Customer opens menu, sees the food they'll order (antipasti → primi → secondi). Drinks and extras are on the back -- they order those after deciding on food.

---

## PRICING

| Item | Cost | Charge | Margin |
|------|------|--------|--------|
| Design (first menu) | Your time | 100-200 EUR | 100% |
| Design (revision) | Your time | 50 EUR | 100% |
| Print per menu (ISOTTO) | ~1 EUR | Included or pass-through | -- |
| Print run 100 menus | ~100 EUR | 150-200 EUR | 50-100% |
| Seasonal update | Your time | 50-75 EUR | 100% |

**Annual value per restaurant:** 200-500 EUR (initial + 2-3 seasonal updates)

---

## SCALING

| Restaurants | Monthly Revenue | Effort |
|-------------|----------------|--------|
| 5 | 250-500 EUR | Part-time |
| 10 | 500-1000 EUR | Part-time |
| 20 | 1000-2000 EUR | Pipeline full |

Every restaurant in tourist-heavy Trapani needs this. Walk in with a printed sample, show them the quality difference. The menu sells itself.

---

## COMMON MISTAKES

| Mistake | Fix |
|---------|-----|
| Prices don't match original | Triple-check every price against photos |
| Wine list overflows panel | Use tighter line-height (7pt) and abbreviate varietals |
| Back panel reads wrong way | Must rotate 180° -- check by folding a test print |
| English translations wrong | Use simple, clear translations -- not Google Translate |
| Too much content for 4 panels | Move least-ordered items to a separate insert, or use smaller font |
| Dark backgrounds | White/cream backgrounds only -- dark kills printers and ink costs |

---

## TEMPLATE FILE

**Golden template:** `docs/business/PB/menu/menu-piccolo-bistrot-A5-bifold.html`

Copy this file for each new restaurant. Change:
1. Business name, address, phone
2. Colors (accent color to match their brand)
3. Menu items and prices
4. Wine list
5. Tagline
6. WiFi credentials

---

## CLIENTS

| # | Restaurant | Location | Status | File |
|---|-----------|----------|--------|------|
| 1 | Piccolo Bistrot | Via Garibaldi 43, Trapani | DRAFT v1 | PB/menu/menu-piccolo-bistrot-A5-bifold.html |

---

**Document Version:** 1.0
**Created:** January 31, 2026
**Author:** HelixNet
**Related:** SOP-001 (Postcard Print), SOP-003 (PDF Generation)
