# Banco Sandbox — build handoff (→ Takes)

**Purpose:** the **empty, HTTPS** Banco instance Angel films **Day One** on. This is the
**one gate** before recording — when it's up and the born-once/photo/label flow is in it,
Angel presses record. See `BANCO-DAY-ONE-DEMO.md` / `-RUN-SHEET.md` / `-VO-SCRIPT.md`.

When it's ready, hand Angel **four things**: the **URL**, the **login**, the **reset
command**, and a pointer to `BANCO-DAY-ONE-RUN-SHEET.md`. Then he's ready.

---

## What Takes builds

Pattern to copy: prod Banco = `helix-platform-banco` (port 8098, `/opt/helix-banco-tree`,
`hetzner/docker-compose.banco-prod.yml`, Caddy-routed). Sandbox is a **third sibling**
container on the **same Hetzner box** (reuses Caddy + the public IP + TLS).

1. **Empty database.** A new Postgres DB (e.g. `banco_sandbox`), **separate** from
   prod/staging — never share. Tables created on startup (create_all / migrations).
2. **Seeding OFF.** The app auto-seeds (`pos_seeding_service`, `artemis_product_seeding`).
   Gate it behind a flag so the sandbox starts **empty** (e.g. `HX_SEED_ON_STARTUP=false`
   — add the flag if one doesn't exist). This is the only real code bit.
3. **Container** `helix-platform-sandbox` on a free port (e.g. 8097), env pointed at the
   empty DB, seeding off, on the **SHA that has the born-once + photo + label flow**.
4. **Caddy route** `sandbox-banco.lapiazza.app` → that port (copy the banco-prod block;
   Caddy gives TLS automatically). **HTTPS is non-negotiable — the phone camera won't open
   without a secure context.**
5. **One-command wipe-and-reset.** A script / make target (e.g. `make sandbox-reset`) that
   empties the sandbox product + transaction tables (or drops+recreates the DB) so a
   flubbed take restarts from zero. Must be **one command**, idempotent.

## DNS — Angel's 2 minutes (do first / in parallel)
- **CONFIRMED 2026-06-22 (Takes):** there is **NO `*.lapiazza.app` wildcard** (a random
  subdomain resolves to nothing). `sandbox-banco.lapiazza.app` does **not** resolve yet.
- **→ Angel adds one A record on Porkbun:** `sandbox-banco` → `46.62.138.218` (same Hetzner
  box as `banco.lapiazza.app`). ~2 min. Without it, Caddy can't issue the TLS cert and the
  camera won't open. (Or hand Takes a Porkbun API token and he'll add it.)

---

## Acceptance — what "ready" means (and the hand-off)

- [ ] `https://sandbox-banco.lapiazza.app` loads over **HTTPS** (padlock), shows login.
- [ ] Cashier login works (give Angel the exact user, e.g. `pam` / `helix_pass`).
- [ ] **Catalogue empty** — 0 products, 0 sales; Shop Pulse reads zeros.
- [ ] **Camera opens on the phone** and scans (the HTTPS gate is satisfied).
- [ ] The **born-once → "no scannable code → make a label" → photo → sell** flow is present
      and works end-to-end.
- [ ] `make sandbox-reset` (or whatever it's called) empties it back to zero.

**Hand Angel:** URL · login · reset command · "read `BANCO-DAY-ONE-RUN-SHEET.md`."

---

## Caveats
- **Hetzner is the resource pinch** (prod shares it). A third container is fine for a
  transient demo; just be aware.
- **Realm / "already logged in" SSO bleed** — reusing the shared POS realm is fine for the
  demo (empty *catalogue* is what matters, not a fresh realm). If the "already logged in"
  friction shows, the Log Out → Login path clears it. A per-env realm is a *later* fix, not
  a blocker for filming.
