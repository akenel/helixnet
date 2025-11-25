FYI: Browser Firefox: install rootCA (recommended)

angel@debian:~/repos/helixnet$ sudo cp compose/traefik/ca/rootCA.pem /usr/local/share/ca-certificates/mkcert-rootCA.crt
sudo update-ca-certificates
[sudo] password for angel: 
Updating certificates in /etc/ssl/certs...
0 added, 0 removed; done.
Running hooks in /etc/ca-certificates/update.d...
Updating Mono key store
Mono Certificate Store Sync - version 6.8.0.105
Populate Mono certificate store from a concatenated list of certificates.
Copyright 2002, 2003 Motus Technologies. Copyright 2004-2008 Novell. BSD licensed.

Importing into legacy system store:
I already trust 143, your new list has 144
Import process completed.

Importing into BTLS system store:
I already trust 142, your new list has 144
Certificate added: C=ES, CN=Autoridad de Certificacion Firmaprofesional CIF A62634068
1 new root certificates were added to your trust store.
Import process completed.
Done
done.
angel@debian:~/repos/helixnet$ 

--- 
Use ../ not ./ in the compose folder to load files
 ../compose to load the files from compose volumes folders

🕵️ You’ve cracked the hardest 90% of the TLS puzzle already.
You’re **absolutely correct**: the root issue is SAN (Subject Alternative Name) trust scope and how Traefik (as reverse proxy) presents your mkcert-generated cert chain. Let’s wrap this into a **production-grade pattern** that’s safe, automated, and avoids per-container certificate hacks.

---

## 🧭 TL;DR Summary

✅ **Keep TLS termination in Traefik only**
❌ **Disable TLS in Keycloak** (`KC_HTTPS_ENABLED=false`, `KC_HTTP_ENABLED=true`)
✅ **Trust mkcert’s Root CA at OS + container level** so that containers see Traefik’s certs as valid
✅ **Use SAN-correct certificates (`*.helix.local`)** generated via mkcert and mounted consistently

---

## 🧱 Architecture Diagram

```
Browser  🔒 HTTPS (mkcert SAN *.helix.local)
    ↓
Traefik — TLS termination (cert.pem + key.pem)
    ↓   HTTP  (trusted internal)
Keycloak (KC_HTTP_ENABLED=true)
Helix FastAPI (HTTP)
Postgres / Redis (internal Docker bridge)
```

---

## ⚙️ Step 1 — Create Proper SAN Certificates

Use `mkcert` to generate a wildcard cert that covers all your subdomains:

```bash
mkcert -install
mkcert "*.helix.local" helix.local
```

That produces:

```
./_wildcard.helix.local+1.pem
./_wildcard.helix.local+1-key.pem
```

Rename for consistency:

```bash
mv _wildcard.helix.local+1.pem cert.pem
mv _wildcard.helix.local+1-key.pem key.pem
mkdir -p compose/traefik/certs
mv cert.pem key.pem compose/traefik/certs/
```

This cert already has SANs: `DNS:*.helix.local, DNS:helix.local`.

---

## ⚙️ Step 2 — Mount and Configure in Traefik

In your `docker-compose.yml`:

```yaml
services:
  traefik:
    image: traefik:v3.1
    command:
      - "--providers.file.filename=/etc/traefik/traefik.yml"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./compose/traefik/traefik.yml:/etc/traefik/traefik.yml:ro
      - ./compose/traefik/certs:/etc/traefik/certs:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - helixnet
```

`compose/traefik/traefik.yml`:

```yaml
entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

tls:
  certificates:
    - certFile: /etc/traefik/certs/cert.pem
      keyFile: /etc/traefik/certs/key.pem
```

Then define routers/services in your dynamic config or via labels:

```yaml
  keycloak:
    labels:
      - "traefik.http.routers.keycloak.rule=Host(`keycloak.helix.local`)"
      - "traefik.http.routers.keycloak.entrypoints=websecure"
      - "traefik.http.services.keycloak.loadbalancer.server.port=8080"
```

---

## ⚙️ Step 3 — Fix Keycloak Environment

```yaml
  keycloak:
    environment:
      KC_HTTP_ENABLED: "true"
      KC_HTTPS_ENABLED: "false"
      KC_PROXY_HEADERS: "forwarded"
      KC_HOSTNAME: "keycloak.helix.local"
      KC_PROXY: "edge"
```

This ensures Keycloak trusts Traefik’s forwarded HTTPS headers and knows it’s behind a reverse proxy.

---

## ⚙️ Step 4 — Trust mkcert Root CA Inside Containers

By default, only your **host OS** trusts mkcert’s CA. Containers don’t, so they’ll reject Traefik’s cert (e.g. FastAPI → Keycloak calls).

Here’s how to inject it properly:

