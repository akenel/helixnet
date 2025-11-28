---
error_id: ERROR-060
title: Celery Tasks Stuck in PENDING State (Worker Not Processing)
service: worker
error_domain: technical
severity: high
resolution_group: tech-devops
assignee: ralph
first_seen: 2025-11-28
last_seen: 2025-11-28
occurrence_count: 1
in_kb: true
auto_fix: true
fix_command: docker restart worker beat
requires_human: false
requires_business_decision: false
related_errors:
  - ERROR-001
  - ERROR-061
keywords: [celery, worker, pending, queue, rabbitmq, tasks, stuck, async]
patterns:
  - "Task.*PENDING.*timeout"
  - "celery.*worker.*not responding"
  - "worker.*heartbeat.*missed"
  - "task.*queued.*not executed"
  - "Received.*tasks.*pending"
---

## 🔍 Symptoms
- Daily sales report not generated (scheduled task didn't run)
- Flower dashboard shows 50+ tasks in PENDING state
- API calls that trigger async tasks return quickly but nothing happens
- RabbitMQ shows messages accumulating in queue
- Worker container logs show no recent activity

## 🧠 Common Causes
1. **Worker crashed silently** (40%) - OOM kill or exception not logged
2. **RabbitMQ connection lost** (25%) - Network issue, broker restart
3. **Beat scheduler stopped** (20%) - Periodic tasks not being scheduled
4. **Task code exception** (10%) - Bug causes worker to hang on specific task
5. **Resource exhaustion** (5%) - Worker stuck due to CPU/memory pressure

## 👥 Resolution Group
**Primary:** tech-devops (Ralph)
**Secondary:** None (auto-fix available)
**Escalation Path:** If auto-fix fails 3x → Check RabbitMQ health (ERROR-061)

## 🩺 Diagnosis Steps

### 1. Check worker container status
```bash
docker ps | grep -E "worker|beat"
# Look for: STATUS column - should be "Up X hours (healthy)"
```

### 2. Check worker logs for errors
```bash
docker logs worker --tail 100 2>&1 | grep -iE "error|exception|traceback|critical"
```

### 3. Check Flower dashboard
```bash
# Open Flower UI
open http://localhost:5555

# Or via CLI
curl -s http://localhost:5555/api/workers | jq '.[] | {name, status, active}'
```

### 4. Check RabbitMQ queue depth
```bash
# Via RabbitMQ management API
curl -s -u guest:guest http://localhost:15672/api/queues | jq '.[].messages'

# Or via docker
docker exec rabbitmq rabbitmqctl list_queues name messages
```

### 5. Check pending tasks
```bash
# Via Flower API
curl -s http://localhost:5555/api/tasks?state=PENDING | jq 'length'
```

### 6. Check memory/CPU pressure
```bash
docker stats --no-stream worker beat
```

## ✅ Resolution

### Auto-Fix Available
**Command:** `docker restart worker beat`

**Success Rate:** 85%

**Auto-fix triggers when:**
- Worker heartbeat missed for >5 minutes
- PENDING tasks >100 for >10 minutes
- Worker container status is "unhealthy"

### Manual Resolution (If Auto-Fix Fails)

**Step 1: Full worker stack restart**
```bash
# Stop workers gracefully
docker stop worker beat

# Clear any stuck tasks in RabbitMQ (CAUTION: loses queued tasks)
docker exec rabbitmq rabbitmqctl purge_queue celery

# Restart workers
docker start beat worker

# Verify
docker logs worker --tail 20
```

**Step 2: Check RabbitMQ health**
```bash
# Verify RabbitMQ is accepting connections
docker exec rabbitmq rabbitmqctl status | head -20

# If RabbitMQ is unhealthy
docker restart rabbitmq
sleep 10
docker restart worker beat
```

**Step 3: Check for hung tasks**
```bash
# List active tasks
docker exec worker celery -A src.tasks.celery_app inspect active

# If a specific task is hanging, terminate it
docker exec worker celery -A src.tasks.celery_app control terminate <task_id>
```

**Step 4: Force recreate containers**
```bash
# Nuclear option: recreate from scratch
docker compose -f compose/helix-main/main-stack.yml up -d --force-recreate worker beat
```

### Post-Fix Verification
```bash
# 1. Check workers are online
docker exec worker celery -A src.tasks.celery_app inspect ping

# 2. Send test task
docker exec worker python -c "
from src.tasks.celery_app import celery_app
from src.tasks.tasks import test_task
result = test_task.delay('hello')
print(f'Task ID: {result.id}')
print(f'Result: {result.get(timeout=10)}')
"

# 3. Verify pending queue is draining
sleep 30
curl -s http://localhost:5555/api/tasks?state=PENDING | jq 'length'
# Should be decreasing
```

## 📝 Notes

### HelixNet Celery Architecture
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Beat      │────▶│   RabbitMQ   │────▶│    Worker    │
│  (Scheduler) │     │   (Broker)   │     │  (Executor)  │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       │                    │                    ▼
       │                    │              ┌──────────┐
       │                    │              │ Postgres │
       │                    │              │ (Results)│
       │                    │              └──────────┘
       │                    │                    │
       └────────────────────┴────────────────────▼
                                          ┌──────────┐
                                          │  Flower  │
                                          │ (Monitor)│
                                          └──────────┘
```

### Common Scheduled Tasks in HelixNet
| Task | Schedule | Purpose |
|------|----------|---------|
| `generate_daily_report` | 6:00 AM | Daily sales summary for Banana export |
| `cleanup_expired_sessions` | Every hour | Remove stale session data |
| `sync_inventory_alerts` | Every 15 min | Check stock levels, send alerts |
| `backup_database` | 3:00 AM | Automated Postgres backup |

### Impact When Workers Are Down
- **High:** Scheduled reports not generated (Felix needs daily summary)
- **Medium:** Async tasks queue up (job submissions delayed)
- **Low:** System still functions for real-time POS (sync operations)
- **Recovery:** Once workers restart, queued tasks process (FIFO)

### Why Workers Crash (Common Bugs)
1. **Memory leak in task:** Long-running task accumulates memory
2. **Database connection pool exhausted:** Too many concurrent tasks
3. **Timeout not set:** Task hangs forever waiting for external API
4. **Exception not caught:** Unhandled error crashes worker process

### Prevention Measures
1. **Task timeouts:** Set `soft_time_limit` and `time_limit` on all tasks
2. **Memory monitoring:** Alert if worker memory >80%
3. **Heartbeat checks:** DebLLM monitors worker health every 5 min
4. **Task result cleanup:** Expire old results (7 days)

### Flower Dashboard Quick Reference
- **URL:** http://localhost:5555 (or https://flower.helix.local via Traefik)
- **Login:** No auth in dev mode
- **Key Views:**
  - Workers: Online/offline status
  - Tasks: PENDING/STARTED/SUCCESS/FAILURE counts
  - Broker: Queue depth
  - Monitor: Real-time task activity

### RabbitMQ Queue Names
- `celery` - Default task queue
- `celery.pidbox` - Worker control messages
- `celeryev.*` - Event queues (for Flower monitoring)

## 📜 History
- **2025-11-28 06:15** (debllm): Detected 47 PENDING tasks, beat missed 3 heartbeats
- **2025-11-28 06:16** (debllm): Auto-fix triggered: `docker restart worker beat`
- **2025-11-28 06:17** (debllm): Workers back online, processing resumed
- **2025-11-28 06:25** (debllm): Pending queue cleared (47 tasks processed)
- **2025-11-28 06:30** (felix): Confirmed daily report generated (delayed 30 min)
- **2025-11-28 08:00** (angel): Root cause: Worker OOM'd processing large CSV export

## 🔗 References
- Celery documentation: https://docs.celeryq.dev/en/stable/
- RabbitMQ troubleshooting: https://www.rabbitmq.com/troubleshooting.html
- Flower monitoring: https://flower.readthedocs.io/
- HelixNet task configuration: `src/tasks/celery_app.py`
- Worker Dockerfile: `compose/helix-main/Dockerfile.worker`
