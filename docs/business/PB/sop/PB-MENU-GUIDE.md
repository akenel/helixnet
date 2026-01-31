# Piccolo Bistrot - Menu Production Guide

**Client:** Piccolo Bistrot
**Address:** Via Garibaldi 43, Trapani
**Tel:** 379 0147 4191 / 0923 050392
**Tagline:** Crudo & Cocktail
**Brand Color:** Burgundy #6B2D3E
**Google Maps:** https://maps.app.goo.gl/yE4c1MGFtcjTM6As6

---

## Files

| File | Location | Purpose |
|------|----------|---------|
| A5 Bifold HTML | `PB/menu/menu-piccolo-bistrot-A5-bifold.html` | SOURCE - edit this |
| A5 Bifold PDF | `PB/menu/menu-piccolo-bistrot-A5-bifold.pdf` | OUTPUT - print this |
| Print Order | `PB/menu/PRINT-ORDER-PB-MENU.html` | SEND TO ISOTTO - email with PDF attached |
| V1 A4 (archive) | `PB/menu/menu-piccolo-bistrot.html` | Original draft, superseded |
| QR Code | `PB/assets/qr-google-maps.png` | Google Maps QR (burgundy) |
| Photos | `PB/photos/` | 7 reference photos from intake |

---

## How to Print & Fold

**Print specs:** A4 landscape, duplex, short-edge binding, 160-200gsm white paper.

**Fold:** Left side over right side. Cover ("Menu") ends up in front. Done.

```
Flat sheet (side 1 up):
┌──────────┬──────────┐
│  BACK    │  COVER   │
│ (upside  │ (Menu)   │
│  down)   │          │
└──────────┴──────────┘
     ↑ fold here

Result: A5 menu, cover in front, food inside, drinks on back.
```

**How to send to ISOTTO:**
1. Open `PRINT-ORDER-PB-MENU.html` in browser
2. Compose email to ISOTTO
3. Paste or attach the print order HTML
4. Attach `menu-piccolo-bistrot-A5-bifold.pdf`
5. State quantity
6. Done -- no USB stick, no driving

---

## How to Update the Menu

### Price change
1. Open `menu-piccolo-bistrot-A5-bifold.html`
2. Search for the item name (e.g., "Tartare")
3. Change the price in the `item-price` span
4. Regenerate PDF:
   ```bash
   node scripts/postcard-to-pdf.js docs/business/PB/menu/menu-piccolo-bistrot-A5-bifold.html docs/business/PB/menu/menu-piccolo-bistrot-A5-bifold.pdf
   ```
5. Verify: `pdfinfo ... | grep Pages` → must be 2

### Add/remove item
1. Copy an existing `<div class="item">` block
2. Change the Italian name, English translation, and price
3. Regenerate + verify

### Seasonal version (e.g., Summer Menu)
1. Copy `menu-piccolo-bistrot-A5-bifold.html` → `menu-piccolo-bistrot-SUMMER.html`
2. Swap seasonal items (e.g., add gazpacho, remove zuppa di cozze)
3. Regenerate PDF with new filename
4. Keep both versions -- switch at season change

---

## Panel Layout

| Panel | Position | Content |
|-------|----------|---------|
| 1 (Cover) | Page 1, RIGHT | Logo, Menu title, tagline, address, phone, QR |
| 2 (Inside L) | Page 2, LEFT | Antipasti (7), Primi Terra (4) + Mare (5) |
| 3 (Inside R) | Page 2, RIGHT | Secondi Terra (4) + Mare (5), Contorni (5), Insalatona, Taglieri (4), Wines (11) |
| 4 (Back) | Page 1, LEFT (rotated 180°) | Dolci, Bibite, Birra, Colazione, Bar, Coperto, WiFi |

---

## Print Specs

- **Format:** A4 landscape, duplex (front + back)
- **Paper:** 160-200gsm recommended
- **Fold:** Once down the center → 4 panels of A5 (148.5 × 210mm)
- **Print partner:** ISOTTO Sport, Trapani
- **Cost:** ~1 EUR per menu

---

## Menu Items (Complete List as of Jan 31, 2026)

