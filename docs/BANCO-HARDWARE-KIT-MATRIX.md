# Banco Shop — Hardware Kit Matrix
### 2026-07-10 · Felix's head-shop go-live kit

> **The doctrine:** everything that can stop a sale needs a backup. Buy **quality** where it runs all
> day (the workhorse); buy **cheap** where it's a commodity or a spare. Phase the backups in as each
> primary proves out — don't buy two of everything up front.

---

## The matrix

| Role | Primary (quality) | Backup (cheap) | Emergency fallback | Consumables / needs |
|------|-------------------|----------------|--------------------|---------------------|
| **Screen** (runs Banco) | Big-screen laptop (the ~€40 salvaged ProBook) **or** a tablet | Cheap 2nd laptop | **Mobile phone** — works for a sale, **not** for bulk migration | Charger ×each + spare · counter **cradle/stand** |
| **Barcode gun** | Cheap wedge scanner (~CHF 80) — upgrade to **Zebra DS8178** only if tiny codes fail | 2nd cheap gun | **Phone camera** (PosScanner — already built) | USB cable / wireless receiver |
| **Label printer** | **Brother QL-820NWB** (mono) | Cheap 2nd label printer | Hand-write / skip the label | **Removable DK label rolls** (+ spares) · USB/network |
| **Power** | Counter **power strip** | Spare cables | — | Chargers, spare USB-C / cables |
| **Network** | Shop **Wi-Fi** (printer is NWB) | **Phone hotspot** | — | (offline mode = separate plan) |

**Why quality lands where it does:** the **printer** and the **screen** run all day and get reused
elsewhere → buy them solid. The **gun** is a commodity (keyboard-wedge, "just works") → buy it cheap,
because **we print our own barcodes** and read *those* 100% (see the Easy Barcode principle). The phone
is proven but is a *fallback*, never the primary — too small, fat-fingers, tiny thumbnails.

**Cheap gun vs webcam/phone camera — the gun wins the JOB:** faster (trigger vs focus-find-decode),
better on small/curved/glossy codes, its own light, pure keyboard-wedge (no app/permissions), and it
doesn't tie up the screen. Camera = the emergency spare, never the workhorse. Ranking:
**phone camera < cheap gun < premium gun.**

### Label spec (PoC) — minimal, "cheap but the RIGHT cheap"
- **Name/slug on top + barcode below.** No logo needed for PoC (Python/`brother_ql` can add logo/QR on upgrade).
- **S / M / L** label sizes. **Removable** adhesive (peel clean off the item).
- Only hard requirements: it **carries a code the cheap gun reads**, and it **peels clean**. Prettiness later.

### Gun acceptance bar
- **PASS** if the cheap gun reads ~**99%** of the small printed labels (1–3 misses / 100 = fine; it's designed for small codes).
- **FAIL → upgrade to DS8178** if it's more like **1-in-10**.
- **Failed scan is never a dead end:** a **human-readable number** prints beside the code → type it in · or search by name · or reprint our own label.

---

## The real job behind the kit: MIGRATION (1,000–2,000 products)

The kit exists to survive the big lift — getting the whole catalog in.

- **Volume:** phone-photos and phone-typing **won't scale** to 1–2k items. This is why the big screen +
  the gun matter — the **gun is the migration workhorse** (most products carry a barcode; zap it, it's
  gold).
- **Variants everywhere:** the same product comes in **flavors** (raspberry / blueberry / green apple …)
  and **sizes** (papers: small / medium / large / king-size slim / classics …). We need a
  **variant-aware add flow** (clone-a-product, change one field) so you're not re-keying the whole item
  for each flavor/size. Pairs with **tier pricing** (papers buy-more-save-more).
- **As-you-go labels:** when you add/zap an item, print a clean label on the spot — **bing-print** (one
  per scan) or **queue/batch mode** (stack them, print together), with an **ON/OFF toggle** (off during
  a normal sale, on during a labeling run). Runs on `generate_label.py` + `brother_ql`.
- **Even a no-hit is fine:** if the gun doesn't find a barcode, we don't have to label it — but the
  background option is to **print our own** clean label as we go, so the item is readable forever after.

### Two weeks → a few sessions: LINK, don't CREATE

**The fear:** scan → photo → categorize → *create* every item (~2 min × 2,000 = **two weeks**).

**The unlock:** **70-80% are ALREADY in the catalog, with a photo** (the 5,111-item Artemis import — every
product has a name + image; the only missing thing is the barcode). So for most items the job is to
**LINK the scanned code to the item that's already there**, not create it.

- **Fast flow (item in hand):** scan (or type 3-4 letters of the name) → tap the matching catalog card —
  **its existing photo confirms the match** → barcode linked → next. **~8 seconds, no photo-taking.**
- **Photo + create only for the 10-20% genuinely new** → queue them, do them at the desk with AI snap-fill.
- **Accelerator:** pre-link barcodes from the **Mosey/Tamar supplier feed** → those auto-link, zero manual
  touch (maybe half the work gone before you start).
- **Result:** a few focused sessions, **not two weeks.** You're not *building* the catalog — Felix's
  webshop already did — you're **teaching it the barcodes.**

> Field note: scanning resolves the barcode via the **Mosey/FourTwenty reference** (which carries EANs),
> not the Artemis catalog (which doesn't) — that's why a scan "just works" ~9/10. The **type-the-letters**
> path is what searches the Artemis catalog. Adopting from Mosey brings *Mosey's* price → **edit to
> Felix's price on the spot** (that's the normal case, not an edge case).

---

## Budget

Felix set **~CHF 500** for printer + gun. That comfortably covers the **primary printer + primary and
backup guns**. The **~€40 salvaged laptop** covers the screen. **Backups** for the printer and screen get
**phased in** as each primary proves out — not bought up front.

*Detail & rationale: memory `banco-hardware-procurement`. Barcode strategy: story
`stories/the-great-escape/FIELD-NOTES-2026-07-10-THE-GARBAGE-LAPTOP-AND-THE-EASY-BARCODE.md`.*
