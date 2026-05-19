# Secret Rotation Runbook — Clean Sweep

**Status:** Canonical happy-path
**Last proven:** 2026-05-19 (9/9 secrets rotated, zero rollback, ~50 min keyboard-time)
**Tool:** `scripts/rotate-secrets.sh` (hardened 2026-05-13)
**For when things go wrong:** see `docs/runbooks/secret-rotation.md` (the disaster-recovery flow)

---

## When to use this

- Scheduled annual / quarterly rotation
- Reactive rotation after a suspected leak
- Suspected compromise of any single secret (rotate just that one — script supports per-secret SKIP on Enter)

## When NOT to use this

- If `lapiazza.app` is currently NOT 200 → fix that first, don't rotate on top of broken state
- If you don't have time to do the full upstream pass — partial rotation is safe but leaves you in a weird state to track
- If you don't have current KeePass access — the script paste-then-rotate flow assumes KP is your single source of truth

---

## Prerequisites checklist

Before you start, confirm all of these:

- [ ] You have current SSH access to Hetzner (`ssh root@46.62.138.218` lands at a prompt)
- [ ] You have your KeePass DB open and unlocked
- [ ] You have browser access to all 7 upstream providers (Telegram, Resend, Ollama, KC admin, GitHub, Google Cloud, PayPal Developer)
- [ ] Postgres is healthy on Hetzner (`docker ps | grep postgres` shows healthy)
- [ ] The `python:3.12-slim` Docker image is already pulled on Hetzner (the script uses it for the asyncpg auth test)
- [ ] Docker network is `hetzner_helixnet` (verify with `docker inspect postgres -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'`)
- [ ] You have ~60-90 min of focused time

---

## Step 1 — Pre-flight (5 min)

SSH in and run:

```bash
ssh root@46.62.138.218
cd /opt/helixnet
git pull                                       # ensure latest hardened script

# Pre-flight: confirm everything is green BEFORE we touch state
curl -sk -o /dev/null -w "lapiazza.app: %{http_code}\n" https://lapiazza.app/
docker ps --filter name=borrowhood --format '{{.Names}} {{.Status}}'
docker ps --filter name=postgres --format '{{.Names}} {{.Status}}'
ls -la /opt/helixnet/hetzner/borrowhood.env
docker inspect postgres -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'
docker pull python:3.12-slim 2>&1 | tail -1
```

**All green if:**
- HTTP code: `200`
- borrowhood + postgres: `Up X hours/days (healthy)`
- env file: exists, mode 600, owned by root
- Network: `hetzner_helixnet`
- Image pull: `Image is up to date`

**STOP if any of those fail** — fix the baseline first.

---

## Step 2 — Upstream rotation pass (20-30 min)

Rotate each secret at its upstream provider, save the new value to KeePass **before** moving to the next.

| # | Secret | Where | Action | Save in KP as |
|---|---|---|---|---|
| 1 | Flask secret | terminal: `openssl rand -hex 32` | generate | `LP Prod — Flask SECRET_KEY` |
| 2 | DB password | terminal: `openssl rand -hex 32` | generate (hex-only for psql quoting safety) | `LP Prod — Postgres DB Password` |
| 3 | KC OIDC client | https://lapiazza.app/admin/master/console (or local KC admin) → realm `borrowhood` → Clients → `borrowhood-web` → Credentials → Regenerate | regenerate | `LP Prod — Keycloak borrowhood-web Client Secret` |
| 4 | Telegram bot token | Telegram → @BotFather → `/revoke` → pick bot → confirm | revoke → new token | `LP Prod — Telegram Bot Token` |
| 5 | Resend API key | https://resend.com/api-keys | revoke old, create new | `LP Prod — Resend Email API Key` |
| 6 | Ollama Cloud key | https://ollama.com/settings/keys | delete old, create new | `LP Prod — Ollama Cloud API Key` |
| 7 | PayPal client secret | https://developer.paypal.com/dashboard/applications | regenerate | `LP Prod — PayPal Sandbox Client Secret` |
| 8 | GitHub IDP secret | https://github.com/settings/developers → OAuth app → "Generate a new client secret" | new secret | `LP Prod — Keycloak GitHub OAuth Client Secret` |
| 9 | Google IDP secret | https://console.cloud.google.com/apis/credentials → OAuth client → "Reset Secret" | reset | `LP Prod — KC_GOOGLE_CLIENT_SECRET` |

**Rules of thumb:**
- Save in KeePass **before** closing the provider's page
- For Telegram: `/revoke` immediately kills the old token; do this LAST among the user-facing rotations to minimize the dead-window
- For KC client: regenerating immediately invalidates active logins (~minutes outage). Do LAST before running rotate-secrets.sh
- Naming convention: `LP Prod — <Provider> <Resource Name>` keeps KP browsable

---

## Step 3 — Run the rotator (5-10 min)

```bash
ssh root@46.62.138.218
cd /opt/helixnet
bash scripts/rotate-secrets.sh
```

The script will:
1. Back up `borrowhood.env` to `/opt/backup-2026-05-10/...` (timestamped)
2. Walk you through 9 prompts in order
3. For each: paste from KeePass, see `*` per character (no value echoed), press Enter
4. Empty Enter = SKIP that secret
5. **For BH_DATABASE_URL specifically:** the script does pre-test → ALTER USER → post-test → auto-rollback on fail

**What you'll see for each non-DB prompt:**
```
──── BH_KC_CLIENT_SECRET ────
  Keycloak borrowhood-web OIDC client secret (from KC admin UI).
  current length: 0 chars
  paste new value (Enter = skip): ********************
  updated (20 chars)
```

