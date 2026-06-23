#!/usr/bin/env python3
# ================================================================
# 🧩 HelixNet Core — FastAPI Application Entrypoint
# ================================================================
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel, OAuthFlowPassword
from fastapi.security import OAuth2

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
# Added datetime import for potential use in service layer mock/UserRead
from datetime import datetime 

from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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
from src.routes.isotto_catalog_router import router as isotto_catalog_router, html_router as isotto_catalog_html_router
from src.services.isotto_seeding_service import seed_isotto_data
from src.services.isotto_catalog_seeding_service import seed_isotto_catalog_data
from src.routes.qa_router import router as qa_router, html_router as qa_html_router
from src.services.qa_seeding_service import seed_qa_checklist
from src.routes.backlog_router import router as backlog_router, html_router as backlog_html_router
from src.services.backlog_seeding_service import seed_backlog_data
from src.routes.compute_router import router as compute_router, html_router as compute_html_router
from src.services.compute_seeding_service import seed_compute_data
from src.routes.bottega_router import router as bottega_router

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
async def _empty_cart_reaper_loop():
    """BL-86: hourly sweep that cancels stale, empty, zero-value OPEN carts (>12h old)
    so abandoned sessions don't clutter the report. Runs inside the web process (no
    extra container/scheduler); idempotent and defensive -- a bad tick never kills the
    app. Celery Beat isn't deployed in this stack, so this is the auto-driver; the same
    work is also exposed at POST /api/v1/pos/maintenance/reap-empty-carts for manual runs."""
    import asyncio
    from src.routes.pos_router import reap_stale_open_carts
    while True:
        try:
            await asyncio.sleep(3600)  # hourly
            async with get_db_session_context() as db:
                result = await reap_stale_open_carts(db, older_than_hours=12)
            if result["cancelled"]:
                logger.info(f"🧹 Empty-cart reaper cancelled {result['cancelled']} stale cart(s)")
        except asyncio.CancelledError:
            break
        except Exception as e:  # never let a maintenance tick crash the app
            logger.warning(f"Empty-cart reaper tick skipped: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle HelixNet startup and shutdown lifecycle events."""
    logger.info("🚀 Starting up HelixNet Core (Lifespan)")

    # Demo-content seeding gate. Default ON (every existing env keeps seeding the
    # Artemis catalogue + CRACK customers). The Banco Day-One sandbox sets
    # HX_SEED_DEMO=false so it boots with an EMPTY catalogue — staff, store
    # settings and login users still seed, so Pam can log in and VAT is correct.
    seed_demo = os.getenv("HX_SEED_DEMO", "true").strip().lower() not in ("false", "0", "no")
    if not seed_demo:
        logger.warning("🌱 HX_SEED_DEMO=false — skipping catalogue + customer demo seeding (empty sandbox).")

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
    if seed_demo:
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
    if seed_demo:
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

    # --- Seed ISOTTO Catalog Data (Suppliers, Products, Stock) ---
    try:
        logger.info("Seeding ISOTTO Sport catalog data...")
        async with get_db_session_context() as db:
            await seed_isotto_catalog_data(db)
        logger.info("ISOTTO Sport catalog seeding completed successfully.")
    except Exception as e:
        logger.warning(f"ISOTTO Sport catalog seeding encountered an issue: {e}", exc_info=True)

    # --- Seed QA Testing Checklist (Anne's 46-item dashboard) ---
    try:
        logger.info("Seeding QA testing checklist...")
        async with get_db_session_context() as db:
            await seed_qa_checklist(db)
        logger.info("QA testing checklist seeding completed.")
    except Exception as e:
        logger.warning(f"QA testing checklist seeding encountered an issue: {e}", exc_info=True)

    # --- Seed Backlog Items (Unified Board) ---
    try:
        logger.info("Seeding backlog items...")
        async with get_db_session_context() as db:
            await seed_backlog_data(db)
        logger.info("Backlog seeding completed.")
    except Exception as e:
        logger.warning(f"Backlog seeding encountered an issue: {e}", exc_info=True)

    # --- Seed LPCX compute starter grants ---
    try:
        logger.info("Seeding LPCX compute starter grants...")
        async with get_db_session_context() as db:
            await seed_compute_data(db)
        logger.info("LPCX compute seeding completed.")
    except Exception as e:
        logger.warning(f"LPCX compute seeding encountered an issue: {e}", exc_info=True)

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

    # --- BL-86: start the hourly empty-cart reaper (background) ---
    import asyncio
    reaper_task = asyncio.create_task(_empty_cart_reaper_loop())
    logger.info("🧹 Empty-cart reaper started (hourly, cancels empty OPEN carts >12h).")

    logger.info("✨ HelixNet Core READY to serve requests.")
    yield

    # --- Shutdown ---
    logger.info("⬆️ Application shutting down. Closing DB engine...")
    reaper_task.cancel()
    try:
        await reaper_task
    except asyncio.CancelledError:
        pass
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
# 🚫 No-stale-HTML — server-rendered pages must NEVER be cached.
# Without this, a browser can serve a months-old page (the cf2794e ghost:
# a Dec-2025 customer-lookup survived 914 commits in a cached tab, showing
# long-fixed bugs). Only text/html is touched; CDN/static assets are
# unaffected. Pages carry a live build stamp, so re-fetch is cheap + correct.
# ================================================================
@app.middleware("http")
async def no_cache_html(request: Request, call_next):
    response = await call_next(request)
    if response.headers.get("content-type", "").startswith("text/html"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


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
app.include_router(isotto_catalog_router, tags=["ISOTTO Sport - Catalog"])
app.include_router(isotto_catalog_html_router, tags=["ISOTTO Sport - Catalog UI"])
app.include_router(qa_router, tags=["QA Testing Dashboard"])
app.include_router(qa_html_router, tags=["QA Testing Dashboard - Web UI"])
app.include_router(backlog_router, tags=["Backlog - Unified Board"])
app.include_router(backlog_html_router, tags=["Backlog - Web UI"])
app.include_router(compute_router, tags=["Compute - LPCX"])
app.include_router(compute_html_router, tags=["Compute - Web UI"])
app.include_router(bottega_router, tags=["Bottega - Onboarding"])

logger.info(f"🖥️ FastAPI app initialized → {settings.PROJECT_NAME} v{settings.PROJECT_APP_VERSION}")
logger.info(f"🔗 API base path: {settings.API_V1_STR}")

# ================================================================
# 🎨 Templates & Static Files
# ================================================================
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.globals["lp_kc_url"] = get_settings().LP_KC_PUBLIC_URL  # browser-facing KC host for LP login
# Real build stamp for the status bar (version + the SHA actually deployed).
from src.build_info import get_version, get_git_sha  # noqa: E402
templates.env.globals["app_version"] = get_version()
templates.env.globals["git_sha"] = get_git_sha()
templates.env.globals["app_env"] = getattr(get_settings(), "HX_ENVIRONMENT", "") or ""  # env code (SBX/STG/PRD) for the status bar + receipt tag
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# ================================================================
# 🖥️ HTML Views (Dashboard, Login, Form Submission)
# ================================================================
@app.get("/", tags=["🧭 Web UI"], response_class=HTMLResponse)
async def home(request: Request):
    """La Piazza front door -- the public landing page."""
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/health/dashboard", tags=["💓 Health"], response_class=HTMLResponse)
async def health_dashboard(request: Request):
    """Standalone diagnostic page: server health, build/system info, and the
    visitor's own browser + screen specs. No login required -- it's pure
    diagnostics (shop figures live behind the in-app 📊 Shop Pulse card).
    build version/sha are Jinja globals; env + shop come from settings."""
    from datetime import datetime, timezone
    _s = get_settings()
    return templates.TemplateResponse("health_dashboard.html", {
        "request": request,
        "env": getattr(_s, "HX_ENVIRONMENT", "") or "",
        "shop": getattr(_s, "STORE_NAME", None) or "Artemis Store",
        "server_time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })

@app.get("/api/maintenance", include_in_schema=False)
async def maintenance_notice():
    """Public maintenance flag for the site banner. Toggle by setting LP_MAINTENANCE_MESSAGE on the
    box (empty/unset = banner off) and restarting -- no code deploy needed. The shared nav polls this."""
    msg = os.getenv("LP_MAINTENANCE_MESSAGE", "").strip()
    return {"active": bool(msg), "message": msg}

@app.get("/get-started", tags=["🧭 Web UI"], response_class=HTMLResponse)
async def get_started_page(request: Request):
    """The one-motion door: name + CV -> account + Bottega + logged in."""
    _s = get_settings()
    return templates.TemplateResponse("get_started.html", {"request": request, "lp_realm": _s.LP_REALM, "lp_client": _s.LP_CLIENT})

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve the Lupo wolf as the favicon so every page has a brand mark (was a 404)."""
    return RedirectResponse(url="/static/lapiazza-wolf.png")

@app.get("/sitemap", tags=["🧭 Web UI"], response_class=HTMLResponse)
async def sitemap_page(request: Request):
    """The app directory: La Piazza/Bottega (the flagship) + the other apps on the platform —
    POS, Camper & Tour (repairs), ISOTTO (printing), Backlog/QA — each its own. Every GET page
    route is auto-bucketed under its app, so the map never drifts."""
    apps = [
        {"icon": "🏛️", "name": "La Piazza · La Bottega", "tag": "the Square (market) + the Workshop — the flagship",
         "prefixes": ["/compute", "/get-started", "/u/", "/s/"], "links": [
            {"p": "/", "l": "Home", "d": "the front door"},
            {"p": "/get-started", "l": "Get Started", "d": "one-motion onboarding (CV or a sentence)"},
            {"p": "/compute/bottega", "l": "🔧 Workshop", "d": "run recipes — the Chinese menu"},
            {"p": "/compute/legends", "l": "🎭 Legends", "d": "browse masters → Ask a Master"},
            {"p": "/compute/me", "l": "🐺 You", "d": "your rebuild dashboard (body/mind/spirit)"},
            {"p": "/compute", "l": "⚡ Exchange", "d": "the compute exchange / jobs"},
            {"p": "/compute/faq", "l": "FAQ", "d": "why La Piazza exists"}]},
        {"icon": "🛒", "name": "POS", "tag": "point-of-sale app", "prefixes": ["/pos"], "links": [
            {"p": "/pos/dashboard", "l": "POS Dashboard", "d": "checkout · products · reports · cash"}]},
        {"icon": "🚐", "name": "Camper & Tour", "tag": "vehicle repairs & service app", "prefixes": ["/camper"], "links": [
            {"p": "/camper/dashboard", "l": "Repairs Dashboard", "d": "jobs · customers · bays · quotations · invoices"}]},
        {"icon": "🖨️", "name": "ISOTTO", "tag": "print-shop app", "prefixes": ["/print-shop"], "links": [
            {"p": "/print-shop/dashboard", "l": "Print Shop Dashboard", "d": "orders · catalog · artworks · suppliers"}]},
    ]
    # Shared services — EVERY app plugs into these, exactly like every app uses Keycloak.
    # The Backlog (BL) is a PLATFORM SERVICE, not an app: every app's 💬 feedback lands on the one board.
    services = [
        {"icon": "🔐", "name": "Keycloak — Auth", "tag": "ONE login for every app (the unified realm + SSO)",
         "prefixes": ["/login"], "links": [
            {"p": "/get-started", "l": "Get Started / Login", "d": "the real door — sign up in one motion, or log in (Keycloak SSO across all apps)"}]},
        {"icon": "🗒️", "name": "Backlog (BL)", "tag": "the shared tracker — every app's 💬 feedback lands here",
         "prefixes": ["/backlog"], "links": [
            {"p": "/backlog", "l": "Backlog board", "d": "kanban + list + activity; all apps feed it"}]},
        {"icon": "✅", "name": "QA / Testing", "tag": "the shared QA dashboard", "prefixes": ["/testing"], "links": [
            {"p": "/testing", "l": "QA Dashboard", "d": "bugs · tests · results"}]},
        {"icon": "🛠️", "name": "API & Docs", "tag": "one backend, all apps", "prefixes": ["/docs"], "links": [
            {"p": "/docs", "l": "API docs", "d": "the OpenAPI explorer (dev)"}]},
    ]
    EXCLUDE = {"/openapi.json", "/redoc", "/docs/oauth2-redirect", "/sitemap",
               "/favicon.ico", "/{full_path:path}", "/"}
    routes = set()
    for r in request.app.routes:
        methods = getattr(r, "methods", None) or set()
        path = getattr(r, "path", "") or ""
        if "GET" not in methods or not path or path.startswith("/api") \
                or path.startswith("/health") or path in EXCLUDE:
            continue
        routes.add(path)
    groups = apps + services
    other = []
    for path in sorted(routes):
        for g in groups:
            if any(path == pre.rstrip("/") or path.startswith(pre) for pre in g["prefixes"]):
                g.setdefault("all", []).append(path)
                break
        else:
            other.append(path)
    curated = {lk["p"].split("?")[0] for g in groups for lk in g["links"]}
    return templates.TemplateResponse("sitemap.html", {
        "request": request, "apps": apps, "services": services, "other": other, "curated": curated})

@app.get("/og/{name}", include_in_schema=False)
async def og_card(name: str):
    """Serve a serialized OG card from MinIO (the artifact vault) — used as og:image by shares.
    Falls back to a bundled static copy so an unfurl bot never gets a 404."""
    from fastapi.responses import Response
    safe = name.replace("..", "").lstrip("/")
    data = None
    try:
        from src.services.minio_service import minio_service
        data = minio_service.download_artifact(f"cards/{safe}")
    except Exception:  # noqa: BLE001
        data = None
    if not data:
        fp = Path(__file__).parent / "static" / "og" / safe
        if fp.exists():
            data = fp.read_bytes()
    if not data:
        return Response(status_code=404)
    return Response(content=data, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=86400"})

@app.get("/s/{session_id}", tags=["🧭 Web UI"], response_class=HTMLResponse)
async def share_page(session_id: str, request: Request):
    """Public postcard for a shared output. Share-1 (BL-010): a *meaty* og:description
    (Ollama Turbo teaser, cached on the session) + a guaranteed-image ladder (object
    image -> Lupo Wolf default) so every share lands gorgeous on WhatsApp/Telegram/X --
    never dry, never imageless. The session id IS the share token (Share-2 serializes it)."""
    import json as _json, re as _re, logging as _logging
    from uuid import UUID as _UUID
    from src.db.models.bottega_model import BottegaSessionModel
    from src.services.bottega_service import share_teaser
    _log = _logging.getLogger("helix.share")

    try:
        sid = _UUID(session_id)
    except Exception:  # noqa: BLE001
        sid = None

    title = content = creator = ""
    inputs: dict = {}
    version = 1
    created_dt = None
    found = False
    if sid is not None:
        async with get_db_session_context() as db:
            s = await db.get(BottegaSessionModel, sid)
            if s is not None:
                found = True
                title = s.title or "La Piazza"
                content = s.output or ""
                # Structured (JSON) outputs were dumped raw on the postcard ({"childhood":...}).
                # Render them as readable markdown instead -- {field: value} -> "## Field\n value".
                if (s.output_type or "") == "json" and content.lstrip().startswith("{"):
                    try:
                        _o = _json.loads(content); _parts = []
                        for _k, _v in _o.items():
                            if str(_k).startswith("_") or _v in (None, "", [], {}):
                                continue
                            _lab = str(_k).replace("_", " ").title()
                            if isinstance(_v, list):
                                _b = "\n".join(f"- {_x}" for _x in _v if _x)
                                if _b:
                                    _parts.append(f"## {_lab}\n{_b}")
                            elif isinstance(_v, (str, int, float)):
                                _parts.append(f"## {_lab}\n{_v}")
                        content = "\n\n".join(_parts) or content
                    except Exception:  # noqa: BLE001
                        pass
                version = s.version or 1
                created_dt = s.created_at
                creator = s.username or ""
                try:
                    inputs = _json.loads(s.inputs or "{}")
                except Exception:  # noqa: BLE001
                    inputs = {}
    if not found:
        return HTMLResponse("<h1 style='font-family:sans-serif;color:#888;text-align:center;margin-top:20vh'>Not found</h1>", status_code=404)

    # --- meaty og:description: cached teaser -> generate (Turbo) + cache -> snippet fallback ---
    og = inputs.get("_og") if isinstance(inputs.get("_og"), dict) else {}
    desc = (og or {}).get("d") or ""
    if not desc:
        desc = await share_teaser(title, content)
        if desc:
            try:
                async with get_db_session_context() as db:
                    s2 = await db.get(BottegaSessionModel, sid)
                    if s2 is not None:
                        try:
                            inp = _json.loads(s2.inputs or "{}")
                        except Exception:  # noqa: BLE001
                            inp = {}
                        meta = inp.get("_og") if isinstance(inp.get("_og"), dict) else {}
                        meta["d"] = desc
                        inp["_og"] = meta
                        s2.inputs = _json.dumps(inp)
                        await db.commit()
            except Exception:  # noqa: BLE001
                _log.warning("share_page: could not cache teaser", exc_info=True)
    if not desc:
        desc = " ".join(content.replace("#", "").replace("*", "").split())[:155]

    # --- guaranteed-image ladder: explicit object image -> Lupo Wolf default ---
    _IMG_RE = _re.compile(r"(https?://\S+\.(?:png|jpe?g|webp|gif)(?:\?\S+)?|/media/\S+)", _re.I)
    cover = (og or {}).get("img") or ""
    if not cover:
        for v in inputs.values():
            if isinstance(v, str):
                m = _IMG_RE.search(v)
                if m:
                    cover = m.group(1)
                    break
    if not cover:
        cover = "/static/lapiazza-wolf.png"

    # behind Caddy, uvicorn sees http -> force the real scheme/host so og:image is HTTPS
    # (WhatsApp/Telegram drop mixed-content images, which is why the card showed no picture)
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme or "https"
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    base_url = f"{proto}://{host}"
    og_image = cover if cover.startswith("http") else f"{base_url}{cover}"
    return templates.TemplateResponse("share.html", {
        "request": request, "title": title, "inputs": inputs,
        "content": content, "snippet": desc, "version": version,
        "serial": str(sid)[:8].upper(), "share_url": f"{base_url}/s/{sid}",
        "created": created_dt.strftime("%d %b %Y") if created_dt else "",
        "creator": creator, "cover": cover, "base_url": base_url, "og_image": og_image,
    })

@app.get("/jobs", tags=["🧭 Web UI"], include_in_schema=False)
async def dashboard():
    """Legacy job-queue view -> retired. The modern, auth'd jobs UI is the Exchange at
    /compute (real schema + KC auth). The old mock-auth dashboard.js called the removed
    /api/v1/jobs; rather than rewrite an orphan to duplicate /compute, redirect there."""
    return RedirectResponse(url="/compute")

@app.get("/login", tags=["🔑 Web UI"])
async def login_page(request: Request):
    """The real door is the one-motion Get Started (sign up) + its 'already a member? log in'
    (Keycloak SSO). The old standalone /login register form looped -- send people to the real
    entrance instead of a dead-end."""
    return RedirectResponse(url="/get-started", status_code=307)

@app.get("/submit-form", tags=["📨 Web UI"])
async def submit_form_page():
    """The August-2025 submit form grew up -- send people to its real self, La Bottega."""
    return RedirectResponse(url="/compute/bottega", status_code=307)