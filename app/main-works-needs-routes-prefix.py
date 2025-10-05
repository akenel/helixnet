import uvicorn
from fastapi import FastAPI
from app.core.config import settings
from app.routes.jobs_router import jobs_router
from app.routes.auth_router import auth_router
from app.routes.users_router import users_router
from app.routes.health_router import health_router
import logging

# 💡 FINAL LOGGING FIX: Silence noisy libraries right at the start
# This must happen before uvicorn starts the server
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING) 

def create_application() -> FastAPI:
    """Initializes and configures the FastAPI application with routers and metadata."""
    
    # 💎 Injecting the rich, informative OpenAPI metadata here
    app = FastAPI(
        title="🌌 HelixNet Core API: Task & Data Management", 
        description="""
        ## 🛠️ Core Services for High-Volume Data Processing and Task Management.
        This API handles user authentication, CRUD operations for users, and the submission and monitoring 
        of long-running background jobs via Celery and PostgreSQL.
        
        * 🔐 **Authentication:** Use `/auth/token` with credentials to get a Bearer Token.
        * 📬 **Job Submission:** Submit heavy tasks to `/jobs/` for async processing.
        * 📊 **Status Check:** Monitor job persistence and status at `/jobs/{job_id}`.
        """,
        version=settings.API_V1_STR, 
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Include Routers
    app.include_router(health_router, prefix="/health", tags=["System"])
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    app.include_router(users_router, prefix="/users", tags=["Users"])
    # Note: jobs_router must now contain the '/jobs' prefix internally (see next file)
    app.include_router(jobs_router) 

    # Hook up application lifespan events (startup/shutdown)
    # ... (e.g., startup DB connection, seeding, shutdown Celery)

    return app

# 🔑 The single, correct assignment for Uvicorn
app = create_application()

if __name__ == "__main__":
    # Uvicorn will use the 'app' object defined above.
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info" # The handlers above will manage the verbosity.
    )
