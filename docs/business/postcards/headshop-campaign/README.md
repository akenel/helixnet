# 🃏 Head-Shop Postcard Campaign

A **4-touch, trackable, personalized** direct-mail sequence to Swiss head-shops.
Each card opens the door in *any* language; the in-language human closes in *theirs*.
Every QR is unique **per shop, per card** → a scan is a warm-lead signal with a name attached.

> The postcard bypasses the language barrier for the opener. The demo pulls them in.
> The human closes. And the QR tells you exactly *when* to bring in the human.

---

## The sequence
Mail one card every ~2–3 weeks. **Four cards, no bite → drop them.** A *scan* = hot → call now.

| # | Card | Role | The hook |
|---|------|------|----------|
| 1 | **intrigue** | pattern-interrupt, no sell | DE→FR jab + a bare QR *(„Mehr sagen wir nicht.")* |
| 2 | **value** | the relief stack | 🌐 languages · 🔞 18+ · 🏪 multi-shop · ⏱️ closeout · 🧾 VAT |
| 3 | **proof** | see it run | *„Glaub kein Wort. Scann und schau."* → the live demo |
| 4 | **last-call** | the human close | hands off to the in-language rep + phone; carries the drop-rule |

---

## Folder layout
```
headshop-campaign/
├── README.md              ← you are here
├── templates/             ← the EDITABLE source HTML — reformat/retune HERE
│   ├── card-1-intrigue.html
│   ├── card-2-value.html
│   ├── card-3-proof.html
│   └── card-4-lastcall.html
├── proofs/                ← rendered PDFs to REVIEW (sample "Muster Head-Shop")
│   ├── card-1-intrigue.pdf
│   ├── card-2-value.pdf
│   ├── card-3-proof.pdf
│   └── card-4-lastcall.pdf
└── assets/
    ├── qr/                ← QR images
    └── images/           ← drop card pictures here  ← the picture idea goes in here
```

## Merge fields (fill per shop before rendering)
`{{SHOP_NAME}}` · `{{SHOP_ADDR1}}` · `{{SHOP_ADDR2}}` · `{{SHOP_ZIP_CITY}}` ·
`{{QR_SRC}}` (path to the shop's QR png) · `{{TOKEN}}` (the tracking token) ·
**card 4 only:** `{{REP_NAME}}` · `{{REP_PHONE}}` (the local voice who closes)

## Render a card for one shop
```bash
# 1. the shop's unique QR (real cards point at PROD, not sandbox)
qrencode -s 10 -m 2 -o assets/qr/<shop>-c<n>.png "https://banco.lapiazza.app/r/<TOKEN>"
# 2. copy the template, fill the merge fields (QR_SRC → that png)
# 3. render
node scripts/postcard-to-pdf.js <merged>.html <out>.pdf
```
Token convention: `HS-<SHOP>-C<n>-<seq>` — e.g. `HS-MOSEY-C3-0001` (shop=Mosey, card=3).

## How the tracking works
QR → `/r/{token}` (endpoint: `src/routes/track_router.py`) → logs the scan (token + time +
coarse ip) → 302-redirects to the demo. The token encodes shop+card, so a scan tells you
*which shop* got curious at *which card*. Read warm leads off the log. Privacy: token + time
only — no device fingerprint, no precise location.

## ✅ Before real cards hit real mailboxes
- [ ] Set the **real REP name + phone** on card 4 (currently a placeholder)
- [ ] **Deploy the tracker to PROD** — sandbox resets nightly, so real QRs must point at `banco.lapiazza.app`
- [ ] **Pictures** — the picture idea → `assets/images/` (see below)
- [ ] **The list** — 10 shops: name · address · city · *one line of inside-scoop each* (the gold column)

## Status
Built 2026-07-01: all 4 templates + tracker live on sandbox, QRs verified firing.
Next: Angel's review + reformat pass (pictures, retuning) — Card 1 first, then apply across.