**What you'll see for the DB prompt (longer, more verification):**
```
──── BH_DATABASE_URL (Postgres password) ────
  Special: password is in URL + must also ALTER USER in Postgres.
  TIP: use hex-only password (openssl rand -hex 32) for safe quoting.
  current user:     lapiazza_app
  current pw chars: 64
  paste NEW password (Enter = skip): ****************************************************************
  pre-test: verifying current env+Postgres are aligned... OK
  altering: ALTER USER lapiazza_app WITH PASSWORD ... done
  post-test: asyncpg connect with new password... OK
  updated env + Postgres aligned (64 chars)
```

**At the end** the script asks `Restart borrowhood container now? [y/N]`. Answer `y`. It restarts and runs a health check.

**Success looks like:**
```
Health check:
    https://lapiazza.app/ -> 200 OK
    OIDC discovery -> 200 OK
```

---

## Step 4 — Post-script: telegram-tigs sync (1 min, ONLY if you rotated Telegram)

The rotate-secrets.sh script only touches `borrowhood.env`. The `telegram-tigs` container reads from `uat.env` and expects the bare name `TELEGRAM_BOT_TOKEN` (no `BH_` prefix). After rotation, sync:

```bash
NEW_TG=$(grep "^BH_TELEGRAM_BOT_TOKEN=" /opt/helixnet/hetzner/borrowhood.env | cut -d= -f2-)

cp /opt/helixnet/hetzner/uat.env /opt/helixnet/hetzner/uat.env.bak-$(date +%Y%m%d-%H%M%S)
awk -v t="$NEW_TG" '/^TELEGRAM_BOT_TOKEN=/{print "TELEGRAM_BOT_TOKEN=" t; next} {print}' \
    /opt/helixnet/hetzner/uat.env > /tmp/uat.env.new
mv /tmp/uat.env.new /opt/helixnet/hetzner/uat.env
chmod 600 /opt/helixnet/hetzner/uat.env

cd /opt/helixnet
docker compose -f hetzner/docker-compose.uat.yml --env-file hetzner/uat.env \
    up -d --force-recreate telegram-tigs
```

Then check `docker logs telegram-tigs --tail 5` — should not say "TELEGRAM_BOT_TOKEN not set".

> Note: telegram-tigs also needs `TELEGRAM_AUTHORIZED_USER_ID` and `ANTHROPIC_API_KEY` to actually function. If those aren't set, the bot will stop after token check. Setup-from-scratch is a separate task — see issue tracker.

---

## Step 5 — Cleanup (2 min)

```bash
# Shred any temp key files left from prep
[ -f /opt/helixnet/hetzner/LP-TMP_KEYS.TXT ] && shred -u /opt/helixnet/hetzner/LP-TMP_KEYS.TXT
[ -f /tmp/new-db-pw.txt ] && shred -u /tmp/new-db-pw.txt
[ -f /tmp/asyncpg_test.py ] && rm -f /tmp/asyncpg_test.py

# Keep the env backups in /opt/backup-2026-05-10/ -- they're recovery anchors
ls -la /opt/backup-2026-05-10/

# Local terminal history: optional but cleaner
history -c
```

On your laptop side (after ending the SSH session): consider clearing terminal scrollback / chat-history if any new secret values appeared in chat by accident.

---

## Step 6 — Verification (5 min)

```bash
# From outside the server (laptop or phone)
curl -sk -o /dev/null -w "HTTP: %{http_code}\n" https://lapiazza.app/
curl -sk -o /dev/null -w "OIDC: %{http_code}\n" https://lapiazza.app/realms/borrowhood/.well-known/openid-configuration

# Login flow sanity (browser, not curl)
# - Open https://lapiazza.app/login
# - Click "Sign in with GitHub" or "Sign in with Google" → confirms IDP secrets work
# - Land in dashboard → confirms KC client secret works
```

Both 200s + working login = 🟢 rotation complete.

---

## What to do if something goes red

| Red condition | What it means | Recovery |
|---|---|---|
| `pre-test: FAIL (AUTH_FAIL)` on DB step | env file's current DB password doesn't actually authenticate (drift exists before you started) | Script aborts safely. See disaster-recovery runbook. Don't continue. |
| `AUTO-ROLLBACK STARTING` after DB rotation | Post-test failed | Script restored env + ALTER'd password back. Investigate `docker logs borrowhood`. |
| Final health check `lapiazza.app != 200` | App startup failed after restart | Auto-rollback runs (env restore + ALTER back + restart). If rollback ALSO fails → manual recovery (see disaster-recovery runbook). |
| `OIDC discovery != 200` | KC client secret is wrong OR realm config drifted | NOT auto-rolled-back (recoverable). Fix the KC client secret in KC admin to match env, restart. |
| login button → blank screen | IDP secret wrong (Google/GitHub) | Update IDP secret in KC admin to match env, no restart needed. |

---

## Post-rotation hygiene

- [ ] Update `docs/runbooks/secret-rotation.md` if you discovered any new failure mode
- [ ] Close out the relevant Backlog item (`BL-XXX` if filed)
- [ ] Update CLAUDE.md memory notes if this rotation surfaced a new lesson
- [ ] Calendar reminder for next scheduled rotation (annual = ~365 days from now)

---

## Why this runbook exists

- The May-12 partial rotation broke prod because we had no script, just manual psql/nano edits
- The May-13 hardening (`rotate-secrets.sh` v2) added pre-test, ALTER USER in-script, post-test, auto-rollback
- The May-19 clean sweep proved the hardened flow works end-to-end with zero rollback
- This runbook captures the May-19 happy path so future rotations follow the same proven flow

**One rule above all others:** never rotate on top of broken state. Pre-flight first, rotate second, verify third.

---

*"If one seal fails, check all the seals. If one window leaks, inspect all the windows."*
*— The Camper & Tour Lesson, 2026-02-06*
