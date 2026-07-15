# The Living Catalog — Banco Product Page (Build Spec)

*Angel's vision, 2026-07-15: bring the catalogue to LIFE. One product page, shareable and rich
like the Artemis/Tamar e-shop — but role-aware (guest browses · cashier serves · manager edits),
multilingual, phone-first, and wired into the La Piazza funnel. The postcard's big brother.*

Kicked off from the Greengo King Size Slim page on artemisluzern.ch (tiers, specs, "you might also
like", store footer). We already own ~80% of the parts — this is mostly ASSEMBLY, not invention.

---

## North star: PHONE-FIRST (non-negotiable)
Everything works on a phone browser, full stop. Friday's shop session (Layla + the scanner gun +
the big laptop) must degrade to **the phone** if anything else fails. "If the phones are down you've
got bigger problems than a headshop." Offline mode stays a KNOWN, DEFERRED dilemma — the base is:
**a phone with a browser is always enough.** Responsive first, desktop second.

## The one idea: ONE page, THREE lenses
The same `/pos/products/{id}` (public: `/p/{code}`) renders by who's looking:

| Lens | Who | Sees |
|------|-----|------|
| **Guest** | no login (QR scan, shared link) | image gallery, name, price, **tier ladder**, description (their language), spec table, **"you might also like"**, store footer, share button. Bounces product→product. |
| **Cashier** | logged-in cashier | all the guest stuff **+** stock/availability, sales history hints, "add to cart", the barcode/SKU |
| **Manager** | logged-in manager/admin | all the above **+** inline **EDIT mode** with live preview, **compare-to-market** (supplier price intel), margin |

Edit mode reuses the unsaved-work guard ([[banco-unsaved-work-guard]]): a manager can never fat-finger
or swipe out of an edit — "You're editing. Discard changes?" first. Preview = what the guest will see.

## What we already have (the ~80%)
- **Tier pricing** (BL-26) — staged prices, editor, cart math. → the ladder.
- **Multi-language descriptions** (BL-36 `description_i18n`) + chrome i18n (en/de/fr/it). → one URL, 4 languages.
- **Enriched attributes** (key:value: Rohstoff, Papierstärke, Breite…). → the spec table.
- **Categories** (2-level + emoji). → breadcrumbs + browse.
- **Image gallery** (multi-image, cover). → the hero.
- **Find-first matcher** (trigram + category). → "you might also like".
- **Postcard maker + QR + short-links** (`/p/{code}`, OG unfurl, Banksy serial). → share + the public shell.
- **Supplier compare** (FourTwenty/Tamar price intel). → compare-to-market (manager).
- **Store footer** (name/address/hours/phone/website/email/socials — shipped b1793). → the footer.
- **Lab-report vision domain** (photo a COA → THC/CBD/lot/date). → CBD transparency.
- **Cleo / run_llm** (BYO-brain). → the concierge.

---

## The 14 (the full ambition — Angel: "we're going all the way")

**PHASE 1 — the MVP (base, build first):**
1. **The product page** — public shell, gallery, name, price, footer. The canvas everything hangs on.
2. **"You might also like"** — 6–12 related items (find-first by category+name) with thumb + price.
3. **Tier ladder** — *ab 10 → 1.60 · ab 50 → 1.10 · ab 150 → 1.00* + "save N%" on the best break.
4. **Spec table** — the enriched attributes rendered clean (Rohstoff, Papierstärke, Blatt, Breite, Länge).

**PHASE 2 — the differentiators (this is why ours BEATS Artemis, not just matches):**
5. **One product, four languages, one URL** — `?lang=` on description + chrome. The Swiss/EU edge, built in.
6. **Maker story up top** — artisan items (Cynthia, Ecolution) lead with the human + photo. Artemis can't.
10. **CBD lab transparency** — THC/CBD/lot/tested-date from the lab-report domain. Seed-to-sale, visible.

**PHASE 3 — the funnel + browse (bounce around, come to the counter):**
7. **Compare-to-market** — our price vs online, "you beat it by X" (manager view first; maybe public).
8. **Clickable breadcrumbs → category browse** — Papers & Co · Drehpapier · Greengo → a listing page.
B1. **Share & referral** — every page shares like the postcard (serial + OG). Foot traffic engine at catalogue scale.
B2. **Reserve for pickup** — "in stock at Artemis Lucerne · reserve" → the pickup CTA → receiving. Loop closes.
+ **Guest filters** (Angel) — filter/sort the browse (price, category, in-stock) so guests explore.

**PHASE 4 — the wow + the operational:**
B3. **Cleo the concierge** — "a beginner-friendly unbleached paper?" → the LLM recommends from OUR catalogue,
    in any language. Cleopatra at the Artemis door — an instant cashier that never sleeps. ([[lp-cleo-agent-loop-go]])
9. **Shelf kiosk mode** — the same page on a cheap tablet clipped to the shelf. Self-serve details/tiers/related.
B4. **Print the page** — one print-CSS → an A4 product sheet / shelf poster. Needed for **labels** + the counter book.

---

## Role model (how the lens is chosen)
- **Guest** = no token (public `/p/{code}` or `/pos/products/{id}` unauthenticated). Read-only, no stock/history.
- **Cashier / Manager** = existing POS roles via the token. Progressive disclosure — same template, more panels.
- No new identity work — rides the roles we have across the 3 realms.

## Open questions (Angel's calls — before Phase 1 code)
1. **Public scope.** Guest pages = per-product (shareable, QR-reachable, like the postcard) — YES for Phase 1.
   A fully indexed, browsable PUBLIC storefront (SEO) is bigger and overlaps the PARKED La Piazza storefront —
   keep that parked; Phase 1 guest = "landed on THIS product, can hop to related", not "browse the whole shop
   from Google". Confirm.
2. **Edit-in-place vs the existing catalog modal.** Manager edit on the product page (unify, with the guard) —
   or keep the catalog edit modal and just deep-link to it? Leaning: edit-in-place, it's the better story.
3. **Compare-to-market visibility** — manager-only, or a public "we beat the online price" flex?

## Friday readiness (2026-07-15 → Fri)
Layla + the scanner gun + the big laptop, ~3–4 h in the shop. The demo target is Felix's "wow" AND a real
prod-migration test. Phase 1 (the page) is the demo centrepiece. Everything shown must work on the PHONE as
the fallback. Label printing (B4/#9) waits on the QL-820 but the page/print-CSS can be ready.

## Doctrine
- Reuse before build (the ~80% list). Every phase is mostly assembly.
- Phone-first, always. Desktop is the bonus, not the base.
- The guard everywhere a manager can edit ([[banco-unsaved-work-guard]]).
- The page is a RENDER of the DB — never a second source of truth (same rule as the label kit).
- This is the [[banco-lapiazza-community-loop]] at catalogue scale: Banco = the funnel, the counter = the destination.
