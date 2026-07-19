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

## ⚠️ Phase 0 — HARD GATES (do these FIRST; a fail here stops everything)

1. **Secret-scan the git history — the #1 blocker.** Before leaning on "it's a public repo," prove there are
   NO secrets in history (not just the current tree). Run `gitleaks detect` / `trufflehog git file://.` over the
   FULL history of every repo that would be public. If anything leaked (KC admin pw, B2 keys, GPG passphrase,
   Resend key, DB creds) → the repo can't go public as-is; needs history scrub (git-filter-repo / BFG) + a
   rotation of whatever leaked. **Assume there ARE secrets in history until proven otherwise** (this app has had
   env files, deploy scripts, KC configs).
2. **Confirm the repo set.** A full stand-up needs the app repo (`helixnet`) AND the KC themes/realm config
   (`BorrowHood` — separate repo, one KC). Decide what's public and what the quickstart references. Ties
   `deploy-topology-bottega-vs-borrowhood`.
3. **Decide the clean-room** — a FRESH box / local VM / throwaway dir with NO access to the existing box,
   `/root/.banco-*` secrets, or Angel's KeePass. That isolation is the whole point (simulate a stranger).
4. **Decide the B2 credential for the drill** — a customer-style **READ** key (like `banco-restore-readonly`),
   NOT the box's write-only key and NOT master. Plus a GPG passphrase for a *test* backup (don't hand out the
   prod backup key). Ideally: make a throwaway encrypted backup with a throwaway key for the public demo.

## Phase 1 — Reproducibility recon (map the gap, no changes)

1. Read the compose stack: what does `docker compose up` bring up? (app / postgres / keycloak / traefik /
   ollama / minio / mailhog…). Which are REQUIRED for a minimal POS vs nice-to-have?
2. List every MANUAL / undocumented step a stranger would hit: KC realm import, first-run migrations
   (`create_all` + `_ADDITIVE_COLUMNS`), the **audit SQL** (`scripts/db/audit_log_setup.sql`), secrets/env,
   MinIO buckets, the "bring your own brain" LLM key (enrich/snap need a model — Turbo key or local Ollama).
3. Produce a **GAP LIST**: "to stand up fresh from docs alone, a stranger needs X, Y, Z — currently missing/
   undocumented." This is the real output of Phase 1.

## Phase 2 — The clean-room drill (the actual proof, iterate to green)

1. In the clean-room, `git clone` the public repo(s) — nothing else from the existing box.
2. Follow ONLY the docs to stand up: `docker compose up` → DB init → KC realm import → migrations → apply
   `audit_log_setup.sql` → seed/minimal config.
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

## Open decisions for Angel (answer at kickoff)
- Which repo(s) public? (helixnet + BorrowHood themes?)
- Clean-room = fresh Hetzner box / local VM / throwaway dir?
- Minimal profile (just POS + Postgres, BYO-brain) vs full stack (KC + traefik + ollama) as the onboarding target?
  → a **minimal profile** is probably the right onboarding target; full stack is the "advanced" path.
- Test backup + throwaway B2 key for the public demo (don't expose prod keys).

## Risks
- **Secrets in git history** (Phase 0 gate — the big one).
- **KC realm reproducibility** — realm export/import must be scriptable (not click-ops).
- **LLM dependency** — enrich/snap need a brain; the quickstart must address BYO-brain or degrade gracefully.
- **Must NOT require the existing box or Angel's secrets** — if the stand-up secretly leans on them, it's not
  a real ownership proof.
