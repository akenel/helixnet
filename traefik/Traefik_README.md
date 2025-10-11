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