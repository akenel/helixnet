#!/bin/bash
# =============================================================
# DEPLOY BORROWHOOD TO HETZNER
# =============================================================
# Usage: ssh root@46.62.138.218 "cd /opt/helixnet && bash hetzner/deploy-borrowhood.sh"
# =============================================================
set -e

echo "=== BorrowHood Deploy Starting ==="

# Step 1: Create borrowhood database (idempotent)
echo "--- Creating borrowhood database..."
docker exec -i postgres psql -U helix_user -d helix_db -c "
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'borrowhood') THEN
        CREATE USER borrowhood WITH PASSWORD 'borrowhood_pass';
    END IF;
END
\$\$;
" 2>/dev/null || true

docker exec -i postgres psql -U helix_user -c "
SELECT 'CREATE DATABASE borrowhood OWNER borrowhood'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'borrowhood')
\gexec
" 2>/dev/null || true

docker exec -i postgres psql -U helix_user -c "
GRANT ALL PRIVILEGES ON DATABASE borrowhood TO borrowhood;
" 2>/dev/null || true

echo "--- Database ready."

# Step 2: Build and start borrowhood container
echo "--- Building BorrowHood..."
cd /opt/helixnet
docker compose -f hetzner/docker-compose.uat.yml build borrowhood

echo "--- Starting BorrowHood..."
docker compose -f hetzner/docker-compose.uat.yml up -d borrowhood

# Step 3: Wait for health check
echo "--- Waiting for BorrowHood to be healthy..."
for i in $(seq 1 30); do
    if docker exec borrowhood curl -sf http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo "--- BorrowHood is healthy!"
        break
    fi
    echo "    Waiting... ($i/30)"
    sleep 2
done

# Step 4: Create tables and seed data
echo "--- Creating tables and seeding..."
docker exec borrowhood python3 -c "
import asyncio
from src.database import engine, Base, async_session
from src.models import *
from src.services.seeding import seed_database

async def setup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as db:
        result = await seed_database(db)
        print(f'Seed result: {result}')
    await engine.dispose()

asyncio.run(setup())
"

# Step 5: Restart Caddy to pick up new config (port 8443)
echo "--- Restarting Caddy..."
docker compose -f hetzner/docker-compose.uat.yml restart caddy

# Step 6: Open firewall port
echo "--- Opening port 8443..."
ufw allow 8443/tcp 2>/dev/null || true

# Step 7: Verify
echo ""
echo "=== VERIFICATION ==="
echo "--- BorrowHood health check:"
sleep 3
curl -sk https://localhost:8443/api/v1/health 2>/dev/null || echo "  (Caddy still starting, try in 10s)"

echo ""
echo "=== BorrowHood Deploy Complete ==="
echo "Public URL: https://46.62.138.218:8443/"
echo "API docs:   https://46.62.138.218:8443/api/docs"
echo "Health:     https://46.62.138.218:8443/api/v1/health"
