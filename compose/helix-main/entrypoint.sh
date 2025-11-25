#!/usr/bin/env bash
set -euo pipefail

echo "⏳ Waiting for Postgres (postgres:5432)..."
until nc -z postgres 5432; do
  echo "  waiting for postgres..."
  sleep 1
done

echo "⏳ Waiting for Redis (redis:6379)..."
until nc -z redis 6379; do
  echo "  waiting for redis..."
  sleep 1
done

echo "⏳ Waiting for RabbitMQ (rabbitmq:5672)..."
# Use a small timeout so this doesn't block forever if broker isn't present
for i in {1..60}; do
  if nc -z rabbitmq 5672; then
    echo "  rabbitmq is up"
    break
  fi
  echo "  waiting for rabbitmq..."
  sleep 1
done

echo "🚀 Starting Helix Service (type: ${SERVICE_TYPE:-platform})..."

# Detect which service to start based on SERVICE_TYPE environment variable
case "${SERVICE_TYPE:-platform}" in
  "worker")
    echo "🥬 Starting Celery Worker..."
    exec celery -A src.tasks.celery_app:app worker --loglevel=INFO
    ;;
  "beat")
    echo "🥁 Starting Celery Beat..."
    exec celery -A src.tasks.celery_app:app beat --loglevel=INFO
    ;;
  "flower")
    echo "🌼 Starting Flower..."
    exec celery -A src.tasks.celery_app:app flower --port=5555
    ;;
  "platform"|*)
    echo "🦄 Starting FastAPI Platform..."
    exec uvicorn src.main:app --host 0.0.0.0 --port 8000
    ;;
esac
