"""Health & System diagnostics — the universal HelixNet platform status surface.

Three endpoints, used across every HelixNet app:
  • GET /health/healthz   — soft liveness (one line, for container healthchecks)
  • GET /health/health    — deep dependency check (DB + services), 503 if a CRITICAL dep is down
  • GET /health/system    — RICH machine-readable snapshot for the System Info dashboard
                            (build, env, wiring, storage, uptime + the dependency grid)

Design rule: only CRITICAL dependencies (PostgreSQL, Keycloak) can drive the
platform to DEGRADED / 503. Everything else (Celery, Redis, RabbitMQ, MinIO,
render-worker, LibreTranslate) is reported honestly but never degrades overall
health — those are optional / off the serving path.
"""
import asyncio
import socket
import time
from datetime import datetime, timezone
from typing import Dict, Any, List
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.db.database import get_db_session
from src.core.config import get_settings
from src.build_info import get_version, get_git_sha, get_build_date
from src.tasks.celery_app import app as celery_app

# The router is instantiated without prefix/tags here, they are applied in app/main.py
health_router = APIRouter()

# Process start — module import ≈ container/app boot. Used for uptime.
_STARTED_MONO = time.monotonic()
_STARTED_AT = datetime.now(timezone.utc)


# ----------------------------------------------------------------------
# INDIVIDUAL CHECKS
# ----------------------------------------------------------------------
async def check_db_status(db: AsyncSession) -> Dict[str, Any]:
    """PostgreSQL — CRITICAL. Measures round-trip latency of a trivial query."""
    t0 = time.monotonic()
    try:
        await db.execute(text("SELECT 1"))
        ms = round((time.monotonic() - t0) * 1000, 1)
        return {"component": "PostgreSQL DB", "status": "OK", "critical": True,
                "latency_ms": ms, "detail": "Connection successful."}
    except Exception as e:
        return {"component": "PostgreSQL DB", "status": "FAIL", "critical": True,
                "detail": f"Connection failed: {type(e).__name__}"}


def check_celery_status() -> Dict[str, Any]:
    """Celery workers — INFORMATIONAL ONLY (not critical).

    Async work runs through the aio-pika `lpcx-consumer`, not Celery, so
    "no workers" is a normal, healthy state and must NOT degrade overall health.
    """
    try:
        resp = celery_app.control.ping(timeout=1.0)
        if resp:
            return {"component": "Celery Workers", "status": "OK", "critical": False,
                    "detail": f"Broker and {len(resp)} worker(s) online.",
                    "workers_online": [list(r.keys())[0] for r in resp]}
        return {"component": "Celery Workers", "status": "NONE", "critical": False,
                "detail": "No Celery workers (optional — async work runs via lpcx-consumer)."}
    except Exception as e:
        return {"component": "Celery Workers", "status": "NONE", "critical": False,
                "detail": f"Celery broker not reachable ({type(e).__name__}) — optional, not on serving path."}


async def _tcp_check(component: str, host: str, port: int, critical: bool,
                     timeout: float = 1.5) -> Dict[str, Any]:
    """Generic reachability probe: open a TCP socket, measure connect latency.

    Dependency-free (no redis/pika/minio client needed) — just confirms the
    service is listening. Non-critical failures report status "NONE" so they
    never flip overall health.
    """
    t0 = time.monotonic()
    try:
        fut = asyncio.open_connection(host, port)
        reader, writer = await asyncio.wait_for(fut, timeout=timeout)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        ms = round((time.monotonic() - t0) * 1000, 1)
        return {"component": component, "status": "OK", "critical": critical,
                "latency_ms": ms, "detail": f"{host}:{port} reachable"}
    except Exception as e:
        return {"component": component, "status": "FAIL" if critical else "NONE",
                "critical": critical,
                "detail": f"{host}:{port} unreachable ({type(e).__name__})"}


def _host_port(url: str, default_port: int) -> tuple:
    """Pull (host, port) from a URL like http://keycloak:8080 or render-worker:8800."""
    if "://" not in url:
        url = "//" + url
    p = urlparse(url)
    return (p.hostname or "", p.port or default_port)


