# Banco CRM & Loyalty — Strategy

*Concept + phased plan. Drafted 2026-06-21 with Angel.*

## The big reframe: we don't have zero CRM — we have a disconnected one

The instinct ("there's no CRM, we don't know who the customer is") is right at the
**counter** — but it's wrong about the **codebase**. A full CRM/loyalty model already
exists; it was built (in the La Piazza/Bottega "CRACK community" era) and never wired
into the sale. We have a Ferrari engine with the driveshaft unbolted.

**What already exists (and is good):**
- `CustomerModel` — 35+ fields: handle + real name, QR member code, email/phone/socials,
  **loyalty tier** (Bronze→Diamond) + `lifetime_spend` + `tier_discount_percent`,
  **credits** ledger balance, birthday, language, favorites, referrals, visit/purchase
  counts, average basket, VIP flag, staff notes. (`src/db/models/customer_model.py`)
- `customer_router.py` — 10 working endpoints: create (with welcome credits), smart
  search (handle/@insta/email/phone), checkout view (tier, discount, birthday, upsell),
  full profile, update, manual credit adjust, credit history, recent visitors, record
  visit, generate QR.
- `CreditTransactionModel` — immutable, audit-ready credits ledger (earn/spend/adjust).
- `customer_lookup.html` — a working POS search/create UI with tier + credits display.
- Credit rules + tier thresholds already defined (1 CHF = 1 credit; 100 credits = CHF 5;
  Bronze 0 / Silver 200 / Gold 500 / Platinum 1000 / Diamond 2500; 5→25% tier discount).

