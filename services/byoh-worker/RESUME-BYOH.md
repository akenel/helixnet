# PASTE-IN FOR TIGS — resume BYOH / Voiceover (after /compact or new session)

Tigs: read memories `[[byoh-project]]` + `[[deploy-topology-bottega-vs-borrowhood]]` FIRST — they have the full detail. This is the quick orient + the prioritized table.

## State (2026-06-17)
**The Voiceover Reel is COMPLETE and LIVE on prod** (`bottega.lapiazza.app` → Workshop → Make Media → Voiceover Reel): text→voice→captioned MP4; F (default) / M (joe) voices; self-explaining top instructions; sample chips; 2000-char cap; **shapes** (Landscape/Portrait/Square); **multi-line karaoke** highlight; karaoke opt-in **+1 credit**; **stats card** (voice/shape/seconds). Rendered by a SHARED `render-worker` container (Piper+ffmpeg+faster-whisper, ~1.3GB) serving prod+staging on the Hetzner box; app calls it at `RENDER_WORKER_URL=http://render-worker:8800`; media saved to `/tmp/bottega-media`, served at `/api/v1/compute/bottega/media/{uuid}.mp4` (unauth, uuid-guarded).

## Deploy (see topology memory)
- Bottega = THIS repo (helixnet) = `bottega.lapiazza.app` (`helix-platform`, mounts `/opt/helixnet/src`). Staging = `helix-platform-staging` @ `127.0.0.1:8099` AND public `https://staging-bottega.lapiazza.app` (login works there; tunnel can't log in). Worktree `/opt/helix-staging-tree`.
- App-code deploy = on box: `git checkout origin/main -- <files>` into the worktree (staging) or `/opt/helixnet` (prod) + `docker restart`. Worker change = `docker build -t byoh-render-worker:latest <tree>/services/byoh-worker` + `docker compose -f docker-compose.uat.yml up -d --force-recreate render-worker` (SHARED → hits prod+staging). NEVER `git pull` in /opt/helixnet. Verify with the `docker exec ... python3` E2E (token via KC direct-grant; staging realm `lapiazza-realm-staging`, prod `lapiazza-realm-dev`, user angel / helix_pass).

## Backlog table (Angel's, 2026-06-17) — recommended next: #1 + #5
- **Polish:** (1) forced-aligner (fix intermittent Whisper brand-word misspell) (2) mic input (Whisper STT) (3) dynamic profile-based sample (4) karaoke effect styles [overkill?]
- **Platform:** (5) job-history dashboard — all runs logged/paginated/re-download/rename/replay (+ MinIO "bucket", today /tmp) (6) per-node token + idiot-proof enroll (7) SPA token-refresh bug (8) separate staging VM w/ own DB
- **Big BYOH:** (9) render jobs through the REAL exchange (remote gamer GPU node) (10) GPU tier (Stable Diffusion / 2D→3D / premium voices; OpenArt as rented stopgap)
- **Breadth/reach:** (11) more recipes from the top-10 catalog (RECIPES.md) (12) recipe→branded postcard→upload to La Piazza (13) multilingual translate+voices (14) voice-cast (master character voices) (15) DISTRIBUTION = warm last-mile (the real lever for users + getting hired)

## House rules: Python-first; verify OUTPUT (for media: ffmpeg astats Flat factor, not just duration; eyeball a frame); staging before prod + explicit sign-off; self-explaining UIs; watch Angel's overwork — endorse stopping when green.
