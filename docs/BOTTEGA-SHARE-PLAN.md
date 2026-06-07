# Bottega Share & Referral — The Build Plan

> *Every recipe output is a personalized example. The share is the advertisement.
> A stranger you'd actually want in your circle sees it, says "how do I get that for me?",
> signs up, builds their own, and comes back daily to rebuild themselves and their community.*
> That's the whole game. **Qualify the customer.**

**The catch:** shares can earn the sharer **credit** for converting a real new member — so
the reward engine is an attack surface (credit = brain-tokens = real money). Every share is a
**serialized, UUID-tracked, fully-logged object** so a scammer leaves fingerprints, and the
defenses are **self-healing** so Angel rarely has to dig by hand.

---

## Locked decisions (2026-06-07)

| Decision | Locked |
|---|---|
| Reward currency | **Tiered:** non-cashable **reputation points** (social/status) + **brain-tokens** (real, gated) |
| Points | **Never convert to tokens** — status only → faking them gains a scammer nothing |
| Token trigger | **Activation** (signup **+** ≥1 recipe run) — hardest to fake; a bot must do real work for nothing |
| Starter grant | **300 credits for everyone** on signup (already live via `ensure_starter_grant`) so they can play |
| Login | Social login **already exists** via Keycloak (Google/Facebook/GitHub). **Promote Google** (Android), **GitHub = techie bonus points**. Android-first. |
| Native iOS app | **Deferred** — web app + PWA covers iPhone via Safari; revisit only when Apple users ask ($99/yr not yet) |

---

## The two hands + the 5 W's (north star)

La Piazza is **two houses / departments, left hand washes the right**:
- **Bottega = the Workshop / the bench (PRODUCTION)** — where you *become* someone (CV, body,
  story, skills, AI mentors) and where the bench is *monitored* (body on the bench? working out?
  eating right? best reviews? — the `/compute/me` self-dashboard). This hand **ACQUIRES**: the share is born here.
- **La Piazza / the Square (SALES)** — where you *trade* (give/rent/sell/teach/host). This hand **TRANSACTS + RETAINS**.
- The share **borrows a member's real, personal work** as the billboard (the soul of "BorrowHood") —
  a person, personalized, beats a generic listing. **Bottega pulls them in; the Square keeps them.**
- **Keystone:** they run on separate identities today (BL-014) — `lapiazza.app/u/<slug>` 404s. "One
  washes the other" is literally true only once ONE identity flows through both hands (one realm / sync / merge).

**Structure everything by the 5 W's + H:**
| | maps to |
|---|---|
| **WHO** | the profile / identity — the storefront `/u/<slug>` |
| **WHAT** | offers, skills, listings — give/rent/sell/teach/host |
| **WHY** | purpose, goal, the dream, the 30-day arc — the onboarding heart |
| **WHERE** | location — city / proximity / HQ |
| **WHEN** | timing — events, schedules, availability, the journey |
| **HOW** | the recipes — procedure-as-code, the Workshop engine |

