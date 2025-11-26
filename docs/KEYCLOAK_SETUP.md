# 🔐 Keycloak Setup Guide - HelixPOS Realm Configuration

## Overview

HelixNet uses Keycloak for authentication and RBAC (Role-Based Access Control). This guide covers the POS realm configuration and setup.

## Realm Structure

### Two Realms (Auto-Imported)

1. **`kc-realm-dev`** (existing) - HelixNet Core Development Realm
   - Location: `compose/helix-core/keycloak/realms/helix-keycloak-realm-dev.json`
   - Users: Chuck Norris, Bruce Lee, Jane Auditor, etc.
   - Roles: admin, developer, auditor, guest

2. **`kc-pos-realm-dev`** (new) - HelixPOS Development Realm
   - Location: `compose/helix-core/keycloak/realms/helix-pos-realm-dev.json`
   - Users: Pam (Cashier), Ralph (Cashier), Michael (Manager), Felix (Admin)
   - Roles: pos-cashier, pos-manager, pos-developer, pos-auditor, pos-admin

Both realms are automatically imported on Keycloak startup via the `COPY` directive in `compose/helix-core/Dockerfile.keycloak`.

## POS Realm Configuration

### Display Name
🛒️ HelixPOS 💳️ Development 🏪️ Realm 📦️ kc-pos-realm-dev 💰️

### Roles

| Role | Emoji | Description | Permissions |
|------|-------|-------------|-------------|
| **pos-cashier** | 💰️ | Cashier | Create transactions, scan products, checkout, discounts ≤10% |
| **pos-manager** | 👔️ | Manager | All cashier + product management + reports + unlimited discounts |
| **pos-developer** | 🛠️ | Developer | Create test products, limited production access |
| **pos-auditor** | 📊️ | Auditor | Read-only access to all transactions and reports |
| **pos-admin** | 👑️ | Admin | Full realm control, all permissions |

### Groups

- **💰️ Cashiers** - Front-line POS staff
- **👔️ Managers** - Store managers (includes cashier role)
- **🛠️ Developers** - Dev/test environment access
- **📊️ Auditors** - Compliance and auditing staff
- **👑️ Admins** - System administrators (includes all roles)

### Users (Pre-Seeded)

All users have default password: `helix_pass` (change in production!)

| Username | Name | Email | Role(s) | Employee ID | UUID |
|----------|------|-------|---------|-------------|------|
| `pam` | Pam Beesly | pam.beesly@artemis-store.local | Cashier | POS-001 | `00000000-0000-0000-0000-000000000001` |
| `ralph` | Ralph Wiggum | ralph.wiggum@artemis-store.local | Cashier | POS-002 | `00000000-0000-0000-0000-000000000002` |
| `michael` | Michael Scott | michael.scott@artemis-store.local | Manager, Cashier | MGR-001 | `00000000-0000-0000-0000-000000000003` |
| `felix` | Felix Manager | felix@artemis-store.local | Admin, Manager, Cashier | OWNER-001 | `00000000-0000-0000-0000-000000000004` |
| `pos-developer` | POS Developer | developer@artemis-store.local | Developer | - | Auto-generated |
| `pos-auditor` | Compliance Auditor | auditor@artemis-store.local | Auditor | - | Auto-generated |

**Note**: User IDs match the database UUIDs in `UserModel` for seamless integration!

### Clients

#### 1. `helix_pos_web` (Public Client)
- **Purpose**: Frontend web application for POS terminals
- **Type**: Public (PKCE recommended)
- **Redirect URIs**:
  - `https://helix-platform.local/*`
  - `https://pos.artemis-store.local/*`
  - `http://localhost:8000/*` (dev)
  - `http://localhost:3000/*` (dev)

#### 2. `helix_pos_service` (Confidential Client)
- **Purpose**: Backend API service account
- **Type**: Service Account
- **Secret**: `helix_pass` (change in production!)
- **Grant Types**: Client Credentials

#### 3. `helix_pos_mobile` (Public Client)
- **Purpose**: Mobile POS app for tablets/smartphones
- **Type**: Public
- **Redirect URIs**: `helixpos://oauth/callback`

## Installation & Setup

### Step 1: Move Realm File to Keycloak Import Directory

The realm file needs to be placed in the Keycloak import directory (requires sudo):

```bash
# From repo root
sudo mv helix-pos-realm-dev.json compose/helix-core/keycloak/realms/
sudo chown root:root compose/helix-core/keycloak/realms/helix-pos-realm-dev.json
```

Or via Docker (if container is already running):

```bash
docker cp helix-pos-realm-dev.json keycloak:/opt/keycloak/data/import/
```

### Step 2: Restart Keycloak Container

Keycloak auto-imports realms on startup:

```bash
# Restart just Keycloak
docker restart keycloak

# Or restart entire stack
make down && make up
```

### Step 3: Verify Import

Check Keycloak logs for successful import:

```bash
docker logs keycloak | grep -i "import\|realm"
```

Expected output:
```
INFO  [org.keycloak.services] Importing realm kc-pos-realm-dev from file...
INFO  [org.keycloak.services] Realm kc-pos-realm-dev imported successfully
```

### Step 4: Access Keycloak Admin Console

1. Navigate to: `https://keycloak.helix.local`
2. Login with master admin credentials
3. Select realm: **kc-pos-realm-dev** (from dropdown)
4. Verify users, roles, groups, and clients

### Step 5: Test Authentication

Test login with POS users:

