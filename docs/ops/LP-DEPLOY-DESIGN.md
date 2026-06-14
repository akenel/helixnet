# `lp deploy` — declarative, reversible deploys (design + Rung ladder)

*Started 2026-06-14. Goal: a deploy is ONE command that refuses on bad
preconditions, records its own rollback point, does the thing, verifies, and
auto-reverts on red — and is the SAME command every time, so there is no SOP
left to remember. The command **is** the SOP.*

This replaces the "Deploy SOP" that currently lives in memory. A checklist in a
human head is a swallowed exception: it works until the one tired night it
doesn't, then fails silent and wide (that is how BUG-015 shipped to prod).

---

## The ladder (climb consciously — L0→L3)

| Rung | What | Status |
|------|------|--------|
| **L1** | `lp deploy <target>` — executable SOP that can't skip smoke + can't clobber box-local edits + auto-rollback | **THIN SLICE shipped 2026-06-14 (staging only)** — `scripts/lp_deploy.py` |
| **L2** | drift is a first-class loud signal (`lp status`); refuse-on-drift | partial (folded into L1 preflight) |
| **L3** | declarative target state (pinned release tag + reconcile) — GitOps-lite | YAGNI until 2+ operators (see [[future-idea-lapiazza-cli]]) |

---

## What shipped tonight (the thin slice — `scripts/lp_deploy.py`)

Staging target **only**. `prod` is a hard refusal until the prerequisites below
are met. Failure-mode-first, every step refuses loudly or reverses:

- **preflight** — report box-tree drift (behind/dirty); **refuse** if any *named*
  file carries uncommitted edits on the box (a checkout would destroy a possible
  prod hotfix — the #140 trap).
- **record** — capture the current `borrowhood:staging` image id = the rollback point.
- **deploy** — `git checkout origin/main -- <named files>` (the proven safe
  single-file pattern, **not** a blind `git pull`) + rebuild ONLY
  `borrowhood_staging` (`--no-deps`).
- **verify** — push THIS repo's `smoke-test.sh` to the box (so box drift on the
  smoke script can't give a false green) and run it against `staging`.
- **rollback** — on red verify or any build error: retag the recorded image +
  restore the named files to box HEAD, then re-smoke to confirm recovery.

Verified tonight on every NON-mutating path: `--help`, `prod` refusal (exit 1),
read-only drift+health run, the clobber-guard firing, the `--dry-run` plan
(prints exact rollback commands), exit codes. The live mutate+rollback path was
**deliberately not exercised** — see the blocker below.

---

## BLOCKER — RESOLVED 2026-06-14 (#141 fixed)

**The staging smoke gave a false-RED.** It *obtained* a token from the
`borrowhood-staging` realm @ `staging.lapiazza.app` (section 4 ✓) but the
`borrowhood_staging` container validates JWTs against `lapiazza-realm-staging` @
`staging-bottega.lapiazza.app` (its `BH_KC_REALM` / `BH_KC_URL`). Wrong issuer →
signature unverifiable → every authed endpoint returned `Authentication required`
while staging was healthy.

**Fix (chose option a — mint a token the app accepts):** point the staging
target's `KC_URL`/`REALM` at the issuer the app trusts. `borrowhood-web` is a
public client there, so no secret is committed. A *second* latent false-RED was
hiding behind it — the demo-login check expected 404 on staging, but the page is
gated on `(not debug AND env==prod)`, so staging legitimately serves it (200).
Both fixed; staging smoke is now **37 passed / 0 failed / exit 0** on the box.

**Lesson stands:** a verify that false-REDs is as dangerous as one that
false-GREENs — if auto-rollback had trusted this, every good deploy would have
rolled itself back. Verifying the verify before trusting it is the whole point.
Now that an absolute-green is trustworthy, the live mutate+rollback path can be
wired — still **exercise rollback first on a trivial file** (refinement #3).

---

## Refinements banked for the full Rung-1 build

1. **Smarter clobber guard.** Today it refuses if a named file is "dirty vs box
   HEAD" — but a file put there by a *prior safe deploy* (origin/main content on a
   17-behind tree) reads as dirty too, so re-deploying the same file is refused.
   Fix: compare box file content against **origin/main**; proceed if box already
   equals origin (idempotent re-deploy); refuse only if box differs from **both**
   HEAD and origin (a genuine local edit / hotfix).
2. **Prod target** — same shape + extra guards: require a clean confirm with the
   commit SHA echoed back; snapshot DB or confirm migrations are
   forward-only+idempotent (see [[lesson-migrations-not-gated-behind-debug]]);
   wider verify (prod smoke + a console-sweep); a `--canary` that holds at "built
   but not switched" for a manual eyeball.
3. **Exercise the rollback first, safely.** The rollback path is the most
   important and least-tested. First real use should be a *trivial* file so the
   retag+restore+re-smoke loop gets its baptism on something harmless.
4. **`lp status`** as its own verb (the no-files read-only run, promoted) — drift
   + container health on demand, the standing #140 watch.
5. **Make it a real `lp` CLI** — `deploy` / `status` / `preflight` / `smoke`
   subcommands; one entry point. The [[future-idea-lapiazza-cli]] seed.

---

## Stack facts (verified 2026-06-14, baked into the tool)

- box `root@46.62.138.218`; compose dir `/opt/helixnet/hetzner`
- staging svc `borrowhood_staging`, image `borrowhood:staging`, builds from the
  diverged tree `/opt/helixnet/BorrowHood` (#140; 17 behind / 37 dirty and growing)
- build: `docker compose -f docker-compose.uat.yml -f docker-compose.staging.yml --env-file uat.env up -d --build --no-deps borrowhood_staging`
- verify: `bash scripts/smoke-test.sh staging` (BASE `https://staging.lapiazza.app`)
- prod svc is `borrowhood` (separate) — untouched by the staging tool
