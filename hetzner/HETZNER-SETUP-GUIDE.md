# Hetzner UAT Server -- Setup Guide

**Goal:** Standalone HelixNet UAT environment on Hetzner Cloud.
No tunnels, no laptop dependency. Anne (or anyone) can test 24/7.

**Cost:** EUR 7.59/month (CX32: 4 vCPU, 8GB RAM, 80GB SSD)

---

## STEP 1: Create a Cloud Project

1. Go to https://console.hetzner.com/projects
2. Click **"+ New Project"**
3. Name it: **HelixNet-UAT**
4. Click into the project

---

## STEP 2: Add Your SSH Key

Before creating the server, add your SSH key so you can log in without a password.

1. Inside your project, go to **Security** (left sidebar) > **SSH Keys**
2. Click **"Add SSH Key"**
3. On your laptop, copy your public key:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```
   (or `~/.ssh/id_rsa.pub` if you use RSA)
4. Paste the key into the Hetzner form
5. Name it: **angel-laptop**

---

## STEP 3: Create the Server

1. Inside your project, click **"+ Create Server"** (big button, top right)
2. Configure:

| Setting | Value |
|---------|-------|
| **Location** | Falkenstein (FSN1) -- cheapest EU location |
| **Image** | Ubuntu 24.04 |
| **Type** | Shared vCPU (x86) |
| **Plan** | **CX32** -- 4 vCPU, 8GB RAM, 80GB SSD -- EUR 7.59/mo |
| **Networking** | Public IPv4 + IPv6 (default) |
| **SSH Key** | Select **angel-laptop** (the key you just added) |
| **Name** | `helixnet-uat` |

3. Click **"Create & Buy Now"**
4. Wait ~30 seconds. You'll see your server with its **public IP address**.
5. **Write down the IP** -- you'll need it everywhere.

---

## STEP 4: SSH Into the Server

```bash
ssh root@YOUR_HETZNER_IP
```

If it asks about the fingerprint, type `yes`.

You should see the Ubuntu welcome screen. You're in.

---

## STEP 5: Install Docker

Run these commands on the Hetzner server:

```bash
# Update system
apt update && apt upgrade -y

# Install Docker (official method)
curl -fsSL https://get.docker.com | sh

# Verify
docker --version
docker compose version
```

---

## STEP 6: Configure Firewall

```bash
# Allow SSH, HTTP, HTTPS
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

Type `y` when asked. That's it -- only SSH and web traffic allowed.

---

## STEP 7: Clone the Repository

```bash
cd /opt
git clone https://github.com/akenel/helixnet.git
cd helixnet
```

If the repo is private, you'll need to set up a deploy key or use a personal access token:
```bash
git clone https://YOUR_GH_TOKEN@github.com/akenel/helixnet.git
```

---

## STEP 8: Configure for Your IP

Replace `YOUR_HETZNER_IP` with the actual IP everywhere:

```bash
cd /opt/helixnet/hetzner

# Update Caddyfile
sed -i "s/YOUR_HETZNER_IP/$(curl -s ifconfig.me)/g" Caddyfile

# Create .env override for the public hostname
echo "HELIX_PUBLIC_HOST=$(curl -s ifconfig.me)" > .env
```

**Verify the Caddyfile looks right:**
```bash
cat Caddyfile
```

You should see `https://123.45.67.89 {` (your actual IP).

---

## STEP 9: Update Keycloak Redirect URIs

The realm JSON needs the Hetzner IP in its allowed redirect URIs.

```bash
cd /opt/helixnet
HETZNER_IP=$(curl -s ifconfig.me)

# Add the Hetzner URL to Keycloak's allowed redirects
python3 -c "
import json
f = 'compose/helix-core/keycloak/realms/helix-camper-service-realm-dev.json'
with open(f) as fh: d = json.load(fh)
for c in d.get('clients', []):
    if c.get('clientId') == 'camper_service_web':
        uri = f'https://${HETZNER_IP}/*'
        origin = f'https://${HETZNER_IP}'
        if uri not in c.get('redirectUris', []):
            c['redirectUris'].append(uri)
        if origin not in c.get('webOrigins', []):
            c['webOrigins'].append(origin)
# Clear realm-level frontendUrl (KC_HOSTNAME_URL takes priority)
d.get('attributes', {})['frontendUrl'] = ''
d.get('attributes', {})['adminUrl'] = ''
with open(f, 'w') as fh: json.dump(d, fh, indent=2)
print('Done - redirect URIs updated')
"
```