**What's broken / missing (the real gap):**
1. `TransactionModel.customer_id` FK points to `users.id` (staff) — **wrong table**.
2. Checkout never attaches a customer — so no sale is tied to anyone.
3. Tier discount + credits earning are **not applied** at checkout.
4. `customer_lookup` UI exists but isn't wired into the checkout flow.
5. No purchase-history view per customer (trivial once #1–#2 are fixed).
6. Coupons: schema only, no model/endpoints.
7. **CRACK knowledge-base gamification** (write articles → earn credits → SEEDLING…ORACLE
   levels, peer review) is baked into the customer model — a community concept that may
   be over-built / off-target for a retail head-shop POS. **Keep or cut? (decision below)**

## What head shops / dispensaries actually use (research, cherry-picked)

Industry standard across Springbig, Alpine IQ, Flowhub, Cova, smoke-shop loyalty:
- **Points**: simple, 1 currency = 1 point, ~100 points = CHF/$5 reward. *(we already match this)*
- **Tiers**: spend-based, increasing perks; the good ones use **3** tiers, not 7. *(we have 5 — simplify)*
- **Auto everything at checkout**: enroll, earn, redeem happen automatically in the POS —
  "integrating directly with POS so enrollment and earning happen automatically." *(our #1 gap)*
- **Purchase history** the customer (and budtender) can see — drives upsell + service.
- **Birthday & referral bonuses** — easy retention wins. *(we have the fields)*
- **SMS/email re-engagement** — "you spent CHF 200 in 2 weeks, here's 15% off" — this is the
  core of Springbig/Alpine IQ. Needs a segment + messaging engine (or a manual export to start).
- **Online pre-order / build-a-cart / pay-in-store or online**, and self-service kiosks —
  "browse the menu, build the order independently, transfer to a budtender for checkout."
  *(this is exactly Angel's "shop at night, pay when you come in" idea)*

Takeaway: **our model already covers the first five.** The genuinely new surfaces are the
member self-service front (pre-order) and the marketing engine.

## Do we need a new module?

**No new back-office module.** The Customers/CRM module already exists — we *connect and
surface* it, we don't rebuild it. The only genuinely new thing later is a **customer-facing
surface** (member card / self-service / pre-order), which is a front-end on top of the
existing model, tied to the planned identity/Keycloak consolidation — not a new module.

## The phased plan

### Phase 0 — Wire it up (the unlock) · small, mostly fixing existing code
The highest-ROI work in the whole plan, because the model already exists.
- Fix `TransactionModel.customer_id` FK → `customers.id`.
- Attach a customer at checkout (add to the cart/checkout flow; `customer_lookup` already finds them).
- On checkout: auto-apply the tier discount, auto-earn credits (1/CHF), update `lifetime_spend`,
  `purchase_count`, `last_purchase`, `average_basket`, and `recalculate_tier()`.
**Delivers immediately:** every sale knows its customer; tiers + auto-discount + credits + the
data for purchase history all start working. This is the keystone.

### Phase 1 — The counter CRM (cashier-facing) · small/medium
- "Who's this?" at checkout: search or QR-scan the member → see tier, credits, **last purchases**,
  favorites, birthday flag, "CHF X to next tier."
- Redeem credits for a discount at the till; member receipt shows points earned + balance.
- Per-customer **purchase history** screen (their daily logs, reusing the shift-log pattern).
**Delivers:** the "it's Charlie, he's Gold, here's his history + 15%" experience.

### Phase 2 — The member card (customer-facing-lite) · medium
- A real **QR member card** (we have `qr_code`): scan to pull up the profile instantly at the till.
- A member "passbook" page (tier, points, history) the customer can view via a magic link/QR —
  **no full login yet**. Decide tier simplification (5 → 3) and finalize earn/redeem rates.
**Delivers:** customers see their own standing; faster repeat checkout.

### Phase 3 — The Community Catalog (customer-facing) · medium/large
**Decision (2026-06-21): pre-order / online checkout is CUT.** The Artemis Lucerne website already
sells online (delivery + in-store pickup). Banco must NOT rebuild commerce. Instead, Banco's member
surface is the thing the website *doesn't* have — the **community around the products.**

A member (via card/login) can BROWSE the same catalog the POS uses and:
- **Review & rate** items — badged **"Verified Buyer"** when their purchase history shows they
  actually bought it (Phase 0 makes this possible — far more trustworthy than anonymous web reviews).
- **Comment / ask questions**; CRACKs + staff answer → the knowledge base grows on the product page.
- **Upvote** reviews/comments/products → surfaces the best content + most-loved items.
- **Wishlist / favorites** (the `favorite_products` field already exists) — save items of interest.
- **Contribute knowledge** (the CRACK loop) → earn credits + level up.

**Wishlist is NOT a cart** (this resolves the earlier "cart" tension). It's engagement + a soft
intent signal, with one lightweight bridge to the till: at checkout the cashier can see the member's
wishlist for a natural upsell ("the X you saved is back in stock"), or the member shows their wishlist
on their phone and the cashier rings those items. No payment, no pre-order pipeline — the till and
the website remain the only two places money changes hands.

**Why this is the moat:** a no-money customer can browse, review what they've bought, upvote, wishlist,
ask questions, and contribute knowledge — earning credits + CRACK status **without spending a franc.**
That keeps them warm and turns them into content creators; when they do have money they buy (website
or store) already invested. The catalog becomes community-enriched — something Springbig/Alpine IQ/the
Artemis website all lack.

**Can / Can't / Should:**
- CAN: browse, verified-review, comment, upvote, wishlist, contribute knowledge, see own wallet/history.
- CAN'T: check out / pay here (website or till only); see others' private data; publish knowledge
  unmoderated (peer-review/staff gate).
- SHOULD: engage + contribute to earn credits/status even with no spend; bring the wishlist in-store.

### Phase 4 — Marketing & re-engagement · medium/large
- Segments ("spent > CHF 200 in 14 days", "no visit in 30 days", "birthday this week") →
  SMS/email offers; win-back; birthday blasts. Build light or integrate a Springbig-style tool.
- This is also where the **CRACK community** layer would live *if kept* — knowledge contributions,
  levels, peer review — as an engagement/gamification add-on, not core retail.

## DECISION (2026-06-21): keep CRACK — it's the differentiator

Angel's call: **keep the CRACK community layer and lean in.** Rationale: points + SMS loyalty
is a commodity (every dispensary platform has it); a **customer knowledge community** is the
thing competitors don't have. Head-shop customers are enthusiasts who love sharing knowledge —
turning them into contributors is a moat. So CRACK is **not** a Phase-4 afterthought; it's a pillar.

### The unifying model: TWO LADDERS, ONE CURRENCY
The cleanest way to hold both retail loyalty and community without confusion:
- **Spend Tier** (Bronze→…): *how much you buy.* Drives the automatic checkout discount. Money.
- **CRACK Level** (Seedling→Oracle): *how much you contribute.* Drives status, badges, early
  access, community standing. Merit.
- **Credits** = the **one shared currency** you earn from BOTH (buying *and* contributing) and
  spend on discounts/perks. This is the glue — a customer can be a small spender but an Oracle
  contributor, and still earn real rewards. Dual identity, one wallet.

Where the community shows up that competitors can't copy: **member-written product/strain
knowledge attached to catalog items** — so the catalog itself becomes community-enriched, and the
pre-order/self-service browsing experience (Phase 3) is richer than a plain menu. CRACK feeds the
catalog; the catalog feeds sales; sales feed credits; credits + status feed contribution. A loop.

### Phase re-cut (community woven in, not bolted on)
- **Phase 0** unchanged — wire the sale to the customer (earns credits from *buying*).
- **Phase 1** counter CRM — also surface CRACK level + badges next to spend tier at the till.
- **Phase 2** member card/passbook — shows BOTH ladders + credit wallet; "contribute" entry point.
- **Phase 3** Community Catalog — browse + verified-buyer reviews + comments + upvotes + wishlist
  (NO checkout; the Artemis website + the till are the only places money moves). The engagement heart.
- **Phase 4** (now "Knowledge engine & Marketing") — the full CRACK loop (submit→peer review→approve→
  feature→levels) + segments/SMS. The deeper knowledge contribution + outreach, layered on Phase 3.

## Identity & Enrollment — the mechanics (idiot-proof by design)

**The core distinction: a MEMBER is not a LOGIN.**
- **Membership** = a row in our app DB (`CustomerModel`): handle/name, optional phone, QR code,
  points, tier. Pam creates it in ~10 seconds. **No email, no password, no social — nothing.** They
  earn points + get the member discount immediately. A million members who never log in = just DB
  rows, zero Keycloak load.
- **Account (login)** = a Keycloak identity, needed ONLY when a customer wants to self-serve online
  (browse/review/wishlist from home). Optional upgrade, layered on top of an existing membership.

**Counter enrollment (Pam-led — the primary path):**
1. Mid-sale: "Are you a member?" → "No." → "Want to be? 10% off today." → tap **+ New Member**.
2. Type **name** (phone optional, birthday optional for the bonus). Create. ~10 seconds.
3. Hand them a **QR card** from the stack (the card = their member ID). The $20 sale attaches to
   them → member discount applies → credits score on checkout. Pam sees them on the list instantly.

**Self-claim (where login comes in — optional, later):**
- The QR card carries a code. If the member ever wants the online community surface, they scan the
  card on their phone → **"Claim your account" → Sign in with Google / Facebook / Instagram / email
  magic-link.** Keycloak brokers all of these natively (social login / identity brokering); that
  creates a Keycloak account **linked to their existing membership row.** No passwords, ever.
- Social = one tap, no typing an email. Magic-link = enter email once, click a link, done.

**Three enrollment patterns (all supported; A is the default):**
- **A — Pam enrolls (active):** the counter flow above. Promotes membership, instant-discount hook. ★
- **B — Self-enroll (the card):** "take this card, sign up on your phone now, instant discount" →
  card QR → social login → member created by the customer themselves.
- **C — Auto-enroll lite (passive):** on first purchase capture name/phone → a "lite" member →
  optionally text/email a claim link later. Lowest friction, least data; a fallback.

**What Pam captures + re-identification (the "which Larry?" problem):**
- A member record needs only a **label** — ideally the customer's **Instagram handle** (⭐ unique,
  freely given, carries their face, doubles as a future login), or just a first name. Everything else
  is optional: phone/email (most decline — don't push), birthday (for the bonus). The `instagram`
  field already exists on `CustomerModel`.
- **Re-identification is by the CARD, not the name.** Returning + has card (printed slip or phone QR)
  → Pam scans → exact record, no guessing. Forgot the card → fall back to search by Instagram/name,
  where an **avatar/photo helps Pam eyeball-match** — hence "more info = better" for the fallback only.
- **Avatar/banner/rich profile are SELF-SERVED** on claim (the customer uploads them online). Pam
  never takes a counter photo (Swiss FADP consent is touchy); the customer's own Instagram/avatar
  supplies the face.
- **Creating a member sends nothing / receives nothing** — it's just Pam typing; the row appears in
  our DB instantly. Email/social only enters if the customer later self-claims, and even then Pam
  gets no email — the login just links to the record she made.

**Card / claim-link delivery:** PRINT by default (a slip with QR + claim URL — needs zero contact
info, always works); optionally email/SMS the link if they gave one; or show an on-screen QR to
claim on the spot. "Take this if you want to log in, comment, score points, get better discounts —
but you don't have to" is the exact pitch.

**Prod/staging & scale:**
- Staff (Pam/Felix) already live in the POS Keycloak realm with roles — unchanged.
- Self-claimed customer logins live in a **customer-facing realm** (mirrored prod + staging so we can
  test with fake members). Keycloak handles 100k+ users comfortably. Ties to
  `[[lp-identity-consolidation]]` for which realm.
- **The CRM (membership) data lives in our DB, not Keycloak** — Keycloak only holds the login for
  members who self-claim. This keeps enrollment instant and offline-friendly.

**Sign-in methods (DECIDED 2026-06-21): Google + Facebook + Instagram + email magic-link.** No
passwords. One-tap social for most; magic-link fallback. Honest ops notes (setup tax, plan for it):
- **Google** — easy (OAuth client, minimal review).
- **Facebook + Instagram** — need a **Meta app + business verification + app review** (Instagram
  login now runs through Meta/Facebook login). Real one-time setup + ongoing maintenance. Worth it
  for a head-shop crowd (Insta-native), but not "free." Can ship Google+magic-link first, add Meta later.
- **Magic-link** — needs reliable **email sending (SMTP/provider)**. Cheap but must be set up + tested.

**Card format (DECIDED 2026-06-21): BOTH.** Physical QR cards (a printed stack at the till — natural
fit for **ISOTTO**, Angel's print partner) AND a digital QR (shown on screen / saved to Apple/Google
Wallet) for phone-first customers. The card code is the bridge to self-claim either way.

## The Contribution Economy (whiteboarded 2026-06-21)

**Governing principle: pay for VALUE, not VOLUME. Posting is free; being judged useful pays.**
Every farming problem comes from paying people to post. Pay only when the community/staff confirms
a contribution is good, and junk earns nothing. The economy hangs on **gates**, not on posting.

**Value ladder** (credits ≈ CHF 0.05 each; 100 cr = CHF 5):
| Contribution | Earns | Gate |
|---|---|---|
| upvote / wishlist / favorite | 0 (engagement) | — |
| ⭐ star rating | ~2 cr, daily-capped | **Verified Buyer** |
| short review | ~5 cr, daily-capped | Verified Buyer; auto-publish + flag/remove |
| accepted/upvoted Q&A answer | ~10–20 cr | upvotes or asker-accept |
| knowledge article submitted | 10 cr | — |
| …approved | **100 cr** | staff or trusted-CRACK review ← the prize |
| …featured | +250 cr | staff selects |
| + photos/video/lab | +25–100 cr | only on approval |

Headline: a no-money customer who writes one approved article earns CHF 5 of discount — knowledge
subsidizes their first purchase. The flywheel made concrete. (These numbers already exist in
`customer_schema.py` credit constants — we're confirming, not inventing.)

**Six anti-junk defenses (layered):**
1. **Verified Buyer** — review only what you bought (kills fake-review farming).
2. **Approval gate** — heavy credits land only after approval; junk submissions earn ~nothing.
3. **Daily/weekly caps** — no bulk-dumping (same cap pattern as the feedback widget).
4. **Up/down-votes + flags** — community buries junk; buried = unpaid.
5. **Reputation-weighted trust** — newbies queued; high-CRACK members auto-publish AND earn review
   rights → they become volunteer moderators because quality = their status/currency.
6. **Clawback** — approved-then-removed content reverses its credits (ledger supports adjustments).

**Protect margin — mix redemption** (don't let every credit become a discount):
- discounts (100 cr = CHF 5, the margin-cost lever) · early access to drops/limited/events (near-zero
  cost, high desire) · status & badges (free, often more motivating than money) · swag/free sample.

**Ties to the two ladders:** contributions build CRACK Level (status) + pay Credits (wallet); spend
drives Spend Tier (discount). A broke brilliant contributor climbs CRACK + earns credits + gets
status/early-access without spending — the strategic-core customer.

**DECIDED 2026-06-21:**
- **Gate = HYBRID.** Staff (Felix/managers) approve knowledge at first; as members climb CRACK,
  top levels (Blazing/Oracle) earn **review rights** and become volunteer moderators. Moderation
  scales for free; quality = their own status/currency.
- **Light contributions DO earn** — ⭐ rating ~2 cr, short review ~5 cr, **daily-capped, Verified
  Buyer only.** Drives high-volume catalog enrichment; caps + VB stop the farm.
- **Redemption = MIXED** — discounts (100 cr = CHF 5) + early access to drops/events + status/badges
  + occasional swag/sample. Protects margin; status motivates enthusiasts (not every credit hits margin).

→ **Contribution economy is SETTLED.** Remaining = rates fine-tuning + spend-tier count + compliance.

## Settled details (2026-06-21)

**Age & consent — checkboxes, not birthdates:**
- **Age gate (required):** a single **"✓ 18 or older"** checkbox. Pam ticks it at the counter
  (in-person judgment); online self-claim has a mandatory 18+ checkbox. NOT a birthdate.
- **Birthday (optional):** only for the birthday bonus; voluntary; separate from the age gate.
- **Marketing consent (optional, separate):** "☐ Yes, send me offers" — **off by default** (Swiss
  FADP needs explicit opt-in); only relevant if a contact channel was given.
- Phase-0 adds: `age_confirmed` (bool, required true), `marketing_consent` (bool, default false).

**Spend tiers — 3, conservative (don't give the store away):**
- 🥉 Bronze — every member: points (spend CHF 100 → CHF 5 back in credits) + birthday treat. No standing %.
- 🥈 Silver — ≥ CHF 500 lifetime: **+5%** member discount + early access.
- 🥇 Gold — ≥ CHF 2,000 lifetime: **+10%** + first dibs + surprises.
- Ceiling ≈ 10% standing + ~5% points for the best customer. One tunable knob (points value) if
  Felix wants it tighter. (Replaces the old 5-tier-up-to-25% model.)

**Moderation — staff-wide, no Felix bottleneck:**
- **Any staff approves** (Pam/Ralph/Felix): tap **"👍 Good"** → content goes live + pays the contributor.
- Felix/Ralph can **edit/improve/feature**; **soft-delete** junk (hidden + recoverable, never hard-lost).
- **Community self-regulates** (upvotes float good, flags sink bad); staff mostly bless what's risen.
- **Trusted CRACKs earn the approve button later** → scales without staff. Lifecycle: create → 👍 approve
  (any staff) → improve/feature → soft-delete → flag/clawback.

**Still-minor / later:** exact credit-rate fine-tuning; CRACK-level thresholds; content categories.
None block Phase 0.

## Lego language — the whole thing, plain (for Pam, and anyone)

Small bricks that snap together:

- **A member is just a name in our list.** Pam adds them in 10 seconds. No email, no password needed.
- **Everyone gets a card** (paper or on their phone). Next time, **scan the card → it's them.** Easy.
- **Buy stuff → earn points.** Spend CHF 100, get CHF 5 back to use later. The more you've spent
  over time, the bigger your member discount (Bronze → Silver → Gold).
- **Help out → earn more.** Leave a review of something you bought, answer a question, write a tip.
  Good stuff earns points too.
- **A grown-up says "👍 Good."** Pam, Ralph, or Felix taps Good and it goes live. Junk gets a thumbs-down
  and earns nothing. The best helpers ("CRACKs") earn the right to tap Good for others.
- **Points buy nice things:** money off, early access to new drops, status/badges, the odd freebie.
- **You don't have to do any of it.** Be a member, get your points, done. The online stuff (reviews,
  wishlist, avatar) is there if you want it — sign in with Google/Insta/Facebook or an emailed link.
- **One tick:** "I'm 18 or older." That's the only must.

The one rule under all of it: **doing good earns; spamming junk earns nothing.**

## Sources
- Gold Standard — Dispensary Loyalty Program Guide
- CannaPlanners — What is Alpine IQ; Sprout vs Springbig
- Heady — Alpine IQ vs Springbig
- Flowhub — Loyalty tools; Best Dispensary POS 2026
- Cova — Dispensary CRM; Springbig integration; Top POS 2026
- Springbig — Cannabis & Smoke-Shop loyalty
- Sweed / Paybotic / Cure8 — online pre-order, POS integration, self-service kiosks
- POS Nation, CigarsPOS, MoolahPoints, bLoyal — smoke/vape shop loyalty
