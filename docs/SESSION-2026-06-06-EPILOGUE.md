# Session Epilogue — 2026-06-06 · The Day Bottega Became a Town

*A marathon: overnight → Saturday afternoon. If the laptop dies, read this + the commit log + `docs/BOTTEGA-WORKSHOP-PLAN.md` and you can pick up exactly here.*

## The chapter (what shipped — all on GitHub, branch `feat/lp-compute-exchange`)
- **Bottega is the front door.** `bottega.lapiazza.app` = the clean La Piazza (own realm `lapiazza-realm-dev`, registration on, login works end-to-end). `lapiazza.app` = the legacy BorrowHood marketplace, now bridged.
- **One-motion Get Started** (`/get-started`): name + (CV **or** a plain description — CV optional) → KC member + cv_to_bio profile + Blueprint archive + auto-login. Kills the chicken-and-egg.
- **Blueprint Archive + clue-scan** (Block A): every input archived with scanned emails/phones/links/skills.
- **Member History** (Block B): searchable, sortable "My Blueprint" over the `bottega_sessions` spine.
- **"Ask a Master"** mentor recipe (the Time Machine).
- **Shares are postcards**: `/s/{id}` with the Wolf cover + OG card (Telegram/WhatsApp/X preview) + serial №.
- **Shared nav bar**: one hallway joining Square ↔ Workshop ↔ Exchange (both buildings, both ways).
- **Human-readable timestamped filenames** + a cover shot on every output.
- **One-click YouTube playlist** proven via yt-dlp (`watch_videos?video_ids=...`).
- **Neil Campbell** (the proof-of-concept dormant member): found, granted 300 credits, second arrow drafted (NOT sent — Angel's trigger).

## Lessons learned (the hard-won ones)
1. **Machine-green ≠ human-green.** The onboarding returned page-200 but 500'd on a real signup. Only the **dry-run** (testing on `artemis`) caught it. Test the *flow*, not the door.
2. **Brain-key gotcha.** `helix-platform` reads `uat.env`; `BH_OLLAMA_KEY` only lived in `borrowhood.env` → cv_to_bio fell back to a local `ollama` host (DNS 500). Fix: key in `uat.env` + `up --force-recreate` (restart won't re-read env_file). Belongs in [hetzner gotchas].
3. **Image gen is out (June 2026):** Pollinations = x402 paywalled, `source.unsplash.com` = 503, no Unsplash key. → **Wolf is the default cover.** yt-dlp works for resolving songs→video IDs.
4. **KC hostname pin:** one Keycloak serves two domains; `KC_HOSTNAME_URL` pinned it to lapiazza.app and dragged bottega login back there. Fix = per-realm `frontendUrl` (`scripts/lp_realm_frontend.py`).
5. **Reuse, don't rebuild.** The marketplace already has `bh_message`, `bh_notification`, `bh_user_points`, and a whole AI layer (`BorrowHood/src/routers/ai.py`: `ai_concierge`, `ai_smart_listing`, `ai_generate_skill_bio`).
6. **Rule Zero = CONSENT.** Every invitation is a free, opt-in offer; ask, take no for an answer. The "why" is about *them*, never "we need their help."
7. **Brain = Llama (Ollama Turbo), always default.** Graceful overload warnings, never raw 500s. Low volume is fine; revisit at 10–20 users.
8. **Everything is a recipe** — an ask is a recipe (ingredients/inputs, method/steps, dish/output). The mentors are recipes that check order + correctness and report to the member.

## Where everything lives (the safety net)
- **GitHub** (`akenel/helixnet` + `akenel/borrowhood`): all code, CLAUDE.md, docs, commit history. Rock-proof.
- **Hetzner box** (46.62.138.218, separate machine): bottega.lapiazza.app + lapiazza.app running.
- **DO box**: the worker node (pull-based compute).
- **Plans/docs:** `docs/BOTTEGA-WORKSHOP-PLAN.md`, `docs/DAY-0.md`, `docs/LA-PIAZZA-BLUEPRINT.md`.

## What's next (in priority)
1. **THE KEYSTONE — the AI reads you and proposes.** Given a person's bio + archive + history, the brain returns ~10 personalized, character-named suggestions (playlists, questions, House prompts) + bonus + "Other". Kills the blank box. *Port the `ai.py` patterns; brain = Llama.* Deserves fresh energy.
2. Fire Neil's arrow (Angel's trigger) — gentle, two shots then let it sit.
3. The YouTube-playlist button on the Music Playlist recipe (yt-dlp resolve → watch_videos URL).
4. Blocks C–G (notifications, messages, teams, Grafana, backlog) — see the plan; reuse the spine + bh_* tables.
5. Themed cover images when an image key arrives (Unsplash API / paid Pollinations) — download + compress + save local, Wolf fallback.

---
*"Be water, my friend." — One town, doors both ways, the brain is Llama, and everything is a recipe.*
