# SOP — The Dream Weavers Method
*AI-assisted, story-driven video production for ANY scenario. The method as IP.*

## What it is, and the KEY
One narrative artifact that is **six things at once**: a **test**, a **demo**, a **tutorial**, living
**docs**, an **onboarding flow**, and **distribution** content — produced by driving the **real,
fully-integrated stack** through a story.

**THE KEY:** the story exercises the *whole caboodle working together* — **Keycloak** (login, roles,
groups, teams), **La Piazza** (the app + recipes), **Postgres** (the real data) — **end to end.** The
camera films the *truth*: a real persona logs in with a real role, does real actions, writes real rows.
A passing episode is proof the **integrated** system works — not a mocked demo. That's why one artifact
can be both the best demo AND the best regression test.

## The stack it drives (the whole caboodle)
- **Keycloak** — auth, the realm, roles (`lapiazza-user`…), groups, teams.
- **La Piazza / Bottega** — the FastAPI app, the recipes (procedure-as-code), the UI.
- **Postgres** — the real data: members, listings, events, RSVPs, posts, views.
- **Supporting cast** — Caddy/Traefik, Redis, RabbitMQ, **Ollama** (AI fill), **Suno** (music).

## The pipeline — any scenario → a dynamic video
**INPUT** (a scenario: garage sale · new-lab invention · an experimental YouTube build · what you're
cooking today · a TikTok · a product feature) → **PROCESS** (these steps) → **OUTPUT** (a video that
teaches + tests + sells).

1. **Concept** — the scenario + the ONE thing it teaches + a Sid-Field logline.
2. **Ask the Masters** — La Piazza's own **Legends** feature (`mentor-session` recipe) writes the
   story/beats in a master's voice. Brief the master first (`BRIEF-for-the-writer.md` pattern), then
   curate the draft. Sid Field structure — **setup → turn → payoff** — even at 30–60s.
3. **Write it up** — the Season Bible + per-episode beats: *timecode · on-screen · action · the teach.*
4. **Record (Puppeteer)** — drive the real stack headless: demo-login as a persona (real KC role/group),
   CDP screencast, banner-suppress (movie only), **natural-length dwells (breathers)**, zoom for
   readability. Data-driven beats.
5. **AI fills the blanks** — **Ollama** seeds the world (personas, dialogue, replies, edge cases like the
   scammer), auto-generates Q&A, and proposes "what could break."
6. **Assemble** — render cards (intro/outro) → stitch (crossfade) → compile (the film).
7. **Voiceover (host only)** — the interactive **director's-cut sheet** (timed beats, editable lines,
   copy-back loop). Special intro episode ≤ **1 minute**; the rest stay silent of voice.
8. **Audio LAST** — pick/make the theme (**Suno**, free→Pro, the brief), **master + seamless-loop**,
   score (intro ep = voice + theme @ ~5%; rest = theme bed ~30–50%). Audio is the *last* layer — you
   score to the feel you built, and you can **upgrade the track later** without redoing anything. **One
   signature theme** across the series (variations "from the masters" come later, once Pro).
9. **Gate** — the episode **joins the regression suite** (`tests/e2e/dream-weavers-regression.js`). The
   stories test the whole caboodle before every prod deploy (`scripts/deploy-prod.sh`). A broken story
   blocks a bad ship. The test value **compounds**.
10. **Publish + measure** — upload kit (title/desc/tags), **`.srt` captions** *(voice episodes ONLY —
    Whisper from the voice → English; YouTube auto-translates = accessibility + global reach; music-only
    episodes skip it, no speech to caption)*, a real **thumbnail** (1280×720), **Shorts** (9:16, lead
    with the hook), a **playlist**. Then **distribute** (see below) — and watch the numbers.

## ⚠️ The hard truth: PUBLISHING ≠ DISTRIBUTION
A video posted to a small channel sits in the void — views are a *lagging* indicator. The *leading*
work is putting the **story + the prototype** where people already are, and inviting them in:
- **Your network first (LinkedIn)** — you're a SAP specialist with a real network; "I built an
  open-source town square, here's episode 1, try the prototype" serves distribution AND the job hunt.
- **Builder communities** — X/Twitter build-in-public (`scripts/lp_tweet.py` + the marketing kit),
  Indie Hackers, Reddit (r/SideProject, r/selfhosted), a "Show HN".
- **The prototype-feedback hook** (Angel's instinct, and it's the right one): *"This is a prototype —
  try it, tell me what to fix, help me build it for you."* People love shaping a thing early.
- **The measure that matters at this stage:** not YouTube views — **"did a real person try La Piazza
  and give feedback?"** Ten real triers > ten thousand passive views.

## The principles (locked)
- **Story = test = demo = teach = onboard = distribution.** One artifact, six jobs.
- **Drive the REAL integrated stack — never mock.** The camera films the truth (the whole caboodle).
- **Sid Field** structure; end every episode on a **hook**.
- **Silent + cards** (host voice only on the intro episode).
- **Natural length**; the special director's cut **≤ 1 min**; **zoom** for readable text; **banner-free**
  (strip the cookie banner from the *movie* only — it's required in the app).
- **Audio LAST**; **one signature theme** (master-flavored variations later, kept recognizable).
- **Shorts = NATIVE PORTRAIT, never padded landscape.** (Learned 2026-06-09 the hard way.) Don't pad
  a landscape episode into a 9:16 frame — you get a tiny unreadable strip with dead bars (rookie).
  **Re-shoot the scene at a phone viewport** (`432×768 @ deviceScaleFactor 2.5, isMobile:true` →
  captures 1080×1920); the app is mobile-first, so the responsive **mobile layout renders full-frame,
  big-text, phone-native.** Exemplar: `tests/e2e/short-scammer-portrait.js`.
- **Build in public** — free tools, document the making (the free Suno account, the 3 takes). *Tell the
  story while making the story.*
- The **draft 1 → your notes → draft 2** loop (interactive task sheets).

## Any scenario (the universal stud)
Scenario-agnostic. Garage sale, a lab invention, a kitchen cook-along, a TikTok, a new feature — **same
pipeline**: pick it → ask a master to write it → drive the stack (or the scene) → assemble → score →
gate → publish. `INPUT → PROCESS → OUTPUT`, every time.

## Artifacts / exemplars
- **Bible + masters:** `stories/dream-weavers/SEASON-BIBLE.md` · `BRIEF-for-the-writer.md` →
  `SEASON-2-draft-by-the-master.md` → `SEASON-2-shootable.md`
- **Record:** `tests/e2e/ep01..12-record.js`
- **Assemble:** `scripts/render-cards.js` · `stitch-episodes.js` · `compile-movie.js`
- **Voice:** `docs/business/marketing/ep01-directors-cut.html`
- **Audio:** `stories/dream-weavers/THEME.md` · `docs/business/marketing/dream-weavers-theme-brief.md`
- **Gate:** `tests/e2e/dream-weavers-regression.js` · `scripts/deploy-prod.sh`
- **Publish:** `docs/business/marketing/dream-weavers-upload-kit.md` · `music-site-finder.html`
- **Task-sheet SOP:** `docs/SOP-interactive-task-sheets.md`
