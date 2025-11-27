---
error_id: ERROR-001
title: Redis Connection Refused
service: redis
error_domain: technical
severity: medium
resolution_group: tech-devops
assignee: ralph
first_seen: 2025-11-20
last_seen: 2025-11-27
occurrence_count: 7
in_kb: true
auto_fix: true
fix_command: docker restart redis
requires_human: false
requires_business_decision: false
related_errors:
  - ERROR-002
  - ERROR-015
keywords: [redis, connection, network, docker, restart]
patterns:
  - "connection refused.*redis"
  - "Redis.*not reachable"
  - "Error connecting to Redis at"
---

## 🔍 Symptoms
- Application logs show "Redis connection refused"
- Redis container may be stopped or unreachable
- Health checks failing on port 6379
- Worker/Beat services unable to connect to Redis

## 🧠 Common Causes
1. **Redis container not started** (most common - 80%)
2. Network connectivity issue (helixnet_core bridge down)
3. Redis crashed due to out-of-memory (see ERROR-002)
4. Port 6379 already in use by another process
5. Redis configuration error

## 👥 Resolution Group
**Primary:** tech-devops (Ralph)
**Secondary:** None
**Escalation Path:** If auto-fix fails 3x → Check ERROR-002 (OOM), notify Ralph

## 🩺 Diagnosis Steps

### 1. Check if Redis container is running
```bash
docker ps | grep redis
```

### 2. Check Redis logs
```bash
docker logs redis --tail 50
```

### 3. Check network connectivity
```bash
docker network inspect helixnet_core | grep redis
```

### 4. Check port binding
```bash
netstat -tuln | grep 6379
```

### 5. Test Redis connection
```bash
docker exec redis redis-cli ping
```

## ✅ Resolution

### Auto-Fix Available
**Command:** `docker restart redis`

**Success Rate:** 95% (fails only if underlying issue like OOM or network bridge)

### Manual Steps (if auto-fix fails)

1. **Check Docker daemon status:**
   ```bash
   systemctl status docker
   ```

2. **Check available memory:**
   ```bash
   free -h
   ```
   If low memory, check ERROR-002 (Redis OOM)

3. **Check disk space:**
   ```bash
   df -h
   ```

4. **Rebuild Redis container:**
   ```bash
   docker compose -f compose/helix-core/core-stack.yml up -d redis --force-recreate
   ```

5. **Check for port conflicts:**
   ```bash
   lsof -i :6379
   ```
   If another process is using 6379, kill it or change Redis port

## 📝 Notes

### Context-Aware Exceptions
- **During Sunday 3-4am backups:** This error is expected (severity downgraded to "low")
- **After system reboot:** Expected during boot sequence (wait 2 minutes before alerting)

### Performance Impact
- **High:** All async jobs (Celery workers) will fail
- **Medium:** Session storage may fall back to database (slower)
- **User Impact:** Login delays, job queue backup

### Related Issues
- See **ERROR-002** if Redis keeps crashing (OOM issue)
- See **ERROR-015** if network bridge is down (affects all services)

## 📜 History
- **2025-11-20** (angel): First occurrence, resolved by restart
- **2025-11-21** (debllm): Auto-fixed successfully (3 occurrences)
- **2025-11-26** (angel): Added backup exception, linked ERROR-002
- **2025-11-27** (debllm): Auto-fixed during deployment (1 occurrence)

## 🔗 References
- Redis documentation: https://redis.io/docs/
- Docker networking troubleshooting: [internal wiki]
- HelixNet service dependencies: README.md section 4.2
