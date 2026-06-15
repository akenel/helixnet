# DEV-TECHNIQUES — how we build so it stays sane

*One canonical page. Read it in five minutes; it links out to the deep lessons.
If a rule here and a memory disagree, this page wins — fix the memory.*

Last reviewed: 2026-06-14 (the night-shift cleanup).

---

## The one idea: machinery, not vigilance

Quality that depends on *remembering* the SOP works until the one tired night it
doesn't — then it fails silent and wide. That is exactly how BUG-015 shipped to
prod. So the goal is always to move a rule **out of our heads and into something
that can't be skipped**: a committed test, a tool that refuses, a gate that runs
itself. A checklist in a human head is a swallowed exception.

Every rule below is here because we paid for it once already.

---

## 1. Verify the verify

A green that's actually broken (false-GREEN) and a red that's actually fine
(false-RED) are *equally dangerous*. Before you trust a gate to make decisions,
confirm the gate means what it says.

- Live proof (found + fixed 2026-06-14): `smoke-test.sh staging` reported **RED
  while staging was healthy** — it minted the auth token from the wrong realm, so
  the app rejected it. If `lp_deploy`'s auto-rollback had trusted it, every good
  deploy would have rolled itself back. *Two* latent false-REDs were hiding there
  (auth realm + a stale demo-login expectation). → #141,
  see `memory/lesson-staging-smoke-false-red.md`.
- **Machine-green is not human-green.** smoke + console-sweep + pytest can all
  pass while a UI feature renders nothing (a silent template miss throws no
  error). For UI work the human eyeball is a *mandatory* second tier. See
  `memory/lesson-machine-green-is-not-human-green.md`.

## 2. No verification lives in /tmp

If you wrote a script to prove something works, it's either worth keeping or it
isn't. Promote it to a committed test, or delete it. Nothing that guards
behaviour is allowed to evaporate when the shell closes.

- **Pure-logic tests run on every pass** (no DB, no network) — they're free, so
  there's no excuse to skip them.
- **DB / integration tests self-skip** when the resource is unreachable (probe
  with `SELECT 1` → `pytest.skip`), so a missing DB never turns the suite red.
- Run the suite **in the app container**, not the host `.venv` (the venv is the
  aux toolbox with no fastapi). See `memory/broken-pytest-gate-email-validator.md`.

## 3. Deploy discipline

- **`scripts/lp_deploy.py` is the only blessed deploy path.** It can't skip the
  smoke gate and can't clobber box-local edits. Full design + roadmap in
  `docs/ops/LP-DEPLOY-DESIGN.md`; pointer in `memory/lp-deploy-tool.md`.
- **Staging first, always. Prod only on explicit Angel sign-off** — no
  exceptions, not even "low-risk." See `memory/feedback-staging-before-prod.md`.
