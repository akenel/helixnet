# SOP — Expose LPCX on compute.lapiazza.app

*Standard Operating Procedure. Status: DRAFT (blocked on DNS — step 1 is Angel's).*

**Goal:** make the La Piazza Compute Exchange (helix-platform) reachable at
`https://compute.lapiazza.app` on the Hetzner UAT box (46.62.138.218), without
disturbing the existing `lapiazza.app` (borrowhood) prod routing.

**Why a new subdomain:** Caddy on that box serves the `lapiazza.app` vhost →
`borrowhood:8000`. LPCX is a *different app* (`helix-platform:8000`). A separate
subdomain keeps them cleanly apart and is the least-risk change.

---

## Step 1 — DNS (Angel, prerequisite — nothing else works until this is done)

Add an **A record** at the lapiazza.app DNS provider:

```
compute.lapiazza.app.   A   46.62.138.218
```

Verify it propagates before continuing:

```
dig +short compute.lapiazza.app      # must return 46.62.138.218
```

Caddy uses ACME (Let's Encrypt) — it can only mint the HTTPS cert once the name
resolves to the box. No DNS → no cert → no site.

## Step 2 — Add the Caddy site block

In `/opt/helixnet/hetzner/Caddyfile`, **below** the `lapiazza.app, borrowhood.duckdns.org`
block, add (mirrors the existing pattern but proxies to **helix-platform**):

```caddy
compute.lapiazza.app {
    handle /realms/*    { reverse_proxy keycloak:8080 }
    handle /resources/* { reverse_proxy keycloak:8080 }
    handle /js/*        { reverse_proxy keycloak:8080 }
    handle /media/*     { reverse_proxy minio:9000 }
    handle              { reverse_proxy helix-platform:8000 }
}
```

## Step 3 — Reload Caddy (zero-downtime; does NOT touch lapiazza.app)

```
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
docker logs caddy --tail 20    # confirm cert issued for compute.lapiazza.app, no errors
```

If the reload errors, the old config stays live — lapiazza.app keeps serving.

## Step 4 — Verify

```
curl -s https://compute.lapiazza.app/api/v1/health        # expect healthy JSON
curl -s -o /dev/null -w "%{http_code}" https://compute.lapiazza.app/compute   # expect 200
```

Then open `https://compute.lapiazza.app/compute` in a browser → the LPCX dashboard.

---

## KNOWN GAP — login won't work yet (must fix before it's usable)

The dashboard's login is wired to realm **`kc-camper-service-realm-dev`** (local name).
UAT Keycloak's realm is **`helix-camper-service-realm-dev`** (different name), and its
test users / roles aren't confirmed. So the page will *load* but **auth will fail**.

To make it actually usable on UAT, one of:
- Make the dashboard's KC realm **configurable** (env/template var) instead of hardcoded, and point it at the UAT realm; OR
- Confirm/seed camper test users (`camper-qa-tester`/`manager`/`admin`, `helix_pass`) in `helix-camper-service-realm-dev`.

Track this as its own task — exposure (this SOP) gets the page up; auth is a separate fix.

## Dry-run option (recommended first)

Before touching the prod box's Caddyfile, prove the block on a throwaway subdomain or
on staging: add the block, reload, confirm cert + 200, then delete. Validates syntax +
routing with zero risk to `lapiazza.app`.

## Alternative — the DigitalOcean box (€5/mo)

Angel has a small separate DO server. Cleaner long-term option: host LPCX (helix-platform
+ rabbitmq + consumer) **there**, point `compute.lapiazza.app` at the DO box, and leave the
Hetzner box entirely to borrowhood/La Piazza. Full isolation, no shared-Caddy risk. Heavier
(deploy the stack to DO) — only worth it if LPCX becomes its own product. Park for now.

---

## Rollback

Remove the `compute.lapiazza.app { ... }` block from the Caddyfile, `caddy reload`.
helix-platform keeps running headless; lapiazza.app is never affected.

*The square goes up beside the old one, not on top of it.*

---

## Deploying updates to bottega.lapiazza.app — and THE RULE (2026-06-05)

`bottega.lapiazza.app` is **live** (helix-platform on the Hetzner box). It has **dev**
(`helix.local`) and **public** (`bottega.lapiazza.app`) — **no staging of its own**. The
`staging.lapiazza.app` that exists belongs to the *marketplace* (borrowhood), not Bottega.

### THE RULE: a Bottega deploy is a PROD-BOX deploy

`bottega.lapiazza.app` rides the **same box, Postgres, Keycloak, and Caddy as PROD
`lapiazza.app`** (real traffic). There is no isolation. So treat every Bottega deploy
with prod care, even though Bottega itself has ~0 users yet:

1. **Gate on dev first.** Before touching the box, on `helix.local`:
   - `./scripts/smoke-test.sh local`
   - `node tests/e2e/console-sweep.js` (anon + 3 personas)
   Both green, or don't deploy.
2. **Deploy = pull + restart (no rebuild; `src` is bind-mounted):**
   ```
   ssh root@46.62.138.218 'cd /opt/helixnet && git pull --ff-only origin <branch> \
     && docker restart helix-platform lpcx-consumer'
   ```
   (Rebuild ONLY when pip deps change — e.g. PyMuPDF/python-docx for CV upload.)
3. **Verify public + confirm prod is untouched:**
   ```
   curl -sk -o /dev/null -w "%{http_code}\n" https://bottega.lapiazza.app/
   curl -sk -o /dev/null -w "%{http_code}\n" https://lapiazza.app/   # MUST stay 200
   ```
4. **Reversible:** to roll back, `git checkout <prev-sha>` + `docker restart helix-platform`.
5. **Caddy edits are the sharp edge.** Editing the box Caddyfile with `sed -i` swaps the
   inode out from under the running container (it keeps reading the old one) — the bug
   that nearly bit us 2026-06-05. **Always:** append-only edit → `caddy validate` a
   throwaway container against the on-disk file → `docker restart caddy`. Never reload
   blind.

### When to graduate (YAGNI until then)

Add real isolation the day **either** happens:
- Bottega gets its **first real user**, OR
- you need to ship something **risky** (DB migration, dependency rebuild, schema change).

Then: stand up `staging.bottega.lapiazza.app` → a second helix-platform container, OR
move helix-platform to its **own box** (the DO option above) so Bottega experiments can
never threaten the marketplace. Not before. Build what the real need reveals.
