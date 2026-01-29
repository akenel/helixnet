# SOP-003: PDF Generation Standards
## Puppeteer (Chrome Headless) Command Reference
### HelixNet Standard Operating Procedure | ISO 9001 Aligned

---

## PURPOSE

Single source of truth for all PDF generation. Copy-paste ready. No guessing.

---

## PRIMARY TOOL

**Puppeteer** - Chrome 144 headless PDF generator

Two scripts available:
- `scripts/postcard-to-pdf.js` -- Cards, postcards, tent cards (NO headers/footers)
- `scripts/sop-to-pdf.js` -- SOPs and documents (WITH headers/footers/page numbers)

---

## STANDARD COMMANDS

### Postcards & Tent Cards (zero margins, no headers)
```bash
node scripts/postcard-to-pdf.js input.html output.pdf
```

### SOPs & Documents (headers, footers, page numbers)
```bash
node scripts/sop-to-pdf.js input.html output.pdf "Document Title" "SOP-001"
```

---

## HOW IT WORKS

The postcard script:
1. Launches Chrome headless (bundled with Puppeteer at `~/.cache/puppeteer/chrome/`)
2. Loads the HTML with `setContent()` and waits for `networkidle0`
3. Calls `page.pdf()` with:
   - `format: 'A4'` (respects `@page` CSS directives for landscape)
   - Zero margins on all sides
   - `printBackground: true` (renders colors, gradients, backgrounds)
   - `displayHeaderFooter: false` (clean output)
4. Closes browser

---

## WHAT CHROME SUPPORTS (everything)

| Feature | Status |
|---------|--------|
| Flexbox | FULL SUPPORT |
| CSS Grid | FULL SUPPORT |
| Gradients (linear, radial, repeating) | FULL SUPPORT |
| Absolute positioning | FULL SUPPORT |
| Float layouts | FULL SUPPORT |
| `@page` size/orientation | FULL SUPPORT |
| `transform: rotate()` | FULL SUPPORT |
| `printBackground` colors | FULL SUPPORT |
| SVG inline | FULL SUPPORT |
| Web fonts (@font-face) | FULL SUPPORT |

---

## VERIFICATION COMMANDS

```bash
# Page count
pdfinfo output.pdf | grep Pages

# File size
ls -lh output.pdf

# Quick view
evince output.pdf
# OR
xdg-open output.pdf
```

---

## BATCH GENERATION

```bash
# All HTML in folder to PDF
for f in *.html; do
  node scripts/postcard-to-pdf.js "$f" "${f%.html}.pdf"
done
```

---

## DEPRECATED TOOLS (UNINSTALLED)

| Tool | Why Removed | Date |
|------|-------------|------|
| **wkhtmltopdf** | Qt WebKit ~2016. Blank second pages, black bars from CSS gradients, broken flexbox. Caused days of debugging. | Jan 29, 2026 |
| **weasyprint** | Chokes on flexbox, floats, gradients, absolute positioning. Never worked properly. | Jan 25, 2026 |

If someone suggests wkhtmltopdf or weasyprint, say: "We use Puppeteer. It's Chrome. It's in the SOP."

---

## TROUBLESHOOTING

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Blank PDF | Page has no content | Check HTML is valid |
| 2 pages instead of 1 | Content exceeds page height | Reduce heights so they sum to page size |
| Images missing | External URL or wrong path | Use relative paths or embed base64 |
| Fonts wrong | Custom font not loaded | Use system fonts or @font-face with local file |

---

## QUICK REFERENCE

```
POSTCARDS/CARDS:  node scripts/postcard-to-pdf.js input.html output.pdf
SOPs/DOCUMENTS:   node scripts/sop-to-pdf.js input.html output.pdf "Title" "SOP-XXX"

Chrome location:  ~/.cache/puppeteer/chrome/linux-144.0.7559.96/chrome-linux64/chrome
Node modules:     /home/angel/repos/helixnet/node_modules/puppeteer/
```

---

**Document Version:** 2.0
**Created:** January 25, 2026
**Revised:** January 29, 2026 -- Migrated from wkhtmltopdf to Puppeteer (Chrome headless)
**Author:** HelixNet

