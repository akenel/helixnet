# Banco — born-once photo lost for cashiers (403 role mismatch) — fix spec

**Severity: demo-affecting.** Found by Angel on the sandbox (phone), 2026-06-22. A cashier
snaps a photo during the born-once "new item, no barcode" flow → the item saves and is
searchable by name, but shows the 📦 placeholder, **no picture**. The photo is silently
dropped.

---

## Root cause (confirmed in code) — a role mismatch, swallowed by the UI
The born-once create and the photo upload are **one action** ("born once *with a picture*"),
but they're gated differently:

| Step | Endpoint | Gate | Cashier (pam)? |
|------|----------|------|----------------|
| Create the item | `POST /api/v1/pos/products/quick` (`pos_router.py:156`) | `require_any_pos_role()` | ✅ allowed |
| Attach the photo | `POST /api/v1/pos/products/{id}/images` (`pos_router.py:431`) | `require_roles([pos-manager, pos-developer, pos-admin])` | ❌ **403** |

So pam creates the product fine via `/quick`, then the photo POST returns **403** — and the
front-end **silently swallows it** (`scan.html:730`, and the lazy-capture twin ~`847`):
```js
} catch (imgErr) { console.warn('photo upload failed', imgErr); }
```
Item saved, searchable, no photo. Invisible until someone eyeballs the result.

*(MinIO is fine — wired in `docker-compose.banco-sandbox.yml` (`depends_on: minio`). The
serve endpoint `GET …/images/{id}` is already public. Neither is the problem.)*

## The fix (small)
1. **Open the photo upload to cashiers** — change `POST /products/{id}/images`
   (`pos_router.py:431`) from `require_roles([manager, dev, admin])` to
   **`require_any_pos_role()`**, matching `/products/quick`. A cashier snapping a photo
   during a sale *is* the born-once flow; the photo must be allowed for whoever can create
   the item. (Catalogue *management* — price edits etc. — stays manager-only; only the
   photo add opens up. Adding a benign photo is low-risk; the cashier already creates the
   product and rings the sale.)
2. **Stop swallowing the failure** — on a failed photo upload, show a toast
   ("Photo couldn't be saved — item saved without it") instead of only `console.warn`
   (`scan.html` OTF ~730 + lazy-capture ~847). This is *why* the bug was invisible.

## Acceptance
- [ ] Log in as **pam (cashier)** → born-once "new item, no barcode" + take a photo →
      product shows the photo **as its cover** (not 📦).
- [ ] The photo renders in the **catalogue picture wall** (Day-One Beat 8).
- [ ] Re-run Day-One sheet **Beat 4** (photo shows on product) on the phone — green.
- [ ] (regression) a failed upload now surfaces a toast, never silent.

## Seal lesson
The create was made cashier-safe; its **sibling** (the photo upload, same born-once action)
was left manager-only. *If you open one component to a role, check the sibling that
completes the same action.*

---

*Still separately unverified (the other readiness unknown): does the label queue actually
**print** the N-up PDF? Confirm on the phone — different seal, not this one.*
