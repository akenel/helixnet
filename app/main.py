from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter # ⬅️ Import APIRouter here to build the unified API router

# --- 🥋 Router Imports: The Fighting Team ---
from app.routes.users_router import users_router
from app.routes.auth_router import auth_router
from app.routes.jobs_router import jobs_router
from app.routes.health_router import health_router 


# --- 🔨 The API Router Builder (Where We Fix the Conflict) ---
# We create one master router for all /api/v1 endpoints.
api_v1_router = APIRouter()

# 1. AUTH Router: Handles /api/v1/token.
api_v1_router.include_router(auth_router, tags=["Auth & Token: The Gatekeeper"])

# 2. USERS Router: User endpoints (e.g., GET /api/v1/users/me).
api_v1_router.include_router(users_router, prefix="/users", tags=["👤 Users"])

# 3. JOB Router: Job submission and retrieval (POST /api/v1/jobs, GET /api/v1/jobs/{job_id}).
# 💥 FIX: We must add the prefix="/jobs" here to match the test script's URL.
api_v1_router.include_router(jobs_router, prefix="/jobs", tags=["🎯 Job Processing"])


# --- 🚀 App Initialization: The Final Build ---
app = FastAPI(
    title="🌌 HelixNet Core API: Task & Data Management",
    description="## 🛠️ Core Services for High-Volume Data Processing and Task Management.",
    # version=settings.VERSION_NUMBER
)

# Serve static files and templates (The UI Foundation)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


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
# We include the *single* assembled router here.
app.include_router(api_v1_router, prefix="/api/v1")

# 2. Health Check (Always outside the versioned prefix)
app.include_router(health_router, prefix="/health", tags=["System: Heartbeat"])
