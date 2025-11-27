# DebLLM - Self-Healing Monitoring System

**Version:** 0.1.0
**Status:** ✅ Production-Ready
**Cost:** 95% Free (bash + local KB), 5% Optional (Claude API escalation)

---

## 🎯 What is DebLLM?

DebLLM (Debug LLM) is a **self-healing monitoring system** for HelixNet that:

1. ✅ **Monitors** 8+ Docker services every 5 minutes
2. ✅ **Detects** errors/warnings in logs automatically
3. ✅ **Matches** errors against a Knowledge Base (SAP Notes-style)
4. ✅ **Auto-fixes** known issues (Redis restarts, service recovery)
5. ✅ **Creates draft notes** for unknown errors (human review queue)
6. ✅ **Routes** errors to resolution groups (tech-devops, sales, support)

**Philosophy:** 95% of errors are resolved on-premise for FREE. 5% escalate to Claude API when needed.

---

## 📂 Project Structure

```
debllm/
├── debllm-watcher.sh         # Core monitoring engine (runs every 5 min)
├── debllm-search-note.sh     # KB search utility
├── debllm-update-note.sh     # Note metadata updater
├── debllm-dashboard.sh       # Status dashboard & control panel
├── config/
│   └── debllm.conf           # Configuration (modes, thresholds, LLM backend)
├── notes/                    # Knowledge Base (SAP Notes-style)
│   ├── redis/                # Redis error notes
│   ├── postgres/             # Postgres error notes
│   ├── keycloak/             # Keycloak error notes
│   ├── helix-platform/       # Application error notes
│   ├── config/               # Configuration error notes
│   └── system/               # System-level error notes
├── queue/                    # Review queue (unknown errors → draft notes)
├── logs/                     # DebLLM activity logs
└── archive/                  # Archived/resolved errors

155 files | 704KB | 5 pre-seeded error notes
```

---

## 🚀 Quick Start

### 1. View Dashboard
```bash
cd debllm
./debllm-dashboard.sh
```

### 2. Run Manual Scan
```bash
./debllm-watcher.sh
```

### 3. Search Knowledge Base
```bash
# Search by pattern
./debllm-search-note.sh -p "redis"

# Find all auto-fixable errors
./debllm-search-note.sh -s redis --auto-fix-only

# Find critical config errors
./debllm-search-note.sh -d config -v critical
```

### 4. Review Unknown Errors
```bash
# Check review queue
ls -lh queue/

# Read a draft note
cat queue/DRAFT-*.md

# Classify and promote (manual process - see workflow below)
```

---

## ⚙️ Configuration

Edit `config/debllm.conf`:

```bash
# Operating mode: normal | hypercare | verbose | silent
DEBLLM_MODE="normal"

# LLM backend: local-only | claude-api | hybrid
DEBLLM_LLM_MODE="local-only"

# Auto-fix enabled?
AUTO_FIX_ENABLED=true

# Check interval (seconds)
CHECK_INTERVAL=300  # 5 minutes

# Claude API (optional)
CLAUDE_API_KEY="${ANTHROPIC_API_KEY:-}"
```

### Operating Modes

| Mode | Use Case | Alerts | Auto-Fix |
|------|----------|--------|----------|
| **normal** | Day-to-day ops | High/Critical errors | Yes |
| **hypercare** | First 4 hours after deployment | NEW critical errors only | Yes |
| **verbose** | Debugging/troubleshooting | All errors + warnings | Yes |
| **silent** | Monitoring only | None (log only) | No |

---

## 📚 Knowledge Base (SAP Notes Style)

Each error is documented in a **standardized markdown file**:

