# SOP-003: PDF Generation Standards
## wkhtmltopdf Command Reference
### HelixNet Standard Operating Procedure | ISO 9001 Aligned

---

## PURPOSE

Single source of truth for all PDF generation commands. Copy-paste ready. No guessing.

---

## PRIMARY TOOL

**wkhtmltopdf** - WebKit-based HTML to PDF converter

```bash
# Check installation
wkhtmltopdf --version
```

---

## STANDARD COMMANDS

### A4 Portrait (Menus, Displays, Labels)
```bash
wkhtmltopdf \
  --page-size A4 \
  --orientation Portrait \
  --margin-top 0 \
  --margin-bottom 0 \
  --margin-left 0 \
  --margin-right 0 \
  --enable-local-file-access \
  input.html output.pdf
```

### A4 Landscape (Tent Cards)
```bash
wkhtmltopdf \
  --page-size A4 \
  --orientation Landscape \
  --margin-top 0 \
  --margin-bottom 0 \
  --margin-left 0 \
  --margin-right 0 \
  --enable-local-file-access \
  input.html output.pdf
```

### 6×4 Inch Postcard
```bash
wkhtmltopdf \
  --page-width 152mm \
  --page-height 102mm \
  --margin-top 0 \
  --margin-bottom 0 \
  --margin-left 0 \
  --margin-right 0 \
  --enable-local-file-access \
  input.html output.pdf
```

### BOXFIT Postcard (140×95mm)
```bash
wkhtmltopdf \
  --page-width 140mm \
  --page-height 95mm \
  --margin-top 0 \
  --margin-bottom 0 \
  --margin-left 0 \
  --margin-right 0 \
  --enable-local-file-access \
  input.html output.pdf
```

---

## USEFUL FLAGS

| Flag | Purpose |
|------|---------|
| `--enable-local-file-access` | Allow loading local images |
| `--javascript-delay 1000` | Wait for JS to render (ms) |
| `--no-stop-slow-scripts` | Don't timeout on slow JS |
| `--print-media-type` | Use @media print styles |
| `--dpi 300` | Higher quality output |
| `--image-quality 100` | Max image quality |
| `--disable-smart-shrinking` | Don't auto-shrink content |

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

# Check for errors in generation
wkhtmltopdf ... 2>&1 | grep -i error
```

---

## BATCH GENERATION

```bash
# All HTML in folder to PDF
for f in *.html; do
  wkhtmltopdf --page-size A4 \
    --margin-top 0 --margin-bottom 0 \
    --margin-left 0 --margin-right 0 \
    "$f" "${f%.html}.pdf"
done
```

---

## DEPRECATED TOOL

**weasyprint** - DO NOT USE

Why:
- Chokes on flexbox
- Breaks on float layouts
- Fails on absolute positioning
- Can't handle CSS gradients
- Wasted hours debugging

If someone suggests weasyprint, say: "We use wkhtmltopdf. It's in the SOP."

---

## TROUBLESHOOTING

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Blank PDF | JS not rendered | Add `--javascript-delay 1000` |
| Images missing | Local file access | Add `--enable-local-file-access` |
| Content cut off | Page size mismatch | Check `@page` CSS matches command |
| Blurry images | Low DPI | Add `--dpi 300` |
| 2 pages instead of 1 | Content overflow | Reduce margins/padding in HTML |
| Fonts wrong | Font not installed | Use web-safe fonts or embed |

---

## QUICK REFERENCE CARD

```
A4 PORTRAIT:  --page-size A4 --orientation Portrait
A4 LANDSCAPE: --page-size A4 --orientation Landscape
6×4 POSTCARD: --page-width 152mm --page-height 102mm
BOXFIT:       --page-width 140mm --page-height 95mm

ALL COMMANDS ADD:
  --margin-top 0 --margin-bottom 0
  --margin-left 0 --margin-right 0
  --enable-local-file-access
```

---

**Document Version:** 1.0
**Created:** January 25, 2026
**Author:** HelixNet

