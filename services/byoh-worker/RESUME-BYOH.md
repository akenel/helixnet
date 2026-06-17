# PASTE-IN FOR TIGS — resume BYOH / Voiceover (after /compact or new session)

Tigs: read memories `[[byoh-project]]` + `[[deploy-topology-bottega-vs-borrowhood]]` FIRST — they have the full detail. This is the quick orient + the prioritized table.

## State (2026-06-17)
**The Voiceover Reel is COMPLETE and LIVE on prod** (`bottega.lapiazza.app` → Workshop → Make Media → Voiceover Reel): text→voice→captioned MP4; F (default) / M (joe) voices; self-explaining top instructions; sample chips; 2000-char cap; **shapes** (Landscape/Portrait/Square); **multi-line karaoke** highlight; karaoke opt-in **+1 credit**; **stats card** (voice/shape/seconds). Rendered by a SHARED `render-worker` container (Piper+ffmpeg+faster-whisper, ~1.3GB) serving prod+staging on the Hetzner box; app calls it at `RENDER_WORKER_URL=http://render-worker:8800`; media saved to the **`bottega_media` named volume** at `/var/bottega-media` (survives restart; shared prod+staging), served at `/api/v1/compute/bottega/media/{uuid}.mp4` (unauth, uuid-guarded). Every run is auto-logged to `bottega_sessions` → appears in **My Blueprint** (replay + re-download).

## Deploy (see topology memory)
- Bottega = THIS repo (helixnet) = `bottega.lapiazza.app` (`helix-platform`, mounts `/opt/helixnet/src`). Staging = `helix-platform-staging` @ `127.0.0.1:8099` AND public `https://staging-bottega.lapiazza.app` (login works there; tunnel can't log in). Worktree `/opt/helix-staging-tree`.
- App-code deploy = on box: `git checkout origin/main -- <files>` into the worktree (staging) or `/opt/helixnet` (prod) + `docker restart`. Worker change = `docker build -t byoh-render-worker:latest <tree>/services/byoh-worker` + `docker compose -f docker-compose.uat.yml up -d --force-recreate render-worker` (SHARED → hits prod+staging). NEVER `git pull` in /opt/helixnet. Verify with the `docker exec ... python3` E2E (token via KC direct-grant; staging realm `lapiazza-realm-staging`, prod `lapiazza-realm-dev`, user angel / helix_pass).

## Backlog table (Angel's, 2026-06-17) — recommended next: #6
- **Polish:** ✅(1) forced-aligner DONE+LIVE (commit 44cd718) — karaoke shows the *script* spelling, borrows only Whisper timings via `align_script_to_timings` (stdlib difflib, no new dep); kills "La Piazza"->"La Pisa/Lapias". (2) mic input (Whisper STT) (3) dynamic profile-based sample (4) karaoke effect styles [overkill?]
- **Platform:** ✅(5) job-history DONE+LIVE (commit 5b93752) — every reel auto-logged to `bottega_sessions` (output_type=video, url+stats as JSON); shows in **My Blueprint** (🎬 reel chip, search/sort/replay/delete — reused, no new UI); `loadSession` unpacks video rows so replay+download work. **Bucket = named volume `bottega_media`** (NOT MinIO — Angel chose the cheaper path: 0 new containers, 0 RAM on the pinched box), mounted at `/var/bottega-media`, shared prod+staging (same DB→same media), survives `up --force-recreate` (proven: force-recreated, file still 200). (6) per-node token + idiot-proof enroll (7) SPA token-refresh bug (8) separate staging VM w/ own DB
- **Big BYOH:** (9) render jobs through the REAL exchange (remote gamer GPU node) (10) GPU tier (Stable Diffusion / 2D→3D / premium voices; OpenArt as rented stopgap)
- **Breadth/reach:** (11) more recipes from the top-10 catalog (RECIPES.md) (12) recipe→branded postcard→upload to La Piazza (13) multilingual translate+voices (14) voice-cast (master character voices) (15) DISTRIBUTION = warm last-mile (the real lever for users + getting hired)

## ⭐ POLISH BATCH — Popsa-derived, APP-WIDE via the recipe chassis (P1+P2+P5 DONE+LIVE 2026-06-17)
**Key call (Angel + Tigs):** don't polish Voiceover in isolation — polish the *recipe chassis* + add presentation
fields to the *recipe/SI contract* so EVERY recipe inherits it (the design-factory: fix the factory, not one product).
Popsa (popsa.com) sells the same bet as us — "so easy it feels like cheating," "impossible to mess up." Cherry-picks:

**✅ SHIPPED (commit c3784fc, prod bottega.lapiazza.app, gate-3 PASS = TEST-UX-006):** `outcome` + `steps` are now
standard SI-contract fields on ALL 14 recipes (`menu()` serializes both); chassis renders P1 outcome-first cards +
run-screen outcome, P2 journey strip, P5 trust strip. Staging→sheet→prod, smoke green both. Angel: "perfect and simple".

Two buckets:
- **CHASSIS (build once, every recipe gets it)** — edit the shared workshop UI (`src/templates/compute/bottega.html`):
  - ✅(P1) **Outcome-first card:** one-line *outcome* under each recipe title; price demoted. DONE.
  - ✅(P2) **3-step journey strip** on the run screen ("Type → Voice → Reel") — kills "what will this ask of me". DONE.
  - (P3) **Confidence / pre-run confirm:** tiny preview of what you'll get + cost BEFORE charging (esp. the +1 karaoke). MED. BANKED.
  - ✅(P5) **Trust strip** on the workshop: *"Your data stays yours. No algorithm. No monthly ransom."* — our story Popsa can't tell. DONE. (ties [[angel-why-and-goal]])
- **PER-RECIPE FIELD (data in the recipe dict / SI definition — `src/compute/recipes.py`)** — ✅ `outcome`+`steps` now standard; remaining:
  - `outcome:` (one-line transformation, feeds P1) · `steps:` (the journey labels, feeds P2) · `sample:`/dynamic sample (P4)
  - (P4) **Never a blank box:** pre-fill a personalized sample (= existing backlog #3 "dynamic profile-based sample"). HIGH.
  - (P6) **Emotional > functional copy** in `outcome`/blurb: "your voice, your story, shareable in 30s" not "a video". (ties Alli-Miller transformation>productivity [[ref-alli-miller-video-validation]])

**Why this is the right altitude:** everything is a Service Interface ([[lp-everything-is-a-service-interface]]); a recipe is one
dict entry ([[lp-the-design-factory]]). Making `outcome/steps/sample` part of the SI contract = every current AND future
recipe is Popsa-grade by default. We're at the START of the recipe formula — standardize the presentation contract NOW
before there are 30 recipes to retrofit. After this batch: back to the **top-10 ideas bonus round** (RECIPES.md, backlog #11).

## House rules: Python-first; verify OUTPUT (for media: ffmpeg astats Flat factor, not just duration; eyeball a frame); staging before prod + explicit sign-off; self-explaining UIs; watch Angel's overwork — endorse stopping when green.
