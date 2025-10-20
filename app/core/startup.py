from fastapi import FastAPI
from app.services.user_service import create_initial_users
from app.db.database import AsyncSession
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
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # --- Startup seeding ---
    @app.on_event("startup")
    async def startup_event():
        async with AsyncSession() as db:
            await create_initial_users(db)

    return app
