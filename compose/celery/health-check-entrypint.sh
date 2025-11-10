#!/usr/bin/env bash
# compose/celery/health-check-entrypint.sh Simple dummy health check for Celery containers 
# Set environment to unbuffered to see logs immediately
PYTHONUNBUFFERED=1
# --- Environment and Dependencies ---
# Set the application's working directory.

CELERY_BROKER_URL= 'amqp://helix_user:helix_pass@rabbitmq:5672//'
CELERY_RESULT_BACKEND= 'redis://redis:6379/1'

# This is the critical setting that causes the ModuleNotFoundError
# It tells Celery Beat which scheduler implementation to use.
# It must match the class path provided by the installed package.
CELERY_BEAT_SCHEDULER= 'redis_scheduler.Scheduler'

# Additional required settings for the Redis Scheduler
CELERY_REDIS_SCHEDULER_URL= 'redis://redis:6379/1' # Matches your backend URI
CELERY_BEAT_MAX_LOOP_INTERVAL= 5 # Interval for checking schedule changes (in seconds)
# Check if any celery process is running
if pgrep -f "celery" > /dev/null; then
  echo "✅ Celery process running fine"
  exit 0
else
  echo "❌ No Celery process detected"
  exit 1
fi
