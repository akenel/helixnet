# Banco — Customer Feedback Loop (Season 2 build spec)

*The "Word of Mouth" loop, teased in Born Once #08, built for real before Season 2 films it.
Status: DESIGN — discussed + decided 2026-06-24. We're ~85% there; this is the last mile.*

> Ethos: build it true, then film it (the "#02 of features"). No "just talk."

---

## 0. The one-line goal
A customer who gave only a **first name** (no email) can, from a **QR on their receipt**, complete a
**10-second survey about a product**, optionally attach a **photo or short clip**, and **earn loyalty
credit** — and their honest words become the **product's reputation**, which **Felix sees tied to
velocity** (what *helped*, not just what *sold*).

## 1. Decisions (locked 2026-06-24)
- **Channel:** **QR-scan is the spine** (works for everyone, no email, no app, no social API).
  **Telegram is the opt-in bonus** (push a survey link only to members who've started our bot).
  **Instagram = identity + organic reach only** — you CANNOT programmatically DM arbitrary IG users
  ("Instagram-auth is a mirage", per `docs/BANCO-COMMUNITY-BRIDGE-MECHANICS.md`).
- **Identity is CRM, not Keycloak.** Customers never log into the POS. Member = `CustomerModel`
  record (first name + optional `instagram`/`telegram` handle). Keycloak stays staff-only. *(Industry
  term for "lazy capture" = **progressive profiling**.)*
- **Gating:** **any customer record can leave a review**; **adding a handle unlocks the points
  payout** (gentle upsell — review freely, get paid when you become a "real member").

## 2. What already EXISTS (verified in code 2026-06-24 — reuse, don't rebuild)
- `CustomerModel` — tiers (Bronze→Gold), **credits_balance**, lifetime_spend, referrals, `instagram`,
  `telegram`, **`favorite_products`** (list).
- Credits economy — earning rules (first purchase +20, IG +10, Telegram +10, referral +50),
  **vouchers** (100cr=CHF5, 180=CHF10, 400=CHF25), ledger writes `balance_after`.
- **Sale attaches a customer** — `TransactionModel.customer_id` (FK) + checkout wiring
  (`pos_router.py:1726` sets `transaction.customer_id`). Cashier customer-lookup UI exists
  (`customer_lookup.html`, checkout view with tier/credits/alerts), plus a `generate-qr` endpoint.
- KB-contribution-for-credits concept ("knowledge is gold") — the spirit of review→points.

## 3. What to BUILD (the last mile)
1. **`Review` model** — `id, customer_id (nullable), product_id, transaction_id (nullable),
   created_at`, plus the survey answers (§4) and media refs (§5) and metadata (§6).
2. **Tokenized public survey page** — reached by QR, **no login**. The token encodes
   `(customer_id?, product_id, transaction_id)` so the review binds to the right person + product +
   purchase. Mobile one-pager. Submitting an answer is the whole interaction.
3. **Award credit on submit** — via the existing ledger; **only if the customer has a handle**
   (else: "add your Instagram to claim your points" — the upsell). "Make favorite" → push to
   `customer.favorite_products`.
4. **Reputation block on the product/catalogue page** — count, average ⭐, recent words, media
   thumbnails. ("See Larry. See Sally. See 'it worked.'")
5. **QR on the receipt** — token-bearing QR. **(Couples with the receipt cleanup — §7.)**
6. **Felix's dashboard: velocity + reason** — surface review signal next to velocity ("what helped,
   not just what sold").
7. **(Bonus) Telegram push** — for members opted into the bot, send the survey link after purchase.

## 4. The survey — "make it brilliant" (quick, honest, ~10s)
One mobile page, mostly taps. Proposed fields (all optional except the headline):
- **Did it work?** 👍 / 👎 / 🤔 not sure / ⏳ haven't had it long enough  ← the headline
- **Rating:** ⭐×5
- **Would you buy it again?** Yes / No / Maybe
- **Value for the price?** Great / Fair / Too expensive
- **Recommend to a friend?** Yes / No  ← *the key signal (NPS-style)*
- **⭐ Make it a favourite** (writes `favorite_products`)
- **A few words** (optional free text) + **photo / short clip** (§5)
- Submit → "Thanks — that's +20 credits" (or the upsell if no handle).

Design rules: no typing required to finish; one screen, no pagination; thumb-reachable; the reward is
visible up front ("10 seconds = 20 credits").

## 5. Media upload (Angel's add)
- Allow **one photo and/or one short video** with a review.
- **Limits:** start civilized — **video ≤ 25 MB / ≤ ~30s** (config), photo ≤ 10 MB. (Could go to ~2
  min later; keep the cap configurable.)
- Store off the app DB (object storage / disk path ref on the `Review`); transcode/thumbnail later.
- Moderation gate before a clip shows publicly on the product (manager review — reuse the RBAC).

## 6. Metadata to capture (Angel: "as much as possible")
On every submission: `submitted_at`, `customer_id` (or anonymous token), `product_id`,
`transaction_id`, **time-to-complete**, **device/user-agent**, **coarse geo** (IP region or, if
granted, geolocation — "where they filled it"), **referral source** (receipt QR vs Telegram vs
in-store), **answer-path** (order they tapped), completed-vs-abandoned. → analytics gold: *who, when,
where, how*, and survey conversion rate.

## 7. Receipt cleanup (coupled task — Angel flagged)
The QR lives on the receipt, so the receipt has to be right first:
- **Every receipt = a clean one-page PDF** (audit all receipt templates; `receipt.html`,
  `closeout.html`). No second blank page, no overflow (per the CLAUDE.md "1-pager" standard).
- Add the **survey QR** + one line: *"How'd it work? 10 seconds, earn 20 credits → scan."*
- Keep the non-prod TEST banner logic intact.

## 8. The velocity tie-in (the storyline + the design)
Felix's dashboard already shows velocity (units/day). Add the **reason layer**: per hot product, the
review signal — % "it worked", recommend rate, recent words. So the owner sees *demand AND the why
behind it*. This is the loop closing: sale → customer → review → reputation → the next sale → and the
owner watching all of it from the road. **That's the Season 2 thesis: two ladders, one currency.**

## 9. Build order (suggested)
`Review` model + migration → public tokenized survey page → award-credit/favorite wiring →
reputation block on product → receipt QR + one-pager cleanup → Felix velocity+reason → (Telegram
push). Build behind a flag; test on sandbox; film Season 2 against the REAL thing.

*Spec owner: Tigs + Angel. Pairs with the #08 finale (the teaser) and the series bible.*
