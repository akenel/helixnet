#!/usr/bin/env bash
# 🧠 helix-diagnostics.sh — Verify service endpoints

set -euo pipefail

echo "🔎 Helix Diagnostics — $(date)"
echo "---------------------------------------------"

urls=(
  "https://helix.local/health"
  "https://helix.local/docs"
  "https://keycloak.helix.local/realms/master"
  "https://traefik.helix.local/dashboard/"

  "https://mailhog.helix.local"


  "http://127.0.0.1:9001/browser/"

  "https://rabbitmq.helix.local"
  "https://portainer.helix.local"

)

for url in "${urls[@]}"; do
  printf "Testing %-45s " "$url"
  if [[ $url == *"postgres"* ]]; then
    # special port check for postgres
    (echo > /dev/tcp/postgres/5432) >/dev/null 2>&1 && echo "✅ open" || echo "❌ closed"
  else
    curl -sk -o /dev/null -w "%{http_code} (%{time_total}s)\n" "$url" || echo "❌ failed"
  fi
done

echo "-----keycloak show-config ---"
docker exec -it keycloak /opt/keycloak/bin/kc.sh show-config
echo "✅ Diagnostics complete"
