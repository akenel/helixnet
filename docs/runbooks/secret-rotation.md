# Secret Rotation Runbook — La Piazza Production

**Last rotation:** 2026-05-12 (the day we discovered `borrowhood.env` had been in the public repo for ~3 months)
**Next due:** 2027-05-12 (or sooner if leaked)
**Operator:** Angel Kenel
**Tool:** `scripts/rotate-secrets.sh` (on the Hetzner server)

---

## The 9 KeePass entries

Create these in KeePass under folder: **`La Piazza / Production / App Secrets`**

| # | KeePass Title | Username field (env var) | URL (rotation) | Notes |
|---|---|---|---|---|
| 1 | `LP Prod — Flask SECRET_KEY` | `BH_SECRET_KEY` | (local — no URL) | Signs user session cookies. Generate locally: `openssl rand -base64 32`. **Side effect: kicks out all logged-in users.** |
| 2 | `LP Prod — Postgres DB Password` | `BH_DATABASE_URL_password` | (local — no URL) | The password embedded in `BH_DATABASE_URL`. Generate: `openssl rand -base64 24`. Apply via `ALTER USER borrowhood WITH PASSWORD '<new>';` on postgres. Script rebuilds the URL automatically. |
| 3 | `LP Prod — Keycloak borrowhood-web Client Secret` | `BH_KC_CLIENT_SECRET` | https://lapiazza.app/admin/master/console/#/borrowhood/clients | KC admin UI → borrowhood-web → Credentials tab → Regenerate |
| 4 | `LP Prod — PayPal Sandbox Client Secret` | `BH_PAYPAL_CLIENT_SECRET` | https://developer.paypal.com/dashboard/applications/sandbox | My Apps → your app → Show/Regenerate Secret |
| 5 | `LP Prod — Resend Email API Key` | `BH_RESEND_API_KEY` | https://resend.com/api-keys | Revoke old → Create new → Full access, all domains. Format: `re_xxx...` |
| 6 | `LP Prod — Telegram Bot Token (@LaPiazza2026MAY_Bot)` | `BH_TELEGRAM_BOT_TOKEN` | (Telegram app → @BotFather) | `/mybots` → pick bot → API Token → Revoke current token → copy new. Format: `<bot_id>:<35-char-hash>` |
| 7 | `LP Prod — Ollama Cloud API Key` | `BH_OLLAMA_KEY` | https://ollama.com/settings/keys | Revoke + Create new. Model in use: `gemma3:12b` |
| 8 | `LP Prod — Keycloak GitHub OAuth Client Secret` | `KC_GITHUB_CLIENT_SECRET` | https://github.com/settings/developers | OAuth Apps → La Piazza → Generate new client secret. Then update in KC admin UI: Identity Providers → github → Client Secret |
| 9 | `LP Prod — Keycloak Google OAuth Client Secret` | `KC_GOOGLE_CLIENT_SECRET` | https://console.cloud.google.com/apis/credentials | OAuth 2.0 Client → Reset Secret. Then update in KC admin UI: Identity Providers → google → Client Secret |

---

## KeePass entry template

For each row above, in KeePass:

```
Add Entry (in folder: La Piazza / Production / App Secrets)

Title:    <copy from "KeePass Title" column>
Username: <copy from "Username field" column>
Password: <NEW VALUE you generate / get from the rotation>
URL:      <copy from "URL" column>
Notes:    <copy from "Notes" column>
Tags:     la-piazza, prod, rotation-2026-05-12
Expires:  2027-05-12  (KeePass has an "Expires" field — set it!)
```

The Expires field is the key. KeePass shows expired entries in red — that's your annual rotation reminder, no calendar needed.

---

## Severity order (rotate these first if time-pressured)

