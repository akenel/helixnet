# Banco — Settings page spec (→ code terminal)

**Purpose:** replace the dead `/pos/settings` stub with a real admin screen so Felix's
**legal name + VAT number** land on receipts. The entire back-end already exists — **this
is a UI-only ticket.**

---

## What already exists (do NOT rebuild)
- **Model** `StoreSettingsModel` (table `store_settings`), seeded by `store_settings_seeding`.
- **API, already live in `pos_router.py`:**
  - `GET  /api/v1/pos/settings/{store_number}` → `StoreSettingsRead`  (line ~1832)
  - `PUT  /api/v1/pos/settings/{store_number}`  ← `StoreSettingsUpdate` (line ~1858)
- **Schemas** `StoreSettingsRead` / `StoreSettingsUpdate`.
- **`shop_setup_service`** — country defaults (CH/DE/AT/IT/FR/NL → currency, vat_rate,
  language, prices_include_vat) + a **`missing_required()`** validator that already defines
  the required set.

## What to build (UI only)
1. Replace the stub handler `pos_settings` (`pos_router.py` ~2986) to render a new
   `src/templates/pos/settings.html` (admin-gated — match `catalog.html` / the `isAdmin`
   pattern in `dashboard.html`).
2. `settings.html`: Alpine page → on init `GET /api/v1/pos/settings/1` → form over the
   fields → **Save** does `PUT /api/v1/pos/settings/1` → toast on success.

## Fields (group them on the form)
| Group | Fields |
|-------|--------|
| **Company identity** | `legal_name`*, `store_name`*, `vat_number`* *(hint: `CHE-XXX.XXX.XXX MWST`)*, `country` (dropdown — drives defaults) |
| **Address** | `address_line1`*, `address_line2`, `postal_code`*, `city` |
| **Contact** | `phone`, `email`, `website` |
| **Receipt** | `receipt_header`, `receipt_footer`, `receipt_logo_url` |
| **Rules** *(phase 2 — show read-only or defer)* | cashier/manager max discount, 3 loyalty tiers |

\* required, per `shop_setup_service.missing_required()`: `store_name`, `legal_name`,
`vat_number`, `address_line1`, `city`, `postal_code`.

## Acceptance
- [ ] Admin opens `/pos/settings` → real form, pre-filled from `GET`.
- [ ] Edit `legal_name` + `vat_number` → Save → reload → **persists** (PUT worked).
- [ ] Required-field validation blocks save if a `*` field is blank.
- [ ] **Print a receipt → the new `legal_name` + VAT number appear on it.**
      ✅ **Confirmed wired:** `receipt.html` already renders `storeSettings.store_name` /
      `legal_name` / `vat_number` (with `Artemis…` fallbacks), loaded from
      `GET /api/v1/pos/settings`. So editing Settings flows straight to receipts. **Just
      verify the Z-report does the same** — if it reads an app-config `STORE_NAME`, wire it
      to `store_settings` too (seal lesson: same value, every printout).
- [ ] A non-admin cashier cannot reach the page.

## Why now (not vanity)
A Swiss receipt is **legally required** to show the business **VAT/UID number + legal
name**. Before Felix's real go-live, this must be *his* company, not the seeded default.
Small screen, API already done → high value, low effort.
