import os
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
from redis import asyncio as aioredis
from minio import Minio
import pika
from sqlalchemy import text
# CRITICAL: Import engine from the new clean location
from app.db.database import engine 
from app.tasks.celery_app import celery_app
from app.routes.tasks_router import tasks_router
from app.routes.users import users_router as users_router  # NEW: Import the user router    
async def check_db_connection() -> bool:
    """
    Checks connectivity to the PostgreSQL service by executing a simple query
    using the imported asynchronous engine.
    """
    try:
        # Use the imported async engine to connect and execute a simple query
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"PostgreSQL connection failed: {e}")
        return False

# --- Utility Functions for Deep Health Check (Kept as before) ---

async def check_redis_connection() -> bool:
    """Check connectivity to the Redis cache service."""
    try:
        redis_host = os.environ.get('REDIS_HOST', 'redis')
        redis_port = int(os.environ.get('REDIS_PORT', 6379))
        
        # Use aioredis for async connection check
        redis = aioredis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        await redis.ping()
        return True
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return False

async def check_rabbitmq_connection() -> bool:
    """Check connectivity to the RabbitMQ broker."""
    try:
        # Pika is sync, so we run the connection attempt in a thread pool
        loop = asyncio.get_running_loop()
        connection = await loop.run_in_executor(
            None,
            lambda: pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=os.environ.get('RABBITMQ_HOST', 'rabbitmq'),
                    port=int(os.environ.get('RABBITMQ_PORT', 5672)),
                    credentials=pika.PlainCredentials(
                        os.environ.get('RABBITMQ_USER', 'admin'),
                        # IMPORTANT: It is best practice to use a secret from environment variables
                        os.environ.get('RABBITMQ_PASS', 'secret_password') 
                    ),
                    heartbeat=60 # Set a heartbeat for stability
                )
            )
        )
        connection.close()
        return True
    except Exception as e:
        print(f"RabbitMQ connection failed: {e}")
        return False

def check_minio_connection() -> bool:
    """Check connectivity to the MinIO object storage service."""
    try:
        client = Minio(
            os.environ.get('MINIO_ENDPOINT', 'minio:9000'), 
            access_key=os.environ.get('MINIO_ROOT_USER', 'minioadmin'),
            secret_key=os.environ.get('MINIO_ROOT_PASSWORD', 'minioadmin'),
            secure=False # Use False for local development over HTTP
        )
        client.list_buckets()
        return True
    except Exception as e:
        print(f"MinIO connection failed: {e}")
        return False

# --- App Initialization ---

app = FastAPI(
    title="HelixNet Core API",
    description="Asynchronous API for job processing and data management.",
    version="0.1.0",
)

# Attach the routers
app.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
# NEW: Include the User Router
app.include_router(users_router, prefix="/users", tags=["Users"])


# --- Health Check Endpoint ---

@app.get("/health", response_model=Dict[str, str], tags=["System"])
async def deep_health_check():
    """
    Performs a deep health check, validating connectivity to all core services:
    PostgreSQL, Redis, RabbitMQ, and MinIO.
    """
    
    # Run all connection checks concurrently
    db_ok, redis_ok, rabbitmq_ok = await asyncio.gather(
        check_db_connection(), 
        check_redis_connection(),
        check_rabbitmq_connection(),
    )
    
    # MinIO is sync, so we check it outside of the asyncio.gather
    minio_ok = check_minio_connection()
    
    status = {
        "status": "UP" if (db_ok and redis_ok and rabbitmq_ok and minio_ok) else "DOWN",
        "postgres_db": "OK" if db_ok else "FAIL",
        "redis_cache": "OK" if redis_ok else "FAIL",
        "rabbitmq_broker": "OK" if rabbitmq_ok else "FAIL",
        "minio_storage": "OK" if minio_ok else "FAIL",
    }
    
    if status["status"] == "DOWN":
        raise HTTPException(
            status_code=503, 
            detail={"message": "Service degraded", **status}
        )
    
    return status

# --- Root Endpoint ---

@app.get("/", tags=["System"])
async def root():
    return {"message": "Welcome to HelixNet API. Check /docs for endpoints and /health for status."}
# Note: In production, consider using connection pooling and more robust error handling.    
# Example usage:
# import asyncio
# asyncio.run(check_db_connection())            
# if __name__ == "__main__":    
#     asyncio.run(check_db_connection())
#     print("Database connection successful!")
# else:
#     print("Database connection failed.")  