**Onboarding = the "Chinese menu":** "What do you want?" is the hardest question — many know "what
they DON'T want" better. Walk the W's and let people *pick from a menu* (wants AND don't-wants),
never a blank prompt. (Feeds the Onboard block.)

---

## North Star

- **Reward activation, not attention.** A click is noise and spoofable; a soul actually
  *playing in La Piazza* is the signal — the one thing you can't fake cheaply.
- **Gorgeous by default.** No share is ever imageless or dry (guaranteed image → Lupo Wolf;
  irresistible Ollama description = the meat & potatoes).
- **The share lands on a doorway, not a dead-end.** It opens an intro page that frames the
  whole imagination machine (give/rent/sell/skills/help-board/events) — the output is just
  *a feature*. Then one-tap login → AI onboards → first recipe = activation.
- **Lean on what exists** — the spine, the ledger, `item_views`, `/s/{id}`, the Block G → Backlog pipe.

---

## 🔥 BHT — why this order

We were about to armor a referral engine for a referral volume of **zero**. Abuse is a
rich-man's problem — it shows up *after* people fight to share. The real bottleneck isn't
scammers; it's **distribution + a frictionless doorway**. So: **build the bait + the door +
the landing, get it in front of five real humans, measure — THEN turn on rewards and armor
them.** The full anti-abuse design (below) is gold and stays on the shelf, ready — just not first.

*Correction logged: the door (social login) already exists — the work is polish + promotion +
ensuring it's wired on every env, not building it.*

---

## The Funnel

```
  BAIT            LANDING           DOOR            ONBOARD          ACTIVATE        REWARD
  gorgeous   ->   intro page   ->   1-tap     ->    AI asks 3 Qs ->  run 1       ->  points (always)
  share          (frames LP)       Google           + FAQ matrix     recipe          + tokens (gated)
                                   /GitHub          + 30-day                         to the sharer
```

---

## What already exists (extend, don't reinvent)

| Piece | Where | Reuse for |
|-------|-------|-----------|
| OG postcard | `/s/{id}` (share.html) — Wolf default cover, serial №, og tags | Share-1 (meaty + guaranteed image) |
| The spine | `bottega_sessions` (one event stream) | the output being shared |
| Compute ledger + 300 grant | `services/compute_service.py` (`post_ledger`, `ensure_starter_grant`) | reward payouts (pending→confirmed) |
| Prod analytics | `item_views` (anonymous, ~33k/30d) | honest click counting |
| Social login | **Keycloak IdPs — live on prod** (Google/FB/GitHub). ⚠️ **missing on staging + local realms** | the Door block |
| Backlog board | Block G feedback → `BacklogItemModel` | abuse review queue (dogfood) |
| Test gates | `make test` (pytest in container), `scripts/smoke-test.sh`, `tests/e2e/console-sweep.js` | every block |

---

## Data model (the serialized, trackable share)

```
share_links
  id (UUID, pk) · serial (human: SH-0001, Banksy-style) · session_id (FK -> the output)
  owner_username · channel (whatsapp|telegram|x|copy|qr)
  og_title · og_description (cached Ollama teaser) · og_image_url (resolved via ladder)
  ref_token (HMAC of owner+serial — unforgeable) · status (active|disabled|flagged)
  created_at · revoked_at

share_events                              (APPEND-ONLY — forensics)
  id · share_id (FK) · event_type (created|view|click_human|bot_skip|conversion)
  ip_hash (salted SHA-256, never raw) · ua_family · fingerprint
  referred_username · is_bot · meta (JSON) · created_at

referral_rewards                          (escrow state machine)
  id · share_id · owner_username · referred_username · kind (points|tokens) · amount
  state (pending|confirmed|clawed_back|denied) · reason · created_at · settled_at
```
Token payouts post to the **existing compute ledger** on confirm (one source of truth).

---

## The Blocks (re-sequenced: bait+door first, money second, armor last)

### Phase 1 — Get real humans through the door (NO payouts)

**Share-1 · Meaty OG + guaranteed-image ladder** *(branch: `feat/share-1-meaty-og`)*
Ollama 200–300 char irresistible teaser → cached `og_description` (owner-editable on preview).
Image ladder never fails: **object image → themed cover → Lupo Wolf default.** All og/twitter tags.

**Share-L · Intro landing page** (the share destination)
`/r/<serial>` doesn't dump the raw output — it opens a page that frames La Piazza (the
imagination machine), features the shared example, and has ONE clear CTA: *Get Started / Sign in*.

**Door · Polish + promote the login we already have**
Confirm Google/FB/GitHub IdPs on **prod ✓ / staging ✗ / local ✗** (wire the missing ones via
`scripts/lp_create_realm.py` + IdP config). Big "Continue with Google", "GitHub = +techie points".
**In-app-browser fix:** detect WhatsApp/Telegram/IG webview (breaks Google OAuth on iOS **and**
Android) → show *"tap ⋯ → Open in Safari/Chrome"*. **PWA + iOS Safari safe-list** (see below).

