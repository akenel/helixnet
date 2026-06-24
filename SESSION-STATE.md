# SESSION STATE — June 24, 2026

*Last updated: Wed Jun 24, 2026 — Trapani. Banco is the center of gravity; Keycloak identity cleanup in flight.*

> The durable, shared signals live in **`docs/RELEASE-TRAIN.md`** (staging→prod ledger) and
> the memory index (`~/.claude/.../memory/MEMORY.md`). This file is the human-readable "where
> are we today" snapshot. When in doubt, the release train wins.

---

## 🚦 RIGHT NOW

- **Release train:** `🟢 IDLE`. Last shipped = cashier barcode born-once **phantom hotfix** `3a38874` → `banco.lapiazza.app` (Angel mobile PASS 6/6).
- **Two terminals live on `main`:** one on **Keycloak identity cleanup**, one on **Banco**. Coordinate via the release train; don't cross streams (KC config vs app code).

---

## ON DECK (priority order)

### 1. Banco — next prod train (built, NOT yet staged)
- **env-colour login** (per-env organic/mystical palette) + **tighter receipt header** — committed `4587189`, local only.
- **Fix-after from Angel's 06-23 staging PASS:**
  - create-form papercuts ("Pam's fat fingers"): default category, autopop description, name-first ordering — make it forgiving.
  - logo: **file-upload → auto thumbnail + logo** (not a URL field).
  - cash-variance **tolerance configurable in Settings** (±0.20 / 5-CHF).
  - receipt **footer** still needs tightening (header capped in `4587189`).
  - version stamp shows a **stale baked SHA** — fix `get_git_sha` to read live worktree HEAD.
- Then: 🔴 `219d42a1` "Report totals are wrong"; velocity report #2.

### 2. Identity North Star — Keycloak cleanup (other terminal)
- **Four nouns:** Realm = environment (×3: dev/staging/prod), Client = app, Role = permission, Group = shop.
- Cleanup: messy realms → 3 clean ones. Box audit landed `5f13ab3` (12 realms; prod=305 users; `lapiazza-realm-staging` on box = 162 real users, marked INVESTIGATE). **Box deletes stay staging-rehearsal-then-go.**
- Toolbox: `scripts/kc_admin.py` (export-realm backup + provision-business-account). Doc: `docs/HELIX-IDENTITY-ARCHITECTURE.md`.

### 3. Artemis Premium cutover (Banco item → La Piazza listing)
- Path B locked: sold item comes to rest **on La Piazza**, public, premium design + QR. ~80% wired (`square_bridge.create_draft_listing`). Phase-0 schema shipped (`fc152ee`). Depends on the KC business-account wiring. Doc: `docs/BANCO-ARTEMIS-PREMIUM-CUTOVER-PLAN.md`.

### 4. Cleo concierge PoC (design locked, nothing built)
- Ten Lego blocks; first slice = a **service**; scorecard auto-runs; hand-off = prefilled deep-link into La Piazza's existing post flow. Docs: `docs/LP-CLEO-POC-KICKOFF.md`, `docs/LP-CLEO-LEVERAGE-WORKFLOW.md`. Build order: verify the existing post flow → discuss → build the Bottega→Square bridge.

---

## SHIPPED RECENTLY (Banco, June)

Banco live on prod in its own clean container `helix-platform-banco` (`banco.lapiazza.app`).
Zero-perpetual-inventory sprint, BL-87→95 (camera scan, lazy capture, catalog CRUD, scan
hardening, receiving-as-cataloguing, QR), CRM Phase 0, per-cashier cash drawer, Settings +
photo + juicy reports, phantom hotfix. Full ledger: `docs/RELEASE-TRAIN.md`.

## Born Once video series
Season 1 COMPLETE (#01–#08), 5+ live on YouTube. Pipeline: voice + Puppeteer screen capture +
slideshow. Render artifacts (slides/shots, ~249M) are gitignored; only the YouTube kit +
thumbnail per episode is tracked. Bible: `videos/banco/SERIES-BIBLE.md`.

---

*This file is Tigs' working memory. Update it often.*
*"Scan once, known forever." — Banco*
*"One person, one account, one login — that walks into any module they have a role in." — Identity North Star*
*"If one seal fails, check all the seals."*
