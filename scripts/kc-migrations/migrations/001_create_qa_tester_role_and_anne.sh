#!/bin/bash
# ================================================================
# Migration 001: Create QA tester role, group, and Anne's account
#
# Realm:  kc-camper-service-realm-dev
# Date:   2026-02-22
# Author: Angel + Tigs
#
# Creates:
#   - Role:  camper-qa-tester
#   - Group: QA Testers (with camper-qa-tester role mapped)
#   - User:  anne (Anne Muthoni, in QA Testers group)
# ================================================================

set -euo pipefail

KC_CONTAINER="${KC_CONTAINER:-keycloak}"
REALM="kc-camper-service-realm-dev"

# Helper: run kcadm inside the keycloak container
kc() {
    docker exec "${KC_CONTAINER}" /opt/keycloak/bin/kcadm.sh "$@" 2>/dev/null
}

echo "    [001] Creating camper-qa-tester role, QA Testers group, and Anne..."

# ---------------------------------------------------------------
# Step 1: Create realm role "camper-qa-tester"
# ---------------------------------------------------------------
if kc get roles -r "${REALM}" --fields name | grep -q '"camper-qa-tester"'; then
    echo "    [001] Role camper-qa-tester already exists. Skipping."
else
    kc create roles -r "${REALM}" \
        -s name=camper-qa-tester \
        -s "description=QA tester - Testing dashboard, bug reporting, test execution, verification."
    echo "    [001] Created role: camper-qa-tester"
fi

# ---------------------------------------------------------------
# Step 2: Create group "QA Testers"
# ---------------------------------------------------------------
if kc get groups -r "${REALM}" | grep -q '"QA Testers"'; then
    echo "    [001] Group QA Testers already exists. Skipping."
else
    kc create groups -r "${REALM}" \
        -s 'name=QA Testers'
    echo "    [001] Created group: QA Testers"
fi

# ---------------------------------------------------------------
# Step 3: Map camper-qa-tester role to QA Testers group
# ---------------------------------------------------------------

# Get group ID
GROUP_ID=$(kc get groups -r "${REALM}" | grep -B2 '"QA Testers"' | grep '"id"' | head -1 | sed 's/.*: "\([^"]*\)".*/\1/')

if [ -z "$GROUP_ID" ]; then
    echo "    [001] ERROR: Could not find QA Testers group ID."
    exit 1
fi

# Check if role already mapped to group
if kc get "groups/${GROUP_ID}/role-mappings/realm" -r "${REALM}" | grep -q '"camper-qa-tester"'; then
    echo "    [001] Role mapping already exists. Skipping."
else
    # Get role ID
    ROLE_ID=$(kc get roles/camper-qa-tester -r "${REALM}" --fields id | grep '"id"' | head -1 | sed 's/.*: "\([^"]*\)".*/\1/')

    if [ -z "$ROLE_ID" ]; then
        echo "    [001] ERROR: Could not find camper-qa-tester role ID."
        exit 1
    fi

    kc create "groups/${GROUP_ID}/role-mappings/realm" -r "${REALM}" \
        -b "[{\"id\":\"${ROLE_ID}\",\"name\":\"camper-qa-tester\"}]"
    echo "    [001] Mapped camper-qa-tester role to QA Testers group."
fi

# ---------------------------------------------------------------
# Step 4: Create user "anne"
# ---------------------------------------------------------------
if kc get users -r "${REALM}" -q username=anne | grep -q '"anne"'; then
    echo "    [001] User anne already exists. Skipping creation."
else
    kc create users -r "${REALM}" \
        -s username=anne \
        -s firstName=Anne \
        -s lastName=Muthoni \
        -s email=anne@helixnet.test \
        -s enabled=true \
        -s emailVerified=true \
        -s 'credentials=[{"type":"password","value":"helix_pass","temporary":false}]'
    echo "    [001] Created user: anne"
fi

# ---------------------------------------------------------------
# Step 5: Ensure Anne is in QA Testers group
# ---------------------------------------------------------------
USER_ID=$(kc get users -r "${REALM}" -q username=anne --fields id | grep '"id"' | head -1 | sed 's/.*: "\([^"]*\)".*/\1/')

if [ -z "$USER_ID" ]; then
    echo "    [001] ERROR: Could not find anne user ID."
    exit 1
fi

# PUT is idempotent -- adding to a group user is already in returns 204
kc update "users/${USER_ID}/groups/${GROUP_ID}" -r "${REALM}" -s realm="${REALM}" -s userId="${USER_ID}" -s groupId="${GROUP_ID}" -n
echo "    [001] Ensured anne is in QA Testers group."

echo "    [001] Done."
