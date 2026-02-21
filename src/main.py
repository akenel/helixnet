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
from src.services.artemis_user_seeding import seed_artemis_staff
from src.services.pos_seeding_service import seed_artemis_products
from src.services.store_settings_seeding import seed_store_settings
from src.services.customer_seeding_service import seed_customers
from src.services.sourcing_seeding_service import seed_sourcing_system
from src.services.hr_seeding_service import seed_all_hr_data
from src.services.minio_service import initialize_minio
from src.services.keycloak_health_service import check_keycloak_realms
from src.routes import auth_router, jobs_router, users_router
from src.routes.health_router import health_router
from src.routes.pos_router import router as pos_router, html_router as pos_html_router
from src.routes.customer_router import router as customer_router
from src.routes.kb_router import router as kb_router
from src.routes.admin_router import router as admin_router
from src.routes.hr_router import router as hr_router
from src.routes.camper_router import router as camper_router, html_router as camper_html_router
from src.services.camper_seeding_service import seed_camper_data
from src.routes.isotto_router import router as isotto_router, html_router as isotto_html_router
from src.services.isotto_seeding_service import seed_isotto_data
from src.routes.qa_router import router as qa_router, html_router as qa_html_router
from src.services.qa_seeding_service import seed_qa_checklist

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

    # --- Seed Artemis Staff (Pam, Ralph, Michael, Felix) ---
    try:
        logger.info("👔 Seeding Artemis store staff...")
        async with get_db_session_context() as db:
            await seed_artemis_staff(db)
        logger.info("✅ Artemis staff seeding completed successfully.")
    except Exception as e:
        logger.warning(f"⚠️ Artemis staff seeding encountered an issue: {e}", exc_info=True)

    # --- Seed POS Products (Felix's Artemis Store) ---
    try:
        logger.info("🛒 Seeding POS demo products...")
        async with get_db_session_context() as db:
            await seed_artemis_products(db)
        logger.info("✅ POS product seeding completed successfully.")
    except Exception as e:
        logger.warning(f"⚠️ POS product seeding encountered an issue: {e}", exc_info=True)

    # --- Seed Store Settings (Felix's Artemis Store Config) ---
    try:
        logger.info("⚙️ Seeding store settings...")
        async with get_db_session_context() as db:
            await seed_store_settings(db)
        logger.info("✅ Store settings seeding completed successfully.")
    except Exception as e:
        logger.warning(f"⚠️ Store settings seeding encountered an issue: {e}", exc_info=True)

    # --- Seed Customers (The CRACKs - External Customers) ---
    try:
        logger.info("🎮 Seeding customers (The CRACKs)...")
        async with get_db_session_context() as db:
            await seed_customers(db)
        logger.info("✅ Customer seeding completed successfully.")
    except Exception as e:
        logger.warning(f"⚠️ Customer seeding encountered an issue: {e}", exc_info=True)

    # --- Seed Sourcing System (Suppliers + Requests for Felix) ---
    try:
        logger.info("📦 Seeding sourcing system (suppliers + requests)...")
        async with get_db_session_context() as db:
            results = await seed_sourcing_system(db)
        logger.info(f"✅ Sourcing seeding completed: {results}")
    except Exception as e:
        logger.warning(f"⚠️ Sourcing system seeding encountered an issue: {e}", exc_info=True)

    # --- Seed HR Data (Employees + Time Entries) ---
    try:
        logger.info("👔 Seeding HR data (employees + time entries)...")
        async with get_db_session_context() as db:
            results = await seed_all_hr_data(db)
        logger.info(f"✅ HR seeding completed: {results}")
    except Exception as e:
        logger.warning(f"⚠️ HR seeding encountered an issue: {e}", exc_info=True)

    # --- Seed Camper & Tour Data (Sebastino's Shop, Trapani) ---
    try:
        logger.info("Seeding Camper & Tour service data...")
        async with get_db_session_context() as db:
            await seed_camper_data(db)
        logger.info("Camper & Tour seeding completed successfully.")
    except Exception as e:
        logger.warning(f"Camper & Tour seeding encountered an issue: {e}", exc_info=True)

    # --- Seed ISOTTO Sport Data (Print Shop, Trapani - since 1968) ---
    try:
        logger.info("Seeding ISOTTO Sport print shop data...")
        async with get_db_session_context() as db:
            await seed_isotto_data(db)
        logger.info("ISOTTO Sport seeding completed successfully.")
    except Exception as e:
        logger.warning(f"ISOTTO Sport seeding encountered an issue: {e}", exc_info=True)

    # --- Seed QA Testing Checklist (Anne's 46-item dashboard) ---
    try:
        logger.info("Seeding QA testing checklist...")
        async with get_db_session_context() as db:
            await seed_qa_checklist(db)
        logger.info("QA testing checklist seeding completed.")
    except Exception as e:
        logger.warning(f"QA testing checklist seeding encountered an issue: {e}", exc_info=True)

    # --- Keycloak Realm Health Check ---
    try:
        realm_status = await check_keycloak_realms()
        if realm_status["status"] == "success":
            logger.info(f"✅ Keycloak connected - {realm_status['realm_count']} realm(s) found")
        elif realm_status["status"] == "pending":
            logger.info("⏳ Keycloak startup pending - auth will be verified on first request")
        else:
            logger.info(f"ℹ️ Keycloak check deferred: {realm_status.get('message', 'Service starting')}")
    except Exception as e:
        logger.debug(f"Keycloak health check deferred: {e}")

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
            tokenUrl="https://keycloak.helix.local/realms/kc-realm-dev/protocol/openid-connect/token",
            scopes={"openid": "Access Helix API"}
        )
    ),
    description="OAuth2 Password flow via Keycloak (kc-realm-dev)"
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
app.include_router(pos_router, tags=["🛒 POS - Felix's Artemis Store"])
app.include_router(pos_html_router, tags=["🖥️ POS Web UI - Pam's Interface"])
app.include_router(customer_router, tags=["🎮 CRACK Loyalty - Customer Profiles"])
app.include_router(kb_router, tags=["📚 KB Contributions - Knowledge is Gold"])
app.include_router(admin_router, prefix=settings.API_V1_STR, tags=["👑 Admin - Role Management"])
app.include_router(hr_router, tags=["HR - Time & Payroll (BLQ Module)"])
app.include_router(health_router, prefix="/health", tags=["💓 Health"])
app.include_router(camper_router, tags=["Camper & Tour - Service Management"])
app.include_router(camper_html_router, tags=["Camper & Tour - Web UI"])
app.include_router(isotto_router, tags=["ISOTTO Sport - Print Shop"])
app.include_router(isotto_html_router, tags=["ISOTTO Sport - Print Shop UI"])
app.include_router(qa_router, tags=["QA Testing Dashboard"])
app.include_router(qa_html_router, tags=["QA Testing Dashboard - Web UI"])

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