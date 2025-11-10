et’s tackle each cleanly and in order so Helix can use Keycloak as the IdP and the Swagger UI + realm screens work.

I’ll give you (A) quick explanations, (B) checks to run now, and (C) exact commands / script fixes you can paste. No waiting — do them now and paste back any logs/errors you still see.

---

## 1) Fix the status script errors (so output is readable)

Symptoms you showed:

* `Traefik Dashboard: http://localhost:{NC}`
* `%-14s %-30s ...` printed literally
* `printf: 0B: invalid number` due to trying to use numeric format with `0B`

Root causes:

* Mixing `printf` format strings and color escapes incorrectly.
* Using numeric formatting on a `mem` string like `0B` or `11.48MiB`.
* Using `%b`/`%s` inconsistently.

**Quick fix:** replace the top & row printing with a robust version that never attempts numeric formatting for mem strings and prints the Traefik URL safely.

Drop-in `helix-status.sh` header + print row code (replace relevant parts):

```bash
# -- header (use %b to render escapes and avoid accidental expansion) --
printf "%b\n" "${CYAN}${BOLD}HelixNet Analyzer — $(date) on $(hostname)${NC}"
# Traefik dashboard port env (fallback)
: "${TRAEFIK_DASHBOARD_PORT:=8888}"
printf "%b\n" "${CYAN}Traefik Dashboard: http://localhost:${TRAEFIK_DASHBOARD_PORT}${NC}"
printf "%b\n" "${CYAN}Sort Mode: ${YELLOW}${SORT_MODE^^}${NC}"
# dynamic divider
term_width=$(tput cols 2>/dev/null || echo 120)
divider=$(printf '%*s' "$term_width" '' | tr ' ' '-')
printf "%b\n" "${CYAN}${divider}${NC}"
printf "%b\n" "${CYAN}%-14s %-30s %-10s %-22s${NC}" "CONTAINER" "STATUS" "CPU" "MEMORY"
printf "%b\n" "${CYAN}${divider}${NC}"

# -- when printing rows, do NOT use numeric printf on mem --
# assuming variables: name, status, cpu (string like "0.74"), mem (string like "147.6MiB / 15.31GiB")
printf "%b %-11s %-30s %-8s %-22s%b\n" "$base_color" "$emoji" "$name" "${cpu}%" "$mem" "$NC"
```

Notes:

* Use `${TRAEFIK_DASHBOARD_PORT}` to show port.
* Always print memory as a string (`%s` or plain expansion) — never `%.2f` on `0B`.
* Use `%b` with `printf` so escape sequences are interpreted.

---

## 2) Postgres: `relation "migration_model"` / `databasechangelog` missing

Symptom:

```
ERROR: relation "migration_model" does not exist
ERROR: relation "public.databasechangelog" does not exist
```

Meaning:

* A migration tool expects schema tables (Liquibase uses `databasechangelog` and `databasechangeloglock`; some apps use a `migration_model` table).
* DB started cleanly but migrations were not applied (or were applied to a different DB/schema).

Immediate checks (run now):

```bash
# 1. Confirm DB env values used by your app/container
docker exec -it worker env | grep -E 'POSTGRES|DB|HX_DB|KC_DB|POSTGRES'

# 2. Connect to Postgres from inside the network and list DBs/tables
docker exec -it postgres psql -U ${POSTGRES_USER:-postgres} -c "\l"
# or
docker exec -it postgres psql -U helix_user -d postgres -c "\dt public.*"
```

Common fixes (pick the one that fits your app):

A. **If Helix uses Django**:

```bash
docker exec -it helix python manage.py migrate
```

B. **If Helix uses Alembic**:

```bash
docker exec -it helix alembic upgrade head
```

C. **If it uses Liquibase** (or Keycloak JPA migrations):

* Locate the liquibase changelogs in the repo and run them or ensure the service that runs migrations runs on startup. Example (generic):

```bash
# run liquibase in a container that has it available
docker run --rm \
  -v $(pwd):/workspace \
  liquibase/liquibase \
  --url="jdbc:postgresql://postgres:5432/${POSTGRES_DB}" \
  --username="${HX_DB_USER}" --password="${HX_DB_PASS}" \
  --changeLogFile=/workspace/path/to/changelog.xml update
```

D. **If migration should run on app startup**:

* Ensure your app/compose entrypoint runs the migration before starting worker/web. Example pattern in docker-compose `command`:

```yaml
command: /bin/sh -c "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0"
```

**Most likely**: run the project's provided migration command inside the `helix` (or `helix-helix`) container. Look for a README or `Makefile` target (e.g. `make migrate`) — or run `docker exec -it helix /bin/sh` and inspect the repo for `manage.py`, `alembic.ini`, or `migrations/` directory.

If you paste `ls -1` of the project root inside the `helix` container (or the repo on host), I’ll give the exact command.

