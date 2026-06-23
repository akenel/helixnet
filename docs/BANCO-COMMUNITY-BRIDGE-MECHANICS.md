# Banco × La Piazza — Community Bridge: Mechanics (spec)

*The buildable companion to `HELIXNET-VISION.md` §6. Every wire connects two things you already
own; the only new build is the bridge. **It all waits behind one keystone** (below) — so this is
"next, not now."*

---

## The keystone (prerequisite) — one realm
Banco and La Piazza on the **same Keycloak realm** (the `borrowhood`-realm consolidation, already
decided). One login, both surfaces, true SSO. **Nothing below works until this lands. Do it first.**

---

## 1. Onboarding — "my name's Sally" → a real identity, **no email forced**
**The problem:** members give a first name or an Instagram handle, not email/phone. Forcing email
kills it (privacy + friction, in a sensitive industry).

**The flow (progressive, points-as-carrot):**
1. **In-store:** capture name + *(optional)* Instagram handle. Member record created, points accrue
   **locally**. Fast, no login, no friction at the counter.
2. **The receipt carries a QR:** *"Claim your points + join."*
3. **Scan → La Piazza → passwordless claim:** the QR carries a **one-time token** (the QR *is* the
   credential) → Keycloak magic-link/OTP creates/links the account → the in-store member record
   **merges** with the community profile. One identity, one ledger. **No email ever typed.**
4. **Return logins:** optionally attach a social account (Google / Apple / Facebook) for convenience.

**Honest caveat — "Instagram login" is a mirage.** Meta deprecated third-party Instagram auth (Basic
Display API). So **auth = the QR magic-link first, Google/Apple/Facebook later**; the Instagram handle
is a **profile field** (for matching + community presence), *not* the sign-in method. Don't promise
"sign in with Instagram." Build the QR-claim; treat social as a later convenience.

---

## 2. The public page — **postcard on demand** (don't push the catalogue)
- A product earns a public page **only when there's a reason** — a member review, staff promotion, or
  a hot item. Most products never get one; the ~50 that matter do.
- When minted: La Piazza creates a **"postcard" page** keyed to the Banco product (shared id) — photo,
  name, the **KB knowledge** (the Clipper-flint gotcha), reviews / Q&A / upvotes, a QR. **Reuses the
  card muscle** you already have (UFA / ISOTTO).
- Surfaced via **QR** (receipt, shelf card, Instagram): *"Scan to review / join the discussion."*
- **Sync:** the card pulls identity (name / photo / description / KB) from Banco; it does **not** need
  live price — the page is about *knowledge + community*, not the till.

---

## 3. Currency & ladders — **local loyalty, global reputation**
- **Loyalty (buying)** = **per-shop** ledger (each Banco node its own).
- **Reputation (contributing** — reviews, answers, upvotes, KB**)** = **global** across La Piazza.
- Both climb a ladder (bronze → diamond / **legend**). A legend **buys, knows, and shares** — and is a
  legend across *every* shop on the network.
- **Moderation:** member content goes through the **existing review gate** (`kb_router` workflow) —
  legal (no medical claims) + spam. Non-negotiable in this industry.

---

## 4. Privacy (non-negotiable)
- **In-store purchases stay private and per-shop.** The community is **opt-in.**
- **Never** expose what someone bought without explicit consent. Community presence ≠ purchase exposure.

---

## Build order (each step small, each reuses what you own)
1. **Realm consolidation** — Banco + La Piazza, one Keycloak realm. *(the keystone)*
2. **QR-claim passwordless onboarding** — receipt QR → claim points → merge identity.
3. **Postcard-on-demand** — a product earns a public page; reuse the card muscle.
4. **Reviews / reputation on La Piazza** — the community engine already exists; wire products ↔ discussions.
5. **Social-login attach** — Google / Apple / Facebook for return convenience. *(later)*

## Problems to respect
Keystone first · chicken-and-egg (points carrot + staff-seeded cards + hot items) · moderation (legal) ·
privacy (opt-in, per-shop) · Instagram-auth is a mirage (use QR + Google/Apple/FB).

---

*"The community already exists on La Piazza. The shop already exists in Banco. The only thing missing
is the one login that makes them the same person — build that, and the rest is wiring you already own."*
