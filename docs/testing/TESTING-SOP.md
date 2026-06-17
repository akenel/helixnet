# Testing SOP — La Piazza / Bottega

*How a change earns its way from staging to prod. Three gates, in order. No skipping.*

Two of the gates are machine checks (fast, run every deploy). The third is a **human
sanity check** — a person actually using the feature like a user would, and signing off.
Machines confirm it didn't break; a human confirms it's actually *good*.

---

## The three gates

| # | Gate | What it catches | Tool |
|---|------|-----------------|------|
| 1 | **Smoke** | dead endpoints, 500s, auth broken, regressions | `scripts/smoke-test.sh staging\|prod` |
| 2 | **Console-sweep** | client-side render errors, blank panels, mixed-content | `tests/e2e/console-sweep.js` (anon + 3 personas) |
| 3 | **Human sanity check** | "it works but feels wrong" — UX, copy, the thing a user actually does | **fillable HTML sign-off sheet** (this folder) |

Gates 1–2 run on **staging first**, then again on **prod after deploy**. Gate 3 runs on
staging before sign-off, and (for anything user-facing) once more on prod as the final
human green-light.

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
