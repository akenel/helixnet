# Banco — `tobacco_nicotine` class review (95 rows)

**Source:** `banco_prod.reference_products` @ `3547efa` · **Date:** 2026-06-25
**Scope:** every reference item the classifier tagged `tobacco_nicotine` (→ 🔞 18+).
**Why:** human backstop for the BL-96 taxonomy. The rules over-gate on purpose
(over-gate = safe, never under-gate), so this list is about catching **wrong-class**
items, not missing-age ones. Real fixes are Felix/Ralph + Treuhänder calls in **Phase F** —
nothing here is enforced yet (flag-only).

---

## ✅ 3 newly caught by the Italian-spelling fix (`tabacc`/`sigaret`)

These were `standard` (un-gated) before today; now correctly 🔞 18+:

1. `Sasso Tabaccos Brazil Hash BIO`
2. `Sasso Tabaccos Brazil Virginia Blend`
3. `VapeLounge Fairline Fresh Tabacco Shortfill 40ml` — *tobacco-flavoured e-liquid shortfill (flavour, not leaf; 18+ is the safe call for e-liquid)*

---

## 🚩 Tigs review flags (wrong-class, not wrong-age — for Felix/Ralph)

**A) Accessories over-gated as tobacco** (hardware, not a substance — 18+ is harmless but the class is wrong; they'd hit tobacco promo/VAT rules in Phase F). Caused by a **compound-word gap** in the accessory guard (the same boundary problem as `tabacc` — `\betui\b` doesn't fire inside `Zigarettenetui`):
- #10 `Chromcase Cigarettes` (chrome case)
- #19 `Ersatzkopf Black für Shishatabak` (replacement bowl)
- #24 `Mata Leon Headhunter Tabakkopf mit Kaminaufsatz` (hookah bowl)
- #25 `One Hitter Cigarette` (one-hitter pipe)
- #92 `Wild Fire Cigarette Case Metal Optic Assort.`
- #93 `Zigarettenetui aus Chrom 100mm Assortiert`
- #94 `Zigarettenetui aus Chrom 80mm Assort.`
- #95 `Zigarettenetui Rainbow`

**B) CBD items classed as tobacco** (should be `cbd_hemp` — still 18+, but they LOSE the `thc_report` compliance flag if left as tobacco):
- #22 `Legendary Premium CBD Pre Rolls Cigarettes`
- #23 `Legendary Premium CBD Pre Rolls Cigarettes 10pcs`

