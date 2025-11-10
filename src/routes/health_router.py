from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, List

# Assuming these imports exist in your project structure
from src.db.database import get_db_session
from src.tasks import celery_app
from src.tasks.celery_app import app

# The router is instantiated without prefix/tags here, they are applied in app/main.py
health_router = APIRouter() 

async def check_db_status(db: AsyncSession) -> Dict[str, Any]:
    """Checks the PostgreSQL connection by executing a simple query."""
    try:
        # Executes a quick, non-data-intensive query to confirm the connection is active
        await db.execute(text("SELECT 1"))
        return {"component": "PostgreSQL DB", "status": "OK", "detail": "Connection successful."}
    except Exception as e:
        # If any exception occurs (e.g., network failure, credentials), the DB is considered down
        return {"component": "PostgreSQL DB", "status": "FAIL", "detail": f"Connection failed: {type(e).__name__}"}

def check_celery_status() -> Dict[str, Any]:
    """Pings the Celery worker(s) and broker to check their availability."""
    try:
        # control.ping() is non-blocking and the fastest way to check workers
        celery_response: List[Dict[str, str]] = celery_app.control.ping(timeout=0.5)
        
        if celery_response:
            # If at least one worker responds, Celery is healthy
            online_workers = len(celery_response)
            return {
                "component": "Celery Workers", 
                "status": "OK", 
                "detail": f"Broker and {online_workers} worker(s) online.",
                # Optionally list the worker names
                "workers_online": [list(r.keys())[0] for r in celery_response]
            }
        else:
            # Ping succeeded (meaning broker is up), but no workers responded
            return {"component": "Celery Workers", "status": "FAIL", "detail": "Broker up, but no workers are active."}
    except Exception as e:
        # Ping failed, meaning the broker (RabbitMQ/Redis) connection failed
        return {"component": "Celery Broker", "status": "FAIL", "detail": f"Connection to Celery broker failed: {type(e).__name__}. Check RabbitMQ/Redis."}




@health_router.get(
    "/health",
    summary="💖 Robust API Health Check",
    description="""
    Performs deep health checks on all critical, complex backend services: 
    **PostgreSQL** (DB) and **Celery** (Worker/Broker).
    
    A successful **HTTP 200 OK** response indicates all core dependencies are functional.
    A **HTTP 503 Service Unavailable** response means at least one dependency is failing.
    """,
    response_description="Returns a JSON object detailing the status of each service."
)
async def health_check(
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Aggregates health status from all critical components.
    """
    db_status = await check_db_status(db)
    celery_status = check_celery_status()
    
    # Aggregate all individual statuses
    service_status = [
        db_status,
        celery_status,
    ]
    
    # Determine overall status and HTTP code
    overall_status = "OK"
    status_code = status.HTTP_200_OK
    
    for check in service_status:
        if check["status"] == "FAIL":
            overall_status = "DEGRADED" 
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            break

    response = {
        "overall_status": overall_status,
        "api_version": "v1", 
        "checks": service_status
    }

    if status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
        # Crucially, we raise an HTTPException to return the correct 503 status code
        # while still providing the informative body payload.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response
        )

    return response
