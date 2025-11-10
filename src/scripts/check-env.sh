#!/usr/bin/env bash
set -e
echo "🔍 Checking required env vars..."
required_vars=(POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB KC_REALM KEYCLOAK_ADMIN_USER)
for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "❌ Missing: $var"
    exit 1
  fi
done
echo "✅ Environment OK."