```bash
# 1️⃣ Locate mkcert root CA
mkcert -CAROOT
# e.g., /home/angel/.local/share/mkcert

# 2️⃣ Copy into a shared folder
mkdir -p compose/traefik/ca
cp "$(mkcert -CAROOT)/rootCA.pem" compose/traefik/ca/rootCA.pem
```

Then mount it into each container that needs to trust Traefik:

```yaml
  keycloak:
    volumes:
      - ./compose/traefik/ca/rootCA.pem:/usr/local/share/ca-certificates/mkcert.crt:ro
    command: >
      sh -c "update-ca-certificates && /opt/keycloak/bin/kc.sh start"
```

Do the same for FastAPI if it calls Keycloak internally via HTTPS.

---

## ⚙️ Step 5 — `/etc/hosts` for Local Domain Routing

On your host OS (Linux/macOS):

```bash
sudo tee -a /etc/hosts >/dev/null <<EOF
127.0.0.1 helix.local keycloak.helix.local api.helix.local
EOF
```

Now your browser will resolve those names correctly.

---

## 🧩 Step 6 — Verify SAN + Trust

Check SAN:

```bash
openssl x509 -in compose/traefik/certs/cert.pem -text -noout | grep -A1 "Subject Alternative Name"
```

Output should show:

```
DNS:*.helix.local, DNS:helix.local
```

Verify trust:

```bash
curl -vk https://keycloak.helix.local
# should show valid mkcert cert, not "TRAEFIK DEFAULT CERT"
```

---

## 🛡️ Production Readiness Notes

* For real prod: replace mkcert with Let’s Encrypt via Traefik’s ACME config.
* For air-gapped / internal environments, keep mkcert but distribute its rootCA to all trusted hosts/containers.
* Never expose internal Keycloak HTTP directly — Traefik should always handle 443 externally.

---

If you show me your `docker-compose.yml` and `traefik.yml`, I can tune the SAN / CA trust injection lines so that your stack behaves *exactly like production RBAC infra*, with full wildcard TLS chain.
Would you like me to generate that tuned combo next?
  --------------------------

---

angel@debian:~/repos/helixnet$ docker compose stop traefik
[+] Stopping 1/1
 ✔ Container traefik  Stopped                                                                                        10.4s 
angel@debian:~/repos/helixnet$ mkcert -install -cert-file ./certs/cert.pem -key-file ./certs/key.pem helix.local *.helix.local localhost 127.0.0.1
The local CA is already installed in the system trust store! 👍
The local CA is already installed in the Firefox and/or Chrome/Chromium trust store! 👍

ERROR: failed to save certificate: open ./certs/cert.pem: no such file or directory
angel@debian:~/repos/helixnet$ cd traefik
angel@debian:~/repos/helixnet/traefik$ mkcert -install -cert-file ./certs/cert.pem -key-file ./certs/key.pem helix.local *.helix.local localhost 127.0.0.1
The local CA is already installed in the system trust store! 👍
The local CA is already installed in the Firefox and/or Chrome/Chromium trust store! 👍


Created a new certificate valid for the following names 📜
 - "helix.local"
 - "*.helix.local"
 - "localhost"
 - "127.0.0.1"

Reminder: X.509 wildcards only go one level deep, so this won't match a.b.helix.local ℹ️

The certificate is at "./certs/cert.pem" and the key at "./certs/key.pem" ✅

It will expire on 11 January 2028 🗓

angel@debian:~/repos/helixnet/traefik$ openssl x509 -in ./certs/cert.pem -text | grep -A1 'Subject Alternative Name'
            X509v3 Subject Alternative Name: 
                DNS:helix.local, DNS:*.helix.local, DNS:localhost, IP Address:127.0.0.1
angel@debian:~/repos/helixnet/traefik$ docker compose restart traefik
[+] Restarting 1/1
 ✔ Container traefik  Started                                                                                         0.2s 
angel@debian:~/repos/helixnet/traefik$ 

# dynamic/certs.yml
tls:
  certificates:
    - certFile: /etc/traefik/certs/cert.pem
      keyFile: /etc/traefik/certs/key.pem


openssl x509 -in ./certs/cert.pem -text | grep -A1 'Subject Alternative Name'


# Command to generate new, fresh certificates for your domain
# Use the appropriate domain list for your setup (e.g., helix.local, *.helix.local, etc.)
mkcert -install -cert-file ./certs/cert.pem -key-file ./certs/key.pem helix.local *.helix.local localhost 127.0.0.1


    volumes:
      # 1. Traefik Static Config
      - ./traefik.yml:/etc/traefik/traefik.yml:ro
      # 2. Dynamic Config (where certs.yml lives)
      - ./dynamic:/etc/traefik/dynamic:ro
      # 3. Certificates
      - ./certs:/etc/traefik/certs:ro

