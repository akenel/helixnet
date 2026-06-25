# Banco for Hofläden — a sketch

*Could the head-shop ERP serve Swiss farm shops? Yes — it's the strongest verified adjacent
vertical, and most of the engine maps over near 1:1. This is the "what would it take" sketch.*
*2026-06-25 · pairs with [[swiss-cbd-market-facts]] + the estate map (vision-as-data, seed-to-sale).*

> **Naming:** "Banco" is the head-shop product. A farm-shop product would be its own brand on the
> same engine (HelixNet) — working name **"Hofladen" / a farm-named twin** — `farm.lapiazza.app` or a
> client subdomain. Same modular-monolith rule: a new vertical = config + a few modules, NOT a new repo.

---

## 1. Why Hofläden (the only count-verified adjacent base)

- **11,358 farms sold their own products directly in 2016 → 12,676 in 2020** (BFS, +60% since 2010). That's
  **~100× the entire CBD shop base** and on a *rising* "regional / direct / Heimat" consumer trend.
- They live the **exact pain set** Banco was built for: cash-heavy, loose/unmarked goods, batch/lot
  **traceability is the law** (eggs, meat, raw milk), seasonal stock, and many run a **farm café** → the
  Swiss **dine-in 8.1% / takeaway 2.6% VAT split** — the same moat no US POS does.
- Caveat: the BFS metric counts any direct sale (fixed Hofladen + roadside stand + market stall + veg-box),
  so "fixed storefront" is a subset — still a large, real base.

## 2. What a farm shop gets for free (engine reuse — near 1:1)

| Farm need | Banco module today | Reuse |
|---|---|---|
| Till, receipts, Z-report | **POS** | direct |
| Food 2.6% vs farm-café dine-in 8.1% | **per-line VAT split** | direct — *the* moat |
| Cash accountability, multiple sellers | **per-cashier drawer + shift** | direct |
| Staff hours / seasonal helpers / payroll | **HR + My Day** | direct |
| Loose, barcode-less produce | **sell-to-seed + camera scan + photo→product AI** | direct (rename categories) |
| Photo → draft product | **`src/services/vision` PRODUCT domain** | direct |
| Batch/lot traceability | **seed-to-sale models** (`farm→batch→lab_test→trace_event`) | **this is the gold** — see §4 |
| Regional marketplace / community | **La Piazza** | direct — fits the "direct/regional" trend perfectly |
| Make-your-own labels/signage | **ISOTTO print pipeline** | direct (farm labels, price cards) |

**Read:** ~70% is already built. The farm twin is mostly *renaming + a few farm-specific bricks*, not a rebuild.

## 3. The UI / config deltas (the "fixes")

Mostly cosmetic + taxonomy, the La Piazza way (a `data-i18n` dict + a vertical config), not new plumbing:
- **Rename the vocabulary:** CBD/strain → **produce/harvest**; categories become Gemüse, Obst, Eier,
  Fleisch, Milch/Käse, Konfitüre, Honig, Getränke, Brot.
- **Drop** the 18+/age gate by default (not needed) — unless they sell wine/spirits/eau-de-vie (then it's
  the *same* `product_class` 18+ we already built — a bonus, not extra work).
- **By-weight pricing** — produce sold per kg / per bunch / per piece, ideally a **scale integration**
  (price = weight × CHF/kg). NEW brick, the biggest one.
- **Seasonality** — a product can be "in season / out" without being discontinued (a flag + a date window).

## 4. The traceability fit (the reuse that's almost too good)

The seed-to-sale models we cut for CBD compliance (`farm → batch → lab_test → traceable_item → trace_event`)
are **literally farm traceability** — the CBD version is the *harder* case. For a Hofladen:
- `farm` = the farm (already named that). `batch` = a harvest/lot (eggs from week 26, a cheese wheel, a
  slaughter lot). `trace_event` = received/packed/sold. `traceable_item` = the unit on the shelf.
- The **vision engine** generalizes: the CBD `lab_report` domain becomes a **`harvest_label` / `origin`
  domain** (snap a delivery label / Selbstdeklaration → batch + origin fields). Same `VisionDomain`
  registry, one new entry — no new integration.
- ⚠ **Verify before building:** Swiss food-traceability + direct-marketing self-declaration rules
  (Lebensmittelrecht / Selbstdeklaration, raw-milk & meat specifics) are NOT yet researched. The data
  model fits; the *legal field requirements* need a pass.

## 5. Farm-specific bricks worth their own design (the genuinely NEW stuff)

1. **Vertrauenskasse / honesty-box mode** — unmanned farm stands where customers self-serve and pay into a
   box / by Twint QR. A "self-checkout / trust" POS mode (scan-or-tap, pay-by-QR, no cashier). Very Swiss,
   very common, and **nobody's POS does it well.** Could be a signature feature.
2. **By-weight + scale** (§3) — the one real hardware/UX brick.
3. **Gemüseabo / subscription boxes** — recurring veg-box orders + pickup lists. Reuses customer/CRM +
   recipes-as-procedure (a box IS a BOM).
4. **Market-stall / offline mode** — selling at a Wochenmarkt with flaky signal → offline-capable till that
   syncs later. (Banco is online today; this is a real gap.)

## 6. La Piazza is the unlock, not a bolt-on

Farm shops + a **community marketplace** = exactly the "buy direct from the farm / regional" behaviour that's
already growing. A Hofladen on La Piazza (listings via the Artemis Premium bridge, reviews, pickup, veg-box
sign-up) is a *better* fit than CBD ever was — no advertising restrictions, a tailwind trend, and the
honesty-box QR is a natural on-ramp to membership.

## 7. Phased plan

- **P0 — Reskin (days):** vertical config + i18n vocabulary (DE first), farm categories, drop 18+ default.
  Stand up `farm.lapiazza.app` on the same engine. Demo to one real Hofladen.
- **P1 — By-weight + seasonality:** the scale brick + in-season flag. The first farm-specific value.
- **P2 — Traceability (after legal pass):** wire `farm/batch/trace_event` + the `harvest_label` vision domain.
- **P3 — Honesty-box mode + Gemüseabo:** the signature features.
- **P4 — Offline market-stall mode.**

## 8. Honest caveats / what to verify
- Swiss **food-traceability & self-declaration law** field requirements — not researched (the *model* fits).
- **Scale/hardware** integration is real engineering (protocols, certified weighing) — scoped as P1, not free.
- **Offline mode** is a genuine architectural addition, not a reskin.
- Fixed-storefront Hofladen count (vs the 11k–12.7k all-direct-sales figure) — needs the same kind of
  directory census we owe for CBD shops.

**Bottom line:** Banco → Hofladen is the highest-leverage generalization on the board — ~70% reuse, a
verified 100×-larger base, a rising trend, and the traceability "gold" is an *easier* fit than CBD. CBD
proves the engine; **Hofläden could be the volume.**
