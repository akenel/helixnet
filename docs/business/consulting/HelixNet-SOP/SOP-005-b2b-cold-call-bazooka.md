# SOP-005: B2B Cold-Call Bazooka
## The 3 EUR Pitch Kit That Sells Itself
### HelixNet Standard Operating Procedure

---

## PURPOSE

Walk into any UFA-worthy local business with a ready-made sample kit -- tent card + 6 postcards -- for 3 EUR total cost. No pitch deck. No portfolio. The product IS the pitch.

---

## THE TWO PRODUCT LINES

| | Business Tent Card (B2B) | Duplex Postcards (B2C) |
|---|---|---|
| **Format** | A4 portrait, single-side, fold = tent | A4 portrait, duplex at ISOTTO, cut to cards |
| **Front** | Brand + theme + flag + quote | Art (Banksy / Bauhaus / UFA original) |
| **Back** | Business info, hours, phone, QR | Postcard: message lines, address, stamp, business QR |
| **Lives** | On counter/table permanently | Goes home with customer |
| **Value** | Google reviews via QR scans | Collectible art + mailable postcard + QR |
| **Cost** | ~1 EUR (1 A4 sheet) | ~33 cents each (3 per A4 sheet) |

**Combined:** 1 tent card + 6 postcards (2 A4 sheets) = **3 EUR at ISOTTO**

---

## THE UFA FILTER

**Not every business gets a kit. This is earned.**

Before you build anything, the business must pass the UFA test:

- [ ] You have eaten/shopped/used their service personally
- [ ] You went back at least once (not a one-time visit)
- [ ] You would genuinely recommend them to a friend
- [ ] The owner/staff treats people right
- [ ] The quality is consistent, not just a lucky day
- [ ] You would give them a real 5-star Google review

**If any box is unchecked: walk away. The UFA seal means something.**

The cold-call bazooka only works because it's authentic. A card for a restaurant you've never eaten at is just spam with better typography.

---

## BUSINESS ASSESSMENT (Before You Build Anything)

### Step 1: Channel Audit

After passing the UFA filter, audit what the business already has online:

| Channel | Check | Link | Notes |
|---------|-------|------|-------|
| Google Maps | Y/N | _____________ | How many reviews? Rating? |
| Facebook | Y/N | _____________ | Active? Last post? Followers? |
| Instagram | Y/N | _____________ | Photos? Likes? Best content? |
| WhatsApp Business | Y/N | _____________ | Do they take orders via WhatsApp? |
| TripAdvisor | Y/N | _____________ | Tourist traffic? Ranking? |
| Website | Y/N | _____________ | Professional or just a placeholder? |

### Step 2: Classify Business Maturity Level

| Level | Profile | Example | Google Reviews | Online Presence |
|-------|---------|---------|----------------|-----------------|
| **1 - Newborn** | Just starting, minimal online | Piccolo Bistrot | Under 20 | Google Maps only |
| **2 - Established** | Years in business, multiple platforms | Pizza Planet | 20-100+ | Google + FB + Instagram + maybe more |
| **3 - Scaling** | Strong brand, active social, delivery | (future) | 100+ | All platforms + WhatsApp ordering + delivery apps |

### Step 3: QR Channel Strategy (Based on Level)

**Level 1 -- Concentrate:**
All 6 postcards point to Google Maps. One QR code. Simple. The goal is REVIEWS.
> "You need 50 reviews before anything else matters. Every card drives one action: leave a review."

| Card 1 | Card 2 | Card 3 | Card 4 | Card 5 | Card 6 |
|--------|--------|--------|--------|--------|--------|
| Google | Google | Google | Google | Google | Google |

**Level 2 -- Diversify:**
Split QR codes across the business's active channels. Each card design = different channel.

| Card 1 | Card 2 | Card 3 | Card 4 | Card 5 | Card 6 |
|--------|--------|--------|--------|--------|--------|
| Google | Instagram | Facebook | Google | Instagram | Facebook |

Or if they have WhatsApp ordering:

| Card 1 | Card 2 | Card 3 | Card 4 | Card 5 | Card 6 |
|--------|--------|--------|--------|--------|--------|
| Google | Instagram | WhatsApp | Google | Instagram | WhatsApp |

**Level 3 -- Full Spectrum:**
All channels covered. Consider seasonal rotation (summer = TripAdvisor for tourists, winter = WhatsApp for locals).

| Card 1 | Card 2 | Card 3 | Card 4 | Card 5 | Card 6 |
|--------|--------|--------|--------|--------|--------|
| Google | Instagram | Facebook | WhatsApp | TripAdvisor | Website |

### Step 4: Generate QR Codes

One QR code per channel, all in business brand color:

```bash
# Example: Pizza Planet (Level 2) -- 3 channels
source .venv/bin/activate

# Google Maps
python3 -c "import qrcode; qr = qrcode.QRCode(border=2); qr.add_data('https://maps.app.goo.gl/XXXXX'); img = qr.make_image(fill_color='#8B0000', back_color='#FFFDF5'); img.save('/tmp/qr-pp-google.png')"

# Instagram
python3 -c "import qrcode; qr = qrcode.QRCode(border=2); qr.add_data('https://instagram.com/pizzaplanet'); img = qr.make_image(fill_color='#8B0000', back_color='#FFFDF5'); img.save('/tmp/qr-pp-instagram.png')"

# Facebook
python3 -c "import qrcode; qr = qrcode.QRCode(border=2); qr.add_data('https://facebook.com/pizzaplanet'); img = qr.make_image(fill_color='#8B0000', back_color='#FFFDF5'); img.save('/tmp/qr-pp-facebook.png')"
```

**Future (HelixNet tracking):** Replace direct URLs with redirect URLs:
```
https://helixnet.app/qr/pp-google-001    → redirects to Google Maps
https://helixnet.app/qr/pp-insta-001     → redirects to Instagram
https://helixnet.app/qr/pp-fb-001        → redirects to Facebook
```
Each scan logs: timestamp, device, channel. Dashboard shows which channels customers actually use. No reprinting needed -- just change the redirect target.

---

## THE ART PIPELINE: From Photos to Postcards

### Where Art Comes From

| Source | How | Quality |
|--------|-----|---------|
| SVG (Tigs builds) | Code-generated geometric/typographic designs | Good for PoC, Bauhaus style, text-heavy |
| Nano Banana AI | Angel runs prompts, AI generates art from reference photos | Great for Banksy, painterly, photorealistic styles |
| Angel's photos | USB pull from FP3, used directly or as Nano Banana reference | Authentic, personal, unique |
| Business photos | Screenshots from their Instagram/Facebook (Angel browses) | Their best content transformed into art |

### The Nano Banana Workflow