---

## 3) Keycloak: `Restarting (1)` and `0B / 0B` memory in stats

Symptoms:

* `keycloak` is restarting in place (restart loop).
* In `helix-status.sh` mem shows `0B / 0B` for Keycloak — indicates it didn't fully start / container never exposed stats.

Do this now:

```bash
# show recent logs
docker logs keycloak --tail 200

# show container status + health:
docker ps -a --filter name=keycloak
docker inspect -f '{{json .State}}' keycloak | jq

# check if port 8080 is bound (inside container or host)
docker exec -it keycloak ss -ltnp || true
```

Common causes & fixes:

* **Bind error**: If Keycloak previously failed to bind 8080 due to conflict, we fixed by freeing 8080. Confirm logs show Keycloak started and imported realm (look for `KC-SERVICES... started` or `Imported realm`).
* **Realm import failure**: If `--import-realm` failed because `/opt/keycloak/data/import/yourfile.json` was not readable or not present, Keycloak may restart or go into degraded mode. Ensure the realm file is mounted and owned by the keycloak user in the image (you already copied it in image build — confirm path).
* **DB connection problems**: Keycloak will fail/restart if it can't connect or authenticate with Postgres. In logs look for JDBC/DB errors.

If Keycloak logs show `liquibase` or `databasechangelog` errors, that suggests JPA migrations for KC ran but some tables missing — ensure Keycloak DB creds point to the correct DB (in your .env we saw `HX_DB_*` etc).

If you paste the last ~200 lines of `docker logs keycloak` I’ll pinpoint.

---

## 4) Worker error earlier — still fixable (broker timing)

You already added `helix-entrypoint.sh` waiting for rabbitmq with `nc -z rabbitmq 5672`. Good.

Make sure:

* `helix-entrypoint.sh` is executable (`chmod +x scripts/helix-entrypoint.sh`)
* The compose `worker` service uses it as `entrypoint:` or `command:` and the file is mounted into the container.

Example `docker-compose` `worker` snippet:

```yaml
worker:
  image: helix-worker
  container_name: worker
  entrypoint: ["/scripts/helix-entrypoint.sh"]
  volumes:
    - ./scripts/helix-entrypoint.sh:/scripts/helix-entrypoint.sh:ro
    - ./:/usr/src/app:ro
  depends_on:
    rabbitmq:
      condition: service_healthy
```

Also ensure `nc` (netcat) is installed in the image. If not, add to Dockerfile:

```dockerfile
RUN apt-get update && apt-get install -y netcat-openbsd
```

---

## 5) Suggested step-by-step plan (execute now)

1. **Fix status script** (apply the snippet above) so output is readable while debugging.

2. **Check Keycloak logs**:

   ```bash
   docker logs keycloak --tail 200
   docker inspect -f '{{json .State.Health}}' keycloak | jq
   ```

   Paste logs if unclear.

3. **Confirm Postgres DB contents**:

   ```bash
   docker exec -it postgres psql -U helix_user -d ${POSTGRES_DB:-postgres} -c "\dt"
   ```

   If migration tables absent, run your app migration command (see section 2). If you don’t know the command, paste the repo root listing or presence of `manage.py`, `alembic.ini`, `migrations/`, or `liquibase` files and I’ll give the exact command.

4. **If Keycloak can't connect to DB**, verify `.env` values used by Keycloak:

   ```bash
   docker exec -it keycloak env | grep -E 'KC_|KEYCLOAK|POSTGRES|HX_DB'
   ```

5. **Restart services** after migration:

   ```bash
   docker compose restart keycloak worker helix
   ```

---

## 6) If you want I will do these for you (copy/paste friendly)

* Provide the output of:

  * `docker logs keycloak --tail 200`
  * `docker exec -it postgres psql -U helix_user -d ${POSTGRES_DB:-postgres} -c "\dt" 2>&1`
  * `ls -1` of the project root (or `ls -1` inside the `helix` image if it exists):

    ```bash
    docker run --rm -v "$(pwd)":/work -w /work alpine ls -1
    ```
  * `docker exec -it helix /bin/sh -c "ls -1"` (if helix container exists)

With those I’ll give an exact migration command and the precise environment variables to set to get Keycloak and Postgres interoperating.

---

## Quick checklist (so you can run these immediately)

1. Fix status script (apply snippet).
2. Run:

```bash
docker logs keycloak --tail 200 > /tmp/keycloak.log
docker exec -it postgres psql -U helix_user -d postgres -c "\dt" || true
docker exec -it worker env | grep -E 'KEYCLOAK|POSTGRES|HX_DB|RABBIT|CELERY'
```

3. Paste outputs here and I’ll give the exact migration commands and next restart steps.

