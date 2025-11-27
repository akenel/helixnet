---
error_id: ERROR-005
title: Keycloak Realm Not Found (kc-realm-dev)
service: keycloak
error_domain: config
severity: critical
resolution_group: config-admin
assignee: devops
first_seen: 2025-11-10
last_seen: 2025-11-25
occurrence_count: 4
in_kb: true
auto_fix: false
fix_command: null
requires_human: true
requires_business_decision: false
related_errors:
  - ERROR-006
  - ERROR-010
keywords: [keycloak, realm, config, import, authentication]
patterns:
  - "Realm.*kc-realm-dev.*not found"
  - "Unknown realm.*kc-realm-dev"
  - "Failed to authenticate.*realm does not exist"
---

## 🔍 Symptoms
- Users cannot log in to POS interface
- Swagger OAuth2 login fails with "Unknown realm"
- Keycloak admin UI shows no realms or wrong realm
- Application logs show realm validation errors

## 🧠 Common Causes
1. **Realm import failed during boot** (50%) - JSON syntax error or missing file
2. **Wrong realm name in config** (30%) - Typo in .env file (kc-realm-dev vs kc-dev-realm)
3. **Keycloak data volume wiped** (15%) - `make nuke` deleted volume
4. **Keycloak version mismatch** (5%) - Realm JSON from older Keycloak version

## 👥 Resolution Group
**Primary:** config-admin (DevOps team)
**Secondary:** tech-devops (if Docker issue)
**Escalation Path:** If realm import fails → Check JSON syntax, review Keycloak logs

## 🩺 Diagnosis Steps

### 1. Check if realm exists in Keycloak
```bash
# Access Keycloak admin UI
# https://keycloak.helix.local/admin

# Or via API
curl -s http://localhost:8180/realms/kc-realm-dev | jq .realm
```

### 2. Check Keycloak logs for import errors
```bash
docker logs keycloak --tail 100 | grep -i "realm\|import\|error"
```

### 3. Verify realm JSON file exists
```bash
ls -lh compose/helix-core/keycloak/realms/
cat compose/helix-core/keycloak/realms/helix-pos-realm-dev.json | jq .realm
```

### 4. Check environment variable
```bash
grep KEYCLOAK_DEV_REALM env/helix.env
```

## ✅ Resolution

### Fix 1: Re-import Realm
```bash
# Stop Keycloak
docker stop keycloak

# Remove data volume (WARNING: loses users/sessions)
docker volume rm helix-core_keycloak_data

# Restart with fresh import
make up

# Verify realm imported
docker logs keycloak | grep "Imported realm"
```

### Fix 2: Manual Realm Import (Keep Data)
```bash
# Copy realm JSON into running container
docker cp compose/helix-core/keycloak/realms/helix-pos-realm-dev.json \
    keycloak:/tmp/realm.json

# Import via Keycloak CLI
docker exec keycloak /opt/keycloak/bin/kc.sh import \
    --override true \
    --file /tmp/realm.json

# Restart Keycloak
docker restart keycloak
```

### Fix 3: Fix Environment Variable
```bash
# Edit helix.env
vim env/helix.env

# Correct the realm name
KEYCLOAK_DEV_REALM=kc-realm-dev  # NOT kc-dev-realm

# Restart services
make down && make up
```

## 📝 Notes

### Data Loss Warning
- **Fix 1** (volume delete) will **DELETE ALL USERS** in Keycloak
- Use Fix 2 if you want to keep existing users (Pam, Ralph, etc.)
- Always backup Keycloak volume before deleting: `docker volume inspect helix-core_keycloak_data`

### Prevention
- Validate realm JSON before committing: `jq . helix-pos-realm-dev.json`
- Check Keycloak logs after `make up` to confirm import
- Document correct realm name in README

### Impact Assessment
- **Critical:** All authentication fails (entire system unusable)
- **User Impact:** No one can log in (Pam, Ralph, Felix all locked out)
- **Downtime:** ~5 minutes to re-import realm

### Related Issues
- **ERROR-006:** Keycloak token expired (different issue, but similar symptoms)
- **ERROR-010:** Redirect URI mismatch (also causes login failures)

## 📜 History
- **2025-11-10** (angel): First occurrence after accidental `make nuke` (deleted volume)
- **2025-11-12** (ralph): Added manual import procedure (Fix 2)
- **2025-11-18** (angel): Typo in .env file caused failure (kc-dev-realm → fixed)
- **2025-11-25** (angel): Updated documentation with data loss warnings

## 🔗 References
- Keycloak import documentation: https://www.keycloak.org/docs/24.0/server_admin/#_export_import
- HelixNet Keycloak setup: README.md section 3.1
- Realm JSON schema: [Keycloak docs](https://www.keycloak.org/docs-api/24.0/rest-api/index.html#_realmrepresentation)
