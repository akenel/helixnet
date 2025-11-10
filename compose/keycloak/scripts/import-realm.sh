# Wait for Keycloak to be fully provisioned first (The check we already cracked)
# This loop should be in your Makefile before this step
# while ! docker exec keycloak curl -fL http://keycloak:8080/realms/master/protocol/openid-connect/certs > /dev/null 2>&1; do sleep 3; done

echo "🌍 [KEYCLOAK] Importing 'kc-realm-dev' realm from JSON..."
docker exec keycloak /opt/keycloak/bin/kc.sh \
  import \
  --file ${KC_IMPORT_FILE} \
  --realm ${KEYCLOAK_REALM}
if [ $? -eq 0 ]; then
  echo "✅ Realm '${KEYCLOAK_REALM}' successfully imported."
else
  echo "❌ Error during realm import. Check Keycloak logs."
  exit 1
fi