### Antipasti
| Item | EN | Price |
|------|----|-------|
| Antipasto misto (carne o pesce) 120g | Mixed starter (meat or fish) | 21,00 |
| Tartare | Tartare | 15,00 |
| Caponata | Sweet & sour aubergine | 8,00 |
| Insalata di polpo | Octopus salad | 12,00 |
| Crudo di pesce | Raw fish selection | 25,00 |
| Impanata di cozze | Breaded mussels | 11,00 |
| Zuppa di cozze | Mussel soup | 13,00 |

### Primi - Terra
| Item | EN | Price |
|------|----|-------|
| Pesto trapanese | Trapani pesto (tomato, almond, basil) | 9,00 |
| Norma | Aubergine, tomato & ricotta | 9,00 |
| Pomodoro | Tomato sauce | 8,00 |
| Piatto del giorno | Daily special | -- |

### Primi - Mare
| Item | EN | Price |
|------|----|-------|
| Scoglio | Mixed seafood pasta | 20,00 |
| Vongole | Clams | 16,00 |
| Cozze e vongole | Mussels & clams | 18,00 |
| Bottarga | Cured fish roe | 16,00 |
| Piatto del giorno | Daily special | 15,00 |

### Secondi - Terra
| Item | EN | Price |
|------|----|-------|
| Entrecote grill | Grilled rib-eye | 22,00 |
| Cotoletta pollo / vitello | Chicken or veal cutlet | 12,00 |
| Tagliata argentina grill 300g | Grilled Argentine steak, sliced | 28,00 |
| Pollo al limone | Lemon chicken | 13,00 |

### Secondi - Mare
| Item | EN | Price |
|------|----|-------|
| Calamaro grill o fritto | Grilled or fried squid | 15,00 |
| Polpo grill o fritto | Grilled or fried octopus | 13,00 |
| Spada grill | Grilled swordfish | 16,00 |
| Tonno grill | Grilled tuna | 18,00 |
| Pescato al Kg | Catch of the day (per kg) | 60,00 |

### Contorni
| Item | EN | Price |
|------|----|-------|
| Insalata verde | Green salad | 4,00 |
| Insalata mista | Mixed salad | 5,00 |
| Patate fritte | French fries | 5,00 |
| Patate al forno | Roasted potatoes | 5,00 |
| Insalata rustica | Fennel, orange & spring onion | 6,00 |
| Insalata arancia | Orange salad | 7,00 |

### Insalatona
| Item | EN | Price |
|------|----|-------|
| Lattuga, cipolla, capperi, pomodoro, acciughe, cipolla rossa | Large salad | 11,00 |

### Taglieri
| Item | EN | Price |
|------|----|-------|
| Affettati e formaggi | Cured meats & cheeses | 15,00 |
| Prodotti di tonnara | Tuna specialties | 8,00 |
| Bruschetta pate assortiti | Assorted pate bruschetta | 7,50 |
| Crudo di pesce | Raw fish selection | 6,50 |

### Vini Bianchi
| Winery | Varietals | Price |
|--------|----------|-------|
| Cantina Mothia | Viola Latina / Mosaikon Grillo | 12-12,50 |
| Iuppa | Etna Bianco / Lavi | 39,00 |
| Mustazza | Catarratto / Grillo / Zibibbo | 24,00 |
| Baglio Oro | Grecanico / Rosato / Frizzante | 18-19 |
| Castelluccio Miano | Miano / Sampieri Frizzante | 27-28 |
| Cellaro | Chardonnay / Rosato / Spumante | 21-24 |

### Vini Rossi
| Winery | Varietals | Price |
|--------|----------|-------|
| Mustazza | Merlot / Cabernet Sauvignon | 27,00 |
| Iuppa | Cio Etna Rosso | 39,00 |
| Baglio Oro | Sciute Frappato | 22,00 |
| Castelluccio Miano | Perricone | 30,00 |
| Cellaro | Luma Nero d'Avola | 21,00 |

### Dolci, Bibite, Birra, Bar, Colazione
*(See back panel in HTML -- full list in the bifold source)*

### Coperto
2,00 EUR per person

### WiFi
FASTWEB-31E44F / Password: 2emP6CpakhkR

---

## Revision History

| Date | Change | By |
|------|--------|----|
| Jan 31, 2026 | V1 A4 4-page draft | Tig |
| Jan 31, 2026 | V2 A5 bifold, SVG logo, Google Maps QR | Tig |

---

*General methodology: see `docs/business/consulting/HelixNet-SOP/SOP-004-restaurant-menu.md`*