async def gather_checks(db: AsyncSession) -> List[Dict[str, Any]]:
    """Run every dependency probe. DB + Keycloak are critical; the rest optional."""
    s = get_settings()
    kc_host, kc_port = _host_port(getattr(s, "KEYCLOAK_SERVER_URL", "") or "http://keycloak:8080", 8080)
    rw_host, rw_port = _host_port(_get_env("RENDER_WORKER_URL", "http://render-worker:8800"), 8800)
    lt_host, lt_port = _host_port(_get_env("LIBRETRANSLATE_URL", "http://libretranslate:5000"), 5000)

    db_status = await check_db_status(db)
    others = await asyncio.gather(
        _tcp_check("Keycloak (Auth)", kc_host, kc_port, critical=True),
        _tcp_check("Redis (Cache)", s.REDIS_HOST, s.REDIS_PORT, critical=False),
        _tcp_check("RabbitMQ (Queue)", s.RABBITMQ_HOST, s.RABBITMQ_PORT, critical=False),
        _tcp_check("MinIO (Storage)", s.MINIO_HOST, s.MINIO_PORT, critical=False),
        _tcp_check("Render Worker", rw_host, rw_port, critical=False),
        _tcp_check("LibreTranslate", lt_host, lt_port, critical=False),
    )
    return [db_status, check_celery_status(), *others]


def _get_env(name: str, default: str) -> str:
    import os
    return (os.environ.get(name) or default).strip()


def _overall(checks: List[Dict[str, Any]]) -> str:
    """DEGRADED only if a CRITICAL check failed; otherwise OK."""
    for c in checks:
        if c.get("critical") and c.get("status") == "FAIL":
            return "DEGRADED"
    return "OK"


# ----------------------------------------------------------------------
# ENDPOINTS
# ----------------------------------------------------------------------
@health_router.get("/healthz")
async def healthz():
    """Soft liveness — fast one-liner for docker compose healthchecks."""
    return {"status": "💚️ Helix API 🍏️ Ready 💦️🔐️⛑️🥁️🥬️🧩️ Running 💯️ PrimeTime ✅️ OK"}


@health_router.get(
    "/health",
    summary="💖 Robust API Health Check",
    description="Deep health check of platform dependencies. HTTP 200 = all CRITICAL "
                "deps healthy; HTTP 503 = a critical dependency is down.",
)
async def health_check(db: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    """Aggregates dependency health. Only critical deps can return 503."""
    checks = await gather_checks(db)
    overall = _overall(checks)
    response = {"overall_status": overall, "api_version": "v1", "checks": checks}
    if overall == "DEGRADED":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=response)
    return response


@health_router.get(
    "/system",
    summary="🩺 Universal System Info snapshot",
    description="Rich machine-readable platform snapshot for the System Info dashboard: "
                "build, environment, service wiring, storage, uptime and the full dependency grid. "
                "Public (no auth) — safe diagnostics only, no secrets or shop figures.",
)
async def system_info(db: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    """The one-stop status payload every HelixNet app can call."""
    s = get_settings()
    checks = await gather_checks(db)

    # --- storage: how big is this app's database + its largest table ---
    storage: Dict[str, Any] = {}
    try:
        row = (await db.execute(text(
            "SELECT pg_size_pretty(pg_database_size(current_database())), "
            "pg_database_size(current_database())"))).first()
        if row:
            storage["db_size"] = row[0]
            storage["db_size_bytes"] = int(row[1])
        trow = (await db.execute(text(
            "SELECT relname, pg_size_pretty(pg_total_relation_size(relid)), "
            "pg_total_relation_size(relid) "
            "FROM pg_stat_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 1"))).first()
        if trow:
            storage["largest_table"] = trow[0]
            storage["largest_table_size"] = trow[1]
    except Exception as e:
        storage["error"] = type(e).__name__

    uptime = int(time.monotonic() - _STARTED_MONO)

    return {
        "overall_status": _overall(checks),
        "api_version": "v1",
        "service": getattr(s, "PROJECT_NAME", None) or "HelixNet",
        "shop": getattr(s, "STORE_NAME", None) or "Artemis Store",
        "environment": getattr(s, "HX_ENVIRONMENT", "") or _get_env("HX_ENVIRONMENT", "local"),
        "version": get_version(),
        "build": {"sha": get_git_sha(), "date": get_build_date()},
        "uptime_seconds": uptime,
        "started_at": _STARTED_AT.isoformat(timespec="seconds"),
        "server_time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "wiring": {
            "database": getattr(s, "POSTGRES_DB", "") or "",
            "pos_realm": getattr(s, "POS_REALM", "") or "",
            "lp_realm": getattr(s, "LP_REALM", "") or "",
            "keycloak_url": getattr(s, "KEYCLOAK_SERVER_URL", "") or "",
        },
        "storage": storage,
        "checks": checks,
    }
