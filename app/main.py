import logging
from pathlib import Path
from contextlib import asynccontextmanager
import asyncio # 📦 NEW: Import for asynchronous sleeping/pausing

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware # Use the middleware specific import

# ================================================================
# 🧠 Core Imports 
# ================================================================
from app.core.config import get_settings
from app.db.database import close_async_engine, get_db_session_context, init_db_tables 
from app.services.user_service import create_initial_users
from app.services.minio_service import initialize_minio # 📦 NEW: Import MinIO initialization function

# Router Imports
from app.routes import auth_router, jobs_router, users_router # Assuming these are defined in app/routes/__init__.py
from app.routes.health_router import health_router as health_check_router 

# ================================================================
# 🧱 CRITICAL FIX: FORCE MODEL REGISTRATION
# ================================================================
# FIX: Use the central registry in app/db/__init__.py for cleaner model registration.
# All model files must be imported here so Base.metadata knows about them.
import app.db # Ensures all models registered in __init__.py are loaded
import app.db.models.artifact_model # Keep explicit imports just in case
import app.db.models.job_model
import app.db.models.refresh_token_model
import app.db.models.task_model
import app.db.models.team_model
import app.db.models.user_model


# ================================================================
# ⚙️ CONFIGURATION INSTANTIATION (Settings must be available globally)
# ================================================================
settings = get_settings() 


# ================================================================
# 🛠️ Logger Setup
# ================================================================
logger = logging.getLogger("helix🛠️net")
logger.setLevel(logging.INFO)


# ================================================================
# 🌍 Lifespan Manager
# ================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup & shutdown lifecycle for HelixNet Core.
    Handles startup (DB init, MinIO init, user seeding) and shutdown (DB cleanup) logic.
    """
    logger.info("🚀 Starting up HelixNet Core (Lifespan).")
    
    # 1. Initialize Database Tables
    logger.info("⬇️ Calling init_db_tables...")
    try:
        await init_db_tables()
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.error(f"FATAL: Database table initialization failed: {e}", exc_info=True)
        # Allow running, but log the severe error.
    logger.info("✅ init_db_tables completed.")

    # 🛑 CRITICAL FIX: Introduce a short delay to mitigate PostgreSQL race conditions.
    # This gives the underlying asyncpg connection time to stabilize DDL visibility.
    logger.info("😴 Waiting 3 seconds for Postgres DDL visibility...")
    await asyncio.sleep(3) # Wait 3 seconds
    
    # 2. Initialize MinIO Bucket (FIX for Race Condition & Service Setup)
    logger.info("⬇️ Calling initialize_minio...")
    try:
        # This synchronous call introduces a slight I/O delay, giving Postgres time to finalize table creation.
        if initialize_minio():
            logger.info("🪣 MinIO bucket initialized successfully.")
        else:
            logger.error("WARNING: MinIO bucket initialization failed.")
    except Exception as e:
        logger.error(f"FATAL: MinIO initialization failed: {e}", exc_info=True)
        # Allow running, but log the severe error.
    logger.info("✅ initialize_minio completed.")

    # 3. Seed Initial Users
    logger.info("⬇️ Attempting to seed initial users...")
    try:
        # FIX: Ensure the AsyncSession is correctly bound via the context manager
        async with get_db_session_context() as db:
            await create_initial_users(db)
        logger.info("🧩 Initial user seeding process complete.")
    except Exception as e:
        # ✅ CRITICAL FIX: Ensure full traceback is shown when seeding fails due to missing table/race condition.
        logger.error(f"WARNING: Initial user seeding failed. Error: {e}", exc_info=True)
        
    yield # Application is ready to handle requests
    logger.info("✨ Application is RUNNING. Yielding control.") 
    
    # 4. Shutdown
    logger.info("⬆️ Application shutting down. Calling close_async_engine...")
    await close_async_engine()
    logger.info("✅ Async database engine closed.")
    logger.info("🛑 HelixNet Core shutdown complete.")


# ===============================================================
# 🌌 FastAPI Application Definition
# ================================================================
app = FastAPI(
    title="🌌 HelixNet Core API: Task & Data Management",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# ================================================================
# 🧱 CORS Middleware
# ================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================================================
# 🧩 Routers Registration
# ================================================================
# Use settings.API_V1_STR (e.g., "/api/v1") as the single prefix
app.include_router(auth_router, prefix=settings.API_V1_STR, tags=["🐘️ Authentication: routes/auth_router"])
app.include_router(users_router, prefix=settings.API_V1_STR, tags=["🥵️ Users: routes/users_router"])
app.include_router(jobs_router, prefix=settings.API_V1_STR, tags=["🥬️ Jobs : routes/jobs_router"])
# Health check uses a separate, unversioned prefix
app.include_router(health_check_router, prefix="/health", tags=["🩺️ System: Heartbeat - app/routes/health_router.py"])

logger.info(f"🖥️ FastAPI application initialized. Mounting API version: {settings.API_V1_STR}")

# ================================================================
# 🖼️ Templates & Static Files
# ================================================================
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# ================================================================
# 🖥️ HTML Views (Serving basic web UI pages)
# ================================================================
@app.get("/", tags=["🧠️ Helix-Web-App"], summary="HTML-VIEW: dashboard.html | 💁️ Helix SECURE Dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the main dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/login", tags=["🧠️ Helix-Web-App"], summary="HTML-VIEW: login.html | 🐘️ Login to control and monitor jobs on your dashborad", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/submit-form", tags=["🧠️ Helix-Web-App"], summary="HTML-VIEW: submit_form.html | 🕹️ Submit Form Request: async upload", response_class=HTMLResponse)
async def submit_form_page(request: Request):
    """Render the form submission page."""
    return templates.TemplateResponse("submit_form.html", {"request": request})
