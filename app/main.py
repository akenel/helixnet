import os
from pathlib import Path
from contextlib import asynccontextmanager # NEW IMPORT

# Core FastAPI imports
from fastapi import FastAPI, Request, APIRouter 
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware

# --- 🥋 Router Imports: The Fighting Team ---
# By importing the routers first, we isolate them for the API builder below.
from .routes.users_router import users_router
from .routes.auth_router import auth_router
from .routes.jobs_router import jobs_router
from .routes.health_router import health_router 

# --- Database and Configuration Imports ---
from .core.config import settings
# CHANGE: We now import the specific functions/objects needed for SQLAlchemy management.
# The legacy 'database' object is removed from imports.
from .db.database import close_async_engine 


# --- Application Lifespan (Startup/Shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events using the modern FastAPI lifespan context manager.
    With SQLAlchemy Async Engine, explicit startup is usually not required (connections are lazy),
    but clean shutdown (disposing the pool) is critical.
    """
    # Startup: Perform any necessary setup before the application starts accepting requests.
    yield # Application runs (handles requests)
    
    # Shutdown: Cleanly dispose of the async engine's connection pool.
    await close_async_engine()


# --- 🚀 App Initialization: The Final Build ---
app = FastAPI(
    title="🌌 HelixNet Core API: Task & Data Management",
    description="## 🛠️ Core Services for High-Volume Data Processing and Task Management.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    version=settings.VERSION,
    lifespan=lifespan, # ADDED: Use the lifespan context manager
)

# --- Path Configuration for Static Files and Templates (CWD Fix) ---
# CRITICAL FIX: Use pathlib to resolve paths relative to this file's location.
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# --- Static Files and Template Mounting ---
app.mount(
    "/static", 
    StaticFiles(directory=BASE_DIR / "static"), 
    name="static"
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Events ---
# REMOVED: The old @app.on_event("startup") and @app.on_event("shutdown") 
# handlers were removed and replaced by the 'lifespan' function above.


# --- 🔨 The API Router Builder (Where We Fix the Conflict) ---
# We use APIRouter here, which is designed to be included in the main FastAPI app.
api_v1_router = APIRouter()

# 1. AUTH Router: Handles /api/v1/token. We apply no prefix here, allowing the token endpoint to be flat.
api_v1_router.include_router(auth_router, tags=["🔑 Authentication"])

# 2. USERS Router: User endpoints (e.g., GET /api/v1/users/me).
api_v1_router.include_router(users_router, prefix="/users", tags=["👤 Users"])

# 3. JOB Router: Job submission and retrieval.
api_v1_router.include_router(jobs_router, prefix="/jobs", tags=["🎯 Job Processing"])


# --- 🌐 HTML Endpoints (The Front Door) ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/submit-form", response_class=HTMLResponse)
async def submit_form_page(request: Request):
    return templates.TemplateResponse("submit_form.html", {"request": request})


# --- 🛡️ API Endpoint Inclusion: The Final Stance ---
# 1. All versioned endpoints live under /api/v1
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

# 2. Health Check (Always outside the versioned prefix)
app.include_router(health_router, prefix="/health", tags=["System: Heartbeat"])
