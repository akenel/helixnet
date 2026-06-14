# The Four Cards — La Piazza Runbook

One file, `LP-RUNBOOK.html`, drives all four. Pick env + device with URL params (or the
picker buttons in the header). Each card saves its own progress (separate localStorage key)
and exports its own dated `.txt`/`.html` report.

## The four

Served at `/static/lp-runbook.html`. Links inside are absolute, so any card can run from any
host — but open the mobile cards **on your phone**.

| Card | URL | Checks | Covers |
|---|---|---|---|
| **Staging · Desktop** | `…/static/lp-runbook.html?env=staging&device=desktop` | 10 | full pass + the newest build (guaranteed-card gate) |
| **Staging · 📱 Mobile** | `…/static/lp-runbook.html?env=staging&device=mobile` | 15 | the above + hamburger/logout, taps, no sideways scroll |
| **Prod · Desktop** | `…/static/lp-runbook.html?env=prod&device=desktop` | 8 | read-only confidence pass on what's LIVE |
| **Prod · 📱 Mobile** | `…/static/lp-runbook.html?env=prod&device=mobile` | 13 | the above + mobile responsive checks |

Quick links once deployed:
- https://staging-bottega.lapiazza.app/static/lp-runbook.html?env=staging&device=desktop
- https://staging-bottega.lapiazza.app/static/lp-runbook.html?env=staging&device=mobile
- https://bottega.lapiazza.app/static/lp-runbook.html?env=prod&device=desktop
- https://bottega.lapiazza.app/static/lp-runbook.html?env=prod&device=mobile

## The split (why four)

- **Staging is "at a different level"** — it carries unreleased work (the guaranteed-card
  escort), so its card is fuller. **Prod** gets a minimal read-only sanity pass — don't break
  what's live.
- **Mobile vs desktop** — the responsive surface is a separate failure mode (the hamburger
  hiding Logout at some resolutions, flagged in the 2026-06-14 prod hypercare). Mobile cards
  add those checks.

## What's automated vs. on these cards

Before any card is handed over, the machine gates run first (that's the rule —
[[feedback-maximize-automated-testing]]):
- `node tests/e2e/console-sweep.js <env>` — every page renders, no console errors / 5xx (read-only, safe on prod)
- `node tests/e2e/escort-probe.js staging` — drives the guaranteed-card flow (writes data → **staging only**)

These cards hold only what a machine can't judge: does it feel warm, does it read right,
does the small-screen experience actually work in your hand.

## Reports land in

`docs/testing/reports/{prod,staging}/` — drop the exported `.txt` (tracked) + `.html` (local).
The export filename already carries the env + device (`lp-runbook-prod-mobile-report.txt`).

> Older one-off per-feature runbooks (PROD-HYPERCARE, NEWUSER-WELCOME, etc.) stay for history.
> Going forward, these four cards are the standing set. The next level (#98) is generating a
> card straight from the Today board inside the Bottega — not yet.
