# app/tasks/tasks.py
"""
HelixNet Celery Tasks 🎯
------------------------
Core task definitions for async execution & periodic scheduling.

Includes:
- Sanity checks ✅
- System health monitoring 🩺
- Example async jobs ⚡
"""

import os
import socket
import redis
import psycopg2
import pika
from celery import shared_task


# --- 1. Simple demo task 🧪 ---
@shared_task(name="say_hello")
def say_hello():
    """Periodic hello message to test Celery Beat scheduling."""
    msg = "👋 Hello from Celery Beat!"
    print(msg)
    return msg


# --- 2. System Health Check 🩺 ---
@shared_task(name="system_healthcheck")
def system_healthcheck():
    """
    Check connectivity with core infrastructure:
    - Redis
    - RabbitMQ
    - Postgres
    Returns a dictionary with status flags.
    """

    status = {
        "redis": False,
        "rabbitmq": False,
        "postgres": False,
    }

    # Redis check
    try:
        r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379)
        r.ping()
        status["redis"] = True
    except Exception as e:
        status["redis"] = f"❌ {e}"

    # RabbitMQ check
    try:
        creds = pika.PlainCredentials(
            os.getenv("RABBITMQ_USER", "admin"),
            os.getenv("RABBITMQ_PASS", "admin"),
        )
        conn = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
                credentials=creds,
            )
        )
        conn.close()
        status["rabbitmq"] = True
    except Exception as e:
        status["rabbitmq"] = f"❌ {e}"

    # Postgres check
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            host=os.getenv("POSTGRES_HOST", "postgres"),
        )
        conn.close()
        status["postgres"] = True
    except Exception as e:
        status["postgres"] = f"❌ {e}"

    print(f"🩺 Healthcheck Results: {status}")
    return status


# --- 3. Example workload task ⚡ ---
@shared_task(name="process_job")
def process_job(data: dict):
    """
    Simulates processing a job payload.
    In real life: transform data, push to API, or run analysis.
    """
    print(f"⚙️ Processing job with data: {data}")
    return {"status": "done", "processed_data": data}
