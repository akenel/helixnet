from fastapi import FastAPI
from app.db.database import AsyncSession, async_engine, AsyncGenerator, AsyncSessionLocal, async_sessionmaker, get_db_session_context, get_db_session, get_db_session_sync, get_settings, create_async_engine
from app.routes import auth_router, health_router, jobs_router, tasks_router, users_router
from app.services.user_service import create_initial_users

def create_application() -> FastAPI:
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
        version="1.0.0",  # <-- ✅ Don't use settings.API_V1_STR here
        docs_url="/docs",
        redoc_url="/redoc"
    )
    # Include Routers
    # app.include_router(health_router, prefix="/health", tags=["🧐️ System"])
    # app.include_router(auth_router, prefix="/auth", tags=["🐘️ Authentication"])
    # app.include_router(users_router, prefix="/users", tags=["🥵️ Users"])
    # app.include_router(jobs_router, prefix="/jobs", tags=["🐇️ Jobs"])  
    # # ✅ enforce jobs prefix here
    # # ✅ DO enforce jobs prefix here (double prefixed routes just remove the seconf prefix=)

    # --- Startup seeding ---
    @app.on_event("startup")
    async def startup_event():
        async with async_session() as db:
            await create_initial_users(db)

    return app
