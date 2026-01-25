# SOP-002: Hotel Pitch Package
## Standard Package for Any Hotel
### Tigs Operations | ISO 9001 Aligned

---

## PURPOSE

Create a complete, professional pitch package for any hotel in under 30 minutes. Reusable template. Consistent quality.

---

## PACKAGE CONTENTS

Every hotel pitch package contains these 6 items:

| # | File | Description | Pages |
|---|------|-------------|-------|
| 1 | ufa-menu-brochure.pdf | Menu/pricing for guests | 1 |
| 2 | ufa-wall-display.pdf | Wall display with pocket | 1 |
| 3 | postcard-[hotel]-tent.pdf | Custom tent card for hotel | 1 |
| 4 | labels-seal-sheet.pdf | Seal + corner labels | 1 |
| 5 | postcard-donny-kenel-STANDARD.pdf | Sample postcard 6×4" | 2 (front/back) |
| 6 | postcard-donny-kenel-MAX.pdf | Sample postcard A4 | 2 (front/back) |

**Total: 8 pages across 6 files**

---

## PROCEDURE

### Step 1: Create Hotel Folder
```bash
HOTEL="hotelname"
mkdir -p /home/angel/repos/helixnet/UFA_r2p/${HOTEL}/
```

### Step 2: Copy Standard Files
```bash
# These don't change per hotel
cp /home/angel/repos/helixnet/UFA_r2p/ufa-menu-brochure.pdf \
   /home/angel/repos/helixnet/UFA_r2p/${HOTEL}/

cp /home/angel/repos/helixnet/UFA_r2p/ufa-wall-display.pdf \
   /home/angel/repos/helixnet/UFA_r2p/${HOTEL}/

cp /home/angel/repos/helixnet/UFA_r2p/labels-seal-sheet.pdf \
   /home/angel/repos/helixnet/UFA_r2p/${HOTEL}/

cp /home/angel/repos/helixnet/UFA_r2p/postcard-donny-kenel-STANDARD.pdf \
   /home/angel/repos/helixnet/UFA_r2p/${HOTEL}/

cp /home/angel/repos/helixnet/UFA_r2p/postcard-donny-kenel-MAX.pdf \
   /home/angel/repos/helixnet/UFA_r2p/${HOTEL}/
```

### Step 3: Create Custom Tent Card
1. Copy template:
```bash
cp /home/angel/repos/helixnet/docs/business/postcards/puntatipa/postcard-puntatipa-A4-tent.html \
   /home/angel/repos/helixnet/docs/business/postcards/${HOTEL}/postcard-${HOTEL}-tent.html
```

2. Edit HTML - replace:
   - Hotel name (PUNTATIPA → NEW HOTEL)
   - Room number if applicable
   - Philosophy/tagline
   - Coordinates
   - Colors to match hotel brand

3. Generate PDF (SOP-001)

4. Verify (SOP-001)

5. Copy to package folder

### Step 4: Verify Package
```bash
ls -la /home/angel/repos/helixnet/UFA_r2p/${HOTEL}/
```

**Checklist:**
- [ ] 6 files present
- [ ] All PDFs open correctly
- [ ] Custom tent card has correct hotel name
- [ ] No broken/corrupt files

### Step 5: Prepare Email
Use template from `/docs/business/consulting/templates/hotel-pitch-package/email-template.md`

---

## CUSTOMIZATION OPTIONS

### Tent Card Variations

| Room Type | Front | Back |
|-----------|-------|------|
| Philosophy Room | "Dualism." + definition | Room°XXX | Philosophy |
| Standard Room | Hotel name + tagline | Room info + address lines |
| Suite | Premium design | VIP messaging |

### Color Schemes

| Hotel Style | Primary | Accent | Background |
|-------------|---------|--------|------------|
| Classic | #2C3E50 | #C0392B | #FAF9F6 |
| Modern | #333333 | #4A90A4 | #FFFFFF |
| Luxury | #1A1A1A | #D4AF37 | #F5F5F0 |
| Coastal | #4A90A4 | #D35F5F | #FFFFFF |

---

## TIMELINE

| Task | Time |
|------|------|
| Create folder + copy standard files | 2 min |
| Customize tent card HTML | 10-15 min |
| Generate + verify PDF | 5 min |
| Prepare email | 5 min |
| **Total** | **~25 min** |

---

## OUTPUT LOCATION

```
/home/angel/repos/helixnet/UFA_r2p/
├── [hotel-name]/
│   ├── ufa-menu-brochure.pdf
│   ├── ufa-wall-display.pdf
│   ├── postcard-[hotel]-tent.pdf
│   ├── labels-seal-sheet.pdf
│   ├── postcard-donny-kenel-STANDARD.pdf
│   └── postcard-donny-kenel-MAX.pdf
```

---

## EXAMPLES

| Hotel | Folder | Status |
|-------|--------|--------|
| PuntaTipa | `Rm°205/` | Complete |
| [Next hotel] | `[name]/` | Template ready |

---

**Document Version:** 1.0
**Created:** January 25, 2026
**Author:** Tigs

