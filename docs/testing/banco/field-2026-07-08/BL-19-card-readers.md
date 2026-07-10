# BL-19 — Card-reader integration: what Felix has (2026-07-08 photos)

Felix has **two Ingenico terminals, both on Worldline** (the Swiss acquirer, ex-SIX Payment Services).
Both run **ep2** (the Swiss ECR/terminal standard) — which is the good news for integration.

## Terminal A — Ingenico **Move/5000** (the older one)
- Portable terminal, EP2 software, acquirer **Worldline**, connected via **Swisscom 4G**.
- Product label: **`Move/5000 CL/4G/WiFi/BT`**, HVN `MOV50BC`, PN `TWB32012105T`.
- **TID `25145450`** · IMEI `353085093029381` · **BT Adr `0B38EFE3A7224E`** · WiFi `0W38EFE3BF1928`.
- So the answer to Angel's question: **yes, it is Bluetooth** (also WiFi + 4G). But see integration note — BT is not the usual till-integration transport.

## Terminal B — Ingenico **AXIUM DX8000** (the newer one)
- **Android smart POS terminal**, acquirer **Worldline**.
- Label: `Model AXIUM DX8000`, PN `TWT52011865A`, SN `22BNHD885709`.
- **TID `25409030`** · Worldline hotline 0800 111 600 / 0848 000 601.
- Contactless/NFC face. Android → can host apps → generally the better integration target of the two.

## Integration options (BL-19)
1. **ep2 ECR "integrated payment" (the standard Swiss path).** Banco sends the sale amount to the
   terminal (over LAN/TCP), the terminal takes the card, returns approved/declined + a txn reference,
   Banco records it. Kills the manual re-keying (the current flow) and the mismatch errors.
2. **The AXIUM DX8000 (Android)** is Worldline's newer platform and usually the cleaner target
   (on-device integration or a cloud API).
3. **Bluetooth** (Move/5000 has it) — real, but not how till↔terminal integration is normally done
   (LAN/TCP/ECR is). Don't anchor on BT.

## Reality check
Integration is **possible** — these are proper ep2 terminals, not dead-ends — but it is a **real project
with an external dependency: Worldline.** It is NOT a quick tune. The first action is not code, it's:
- **Felix asks Worldline** to enable the **ECR / ep2 integration interface** on his terminal(s), get the
  **protocol spec/SDK**, and confirm any fee + that his contract allows integrated payments.
- Ask Worldline **which terminal** to integrate (likely the AXIUM DX8000).
- Then Banco builds the ep2-ECR client (send amount → get result → record).

## Friday questions for Felix
- Which terminal does he actually use day-to-day — the Move/5000, the AXIUM, or both?
- Will he call Worldline about enabling integrated/ECR mode? (We can draft that ask.)
- New hardware is a fallback he offered — but we likely don't need it; these are integrable.

---

## BONUS — photo_1 is the **"Bestellungen" (orders) sheet** → the BL-21/BL-22 blueprint
Not a card reader — Felix's actual **handwritten reorder sheet**. It IS the paper we're digitising:
- Columns: **Datum | Produkt | Felix | Lieferant (supplier)**, rows checked off as ordered.
- **Supplier legend (seed this list for BL-22 "alternative suppliers"):**
  `420 = FourTwenty · BR = Breakshop · KK = Kings Castle · GV = Good Vibe · KB = Kundenbestellung
  (customer order) · WR = Wellauer · Hem = Hemag Nova · ND = Near Dark`.
- Confirms the BL-22 need: one product, multiple possible suppliers, Felix picks per-order (price vs
  who's already shipping). This sheet = the exact UI to design for the Order Book. Photo kept in `shop/`.