**C) Tobacco *substitute* over-gated** (herbal, no tobacco/nicotine — defensible to keep 18+, but it's not a tobacco product):
- #11 `C-Pure Fedtonic - Tabakersatz 10gr`
- #12 `C-Pure Fedtonic - Tabakersatz 3gr`

> Suggested follow-up (NOT done — your call): a "substance-accessory compound" pass
> (catch `*etui`, `*kopf`, `case`, `one hitter`) + route `CBD … Cigarettes/Pre Roll`
> to `cbd_hemp`. Queue it like the Italian fix once you've eyeballed the field run.

---

## Full list (95)

| # | Title | Category |
|---|-------|----------|
| 1 | Sasso Tabaccos Brazil Hash BIO `NEW` | Tobacco & Cigarettes |
| 2 | Sasso Tabaccos Brazil Virginia Blend `NEW` | Tobacco & Cigarettes |
| 3 | VapeLounge Fairline Fresh Tabacco Shortfill 40ml `NEW` | Tobacco & Cigarettes |
| 4 | 10x Pueblo Blue Tabak 25g | Tobacco & Cigarettes |
| 5 | 10x Pueblo Classic Tabak 25g | Tobacco & Cigarettes |
| 6 | American Spirit Tabak Dose 75g | Tobacco & Cigarettes |
| 7 | American Spirit Tabak Natural Blue RYO Big Pack 5 x 25g | Tobacco & Cigarettes |
| 8 | American Spirit Tabak Natural Yellow RYO 25g | Tobacco & Cigarettes |
| 9 | American Spirit Tabak Naturlal Blue RYO 25g | Tobacco & Cigarettes |
| 10 | Chromcase Cigarettes 🚩A | Tobacco & Cigarettes |
| 11 | C-Pure Fedtonic - Tabakersatz 10gr 🚩C | CBD & Hemp |
| 12 | C-Pure Fedtonic - Tabakersatz 3gr 🚩C | CBD & Hemp |
| 13 | D'Lice USA Classic - Tabakgeschmack 12mg 10ml | Vaporizers |
| 14 | D'Lice USA Classic - Tabakgeschmack 18mg 10ml | Vaporizers |
| 15 | D'Lice USA Classic - Tabakgeschmack 3mg 10ml | Vaporizers |
| 16 | D'Lice USA Classic - Tabakgeschmack 6mg 10ml | Vaporizers |
| 17 | D'Lice Virgina - Tabakgeschmack 18mg 10ml | Vaporizers |
| 18 | D'Lice Virgina - Tabakgeschmack 6mg 10ml | Vaporizers |
| 19 | Ersatzkopf Black für Shishatabak 🚩A | Tobacco & Cigarettes |
| 20 | Fred Rose Additive Free Fine Cut Tobacco 25gr | Tobacco & Cigarettes |
| 21 | Fred Rose Tabak Dose 80g | Tobacco & Cigarettes |
| 22 | Legendary Premium CBD Pre Rolls Cigarettes 🚩B | Tobacco & Cigarettes |
| 23 | Legendary Premium CBD Pre Rolls Cigarettes 10pcs 🚩B | Tobacco & Cigarettes |
| 24 | Mata Leon Headhunter Tabakkopf mit Kaminaufsatz 🚩A | Accessories |
| 25 | One Hitter Cigarette 🚩A | Tobacco & Cigarettes |
| 26 | OS Tobacco 54 Watermelon 200g | Tobacco & Cigarettes |
| 27 | OS Tobacco African Queen Fruitmix 1kg | Tobacco & Cigarettes |
| 28 | OS Tobacco African Queen Fruit Mix 200g | Tobacco & Cigarettes |
| 29 | OS Tobacco Afrikan King Fruitmix 200g | Tobacco & Cigarettes |
| 30 | OS Tobacco Bad Girl Lime Grapefruit 200g | Tobacco & Cigarettes |
| 31 | OS Tobacco Bonnie and Clyde Apple Mint 200g | Tobacco & Cigarettes |
| 32 | OS Tobacco Cosanostra Blueberry Mint 200g | Tobacco & Cigarettes |
| 33 | OS Tobacco Disco Peach 200g | Tobacco & Cigarettes |
| 34 | OS Tobacco Queen of the Desert Pricklypear Coconut 200g | Tobacco & Cigarettes |
| 35 | OS Tobacco Red Lagoon Fruitmix Pricklypear 200g | Tobacco & Cigarettes |
| 36 | OS Tobacco TNT Blueberry Wildberry Raspberry 200g | Tobacco & Cigarettes |
| 37 | OS Tobacco Unknown Pricklypear Lime Mint 200g | Tobacco & Cigarettes |
| 38 | Pueblo Blue Tabak 25g | Tobacco & Cigarettes |
| 39 | Pueblo Blue Zigaretten | Tobacco & Cigarettes |
| 40 | Pueblo Classic Tabak 25g | Tobacco & Cigarettes |
| 41 | Pueblo Classic Tabak Dose 100g | Tobacco & Cigarettes |
| 42 | Pueblo Classic Zigaretten | Tobacco & Cigarettes |
| 43 | Sennenquöll Glacier Water Tobacco Crystal Shortfill 50ml | Tobacco & Cigarettes |
| 44 | Social Smoke Tobacco Absolute Zero 100g | Tobacco & Cigarettes |
| 45 | Social Smoke Tobacco Absolute Zero 200g | Tobacco & Cigarettes |
| 46 | Social Smoke Tobacco Baja Blue 100g | Tobacco & Cigarettes |
| 47 | Social Smoke Tobacco Baja Blue 200g | Tobacco & Cigarettes |
| 48 | Social Smoke Tobacco Cucumber Chill 100g | Tobacco & Cigarettes |
| 49 | Social Smoke Tobacco Cucumber Chill 200g | Tobacco & Cigarettes |
| 50 | Social Smoke Tobacco Lemon Chill 100g | Tobacco & Cigarettes |
| 51 | Social Smoke Tobacco Lemon Chill 200g | Tobacco & Cigarettes |
| 52 | Social Smoke Tobacco Pear Chill 100g | Tobacco & Cigarettes |
| 53 | Social Smoke Tobacco Pear Chill 200g | Tobacco & Cigarettes |
| 54 | Social Smoke Tobacco Watermelon Chill 100g | Tobacco & Cigarettes |
| 55 | Social Smoke Tobacco Watermelon Chill 200g | Tobacco & Cigarettes |
| 56 | Social Smoke Tobacco Wild Berry Chill 100g | Tobacco & Cigarettes |
| 57 | Social Smoke Tobacco Wild Berry Chill 200g | Tobacco & Cigarettes |
| 58 | Swiss Smoke Bajaa Blue Shisha Tabak 50g | Tobacco & Cigarettes |
| 59 | Swiss Smoke Baja Blue Shisha Tabak 100g | Tobacco & Cigarettes |
| 60 | Swiss Smoke Baja Lemon Chill Shisha Tabak 50g | Tobacco & Cigarettes |
| 61 | Swiss Smoke Black Grape Shisha Tabak 100g | Tobacco & Cigarettes |
| 62 | Swiss Smoke Black Grape Shisha Tabak 50g | Tobacco & Cigarettes |
| 63 | Swiss Smoke Blue Berry Mint Shisha Tabak 50g | Tobacco & Cigarettes |
| 64 | Swiss Smoke Blue Ice Shisha Tabak 100g | Tobacco & Cigarettes |
| 65 | Swiss Smoke Blue ICE Shisha Tabak 50g | Tobacco & Cigarettes |
| 66 | Swiss Smoke Capri Sonne Shisha Tabak 100g | Tobacco & Cigarettes |
| 67 | Swiss Smoke CBD Blueberry Shisha Tabak 100g | Tobacco & Cigarettes |
| 68 | Swiss Smoke CBD Exotic Shisha Tabak 100g | Tobacco & Cigarettes |
| 69 | Swiss Smoke Cold Peach Shisha Tabak 50g | Tobacco & Cigarettes |
| 70 | Swiss Smoke Crazy Lady Shisha Tabak 50g | Tobacco & Cigarettes |
| 71 | Swiss Smoke Double Apple Shisha Tabak 100g | Tobacco & Cigarettes |
| 72 | Swiss Smoke Double Apple Shisha Tabak 50g | Tobacco & Cigarettes |
| 73 | Swiss Smoke Double Melon Ice Shisha Tabak 50g | Tobacco & Cigarettes |
| 74 | Swiss Smoke Grape Mint Shisha Tabak 50g | Tobacco & Cigarettes |
| 75 | Swiss Smoke Grape Shisha Tabak 50g | Tobacco & Cigarettes |
| 76 | Swiss Smoke Ice Ananas Shisha Tabak 50g | Tobacco & Cigarettes |
| 77 | Swiss Smoke Lemonade Shisha Tabak 50g | Tobacco & Cigarettes |
| 78 | Swiss Smoke Lemon Chill Shisha Tabak 100g | Tobacco & Cigarettes |
| 79 | Swiss Smoke Lemon Chill Shisha Tabak 50g | Tobacco & Cigarettes |
| 80 | Swiss Smoke Love69 Shisha Tabak 100g | Tobacco & Cigarettes |
| 81 | Swiss Smoke Love69 Shisha Tabak 50g | Tobacco & Cigarettes |
| 82 | Swiss Smoke Mango Passion Shisha Tabak 50g | Tobacco & Cigarettes |
| 83 | Swiss Smoke Orange Mint Shisha Tabak 50g | Tobacco & Cigarettes |
| 84 | Swiss Smoke Peach Shisha Tabak 50g | Tobacco & Cigarettes |
| 85 | Swiss Smoke Persian Apple Shisha Tabak 50g | Tobacco & Cigarettes |
| 86 | Swiss Smoke Tropical Fruit Shisha Tabak 50g | Tobacco & Cigarettes |
| 87 | Swiss Smoke Watermelon Chill Shisha Tabak 50g | Tobacco & Cigarettes |
| 88 | Swiss Smoke Watermelon Shisha Tabak 100g | Tobacco & Cigarettes |
| 89 | Swiss Smoke Watermelon Shisha Tabak 50g | Tobacco & Cigarettes |
| 90 | Tobac Tobacco pouches MIX Assort. 1pc | Tobacco & Cigarettes |
| 91 | VapeLounge Fairline Sweet Tobacco 40ml Shortfill Overdosed | Tobacco & Cigarettes |
| 92 | Wild Fire Cigarette Case Metal Optic Assort. 🚩A | Tobacco & Cigarettes |
| 93 | Zigarettenetui aus Chrom 100mm Assortiert 🚩A | Tobacco & Cigarettes |
| 94 | Zigarettenetui aus Chrom 80mm Assort. 🚩A | Tobacco & Cigarettes |
| 95 | Zigarettenetui Rainbow 🚩A | Tobacco & Cigarettes |

**Legend:** `NEW` = caught by today's Italian fix · 🚩A accessory over-gated ·
🚩B CBD-as-tobacco (loses THC-report) · 🚩C tobacco-substitute.
