#!/usr/bin/env python3
# ================================================================
# 🧩 HelixNet Core — FastAPI Application Entrypoint
# ================================================================
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel, OAuthFlowPassword
from fastapi.security import OAuth2

import logging
from contextlib import asynccontextmanager
from pathlib import Path
# Added datetime import for potential use in service layer mock/UserRead
from datetime import datetime 

from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2AuthorizationCodeBearer

# ================================================================
# ⚙️ Core Helix Imports
# ================================================================
from src.core.config import get_settings
from src.db.database import init_db_tables, close_async_engine, get_db_session_context
from src.services.user_service import create_initial_users
from src.services.minio_service import initialize_minio
from src.routes import auth_router, jobs_router, users_router
from src.routes.health_router import health_router

# ================================================================
# 🌍 Global Configuration
# ================================================================
settings = get_settings()
API_V1_STR = settings.API_V1_STR
# ================================================================
# 🪵 Logger Setup
# ================================================================
logger = logging.getLogger("helix.main")
logger.setLevel(logging.INFO)

# ================================================================
# 🌌 Lifespan Manager (Startup / Shutdown)
# ================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle HelixNet startup and shutdown lifecycle events."""
    logger.info("🚀 Starting up HelixNet Core (Lifespan)")

    # --- DB Init ---
    try:
        logger.info("🧱 Initializing database tables...")
        await init_db_tables()
        logger.info("✅ Database tables verified/created successfully.")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}", exc_info=True)

    # --- MinIO Init ---
    try:
        logger.info("🪣 Initializing MinIO bucket(s)...")
        if initialize_minio():
            logger.info("✅ MinIO initialized successfully.")
        else:
            logger.warning("⚠️ MinIO initialization returned False.")
    except Exception as e:
        logger.error(f"❌ MinIO initialization failed: {e}", exc_info=True)

    # --- Seed Users ---
    try:
        logger.info("👥 Seeding initial users...")
        async with get_db_session_context() as db:
            await create_initial_users(db)
        logger.info("✅ User seeding completed successfully.")
    except Exception as e:
        logger.warning(f"⚠️ User seeding encountered an issue: {e}", exc_info=True)

    logger.info("✨ HelixNet Core READY to serve requests.")
    yield

    # --- Shutdown ---
    logger.info("⬆️ Application shutting down. Closing DB engine...")
    await close_async_engine()
    logger.info("🛑 HelixNet Core shutdown complete.")

# ================================================================
# 🧠 FastAPI Application Factory
# ================================================================
app = FastAPI(
    title="HelixNet Core API",
    description="HelixNet FastAPI backend secured via Keycloak OpenID Connect",
    version=settings.API_VERSION,
    lifespan=lifespan,
    # This setting is crucial for Swagger UI OAuth2/Keycloak integration
    swagger_ui_oauth2_redirect_url="/docs/oauth2-redirect", 
)

# ================================================================
# 🔐 OAuth2 / Keycloak Integration
# ================================================================
# NOTE: This section correctly uses the environment settings.

oauth2_scheme = OAuth2(
    flows=OAuthFlowsModel(
        password=OAuthFlowPassword(
            tokenUrl="https://keycloak.helix.local/realms/master/protocol/openid-connect/token",
            scopes={"openid": "Access Helix API"}
        )
    ),
    description="OAuth2 Password flow via Keycloak"
)


@app.get("/protected", dependencies=[Depends(oauth2_scheme)], tags=["🔐 Security"])
def protected_route():
    """Protected route for verifying Keycloak authentication."""
    return {"status": "You are authenticated via Keycloak"}

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
# 🧩 Router Registration
# ================================================================
app.include_router(auth_router, prefix=settings.API_V1_STR, tags=["🔑 Authentication"])
app.include_router(users_router, prefix=settings.API_V1_STR, tags=["👤 Users"])
app.include_router(jobs_router, prefix=settings.API_V1_STR, tags=["⚙️ Jobs"])
app.include_router(health_router, prefix="/health", tags=["💓 Health"])

logger.info(f"🖥️ FastAPI app initialized → {settings.PROJECT_NAME} v{settings.PROJECT_APP_VERSION}")
logger.info(f"🔗 API base path: {settings.API_V1_STR}")

# ================================================================
# 🎨 Templates & Static Files
# ================================================================
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# ================================================================
# 🖥️ HTML Views (Dashboard, Login, Form Submission)
# ================================================================
@app.get("/", tags=["🧭 Web UI"], response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render main dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/login", tags=["🔑 Web UI"], response_class=HTMLResponse)
async def login_page(request: Request):
    """Render login page."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/submit-form", tags=["📨 Web UI"], response_class=HTMLResponse)
async def submit_form_page(request: Request):
    """Render form submission page."""
    return templates.TemplateResponse("submit_form.html", {"request": request})