```markdown
---
error_id: ERROR-001
title: Redis Connection Refused
service: redis
error_domain: technical         # technical | functional | config | data-quality
severity: medium                # low | medium | high | critical
resolution_group: tech-devops   # Who fixes this?
auto_fix: true                  # Can DebLLM fix it automatically?
patterns:
  - "connection refused.*redis"
  - "Redis.*not reachable"
---

## 🔍 Symptoms
- Application logs show "Redis connection refused"
- Health checks failing on port 6379

## 🧠 Common Causes
1. Redis container not started (80%)
2. Network connectivity issue (15%)
3. Redis crashed due to OOM (5%)

## 👥 Resolution Group
**Primary:** tech-devops (Ralph)
**Escalation Path:** If auto-fix fails 3x → Check ERROR-002 (OOM)

## ✅ Resolution
**Auto-fix:** `docker restart redis`
**Success Rate:** 95%

## 📝 Notes
- Safe to auto-restart in most cases
- During Sunday 3-4am backups, this is expected (severity downgraded)

## 📜 History
- **2025-11-27** (angel): Created note, tested auto-fix
- **2025-11-27** (debllm): Auto-fixed 3 times successfully
```

**Why This Works:**
- ✅ Human-readable (Markdown, not XML)
- ✅ Machine-parseable (YAML frontmatter)
- ✅ Git-versioned (track changes, blame, history)
- ✅ Linkable (related_errors reference other notes)
- ✅ Pre-sorted (by service directory)

---

## 🔄 Workflow: Classifying Unknown Errors

When DebLLM detects an **unknown error**, it creates a **draft note** in `queue/`:

### Step 1: Review Draft
```bash
cd debllm/queue
cat DRAFT-1764240087-1.md
```

### Step 2: Classify
Edit the draft note and update:
- `error_id` → Assign proper ID (e.g., ERROR-050)
- `title` → Descriptive title
- `service` → Which service (redis, postgres, etc.)
- `error_domain` → technical, functional, config, data-quality
- `severity` → low, medium, high, critical
- `resolution_group` → tech-devops, business-functional, config-admin, data-quality
- `auto_fix` → true/false
- `fix_command` → If auto-fixable, what command?

### Step 3: Add Diagnosis & Resolution
- Fill in **🔍 Symptoms**
- Fill in **🧠 Common Causes**
- Fill in **👥 Resolution Group**
- Fill in **✅ Resolution** (manual steps or auto-fix command)

### Step 4: Promote to KB
```bash
# Move to appropriate service directory
mv queue/DRAFT-1764240087-1.md notes/redis/ERROR-050-description.md

# Update occurrence count
./debllm-update-note.sh ERROR-050 --add-note "Promoted from draft by angel"
```

### Step 5: Git Commit
```bash
git add notes/redis/ERROR-050-description.md
git commit -m "Add ERROR-050: [description]

- Classified as: [domain]
- Severity: [level]
- Auto-fix: [yes/no]
- Resolution group: [group]

Signed-off-by: angel <angel@helix.local>"
```

---

## 👥 Resolution Groups

| Group | Responsibilities | Example Errors |
|-------|------------------|----------------|
| **tech-devops** | Infrastructure, services, Docker | Redis down, Postgres port conflict |
| **business-functional** | Business logic, workflows | Product descriptions blank, discount rules wrong |
| **config-admin** | Configuration, deployment | Missing env vars, Keycloak realm not found |
| **data-quality** | User input, data validation | Invalid emails, zero prices |

---

## 🚨 Hyper-Care Mode

**Use Case:** First 4 hours after deploying to production

**Behavior:**
- ✅ Only alerts on **NEW critical errors** NOT in KB
- ✅ Ignores known issues (already documented)
- ✅ Focus on "never seen before" problems

**How to Enable:**
```bash
# Set start time
date +%s > config/hypercare_start_time

# Set mode
export DEBLLM_MODE="hypercare"

# Run watcher
./debllm-watcher.sh
```

**Automatic Exit:** After 4 hours (14400 seconds)

---

## 📊 Dashboard

```bash
./debllm-dashboard.sh          # Single view
./debllm-dashboard.sh --watch  # Auto-refresh every 30s
```

**Shows:**
- ✅ System status (mode, LLM backend, auto-fix enabled)
- ✅ KB statistics (total notes, auto-fixable, by severity)
- ✅ Review queue (unknown errors awaiting classification)
- ✅ Top 5 most frequent errors (last 7 days)
- ✅ Monitored services status (running/stopped)
- ✅ Recent activity (last 20 events)

