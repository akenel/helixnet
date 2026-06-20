# SOP — Banco POS Testing Standard Procedure

*Standard Operating Procedure for testing the Banco / HelixPOS till.*
*Version 1.0 — 2026-06-20. Owner: Tigs (technical+functional), Angel (final look-and-feel).*

---

## 1. Purpose

Stop finding bugs by hand on staging. Every change to the POS — money math, stock,
flows, sessions — must pass an automated suite **before** Angel ever looks at it.
The "logs out after submitting a sale" bug is exactly the kind of thing a flow test
catches in 5 seconds; we found it by accident, on staging, with the human. Never again.

This is the seal-inspection lesson in software: **when one thing fails, a test should
check all the things with the same failure mode.**

## 2. The division of labour (who tests what)

| Layer | Who | What it proves | Where |
|-------|-----|----------------|-------|
| **API regression** (pytest) | Tigs, automated | Money math, VAT, stock, reports, RBAC | local first, then staging |
| **E2E flow** (Playwright) | Tigs, automated | Real browser: login → sale → receipt → **still logged in** → nav | local first, then staging |
| **Look & feel** (test sheet) | **Angel**, by hand | Spacing, colours, wording, "feels right" | **staging only**, last 1% |

Tigs does 99%. Angel verifies the final 1% — and only the visual/UX part, never the
plumbing. If the plumbing isn't green by machine, it does not reach Angel.

## 3. The iron rule: test-first, before-and-after

**Before changing any POS code:**
1. Write (or confirm) a test that captures the **current** behaviour — the "before".
2. If it's a bug, the test should FAIL on the current code (red = bug reproduced).
3. Make the change.
4. The test goes GREEN (after). The before/after is now permanent regression cover.

For a *new* feature: write the test for the intended behaviour first (it's red because
the feature doesn't exist), then build until green.

**No code change ships without a test that would have caught its absence.**

## 4. The pipeline (every change follows this, no exceptions)

```
   LOCAL                          STAGING                    ANGEL
   ─────                          ───────                    ─────
1. write/confirm test    →  4. deploy to staging tree  →  6. Angel runs the
2. change code              5. run SAME suite against       robust test sheet
3. run suite GREEN local       staging, GREEN               (look & feel only)
                                                            7. Angel PASS → prod
```

- **Build everything on local** (`helix.local`). Run it. Test it. Be happy with it.
- **Push to staging.** Run the **same** suite against staging end-to-end. Green again.
- **Only then** hand Angel a test sheet for the final visual pass.
- **Prod only on Angel's explicit PASS.** (Unchanged hard rule.)

## 5. How to run

```bash
# API regression (black-box HTTP, needs the stack up + Keycloak)
source .venv/bin/activate
make test-pos                      # local   (helix.local)
make test-pos ENV=staging          # staging (staging-banco.lapiazza.app)

# E2E browser flow
npm run test:pos:dev               # local
npm run test:pos:staging           # staging
npm run test:e2e:report            # open the HTML report (traces/screenshots/video)
```

Auth: tests mint a **real Keycloak token** via direct-access-grant
(`helix_pos_web` is a public client, grants enabled) — real RBAC, no mock bypass.
All test users = `helix_pass`.

## 6. The essential tests (the minimum bar — must always be green)

**API (`tests/pos/`):**
- `test_pos_vat.py` — inclusive Swiss VAT: a CHF 89.90 item rings a **total of 89.90**
  (not 97.18), contained VAT ≈ 6.74. Multi-item. Discount. **Locks the 2026-06-20 fix.**
- `test_pos_stock.py` — catalog returns `stock_quantity`; checkout deducts stock by qty
  sold; stock never goes negative.
- `test_pos_reports.py` — daily summary carries `vat_total`; Banana CSV requires auth and
  has headers `Date,Description,Income,Expenses,Account,VatCode`; methods sum to total.

**E2E (`tests/scenarios/pos-cashier-flow.spec.ts`):**
- Full cashier flow: login → catalog (shows stock) → add → checkout → receipt.
- **Session survives the sale** — after submit, the cashier is STILL logged in and lands
  on the receipt, NOT bounced to the Keycloak login/logout screen. (The open bug.)
- Navigation: catalog ⇄ sale ⇄ receipt with no back-button dead-end.
- Receipt shows the real product name + `incl. VAT (8.1%)` line.

## 7. When a test goes red

1. Read the failure + the trace/screenshot (Playwright saves them on failure).
2. Reproduce locally.
3. Fix the **root cause**, not the symptom. Then ask the seal question: *what else has
   the same failure mode?* Add tests for those too.
4. Green local → green staging → hand to Angel.

## 8. Definition of done (a POS change is "done" when)

- [ ] A test exists that would fail without the change (before/after proven).
- [ ] Full API suite green on **local**.
- [ ] Full E2E suite green on **local**.
- [ ] Same suites green on **staging**.
- [ ] Robust test sheet handed to Angel for the visual 1%.
- [ ] Angel PASS on staging.
- [ ] (Only now) deploy to prod per the Deploy SOP.

> "If one seal fails, check all the seals."
> The test suite is how we check all the seals every single time.