```bash
# Test as cashier (Pam)
curl -X POST https://keycloak.helix.local/realms/kc-pos-realm-dev/protocol/openid-connect/token \
  -d "client_id=helix_pos_web" \
  -d "username=pam" \
  -d "password=helix_pass" \
  -d "grant_type=password"

# Test as manager (Felix)
curl -X POST https://keycloak.helix.local/realms/kc-pos-realm-dev/protocol/openid-connect/token \
  -d "client_id=helix_pos_web" \
  -d "username=felix" \
  -d "password=helix_pass" \
  -d "grant_type=password"
```

## Multi-Environment Strategy

### Same Realm, Different Environments

The `kc-pos-realm-dev.json` file serves as the **template for all environments**:

1. **DEV** - `kc-pos-realm-dev` (auto-imported)
2. **UAT** - Manually import as `kc-pos-realm-uat` (change display name emoji: 🧪️)
3. **PROD** - Manually import as `kc-pos-realm-prod` (change display name emoji: 🚀️)

**Key Point**: Users, roles, groups, and permissions are **identical across all environments**. Only the realm name and emojis change!

### Manual Import for UAT/PROD

1. Access Keycloak Admin Console
2. Click "Add Realm" (top-left dropdown)
3. Click "Import" → Select `helix-pos-realm-dev.json`
4. Edit `realm` field: change `kc-pos-realm-dev` to `kc-pos-realm-uat` or `kc-pos-realm-prod`
5. Edit `displayName`: change emoji to 🧪️ (UAT) or 🚀️ (PROD)
6. Click "Create"

### Why This Approach?

✅ **Consistency** - Same RBAC across environments (no confusion)
✅ **Simplicity** - One source of truth for realm config
✅ **Safety** - No accidental prod changes (separate realms)
✅ **Testing** - Test auth flows in DEV/UAT before PROD
✅ **Audit** - Same role names = consistent audit logs

## Security Considerations

### Development vs Production

**Current Config (Development)**:
- ✅ Registration disabled
- ✅ Brute force protection enabled
- ✅ SSL required (external)
- ✅ Email verification enabled
- ⚠️ Simple passwords (`helix_pass`)
- ⚠️ Long session timeouts (10 hours)

**Production Changes Required**:
1. **Change all passwords** - Use strong, unique passwords
2. **Rotate client secrets** - Change `helix_pass` to secure secrets
3. **Reduce session timeouts** - 30 min idle, 8 hours max
4. **Enable 2FA** - For admin and manager roles
5. **Configure SMTP** - Use real mail server (not MailHog)
6. **Audit logging** - Enable and monitor admin events
7. **IP restrictions** - Limit access to known IPs (optional)

### Password Policy (Recommended for Prod)

Configure in Keycloak Admin Console → Realm Settings → Authentication → Password Policy:

- Minimum length: 12 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character
- Not recently used (last 3 passwords)
- Password expiry: 90 days

## Integration with HelixPOS API

### Configure FastAPI to Use POS Realm

Edit `src/core/config.py`:

```python
KEYCLOAK_REALM = "kc-pos-realm-dev"  # or kc-pos-realm-uat, kc-pos-realm-prod
KEYCLOAK_CLIENT_ID = "helix_pos_web"
KEYCLOAK_CLIENT_SECRET = "helix_pass"  # Change in production!
```

### Enforce RBAC in Endpoints

Example: `src/routes/pos_router.py`

```python
from src.core.local_auth_service import require_roles

@router.post("/products")
async def create_product(
    current_user: UserModel = Depends(require_roles(["💰️ pos-manager", "🛠️ pos-developer"]))
):
    # Only managers and developers can create products
    pass

@router.post("/transactions/{id}/checkout")
async def checkout(
    current_user: UserModel = Depends(require_roles(["💰️ pos-cashier", "👔️ pos-manager"]))
):
    # All POS staff can process checkout
    pass
```

## Troubleshooting

### Realm Not Imported

**Problem**: Realm doesn't appear in Keycloak dropdown

**Solutions**:
1. Check file location: `compose/helix-core/keycloak/realms/helix-pos-realm-dev.json`
2. Check Dockerfile: `COPY compose/helix-core/keycloak/realms/ /opt/keycloak/data/import/`
3. Rebuild Keycloak image: `docker compose build keycloak`
4. Check logs: `docker logs keycloak | grep -i error`

### Users Can't Login

**Problem**: Authentication fails with valid credentials

**Solutions**:
1. Verify realm is selected: `kc-pos-realm-dev`
2. Check user enabled: Admin Console → Users → Find user → Check "Enabled"
3. Reset password: Admin Console → Users → Credentials → Reset Password
4. Check client configuration: Redirect URIs must match exactly

### Roles Not Applied

**Problem**: User authenticated but lacks permissions

**Solutions**:
1. Verify group membership: Admin Console → Users → Groups tab
2. Check role mapping: Admin Console → Groups → Select group → Role Mappings
3. Re-login: Token claims are set at login time
4. Check token payload: Decode JWT at jwt.io

## Reference

- Keycloak Admin Console: `https://keycloak.helix.local`
- Realm Endpoint: `https://keycloak.helix.local/realms/kc-pos-realm-dev`
- Token Endpoint: `https://keycloak.helix.local/realms/kc-pos-realm-dev/protocol/openid-connect/token`
- OIDC Discovery: `https://keycloak.helix.local/realms/kc-pos-realm-dev/.well-known/openid-configuration`

---

**Version**: 1.0.0
**Last Updated**: 2025-11-26
**Status**: Production-Ready (with password changes) ✨
