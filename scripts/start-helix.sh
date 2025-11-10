#!/usr/bin/env bash
set -e

# echo "🔐 Updating CA certificates..."
# update-ca-certificates

echo "🚀 Starting Helix API..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
