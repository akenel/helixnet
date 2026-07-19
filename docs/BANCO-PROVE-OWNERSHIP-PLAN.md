# PROVE IT — "Own Your Banco" clone-and-restore drill (the trust proof)

**Status:** PLAN — written 2026-07-19, to execute fresh next session.
**Why:** Angel's answer to the #1 sales blocker (bus-factor / "what if the vendor vanishes"): the customer
**owns everything** — public repo + their own B2 backup key + DR docs = **self-insured continuity.** The proof
*is* the sale: show a **stranger** can clone the public repo, stand up a fresh instance, and restore a real
backup from B2 with a key we hand them. Stronger than the 2026-07-19 on-box DR drill (that restored on the
*existing* box; this proves reproducibility + genuine ownership from ZERO). Memory:
`banco-self-insured-ownership-model`. Deliverable = a tested **"Own Your Banco" quickstart** that doubles as the
onboard-shop-#2 artifact and the steward-training material.

> Support has TWO meanings — keep them separate. **Continuity** ("am I stranded if the vendor's gone?") is what
> this proves and solves. **Day-to-day support** ("bug at 2pm Saturday") is a *separate* tiered answer
> (community / paid / outsourced / own-IT) — this drill does NOT cover it. Don't let one pretend to be the other.

---

## 🍪 THE APPROACH — extract a clean `banco-starter`, do NOT publish the messy monorepo

**Recon 2026-07-19 (why we extract, not clone):** the current `helixnet` repo is a monorepo junk-drawer:
- **`.git` is ~1 GB** — bloated with media/artifacts over hundreds of commits → a public clone is a 1GB
  download, secret-scanning it is slow, and 1GB of history is *far* more likely to hide a leaked key.
- **Tree is full of junk + unrelated projects**: `node_modules/ __pycache__/ build/ dist/ test-results/
  e2e-out/ scratch/ scratchpad/ videos/ stories/ demo/`, plus WHOLE other projects nested in — **BorrowHood**
  (a full app + Keycloak), `piccola-bistro/ crm/ debllm/ n8n-workflows/`. Not "here's Banco," it's "here's everything."
- **No root `docker compose up`, no `.env.example`, no quickstart** — stand-up steps are undocumented.

**So the cookie-cutter is a freshly-`git init`'d `banco-starter` repo** — curated files + FRESH history. Fresh
history means **1GB → tiny AND the "secrets in git history" problem vanishes entirely** (we don't publish the old
history; Phase 0 shrinks to scanning the small curated set). Same pattern already proven: **wolfhold.app /
Freehold starter kit.** The app stack itself (FastAPI + Postgres + Keycloak + compose) is standard + cloneable;
the mess is a reason to EXTRACT, not a reason it's impossible. Est. a focused day.

**`banco-starter` file manifest (curate IN only these):**
`src/` (app; strip `__pycache__`) · `src/static/vendor/` (Alpine/etc. — frontend is CDN + vendored, no
node_modules needed for runtime) · ONE clean `compose.yml` (app + postgres + keycloak [+ minio if image
storage wanted]) · `.env.example` (ALL required vars, NO real values: KC admin, POSTGRES, B2 keys, LLM/Turbo
key, secret keys) · `keycloak/` = the **banco realm export (scriptable import)** + the banco theme (from
`BorrowHood/keycloak/themes/banco`) · `scripts/db/audit_log_setup.sql` (the audit machine) · a `scripts/`
minimal set (`standup.sh`, `restore-from-b2.sh`, `banco_b2_push.py`) · `requirements.txt`/pyproject ·
`README.md`/`QUICKSTART.md` (the "Own Your Banco" runbook). **Leave OUT:** the 1GB history, node_modules, build/
dist/test junk, BorrowHood(whole), piccola-bistro/crm/debllm/n8n, scratch, videos, stories.

⚠️ **Trickiest reproducibility piece = Keycloak realm.** The app needs KC + the `banco`/`borrowhood` realm
(clients, roles, redirect URIs). Extract a **realm.json export** + a scripted `kcadm`/import so a stranger gets
it with one command, not click-ops. This is the make-or-break of the stand-up. (BYO-brain LLM key is the second
dependency — enrich/snap need a model; quickstart must set `BH_OLLAMA_KEY` or a local Ollama, or degrade.)

---

## ⚠️ Phase 0 — HARD GATES (do these FIRST; a fail here stops everything)

1. **Secret-scan the CURATED SET (not 1GB of history).** Because we EXTRACT into a fresh-`git init` starter, the
   old history never ships — so the gate shrinks from "scan/scrub 1GB history" to "scan the small curated file
   set before the first public commit." Run `gitleaks detect` / `trufflehog filesystem` over the `banco-starter`
   tree; any real value in `.env`/configs/scripts → replace with a placeholder in `.env.example`. Still assume
   the *source* files may carry a stray key — scan before publishing. (No BFG/filter-repo needed — fresh history.)
2. **Decide the clean-room** — a FRESH box / local VM / throwaway dir with NO access to the existing box,
   `/root/.banco-*` secrets, or Angel's KeePass. That isolation is the whole point (simulate a stranger).
