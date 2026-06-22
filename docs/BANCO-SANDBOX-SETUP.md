# Banco Sandbox — the empty Day-One instance

> ## ✅ BUILT & LIVE (2026-06-22)
> | | |
> |---|---|
> | **URL** | **https://sandbox-banco.lapiazza.app** (lands on `/pos`, valid TLS) |
> | **Login** | `pam` / `helix_pass` (cashier) — also `felix` / `helix_pass` (admin) |
> | **Reset** (between takes) | `ssh root@46.62.138.218 'cd /opt/helixnet && make sandbox-reset'` |
> | **Run sheet** | `docs/BANCO-DAY-ONE-RUN-SHEET.md` |
>
> Catalogue boots **empty** (0 products, 0 sales, no open drawer). Reset is sub-second,
> idempotent, clears no staff/settings. Container `helix-platform-sandbox` :8097 on its own
> `banco_sandbox` DB — prod's `helix_db` is never touched. Built from `main` (`ecf999d`+).
> **One human gate left:** Angel does the on-phone pass (camera + born-once/photo/label/sell)
> — that's the 1% only a Fairphone can verify.

**Purpose:** the **empty, HTTPS** Banco instance Angel films **Day One** on. See
`BANCO-DAY-ONE-DEMO.md` / `-RUN-SHEET.md` / `-VO-SCRIPT.md`.

---

## Operating it (runs on the Hetzner box, `ssh root@46.62.138.218`)

All four targets live in the repo `Makefile` (run from `/opt/helixnet`):

| Command | What it does |
|---|---|
| `make sandbox-reset` | **The tool.** TRUNCATE the Banco tables (products, transactions, line items, barcodes, stock moves, cash shifts, customers) `RESTART IDENTITY CASCADE`. Re-zero between takes. |
| `make sandbox-up` | Ensure worktree on `origin/main`, create `banco_sandbox` DB if missing, start the container. |
| `make sandbox-down` | Stop the container (hands its RAM back to prod when not filming). |
| `make sandbox-deploy` | Pull latest `origin/main` into the sandbox worktree + restart (code refresh). |

**Reset from your phone (no laptop):** bookmark/alias
`ssh root@46.62.138.218 'cd /opt/helixnet && make sandbox-reset'` — fire it between takes.

**Two kinds of "empty":** reset zeroes the *server*. It can't touch the *phone* — so start
each take with a **fresh tab → Log Out → Log In** (clears the cart + the "already logged in"
SSO state). One line, but skip it and a flubbed take's cart survives the reset.

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
