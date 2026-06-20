# Runbook — expose Banco at `banco.lapiazza.app`

*Goal: Felix types `banco.lapiazza.app`, lands on his till, live on the internet (Hetzner) — not a laptop.*

**What this is:** a new Caddy hostname → the **existing** `helix-platform` container → the **existing** `/pos`
app. **No code rename, no new app, no `/pos`→`/banco` refactor.** The public sees "Banco"; the engine keeps
serving `/pos`. Identity without the rewrite.

**Box:** `ssh root@46.62.138.218` · **Caddyfile:** `/opt/helixnet/hetzner/Caddyfile`
**App:** `helix-platform` (prod, `helix-platform:8000` on the caddy network) · `helix-platform-staging`
(`127.0.0.1:8099`). **POS realm:** `artemis` (Keycloak).

> ⚠️ **Three landmines, all already learned the hard way:**
> 1. **Caddy stale-inode mount** — *edit the Caddyfile in place (append/`sed`), never replace the file*, or the
>    bind mount goes stale and Caddy serves the old config. Verify with `md5sum`. (Took prod down May 10.)
> 2. **Keycloak redirect URIs** — a new hostname needs its redirect URIs added to the POS client, or login
>    dead-ends with "Incorrect redirect_uri".
> 3. **Never `git pull` in `/opt/helixnet`** — prod runs mounted src; use `git checkout origin/main -- <files>`.

---

## 0. Prereqs
- [ ] **A record:** `banco.lapiazza.app  A  46.62.138.218` (Caddy can't issue TLS until it resolves — `dig +short banco.lapiazza.app` returns the IP).
- [ ] Today's bricks are committed locally (`1289877` Banana+stock, `72157dc` print Z-report) but **not on the box** — Step 1 pushes + deploys them.

## 1. Push + deploy today's bricks  *(staging first — the code gate)*
**From the laptop:**
```bash
cd /home/angel/repos/helixnet
git push origin main                       # lands 1289877 + 72157dc on origin/main
```
**On the box — STAGING worktree, then verify:**
```bash
ssh root@46.62.138.218
cd /opt/helix-staging-tree
git fetch -q origin main
git checkout origin/main -- src/routes/pos_router.py src/templates/pos/closeout.html
docker restart helix-platform-staging
```
- [ ] **Verify on staging:** open `https://staging-bottega.lapiazza.app/pos`, log in (artemis realm,
      `felix`/`helix_pass`), ring one sale, hit **Close Shift → Print Daily Summary** (clean Z-report),
      and `GET /api/v1/pos/reports/daily-summary.csv` (Banana CSV downloads). Stock decremented on the sale.

**Only once staging is green — deploy to PROD:**
```bash
cd /opt/helixnet
git fetch -q origin main
git checkout origin/main -- src/routes/pos_router.py src/templates/pos/closeout.html
docker restart helix-platform
# smoke: curl -sS -o /dev/null -w '%{http_code}\n' https://bottega.lapiazza.app/pos   (expect 200)
```

## 2. Wire `banco.lapiazza.app` in Caddy  *(append in place — never replace the file)*
Append this block to `/opt/helixnet/hetzner/Caddyfile` (it's a clone of the `bottega.lapiazza.app` block,
same backend, plus a root→/pos redirect so the bare host lands on the till):
```bash
cd /opt/helixnet/hetzner
cat >> Caddyfile <<'EOF'

banco.lapiazza.app {
	handle /realms/* { reverse_proxy keycloak:8080 }
	handle /resources/* { reverse_proxy keycloak:8080 }
	handle /js/* { reverse_proxy keycloak:8080 }
	handle /media/* { reverse_proxy minio:9000 }
	# Banco IS the POS — land the bare host on the till.
	@root path /
	redir @root /pos 302
	handle { reverse_proxy helix-platform:8000 }
}
EOF

docker compose -f docker-compose.uat.yml --env-file uat.env restart caddy
# CONFIRM the mount isn't stale -- these two md5s MUST match:
md5sum Caddyfile && docker exec caddy md5sum /etc/caddy/Caddyfile
```
- [ ] The two `md5sum` values are identical (if not: the bind mount is stale — do **not** proceed; recreate
      the caddy container with `docker compose -f docker-compose.uat.yml --env-file uat.env up -d --force-recreate caddy`).
- [ ] `dig` resolves + Caddy issues the TLS cert (give it ~30s; `docker logs caddy --tail 30` shows the cert obtain).

## 3. ⚠️ Keycloak — add the redirect URIs (the bite-you step)
In the Keycloak admin console → realm **`artemis`** → Clients → the **POS client** → Settings:
- **Valid redirect URIs:** add `https://banco.lapiazza.app/*`
- **Valid post-logout redirect URIs:** add `https://banco.lapiazza.app/*`
- **Web origins:** add `https://banco.lapiazza.app`
- Save. (Mirror whatever `bottega.lapiazza.app` already has on that client.)

## 4. Verify live
- [ ] `https://banco.lapiazza.app` → redirects to `/pos` → POS login.
- [ ] Log in (artemis realm) — lands inside, no "Incorrect redirect_uri".
- [ ] Ring a sale → stock decrements · Close Shift → **Print Daily Summary** prints the Z-report · Banana CSV downloads.
- [ ] Show Felix the URL. It's on the internet, not a laptop. 🎯

## Rollback (reversible by design)
- **Caddy:** delete the appended `banco.lapiazza.app {…}` block from `/opt/helixnet/hetzner/Caddyfile`
  (edit in place), `restart caddy`, re-check the `md5sum` match. `bottega.lapiazza.app` is untouched throughout.
- **Code:** `git checkout origin/main~1 -- <files>` + `docker restart helix-platform` reverts the bricks.
- **Keycloak:** the extra redirect URIs are harmless to leave; remove them if desired.
- Nothing destructive: the marketplace, Bottega, and the DB are never touched.

## Staging the hostname too (optional, extra-cautious)
To rehearse the *whole* wiring before prod: add an A record `staging-banco.lapiazza.app`, append the same
Caddy block pointed at `helix-platform-staging` (the staging snippets in `hetzner/Caddyfile.*-snippet` show
the staging pattern), add `https://staging-banco.lapiazza.app/*` to the artemis POS client, verify, then do prod.
