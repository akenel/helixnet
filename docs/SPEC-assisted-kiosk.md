# SPEC — Assisted Kiosk (Pam's super-powered kiosk)

*Status: DRAFT + M1 building · 2026-07-18 · ties memory `banco-kiosk-guest-station`, `banco-role-lifecycle-rules`,
`banco-barcode-matching-doctrine`, `banco-first-real-user-inventory-ownership`, `banco-master-data-vision`.*

## The idea

The kiosk is normally the **anonymous guest station** (scan → view → build basket → show code to cashier). The
**assisted kiosk** is the SAME screen when a staff member launches it from their dashboard: it recognises them and
unlocks cashier powers. The headline power: **a scan-miss becomes "create this product now"** — Pam photographs it
(kiosk camera), captures whatever barcode exists (or none), names + prices it (often a live negotiation), and sells
it — the born-once doctrine with a human at the wheel, at the counter, in front of the customer.

Angel's story (2026-07-18): *"The customer says it's not working. Pam scans it — that product's not in the system. 'I
can fix that. How much you wanna pay?' Ten boxes, deal. She creates it right from the kiosk — takes a picture, the
barcode reader's there, maybe it has an EAN, maybe not. She'd have the power to do it right then and there."*

## The safety rule (non-negotiable)

The kiosk runs on **guest-facing devices** — powers must NEVER leak to a guest. So staff powers appear **only** when
BOTH hold: (1) the kiosk was launched with `?staff=1` (comes from the authenticated dashboard card), AND (2) a valid
POS session (`pos_token`) is present in this tab. A new tab opened via `window.open` from the dashboard **inherits a
copy** of the opener's `sessionStorage` (same-origin) — so Pam's launch carries her token, while a cold guest tablet
that just browsed to `/pos/kiosk` has no token and stays pure guest. Server-side, every create/sale endpoint still
enforces the staff role independently — the client flag is an affordance, not the security boundary.

## Slices

- ✅ **M1 (this turn) — staff-awareness + create-on-miss hand-off.** The kiosk detects assisted mode, shows a
  "👑 Assisted · {name}" badge, and on a scan-MISS shows a **"➕ Create this product"** button that hands off to the
  till's existing born-once create flow (`/pos/scan?capture=<barcode>` → `openLazyCapture`), barcode prefilled. Pam
  finishes the create + sale on her powered till. Smallest safe vertical slice that proves the whole story.
- **M2 — create IN the kiosk.** Bring the create-on-fly modal (photo via kiosk camera, name, price, category) into
  the kiosk itself so Pam never leaves the screen. Reuse the `openLazyCapture` primitives + `_copy_external_image`.
- **M3 — ring out IN the kiosk (assisted checkout).** Complete the sale on the spot (payment method + the 🌍-1
  payments seam when live) instead of routing through Held Orders. Skips the "guest gets a code → cashier re-rings".
- **M4 — supplier on-ramp (bonus).** A "new maker" flow: photograph a batch of never-seen goods (Ecolution/Cynthia),
  set wholesale-agreed prices, create them live at the counter. Master-data onboarding one product at a time.

## M1 build notes

- `dashboard.html`: the Guest Kiosk card (isCashier) opens `/pos/kiosk?staff=1`.
- `kiosk.html`: `init()` sets `staff`/`staffName` from `?staff=1` + `pos_token` (JWT `preferred_username`); a fixed
  staff badge; the `notfound` view gains a staff-only Create CTA → `/pos/scan?capture=<lastBarcode>`.
- `scan.html`: `init()` adopts `?capture=<barcode>` → `openLazyCapture(barcode)` and cleans the URL.
- Guest path unchanged (no `?staff=1` / no token → byte-identical to today). Sandbox-first; deploy sandbox, human-green.
