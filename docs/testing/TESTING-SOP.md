# Testing SOP — La Piazza / Bottega

*How a change earns its way from staging to prod. Three gates, in order. No skipping.*

Two of the gates are machine checks (fast, run every deploy). The third is a **human
sanity check** — a person actually using the feature like a user would, and signing off.
Machines confirm it didn't break; a human confirms it's actually *good*.

---

## The gates

| # | Gate | What it catches | Tool |
|---|------|-----------------|------|
| 1 | **Smoke** | dead endpoints, 500s, auth broken, regressions | `scripts/smoke-test.sh staging\|prod` |
| 2 | **Console-sweep** | client-side render errors, blank panels, mixed-content | `tests/e2e/console-sweep.js` (anon + 3 personas) |
| 2b | **O2C end-to-end ("the works")** | the full sell-side journey actually holds (login → catalog → cart → checkout → payment → receipt) | **`make e2e`** → `scripts/testing/e2e_sandbox.js` |
| 3 | **Human sanity check** | "it works but feels wrong" — UX, copy, the thing a user actually does | **fillable HTML sign-off sheet** (this folder) |

Gates 1–2b run on **staging first**, then again on **prod after deploy**. Gate 3 runs on
staging before sign-off, and (for anything user-facing) once more on prod as the final
human green-light.

### Gate 2b — Order-to-Cash (O2C) end-to-end

`make e2e` drives a **real browser** (Puppeteer/Chrome) through the whole sell-side cycle and
asserts each journey GREEN/RED, printing a summary table and exit 1 on any RED (so it gates a
pipeline). It is a **happy-path verification** (the works hold), not an adversarial fuzz.

```
SIGN-IN → BROWSE (catalog) → FILTER (grouped dropdown) → FIND (fuzzy search)
        → IDENTIFY (scan-by-EAN) → CART → CHECKOUT → PAYMENT → RECEIPT  (+ camera fallback, manual-product sanity)
```

- **Parameterized** — defaults to sandbox; point it at any env:
  `make e2e` or `E2E_BASE_URL=https://staging-banco.lapiazza.app E2E_USER=… E2E_PASS=… node scripts/testing/e2e_sandbox.js`
  (env vars: `E2E_BASE_URL`, `E2E_USER`, `E2E_PASS`, `E2E_REALM`, `E2E_KC_URL`, `E2E_OUT`, `E2E_HEADFUL`).
- **Self-cleaning / idempotent** — every run refunds its own test sale and deactivates its
  throwaway `LZ-` product, so a nightly/CI run leaves **no residue**. Safe to re-run.
- **Screenshots** of each key state land in `$E2E_OUT` (`e2e_*.png`).
- **Future P2P:** the buy-side sibling (Procure-to-Pay: receiving → restock → supplier → pay)
  plugs in as `scripts/testing/e2e_p2p_sandbox.js` + `make e2e-p2p`, reusing the same harness
  shape (config block, `journey()` helper, GREEN/RED table, self-cleaning teardown).

> Note: `smoke-test.sh hetzner` (the on-box self-signed target) is currently broken — it
> aborts on the first TLS check. Verify prod via the **public hostnames** instead
> (`https://bottega.lapiazza.app/...`). See memory `test-gates-smoke-and-console-sweep`.

---

## Gate 3: the human sanity-check sheet

A short, **fillable** HTML form: numbered steps, expected result per step, a Pass box and
a Notes field per step, an overall PASS/FAIL + signature, and a **"polish notes for the
next batch"** section so cosmetic feedback is captured at the moment it's noticed.

**Why a form and not just "click around":** it makes the check *structured and repeatable*
(same steps every time), gives an **official sign-off record**, and turns the tester's eye
into a backlog — the polish notes feed the next cosmetic pass. It's the human equivalent of
the seal inspection: when one thing works, walk every step and look for what else needs love.

### How to make one (2 minutes)

1. Copy `TEST-SHEET-TEMPLATE.html` → `FEATURE-NAME-TEST-SHEET.html` in this folder.
2. Replace the placeholders: `__FEATURE__`, `__NNN__` (next doc number), `__ENV__`,
   `__BUILD__` (commit SHA), `__DATE__`.
3. Write one `<tbody>` row per check: **Step** (do this) → **Expected result** (see this).
   Mark the make-or-break check with `class="step big"` so it stands out.
4. Open it in a browser, hand it to the tester.

### How to fill it (important)

Fill it **on screen** — type in the fields, tick the boxes — **then** click
**🖨️ Print / Save as PDF**. A browser-printed PDF *freezes* the form fields, so a blank
PDF can't be filled in most viewers. Always complete it in the browser first.

### Where filled copies go

Archive the signed PDF under `docs/testing/archive/`. The blank template and the live
per-feature `.html` stay in `docs/testing/`.

---

## When each gate is required

- **Backend-only / internal change:** gates 1–2. Gate 3 if behaviour is observable.
- **Any user-facing change (UI, copy, a recipe, a flow):** all three. Gate 3 is mandatory
  before prod sign-off — this is the one that catches "ships, but cheap."
- **Infra/ops only (compose, volumes, env):** gate 1 + a targeted manual check; gate 3 if
  it changes what a user sees or can do (e.g. media durability → reopen a saved item).

---

## Sign-off rule

Staging green on all required gates → ask Angel for explicit sign-off → deploy to prod →
re-run the gates on prod. Never skip the prod re-run; never deploy to prod without the
explicit human go (memory `feedback-staging-before-prod`).

*First sheet: `VOICEOVER-JOBHISTORY-TEST-SHEET.html` (TEST-VO-005). All 8 steps passed,
prod, 2026-06-17.*
