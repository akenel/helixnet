#!/usr/bin/env bash
set -e

VAULT_ADDR=${VAULT_ADDR}
INIT_FILE=${VAULT_INIT_FILE}

echo ">>> Waiting for Vault to start..."
sleep 5

# Check if already initialized
if vault status | grep -q 'Initialized.*true'; then
  echo "Vault already initialized — skipping init."
else
  echo ">>> Initializing Vault..."
  vault operator init -key-shares=1 -key-threshold=1 -format=json > "$INIT_FILE"
  echo "Saved init info to $INIT_FILE"
fi

UNSEAL_KEY=$(jq -r .unseal_keys_b64[0] "$INIT_FILE")

echo ">>> Unsealing Vault..."
vault operator unseal "$UNSEAL_KEY"

# Optionally log in automatically with root token
ROOT_TOKEN=$(jq -r .root_token "$INIT_FILE")
vault login "$ROOT_TOKEN"

echo ">>> Vault unsealed and ready."
