# Banco Label & Tagging Kit — Hardware Prescription + System Spec

*Part of the Artemis cutover plan + migration toolkit. As a new product comes onboard, print its
QR / barcode tag right then and there — "0,1,2,3 go, next next next." In-house, no outside printer.*

*Author: Tigs · 2026-07-13 · Status: hardware = prescription (ready to buy) · software = spec (build after stock in hand)*

---

## 1. The job

Two different outputs, and this doc covers the **label/sticker** side (thermal, on-demand). The
**color postcard** (photo keepsake on cardstock) is a *separate* machine — see §7.

The label is the workhorse of the cutover: every product — catalog item **and** onboarded maker
product — gets a tag with a **barcode (for the till)** and a **QR (for the customer's phone)**.

---

## 2. Printer — prescription

### Primary: **Brother QL-820NWB** ✅ buy this

| Spec | Value | Why it matters |
|---|---|---|
| Print tech | Direct **thermal** | No ink, no toner — *ever*. Just buy rolls. |
| Resolution | 300 dpi | Sharp enough for scannable QR + barcode. |
| Speed | ~176 mm/s | "next next next" batch flow. |
| Cutter | Auto guillotine | Cuts each label — no tearing. |
| Connectivity | **USB + Wi-Fi + Bluetooth + Ethernet** | **Any till/terminal or phone sends to it** — this is the one that fits "print from Banco on the spot." |
| Colour | **Mono (B&W)** on our path | Our print rail is `brother_ql` on Linux → **B&W only** (Brother's red needs Windows/P-touch). Already our decided call — costs us nothing; design in grayscale. |
| Max width | 62 mm | Covers product + shelf tags. |
| CH availability | Digitec/Galaxus, Brack, Microspot | Parts + rolls stocked locally (our criterion). |
| Street price | ~CHF 130–160 | — |

**Why not the cheaper siblings:** QL-800 is USB-only, QL-810W has no Ethernet/Bluetooth. The **NWB**
is the *connected* one — it's what lets Banco print to it over Wi-Fi from any station.

### Redundancy: buy **2 units** (one live, one spare)
*"If one seal fails, check all the seals."* A dead label printer **stops onboarding**. A CHF ~140
spare on the shelf removes that risk entirely. Same principle as the twin scanners.

### Optional wide upgrade: **Brother QL-1110NWB** (up to 103 mm / 4")
Only if you want big shelf-talkers or mini-postcards from the *same thermal unit*. Not required for
product/shelf tags — note it and decide later.

---

## 3. Rolls (Brother DK tapes) — **genuine only**

Off-brand rolls skip the calibration chip → mis-feed and wrong sizing. Genuine Brother, always
(same "no shortcut subsets" rule as the code).

### ⚠️ The part number IS the adhesive — read it before you buy
| Prefix | Adhesive | Form |
|---|---|---|
| **DK-44xxx** | **REMOVABLE** ✅ buy these | continuous (cut-to-length) |
| DK-22xxx | permanent | continuous |
| DK-11xxx | permanent | die-cut (pre-shaped) |

**Brother makes NO die-cut removable label** — removable exists **only as continuous rolls**. So peel-clean
= continuous DK-44xxx, and the printer's **auto-cutter cuts each label to length.** You trade pre-shaped
corners for peel-clean; peel-clean wins (Felix's requirement).

### Your criterion = REMOVABLE / peelable → these two rolls
| Roll | Size | Use |
|---|---|---|
| **DK-44205** ⭐ | 62 mm × 30.48 m continuous, **white, REMOVABLE** | THE workhorse — cut to any length, peels clean. Product tags, shelf tags, QR+barcode+name+price. |
| **DK-44605** | 62 mm × 30.48 m continuous, **yellow, REMOVABLE** | Sale / NEU / attention tags. |

> **Do NOT buy** the permanent lookalikes that dominate search results: **DK-22205** (62 mm white
> *permanent* continuous) or **DK-22251** (62 mm black/red 15.24 m — permanent *and* red, which our
> mono Linux path can't print anyway). If the listing says "Adhesive property: Permanent" → **wrong roll.**

### Recommended starter bundle
- QL-820NWB **× 2** (one spare)
- **DK-44205** (removable white 62 mm) **× 3** — the everyday product/shelf/QR tag
- **DK-44605** (removable yellow 62 mm) **× 1** — sale/NEU tags
- *(optional, only if some labels should stay PERMANENTLY put — e.g. our own packaging):* DK-11201 die-cut ×1

---

## 4. Maintenance gear

| Item | Why / cadence |
|---|---|
| **99 % isopropyl alcohol + lint-free swabs/wipes** | Clean the **thermal print head + platen roller** every few rolls. Adhesive/dust build-up = streaky, *unscannable* codes. **This is the main maintenance.** |
| **Compressed air** | Dust out the roll bay. |
| **Spare DK roll spool/holder** | Ships with the printer; a spare speeds swaps. |
| Keep printer + rolls **out of direct sun/heat** | Thermal media fades with UV/heat. Shop-floor lifespan is fine; anything that must last years in a sunny window → use the color-cardstock path (§7), not thermal. |

---

## 5. QR sizing — must scan with a normal phone

Your rule, and it's the right one. Two levers:

1. **Physical size:** minimum **~20–25 mm square**, with a **quiet zone** (blank margin ≥ ~2 mm all
   around). Rule of thumb: min size ≈ scan distance ÷ 10; a phone at ~20 cm → ~20 mm. The QL's 300 dpi
   is *not* the limiter — physical size + density is.
2. **Density (the sneaky one):** the QR currently encodes the **full URL**
   `https://…/pos/products/{uuid}/postcard` — long → dense → needs to be *bigger* to scan. **Fix: a
   short redirect** like `banco.lapiazza.app/p/{code}` → far fewer modules → scans reliably at 20 mm
   even on a 29 mm die-cut label. **Small build (short-link table + redirect route); do it independent
   of the printer — it also makes the on-screen/postcard QR crisper.** ← recommended first code step.

---

## 6. QR **and** barcode — both, because they do different jobs

Your synergy call, dead on. They're not redundant — they're complementary:

| | **Barcode (EAN-13)** | **QR code** |
|---|---|---|
| Read by | till scanner (Zebra) | **any phone camera** |
| Job | fast checkout ring-up | customer → product page / postcard |
| Reach | in-store only | **internet-wide** |
| Trackable | no | **yes** — product, timestamp, scan count |

So every label carries **both**: **barcode for the till**, **QR for the customer**. Converting the
store to have both means the traditional POS scan still works *and* every product becomes a
**trackable internet touchpoint**. The same little sticker does **checkout + marketing + analytics**.

**Tracking (free bonus):** the QR opens a Banco route, so we can **log each scan** (product, time,
coarse device) → "which products get scanned, when." Real analytics off the label. A maker (Mama
Cynthia) can even see her own postcard scans — ties the [[banco-local-maker-onboarding]] loop.

---

## 7. Software — the label templates (SPEC — build after stock lands)

**Default templates** (pick from a dropdown when printing):
1. **Item sticker** — on the product: name + QR + barcode + SKU + price *(die-cut DK-11201/11209)*
2. **Shelf sticker / talker** — on the shelf edge: name + **price (big)** + QR + barcode *(removable DK-44205)*
3. **Catalog / printout sticker** — for the printed catalog/order sheet: name + QR + SKU

**Custom designer** (the key — "whatever they want"): toggle each element on/off + position/size —
logo, QR, barcode, name, SKU, price. E.g. *"logo here, no barcode, just QR + name + SKU."* Save as a
named template.

**Print flow:** product → **Print label** → pick template → **ask quantity N** → sends N to the QL
over Wi-Fi. *"0,1,2,3 go — next next next."*

**Integration rail (Python-first):** drive the QL-820NWB from Banco via the open-source
**`brother_ql`** library — render the label PNG server-side (same QR/barcode libs we already use),
pipe to `brother_ql` → printer over network/USB. No vendor lock, fits our stack.

**Build discipline:** template dimensions must match the physical DK stock to the millimetre — so
**build the label-print feature once the printer + rolls are in hand.** The §5 short-URL is the one
piece worth building *now* (independent, and it also sharpens the postcard QR).

---

## 8. Buy list (tl;dr)

- [ ] Brother **QL-820NWB × 2**
- [ ] **DK-44205** removable white 62 mm × 3  ← *the roll; anything marked "Permanent" is wrong*
- [ ] **DK-44605** removable yellow 62 mm × 1
- [ ] 99 % isopropyl + lint-free swabs, compressed air, spare spool
- [ ] *(optional)* QL-1110NWB if you want 4" wide shelf-talkers/mini-postcards

*Next code step regardless of hardware: the short-URL `/p/{code}` redirect (§5) → scannable small QRs everywhere.*