**Onboard · AI nudge + FAQ matrix + 30-day**
After login the AI asks: *got a CV? what work do you want? why are you here / why'd you click?*
Points to a simple **who-benefits / who-doesn't matrix** and frames the **30-day challenge**
(day 1 → week 1–4 → habit → the dream). 300 credits already in their pocket to play.

**Share-2/3-lite · Honest tracking (no money yet)**
`share_links` + `share_events` (serial + UUID + full who/when/how/where log). HMAC `ref`.
**Bot filter:** never count unfurl bots (WhatsApp/Telegram/Twitterbot/facebookexternalhit/
Slackbot/Discordbot/LinkedInBot). Human-click = app boots + UA not bot + not the sharer.
A "Shares" tab on `/compute/me`.

### Phase 2 — Turn on rewards, carefully (only once sharing is real)

**Share-4 · Conversion + activation gate** — carry `ref` through onboarding; conversion only on
first meaningful action (account + ≥1 recipe run). Double-sided: newcomer gets a small token bump.
**Share-5 · Reward ledger** — `referral_rewards` pending→confirmed; caps (daily/lifetime/diminishing);
dedup by KC id; self-referral block (account/IP/fingerprint); clawback on deleted/flagged.
**Share-6 · Self-healing anomaly engine** — rolling per-sharer scoring → soft throttle → auto-pause
+ flag + **file a Backlog item** (dogfoods Block G) → hard freeze until review.

### Deferred
**Share-7** dynamic Puppeteer OG image (branded PNG for text-only outputs). · **Native iOS** (when asked).

---

## iOS / cross-platform prep (be ready, don't over-build)

Audience is split: Sicily ≈ Android, Swiss/Canadian network ≈ iOS-heavy → plan for **~50/50**.

1. **PWA** — manifest + service worker + apple-touch-icon → iOS "Add to Home Screen", web push (iOS 16.4+).
2. **Safari safe-list** — inputs ≥16px (no zoom-on-focus), `dvh` not `vh`, `-webkit-` prefixes, test `position:fixed` + file inputs.
3. **In-app-browser OAuth** — the #1 cross-platform funnel killer; handled in the Door block.
4. **Test without an iPhone** — friend's phone or free cloud-Safari at milestones; apply the safe-list always.

---

## Anti-abuse summary (the "pitfalls so it's not worth their while")

1. Pay on **activation**, not click. 2. **Escrow + clawback.** 3. **Hard caps + diminishing returns.**
4. **Bot-UA filter** (biggest fake-click source). 5. **Identity + IP + fingerprint dedup.**
6. **Self-referral block.** 7. **Unforgeable attribution** (HMAC + serial + UUID + append-only log).
8. **Self-healing anomaly engine** auto-acts before a human looks. 9. **Forensics on demand** when Angel digs.
10. **Points are non-cashable** — the social layer can't be farmed for money.

---

## Privacy (we're in the EU)
Never store raw IPs — salted SHA-256 `ip_hash` only, discarded at the request edge. Short
retention on raw-ish signals; keep derived scores. Anonymous until a real account converts.

---

## Test discipline (every block, no exceptions)
1. Unit/integration (each guard must fire) → 2. `make test` (full suite in container) →
3. `scripts/smoke-test.sh` → 4. `tests/e2e/console-sweep.js` (anon + personas) →
5. **Human-green** (Angel clicks it for real — the canonical close).
One branch per block off `main`; staging from the branch; prod only after human-green.
*If one seal fails, check all the seals.*

---
*Started 2026-06-07 (Sunday, Sylvie asleep, pancakes pending). Two hands on the wheel.
Riding shotgun: Angel. Driving: Tigs. "Reward activation, not attention."*
