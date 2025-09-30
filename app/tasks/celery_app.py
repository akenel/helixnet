# app/tasks/celery_app.py
"""
Celery Application Instance and Configuration.
Defines broker, backend, and periodic tasks.
"""
import os
from celery import Celery
from datetime import timedelta

# --- Configuration for Celery ---
# Broker: RabbitMQ
# Backend: Redis (for result storage)
# NOTE: The Celery app name is crucial for the worker command:
# `celery -A tasks.celery_app` where `tasks` is the folder and 
# `celery_app` is the module/instance name.

# Get environment variables from the Docker environment
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "admin")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", "5672")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")

BROKER_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}//"
BACKEND_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"


# Initialize the Celery application
celery_app = Celery(
    "helixnet_tasks",
    broker=BROKER_URL,
    backend=BACKEND_URL,
    include=['app.tasks.tasks'] # CRITICAL FIX: Explicitly load the module containing the task definitions
)

# Configure Celery settings
celery_app.conf.update(
    # Timeouts for connection/retries
    broker_connection_retry_on_startup=True,
    broker_transport_options={'visibility_timeout': 3600},  # 1 hour
    task_track_started=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    
    # Enable Celery Beat for periodic tasks
    beat_schedule={
        'say-hello-every-10-seconds': {
            'task': 'app.tasks.tasks.say_hello', # Use the fully qualified path
            'schedule': timedelta(seconds=10),
            'args': (),
        },
        'system-healthcheck-every-60-seconds': {
            'task': 'app.tasks.tasks.system_healthcheck',
            'schedule': timedelta(seconds=60),
            'args': (),
        },
    },
)

# Optional sanity check to confirm the app loaded
print("🚀 Celery Application initialized. Broker:", BROKER_URL)
