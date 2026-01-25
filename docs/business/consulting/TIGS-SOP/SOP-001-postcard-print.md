# SOP-001: Postcard Print Workflow
## From HTML to Print-Ready PDF
### Tigs Operations | ISO 9001 Aligned

---

## PURPOSE

Convert HTML postcard designs to print-ready PDFs. Every time. Same quality. No surprises.

---

## TOOLS

| Tool | Use | Status |
|------|-----|--------|
| wkhtmltopdf | HTML → PDF conversion | PRIMARY |
| weasyprint | DO NOT USE | DEPRECATED |
| Browser Print | Fallback only | BACKUP |

---

## FILE LOCATIONS

```
SOURCE (edit here):
/home/angel/repos/helixnet/docs/business/postcards/
├── donny/                    # Donny Kenel designs
├── puntatipa/                # PuntaTipa hotel designs
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
| Postcard Standard | 6in × 4in (152mm × 102mm) | Landscape |
| Postcard BOXFIT | 140mm × 95mm | Landscape |
| Postcard A4 Tent | A4 (297mm × 210mm) | Landscape |
| Menu/Brochure | A4 (210mm × 297mm) | Portrait |
| Wall Display | A4 (210mm × 297mm) | Portrait |
| Labels Sheet | A4 (210mm × 297mm) | Portrait |

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
# A4 Portrait (menu, wall display, labels)
wkhtmltopdf --page-size A4 \
  --margin-top 0 --margin-bottom 0 \
  --margin-left 0 --margin-right 0 \
  input.html output.pdf

# A4 Landscape (tent cards)
wkhtmltopdf --page-size A4 --orientation Landscape \
  --margin-top 0 --margin-bottom 0 \
  --margin-left 0 --margin-right 0 \
  input.html output.pdf

# Custom size (postcards)
wkhtmltopdf --page-width 152mm --page-height 102mm \
  --margin-top 0 --margin-bottom 0 \
  --margin-left 0 --margin-right 0 \
  input.html output.pdf
```

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

## COMMON FIXES

| Problem | Cause | Fix |
|---------|-------|-----|
| 2 pages instead of 1 | Content too big | Reduce padding/margins/font |
| Blank second page | Extra whitespace | Check body/page height in CSS |
| Empty gaps | Flexbox issues | Use table-based layout |
| Text collision | Absolute positioning | Use normal document flow |
| Images missing | Wrong path | Use absolute paths or embed base64 |

---

## CSS THAT WORKS

```css
/* Page setup */
@page {
    size: A4 portrait;
    margin: 0;
}

/* Use tables, not flexbox */
table { width: 100%; border-collapse: collapse; }

/* Fixed heights that add up to page height */
.header { height: 50mm; }
.content { height: 200mm; }
.footer { height: 47mm; }
/* Total: 297mm = A4 height */
```

---

## CSS THAT BREAKS

```css
/* AVOID THESE */
display: flex;           /* Unreliable in PDF */
position: absolute;      /* Causes collisions */
float: left/right;       /* Unpredictable */
background: linear-gradient(); /* May not render */
```

---

## NEVER

- Never say "fixed" without opening the PDF
- Never say "1 page" without checking page count
- Never blame the tool - own the HTML
- Never skip verification

---

**Document Version:** 1.0
**Created:** January 25, 2026
**Author:** Tigs