---

## STEP 10: Build and Start

```bash
cd /opt/helixnet/hetzner
docker compose -f docker-compose.uat.yml up -d --build
```

This will:
1. Build the Keycloak custom image (imports realms)
2. Build the helix-platform image (installs Python deps)
3. Start PostgreSQL, wait for healthy
4. Start Keycloak, wait for healthy
5. Start Redis + RabbitMQ
6. Start helix-platform
7. Start Caddy (HTTPS reverse proxy)

**First boot takes 3-5 minutes.** Watch the progress:

```bash
docker compose -f docker-compose.uat.yml logs -f
```

Wait until you see:
- `postgres | database system is ready to accept connections`
- `keycloak | Keycloak ... started in Xs`
- `helix-platform | Starting FastAPI Platform...`

---

## STEP 11: Verify

```bash
# Check all containers are healthy
docker ps --format "table {{.Names}}\t{{.Status}}"

# Test the app
curl -sk https://localhost/camper -o /dev/null -w "%{http_code}\n"
# Should return: 200
```

Open in your browser: `https://YOUR_HETZNER_IP/camper`

Accept the self-signed cert warning, then login as **nino** / **helix_pass**.

---

## STEP 12: Add SSH Alias (On Your Laptop)

Add this to `~/.ssh/config` on your laptop:

```
Host helix-uat
    HostName YOUR_HETZNER_IP
    User root
    IdentityFile ~/.ssh/id_ed25519
```

Now you can just type `ssh helix-uat` to connect.

---

## OPTIONAL: Add a Domain (Real HTTPS Cert)

If you point a domain to the Hetzner IP, Caddy auto-provisions a Let's Encrypt cert.

1. **Add a DNS A record:** `uat.yourdomain.com` -> `YOUR_HETZNER_IP`
2. **Update Caddyfile:** Switch from Option A (IP) to Option B (domain)
3. **Update KC_HOSTNAME_URL** in docker-compose.uat.yml to `https://uat.yourdomain.com`
4. **Restart:** `docker compose -f docker-compose.uat.yml up -d`

Caddy handles the rest -- no certbot, no cron jobs, no renewal headaches.

---

## MAINTENANCE

**View logs:**
```bash
docker compose -f docker-compose.uat.yml logs -f helix-platform
```

**Restart a service:**
```bash
docker compose -f docker-compose.uat.yml restart helix-platform
```

**Pull latest code and rebuild:**
```bash
cd /opt/helixnet
git pull
cd hetzner
docker compose -f docker-compose.uat.yml up -d --build
```

**Full reset (nuclear option):**
```bash
docker compose -f docker-compose.uat.yml down -v
docker compose -f docker-compose.uat.yml up -d --build
```

**Check disk space:**
```bash
df -h /
docker system df
```

**Prune old images:**
```bash
docker system prune -af
```

---

## RESOURCE USAGE (Expected)

| Service | RAM | CPU |
|---------|-----|-----|
| PostgreSQL | ~300MB | Low |
| Keycloak | ~800MB | Moderate at startup |
| Redis | ~50MB | Minimal |
| RabbitMQ | ~150MB | Low |
| helix-platform | ~200MB | Low |
| Caddy | ~30MB | Minimal |
| **Total** | **~1.5GB** | Leaves 6.5GB headroom |

The CX32 with 8GB RAM gives you plenty of room to grow.

---

## COSTS

| Item | Monthly |
|------|---------|
| Hetzner CX32 | EUR 7.59 |
| Public IPv4 | included |
| 80GB SSD | included |
| Domain (optional) | EUR 0-1 |
| **Total** | **EUR 7.59/mo** |

Compare: DigitalOcean equivalent (4 vCPU / 8GB) = $48/mo.

---

*Generated: Feb 17, 2026 | HelixNet UAT Deployment Guide*
