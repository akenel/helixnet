---
kb_id: HelixPOS_KB-041
title: UNBOXING Workflow - New Product Arrival Documentation
domain: headshop-retail
language: en
contributor: Pam (Artemis Headshop - Front of House)
category: operations
status: approved
version: 1.0.0
created: 2025-12-03
last_updated: 2025-12-03
applies_to: [helix-pos, artemis-headshop]
vat_critical: false
compliance_level: medium
related_products: [GRINDER-BRUCE-FLOW, GRINDER-BRUCE-DRAGON, GRINDER-BRUCE-MASTER]
points: 5
---

# HelixPOS_KB-041: UNBOXING Workflow - New Product Arrival Documentation

**The 2-Minute UNBOX Protocol for Returns-Ready Documentation**

---

## Purpose

This KB teaches staff how to:
- Document new product arrivals with video
- Create returns-ready reboxing documentation
- Quick edit for social media (Flixer clips)
- Link MP4s to product KB entries
- Enter pricing, cost, min/max stock, and reorder leads

**Target:** Pam, Leandra, any staff receiving shipments

---

## The 2-Minute UNBOXING Protocol

### BEFORE YOU START

```
CHECKLIST:
[ ] Phone charged (50%+ battery)
[ ] Clean work surface (back area)
[ ] Good lighting (natural preferred)
[ ] Box cutter ready
[ ] Packing list from supplier
[ ] HelixPOS open on tablet
```

---

### STEP 1: Pre-Recording Setup (30 seconds)

```
1. Place sealed box on clean surface
2. Position phone/camera (landscape mode!)
3. Have packing list visible in frame
4. Check audio is on (important for narration)
5. Start recording BEFORE touching box
```

**Pam's Tip:**
> "I always say the date and product name first: 'December 3rd, Bruce Lee Grinder Collection arrival.' Makes finding clips easier later."

---

### STEP 2: The UNBOX (60 seconds)

```
RECORD CONTINUOUSLY - DO NOT STOP

1. Show sealed box (all sides, labels visible)
2. Cut tape cleanly (not the box!)
3. Open flaps, show contents arrangement
4. Remove items ONE BY ONE:
   - Show each item to camera
   - Check for damage (verbalize: "No damage")
   - Show serial numbers if applicable
   - Count: "Item 1 of 12... Item 2 of 12..."
5. Show all packaging materials (for reboxing)
6. Final shot: All items laid out together
```

**Critical for Returns:**
> Keep ALL original packaging. Customers return items, we need EXACT reboxing. The video shows how it was packed.

---

### STEP 3: Quick Quality Check (20 seconds)

```
While still recording:
1. "Quality check - Item 1..."
2. Open one sample unit (if testing approved)
3. Show key features working
4. "All items verified, shipment complete."
5. STOP recording
```

---

### STEP 4: Post-Recording Admin (10 seconds)

```
1. Save video with naming convention:
   UNBOX_[DATE]_[PRODUCT-SKU]_[SUPPLIER].mp4
   Example: UNBOX_2025-12-03_GRINDER-BRUCE-FLOW_SylKen.mp4

2. Upload to designated folder (MinIO/shared drive)

3. Note the MP4 link for KB entry
```

---

## HelixPOS Data Entry

### After UNBOXING, enter in system:

```
PRODUCT CARD:
├── SKU: [from packing list]
├── Name: [full product name]
├── Price (retail): [from Felix/pricing sheet]
├── Cost (wholesale): [from invoice]
├── Stock Qty: [counted from unbox]
├── Min Stock: [reorder trigger - usually 20% of order]
├── Max Stock: [storage limit]
├── Supplier: [company name]
├── Lead Time: [days to reorder]
├── Vending Slot: [if applicable]
├── Category: [Grinders, Lighters, etc.]
└── KB Link: [MP4 URL]
```

---

## Bruce Lee Grinder Arrival - Example Entry

### Pam's Entry for Today's Shipment:

```
╔══════════════════════════════════════════════════════════════════╗
║ UNBOXING RECORD: Bruce Lee Signature Collection                  ║
║ Date: 2025-12-03 | Received by: Pam                             ║
╠══════════════════════════════════════════════════════════════════╣
║ ITEM 1: Bruce Lee Flow Grinder - Limited Edition                ║
├──────────────────────────────────────────────────────────────────┤
│ SKU: GRINDER-BRUCE-FLOW                                         │
│ Qty Received: 12 units                                          │
│ Retail Price: CHF 120.00                                        │
│ Wholesale Cost: CHF 65.00                                       │
│ Margin: 46%                                                     │
│ Min Stock: 3 | Max Stock: 20                                    │
│ Supplier: SylKen | Lead Time: 14 days                           │
│ Vending: YES - Slot #16                                         │
│ Condition: All perfect, no damage                               │
│ Serial Numbers: BLF-001 through BLF-012                         │
│ MP4: /unbox/UNBOX_2025-12-03_GRINDER-BRUCE-FLOW.mp4            │
╠══════════════════════════════════════════════════════════════════╣
║ ITEM 2: Bruce Lee Dragon Grinder - Collectors Edition           ║
├──────────────────────────────────────────────────────────────────┤
│ SKU: GRINDER-BRUCE-DRAGON                                       │
│ Qty Received: 6 units                                           │
│ Retail Price: CHF 180.00                                        │
│ Wholesale Cost: CHF 95.00                                       │
│ Margin: 47%                                                     │
│ Min Stock: 2 | Max Stock: 10                                    │
│ Supplier: SylKen | Lead Time: 21 days                           │
│ Vending: NO - Display case only (Ralph installing)              │
│ Display Location: TT Section (Top Tier)                         │
│ Condition: All perfect, display boxes intact                    │
│ Serial Numbers: BLD-001 through BLD-006                         │
│ MP4: /unbox/UNBOX_2025-12-03_GRINDER-BRUCE-DRAGON.mp4          │
╠══════════════════════════════════════════════════════════════════╣
║ ITEM 3: Bruce Lee Master Grinder - Museum Grade                 ║
├──────────────────────────────────────────────────────────────────┤
│ SKU: GRINDER-BRUCE-MASTER                                       │
│ Qty Received: 3 units                                           │
│ Retail Price: CHF 350.00                                        │
│ Wholesale Cost: CHF 180.00                                      │
│ Margin: 49%                                                     │
│ Min Stock: 1 | Max Stock: 5                                     │
│ Supplier: SylKen | Lead Time: 30 days (custom order)            │
│ Vending: NO - Locked display + Felix approval required          │
│ Display Location: TT Section - Glass case                       │
│ Condition: Museum grade, velvet cases pristine                  │
│ Serial Numbers: BLM-001, BLM-002, BLM-003                       │
│ Certificates: Included and verified                             │
│ MP4: /unbox/UNBOX_2025-12-03_GRINDER-BRUCE-MASTER.mp4          │
╚══════════════════════════════════════════════════════════════════╝
```

---

## Accessory Pairing (Upsell Setup)

### For Bruce Lee Grinders, configure these pairings:

| Grinder | Included Free | Suggested Upsell |
|---------|---------------|------------------|
| Bruce Flow (CHF 120) | CLEAN-KIT-C (CHF 3.50) | CLEAN-KIT-B (CHF 9.00) |
| Bruce Dragon (CHF 180) | CLEAN-KIT-B (CHF 9.00) | CLEAN-KIT-A (CHF 20.00) |
| Bruce Master (CHF 350) | CLEAN-KIT-A (CHF 20.00) | Custom care package |

**All include:** GIFT-ARTEMIS-POUCH (complimentary)

---

## Reboxing Protocol (For Returns)

### When customer returns, reference UNBOX video:

```
REBOXING CHECKLIST:
[ ] Watch original UNBOX MP4
[ ] Verify all components present
[ ] Match packing arrangement from video
[ ] Check serial number matches
[ ] Note any damage (new vs. original)
[ ] Re-seal appropriately
[ ] Update stock in HelixPOS
[ ] Flag for Felix if damage dispute
```

---

## Quick Edit for Social (Flixer Clips)

### 10-20 minute edit workflow:

```
1. Import MP4 to Flixer/CapCut
2. Cut to highlights (15-30 seconds max)
3. Add text overlays:
   - Product name
   - "NEW ARRIVAL"
   - Price (optional)
4. Add Artemis logo bumper
5. Export for Instagram/TikTok
6. Schedule post (Felix approves first)
```

**Best times to post:**
- Tuesday 6pm
- Thursday 6pm
- Saturday 11am

---

## Black Friday Special Note

### For George Clooney / Bruce Lee Collection Event:

```
FRIDAY BLACK SPECIAL - Preparation:
[ ] All Bruce grinders in TT display
[ ] Vending Slot #16 loaded (Flow model)
[ ] Demo unit available for testing
[ ] UNBOX videos ready for social push
[ ] George Clooney possibly attending (afternoon)
[ ] Felix and Bruce Lee promo materials ready
```

---

## Related KBs

- **HelixPOS_KB-040:** Zippo Maintenance Guide
- **HelixPOS_KB-002:** Storz & Bickel (high-ticket sales)
- **HelixPOS_KB-030:** High-Ticket Demo Sales

---

## KB Contribution

This KB was created by Pam during the Bruce Lee Grinder Collection arrival.

**To update or contribute:**
1. Email: `kb@helixnet.local`
2. Subject: `UPDATE HelixPOS_KB-041 - [Your Change]`
3. Credit: +2 points for approved updates

---

## Changelog

- **2025-12-03 (v1.0.0):** Initial creation during George Clooney visit. Bruce Lee Collection arrived.

---

**End of HelixPOS_KB-041**
