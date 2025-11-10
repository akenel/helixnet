#!/bin/sh
set -e  # 💥 Stop immediately if any step crashes!

# ==============================================================================
# 1. Dependency Waits (The Brain checks if its friends are ready)
# ==============================================================================

export PYTHONUNBUFFERED=1

# --- Environment and Dependencies ---
# Remove spaces around '=' and do NOT wrap URLs in single quotes
export CELERY_BROKER_URL=amqp://helix_user:helix_pass@rabbitmq:5672//
export CELERY_RESULT_BACKEND=redis://redis:6379/1

# Redis scheduler config
export CELERY_BEAT_SCHEDULER=redis_scheduler.Scheduler
export CELERY_REDIS_SCHEDULER_URL=redis://redis:6379/1
export CELERY_BEAT_MAX_LOOP_INTERVAL=5

echo "⏳ Waiting for the Memory 🐘 Elephant (postgres:5432) and Keycloak..."
sleep 180  # (consider reducing once health checks are stable)

# ==============================================================================
# 2. Database Initialization
# ==============================================================================
echo "🌱 Planting the first seeds in the Elephant's memory (seed_users)..."
python3 -m src.scripts.seed_users || echo "⚠️ Seed script failed, continuing..."
echo "🌱 Seeds planted! ✅"

# ==============================================================================
# 3. Service Readiness Checks
# ==============================================================================
echo "Waiting for Postgres..."
until nc -z postgres 5432; do sleep 2; done

echo "Waiting for RabbitMQ..."
until nc -z rabbitmq 5672; do sleep 2; done

# ==============================================================================
# 4. Start the Main Application
# ==============================================================================
echo "🚀 Starting Uvicorn..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
