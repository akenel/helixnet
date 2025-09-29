# app/tasks/celery_app.py
"""
Celery configuration for HelixNet 🚀
------------------------------------
Handles distributed task execution (workers) and scheduling (beat).
We use RabbitMQ as broker + Redis as result backend for resilience.

💡 This is production-ready, but simple enough for local dev & Docker Compose.
"""

import os
from celery import Celery
from dotenv import load_dotenv

# --- 0. Load Environment Variables 🌱 ---
# Local dev: .env file | Docker: passed via docker-compose
load_dotenv()

# --- 1. Connection Strings 🔗 ---
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "admin")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")

CELERY_BROKER_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:5672//"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:6379/0"

# --- 2. Celery App Instance ⚙️ ---
celery_app = Celery(
    "helixnet_celery",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks.tasks"],  # Load tasks from app/tasks/tasks.py
)
print(f"🚀 Celery connecting to broker: {CELERY_BROKER_URL}")

# --- 3. Global Celery Configuration 🌍 ---
celery_app.conf.update(
    task_track_started=True,     # Track "started" state of tasks
    task_time_limit=300,         # Hard timeout (seconds) ⏳
    task_soft_time_limit=240,    # Soft timeout (grace period) ⏱️
    task_acks_late=True,         # Ensure tasks are not lost if worker crashes
    worker_prefetch_multiplier=1,# Fair task distribution ⚖️
    timezone="Europe/Zurich",    # Local time zone 🕰️
    enable_utc=True,
)

# --- 4. Beat Schedule (Periodic Tasks) ⏰ ---
celery_app.conf.beat_schedule = {
    "say-hello-every-10s": {
        "task": "app.tasks.tasks.say_hello",
        "schedule": 10.0,  # Run every 10 seconds
    },
    "system-healthcheck-1m": {
        "task": "app.tasks.tasks.system_healthcheck",
        "schedule": 60.0,  # Run every 1 minute
    },
}

# --- 5. Example Sanity Task 🧪 ---
@celery_app.task(name="sanity_check_task")
def add(x, y):
    """Quick test task to validate worker/queue connectivity."""
    print(f"🧮 Task received: Adding {x} and {y}")
    return x + y
