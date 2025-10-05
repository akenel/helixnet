#!/bin/sh

# Wrapper script to handle database migration/seeding before starting the web server.

echo "Waiting for PostgreSQL to be ready... 🐘"
# 1. WAIT FOR DB (Using a simple loop or a dedicated tool like 'wait-for-it.sh')
# Since you likely have a PostgreSQL dependency, this step is CRITICAL.
# Assuming you use the hostname 'postgres' from your docker-compose.yaml:
/usr/local/bin/wait-for-it.sh postgres:5432 --timeout=30 -- echo "PostgreSQL is up! 🟢"

# 2. RUN THE SEED SCRIPT
echo "Running database seeding script... 🌱"
python3 -m app.scripts.seed_users

# 3. START THE MAIN APPLICATION
echo "Starting Uvicorn web server... 🚀"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload