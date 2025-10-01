# app/main.py - Rewritten, Cleaned, and Highly Commented for HelixNet

# 🚀 CORE IMPORTS & CONFIGURATION ⚙️
import os
import asyncio
from typing import Dict

# 🌐 FastAPI & Core Dependencies
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import asynccontextmanager

# 💾 Database, Redis, MinIO, RabbitMQ Clients
from sqlalchemy import text # Used for the DB health check query
from redis import asyncio as aioredis
from minio import Minio
import pika

# 📦 PROJECT MODULE IMPORTS (We keep these separated and clean!)
from app.db.database import engine, init_db # Postgres Engine & Initialization 🐘
from app.tasks.celery_app import celery_app # Celery Application Instance (The Job Runner) 🏃

# 🚦 ROUTER IMPORTS (CRITICAL FIX APPLIED HERE!)
# We MUST import the APIRouter *instance* (e.g., auth_router), not the module itself.
from app.routes.tasks_router import tasks_router
from app.routes.users_router import users_router
from app.routes.auth_router import auth_router 


# --- HELPER FUNCTIONS: DEEP HEALTH CHECK 🩺 ---

async def check_db_connection() -> bool:
    """
    Checks connectivity to the PostgreSQL service by executing a simple 'SELECT 1' query. 
    If this passes, the DB is smokin'! 🔥
    """
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True # 🎉 Success!
    except Exception as e:
        print(f"PostgreSQL connection failed: {e} 🚨")
        return False

async def check_redis_connection() -> bool:
    """Check connectivity to the Redis cache service (Async). 💨"""
    try:
        redis_host = os.environ.get('REDIS_HOST', 'redis')
        redis_port = int(os.environ.get('REDIS_PORT', 6379))
        
        # Using aioredis for true async checks
        redis = aioredis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        await redis.ping()
        return True # 🥳 OK!
    except Exception as e:
        print(f"Redis connection failed: {e} 🚨")
        return False

async def check_rabbitmq_connection() -> bool:
    """Check connectivity to the RabbitMQ broker (The message highway!). 🛣️"""
    try:
        # Pika is synchronous, so we safely run the connection attempt in a thread pool
        loop = asyncio.get_running_loop()
        connection = await loop.run_in_executor(
            None,
            lambda: pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=os.environ.get('RABBITMQ_HOST', 'rabbitmq'),
                    port=int(os.environ.get('RABBITMQ_PORT', 5672)),
                    credentials=pika.PlainCredentials(
                        os.environ.get('RABBITMQ_USER', 'admin'),
                        os.environ.get('RABBITMQ_PASS', 'secret_password') 
                    ),
                    heartbeat=60
                )
            )
        )
        connection.close()
        return True # 👍 RabbitMQ is listening.
    except Exception as e:
        print(f"RabbitMQ connection failed: {e} 🚨")
        return False

def check_minio_connection() -> bool:
    """Check connectivity to the MinIO object storage service (Sync). 🗄️"""
    try:
        client = Minio(
            os.environ.get('MINIO_ENDPOINT', 'minio:9000'), 
            access_key=os.environ.get('MINIO_ROOT_USER', 'minioadmin'),
            secret_key=os.environ.get('MINIO_ROOT_PASSWORD', 'minioadmin'),
            secure=False # Use False for local dev/HTTP
        )
        client.list_buckets() # Simple check to confirm authentication and connection
        return True # ✅ MinIO bucket list worked!
    except Exception as e:
        print(f"MinIO connection failed: {e} 🚨")
        return False


# --- APP LIFESPAN MANAGEMENT ⏳ ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup (DB initialization) and shutdown events for FastAPI.
    """
    print("Application starting up... 🌟 Running Critical Initialization...")
    
    # CRITICAL STEP: Ensure the database tables exist!
    await init_db() 
    
    print("Initialization complete. Yielding control. Server is ready! 🟢")
    yield # Server runs here
    
    print("Application shutting down. Goodbye! 👋")


# --- FASTAPI APPLICATION INITIALIZATION 💻 ---

app = FastAPI(
    title="HelixNet Core Enterprise API",
    description="Asynchronous API for job processing and backend services for user management and asynchronous processing. Built for speed and reliability! ⚡",
    version="0.1.0",
    lifespan=lifespan # Attach the startup/shutdown logic
)


# --- ROUTER INCLUSION (This is the stable method!) 🛠️ ---
# Including all the routers we imported above with clear, explicit prefixes.
app.include_router(auth_router, prefix="/auth", tags=["Authentication"]) # JWT, Login, etc.
app.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])       # Celery/Job handling
app.include_router(users_router, prefix="/users", tags=["Users"])       # CRUD for user accounts


# --- SYSTEM ENDPOINTS ⚙️ ---

@app.get("/health", response_model=Dict[str, str], tags=["System"])
async def deep_health_check():
    """
    Performs a deep health check, validating connectivity to all core services:
    PostgreSQL, Redis, RabbitMQ, and MinIO. The pulse of the system! ❤️
    """
     # Run async checks concurrently for speed! 🏎️
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
        print("ALERT: Core services are DOWN! ❌")
        raise HTTPException(
            status_code=503, 
            detail={"message": "Service degraded", **status}
        )
    
    return status

@app.get("/", tags=["System"])
async def root():
    """Welcome endpoint. The door to our powerful API! 🚪"""
    return {"message": "Welcome to HelixNet API. Check /docs for endpoints and /health for status."}
# Note: /home/angel/repos/helixnet/app/main.py and /home/angel/repos/helixnet/app/docs is auto-generated by FastAPI for interactive API exploration.