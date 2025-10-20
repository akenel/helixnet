# Wait for Keycloak to be fully provisioned first (The check we already cracked)
# This loop should be in your Makefile before this step
# while ! docker exec keycloak curl -fL http://keycloak:8080/realms/master/protocol/openid-connect/certs > /dev/null 2>&1; do sleep 3; done

echo "🌍 [KEYCLOAK] Importing 'helixnet' realm from JSON..."
docker exec keycloak /opt/keycloak/bin/kc.sh \
  import \
  --file /opt/keycloak/data/import/helix-realm.json \
  --realm helixnet 
if [ $? -eq 0 ]; then
  echo "✅ Realm 'helixnet' successfully imported."
else
  echo "❌ Error during realm import. Check Keycloak logs."
  exit 1
fi