---
error_id: ERROR-003
title: Postgres Port 5432 Already in Use
service: postgres
error_domain: technical
severity: high
resolution_group: tech-devops
assignee: ralph
first_seen: 2025-11-15
last_seen: 2025-11-27
occurrence_count: 12
in_kb: true
auto_fix: false
fix_command: null
requires_human: true
requires_business_decision: false
related_errors:
  - ERROR-008
keywords: [postgres, port, 5432, conflict, bind]
patterns:
  - "bind.*address already in use.*5432"
  - "port 5432.*already allocated"
  - "Postgres.*failed to start.*port"
---

## 🔍 Symptoms
- Docker fails to start Postgres container
- Error message: "bind: address already in use" on port 5432
- HelixNet fails to boot (Postgres dependency)
- Other services waiting on Postgres health check

## 🧠 Common Causes
1. **Postgres container already running** (60%) - User ran `make up` twice
2. **System Postgres service running** (30%) - Debian default Postgres on 5432
3. **Another container using 5432** (5%) - Leftover container from previous install
4. **Postgres crashed but port still bound** (5%) - Zombie process

## 👥 Resolution Group
**Primary:** tech-devops (Ralph)
**Secondary:** None
**Escalation Path:** If issue persists after manual fix → Check system-level Postgres

## 🩺 Diagnosis Steps

### 1. Check if Postgres container is already running
```bash
docker ps -a | grep postgres
```

### 2. Check what's using port 5432
```bash
lsof -i :5432
# or
netstat -tuln | grep 5432
```

### 3. Check system Postgres service
```bash
systemctl status postgresql
```

### 4. Check for zombie processes
```bash
ps aux | grep postgres
```

## ✅ Resolution

### Manual Fix (No Auto-Fix Available)

#### Option 1: Stop duplicate Postgres container
```bash
# Find the container
docker ps -a | grep postgres

# Stop and remove it
docker stop postgres && docker rm postgres

# Restart HelixNet
make up
```

#### Option 2: Disable system Postgres
```bash
# Stop system Postgres
sudo systemctl stop postgresql

# Disable on boot (optional)
sudo systemctl disable postgresql

# Restart HelixNet
make up
```

#### Option 3: Change HelixNet Postgres port
```bash
# Edit helix.env
vim env/helix.env

# Change POSTGRES_PORT from 5432 to 5433
POSTGRES_PORT=5433

# Update docker-compose port mapping
# Then restart
make nuke && make up
```

## 📝 Notes

### Why No Auto-Fix?
- **Risk:** Stopping wrong Postgres could cause data loss
- **Context needed:** Must verify which Postgres is the "right" one
- **Human decision:** System Postgres vs Docker Postgres

### Prevention
- Add health check before `make up` to detect port conflicts
- Document proper shutdown procedure (`make down` before `make up`)

### Common User Mistakes
- Running `make up` multiple times without `make down`
- Installing system Postgres after HelixNet was already set up
- Not cleaning up after failed Docker installs

## 📜 History
- **2025-11-15** (angel): First occurrence during fresh install (system Postgres running)
- **2025-11-18** (ralph): Added documentation about stopping system Postgres
- **2025-11-22** (angel): 3 occurrences due to user error (double `make up`)
- **2025-11-27** (angel): Updated prevention notes

## 🔗 References
- Docker port binding: https://docs.docker.com/config/containers/container-networking/
- HelixNet Makefile: Check `make down` command
- Postgres troubleshooting: [internal wiki]
