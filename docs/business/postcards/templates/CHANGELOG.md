# Template Changelog

## v3 (Feb 8, 2026) - CURRENT

- `object-position: top center` on portrait card images (prevents logo/sign clipping)
- Brand color neutral -- set per client via CSS variables or find/replace
- Landscape footer: QR + label side by side (saves vertical space)
- Portrait footer: QR stacked with label below (more vertical room)
- Both: footer border matches brand color (not hardcoded red)
- Short-edge duplex back ordering: B, A, D, C

### Files
- `4UP-PORTRAIT-GOLD.html` - 99mm x 142.5mm cards, A4 portrait
- `4UP-LANDSCAPE-GOLD.html` - 142.5mm x 99mm cards, A4 landscape
- `TENT-CARD-GOLD.html` - A4 tent fold, story back panel

## v2 (Feb 3, 2026)

- 30mm QR on portrait, 24mm on landscape
- Added "Reviews + Directions" sublabel on landscape
- Removed "Your Message" label on landscape (blank space is obvious)
- Footer red top border standardized

## v1 (Jan 26, 2026)

- Initial 4-UP layout created from Pizza Planet prototype
- Card math locked in: 3mm frame, 6mm gaps, fills A4 exactly
- Tent card created: 42mm top tab + 100mm front + 100mm back + 55mm bottom tab

---

*When updating a GOLD template: copy current to arc/ with version suffix, edit the GOLD file, update this changelog.*