- **Never blind-`pull`/`reset` the box BorrowHood tree.** It runs uncommitted
  code (#140). The only safe single-file deploy is
  `git checkout origin/main -- <file>` + rebuild the one target container. See
  `memory/borrowhood-box-divergence.md`.
- **Commit and push only when Angel asks.** Doing the work ≠ landing it.
- The deploy SOP itself (commit → deploy → smoke → *read the output*) lives in
  `MEMORY.md` under "Deploy SOP — MANDATORY" until lp_deploy fully absorbs it.

## 4. Push complexity into data, not code branches

The 98% branch the code for every new case. We push the variation into
data/structure and keep the code dumb, small, and identical:

- the model is a *field* (BYO-brain: a recipe names its own brain), not a fork
- a recipe / product line is a *dict row*, not a new module
- edition info is `item.attributes["edition"]`, not an `if is_art:` ladder
- one event spine (`bottega_sessions`) carries messages, notifications, history

A new feature should usually be a new row, not a new branch. See
`memory/lp-the-design-factory.md` and `memory/lp-everything-is-a-service-interface.md`.

**UI corollary — one component, not N copies.** Every repeated piece of markup
(avatar, user-card, badge) lives ONCE in `templates/components/_*.html` and is
registered as a Jinja global (see `pages/_helpers.py` → `avatar`), so it's
`{{ avatar(...) }}` everywhere with no import. Client-rendered (Alpine) lists
share one JS helper (`window.lpAvatar` in base.html). If you ever edit the "same"
thing in more than one file, stop — make it a component. The 2026-06-14 avatar
fix was a 14-file edit *because* this layer didn't exist; now it's one file. This
is the structural cure for the "check all the seals" duplication.

## 5. Failure-mode-first

Design the failure before the feature. For anything non-trivial, answer in one
line: **"this breaks when ___, and we find out because ___."** If the "find out
because" is "a user notices," make it louder.

- Silent success is the worst bug class. Loud failure beats quiet wrong.
- Fix the *class*, not the instance — "if one seal fails, check all the seals"
  (CLAUDE.md). One bad endpoint → audit the siblings.
- Schema/setup must run on **every** env, not gated behind debug — staging runs
  debug=false and a debug-gated migration silently never ran (search 500'd). See
  `memory/lesson-migrations-not-gated-behind-debug.md`.

## 6. Repo hygiene (kills drift at the source)

- **Filenames are chosen, never derived from a heading.** The garbage
  `` UPLOAD - `clip.mp4` · **Captions:**… .md `` files came from dumping a
  markdown title into a filename. Use short kebab/convention names; a tool that
  writes files must name them deterministically.
- **Heavy media stays out of git (helixnet).** `.gitignore` scopes blueprint /
  marketing / test-script binaries; sources (`.md`/`.html`/`.srt`) stay tracked.
  Keep `git status` honest — a noisy status hides the one real change.
  - *Open policy fork:* BorrowHood **tracks** episode media by convention (290+
    files). That bloats history forever. Decide deliberately (git-LFS / external)
    before the next big episode kit — don't let it grow by default.
- Generated artifacts (PDFs, workflow scripts, run reports) are ignored, not
  committed. If a generated thing becomes a keeper, force-add it on purpose.

## 7. The gates, and what each one catches

Run these before handing Angel anything. See
`memory/test-gates-smoke-and-console-sweep.md`.

| Gate | Command | Catches | Blind to |
|------|---------|---------|----------|
| pytest | `make test` (in container) | logic, contracts, regressions | rendering, real UI |
| smoke | `scripts/smoke-test.sh <env>` | HTTP/route/health, API shapes | client-side JS; auth false-REDs on staging (#141) |
| console-sweep | `tests/e2e/console-sweep.js` | browser console errors, blank renders (anon + 3 personas) | logic correctness |
| human | open it, click it | "the button is dead", silent empties | nothing — it's the canonical close for UI |

No gate alone is "done." For UI, human is mandatory.

---

## Known gate gaps (don't trust blindly until closed)

- **CI alarm is still GitHub-native** (BorrowHood). The gate is green and
  trustworthy again (#147), but a future red only shows as a buried email + a red
  ✗ in the web UI — which is how it stayed red for 5+ days last time. The loud
  upgrade (Telegram via telegram-tigs, ~5-line workflow step) is banked, not
  built. Until then, *glance at `gh run list` after a push.*

*Closed:* **#141** (staging smoke false-RED) — fixed 2026-06-14: smoke now mints
its token from the realm the staging app actually trusts; staging is a clean
37/0 green, so lp_deploy auto-rollback can trust an absolute green.

*Closed:* **#140** (BorrowHood box divergence) — reconciled 2026-06-15 via a
*verified* `git reset --hard origin/main` (full-tree diff proved only 1 runtime
file changed), tagged release `prod-2026-06-15-0517`, prod + staging both 37/0.
The verified-reset playbook lives in `memory/borrowhood-box-divergence.md`.

*Closed:* **#147** (BorrowHood CI red-as-wallpaper) — green again 2026-06-15
(c49a370). The 5 stale homepage tests were de-brittled to assert
structure/behaviour, and a seed-realism gap (`trust_score` NULL on fresh seeds)
was fixed at the source. Lesson: `memory/lesson-ci-red-as-wallpaper.md`. NOTE:
verifying the 5 in-container was *not* enough — CI's fresh seed differs from the
real DB; machine-green-in-container ≠ CI-green (verify the verify, again).

*Closed:* **#148** (helixnet box checkout drift) — reconciled 2026-06-15. The
box's `/opt/helixnet` was 0 ahead / 10 behind, all docs/scripts/tests (no `src/`
runtime). Verified reset to origin/main (`../src` is volume-mounted but the
tracked diff was empty, so zero runtime change — no rebuild), then pinned box ==
origin. Prod + staging 37/0. Both box repos (BorrowHood + helixnet) now run a
known commit. Untracked box-local overrides/backups (`banner.override.yml`, env
backups) were left untouched, not mine to delete.

When you close one, move it to *Closed* with the date — keep the page honest.
