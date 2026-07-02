# Head-Shop Qualification Scorecard (CH batch 1 — 20 shops)

*Qualified 2026-07-01 from the Swiss commercial register + directories.
This scoring rubric is the spec for the recipe when we run 100+.*

## The gates (a lead must pass BOTH)

- **G1 — Working public website.** Password-protected, social-only, or no site = OUT.
- **G2 — Reachable named human OR a registered entity we can ask for by role.**

Fail a gate → `DROP`, no matter how good the reviews.

## The score (0–100, among qualified)

| Signal | Points | Why it matters |
|---|---|---|
| Named manager (from register) | +30 | The postcard lands on a desk, not a doormat |
| Personal email (`name@` / `owner@`) | +10 | Reaches the decision-maker, not a shared inbox |
| Reviews (busy = established + feeling the load) | up to +25 | Volume = real business = real paperwork pain |
| Registered GmbH/AG | +15 (Einzelfirma +8) | More admin burden; also a serious operator |
| Multi-location / chain | +12 | Consolidated VAT/reporting = the deepest pain (Banco sweet spot) |
| Regulated product load (CBD/cannabis/tobacco/vape/snus) | +8 | Age-gate + tax + reporting mandates = our wedge |

## The pain lens — two personas fell out of the data

**Owner-operator (drowning, easiest to reach):** sole proprietor, personal name+email,
answers their own phone. The paperwork pain is *personal* — every hour on admin is an hour
off the floor. → **Hanfbob (Nino), Paff Paff (Günes), Rudestore (Stephan), Zauber (Sebastian).**
Fastest warmth, fastest close. Start here.

**Multi-shop (scaling, biggest deal):** GmbH/AG, several locations, high reviews.
The pain is *structural* — VAT across branches, staff, consolidated closeout. → **Werners,
Stayhigh, Fourtwenty, Snushus, smokee.** Bigger contract, more decision layers, longer sell.

## Ranked A-list (website ✓ + named human ✓ — POSTCARD THESE)

| # | Shop | Manager | City | Reviews | Score | Persona |
|---|------|---------|------|---------|-------|---------|
| 1 | Werners Head Shop (chain) | Nicola Bösch (CEO) | Zürich +4 | 521 | 92 | multi-shop |
| 2 | Stayhigh GmbH | Emanuel Fischer | Reiden | 489 | 90 | multi-shop |
| 3 | Fourtwenty Trendshop | Michael Mosimann | Bern | 328 | 88 | multi-shop |
| 4 | Snushus AG | Denis Huber | Luzern | 167 | 80 | multi-shop |
| 5 | Hanfbob's | Nino Pianezzi | Affoltern | 128 | 78 | owner-operator ★ warmest |
| 6 | Zauber-Blüten | Sebastian Hampl | Bremgarten | 53 | 74 | owner-operator |
| 7 | Paff Paff | Günes Gezen | Zürich | 120 | 72 | owner-operator |
| 8 | Rudestore | Stephan Frei | Luzern | 87 | 68 | owner-operator |

**Werners is one contact (Nicola Bösch) for 4 of your 20 listings** — K4, K5, Limmatquai, Zug.
One relationship, one multi-location deal. That's the Banco multi-tenant story in a single lead.

## B-list — website ✓ but no name yet (ONE phone call qualifies them)

smokee (438 reviews, 6 shops), Highstore (260, franchise), Cannabis Sommelier (350, no phone),
Greenhouse/Greenweed (3 shops), Star-Buds (likely Stayhigh-linked), Headshop X Snustrend.
High-value — just need "Wer ist der Geschäftsführer?" answered on a call.

## Dropped — failed the website gate

- **Inside Headshop** — site is password-protected (has a name, Irene Haas, if ever revisited)
- **Alchemist** — no website + only 10 reviews
- **Blow Up** — Facebook/IG + gmail only, no real website

## Metadata that becomes the recipe (for the 100-shop run)

Each shop record should carry, with a source + confidence per field:
`name, chain, category, city, phone, street_address, postal_code, website(+is_live),
email(+is_personal), legal_entity, manager_name, manager_role, reviews, multi_location,
qualify_score, tier(A/B/DROP), persona`

The recipe computes `qualify_score` and `tier` from the rubric above — so 100 shops sort
themselves, and you print postcards top-down.
