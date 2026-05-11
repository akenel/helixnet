#!/usr/bin/env bash
# seed-staging-personas.sh -- Provision test personas in BorrowHood staging realm.
#
# Two passes:
#   1. NEW personas (Playwright test fixtures): alice, bob, carol, eve, gia, gemma
#      Created if missing, password set, roles assigned.
#   2. EXISTING demo users (from realm import: anne, angel, dave, etc.):
#      Password set to helix_pass so they're all testable via the same key.
#
# Idempotent: safe to re-run. Existing users are not overwritten -- only their
# password is normalized and any missing roles from our intended set are added.
#
# All passwords: helix_pass (per CLAUDE.md standing rule).
#
# Usage (on Hetzner server):
#   bash scripts/seed-staging-personas.sh
# ============================================================

set -uo pipefail

REALM="${REALM:-borrowhood-staging}"
PASSWORD="${PASSWORD:-helix_pass}"
KC_ADMIN_USER="${KC_ADMIN_USER:-helix_user}"
KC_ADMIN_PASS="${KC_ADMIN_PASS:-helix_pass}"

kcadm() {
    docker exec keycloak /opt/keycloak/bin/kcadm.sh "$@"
}

echo "=== Authenticating kcadm against master realm ==="
kcadm config credentials \
    --server http://localhost:8080 \
    --realm master \
    --user "$KC_ADMIN_USER" \
    --password "$KC_ADMIN_PASS" >/dev/null
echo "OK"
echo ""

# ── Robust upsert: try create, fall through on conflict, always set
#    password + try to assign listed roles ─────────────────────────
ensure_persona() {
    local username="$1"
    local email="$2"
    local first="$3"
    local last="$4"
    shift 4
    local roles=("$@")

    local action="created"

    # Try to create. If exists, that's fine -- we'll just update.
    if kcadm create users -r "$REALM" \
        -s "username=$username" \
        -s "email=$email" \
        -s "firstName=$first" \
        -s "lastName=$last" \
        -s "enabled=true" \
        -s "emailVerified=true" >/dev/null 2>&1; then
        :  # created fresh
    else
        action="updated"
    fi

    # Set password unconditionally (works for new or pre-existing users)
    kcadm set-password -r "$REALM" \
        --username "$username" \
        --new-password "$PASSWORD" >/dev/null 2>&1 || {
            echo "  ✗  $username  could not set password"
            return 1
        }

    # Assign roles (one at a time, ignore failures for missing roles)
    local assigned=()
    for role in "${roles[@]}"; do
        if kcadm add-roles -r "$REALM" \
            --uusername "$username" \
            --rolename "$role" >/dev/null 2>&1; then
            assigned+=("$role")
        fi
    done

    echo "  ✓  $username  ($action)  roles+=[${assigned[*]:-none}]"
}

# ── Ensure password only (for users imported from realm JSON) ─────
# Skip existence check -- just attempt set-password and report.
# set-password is idempotent and only fails if the user truly doesn't exist.
ensure_password_only() {
    local username="$1"
    if kcadm set-password -r "$REALM" \
        --username "$username" \
        --new-password "$PASSWORD" >/dev/null 2>&1; then
        echo "  ✓  $username  password = $PASSWORD"
    else
        echo "  ⊘  $username  not in realm (or password set failed)"
    fi
}

# ── Pass 1: 6 Playwright test personas ────────────────────────────
echo "=== Pass 1: Playwright test personas (6 new, deterministic) ==="
ensure_persona alice  alice@piazza.test  Alice  TestBuyer       bh-member
ensure_persona bob    bob@piazza.test    Bob    TestSeller      bh-member bh-lender
ensure_persona carol  carol@piazza.test  Carol  TestOrganizer   bh-member bh-lender
ensure_persona eve    eve@piazza.test    Eve    TestAdmin       bh-admin bh-moderator
ensure_persona gia    gia@piazza.test    Gia    TrapaniNeighbor bh-member
ensure_persona gemma  gemma@piazza.test  Gemma  SiciliaNeighbor bh-member

# Note: dropped "dave" -- realm import already has "Dave Thompson" who plays
# the same mixed-seller role. We use him via ensure_password_only below.

echo ""
echo "=== Pass 2: Sync helix_pass to demo users from realm import ==="
# These came in via borrowhood-staging-realm.json. They keep their original
# data (workshop name, language, etc.) but get the standard test password.
for u in anne angel dave jake luna marco maria mike nino rosa sally; do
    ensure_password_only "$u"
done

echo ""
echo "=== Final inventory ==="
kcadm get users -r "$REALM" --fields username,email,enabled,firstName,lastName 2>/dev/null \
    | python3 -c "
import json, sys
users = sorted(json.load(sys.stdin), key=lambda u: u.get('username',''))
print(f'  Total: {len(users)} users in realm \"$REALM\"')
print()
print(f\"  {'username':12s}  {'email':32s}  {'name':28s}  enabled\")
print(f\"  {'-'*12:12s}  {'-'*32:32s}  {'-'*28:28s}  -------\")
for u in users:
    name = (u.get('firstName','') + ' ' + u.get('lastName','')).strip()
    print(f\"  {u.get('username',''):12s}  {u.get('email',''):32s}  {name:28s}  {u.get('enabled')}\")
"

echo ""
echo "=== Done. Login URL: https://staging.lapiazza.app/ ==="
echo "All users above use password: $PASSWORD"
echo "First login as each persona auto-creates the BorrowHood DB row via JIT."
