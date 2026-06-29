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

Tools: `scripts/ops/deploy-banco.py` (box: `/opt/ops/`) · `scripts/ops/env-parity.py`.

## 3. THE GATE LADDER (procedure)
Never skip a rung. A change rides: **dev → sandbox → staging → prod.**

1. **Build on a branch off `main`** (`feat/<name>`). Sandbox-first — never edit prod by hand.
2. **Deploy to sandbox:** `python3 /opt/ops/deploy-banco.py sandbox feat/<name>` → human eyeballs it.
3. **Merge to `main`** (FF) once sandbox is human-green; push.
4. **Deploy to staging:** `python3 /opt/ops/deploy-banco.py staging main` → verify + sign-off.
5. **Prod — backup GATES the deploy:**
   - `docker exec postgres pg_dump -U helix_user -d banco_prod | gzip > /opt/backups/banco/banco_prod-pre<change>-<ts>.sql.gz`
   - `gzip -t` it; abort if < 1 KB. **No verified backup → no deploy.**
   - `python3 /opt/ops/deploy-banco.py prod main`
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
- [ ] `deploy-banco.py` reported `live + healthy ✅`
- [ ] **Re-probed** after restart — container `healthy` with rising uptime (not flapping)
- [ ] Logs show `Application startup complete`, no tracebacks
- [ ] The actual change is **rendered/observed** (grep the served page, or eyeball) — not assumed
- [ ] Build bar shows the real SHA + date (`3.3.0·<sha> · DD Mon`)
- [ ] (prod) backup exists + `gzip -t` clean
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
