# Banco — environment colour band + user customisation (spec / decision)

**The decision in one line:** customisation has **three levels** that must not be confused —
the **environment** owns the safety signal (build now), the **shop** owns its brand (defer,
but real), and the **user** owns ~nothing (skip). Precedence: **Environment > Shop > User.**

| Level | What | Type | Verdict |
|-------|------|------|---------|
| **Environment** | sandbox vs staging vs prod | **safety** | **BUILD NOW** (system-set, tamper-proof) |
| **Shop / tenant** | Artemis's logo, fonts, accent | **branding (white-label)** | **DEFER to shop #2** (StoreSettings is the seam) |
| **User / cashier** | Pam's favourite colour | **vanity** | **SKIP v1** (accent at most, never the background) |

They all reach for the same pixel (the page look), so the rule is: the **environment** owns
the page background (it can only *mean* one thing — which box am I on); the **shop** owns its
brand *underneath* that; the **user** owns nothing that could muddy either.

---

## PART 1 — BUILD NOW: the environment band

**System-set, not user-editable.** Read once from `HX_ENVIRONMENT` (already an env var; the
build stamp already shows it). Render a persistent band on **every page** (it belongs in
`base.html`, alongside the existing status bar).

| Env | Treatment | Why |
|-----|-----------|-----|
| **sandbox** | LOUD — purple band, e.g. `🧪 SANDBOX · playground, resets anytime` | impossible to mistake for real |
| **staging** | LOUD — amber band, e.g. `⚠ STAGING · test data` | clearly not live |
| **prod** | CALM but CLEAR — thin deep-green top line + `● LIVE · Artemis` | never cry-wolf, but never fooled |

Design rules:
- **Asymmetry on purpose:** non-prod is loud (you always *notice* you're in a safe place);
  prod is calm but unmistakable (so a destructive action there always feels deliberate).
- One source of truth — `HX_ENVIRONMENT` → a `body` class / CSS var → the band colour.
  **No DB, no user input, no API.** Trivial and tamper-proof.
- Band shows on every page; never collapses/hides (it's a guardrail, not a toast).

**Acceptance**
- [ ] sandbox / staging / prod each render a visibly different, unmistakable band.
- [ ] The band is identical for every user — a cashier cannot change or remove it.
- [ ] It reads purely from `HX_ENVIRONMENT`; flipping that var flips the band.

---

## PART 2 — DEFER (but real): per-shop branding (white-label)

This is the **strategically real** one — "every head shop wants something special" is true,
and it's not user vanity, it's **white-labeling**: each *shop* (tenant) gets its own logo,
fonts, accent colour, so the same engine feels like *their* system. This is how
*"win one head shop → win the category → 100 shops"* becomes *100 shops that each feel like
theirs.* Special fonts included.

But it's a **shop #2 capability** — same bucket as German (below). You build the
*generalised* theming engine when there's a SECOND shop to theme. For **Felix (shop #1)**,
his brand is just set directly — no engine needed yet.

**The seam already exists:** `StoreSettings` is the per-shop config record and already holds
`receipt_logo_url`. Extending it with `brand_font`, `brand_accent`, `logo_url` (site-wide,
not just receipts) = the white-label path. **Admin-set per shop, never per user.**

**Precedence (critical):** the environment band (Part 1) sits ABOVE shop branding — a
white-labeled shop running on staging STILL shows `⚠ STAGING`. Brand may not paint over the
safety guardrail. **Environment > Shop > User.**

Defer trigger: build when shop #2 signs. Until then, Felix's brand = a few `StoreSettings`
values, hardcoded-simple.

---

## PART 3 — SKIP (v1): user profile / customisation

**Recommendation: don't build for v1.** Reasons:
- Low value for a shop with a few cashiers; high cost (a new profile model + preferences
  store + settings UI + per-user theming).
- It **fights the safety signal** — the one surface people reach for (the background) is
  reserved.
- Identity already exists without a profile: login, the cashier's **own drawer**, her
  **name on the receipt**. Shop-wide config already lives in `StoreSettings` (admin-only).

**If it's ever built:** make it an **accent, never the background** — an avatar, a
`Hi, Pam` greeting, maybe a small accent colour on buttons. The environment owns the page
background, permanently.

---

## Demo note
We film Day One on the **sandbox**, so a loud `🧪 SANDBOX` band would show in the video and
undercut the "this is your real shop" story. For the *recording*, either: (a) film with the
band suppressed / in a prod-look config, or (b) accept a subtle marker. Decide before the
shoot — internal safety tool vs. on-camera polish. (Doesn't block building Part 1.)
