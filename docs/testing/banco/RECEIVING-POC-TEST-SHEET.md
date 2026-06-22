# Receiving PoC — Fairphone test sheet (BL-91 + BL-93)

**What we're proving:** the receiving flow handles the real-world mix of items —
known, new-with-code, and no-code — by scanning each one in, one at a time, and
watching stock go up. The mock slip is the prop; later the AI will *read* this
same slip, but today you drive it by hand.

**Companion file:** `artemis-mock-delivery-slip-001.pdf` — print it, or just open
it on a second screen and scan the QR codes off the glass.

---

## Setup

| | |
|---|---|
| **URL** | https://staging-banco.lapiazza.app |
| **Login** | manager — `felix` / `helix_pass` |
| **Path** | Dashboard → **📥 Receiving** |
| **Deployed** | BL-91 receiving + BL-93 QR scanner (`?v=qr1` — force-refresh if the camera ignores QR) |

> **Why QR, not barcodes:** real manufacturer goods keep their EAN-13 (the scanner
> still reads those). QR is for codes **we** mint — easier to scan off a phone, and
> the only option for items with no barcode. This slip uses QR so your scan is clean.

---

## The four cases

| # | Item on slip | Qty | Scan | What should happen |
|---|---|---|---|---|
| **1** | Gizeh 6m Aktiv-Filter | 2 | QR `4002604431002` | **Known item** — resolves to the catalog product by name. Set qty 2, confirm → on-hand **+2**. |
| **2** | Sun Sack 125g | 5 | QR `7610442291046` | **Known item** — resolves. Qty 5, confirm → on-hand **+5**. |
| **3** | Hemp Wick Spule 5m | 12 | QR `7649912000017` | **New item, has a code** — "not on file" → **create it** (starts at stock 0), qty 12, confirm → on-hand **12**. |
| **4** | Räucherstäbchen lose | 3 | *(no code)* | **No-code item** — can't scan. Look it up by name or create it without a code, qty 3, confirm → on-hand **3**. |

**Bonus — "scan once, known forever":** after case 3, scan QR `7649912000017`
**again** (pretend it's next week's delivery). It should be recognised instantly as
"Hemp Wick Spule 5m" — no re-typing. That's the whole point of capturing it once.

---

## Also check while you're in there (BL-FB)

- The **💬 feedback button** can be **dragged** off the Submit button and stays where
  you drop it. A real drag should NOT pop the feedback form open.

---

## Report back

For each line, just: **PASS** or **what went wrong**. Things worth flagging:

- Did the QR scan first-try, or did you have to fight the camera?
- For known items (1, 2) — did the **right product name** come up?
- For the new item (3) — did create-then-receive feel smooth, or clunky?
- For the no-code item (4) — was the manual path obvious, or did you get stuck?
- Anything about quantities, the running total, or the confirm step.

When this passes, the next build is the **AI slip reader**: photograph this slip,
the model fills the worksheet for you, and you just scan to confirm each line.