| Priority | # | Why |
|---|---|---|
| 🔴 **Critical** | 1 (Flask SECRET_KEY) | Session forgery — attacker can be "logged in as you" |
| 🔴 **Critical** | 2 (Postgres password) | Direct database access — read/write everything |
| 🟠 **High** | 3 (KC client secret) | Impersonate the OIDC client to KC |
| 🟠 **High** | 6 (Telegram bot token) | Take over the bot, send messages from it |
| 🟡 **Medium** | 5 (Resend API key) | Send emails AS La Piazza (phishing-grade) |
| 🟡 **Medium** | 7 (Ollama key) | Burn through AI quota → real $$ |
| 🟢 **Low** | 4 (PayPal sandbox) | Sandbox only — no real money |
| 🟢 **Low** | 8, 9 (GitHub/Google OAuth) | OAuth bridges — narrower attack surface |

---

## The 6 steps to complete a rotation

```
1. (you, browser)   For each KeePass entry without a Password value:
                    - Open the URL
                    - Click Regenerate / Reset / Create
                    - Copy the new value
                    - Paste into the KeePass entry's Password field
                    - Save KeePass

2. (you, terminal)  For the 2 local secrets (BH_SECRET_KEY + DB password):
                    openssl rand -base64 32   (for Flask SECRET_KEY)
                    openssl rand -base64 24   (for Postgres password)
                    Paste outputs into the matching KeePass entries.

3. (you, terminal)  SSH to Hetzner, run the rotation script:
                    ssh root@46.62.138.218 "bash /opt/helixnet/scripts/rotate-secrets.sh"

4. (you, interactive) Script walks through each of the 9 secrets:
                    - Pastes new value from KeePass at each prompt
                    - Press Enter on empty line to skip
                    - Values are hidden as you type (read -s)

5. (script, auto)   Backup taken, env file updated, container restarted,
                    health check on https://lapiazza.app/ and OIDC.
                    Auto-rollback hint if health check fails.

6. (you, cleanup)   When app verified working:
                    ssh root@46.62.138.218 "shred -u /opt/helixnet/hetzner/LP-TMP_KEYS.TXT"
                    (shred overwrites bytes before unlinking — safer than rm)
```

---

## Rollback procedure (if something breaks after rotation)

The script auto-backs up `borrowhood.env` before any change. Backup location:

```
/opt/backup-2026-05-10/borrowhood.env.before-rotation-<TIMESTAMP>
```

To roll back:

```bash
ssh root@46.62.138.218
# Find the latest backup
ls -la /opt/backup-2026-05-10/borrowhood.env.before-rotation-*
# Restore the most recent
cp /opt/backup-2026-05-10/borrowhood.env.before-rotation-<TIMESTAMP> /opt/helixnet/hetzner/borrowhood.env
# Restart container
cd /opt/helixnet
docker compose -f hetzner/docker-compose.uat.yml --env-file hetzner/uat.env up -d --force-recreate borrowhood
# Verify
curl -sk -o /dev/null -w "%{http_code}\n" https://lapiazza.app/
```

---

## Lessons that drive this runbook (so we don't repeat them)

1. **`hetzner/borrowhood.env` was in a PUBLIC git repo for 3+ months** (Feb 28 → May 10, 2026). Found by `grep` in the security review. Fixed by `git rm --cached` + `.gitignore`. **Lesson:** env files NEVER in tracked git. Only `*.env.template` with placeholder values.
2. **The OLD leaked PAT was visible in the BorrowHood git remote URL** — embedded as `https://akenel:ghp_XXXX@github.com/...`. **Lesson:** never embed tokens in remote URLs. Use `gh auth login` or credential helper.
3. **The Tigs ops bot's `TELEGRAM_BOT_TOKEN` was also leaked** via `uat.env` history. **Lesson:** rotate ALL secret-bearing env files, not just the obviously-named one.

---

## How to update this runbook

After each rotation:

1. Update the "Last rotation" date at the top
2. Update "Next due" (~365 days later)
3. If you added/removed a secret, add/remove its row in the table
4. Commit + push: `git add docs/runbooks/secret-rotation.md && git commit -m "ops: rotation YYYY-MM-DD"`

---

*Be water. Stay rotated.*
