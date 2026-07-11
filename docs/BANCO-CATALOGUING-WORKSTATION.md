# Banco — The Cataloguing Workstation
### 2026-07-11 · the rig + the method for getting ~2,000 items in, properly

> **The job:** take Felix's shop from "a pile of stock" to a clean master-data repository —
> every item with a name, a price, a category, a photo, a description, a class (18+ or not),
> and a barcode that a gun can read. ~2,000 items. This doc is the *rig*, the *method*, and
> the *one piece of software that doesn't exist yet*.

**Companion docs:** [BANCO-HARDWARE-KIT-MATRIX.md](BANCO-HARDWARE-KIT-MATRIX.md) (what to buy, and
the backup for every part) · [BANCO-ENRICHMENT-BACKLOG.md](BANCO-ENRICHMENT-BACKLOG.md) (pull-from-Artemis
and friends) · [BANCO-BL97-HOUSE-SCAN-SHEET.md](BANCO-BL97-HOUSE-SCAN-SHEET.md) (the no-barcode items).

---

## 0. The doctrine (read this before building anything)

### The binder is an OUTPUT of the database, never an INPUT to it

The tempting idea: as you label each item, file a copy of the label in a ring binder, tabbed by
category — bongs, trays, CBD — so the shop has a physical catalogue that grows as you go.

**Don't.** A hand-assembled binder is a *second source of truth*. The day a price changes, an item
is discontinued, or a supplier swaps a SKU, the binder is wrong — and nobody will ever re-file 2,000
pages to fix it. You'd spend the whole migration building an artifact that starts rotting on day one.

The instinct underneath it is correct, though. It's **three different needs wearing one coat**:

| The need | The wrong answer | The right answer |
|---|---|---|
| *"Which items are done?"* | Count pages in the binder | A **query**. The Enrichment Queue screen (§3) — always true, never stale. |
| *"A physical book on the counter"* | Hand-file 2,000 labels | **Generate it.** `scripts/generate_catalog.py` already exists. Print it Friday, bin it, print a fresh one next Friday. |
| *"Ring up the stuff with no barcode"* | Flip through a binder | **BL-97 House Scan Sheet** — a small, genuinely-physical, genuinely-durable subset. |

> **The rule:** anything paper is a *render* of the DB at a moment in time. It is disposable by design.
> If a piece of paper ever becomes the thing you trust more than Banco, the migration has failed.

The one exception that earns its paper: **items with no EAN**. They need a house barcode and a
physical, scannable reference so a cashier can actually ring them up. That's BL-97, it's a small
subset, and it too is generated — not hand-assembled.

### The phone is the camera

Do not buy a webcam. A CHF 40 webcam is meaningfully worse than the phone already in your pocket,
and the **Snap-&-fill photo→product flow is already LIVE and mobile-camera-tested in prod** (2026-07-06).
The "camera rig" is therefore not software — it's a *jig* that holds the phone still so the pictures
come out consistent. See §2.

### Batch of 10–20, in-tray → out-tray

Work in physical batches. Twenty items on the bench, worked over, marked done, off the bench. This
is what makes throughput measurable (min/100) and what makes the Enrichment Queue's counter mean
something. Never have "some items, somewhere, partly done."

---

## 1. Build list (BOM)

| # | Part | Pick | ~CHF | Why / notes |
|---|------|------|------|-------------|
| 1 | **Screen** | Big-screen laptop (the salvaged ProBook) | — | Already have. Phone is a *fallback for a sale*, **never** for bulk migration. |
| 2 | **Barcode gun (workhorse)** | **Zebra DS2208-SR — WIRED USB, 1D+2D** | ~88 | See §1.1. **Must be the kit WITH the cable.** |
| 3 | **Gun (roaming / stock counts)** | Inateck Bluetooth 1D+2D, stand included | ~39 | Optional-but-useful. Cordless is the *right* tool for walking shelves (BL-97, receiving). **Not** the till gun — see §1.1. |
| 4 | **Label printer** | **Brother QL-820NWB** | ~200 | Already the decided pick. WiFi/USB, Debian-friendly via `brother_ql`. |
| 5 | **Labels** | Brother DK **removable** rolls + spares | ~30/roll | **Removable adhesive is a hard requirement** — must peel clean off merchandise. |
| 6 | **Phone mount** | Gooseneck / copy-stand clamp | ~20 | Holds the phone steady above the item. The whole "photo booth." |
| 7 | **Lightbox** | Cheap foldable LED cube, or a sheet of white A2 + a desk lamp | 0–40 | Consistent white background = consistent product shots. Start with paper. |
| 8 | **Trays** | In-tray / out-tray (any two boxes) | ~0 | The batch discipline made physical. |
| 9 | **Power** | Counter power strip + spare cables | ~20 | |

**Case:** shoebox for now. Build the leather case (Sylvie) **after** the workflow has survived a few
hundred items and you know what it actually has to hold. Don't tailor a case to a guess.