**Angel does the recon (Tigs can't access Instagram/Facebook):**

1. Browse the business's Instagram / Facebook on your phone or laptop
2. Screenshot their best content:
   - Posts with the most likes/engagement
   - Beautiful food/product shots
   - Atmosphere shots (the oven, the team, the view)
   - Anything that captures their identity
3. Save screenshots to a folder or plug in phone for USB pull
4. Tell Tigs: "Here are 5 screenshots from Pizza Planet's Instagram"

**Tigs writes the AI prompts:**

Based on the reference photos, Tigs writes style-specific prompts for Nano Banana:

**Banksy/Street Art Style:**
```
A Banksy-style stencil artwork of [describe the key element from their photo].
Dark red (#8B0000) and cream, spray paint drip effects running down.
High contrast, urban street art aesthetic. No text.
Landscape format, 520x352 pixels.
```

**Bauhaus/Geometric Style:**
```
Bauhaus geometric poster inspired by [describe the scene].
Primary forms: circles, triangles, rectangles. Grid lines.
Color palette: deep red, golden yellow, charcoal on warm cream.
1920s German design school aesthetic. Clean, mathematical.
Landscape format, 520x352 pixels.
```

**Pop Art / Warhol Style:**
```
Pop art interpretation of [describe the food/product].
Bold outlines, flat colors, halftone dots.
Italian color palette: green, white, red accents.
Andy Warhol meets Sicilian cuisine.
Landscape format, 520x352 pixels.
```

**Minimalist/Japanese Style:**
```
Minimalist line drawing of [describe the subject].
Single continuous line, negative space, zen aesthetic.
One accent color: [brand color]. White background.
Less is more. Landscape format, 520x352 pixels.
```

**Angel runs the prompts:**

1. Open Nano Banana
2. Paste the prompt
3. Generate 3-4 variations
4. Pick the best one
5. Save as PNG (name: `nb-[business]-[style]-[number].png`)
6. Drop in the business folder

**Tigs formats into postcards:**

1. Place the Nano Banana images into the card-front template
2. Adjust cropping/positioning with `object-fit: cover`
3. Generate PDF
4. Proof together

### Reference Photo Folder Structure

```
docs/business/postcards/[business-name]/
    reference/                        # Screenshots + photos for art direction
        insta-01-pizza-oven.png       # Instagram screenshot
        insta-02-seafood-close.png    # Their best food shot
        fb-01-team-photo.png          # Facebook screenshot
        angel-01-exterior.jpg         # Angel's own photo
    nb-art/                           # Nano Banana outputs
        nb-pp-banksy-01.png           # AI-generated art
        nb-pp-bauhaus-01.png
        nb-pp-popart-01.png
```

---

## THE 3-VISIT PIPELINE

### Visit 1: Experience + Recon (Customer Mode)

You are a customer. Not a salesman. Not a consultant.

- Eat the food / use the service
- Observe: What's their vibe? Brand colors? Tagline?
- Note: Do they have social media? What platforms?
- Check: Google Maps listing, Facebook, Instagram, WhatsApp
- Decide: Is this a UFA business? Would you come back?
- **Screenshot their best Instagram/Facebook content** (for Nano Banana later)
- Fill out the Channel Audit table

**If YES:** Take mental notes, screenshots, photos. You'll be back.

**If NO:** Enjoy the meal and move on. Not every business is UFA material.

### Between Visits: Build the Kit (Tigs + Angel)

**Phase 1 -- Tigs builds the foundation (30 min):**

1. **QR Codes** -- One per channel based on maturity level
2. **Tent Card** -- Copy template, customize business info
3. **Postcard backs** -- Business-branded, channel-specific QR per card
4. **SVG front designs** -- PoC quality, good enough for first gift

**Phase 2 -- Art upgrade (optional, 30 min):**

5. Angel reviews reference photos
6. Tigs writes Nano Banana prompts
7. Angel generates AI art
8. Tigs drops art into postcard fronts
9. Regenerate PDFs

**Phase 3 -- Print:**

**Print at ISOTTO:**
- Tent card: 1 x A4 portrait, single-side, 160-200gsm
- Postcards: 2 x A4 portrait, duplex short-edge, 160-200gsm
- Total cost: ~3 EUR
- Cut postcards by hand (6mm gap = easy cutting)

10. **Google Review** -- Angel writes a genuine 5-star review
    - Real experience, real words
    - Mention specific dishes/products/people by name
    - This is NOT transactional -- you write it because you mean it

### Visit 2: The Gift (No Strings Mode)

You return as a customer. You order food. You eat.

Then you give the kit:

> "I come here a lot. I do design work. I made this for you because I think your place deserves it. No charge. It's a gift."

**What you hand them:**
- 1 tent card (folded, standing)
- 6 postcards (3 unique designs, 2 of each)
- Show them the QR code works (scan it together)
- Mention you left a Google review

**What you DON'T do:**
- Don't quote prices
- Don't mention "more where that came from"
- Don't leave a business card
- Don't pitch anything
- Don't use the word "service" or "client"

**Let the product speak. Walk away.**

### Visit 3+: They Come to You

If the kit is good (and it will be), one of these happens:

- Owner calls/texts: "Can I get more of those postcards?"
- Owner asks: "Can you do this for my cousin's restaurant?"
- Customer asks the owner: "Where'd you get these cards?"
- Owner puts tent card on counter permanently

**Now the conversation is:**

| They ask | You say |
|----------|---------|
| "Can I get 50 more cards?" | "50 cards is about 17 EUR to print. I can do a custom set for 50 EUR total." |
| "Can you change the design?" | "Of course. What would you like? I can have new ones in a day." |
| "My friend has a restaurant..." | "I'd love to check it out. Where is it?" |
| "Can you do menus too?" | "I just did one for Piccolo Bistrot. Want to see it?" |
| "What about t-shirts?" | "My print partner ISOTTO does shirts, cups, everything. Let's talk." |

---

## THE SCALING PATH

| Stage | What | Revenue per business | Your effort |
|-------|------|---------------------|-------------|
| Gift | 1 tent + 6 cards | 0 (3 EUR cost) | 1 hour build + print |
| First order | 50 postcards | 50 EUR | 30 min customize + print run |
| Seasonal update | New designs | 50-75 EUR | 30 min |
| Menu design | Full A5 bifold menu | 100-200 EUR | 2-3 hours |
| Merch | T-shirts, cups, stickers via ISOTTO | 200+ EUR | Design time |
| Referral | New business from their network | Repeat cycle | Visit 1 again |

**Annual value per restaurant: 200-500+ EUR**

---

## FILE STRUCTURE (Per Business)

```
docs/business/postcards/[business-name]/
    postcard-[name]-TENT.html          # Tent card source
    postcard-[name]-TENT.pdf           # Tent card print-ready
    postcards-[name]-B2B.html          # Postcard set source
    postcards-[name]-B2B.pdf           # Postcard set print-ready
    qr-[name]-google.png               # QR: Google Maps
    qr-[name]-instagram.png            # QR: Instagram (if Level 2+)
    qr-[name]-facebook.png             # QR: Facebook (if Level 2+)
    qr-[name]-whatsapp.png             # QR: WhatsApp (if applicable)
    reference/                          # Screenshots + photos for art direction
        insta-01-description.png
        fb-01-description.png
        angel-01-description.jpg
    nb-art/                             # Nano Banana AI-generated artwork
        nb-[name]-banksy-01.png
        nb-[name]-bauhaus-01.png
        nb-[name]-popart-01.png
```

---

## DESIGN STANDARDS

### Tent Card (B2B)
- A4 portrait, single side
- 50mm top flap + 98.5mm back + 98.5mm front + 50mm bottom flap = 297mm
- Front: business name, theme (IT + EN), Italian flag SVG, quote
- Back: business info, hours, phone, QR code (rotated 180deg)
- SVG tick marks at fold lines (8mm, edges only)
- Color: adapt to business brand
- Template: `postcards/pizza-planet/postcard-pizza-planet-TENT.html`

### Postcards (B2C with B2B branding)
- Format B: 3 per A4, 137.6mm x 93mm, 6mm gaps
- Front: SVG art (no raster images needed for first draft)
- Back: business name (not UFA) as primary brand in header
  - "UFA Collection" as secondary in top-right
  - Unique Italian quote per design + English translation
  - Message lines + address lines + stamp box (mailable)
  - Business QR in footer (not UFA HQ QR)
  - Business address + phone in footer metadata
- 3 unique designs per set, printed twice = 6 cards
- Template: `postcards/pizza-planet/postcards-pizza-planet-B2B.html`

### Design Styles
- **Banksy/Stencil:** Bold silhouettes, drip effects, high contrast
- **Bauhaus:** Geometric forms (circles, triangles), grid lines, primary colors + brand accent
- **Minimalist Quote:** Centered text, subtle flag tints, flame/icon motifs, lots of white space

---

## WHAT MAKES THIS UNFUCKABLE

1. **3 EUR entry cost.** There is no financial risk. You're spending pizza money.
2. **The gift creates obligation.** Not manipulative -- genuine generosity creates genuine reciprocity.
3. **The product IS the pitch.** No deck, no slides, no "let me tell you about my services."
4. **The QR code is measurable.** "Since I put your card on the counter, have you noticed more Google reviews?"
5. **Every card carries the UFA message.** The business gets marketing. The world gets the Unfuckables philosophy. Both win.
6. **ISOTTO scales everything.** Cards today, menus tomorrow, t-shirts next month. Same partner, same pipeline.
7. **The filter is the quality.** You only make cards for businesses you love. That authenticity is what makes the owner trust you.
8. **Referrals are built in.** "My friend has a restaurant" is the most natural sales pipeline on earth.

---

## PRINT SPECS QUICK REFERENCE

| Item | Format | Sides | Paper | ISOTTO cost |
|------|--------|-------|-------|-------------|
| Tent card | A4 portrait | Single | 160-200gsm | ~1 EUR |
| Postcards (3) | A4 portrait | Duplex short-edge | 160-200gsm | ~1 EUR per sheet |
| **Full kit** | **3 x A4** | **Mixed** | **160-200gsm** | **~3 EUR** |

---

## HELIXNET QR TRACKING (Future Build)

**Phase 1 (Now):** QR codes point directly to Google Maps, Instagram, etc. Zero infrastructure needed.

**Phase 2 (When we have 5+ businesses):** QR codes point to HelixNet redirect endpoint.

```
SCAN FLOW:
Customer scans QR on postcard
    → hits helixnet.app/qr/pp-instagram-001
    → HelixNet logs: timestamp, channel, device type, approx location
    → instant redirect to instagram.com/pizzaplanet
    → customer never notices (< 100ms hop)
```

**What the dashboard shows (per business):**

| Metric | What it tells you |
|--------|-------------------|
| Scans per channel | Instagram vs Google vs Facebook -- where do customers actually go? |
| Scans per card design | Banksy outselling Bauhaus? Print more Banksy next round. |
| Scans over time | Did the Christmas postcards drive more traffic than summer ones? |
| Day/time patterns | Customers scan at dinner time? Sunday morning? Tourist season? |
| Total scans per business | Is the kit actually getting used or sitting in a drawer? |

**What you can tell the owner:**

> "In the last month, 47 people scanned your postcards. 28 went to Google (60%), 12 to Instagram (25%), 7 to Facebook (15%). Your Instagram is underperforming -- maybe post more food photos. Your Google reviews went from 45 to 58. That's 13 new reviews from postcards alone."

**That conversation is worth 200 EUR.** The postcards were free. The intelligence is the product.

**No reprinting needed** -- when we switch from direct QR to tracked QR, the redirect URLs stay permanent. We just change what they point to on the server side. Old cards keep working.

**FastAPI endpoint (sketch):**
```python
@app.get("/qr/{business}-{channel}-{card_id}")
async def qr_redirect(business: str, channel: str, card_id: str):
    # Log the scan
    log_scan(business=business, channel=channel, card_id=card_id,
             timestamp=now(), user_agent=request.headers.get("user-agent"))
    # Redirect to actual URL
    target = get_redirect_url(business, channel)
    return RedirectResponse(url=target, status_code=302)
```

---

## CURRENT B2B PIPELINE

| # | Business | Location | UFA Status | Kit Status |
|---|----------|----------|------------|------------|
| 1 | Camper & Tour | Via F. Culcasi 4, Trapani | APPROVED by Nino | Tent card printed |
| 2 | Pizza Planet | Via Asmara 35, Bonagia | DEMO (not visited yet) | Tent + postcards ready |
| 3 | Piccolo Bistrot | Via Garibaldi 43, Trapani | Menu designed | Menu v3 ready |
| 4 | Mixology Trapani | Via M. Buscaino 15, Trapani | PoC draft | Tent card draft |

---

**Document Version:** 2.0 -- Added Business Assessment, QR Channel Strategy, Art Pipeline, Nano Banana Workflow, HelixNet Tracking
**Created:** February 1, 2026
**Author:** HelixNet (Angel + Tigs)
**Related:** SOP-001 (Postcard Print), SOP-003 (PDF Generation), SOP-004 (Restaurant Menu)

*"The postcard is the handshake. The coffee is the close."*
*"3 EUR gets you in the door. The relationship is the business."*
*"RESISTANCE IS NOT FUTILE."*
