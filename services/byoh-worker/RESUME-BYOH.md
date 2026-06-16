# PASTE-IN FOR TIGS — resume the BYOH work (after /compact or in a new session)

Tigs: we're building **BYOH (Bring Your Own Hardware)** — "our own Vast." Read the
memories `[[byoh-project]]` and `[[deploy-topology-bottega-vs-borrowhood]]` first;
they have the full context. This is the quick orient + what to do next.

## Where we are (as of 2026-06-16, before Angel left for the Zurich show)
- **Thesis:** shared cheap brain (Ollama Turbo / BYO) + muscle on members' hardware, brokered by us. Recipes = fixed tested software. 3 axes: brain & hardware swap freely; software does NOT (it's the recipe; app-store-not-sideloading).
- **PoC built + proven on Angel's laptop:** `services/byoh-worker/` — `render.py` (text→voice→mp4), `worker.py` (HTTP), `capabilities.py` (preflight door-guard), `broker_demo.py`+`render_worker.py` (pull-loop, mirrors `scripts/lpcx_worker.py`), `enroll.py`, `test_byoh.py` (**6/6 green** — run it: `cd services/byoh-worker && .venv/bin/python test_byoh.py`).
- **"A" (capability window) shipped to Bottega staging** (commits 0418f75, c3d143d): `compute_nodes.caps_json`, Provider Console capability badges + runs/can't-run + BYOH callout + tooltips, FAQ grouped submenu + BYO-hardware/what-runs/lend-a-GPU/own-software sections. Verified local (screenshots) + staging (8099).
- **One-pager for the show:** `UFA_r2p/la-piazza-byoh-onepager.pdf` (source `docs/business/byoh-onepager/`).

## DEPLOY TRAPS — do not forget (see topology memory)
- Bottega = **helixnet repo** = `bottega.lapiazza.app` = `helix-platform` container. Local app `localhost:9003`.
- `lp_deploy.py staging` and `staging.lapiazza.app` = the **BorrowHood marketplace**, a DIFFERENT app. NOT Bottega.
- **Bottega staging = `127.0.0.1:8099`** (`helix-platform-staging`), worktree at `/opt/helix-staging-tree`. Deploy = on box `root@46.62.138.218`: `cd /opt/helix-staging-tree && git fetch && git checkout <sha>` + `docker restart helix-platform-staging`. ONLY the worktree.
- Bottega staging **shares prod DB** (`helix_db`) → migrations must be additive/`IF NOT EXISTS`/nullable. Prod mounts `/opt/helixnet/src` — **NEVER `git pull` in /opt/helixnet**.
- Local KC token for testing: `curl -sk https://keycloak.helix.local/realms/lapiazza-realm-dev/protocol/openid-connect/token -d grant_type=password -d client_id=lapiazza_web -d username=angel -d password=helix_pass`.

## NEXT MOVES (pick with Angel)
1. **C — render jobs through the REAL exchange** (today it runs brain/text jobs; render loop proven only in the demo broker). Wire render-as-a-job-type + artifact return so a node actually RUNS dispatched work.
2. **Artifacts = "the bucket":** MinIO per-user folder / per-recipe subfolder + CRUD + replay dashboard.
3. **Output-type-aware viewer** standardized in the Service Interface (reading mode / image-PDF / **video player for mp4** / MD download — display+save+edit, simple but dynamic, same for every recipe).
4. **Recipe → branded A4 postcard** (Locandina pipeline) = the advertisement piece → uploadable to La Piazza.
5. **Warm-toolbox worker:** one image with all CPU tools (add Puppeteer + Whisper to render.py's worker), then knock off the top-10 recipes one by one (Angel + Tigs).
6. **Separate staging VM** (own DB, ~€5 Hetzner CX22) to retire the worktree hack + shared-DB fragility; doubles as the always-on warm-services host.

## HOUSE RULES (reminders)
Python-first; verify output visually before claiming done; staging before prod, explicit sign-off before prod; watch Angel's overwork — endorse stopping when green.