3. **Decide the B2 credential for the drill** — a customer-style **READ** key (like `banco-restore-readonly`),
   NOT the box's write-only key and NOT master. Plus a GPG passphrase for a *test* backup (don't hand out the
   prod backup key). Ideally: make a throwaway encrypted backup with a throwaway key for the public demo.

## Phase 1 — EXTRACT the clean `banco-starter` (build the cookie-cutter)

1. **New empty repo, fresh `git init`.** Copy in ONLY the manifest above (curate — no `__pycache__`, no junk,
   no other projects). Result: a tiny, clean tree with no 1GB baggage and no history secrets.
2. **Write the missing plumbing that the monorepo lacks:**
   - ONE root `compose.yml` (app + postgres + keycloak [+ minio]) — the `docker compose up` entry point.
   - A real `.env.example` (every required var: KC admin, POSTGRES, secret keys, B2 read-key vars, `BH_OLLAMA_KEY`).
   - `keycloak/` = a **realm.json export** + a scripted `import-realm.sh` (kcadm) so KC comes up configured, not click-ops.
   - `scripts/standup.sh` (compose up → wait healthy → run `audit_log_setup.sql`) + `scripts/restore-from-b2.sh`
     (b2 authorize → download → gpg-decrypt → psql-restore, the DR-brief chain).
   - `QUICKSTART.md` = the "Own Your Banco" runbook (incl. B2 training + BYO-brain).
3. **First-run migrations:** confirm the app's `create_all` + `_ADDITIVE_COLUMNS` build the schema on a virgin
   DB (or add a bootstrap step). The GAP LIST for a stranger is now the checklist of what `standup.sh` must do.

## Phase 2 — The clean-room drill (the actual proof, iterate to green)

1. In the clean-room, `git clone` **`banco-starter`** — nothing else from the existing box.
2. Follow ONLY `QUICKSTART.md`: `cp .env.example .env` (fill) → `docker compose up` → `import-realm.sh` →
   `standup.sh` (schema + `audit_log_setup.sql`). If any step needs knowledge that isn't in the docs, that's a bug — fix the starter, re-run.
3. **Restore a real backup from B2:** with the handed READ key, `b2 account authorize` → `b2 file download` a
   `.sql.gz.gpg` → `gpg --pinentry-mode loopback -d | gunzip | psql` into the fresh DB (the exact chain the DR
   brief documents). Use a TEST backup + test key for the public demo.
4. **Verify the fresh instance:** `/pos` serves, login works, catalog + sales present, the 🕵️ audit cockpit
   loads. A working till on a box that never saw the original = ownership proven.
5. Every doc gap → fix it → re-run. **Done = a clean run works from docs ALONE, by someone who isn't Angel.**

## Phase 3 — The deliverable

- A polished **"Own Your Banco" quickstart** (README + maybe the gold HTML TESTSHEET treatment): clone →
  `compose up` → restore-from-B2 → running, followable by a competent non-Angel. Include the **B2 training**
  (own your bucket, keys, run a restore) and the **BYO-brain** step (LLM key).
- This one artifact = the trust proof + the onboard-shop-#2 kit + steward-training material, all at once.

## Phase 4 — Package as the trust story

- Fold into the **sell-shop-#2 plan** as the "continuity" pillar (pairs the DR brief
  `docs/business/BANCO-DR-BRIEF.html`). Ties `solo-founder-plan`, `steward-guild-why-now`,
  `freehold-starter-kit` (wolfhold.app = the same clone-and-run pattern already LIVE — reuse it).
- Optional: film it (Born Once) — "watch a stranger stand up Banco from scratch + restore, in X minutes."

## Decisions made 2026-07-19 (banked before compaction)
- **SCOPE = Banco/POS only.** BUT the app is a MONOLITH (one `src/` serves /pos + /compute/bottega + Cleo).
  v1 of the starter ships the WHOLE app code (clean — minus junk + other repos), **positioned/documented as
  Banco POS**; the other routes sit harmlessly. A true POS-only code-carve = a separate bigger refactor (weeks),
  do NOT gate the cookie-cutter on it. This keeps the extract ~a day.
- **DON'T pre-create the repo.** The work is curation → write plumbing → secret-scan → THEN `git init`. Flow:
  extract into a fresh local dir → build plumbing → scan the curated set → `git init` → push **PRIVATE** →
  prove the clean-room stand-up → **flip PUBLIC** only once it stands up + is secret-clean. Name: `akenel/banco-starter`.

## Still-open decisions (answer at kickoff)
- Clean-room = fresh Hetzner box / local VM / throwaway dir?
- Minimal profile (POS + Postgres + KC, BYO-brain) vs full stack (+ traefik/ollama/minio) as the onboarding target?
  → **minimal profile** is the right onboarding target; full stack is the "advanced" path.
- Test backup + throwaway B2 key for the public demo (don't expose prod keys).

## Risks
- **Secrets in git history** (Phase 0 gate — the big one).
- **KC realm reproducibility** — realm export/import must be scriptable (not click-ops).
- **LLM dependency** — enrich/snap need a brain; the quickstart must address BYO-brain or degrade gracefully.
- **Must NOT require the existing box or Angel's secrets** — if the stand-up secretly leans on them, it's not
  a real ownership proof.
