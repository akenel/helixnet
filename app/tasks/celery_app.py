# app/tasks/celery_app.py
"""
Celery Application Instance and Configuration.
Defines broker, backend, and periodic tasks.
"""
import os
from celery import Celery
from datetime import timedelta

# --- Configuration for Celery ---
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "admin")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", "5672")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")

# CRITICAL FIX: Use robust string formatting to ensure variables are substituted 
# and the port is always a string that looks like an integer.
BROKER_URL = "amqp://{user}:{password}@{host}:{port}//".format(
    user=RABBITMQ_USER,
    password=RABBITMQ_PASS,
    host=RABBITMQ_HOST,
    port=RABBITMQ_PORT
)
BACKEND_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Initialize the Celery application
celery_app = Celery(
    "helixnet_tasks",
    broker=BROKER_URL,
    backend=BACKEND_URL,
    # 💥 CN FIX: This now includes both the utility tasks and the core job tasks.
    include=[
        'app.tasks.tasks',     # Existing module (health checks)
        'app.tasks.job_tasks'  # <-- ADD THIS LINE! (where process_data lives)
    ]
)
# Configure Celery settings
celery_app.conf.update(
    # Timeouts for connection/retries
    broker_connection_retry_on_startup=True,
    broker_transport_options={'visibility_timeout': 3600},
    task_track_started=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    
    # Celery Beat schedule - Tasks must be registered via 'include' above to work here.
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

print("🚀 Celery Application initialized. Broker:", BROKER_URL)
# ----------------------------------------------------
# End of celery_app.py /app/tasks/celery_app.py
# ----------------------------------------------------