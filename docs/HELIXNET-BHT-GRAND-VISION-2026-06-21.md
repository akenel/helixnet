# HelixNet — Brutal Honest Truth + Grand Vision

*Wide-sweep scan, 2026-06-21. Three parallel passes: structure/maturity, technical flaws, product value. This is the "step back from the BL grind and look at the whole drive" doc.*

---

## ONE-PARAGRAPH TRUTH

You have built **a real platform, not a toy** — 68K lines of production Python, 65 models, 13 live routers, Keycloak SSO across 6 apps, weekly shipping, smoke-tested, deployed. That is rare for a solo dev. The flaws are **not "the code is bad"** — the code is healthy (14 TODOs, 2 skipped tests, no SQLi, ORM-clean). The flaws are **operational and strategic**: prod runs uncommitted bind-mounted source behind one Keycloak and one Postgres with the password `helix_pass` committed to git, Alembic is abandoned, and you have **eight products competing for one operator's hours when only two are close to money.** The grand vision is sound. The risk is spreading yourself across the whole estate instead of the two rooms that pay rent.

---

## PART 1 — THE FLAWS (ranked by what can actually hurt you)

### 🔴 Critical — fix these before they bite

1. **`helix_pass` is the prod password for everything, committed in git.**
   `hetzner/docker-compose.uat.yml` — Postgres, Keycloak DB, Keycloak admin, MinIO root are all the literal string `helix_pass`, identical to the documented *test* password. One password, public in git, guards the entire prod data tier.

2. **Real secret files were committed to git history.**
   `borrowhood.env` (commit `7bc987d`) and `uat.env` (`33c5fff`) — gitignored at HEAD but recoverable forever. Contains `BH_SECRET_KEY=...change-in-production-2026` (never rotated) + named slots for PayPal/Telegram/KC secrets. **Rotate + `git filter-repo` scrub.**

3. **Prod runs uncommitted, bind-mounted source; deploy = `git pull` on the box.**
   `helix-platform`, `lpcx-consumer`, BorrowHood all mount `../src:/app/src` writable. Whatever sits in the box's working tree IS prod. This is the "BorrowHood box divergence" from memory — now confirmed *structural, not accidental*. No pinned image, no clean rollback.

### 🟠 High — will cause a bad day eventually

4. **Alembic is effectively abandoned.** 72 model files, only **5 migrations** (stops at `005`). Everything after (Banco, customer, transaction, loyalty, compute, bottega, BYOH) has no migration — schema is `create_all` + a hand-rolled list of **22 raw `ALTER TABLE` statements** that run on every prod boot (`src/db/database.py:115+`). No down-migrations, no drift detection. A column rename has no path.

5. **One Keycloak + one Postgres = single point of failure for all 6 apps + all realms.** 13 containers, zero replication. KC or PG down = everything down at once. This is the same shared-realm fabric that causes the "already logged in" SSO bleed.

6. **Staging shares the prod database/network.** `hetzner/docker-compose.helix-staging.yml` joins the `postgres` network. A staging test that writes/migrates can corrupt prod. There is no real data-tier isolation.

7. **Transaction-number race condition.** `pos_router.py:932` — `TXN-{date}-{count+1}` via `SELECT count(*)` then insert. Two cashiers checking out at once (the whole point of per-cashier drawers) can mint duplicate receipt IDs. Needs a real `pg_sequence`.

### 🟡 Medium — tech debt / hygiene

8. **4,044-line `camper_router.py`**, 2,474-line `pos_router.py`, 2,093-line `bottega_router.py`. Untestable in isolation, merge-conflict magnets.
9. **3 orphaned demo routers** (`bookstore`, `pets`, `tasks`) — not wired, safe to delete.
10. **Repo is 32 GB** with whisper transcripts, `.png` screenshots, raw audio, and `node_modules` tracked-adjacent. Clutter, not danger.
11. **Hardcoded prod IPs in 195 places** — IP change = 195-site find/replace.

---

