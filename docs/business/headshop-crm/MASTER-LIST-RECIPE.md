# 🐺 MASTER-LIST RECIPE — "Every Swiss Head-Shop, Enriched"

*The recipe to build + enrich the master list of Banco head-shop prospects. Hand this to an
ultracode/workflow session. Output feeds the CRM + the postcard campaign.*

---

## Goal
One structured row per head-shop in Switzerland (all cantons, or a region to start), enriched
enough to (a) qualify fit, (b) personalize a card + landing page, (c) prioritize. This is the
**master prospect list** — the fuel for the whole campaign.

## The catch that shapes it (read first)
- The postcard is a **one-shot pain filter** → the same first card goes to everyone; no second card.
- The reply is a **request for an invite to a live demo event** (waiting-list), not a 1:1 coffee.
- Public data estimates **FIT**; only the card's response measures **PAIN**. So enrichment
  *pre-qualifies + personalizes* — it is a hypothesis, not the truth. **A human reviews AI fields
  before anything is mailed** (never mail a wrong "fact" about a real shop).

---

## PHASE 1 — DISCOVER (find them all)
**Source:** Google Maps / Places, swept **by canton** (start Central CH: ZH, ZG, LU, SZ, UR, OW,
NW, AG → then expand). Supplement with industry directories (CannaTrade exhibitor lists, IG Hanf /
Hanfverband members, CBD directories) + known chains (e.g. Werners = many locations).

**Search terms (sweep all, DE + FR + IT):**
`Head-Shop` · `Growshop` · `Hanfladen` · `CBD Shop` · `CBD Laden` · `Smoke Shop` · `Vape Shop` ·
`Tabakladen` · `Kiosk` (filter) · FR: `magasin CBD` · `growshop` · IT: `negozio CBD` · `growshop`

**Dedup** by name+address; keep chain locations as separate rows but tag the chain.
**Phase-1 output:** candidate rows — name, address, city, canton, phone, website (from Maps).

## PHASE 2 — ENRICH (per shop, fan out)
For each candidate, gather (best-effort; **flag gaps, never invent**):

**Identity**
- `shop_name`, `legal_name` (Impressum), `owner_first_name` (site/Impressum/reviews — best-effort)
- `street`, `zip`, `city`, `canton`, `phone`, `email` (Impressum/site), `website`

**Signals (fit)**
- `google_rating`, `google_reviews_count`  (volume = traffic = more bookwork)
- `locations_count`, `is_chain`  (multi-shop = more pain = higher fit)
- `product_mix` (flags: headshop / cbd / grow / vape / tabak)  · `site_languages` (de/fr/it/en)
- `systemed_signal` = **basic** / **moderate** / **webshop**  (webshop/modern-till = *already sorted* = LOWER fit; bare-bones = paper-pen = HIGHER fit) · `has_webshop` (bool)

**Media** (for the personalized card + landing)
- `img_1_url`, `img_2_url` = their 2 best/most-prominent photos (website hero / first-page image
  first, then one more). **Fallback to a default asset if none found** (flag `img_default=true`).
- `logo_url` (from site header; fallback default, flag `logo_default=true`).

**Fit assessment (AI — from ANGEL-THE-SELLER's view: "is this a good Banco prospect?")**
- `swot` = compact: `strengths` / `weaknesses` / `opportunities` / `threats` (2–3 bullets each,
  about them AS A PROSPECT — e.g. weakness "likely still on paper", opportunity "multi-shop pain")
- `why_fit` = 2–3 bullets: why this is (or isn't) a Banco fit
- `pain_estimate` = short read on their likely bookwork/compliance burden
- `fit_score` = 1–5 · `priority_tier` = A / B / C
- `scoop_line` = ONE warm personalization hook for the card/landing ("inside scoop")
- `needs_human_review` = true if any AI claim is shaky (default true for anything shop-specific)

## PHASE 3 — PRIORITIZE + OUTPUT
- Rank by `fit_score` + reachability (region). Tier A = paper-pen + multi-shop + regulated + owner-run + not-systemed.
- Assign a campaign token per shop: `HS-<SHOPCODE>-<CARDNO>-<seq>` (e.g. `HS-HIGHSTORE-C1-0001`).
- **Output = one CSV/JSON row per shop, all fields above** → import into the CRM.

---

## Output schema (CRM columns)
```
token · shop_name · owner_first_name · legal_name · street · zip · city · canton ·
phone · email · website · google_rating · google_reviews_count · locations_count ·
is_chain · product_mix · site_languages · systemed_signal · has_webshop ·
img_1_url · img_2_url · img_default · logo_url · logo_default ·
swot_strengths · swot_weaknesses · swot_opportunities · swot_threats ·
why_fit · pain_estimate · fit_score · priority_tier · scoop_line ·
source · enriched_at · needs_human_review
```

## Honest limits (bake into the run)
- `email` + `owner_first_name` are often NOT public → best-effort, expect gaps, flag them.
- `swot`/`fit`/`pain` are AI **hypotheses** — the card's response is the real qualifier.
- Human eyeballs AI fields before mailing (a wrong detail to a real owner kills trust).
- Realistic CH universe: low hundreds of shops, not thousands.

---

## READY-TO-PASTE WORKFLOW PROMPT (ultracode)
> Build + enrich a master list of every head-shop / grow-shop / CBD / smoke / vape shop in
> Switzerland, starting with cantons ZH, ZG, LU, SZ, UR, OW, NW, AG. **Phase 1 (Discover):** fan
> out one agent per canton — search Google Maps + the terms [Head-Shop, Growshop, Hanfladen, CBD
> Shop, Smoke Shop, Vape Shop, Tabakladen, magasin CBD, negozio CBD] — return name/address/city/
> canton/phone/website; dedup by name+address across cantons (tag chains). **Phase 2 (Enrich):**
> pipeline each shop through: (a) scrape identity (owner first name, email, Impressum) + signals
> (rating, #reviews, #locations, product mix, site languages, webshop-or-not) + 2 best photos +
> logo (default fallbacks, flagged); (b) an AI fit pass that writes a compact SWOT from the
> seller's view, a why-fit, a pain estimate, a 1–5 fit score, a priority tier, and one warm
> scoop line — flag needs_human_review on any shaky claim. **Phase 3:** rank by fit + assign a
> token per shop; output one CSV row per shop with the schema in MASTER-LIST-RECIPE.md. Never
> invent facts — flag gaps. Cite sources per shop.

*Feeds: the CRM (built separately) + the postcard/landing personalization + the campaign board.*
