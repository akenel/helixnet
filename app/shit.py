from fastapi import FastAPI

# Assuming you import settings and other core components here
# from app.core.config import get_settings

# --- Router Imports (FIX for ImportError) ---
# Assuming the exported object in each file is named after the file (e.g., 'users_router').
from app.routes.users_router import users_router
from app.routes.auth_router import auth_router
from app.routes.jobs_router import jobs_router
from app.routes.health_router import health_router  # Assuming this also exists
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

# Initialize the FastAPI application (required before calling app.include_router)
# If you use get_settings(), include it here:
# settings = get_settings()
app = FastAPI(
    title="🌌 HelixNet Core API: Task & Data Management",
    description="## 🛠️ Core Services for High-Volume Data Processing and Task Management.",
    # version=settings.VERSION_NUMBER (or hardcode the version)
)

# Serve static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/submit-form", response_class=HTMLResponse)
async def submit_form_page(request: Request):
    return templates.TemplateResponse("submit_form.html", {"request": request})


# ... (Place middleware or startup/shutdown events here) ...

# 💡 FIX: Add prefix="/api/v1" to apply the standard API versioning path.
# We also use the tags argument to avoid the ugly, duplicated tags seen in the OpenAPI spec.

# Core API Endpoints (Now consistently prefixed)
app.include_router(auth_router, prefix="/api/v1", tags=["Authentication"])
app.include_router(users_router, prefix="/api/v1", tags=["Users"])
app.include_router(jobs_router, prefix="/api/v1", tags=["Job Processing"])

# Health Check (Typically kept outside the versioned prefix)
app.include_router(health_router, prefix="/health", tags=["System"])

# 🚨 Important Note: You may need to adjust your existing include_router calls
# to match this clean pattern (including setting the tags here).
