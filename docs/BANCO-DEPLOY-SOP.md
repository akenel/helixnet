# SOP — Banco Deploy Through the Loop

*Standard Operating Procedure. 2026-06-29. How to ship a Banco change from sandbox → staging →
prod safely, every time. Born from a real session where **assuming** burned us and **proving**
saved us. The rule that pays the rent: **prove, don't assume.***

---

## 1. PURPOSE
Ship Banco POS changes with zero surprises on the live till — through environment gates, with a
backup, a real build stamp, and proof at each stop. This is the discipline that scales from one
shop to many: at scale, "assume it worked" ships broken to thousands; **only proof survives.**

## 2. SCOPE
The Banco trio on the box (`helixnet-uat`, `46.62.138.218`):
- **sandbox** — `/opt/helix-sandbox-tree` · `helix-platform-sandbox` · sandbox-banco.lapiazza.app
- **staging/UAT** — `/opt/helix-banco-staging-tree` · `helix-platform-banco-staging` · staging-banco.lapiazza.app
- **prod** — `/opt/helix-banco-tree` · `helix-platform-banco` · banco.lapiazza.app

Tools: **`make deploy` (the front door — use this)** · `scripts/ops/app-gate.py` ·
`scripts/ops/kc-login-audit.js` · `scripts/ops/deploy-banco.py` (box: `/opt/ops/`) ·
`scripts/ops/env-parity.py`.

## 2b. THE FRONT DOOR — `make deploy` (added 2026-07-14)
**Run it from the LAPTOP, not the box** (the login gate needs Chrome; the box has none, on purpose).

```
make deploy ENV=<sandbox|staging|prod> [REF=feat/x]   # deploy + BOTH gates
make app-gate    ENV=prod [SHA=<short-sha>]           # gate 1 standalone
make login-audit ENV=prod                             # gate 2 standalone (no ENV = all 4 screens)
```

It runs `deploy-banco.py` on the box, then **TWO BLOCKING GATES. Either fails → the deploy fails.**

| # | Gate | Proves |
|---|------|--------|
| 1 | `app-gate.py` | `/health/healthz` 200 (**the exact path the container healthcheck uses — `/health` 404s**), `/pos` 200, and **the RENDERED build stamp == the SHA just deployed** |
| 2 | `kc-login-audit.js` | A **human can READ the login screen** — drives Chrome, **types into the username + password fields**, measures the contrast of what Chrome actually painted |

**Why gate 1's stamp check is the sharp one:** `build_info` caches the stamp per process, so a
restart that quietly kept the **old process** still passes the healthcheck *and* returns 200. Only
the **rendered SHA** proves the new code is live. On its first prod run it caught the app returning
**502 while Docker reported `live + healthy ✅`** — rule #1 and #2 below, turned from a habit into a check.

**Why gate 2 exists:** the Banco login shipped **black-on-black** (username + password at 1.17:1 —
invisible) and was marked verified because the stylesheet returned **HTTP 200**.
**HTTP 200 means the file exists. It does not mean anyone can use it.**

Hand-running `deploy-banco.py` on the box **skips both gates**, so it prints a loud
**"⚠️ LOGIN GATE NOT RUN"** with the command to run. (Suppressed when `make deploy` sets
`BANCO_LOGIN_GATE=1` — a warning that cries wolf gets ignored.)

## 3. THE GATE LADDER (procedure)
Never skip a rung. A change rides: **dev → sandbox → staging → prod.**

1. **Build on a branch off `main`** (`feat/<name>`). Sandbox-first — never edit prod by hand.
2. **Deploy to sandbox:** `make deploy ENV=sandbox REF=feat/<name>` → gates run → human eyeballs it.
3. **Merge to `main`** (FF) once sandbox is human-green; push.
4. **Deploy to staging:** `make deploy ENV=staging` → gates run → verify + sign-off.
5. **Prod — backup GATES the deploy:**
   - `bash /opt/backups/banco_backup.sh` — encrypted (AES256) **+ verified restore drill**
     (decrypts, restores into a throwaway DB, compares row counts). **No verified backup → no deploy.**
   - `make deploy ENV=prod` → both gates must pass.