## PART 2 — THE GRAND VISION (what this actually IS)

Strip away the eight names and there are **three real engines**, and everything else is an application of one of them:

### Engine A — "Swiss-correct vertical ERP on a shared spine"
HelixNet core + the seeding/RBAC/Keycloak fabric. **Banco** (head-shop), **Camper & Tour**, **ISOTTO** are all the *same engine* pointed at a different trade. The vision: *SAP for Swiss SMEs at 1/10th the cost, where each vertical is one config + one realm.* This is the most defensible thing you have because the moat is **captured SOPs** (Felix's 25 years as procedure-as-code), not software anyone can clone.

### Engine B — "Anti-rejection AI reception" (La Piazza / Bottega / Cleo)
The recipe engine + concierge + reception. The vision: *a town square that catches the people the system spits out (the 50+, the squeezed, the rejected) and routes them to an adjacent income they already have the skills for — leverage, not a career jump.* This is the highest *ceiling* and the most *personal* (it's literally Angel's own bridge). It's also the least proven: **zero real users coached to a real win yet.**

### Engine C — "Reverse-CDN compute brokerage" (BYOH / LPCX)
Compute flows *toward* the member's idle GPU instead of to AWS. The vision: *a member-owned compute network we broker.* PoC proven (text→voice→MP4, 6/6). But it's **infrastructure for Engine B** — it has no reason to exist until B has users generating compute jobs.

Plus the **non-software cash engine**: **UFA postcards** — the handshake-and-coffee business that needs no app and is already shipping.

---

## PART 3 — BEST OPS (where to actually point your hours)

Ranked by **(closeness to money) × (defensibility) ÷ (operator hours to get there)**:

| Rank | Bet | State | Time to € | Why |
|------|-----|-------|-----------|-----|
| **1** | **Banco → Felix live** | Staging green, VAT+stock+CSV working | **2–3 wks** | Real customer, real pain, captured SOPs. One TEST-BANCO-002 PASS → prod → invoice. This is the closest real money + the strongest moat. |
| **2** | **UFA postcards** | 3 pilot locations in motion, ISOTTO confirmed | **Now** | Cash, no app, no tech risk. €1.5–2.5k/mo with 3–5 locations. Ceiling capped by *your* legs — needs a local ops partner to scale. |
| **3** | **La Piazza: be your own first user** | App live, Cleo works, loop untested | **8–12 wks** | Highest ceiling, but blocked on *one proven human win*. Dogfood it to land a SAP gig → that case study unlocks everything. Don't add recipes; prove the loop. |
| — | BYOH / LPCX | PoC only | parked | Don't touch until #3 has users needing compute. |

**The decisive fork (this is the real question):** Are you optimizing for **revenue now** or **a credible SAP-bridge proof**?
- Revenue now → **Banco + UFA**, both can hit CHF/€ 5–10k/mo by summer with execution discipline.
- SAP bridge → **become La Piazza's first real user**, land a contract through it, capture the case study.

They're not contradictory, but they spend different hours. Banco is a *known multiplier* (Felix is ready). La Piazza is a *moonshot*. UFA is the cash that buys you time to choose.

---

## PART 4 — THE "FIX ONE SEAL, CHECK ALL SEALS" LIST

Per the CLAUDE.md seal lesson — when you find one problem, find the pattern. The pattern here is **prod has no isolation and no rollback.** The five-seal fix, in order:

1. Rotate every prod secret; scrub `borrowhood.env`/`uat.env` from history.
2. Replace `helix_pass` literals with env-injected secrets.
3. Stop bind-mounting source into prod — build a pinned image, deploy the image, keep a rollback tag.
4. Re-adopt Alembic: autogenerate a baseline from the 67 un-migrated models, retire the raw-ALTER list.
5. Isolate staging from the prod DB + put a `pg_sequence` behind the transaction number.

None of these block shipping Banco. They're the floor under it.

---

*"Measure the whole drive, not just git log." — this is the whole drive.*
