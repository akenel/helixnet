#!/usr/bin/env bash
set -euo pipefail

API_URL="http://localhost:8000"
echo "🔑 Requesting token..."
ACCESS_TOKEN=$(curl -s -X POST "${API_URL}/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret" | jq -r '.access_token')

if [[ "$ACCESS_TOKEN" == "null" || -z "$ACCESS_TOKEN" ]]; then
  echo "❌ Failed to obtain token"
  exit 1
fi

echo "✅ Token acquired."
echo "Testing /users/me ..."
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" "${API_URL}/users/me" | jq .

echo "🧪 Creating test record..."
curl -s -X POST "${API_URL}/items" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test item", "description": "E2E test"}' | jq .

echo "✅ Authenticated flow completed successfully!"