6. **Close the loop:** mark the BL ticket fixed with the **real commit SHA** (`/feedback/{n}/done`)
   → reporter confirms → Resolution writes itself.

## 4. THE NON-NEGOTIABLE RULES (the discipline)
1. **PROVE, DON'T ASSUME.** Never say "fixed/shipped" without seeing the bytes. The healthcheck
   flips green a beat *before* the first request fully serves.
2. **RE-PROBE AFTER EVERY RESTART.** The first read after a restart can be a race — a "before"
   snapshot can masquerade as "after." Read it twice.
3. **NEVER assume broken either.** A blank/odd first read is usually timing — re-probe before you
   panic-rollback a *good* deploy.
4. **BACKUP GATES PROD.** Verified `banco_prod` dump first, always.
5. **NO MIGRATION = SAFEST.** Confirm `git diff --name-only <oldsha> HEAD -- src/db/models alembic`
   is empty for a code-only ship. If not, plan the migration deliberately.
6. **MARK FIXED WITH A REAL COMMIT.** The timeline/Resolution must be truthful, never theater.
7. **PARITY BEFORE NEW WORK.** `env-parity.py --local` → trio on the same SHA, clean, before starting.

## 5. VERIFICATION CHECKLIST (per deploy)
Deploying via `make deploy` performs items 1–4 for you **and fails the deploy if they don't hold** —
that is the whole point of the gates. The rest stay human.
- [ ] **GATE 1** `app-gate` PASS — `/health/healthz` 200, `/pos` 200, **rendered stamp == deployed SHA**
- [ ] **GATE 2** `login-audit` PASS — every text element readable (it **types into the fields**)
- [ ] **Re-probed** after restart — not the first read (the healthcheck greens before it serves)
- [ ] Build bar shows the real SHA (`bNNNN · <sha>`) — the *rendered* one, not the checked-out one
- [ ] Logs show `Application startup complete`, no tracebacks
- [ ] The actual change is **rendered/observed** (grep the served page, or eyeball) — not assumed
- [ ] (prod) `banco_backup.sh` ran: encrypted **and restore-drill verified** (row counts matched)
- [ ] BL ticket marked fixed with the commit SHA

## 6. KNOWN SEALS TO CHECK (gotchas that bit us — "if one fails, check all")
- **Two `Jinja2Templates` instances.** `main.py` AND `pos_router.py` each have one; POS pages render
  via pos_router's. A template global (e.g. `build_date`) must be set on **both** or it's empty on
  POS pages. (Cost us a "missing date" red herring.)
- **PWA cache / the in-app Refresh ≠ the shell.** "Refresh" reloads DATA only; a new build isn't
  discovered without a navigation. Fixed by the **tap-to-update nudge** (BL-011) — but after any
  `sw.js` CACHE_NAME bump, the *bootstrapping* load still needs one hard refresh; the nudge handles
  every deploy after that. Always bump `sw.js` CACHE_NAME on a shell change.
- **Restart-race.** See rules #1–3. The first curl after `docker restart` may serve mid-reboot.
- **Legacy `/opt/helixnet` tree** is bottega-prod — never blanket-deploy Banco code there.

## 7. ROLLBACK
Code-only ship gone bad: `python3 /opt/ops/deploy-banco.py prod <previous-good-sha>` (re-stamps +
restarts). Data issue: restore the pre-deploy backup. Prefer a small, fast forward-fix when safe.

---
*"Never assume broken, never assume fine — re-probe and let the bytes talk."*
*"Backup gates the deploy. No backup, no go."*
*"Prove it — because at 100K tills, a guess ships broken to thousands."*
