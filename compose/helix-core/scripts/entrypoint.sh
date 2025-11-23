#!/bin/bash
#
# Custom entrypoint to check and import the realm before Keycloak starts.
# We must wait for Keycloak to be UP and ready to accept admin commands (kcadm.sh).

set -e

echo "🧠 Starting Keycloak with Sherlock entrypoint..."


# --- Configuration ---
# Keycloak internal URL and port
KC_INTERNAL_URL="${KC_INTERNAL_URL}"
# Realm name from your JSON file
REALM_NAME="${KEYCLOAK_REALM}"
# Path to the JSON file inside the container, mounted via docker-compose volume
IMPORT_FILE="${KC_IMPORT_FILE}"
# Admin credentials (matching KC_BOOTSTRAP_ADMIN_USERNAME/PASSWORD)
ADMIN_USER="${KC_BOOTSTRAP_ADMIN_USERNAME}"
ADMIN_PASSWORD="${KC_BOOTSTRAP_ADMIN_PASSWORD}"

# --- Utility Function to Wait for Keycloak Service ---
function wait_for_keycloak {
  echo "Waiting for Keycloak service to be available trying a few times.."
  for i in {1..5}; do
    if curl -s --fail "${KC_INTERNAL_URL}/health/ready" > /dev/null; then
      echo "Keycloak is ready!"
      return 0
    fi
    echo "Attempt $i: Keycloak not yet ready. Waiting ..."
    sleep 20
  done
  echo "Error: Keycloak service did not become available within the timeout."
  exit 1
}

# ----------------------------------------------------
# 1. Start Keycloak in the background
# We must start it first so that the DB connection is established and the service is running.
echo "Starting Keycloak server..."
# Note: "&" puts the process in the background. We log its PID.
/opt/keycloak/bin/kc.sh start --optimized --verbose &
KC_PID=$!

# 2. Wait for Keycloak's readiness endpoint
wait_for_keycloak

# 3. Check if the realm already exists via the Admin API
echo "Attempting to check for realm: ${REALM_NAME}"
# Keycloak's built-in Admin CLI tool: kcadm.sh
/opt/keycloak/bin/kcadm.sh config credentials \
    --server "${KC_INTERNAL_URL}" \
    --realm master \
    --user "${ADMIN_USER}" \
    --password "${ADMIN_PASSWORD}" > /dev/null

REALMS_LIST=$(/opt/keycloak/bin/kcadm.sh get realms | grep "\"realm\":\"${REALM_NAME}\"")

if [[ -z "${REALMS_LIST}" ]]; then
  echo "Realm '${REALM_NAME}' not found. Importing now..."
  
  # 4. Import the realm using kcadm.sh
  /opt/keycloak/bin/kcadm.sh create realms -f "${IMPORT_FILE}"
  
  if [ $? -eq 0 ]; then
    echo "Successfully imported realm: ${REALM_NAME}"
  else
    echo "Error during realm import."
    # We exit here so the container stops and alerts the user of the failure
    kill $KC_PID
    exit 1
  fi
else
  echo "Realm '${REALM_NAME}' already exists. Skipping import."
fi

# 5. Bring Keycloak process to the foreground
# This ensures the container stays running and outputs the normal logs
echo "Realm setup complete. Attaching to Keycloak logs..."
wait $KC_PID
#!/bin/bash
# Keycloak Entrypoint Script

# If you need to wait for the database before Keycloak starts (highly recommended),
# you would add a 'wait-for-it.sh' or similar script here.

# Note: Keycloak automatically performs realm imports if KC_IMPORT_FILE is set
# when the server starts, so we don't need explicit import logic here.

# --- Core Setup ---

# Ensure the Keycloak data directory and imported realm file have the correct ownership
# The Keycloak container often runs as user 1000, but the build might have used root.
chown -R 1000:1000 /opt/keycloak/data
chmod +x /opt/keycloak/bin/kc.sh

echo "Starting Keycloak server with command: /opt/keycloak/bin/kc.sh start --optimized"

# Execute the main Keycloak start command
exec /opt/keycloak/bin/kc.sh start --optimized