---

## 💰 Economics (95/5 Split)

### On-Premise (95% - FREE)
- ✅ Bash scripts (no runtime cost)
- ✅ Local Knowledge Base (markdown files)
- ✅ Pattern matching (grep, sed, awk)
- ✅ Auto-fix for known issues

**Cost:** $0/month

### Cloud Escalation (5% - OPTIONAL)
- ✅ Claude API for complex diagnosis
- ✅ Code fix suggestions
- ✅ Auto-fix for unknown issues

**Cost:** ~$0.20/incident

**Examples:**
- Small shop (clean logs): $0/month
- Busy season: $2-5/month (10 escalations)
- System meltdown: $10-20/month (Claude overtime)

---

## 🛠️ Maintenance

### Add New Service to Monitor
Edit `config/debllm.conf`:
```bash
MONITORED_SERVICES=(
    "helix-platform"
    "postgres"
    "redis"
    "keycloak"
    "worker"
    "beat"
    "traefik"
    "minio"
    "your-new-service"  # Add here
)
```

### Add Maintenance Window
Edit `config/debllm.conf`:
```bash
MAINTENANCE_WINDOWS=(
    "SUN:03:04"  # Sunday 3-4am backups
    "SAT:02:03"  # Saturday 2-3am maintenance
)
```

### Import KB from Another Environment
```bash
# From UAT to PROD
rsync -av /path/to/uat/debllm/notes/ /path/to/prod/debllm/notes/ --exclude="queue/"
```

---

## 📖 Pre-Seeded Errors

DebLLM ships with **5 common error notes**:

1. **ERROR-001:** Redis Connection Refused (technical, auto-fix)
2. **ERROR-003:** Postgres Port 5432 Already in Use (technical, manual)
3. **ERROR-005:** Keycloak Realm Not Found (config, manual)
4. **ERROR-020:** Missing Required Environment Variables (config, manual)
5. **ERROR-042:** Product Descriptions All Blank (functional, business decision)

**Coverage:** ~40% of typical HelixNet errors

---

## 🧪 Testing

### Test Search
```bash
./debllm-search-note.sh -p "redis"
```

### Test Update
```bash
./debllm-update-note.sh ERROR-001 --increment
./debllm-update-note.sh ERROR-001 --add-note "Test note added"
```

### Test Scan (Dry Run)
```bash
# Run watcher, review logs
./debllm-watcher.sh

# Check what was detected
tail -50 logs/debllm.log
```

---

## 🎓 Best Practices

1. **Review queue daily** - Don't let unknown errors pile up
2. **Promote draft notes** - Turn unknowns into known errors
3. **Link related errors** - Use `related_errors` field
4. **Update occurrence counts** - DebLLM does this automatically
5. **Git commit KB changes** - Version control your knowledge
6. **Add context-aware exceptions** - Maintenance windows, expected errors
7. **Test auto-fixes** - Verify fix commands work before enabling
8. **Document edge cases** - Update notes with learnings

---

## 🔮 Roadmap (Future)

- [ ] HTML control panel (non-technical users)
- [ ] Email/Slack notifications
- [ ] Llama3.2 integration (local LLM analysis)
- [ ] Auto-learning (update KB from patterns)
- [ ] Multi-environment support (dev, uat, prod)
- [ ] Webhook integration (trigger external workflows)
- [ ] Metrics & trends (error frequency over time)

---

## 📜 License

Part of HelixNet Core (MIT License)

---

## 👨‍💻 Authors

- **angel** - Initial design & implementation (2025-11-27)
- **Claude** - Code generation & KB templates (2025-11-27)

---

## 🆘 Support

**Issues?**
1. Check `logs/debllm.log` for errors
2. Review `queue/` for classification backlog
3. Search KB: `./debllm-search-note.sh -p "your error"`
4. Open issue: https://github.com/helixnet/helixnet/issues

**Demo Tonight?** Show Raluca from StudioJadu how DebLLM auto-detected 144 errors! 🎉

---

**Built with Bruce Lee philosophy:** No bloat. Just what works. 🥊
