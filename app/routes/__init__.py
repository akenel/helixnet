# app/routes/__init__.py
# Just make the routers importable. No Base or DB imports here!
# FIX: The 'auth_router' object must be explicitly named here.
from app.routes.auth_router import  auth_router
from app.routes.jobs_router import jobs_router
from app.routes.users_router import users_router
from app.routes.tasks_router import tasks_router
__all__ = ["auth_router", "jobs_router", "tasks_router", "users_router"]