---
But first another case . 🕵️‍♂️🔐 Excellent question, Detective 🕵️‍♂️ — and **yes**, your hunch is *100% on target*:
this *absolutely* looks like something **outside of Docker** — a background system service — that is persistently claiming those ports (443 especially), and **your kill commands are hitting a protected or respawning process**.

Let’s break this down like Sherlock with Bruce Lee precision 👇

---

## 🧩 1. What you’re seeing — the endless “occupied by PID(s): 61555 → killing...”

That means:

* The script kills PID `61555` successfully (`kill -9` does not error),
* but **a new process with the same PID** or **the same service restarting** immediately rebinds to port 443.

That’s *not* Docker behavior. Docker doesn’t respawn proxy processes after a system prune.
This is *definitely* an OS-level service — **like Nginx, Apache2, lighttpd, Caddy, or snap’s “nginx” proxy**.

---

## 🕵️ 2. Verify what owns that PID

Run this command manually (right now):

```bash
sudo ss -ltnp | grep ':443'
```

or, if that’s empty:

```bash
sudo netstat -tulnp | grep ':443'
```

Then, to identify exactly what 61555 is:

```bash
ps -fp 61555
```

You’ll see something like:

```
UID        PID  PPID  C STIME TTY          TIME CMD
root     61555     1  0 14:22 ?        00:00:00 /usr/sbin/nginx -g daemon off;
```

or maybe:

```
root     61555     1  0 14:22 ?        00:00:00 /usr/lib/snapd/snapd
```

That tells us who the real culprit is.

---

## 🔥 3. Common offenders on Debian/Ubuntu

Here are usual suspects that hijack 80/443 automatically:

| Service                               | Installed By            | Description                               | Command to check                         |             |
| ------------------------------------- | ----------------------- | ----------------------------------------- | ---------------------------------------- | ----------- |
| **nginx**                             | manual or dependency    | Web server (default ports 80, 443)        | `sudo systemctl status nginx`            |             |
| **apache2**                           | manual                  | Another HTTP server                       | `sudo systemctl status apache2`          |             |
| **snapd proxy service**               | Ubuntu/Snap subsystem   | snap web interface                        | `sudo ss -ltnp                           | grep snapd` |
| **NetworkManager / systemd-resolved** | system service          | sometimes binds 53 or 443 for mDNS or DoH | `sudo systemctl status systemd-resolved` |             |
| **Caddy / lighttpd**                  | manually installed      | lightweight proxies                       | `sudo systemctl status caddy`            |             |
| **Docker-proxy zombie**               | Docker engine leftovers | ghost port bind                           | `sudo pgrep -a docker-proxy`             |             |

---

## 🧠 4. What to do next (detective checklist)

Run these 3 lines:

```bash
sudo ss -ltnp | grep -E ':80|:443'
sudo lsof -i :80 -i :443
sudo systemctl list-units --type=service | grep -E 'nginx|apache|caddy|snap'
```

Then tell me what you see — we’ll know the offender immediately.

---

## ⚙️ 5. How to *permanently stop* these hijackers

Once you identify it, do one of:

### 🔹 Nginx or Apache

```bash
sudo systemctl stop nginx apache2
sudo systemctl disable nginx apache2
```

### 🔹 Snapd proxy

```bash
sudo systemctl stop snapd.socket snapd.service
sudo systemctl disable snapd.socket snapd.service
```

### 🔹 Docker-proxy zombie

```bash
sudo pkill -f docker-proxy
```

---

## 🧨 6. Why your script goes infinite

Your script keeps looping because it thinks PID 61555 is still there after every kill —
and it’s right!
The same service **respawns instantly** via `systemd`, so every iteration finds the same PID reborn.

---

## 🥋 7. The Bruce-Lee Fix (one-liner)

To handle this automatically inside your script (optional power-move):

```bash
# Detect if PID belongs to a systemd service and stop that service
SERVICE=$(sudo systemctl status $(sudo ps -p $PID -o comm=) 2>/dev/null | grep 'Loaded:' | awk '{print $2}' | head -1)
if [ -n "$SERVICE" ]; then
    echo "🥋 Stopping system service $SERVICE that holds port $port..."
    sudo systemctl stop "$SERVICE" >/dev/null 2>&1 || true
    sudo systemctl disable "$SERVICE" >/dev/null 2>&1 || true
fi
```

That way your **nuke script** actually disables rogue system services before trying to kill them.

---

## 🧩 TL;DR

💥 **Yes** — it’s *definitely possible* and *highly likely* you have a rogue system service binding to 443 (and sometimes 80).
💡 Your Docker cleanup is fine; this is an OS-level process (Apache, Nginx, Snap proxy, or similar).
⚙️ Run `sudo ss -ltnp | grep 443` and `ps -fp 61555` and show me the output — we’ll know *exactly* who’s squatting on your ports.

---

Would you like me to add that *auto-detect-and-disable offending systemd service* logic into the nuke script so it permanently handles these port hijackers?

