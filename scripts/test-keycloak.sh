#!/bin/bash

echo "🔍 Testing Keycloak login token retrieval..."

TOKEN=$(curl -s \
  -d "client_id=admin-cli" \
  -d "username=helix_user" \
  -d "password=helix_pass" \
  -d "grant_type=password" \
  "http://localhost:8080/realms/master/protocol/openid-connect/token" \
  | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ FAILED - No token returned"
  exit 1
fi

echo "✅ SUCCESS — Admin token retrieved."
echo "🔑 Token (shortened): ${TOKEN:0:50}..."
