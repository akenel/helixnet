# Banco — Realm & Environment Model (the long-term shape)

*The north star for how shops, realms, and environments fit. Written 2026-06-20 from Angel's
"realm = a shop, not an environment" call. Keep it simple — this is the funnel, not a cathedral.*

## One line
**A realm is a shop.** An **environment** (dev / staging / prod) is just *where* that shop runs and
*whose* data it holds. A shop is **born in staging as a 30-day sandbox**, and **goes live by promoting
its realm to prod.**

## The three environments
| Env | Box | Purpose | Keycloak |
|-----|-----|---------|----------|
| **dev** | your laptop | developer playground | local KC (`keycloak.helix.local`), realm `kc-pos-realm-dev` |
| **staging** | Hetzner | the **sandbox / trial / QA** — where shops are born and tested | Hetzner KC (today shared with prod) |
| **prod** | Hetzner | **live** shops, real money | Hetzner KC (today shared with staging) |

## The shop lifecycle (the funnel)
1. **Onboard (staging).** The setup wizard creates the shop's realm from a **reference template** —
   the 3 reference roles (Cashier / Manager / Owner) + a few reference users they duplicate and play
   with. The **30-day trial lives here**. It's deliberately *not* good enough to run the real business
   on — that's the upsell to stewardship.
2. **Test / confirm.** Push changes to staging (easy on Hetzner) → run the **QA + Backlog + feedback**
   loop and the **HTML test sheets**. Users confirm it's OK, or Angel signs off via the test log.
3. **Go live (prod).** Promote the shop's realm to prod → real data, real money. Stewardship begins.

## The reference template (the wizard's Keycloak half)
A realm export JSON — `realm-reference-shop.json` — holding **Cashier / Manager / Owner** + sample
users. New shop = **copy, rename, import**. This pairs with `src/services/shop_setup_service.py`
(the *data* half: currency / VAT / language / store settings). Together they are the onboarding wizard:
one builds the shop's control data, the other builds the shop's realm.

## Felix / Artemis
His shop's realm = **`artemis`**. BUT: today the POC runs on **`kc-pos-realm-dev`** and it **works on
staging** — so leave it. The rename to `artemis` (shop-based naming) is a clean reorg step we do
**after the demo runs end-to-end**, never mid-test. It's "rename + copy a JSON + reimport," low risk.

## The "already logged in" dead-end — why, and the fix
Today every environment shares the one realm `kc-pos-realm-dev` on the shared Hetzner KC, so a session
from one host bleeds into another and Keycloak shows "You are already logged in" instead of bouncing
back. Two layers of fix:
- **App-side guard (do anytime):** if the POS already holds a valid token, send the user straight to
  `/pos` — don't bounce them to a KC login page at all. Kills the dead-end on re-login.
- **Structural (the clean split, later):** give staging and prod their **own** Keycloak (and DB). Then
  a shop's realm (e.g. `artemis`) exists in staging-KC (sandbox) and prod-KC (live) **independently**,
  and "go live" = export from staging-KC → import to prod-KC. Different KCs = no shared SSO = the bleed
  is gone permanently.

## Now vs later (don't over-build)
**Now (this weekend's POC):**
- Keep the working `kc-pos-realm-dev` setup on staging. **Finish testing the three bricks** end-to-end
  via `BANCO-STAGING-TEST-SHEET.html`. Get the demo green.
- App-side "already logged in" guard — ready when you want it.

**Later (deliberate, after the demo is green):**
- Realm reorg to shop-based naming (`artemis` for Felix); build the `realm-reference-shop.json` template.
- Make the app pick the realm by **shop** (hostname → shop realm), the same way it now picks the KC host.
- Eventually split staging and prod into their own Keycloak + DB.

> Rule of thumb: **realm = shop, environment = where + whose data.** A shop walks dev → staging
> (trial) → prod (live). Don't let environment names leak into realm names except for the dev
> playground.
