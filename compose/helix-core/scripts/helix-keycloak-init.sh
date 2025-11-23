#!/bin/sh
#
# Unified initialization script for Keycloak.
# This wrapper executes the realm import and the Python seeder script.

set -e

# 1. Wait for Keycloak server to be fully responsive
# Keycloak is listening on port 8080 inside the container.
echo "Waiting for Keycloak to start..."
while ! curl -s http://localhost:8080/health | grep -q '"status":"UP"'; do
    sleep 1
done
echo "Keycloak server is UP."

# 2. Import the initial realm configuration (import-realm.sh)
echo "Executing Keycloak Realm Import..."
/opt/keycloak/bin/kc.sh import --dir /tmp/init/realms/

# 3. Run the Keycloak seeder (keycloak_seeder.py)
# NOTE: This assumes your Python seeder handles user/client creation
# and that Python/pip are available in the Keycloak image or run externally.
# Since keycloak containers are often minimal, running Python/pip inside might fail.
# A common pattern is running the seeder from a separate container like helix-main.
# However, assuming keycloak_seeder.py is meant to run here:
if [ -f "/tmp/init/keycloak_seeder.py" ]; then
    echo "Running Keycloak Seeder Script..."
    # Replace 'python3' with the correct interpreter if necessary
    python3 /tmp/init/keycloak_seeder.py
else
    echo "Warning: keycloak_seeder.py not found in /tmp/init. Skipping seeder."
fi

echo "Keycloak initialization complete."