### 1.1 The scanner decision — reconciled

There are two entries on record and they need squaring:

- Worklist **2026-07-06** says *"Scanner DECIDED: Zebra DS8178 (`DS8178-SR7U2100PFW`)"* — the premium **cordless** gun.
- **HARDWARE-KIT-MATRIX (2026-07-10, newer)** says: *primary = **cheap wedge scanner ~CHF 80**, upgrade to
  DS8178 **only if** tiny codes fail.*

**The matrix is newer and it wins.** The **Zebra DS2208-SR at ~CHF 88, wired USB** lands exactly in the
matrix's "cheap wedge" primary slot — same Zebra build quality, keyboard-wedge, no battery. DS8178 stays
where the matrix put it: the **upgrade path if the acceptance bar fails** (gun must read ~99% of our own
printed labels; 1-in-10 misses = escalate).

**Three hard notes on the DS2208:**

1. **⚠️ THE CABLE.** Two Digitec reviewers report the listing shipping **with no cable** — and a Zebra cable
   is ~CHF 30. The scanner-only SKU (`DS2208-SR00007ZZWW`) is a brick; you want the **USB kit**
   (`DS2208-SR7U2100AZW`). Check the "additional offers" on the product page for one that lists a cable in
   the box. **Verify before ordering.**
2. **⚠️ Swiss QR-bill: probably NOT supported.** A reviewer reports it can't read Swiss QR (the QR-bill puts a
   Swiss cross in the middle, which technically breaks the QR spec). **Irrelevant for the till** — we scan
   product codes and phone screens, not invoices. But if scanning supplier QR-bills into Banco ever becomes a
   want, this gun won't do it, and Datalogic/Honeywell are the brands that advertise Swiss QR support.
3. **1D is not enough — this is why the cheap CHF 64 LS2208 was rejected.** A 1D laser **cannot read a barcode
   off a phone screen** (it needs ink-on-paper contrast; backlit glass defeats it). The moment a member shows a
   loyalty code or voucher on their phone, a 1D gun is a paperweight. 2D imager is non-negotiable. It also gets
   us QR/DataMatrix and omnidirectional reading (no lining up the laser line — real seconds saved per item).

**Why wired for the till, Bluetooth for the floor.** A USB gun is a keyboard: plug it in, it types the barcode,
nothing a cashier can break. Bluetooth adds three failure modes that all land on Felix at the worst moment —
battery dies mid-shift, pairing drops after a reboot and the cashier can't fix it, and BT HID can drop
characters (a *partial* EAN is worse than a clean failure: Banco either says "not found" or matches the wrong
item). Cordless is genuinely right for **walking the shelves** — stock counts, goods-in, BL-97. Different job,
different tool.

---

## 2. The workstation, physically

```
        [ phone on gooseneck ]
                 |
                 v
   ┌───────────────────────────┐
   │   lightbox / white sheet  │   <- item sits here, shot from above
   └───────────────────────────┘
   [IN-TRAY]  → work the item →  [OUT-TRAY]
        laptop (Banco)  ·  DS2208 on stand  ·  QL-820NWB
```

**The loop, per item:**

1. **Scan** the EAN with the gun. Banco looks it up.
   - **Hit** → prefill from reference/supplier data. Confirm, adjust, done.
   - **Miss** → it's an enrichment item. Continue.
2. **Photo** — item under the phone, Snap-&-fill does the rest (already live).
3. **Describe** — pull from the web / Artemis where possible (see ENRICHMENT-BACKLOG §1 — by-URL
   pull is proven), voice-dictate otherwise (mic dictation works, field-tested).
4. **Classify** — category + 18+ class. *The classifier decides 18+ at enrich time, not by hand* —
   see `catalog_taxonomy.classify`. Verify, don't re-key.
5. **Price** + cost.
6. **Label** → print (§3). **No EAN? → the label carries a house Code128** and the item joins BL-97.
7. **Out-tray.** The Enrichment Queue counter ticks.

---

## 3. Labels: sizes × flags, NOT twelve templates

The temptation is to hand-draw ~12 label templates ("one for bongs, one for trays, one for the box…").
**Don't.** Twelve templates is twelve things to maintain, and they will diverge.

What we actually have is a small number of **physical sizes** crossed with a handful of **content flags**.
That's a matrix, and it's **one renderer reading data** — the same instinct already applied to vertical
packs and recipes: *the layout is data, not code*.

### The sizes (3)

| Size | Roughly | Job | Roll |
|------|---------|-----|------|
| **S** | ~29 × 62mm | Price sticker on the item itself | DK-11209 / continuous |
| **M** | ~62 × 37mm | Shelf-talker / bin label | DK-22205 (what `generate_label.py` targets today) |
| **L** | ~62 × 100mm | Box / display card — photo + description + name | DK-11202 / continuous |

### The flags (content, independent of size)

| Flag | Effect |
|------|--------|
| `show_price` | Print the price. **Off** for a pure stock/bin label (a label with no price never goes stale). |
| `show_photo` | Print the product thumbnail (L mainly). |
| `show_barcode` | Print the scannable code. **Always on** for anything a gun must read. |
| `show_human_code` | Print the code as **human-readable digits** beside the bars. **Always on** — a failed scan is then never a dead end; the cashier types it. |
| `show_age` | Print the 🔞 mark. **Driven by `product_class`, never hand-set.** |
| `show_unit` | Print weight/volume (3.5g, 500ml…). |
| `show_desc` | Print the short description (L only). |

**So "the big label with a picture and a description that goes on a box" is not a template** — it's
`size=L, show_photo=1, show_desc=1, show_price=0`. And "the counter card with a price" is
`size=L, show_photo=1, show_price=1`. Nothing new to build per variant.

### What exists vs. what's needed

- ✅ **`scripts/generate_label.py`** — v1. Barcode (EAN-13 → Code128 fallback) + title + price, 62mm,
  SVG → HTML → Puppeteer PDF, mono black for scan reliability. **The bones are right.**
- ▶ **Needed:** widen it to take `size` (S/M/L) + the flags above, driven from product data.
  → **BL-99** (§5).
- ✅ **`scripts/generate_catalog.py`** — the paper catalogue generator (photo + title + badges + price
  + description, A4 card grid → PDF). **This is the binder, and it already exists.** Point it at a
  category, print, done.

> **Note the ⚠️:** `generate_label.py` currently derives EAN-13 from a 12/13-digit numeric and falls back
> to Code128 for anything else. That's exactly right for house-printed codes. Keep it.

---

## 4. The Easy Barcode principle (why the cheap gun is fine)

We **print our own barcodes**, so we read *our own* codes ~100%. The gun only has to cope with
supplier codes as a convenience. That's why the matrix buys the gun cheap and the *printer* solid —
and why the acceptance bar is measured against **our** labels, not against the worst code in the shop.

**A failed scan is never a dead end:** human-readable digits beside the code → type it in · or search
by name · or reprint our own label. (And per ENRICHMENT-BACKLOG: **the name is the key, not the
barcode.**)

---

## 5. Backlog items

### BL-98 — Enrichment Queue (the one piece of software that doesn't exist)

**The spine of the whole migration.** Everything else in this doc is hardware, paper, or a script that
already exists. This is the screen that makes 2,000 items tractable.

**What it does:**
- **Hand me the next N items** (default 20) that are *not done*.
- **"Done" is objective, not a vibe** — the same kind of gap-test the Cleanup Cockpit already uses:
  has a photo · has a description · has a real category (not blank / not "On the fly") · has a cost ·
  has a class. Missing any → it's in the queue.
- **Fix inline, one at a time** — photo (Snap-&-fill), description, category, price/cost, 18+ (which
  must go through the shared `reconcile_age` seal, *not* a bare column write — see the 2026-07-06
  seal-inspection catch).
- **An item drops off the queue the moment its gaps are filled.**
- **A counter: `1,247 / 2,000 complete`.** This is the number that replaces the binder.
- **Print the label** straight from the row (§3).

**Reuse, don't rebuild:** this is a close sibling of `/pos/cleanup` (the sold-but-half-baked cockpit —
manager-gated, gap-defined, inline-fix, drops-off-when-filled). Same shape, different selector:
cleanup sorts by *what sold*, the enrichment queue sorts by *what's on the bench*. **Start by reading
`tests/pos/test_pos_cleanup_queue.py` and the cleanup router — then decide whether this is a new
screen or a second mode on the existing one.** Strong prior: a **filter/mode on the existing cockpit**
beats a new screen.

**Owner:** 🐯 Tigs · **Size:** small-to-medium · **Blocks:** nothing, but it's the thing that makes the
migration humane.

### BL-99 — Label renderer: size × flags

Widen `scripts/generate_label.py` from one fixed 62×37 layout to **S/M/L × content flags** (§3), fed
from product data. Ship with a print-preview PDF (Puppeteer, as today) and the `brother_ql` raster path
to the QL-820NWB. **Do NOT create per-category templates.**

**Owner:** 🐯 Tigs · **Size:** small · **Depends on:** nothing (script is standalone today).

---

## 6. Open decisions for Angel 🧍

1. **Order the DS2208 — but confirm the SKU ships WITH THE CABLE** before paying. (And decide whether the
   ~CHF 39 Inateck BT joins the order as the shelf-walking gun — it's cheap and it's the right tool for BL-97.)
2. **Lightbox: buy one (~CHF 40) or start with white paper + desk lamp (CHF 0)?** Recommend paper first.
3. **Enrichment Queue — new screen, or a mode on `/pos/cleanup`?** Tigs' prior is *mode on the existing one*.
   Say the word and it gets built.

---

*"The paper is a render of the truth, never the truth."*
*"If one seal fails, check all the seals." — and the 18+ flag goes through `reconcile_age`, always.*
