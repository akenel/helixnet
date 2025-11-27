---
error_id: ERROR-020
title: Missing Required Environment Variables
service: helix-platform
error_domain: config
severity: high
resolution_group: config-admin
assignee: devops
first_seen: 2025-11-22
last_seen: 2025-11-27
occurrence_count: 3
in_kb: true
auto_fix: false
fix_command: null
requires_human: true
requires_business_decision: false
related_errors:
  - ERROR-021
keywords: [env, environment, config, variables, missing]
patterns:
  - "environment variable.*not set"
  - "missing.*environment variable"
  - "KeyError.*env"
  - "POSTGRES_USER.*not set"
  - "POSTGRES_DB.*not set"
---

## 🔍 Symptoms
- Docker Compose warnings: "The POSTGRES_USER variable is not set. Defaulting to a blank string."
- Application fails to start with config errors
- Services cannot connect to database (blank credentials)
- HelixNet boot sequence partially fails

## 🧠 Common Causes
1. **Fresh install without helix.env** (40%) - User didn't create .env file
2. **Typo in .env file** (30%) - Variable name misspelled (POSTGRE_USER vs POSTGRES_USER)
3. **env file not sourced** (20%) - Docker Compose not reading .env file
4. **Missing variable after update** (10%) - New version requires new env vars

## 👥 Resolution Group
**Primary:** config-admin (DevOps team)
**Secondary:** None
**Escalation Path:** If .env file is correct → Check Docker Compose version

## 🩺 Diagnosis Steps

### 1. Check if helix.env exists
```bash
ls -lh env/helix.env
```

### 2. Verify required variables are set
```bash
grep -E "POSTGRES_USER|POSTGRES_PASSWORD|POSTGRES_DB" env/helix.env
```

### 3. Check for typos
```bash
# Look for common typos
grep -i "POSTGRE_" env/helix.env  # Should be POSTGRES_
grep -i "KEYCLOACK" env/helix.env  # Should be KEYCLOAK_
```

### 4. Test variable expansion
```bash
source env/helix.env
echo "User: $POSTGRES_USER, DB: $POSTGRES_DB"
```

## ✅ Resolution

### Fix 1: Create Missing .env File
```bash
# Copy from example
cp env/helix.env.example env/helix.env

# Edit with your values
vim env/helix.env

# Restart services
make down && make up
```

### Fix 2: Add Missing Variables
```bash
# Edit helix.env
vim env/helix.env

# Add missing variables (example)
export POSTGRES_USER=helix_user
export POSTGRES_PASSWORD=secure_password_here
export POSTGRES_DB=helix_db

# Restart services
make down && make up
```

### Fix 3: Fix Variable Names (Typos)
```bash
# Find the typo
grep -i "POSTGRE_USER" env/helix.env

# Replace with correct name
sed -i 's/POSTGRE_USER/POSTGRES_USER/g' env/helix.env

# Restart services
make down && make up
```

## 📝 Notes

### Required Environment Variables (as of v2.1.0)

**Core Database:**
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `POSTGRES_PORT` (default: 5432)

**Keycloak:**
- `KEYCLOAK_ADMIN_USER`
- `KEYCLOAK_ADMIN_PASSWORD`
- `KEYCLOAK_DEV_REALM`
- `KEYCLOAK_POS_CLIENT_ID`

**Redis:**
- `REDIS_PASSWORD` (optional)

**MinIO:**
- `MINIO_ROOT_USER`
- `MINIO_ROOT_PASSWORD`

**HelixNet App:**
- `SECRET_KEY`
- `API_V1_STR` (default: /api/v1)
- `PROJECT_NAME`

### Prevention
- Provide `env/helix.env.example` with all required variables
- Add validation script: `scripts/validate-env.sh`
- Document required env vars in README.md

### Common Mistakes
- Forgetting to `export` variables (only needed for shell scripts, not Docker Compose)
- Using spaces around `=` (should be `VAR=value`, not `VAR = value`)
- Quoting issues (use `VAR="value with spaces"`)

## 📜 History
- **2025-11-22** (angel): First occurrence during fresh install (no .env file)
- **2025-11-25** (ralph): Added helix.env.example to repo
- **2025-11-27** (angel): Updated required variables list for v2.1.0

## 🔗 References
- Docker Compose environment variables: https://docs.docker.com/compose/environment-variables/
- HelixNet setup guide: README.md section 2
- Environment variable best practices: [internal wiki]
