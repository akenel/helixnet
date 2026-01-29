# SOP-001: Postcard Print Workflow
## From HTML to Print-Ready PDF
### HelixNet Standard Operating Procedure | ISO 9001 Aligned

---

## PURPOSE

Convert HTML postcard designs to print-ready PDFs. Every time. Same quality. No surprises.

---

## TOOLS

| Tool | Use | Status |
|------|-----|--------|
| Puppeteer (Chrome headless) | HTML to PDF conversion | PRIMARY + ONLY |
| Browser Print (Ctrl+P) | Fallback only | BACKUP |

---

## FILE LOCATIONS

```
SOURCE (edit here):
/home/angel/repos/helixnet/docs/business/postcards/
├── donny/                    # Donny Kenel designs
├── puntatipa/                # PuntaTipa hotel designs
├── camperandtour/            # Camper & Tour designs
├── colorclean/               # Color Clean designs
├── ufa-menu-brochure.html
├── ufa-wall-display.html
└── ufa-order-form.html

OUTPUT (grab for print):
/home/angel/repos/helixnet/UFA_r2p/
├── Rm°205/                   # Hotel pitch packages
└── *.pdf                     # All print-ready files
```

---

## STANDARD SIZES

| Product | Size | Orientation |
|---------|------|-------------|
| Postcard Standard | 6in x 4in (152mm x 102mm) | Landscape |
| Postcard BOXFIT | 140mm x 95mm | Landscape |
| Postcard A4 Tent | A4 (297mm x 210mm) | Landscape |
| Menu/Brochure | A4 (210mm x 297mm) | Portrait |
| Wall Display | A4 (210mm x 297mm) | Portrait |
| Labels Sheet | A4 (210mm x 297mm) | Portrait |

---

## PROCEDURE

### Step 1: Verify HTML
```bash
# Open in browser first
firefox /path/to/postcard.html
```
- Check layout looks correct
- Check no overflow/collision
- Check text readable

### Step 2: Generate PDF
```bash
node scripts/postcard-to-pdf.js input.html output.pdf
```

That's it. One command. Chrome handles orientation from the HTML's `@page` CSS.

### Step 3: VERIFY (Critical)
```bash
# Check page count
pdfinfo output.pdf | grep Pages

# Open and visually inspect
evince output.pdf
# OR
xdg-open output.pdf
```

**Verification Checklist:**
- [ ] Correct number of pages (1-pager = 1 page, not 2)
- [ ] No blank pages
- [ ] No content overflow
- [ ] No empty gaps in middle
- [ ] Text readable
- [ ] Images display correctly
- [ ] Colors and backgrounds rendered

### Step 4: Move to Output
```bash
cp output.pdf /home/angel/repos/helixnet/UFA_r2p/
```

---

## WHAT "1-PAGER" MEANS

1. **Exactly 1 page** when printed
2. **Content fills the page** - no huge empty gaps
3. **No overflow** - nothing spills to page 2
4. **Print-ready** - open, print, done

**If any of these fail, it is NOT fixed. Go back to Step 1.**

---

## CSS THAT WORKS (everything with Chrome)

```css
/* Page setup */
@page {
    size: A4 landscape;  /* Chrome respects this */
    margin: 0;
}

/* All modern CSS works */
display: flex;                    /* WORKS */
display: grid;                    /* WORKS */
position: absolute;               /* WORKS */
background: linear-gradient();    /* WORKS */
background: repeating-linear-gradient();  /* WORKS */
transform: rotate(180deg);       /* WORKS */
```

Fixed heights should still add up to page height for predictable layouts:
```css
/* A4 landscape = 210mm height */
.tab-top { height: 15mm; }
.front { height: 90mm; }
.back { height: 90mm; }
.tab-bottom { height: 15mm; }
/* Total: 210mm */
```

---

## COMMON FIXES

| Problem | Cause | Fix |
|---------|-------|-----|
| 2 pages instead of 1 | Content exceeds page size | Heights must sum to page height |
| Blank second page | Extra whitespace/margin | Add `overflow: hidden` to body |
| Images missing | Wrong path | Use relative paths from HTML location |
| Text collision | Layout error | Check your CSS, Chrome renders it faithfully |

---

## NEVER

- Never say "fixed" without opening the PDF
- Never say "1 page" without checking page count
- Never blame the tool -- Chrome renders faithfully, own the HTML
- Never skip verification
- Never use wkhtmltopdf or weasyprint (uninstalled)

---

**Document Version:** 2.0
**Created:** January 25, 2026
**Revised:** January 29, 2026 -- Migrated from wkhtmltopdf to Puppeteer (Chrome headless)
**Author:** HelixNet

