# /code/app/main.py
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, logger
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware

# ================================================================
# 🧠 Core Imports 
# ================================================================
from app.core.config import get_settings
# NOTE: We only import functions from database.py now. 
from app.db.database import close_async_engine, get_db_session_context, init_db_tables 
from app.routes import auth_router, jobs_router, users_router
from app.routes.health_router import health_router as health_check_router 

from app.services.user_service import create_initial_users

# ================================================================
# 🧱 CRITICAL FIX: FORCE MODEL REGISTRATION
# ================================================================
# When using SQLAlchemy ORM (Base.metadata), the application MUST import
# all files that define model classes before the engine starts up.
# This forces the models (User, Job, TaskResult, Artifact) to register 
# themselves with the Base.metadata registry, solving the "KeyError: 'TaskResult'"
# and ensuring tables are created during init_db_tables().
import app.db.models.user_model
import app.db.models.job_model
import app.db.models.task_model
import app.db.models.artifact_model # Assuming this model also exists
# ================================================================
# ⚙️ CONFIGURATION INSTANTIATION (MOVE IT HERE!)
settings = get_settings() # <--- 🥇 MOVE THIS LINE UP HERE! 🥳
# ================================================================
# ⚙️ Configuration (Keep the logger setup, but the settings definition moves up)
# ================================================================
logger = logging.getLogger("helixnet")
logger.setLevel(logging.INFO)
# ================================================================
# 🌍 Lifespan Manager
# ================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown lifecycle for HelixNet Core."""
    logger.info("🚀 Starting up HelixNet Core (Lifespan).")

    # 1. Ensure all DB tables are created (This triggers Step 3/init_db_tables)
    logger.info("⬇️ Calling init_db_tables...")
    # NOTE: This call now correctly sees all models (User, Job, TaskResult) 
    # because they were explicitly imported above.
    await init_db_tables()
    logger.info("✅ init_db_tables completed.")

     # 2. Seed initial users once DB is ready
    logger.info("⬇️ Attempting to seed initial users...")

    # THE FIX from previous turn: use 'async with'
    async with get_db_session_context() as db: 
        await create_initial_users(db)
    
    logger.info("✨ Application is RUNNING. Yielding control.")
    yield 

    # 3. Shutdown
    logger.info("⬆️ Application shutting down. Calling close_async_engine...")
    await close_async_engine()
    logger.info("🛑 HelixNet Core shutdown complete.")
# ================================================================
# 🌌 FastAPI Application Definition
# ================================================================
app = FastAPI(
    title="🌌 HelixNet Core API: Task & Data Management",
    description="## 🛠️ Core Services for High-Volume Data Processing and Task Management.",
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
    allow_origins=settings.BACKEND_CORS_ORIGINS or ["*"],
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
app.include_router(health_check_router, prefix="/health", tags=["🩺️ System: Heartbeat - app/routes/health_router.py"])


# ================================================================
# 🖼️ Templates & Static Files
# ================================================================
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# ================================================================
# 🖥️ HTML Views
# ================================================================
@app.get("/", tags=["🧠️ Helix-Web-App"], summary="HTML-VIEW: dashboard.html | 💁️ Helix SECURE Dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the main dashboard page."""
# Health check endpoint for the root path
    logger.info(f"🖥️ FastAPI application initialized. Mounting API version: {settings.API_V1_STR}")
    return templates.TemplateResponse("dashboard.html", {"request": request})

# ================================================================

@app.get("/login", tags=["🧠️ Helix-Web-App"], summary="HTML-VIEW: login.html | 🐘️ Login to control and monitor jobs on your dashborad", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page."""
    return templates.TemplateResponse("login.html", {"request": request})

# ================================================================

@app.get("/submit-form", tags=["🧠️ Helix-Web-App"], summary="HTML-VIEW: submit_form.html | 🕹️ Submit Form Request: async upload", response_class=HTMLResponse)
async def submit_form_page(request: Request):
    """Render the form submission page."""
    return templates.TemplateResponse("submit_form.html", {"request": request})
