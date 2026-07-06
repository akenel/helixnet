# Banco POS — Proposal & Bill of Materials for Artemis

*Prepared for Felix (Artemis head shop) · draft 2026-07-06 · the "RFQ before he asks" —
we prescribe the complete kit for success instead of waiting for a brief.*

*Grounded in a real in-shop dry run (Angel + Layla, on prod, ~19 products, real sales).
Companion: [CUTOVER-PLAN.md](../CUTOVER-PLAN.md) · [BANCO-WORKLIST.md](../BANCO-WORKLIST.md).*

> **The pitch in one line:** *Here's your hardware, your prod server, your users, a database
> with ~500 items preloaded, and training for every employee — a till your shop runs on, not a
> gadget it fights with.* Buy-once quality, Swiss-native, field-tested in your own shop.

---

## 1. HARDWARE — Bill of Materials

Indicative CHF (confirm at Brack / Digitec / Galaxus). Every "Recommended" is the buy-once,
lasts-3–5-years, no-fuss choice; alternatives trade cost for a specific give.

| # | Item | ✅ Recommended | Alternative(s) | Indic. CHF |
|---|------|---------------|----------------|-----------|
| 1 | **Tablet** (the till) | **iPad (10th/11th gen), 64 GB** | Samsung Galaxy Tab A9+ (value) · Galaxy Tab Active (rugged) | 220–450 |
| 2 | **Barcode scanner** | **Zebra DS8178** (`DS8178-SR7U2100PFW`, BT 2D, cradle) | Zebra DS2278 (value) · Honeywell Voyager 1602g | 250–350 |
| 3 | **Label printer** | **Brother QL-820NWB** (WiFi/BT) | Zebra ZD421 (industrial/scale) | 150–400 |
| 4 | **Receipt** | **Epson TM-m30III** *(or paperless)* | Star mC-Print3 · **Banco email/QR = CHF 0** | 0–350 |
| 5 | **Tablet stand** | Locking, weighted, 360° counter stand | — | 60–100 |
| 6 | **Internet backup** | 4G failover router + Swiss data SIM | — | 100–200 |
| 7 | **Payment terminal** | *(already owned — Twint/Visa, standalone)* | integrate in Phase 2 | — |
| 8 | **Cash** | *(manual cash box — owner's call, no change)* | trigger drawer later | — |

**Indicative hardware total: ~CHF 900–1,450** one-time, depending on tablet & receipt choices.

### Why each pick (the trade-offs)

1. **Tablet — iPad 10th/11th gen.** Same "buy once" logic as the scanner: **6–7 years of OS
   support** (an Android budget tablet gets 2–3), reliable rear camera for Snap-&-fill, best
   resale, pairs cleanly with the Zebra over Bluetooth HID. *Alt:* **Galaxy Tab A9+** (~CHF 220,
   11" screen, fine for POS) if capex is tight — the honest value pick, just a shorter life.
2. **Scanner — Zebra DS8178** (already researched & decided). One device reads retail 1D **and**
   the loyalty/campaign **QR**; presentation cradle = hands-free counter scanning; 0.7% defect
   rate (Galaxus data). *Alt:* **DS2278** halves the cost with the same 2D capability.
3. **Label printer — Brother QL-820NWB.** Right-sized for a boutique: WiFi + Bluetooth, fast,
   black/red, cheap. **Two jobs:** price/shelf stickers **and printing a scannable barcode for
   on-the-fly / sticker-only items with no code** — the missing half of the OTF workflow. *Avoid
   Dymo* (locked to pricey proprietary labels). *Alt:* **Zebra ZD421** if volume climbs or you
   want one-brand fleet support (uses the cheapest, most flexible standard media).
4. **Receipt — Epson TM-m30III, or go paperless.** The card terminal prints the *card slip*, not
   the itemized receipt. The TM-m30III is the modern tablet-POS printer: **its ePOS-Print API is
   callable straight from JavaScript in the browser**, so our web POS prints to it with *no* middle
   layer — a real integration win. Bonus: over one USB-C it can **charge the tablet + give it wired
   network**. *Or* skip the box entirely — **Banco can email/QR the receipt (CHF 0, greener)**.
   Decide per shop; Artemis likely wants paper-on-request.
5. **Tablet stand — locking, weighted, 360°.** Anti-walk-off lock, rotates so the customer sees
   the total. Commercial (Bouncepad/Maclocks) or value (Mount-It!/AboveTEK).
6. **Internet backup — 4G failover + SIM.** The POS is web-based; a dead line = no sales. A small
   4G failover router on a separate cellular path keeps the till alive. (True offline is on the
   roadmap — until it ships, this is cheap insurance, not optional.)

---

## 2. SOFTWARE & SERVICE — what makes the hardware *work*

The gear is a third of the value. The prescription:

- **Prod server** — a dedicated, **DR-hardened box** (own environment), encrypted backups that are
  **restore-drilled**, on the proven gate ladder **sandbox → staging → preprod → prod**. Backups
  gate every prod deploy. (Today's dry-run box "slips" to preprod at go-live.)
- **Identity & users** — a Keycloak realm for Artemis, users provisioned to the role model:
  **Felix = admin · Layla = manager · cashiers = fast-path**. One login, proper RBAC.
- **Catalog — ~500 items preloaded + enriched** — FourTwenty reference for identity, **shop prices
  confirmed** (per the price doctrine), 18+ flags set, categories assigned. Plus the **cleanup
  cockpit** so "sold-but-unconfirmed" items surface for the manager daily.
- **Training, per role** — cashier (name + price + two ticks), manager (cockpit, price-confirm,
  labels, photos), admin (config). Converge an **SOP per use-case** during the 1–2 week on-site.
- **Support / hypercare** — the AI triage cockpit turns feedback into a backlog; tickets become the
  knowledge base.

---

## 3. SWOT — on the proposal as a whole

**Strengths**
- Field-tested **in Felix's own shop** — not a demo, a dry run on real products and sales.
- **Complete prescription**, not à-la-carte — hardware + server + users + data + training as one.
- **Swiss-native** VAT/fiscal fit; proximity + stewardship a big vendor can't match.
- **Buy-once quality** (Zebra + iPad + Epson) → low maintenance, long life.
- One device does barcodes **and** QR; receipt printer integrates via browser JS (Epson ePOS).

**Weaknesses**
- **Upfront hardware capex** (~CHF 1k+) vs. the status-quo paper/cash-box (~free).
- **Internet-dependent** until offline mode ships (mitigated by the 4G failover).
- **Single-shop reference** — no large install base yet; we're small.
- Training + curation is **real Angel-time** for 1–2 weeks.

**Opportunities**
- This proposal is a **template** — repeat it per head shop (the vertical GTM).
- Hardware **bundle margin** + setup fee + monthly = a real revenue line.
- **La Piazza community loop** (Banco funnels members into the Square).
- Felix's **March-2027 multi-department move** = a natural expansion beat.
- **Layla as steward/trainer** — she can carry the SOP to the next shop.

**Threats**
- Felix prefers the status quo / balks at capex.
- A big POS vendor undercuts on price (we win on fit, not price).
- Hardware availability / supply timing.
- Connectivity reliability at the shop.
- Key-person risk (Layla leaves; Pam already gone).

---

## 4. INVESTMENT SUMMARY (skeleton — Angel sets the CHF)

| Line | One-time | Recurring |
|------|----------|-----------|
| Hardware (BOM §1) | ~CHF 900–1,450 | — |
| Setup: server, realm+users, ~500-item preload+enrich | CHF _[set]_ | — |
| Training (per employee, 1–2 wk on-site) | CHF _[set]_ | — |
| Hosting + backups + support/hypercare | — | CHF _[set]_/mo |

> **The close:** *"Felix — here's exactly what your shop needs to run on Banco, priced and ready.
> Hardware, server, your team's logins, 500 products already in, and training so day one just
> works. Say yes and we start loading."*

---

*"The feed owns the name. The shop owns the price. We own that it all just works."*
*Draft — prices indicative, confirm at Swiss retailers; service CHF to be set by Angel.*
